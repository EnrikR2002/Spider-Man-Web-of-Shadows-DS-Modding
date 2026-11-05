"""Candidate v0.40: repair Ballast colors and stage Freight cargo at the approach.

This guarded post-pass leaves published v0.39 bytes untouched. The Freight
models are private to that room; Dry Dock and Crown retain their cargo models.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import (chapter_spectacle_audio as audio, chapter_spectacle_events as ev,
                   crane_arm, crane_drop as drop, crane_row, midnight_voltage,
                   oscorp_resources, room_author, room_script as s, spider2099 as assets, tasm_kit as kit,
                   vortex_forge_art, wos_tool as w)
from tools.actor_resources import ModelSheet
from tools.crane_creature_art import packets
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects
from tools.room_collision import RoomCollision
from tools.spider2099_art import gpu_commands

VERSION, DATE = '0.40.0', '2026-11-04'
PARENT = 'b53e3879cc575e63979f1a65a7d29fc610a3d1d44080f2205b29aec26075d37c'
PARENT_PATH = ROOT / 'build/version-0.39.0-final/Versioned.nds'
OBJ = 'zz_AR_FreightExchange_app.obj'
BALLAST_MODEL, BALLAST_TEXTURE = 'zz_F22_ballast.nsbmd', 'zz_C40_ballast.nsbtx'
CARGO_MODELS = ('zz_C40_closed.nsbmd', 'zz_C40_open.nsbmd')
GROUP = 183
MOTION, ROWS, WORLD = 0x02175DD4, 0x02175D94, 0x02175BDC
OLD_TICK = 0x02159914
UPPER_X, LOWER_X = 220, 248
LAND_FRAMES = 17
MODE = 0x12C
SPAWN_CALL = 0x0204C648
ANCHOR_NATIVE = 0x0203147C
ANCHOR_SITES = (0x02080814, 0x0208096C, 0x02080C40)
CONFIGS = (0x02159AF4, 0x02159B48, 0x02159B9C)


def ballast_texture(raw):
    """Give Ballast a private direct-color atlas and brighten its two dark body tiles."""
    model, texture = vortex_forge_art.direct_texture(raw)
    out = bytearray(texture)
    entry = TextureArchive.parse(out).textures[0]
    if (entry['format'], entry['width'], entry['height']) != (7, 64, 64):
        raise ValueError('Expected Ballast 64px direct-color atlas')
    for tile in (3, 4):
        for y in range(tile // 4 * 16, (tile // 4 + 1) * 16):
            for x in range(tile % 4 * 16, (tile % 4 + 1) * 16):
                at = entry['offset'] + 2 * (y * 64 + x)
                old = w.u16(out, at)
                channels = [min(31, (((old >> shift) & 31) * 3 + 1) // 2 + 3) for shift in (0, 5, 10)]
                struct.pack_into('<H', out, at, (old & 0x8000) | channels[0] | channels[1] << 5 | channels[2] << 10)
    return model, bytes(out)


def cargo_model(raw, *, opened=False):
    """Narrow Freight's scenery and give the open container a readable interior."""
    geometry = ModelGeometry.parse(raw)
    commands = []
    cavity = 2 | 3 << 5 | 5 << 10
    additions = cavity_hits = 0
    for op, args in gpu_commands(raw):
        if opened and op == 0x20 and args[0] == cavity:
            args = (6 | 9 << 5 | 13 << 10,)
            cavity_hits += 1
        if opened and op == 0x41:
            for x0, y0, x1, y1 in ((-14.3, 2, -13.7, 17), (-.3, 2, .3, 17),
                                   (13.7, 2, 14.3, 17), (-17, 17, 17, 17.6)):
                commands.append((0x20, (11 | 14 << 5 | 17 << 10,)))
                for x, y in ((x0, y1), (x0, y0), (x1, y0), (x1, y1)):
                    vx, vy, vz = round(x * .55 * 4096 / 64), round(y * .70 * 4096 / 64), round(-16.4 * 4096 / 64)
                    commands.extend(((0x22, (0,)), (0x23, ((vx & 65535) | ((vy & 65535) << 16), vz & 65535))))
                additions += 1
        if op == 0x23:
            x, y = struct.unpack('<2h', struct.pack('<I', args[0]))
            args = ((round(x * .55) & 65535) | ((round(y * .70) & 65535) << 16), args[1])
        commands.append((op, args))
    if additions != (4 if opened else 0) or cavity_hits != int(opened):
        raise ValueError('Unexpected cargo model shape')
    return geometry.replace_streams([packets(commands)], vertices=w.u16(raw, geometry.model + 36) + additions * 4,
                                    quads=w.u16(raw, geometry.model + 38) + additions)


def freight_script(raw):
    """Use the upper or right-ground staging point, preserving the native crew callback."""
    obj = RoomObjects.parse(raw)
    for record in obj.records:
        for group in Events.parse(record.sections[1], record.raw[3]).groups:
            if any(command.opcode in (s.IF_VAR, s.INC_VAR, s.SET_VAR) and len(command.operand) >= 2
                   and struct.unpack_from('<H', command.operand)[0] == MODE for command in group.commands):
                raise ValueError('Freight route variable is already used')
    section = obj.records[0].sections[3]
    _, head, count = struct.unpack_from('<HBB', section)
    floors = [struct.unpack_from('<5i', section, head + 20 * i) for i in range(count)
              if struct.unpack_from('<i', section, head + 20 * i + 16)[0] == room_author.FLOOR]
    if not floors or any(row[2:4] != (0, 0) for row in floors):
        raise ValueError('Freight floor-anchor metadata differs')
    anchors = room_author.anchors(raw)
    if any((x, y, room_author.FLOOR) not in anchors for x, y in ((208, 42), (228, 42), (236, 2), (260, 2))):
        raise ValueError('Freight delivery anchors differ')
    batches = s.names(raw, 1)[2]
    if 'Lower Cargo Gate' in batches:
        raise ValueError('Freight already has a lower cargo gate')
    burst = batches.index('Cargo Burst')
    index = sum(s.counts(raw, 1)[0][:burst])
    entities = Entities.parse(obj.records[1].sections[0])
    burst_record = bytearray(entities.records[index])
    if (len(burst_record) != 28 or struct.unpack_from('<3iI2H', burst_record) !=
            (244 * drop.U, 22 * drop.U, 0, 4, 56, 30)):
        raise ValueError('Published Freight burst differs')
    struct.pack_into('<2H', burst_record, 16, 88, 72)
    raw = obj.replace_section(1, 0, entities.replace_record(index, burst_record))
    scoped = []
    for record in RoomObjects.parse(raw).records:
        for entity in Entities.parse(record.sections[0]).records:
            if len(entity) == 28 and struct.unpack_from('<3iI2H', entity) == (244 * drop.U, 22 * drop.U, 0, 4, 88, 72):
                scoped.append(entity)
    if len(scoped) != 1 or scoped[0] != bytes(burst_record):
        raise ValueError('Freight burst signature is not unique')
    originals = {}
    for name, x, y, old_y in (('Cargo Drop', UPPER_X, 60, 74), ('Cargo Drop Open', UPPER_X, 40, 0)):
        if batches.count(name) != 1:
            raise ValueError('Published Freight batch differs: ' + name)
        ag = batches.index(name)
        index = sum(s.counts(raw, 1)[0][:ag])
        obj = RoomObjects.parse(raw)
        entities = Entities.parse(obj.records[1].sections[0])
        old = entities.records[index]
        if len(entities.batches[ag].records) != 1 or len(old) != 28 or struct.unpack_from('<2i', old) != (244 * drop.U, old_y * drop.U):
            raise ValueError('Published Freight placement differs: ' + name)
        originals[name] = old
        changed = bytearray(old)
        struct.pack_into('<2i', changed, 0, x * drop.U, y * drop.U)
        raw = obj.replace_section(1, 0, entities.replace_record(index, changed))

    right = {}
    for name, y in (('Cargo Drop', 20), ('Cargo Drop Open', 0)):
        changed = bytearray(originals[name])
        struct.pack_into('<2i', changed, 0, LOWER_X * drop.U, y * drop.U)
        raw, right[name] = s.append_batch(raw, 1, [(bytes(changed), 'Object (Right ' + name + ')')], 'Right ' + name)

    first = s.counts(raw, 1)[1] + 1
    begin, land, rise, clear, stop = range(first, first + 5)
    batches = s.names(raw, 1)[2]
    gate, closed, crew, burst = (batches.index(n) for n in ('Cargo Drop Gate', 'Cargo Drop', 'Dock Crew', 'Cargo Burst'))
    trigger = s.trigger(244 * drop.U, 18 * drop.U, (8, 30), begin)
    raw, right_gate = s.append_batch(raw, 1, [(trigger, 'Trigger (Lower Cargo)')], 'Lower Cargo Gate')
    raw = s.extend_group(raw, 1, s.names(raw, 1)[1].index('Drop_Arm'), [s.activate(ag=right_gate)])
    raw = s.extend_group(raw, 1, 0, [s.set_var(MODE, 0)], prepend=True)

    def upper_begin(commands):
        found = [c for c in commands if c.opcode == 0x1c and struct.unpack_from('<H', c.operand)[0] == drop.LAND_FRAMES]
        if len(found) != 1:
            raise ValueError('Published Freight descent timing differs')
        return [s.deactivate(ag=right_gate)] + [Command(c.opcode, struct.pack('<H', LAND_FRAMES) + c.operand[2:])
                                                  if c is found[0] else c for c in commands]

    raw = ev.rewrite(raw, 1, 'Drop_Begin', upper_begin)
    raw = ev.rewrite(raw, 1, 'Drop_Land', lambda commands: (s.set_var(MODE, 1), *commands))
    raw = ev.rewrite(raw, 1, 'Drop_Burst_Stop', lambda commands: (s.set_var(MODE, 0), *commands))
    groups = (
        ('Right_Drop_Begin', (s.deactivate(ag=gate), s.deactivate(ag=right_gate), s.deactivate(ag=closed),
                              s.activate(ag=right['Cargo Drop']), s.set_var(drop.DROP, 1),
                              ev.sound(audio.IDS['hoist-tell']), s.activate(eg=land, frames=LAND_FRAMES))),
        ('Right_Drop_Land', (s.set_var(MODE, 2), ev.sound(audio.IDS['hoist-impact']), s.deactivate(ag=right['Cargo Drop']),
                             s.activate(ag=right['Cargo Drop Open']), ev.sound(audio.IDS['motor-open']), s.activate(ag=crew),
                             s.activate(ag=burst), s.activate(eg=stop, frames=drop.BURST_FRAMES),
                             s.activate(eg=rise, frames=drop.LIFT_FRAMES))),
        ('Right_Drop_Rise', (s.set_var(drop.DROP, 2), s.activate(eg=clear, frames=drop.CLEAR_FRAMES))),
        ('Right_Drop_Clear', (s.deactivate(ag=right['Cargo Drop Open']),)),
        ('Right_Drop_Burst_Stop', (s.set_var(MODE, 0), s.deactivate(ag=burst))),
    )
    raw, got = s.append_groups(raw, 1, [(EventGroup(commands), name) for name, commands in groups])
    if got != first:
        raise ValueError('Freight event group IDs moved')
    return raw


def height_adapter(at):
    """Adjust only Freight's upper scenery target; replay the overwritten stack load."""
    return crane_arm.assembled(f'''
        ldr r0,[r5]
        cmp r0,#97
        bne done
        ldr r0,[sp]
        ldr r1,lit0_upper_x
        cmp r0,r1
        addeq r7,r7,#0x28000
    done:
        ldr r0,[sp,#4]
        bx lr
lit0_upper_x: .word {UPPER_X * drop.U}
    ''', at)


def spawn_anchor_adapter(at):
    """Read an existing Freight floor point for the active burst; retain the native return ABI."""
    # Keep each native anchor's choice stable across the check and placement reads.
    return crane_arm.assembled('''
        push {r4-r7,r12,lr}
        mov r4,r0
        mov r5,r1
        bl 0x0203147c
        push {r0-r3}
        mrs r7,cpsr
        ldr r0,[sp,#0x224]
        ldr r1,lit0_return
        cmp r0,r1
        bne done
        ldr r6,[sp,#0x20c]
        ldr r0,lit1_ram_low
        cmp r6,r0
        blo done
        ldr r0,lit2_ram_high
        cmp r6,r0
        bhs done
        tst r6,#3
        bne done
        ldr r0,[r6]
        ldr r1,lit3_spawner
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x28]
        ldr r1,lit4_burst_x
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x2c]
        ldr r1,lit5_burst_y
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x30]
        ldr r1,lit12_burst_w
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x34]
        ldr r1,lit13_burst_h
        cmp r0,r1
        bne done
        ldr r0,[r5]
        ldrb r1,[r0,#0x10]
        cmp r1,#1
        bne done
        ldr r1,[r0,#8]
        cmp r1,#0
        bne done
        ldr r1,[r0,#12]
        cmp r1,#0
        bne done
        ldr r0,lit6_stats
        ldr r0,[r0]
        ldr r1,lit1_ram_low
        cmp r0,r1
        blo done
        ldr r1,lit2_ram_high
        cmp r0,r1
        bhs done
        tst r0,#3
        bne done
        ldr r0,[r0]
        cmp r0,#97
        bne done
        ldr r0,lit7_manager
        ldr r0,[r0]
        ldr r1,lit1_ram_low
        cmp r0,r1
        blo done
        ldr r1,lit14_manager_high
        cmp r0,r1
        bhs done
        ldrb r0,[r0,#0x1c5]
        cmp r0,#1
        beq upper
        cmp r0,#2
        bne done
        ldr r0,[r5]
        tst r0,#4
        ldreq r1,lit10_lower_x
        ldrne r1,lit15_lower_alt
        ldr r2,lit11_lower_y
        b selected
    upper:
        ldr r0,[r5]
        tst r0,#4
        ldreq r1,lit8_upper_x
        ldrne r1,lit16_upper_alt
        ldr r2,lit9_upper_y
    selected:
        str r1,[r4]
        str r2,[r4,#4]
    done:
        msr cpsr_f,r7
        pop {r0-r3}
        pop {r4-r7,r12,pc}
lit0_return: .word 0x0204c64c
lit1_ram_low: .word 0x02000000
lit2_ram_high: .word 0x023fffa8
lit3_spawner: .word 0x0212bda4
lit4_burst_x: .word 999424
lit5_burst_y: .word 90112
lit6_stats: .word 0x02145c5c
lit7_manager: .word 0x02145c34
lit8_upper_x: .word 933888
lit9_upper_y: .word 172032
lit10_lower_x: .word 1064960
lit11_lower_y: .word 8192
lit12_burst_w: .word 180224
lit13_burst_h: .word 147456
lit14_manager_high: .word 0x023ffe3a
lit15_lower_alt: .word 966656
lit16_upper_alt: .word 851968
    ''', at)


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Crane visibility requires exact published v0.39.0')
    names, blobs = assets.resources(rom)
    old_names, before = list(names), tuple(blobs)
    collision = RoomCollision.parse(blobs[names.index('zz_R21_AR_FreightExchange.bsp')])
    for x, y, floor in ((208, 42, 40), (228, 42, 40), (236, 2, 0), (260, 2, 0)):
        if collision.solid_at(x, y) is not None or collision.floor_below(x, y, 10) != floor:
            raise ValueError('Freight delivery floor is not clear')
    i = names.index(BALLAST_MODEL)
    blobs[i], texture = ballast_texture(blobs[i])
    blobs[names.index(OBJ)] = freight_script(blobs[names.index(OBJ)])
    from tools.qol_suits_menu import StringSlots
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native, _ = w.parse_glob(glob)
    for name in ('American.strings', 'English.strings'):
        i, j = names.index(name), native.index(name)
        raw = StringSlots(glob[offsets[j]:offsets[j + 1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = raw + bytes((len(before[i]) - len(raw)) % 4)

    extra = {}
    size = sum(map(len, blobs))
    for name, data in ((BALLAST_TEXTURE, texture), *((new, cargo_model(blobs[names.index(old)], opened=old == drop.MODELS[1]))
                                                     for old, new in zip(drop.MODELS, CARGO_MODELS))):
        if size % 4:
            pad = bytes(-size % 4)
            extra[f'zz_C40_align{len(extra)}.bin'] = pad
            size += len(pad)
        extra[name] = data
        size += len(data)
    names, blobs = oscorp_resources.append_resources(names, blobs, extra)
    i = names.index('model_sheet.xbd')
    sheet = ModelSheet.parse(blobs[i])
    if sheet.groups[GROUP][0] != names.index(BALLAST_MODEL) or sheet.groups[GROUP][2] != names.index('zz_F22_Atlas.nsbtx'):
        raise ValueError('Published Ballast model-sheet binding differs')
    changed = bytearray(blobs[i])
    struct.pack_into('<H', changed, sheet.start + GROUP * 6 + 4, names.index(BALLAST_TEXTURE))
    blobs[i] = bytes(changed)
    ModelSheet.parse(blobs[i])

    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
    rt = midnight_voltage.Runtime.__new__(midnight_voltage.Runtime)
    rt.rom, rt.header, rt.arm, rt.new = rom, h, arm, bytearray(arm)
    rt.end, rt.data = len(arm) - 36, bytearray()
    rt.start = kit.TARGET + rt.end - kit.SOURCE
    off = lambda a: kit.SOURCE + a - kit.TARGET
    if w.u32(arm, oscorp_resources.COUNT_OFFSET) != len(before):
        raise ValueError('Published resource count differs')
    struct.pack_into('<I', rt.new, oscorp_resources.COUNT_OFFSET, len(names))

    # Change only the Freight rows; other rooms retain the published records/models.
    at, found = off(WORLD), set()
    while w.u32(arm, at):
        room, kind, var, record_a, record_b = struct.unpack_from('<5I', arm, at)
        if room == 97 and kind in (drop.CLOSED, drop.OPEN):
            if kind in found or var != drop.DROP or record_a != record_b:
                raise ValueError('Published Freight world row differs')
            record = bytearray(arm[off(record_a):off(record_a) + 64])
            if w.u32(record, 0) != 0 or w.u32(record, 4) != 0xB6 or w.u32(record, 8) != old_names.index(drop.MODELS[kind == drop.OPEN]):
                raise ValueError('Published cargo model record differs')
            struct.pack_into('<I', record, 8, names.index(CARGO_MODELS[kind == drop.OPEN]))
            new_record = rt.alloc(record)
            struct.pack_into('<2I', rt.new, at + 12, new_record, new_record)
            found.add(kind)
        at += 20
    if found != {drop.CLOSED, drop.OPEN}:
        raise ValueError('Freight cargo rows missing')

    code = drop.drop_motion(MOTION, OLD_TICK, ROWS)
    if arm[off(MOTION):off(MOTION) + len(code)] != code:
        raise ValueError('Published cargo motion differs')
    needle = struct.pack('<I', 0xE59D0004)
    if code.count(needle) != 1:
        raise ValueError('Cargo motion stack load differs')
    motion_site = MOTION + code.index(needle)
    hook = rt.alloc()
    rt.data.extend(height_adapter(hook))
    struct.pack_into('<I', rt.new, off(motion_site), crane_row.branch(motion_site, hook, link=True))
    row = off(ROWS)
    if struct.unpack_from('<4i', arm, row) != (97, 74 * drop.U, 0, drop.RISE):
        raise ValueError('Published Freight motion row differs')
    struct.pack_into('<2i', rt.new, row + 4, 20 * drop.U, 0)
    if w.u32(arm, SPAWN_CALL - 0x02000000) != crane_row.branch(SPAWN_CALL, 0x02080620, link=True):
        raise ValueError('Published enemy spawn caller differs')
    if any(w.u32(arm, off(cfg) + 4) & 0x33 for cfg in CONFIGS):
        raise ValueError('Crane creature anchor-kind flags differ')
    anchor_hook = rt.alloc()
    rt.data.extend(spawn_anchor_adapter(anchor_hook))
    for site in ANCHOR_SITES:
        if w.u32(arm, site - 0x02000000) != crane_row.branch(site, ANCHOR_NATIVE, link=True):
            raise ValueError('Published spawn-anchor read differs')
        struct.pack_into('<I', rt.new, site - 0x02000000, crane_row.branch(site, anchor_hook, link=True))

    changed_names = [n for n, a, b in zip(old_names, before, blobs) if a != b]
    allowed = {BALLAST_MODEL, OBJ, 'American.strings', 'English.strings', 'GlobFiles.txt', 'model_sheet.xbd'}
    if set(changed_names) != allowed:
        raise ValueError('Unexpected Crane visibility resources: ' + str(set(changed_names) ^ allowed))
    result = rt.finish({'Glob.bin': w.pack_glob(names, blobs)})
    hh = w.parse_header(result)
    result_arm = result[hh['arm9_offset']:hh['arm9_offset'] + hh['arm9_size']]
    report = {'version': VERSION, 'parent_sha256': PARENT, 'rom_sha256': w.sha256(result),
              'arm9_sha256': w.sha256(result_arm), 'modified_resources': changed_names,
              'appended_resources': list(extra), 'height_hook': hook, 'motion_patch': motion_site, 'anchor_hook': anchor_hook,
              'anchor_sites': list(ANCHOR_SITES), 'route_var': MODE,
              'scope': 'Ballast private direct-color material and Freight-only cargo/guarded native burst floor anchors; native crew callback and collision retained'}
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v' + VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Crane visibility differs from its release pin')
    return result, report


def generate(output, source=PARENT_PATH):
    source, output = Path(source), Path(output)
    if not output.resolve().is_relative_to((ROOT / 'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output / 'Versioned.nds'
    validation = w.validate_rom(result, target=True)
    meta = json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'))
    glob = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(crane_visibility=report, release_version=VERSION, release_date=DATE,
                output_rom_sha256=w.sha256(result), output=str(path.resolve()), rom_size=len(result),
                used_rom_size=validation['header']['used_rom_size'], nitrofs=validation['nitrofs'],
                header_crc16=validation['header']['header_crc16'],
                output_glob_sha256=w.sha256(result[glob['start']:glob['end']]),
                verified_resource_count=len(assets.resources(result)[0]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT / 'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v' + VERSION, release_version=VERSION)
    w.write_json(output / 'gameplay_profile.json', recipe)
    w.write_json(output / 'changes.json', report)
    print(json.dumps({'path': str(path), 'sha256': report['rom_sha256']}), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    args = p.parse_args()
    generate(args.out, args.source)
