"""Exact v0.38.0 post-pass: Crane Row becomes a crane fight, cargo drops, a ring map and a harbour.

Act I keeps the published slam/sweep loop with no add, so the lanes are learned
alone. Act II (core at two thirds of its health) calls a Maw as backup. Act III
(a third) shortens every tell, chains a second slam onto wherever the player
dodged, and calls a second Maw from the left. Everything is the room's own
event script plus one HP-threshold wrapper; hoist HP, damage, collision, hook
motion and saved victory are the published ones.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, tasm_kit as kit, spider2099 as assets, midnight_voltage as extension
from tools import crane_drop as drop, oscorp_resources
from tools import midnight_rooms as mr, room_script as s, crane_boss, chapter_spectacle_events as ev
from tools import chapter_spectacle_audio as audio
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.chapter_renewal_combat import asm
from tools.crane_row import target, branch
from tools.room_events import Command, EventGroup
from tools.room_objects import RoomObjects
from tools.room_events import Events

PARENT = '21c7a05140a4ac17bf1061f5336c53e9a7480e8152c2797243329bd8799643ca'
PARENT_PATH = ROOT/'build/version-0.38.0-final/Versioned.nds'
VERSION, DATE = '0.39.0', '2026-10-28'
ROOM, OBJ = 106, 'zz_AR_LongArm_app.obj'
PHASE, WAVE_A, WAVE_B, CHAIN = ev.HOIST_PHASE, 0x12D, 0x12E, 0x130
HALF_HP, FURY_HP = 0x18000, 0xC000   # core health (Q12, 36 units full) at Acts II and III; the published marker is 0x12000
STEADY_TELL, FURY_TELL = 0x30, 28
CALL_FRAMES = 30         # a backup spawner stays live this long: about one arrival
CREW_AG = 12             # the published start crew's spawner batch (0-based)
BASE = 0x02000000


def assembled(text, at):
    code = asm(text, at)
    errors = literal_errors(code, text)+native_branch_errors(code, text, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Long Arm assembly: '+str(errors))
    return code


def fury_phase(at, old, cells):
    """Mirror real core health into the meter cells and mark Act III; chains after the published marker."""
    return assembled(f'''
        push {{r4-r7,r12,lr}}
        mov r4,r0
        ldr r5,[r4]
        bl 0x{old:08x}
        push {{r0-r3}}
        mrs r7,cpsr
        ldr r0,lit0_stats
        ldr r0,[r0]
        cmp r0,#0
        beq done
        ldr r0,[r0]
        cmp r0,#{ROOM}
        bne done
        ldr r0,[r4]
        cmp r0,r5
        bne done
        ldr r0,[r4,#0x10c]
        cmp r0,#0x21
        bne done
        ldr r0,[r4,#0x110]
        cmp r0,#0
        movlt r0,#0
        ldr r1,lit2_cells
        str r0,[r1,#0x44]
        cmp r0,#0
        ble done
        cmp r0,#0x{FURY_HP:x}
        bgt done
        ldr r1,lit1_manager
        ldr r1,[r1]
        cmp r1,#0
        movne r0,#2
        strbne r0,[r1,#0x1c8]
    done:
        msr cpsr_f,r7
        pop {{r0-r3}}
        pop {{r4-r7,r12,pc}}
lit0_stats: .word 0x02145c5c
lit1_manager: .word 0x02145c34
lit2_cells: .word 0x{cells:x}
    ''', at)


def hoist_resolver(at, old, cells):
    """The native boss meter's boss finder: the running Long Arm first, otherwise the published Conductor finder."""
    return assembled(f'''
        ldr r1,lit0_stats
        ldr r1,[r1]
        cmp r1,#0
        beq elsewhere
        ldr r1,[r1]
        cmp r1,#{ROOM}
        bne elsewhere
        ldr r1,lit1_manager
        ldr r1,[r1]
        cmp r1,#0
        beq elsewhere
        ldrb r2,[r1,#0x1c0]
        ldr r0,lit2_cells
        cmp r2,#1
        bxeq lr
        ldr r2,[r0,#0x48]
        str r2,[r0,#0x44]
    elsewhere:
        b 0x{old:08x}
lit0_stats: .word 0x02145c5c
lit1_manager: .word 0x02145c34
lit2_cells: .word 0x{cells:x}
    ''', at)


def commands(raw, name):
    rec = RoomObjects.parse(raw).records[1]
    return Events.parse(rec.sections[1], rec.raw[3]).groups[ev.group_index(raw, 1, name)].commands


def retime(group, old, new):
    return tuple(Command(c.opcode, struct.pack('<H', new)+c.operand[2:])
                 if c.opcode == 0x1C and struct.unpack_from('<H', c.operand)[0] == old else c for c in group)


def script(raw, blob):
    """The published Long Arm room script with its three acts; every new entry point is a guarded published one."""
    sounds = audio.IDS
    nxt, rec = ev.group_index(raw, 1, 'Next')+1, ev.group_index(raw, 1, 'Recover')+1
    # Act III tell: the same lane warning, shorter, for all three lanes and the sweep.
    for name in ('Warn0_Go', 'Warn1_Go', 'Warn2_Go', 'Sweep_Warn_Go'):
        steady = retime(commands(raw, name+'_Steady'), STEADY_TELL, FURY_TELL)
        if steady == commands(raw, name+'_Steady'):raise ValueError('Published tell timing differs: '+name)
        raw, fury = s.append_groups(raw, 1, [(EventGroup(steady), name+'_Fury')])
        raw, calm = s.append_groups(raw, 1, [(EventGroup(commands(raw, name)), name+'_Calm')])
        raw = ev.rewrite(raw, 1, name, lambda _, f=fury, c=calm: (
            s.if_var(PHASE, '==', 2, then=s.action(eg=f), otherwise=s.action(eg=c)),))
    # A slam in Act III is followed by a second tell on the player's new lane, once per opening.
    raw, again = s.append_groups(raw, 1, [(EventGroup((s.set_var(CHAIN, 1), s.activate(eg=nxt, frames=8))), 'Fury_Again')])
    raw, gate = s.append_groups(raw, 1, [(EventGroup((s.if_var(
        CHAIN, '==', 0, then=s.action(eg=again), otherwise=s.action(eg=rec)),)), 'Fury_Gate')])
    raw, after = s.append_groups(raw, 1, [(EventGroup((s.if_var(
        PHASE, '==', 2, then=s.action(eg=gate), otherwise=s.action(eg=rec)),)), 'Slam_Aftermath')])
    for i in range(3):
        def aftermath(group, i=i):
            last = group[-1]
            if last.opcode != 0x1C or struct.unpack_from('<H', last.operand)[0] != 18 or last.operand[5] != rec:
                raise ValueError(f'Published Hit{i} recovery call differs')
            return (*group[:-1], s.activate(eg=after, frames=18))
        raw = ev.rewrite(raw, 1, f'Hit{i}_Go', aftermath)
    # Act I teaches the lanes alone: the published start add is withdrawn, and
    # each later act brings its backup instead.
    start = ev.group_index(raw, 1, 'Start')
    raw, dropped = s.drop_commands(raw, 1, lambda g, c: g == start and c.opcode == 0x1C
                                   and c.operand[:2] == bytes(2) and c.operand[4] == CREW_AG+1)
    if len(dropped) != 1:raise ValueError('Published start crew call differs')
    # One backup call per act, from the opening that follows its health threshold.
    calls = []
    for label, var, gang in (('Backup', WAVE_A, mr.Gang('Pier_Map04', 8, (344, 12), (80, 38), 'Hoist Backup')),
                             ('Reserve', WAVE_B, mr.Gang('Pier_Map04', 8, (296, 12), (70, 38), 'Hoist Reserve'))):
        raw, ag = s.append_batch(raw, 1, [(mr._spawner(blob, gang), 'EnemySpawner ('+gang.label+')')], gang.label)
        raw, stop = s.append_groups(raw, 1, [(EventGroup((s.deactivate(ag=ag),)), label+'_Stop')])
        raw, call = s.append_groups(raw, 1, [(EventGroup((s.set_var(var, 1), ev.sound(sounds['hoist-impact']),
            s.activate(ag=ag), s.activate(eg=stop, frames=CALL_FRAMES))), label+'_Call')])
        calls.append(call)
    raw, reserve = s.append_groups(raw, 1, [(EventGroup((s.if_var(
        WAVE_B, '==', 0, then=s.action(eg=calls[1])),)), 'Reserve_Check')])
    openings = (s.if_var(WAVE_A, '==', 0, then=s.action(eg=calls[0])),
                s.if_var(PHASE, '==', 2, then=s.action(eg=reserve)))
    raw = ev.rewrite(raw, 1, 'Motor_Open_Steady', lambda g: (s.set_var(CHAIN, 0), *g))
    raw = ev.rewrite(raw, 1, 'Motor_Open_Damaged', lambda g: (s.set_var(CHAIN, 0), *g, *openings))
    return s.extend_group(raw, 1, 0, [s.set_var(v, 0) for v in (WAVE_A, WAVE_B, CHAIN)], prepend=True)


def apply_rom(rom, *, meter=True, parent_meta=None, compose=True):
    """Exact v0.38.0 only. `parent_meta` is the build log of the passes before this one (`mod.create_build`
    supplies it); without it the published parent's build json is read. `compose` then applies the
    chainable room-scenery and map passes (crane_vista, crane_map) to the finished ROM."""
    from tools import release_info
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    if w.sha256(rom) != PARENT:
        raise ValueError('Crane Row requires exact published v0.38.0')
    if w.sha256(arm) != release_info.PROFILE_INFO['tasm-v0.38.0']['arm9_sha256']:
        raise ValueError('Published parent ARM9 differs')
    meta = parent_meta or json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    sr = meta['chapter_spectacle']['scripted_runtime']
    names, blobs = assets.resources(rom)
    base_names, before = list(names), tuple(blobs)
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    native = lambda name: glob[offsets[native_names.index(name)]:offsets[native_names.index(name)+1]]
    i = names.index(OBJ)
    raw = script(before[i], native)
    blobs[i] = raw+bytes(-len(raw) % 4)
    from tools.qol_suits_menu import StringSlots
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    # The Freight, Dry Dock and Crown crews arrive by crane: three room scripts and two appended models.
    for room, cfg in drop.ROOMS.items():
        i = names.index(f'zz_{cfg[0]}_app.obj')
        raw = drop.script(before[i], room, native)
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    extras = drop.models()
    if sum(map(len, blobs)) % 4:
        extras = {'zz_CD38_align.bin': bytes(-sum(map(len, blobs)) % 4), **extras}
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    names, blobs = oscorp_resources.append_resources(names, blobs, extras)
    rt = extension.Runtime.__new__(extension.Runtime)
    rt.rom, rt.header, rt.arm, rt.new = rom, h, arm, bytearray(arm)
    rt.end, rt.data = len(arm)-36, bytearray()
    rt.start = kit.TARGET+rt.end-kit.SOURCE
    off = lambda address: kit.SOURCE+address-kit.TARGET if address >= kit.TARGET else address-BASE
    # Act III marker, chained after the published half-health marker.
    site = crane_boss.HP_SITE
    old = target(site, w.u32(arm, site-BASE))
    if old != sr['core_hp']:raise ValueError('Published core health hook differs')
    # The published marker raises the second act at half health; move it to two thirds.
    first, second = asm('cmp r0,#0x12000', 0), asm(f'cmp r0,#0x{HALF_HP:x}', 0)
    body = bytes(arm[off(old):off(old)+160])
    if body.count(first) != 1 or body.index(first) % 4:raise ValueError('Published half-health marker differs')
    rt.new[off(old)+body.index(first):off(old)+body.index(first)+4] = second
    cells = rt.alloc(bytes(0x4C))
    struct.pack_into('<2I', rt.data, cells-rt.start+0x44, crane_boss.HEALTH, crane_boss.HEALTH)
    entry = rt.alloc()
    code = fury_phase(entry, old, cells)
    rt.data.extend(code)
    rt.hook(site, entry)
    if meter:
        # The native boss meter finds its boss at two published call sites; the Long Arm answers first.
        hud = meta['midnight_encore']['runtime']
        resolver = rt.alloc()
        rt.data.extend(hoist_resolver(resolver, hud['resolver'], cells))
        for site_name, hook_site in (('hud', 0x020e0ae8), ('meter', 0x020e77b4)):
            if target(hook_site, w.u32(arm, hook_site-BASE)) != hud[site_name]:raise ValueError('Published boss meter hook differs')
            call = hud[site_name]+8
            if target(call, w.u32(arm, off(call))) != hud['resolver'] or w.u32(arm, off(call)) >> 24 != 0xEB:
                raise ValueError('Published boss finder call differs')
            struct.pack_into('<I', rt.new, off(call), branch(call, resolver, link=True))
    # The published hoist budget admits one Maw at a time and nothing more; give it the existing
    # three-total/two-live pair so a backup can arrive while the first is still alive.
    goals = sr['goal_table']
    row = next(r for r in range(40) if w.u32(arm, off(goals)+20*r) == ROOM)
    one_one, two_live = w.u32(arm, off(goals)+20*row+4), w.u32(arm, off(goals)+20*row+8)
    if one_one == two_live:raise ValueError('Published hoist budget differs')
    struct.pack_into('<I', rt.new, off(goals)+20*row+4, two_live)
    # Container models join the published world-object table; the hook moves them on the published tick.
    wd, wt = sr['world_data'], sr['world_table']
    rows, at = [], off(wt)
    while w.u32(arm, at):
        rows.append(bytes(arm[at:at+20]));at += 20
    template = bytes(arm[off(struct.unpack_from('<I', rows[0], 12)[0]):][:64])
    if w.u32(template, 0) or w.u32(template, 4) != 0xB6:raise ValueError('Published harmless world record differs')
    def record(name):
        raw = bytearray(template);struct.pack_into('<I', raw, 8, names.index(name));return rt.alloc(bytes(raw))
    closed, opened = (record(n) for n in drop.MODELS)
    new_table = rt.alloc(b''.join(rows)+drop.world_rows(sorted(drop.ROOMS), closed, opened)+bytes(20))
    adapter = bytes(arm[off(wd):off(wd)+0x100])
    hits = [i for i in range(0, 0xFC, 4) if adapter[i:i+4] == struct.pack('<I', wt)]
    if len(hits) != 1:raise ValueError('Published world-data table literal differs')
    struct.pack_into('<I', rt.new, off(wd)+hits[0], new_table)
    tick = crane_boss.TICK_SITE
    if w.u32(arm, tick-BASE) >> 24 != 0xEA:raise ValueError('Published hook tick differs')
    rows_at = rt.alloc(drop.table())
    entry_drop = rt.alloc()
    rt.data.extend(drop.drop_motion(entry_drop, target(tick, w.u32(arm, tick-BASE)), rows_at))
    rt.hook(tick, entry_drop)
    if w.u32(arm, oscorp_resources.COUNT_OFFSET) != len(before):raise ValueError('Published resource count differs')
    struct.pack_into('<I', rt.new, oscorp_resources.COUNT_OFFSET, len(names))
    result = rt.finish()
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(result) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    hh = w.parse_header(result)
    if growth > 0:
        if hh['used_rom_size']+growth > len(result) or any(x not in (0, 255) for x in result[-growth:]):
            raise ValueError('Insufficient verified cart padding')
        staged = bytearray(result[:ge['end']]+bytes(growth)+result[ge['end']:-growth])
        for e in w.nitrofs_entries(result):
            if e['start'] >= ge['end']:
                struct.pack_into('<2I', staged, hh['fat_offset']+e['id']*8, e['start']+growth, e['end']+growth)
        struct.pack_into('<I', staged, 0x80, hh['used_rom_size']+growth)
        struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
        result = bytes(staged)
    result = w.rebuild_rom(result, {'Glob.bin': packed})
    w.validate_rom(result, target=True)
    hh = w.parse_header(result)
    new_arm = result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]
    changed += ['GlobFiles.txt']
    expected = {OBJ, 'American.strings', 'English.strings', 'GlobFiles.txt', *(f'zz_{cfg[0]}_app.obj' for cfg in drop.ROOMS.values())}
    if set(changed) != expected:
        raise ValueError('Unexpected Crane Row resource scope: '+str(sorted(set(changed) ^ expected)))
    report = dict(version=VERSION, parent_sha256=w.sha256(rom), rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new_arm),
        modified_resources=changed, nitrofs_relocation_bytes=max(growth, 0),
        runtime=dict(fury_hook=entry, meter_cells=cells, boss_finder=resolver if meter else None, fury_old=old, half_hp_q12=HALF_HP, fury_hp_q12=FURY_HP, bytes=len(code)),
        script=dict(phase_var=PHASE, wave_vars=(WAVE_A, WAVE_B), chain_var=CHAIN, fury_tell_frames=FURY_TELL),
        cargo_drop=dict(rooms=sorted(drop.ROOMS), appended_resources=list(extras), motion_hook=entry_drop, rows=rows_at,
                        world_table=new_table, closed_record=closed, open_record=opened, drop_var=drop.DROP,
                        land_frames=drop.LAND_FRAMES, lift_frames=drop.LIFT_FRAMES),
        player_kit_32k_unchanged=True)
    if compose:
        # Both passes find their targets by structure and expect the finished ROM, so they run last.
        from tools import crane_vista, crane_map
        mine = report['rom_sha256']
        result, vista_report = crane_vista.apply_rom(result)
        result, map_report = crane_map.apply_rom(result)
        hh = w.parse_header(result)
        names_now, blobs_now = assets.resources(result)
        now = dict(zip(names_now, blobs_now))
        everything = {n for n, a in zip(base_names, before) if now[n] != a}
        allowed = expected | {crane_vista.MODEL, crane_vista.TEXTURE, *crane_map.nav.SCREENS}
        if not everything <= allowed:
            raise ValueError('Unexpected composed resource scope: '+str(sorted(everything-allowed)))
        report.update(rom_sha256=w.sha256(result), arm9_sha256=w.sha256(result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]),
                      modified_resources=sorted(everything), nitrofs_relocation_bytes=report['nitrofs_relocation_bytes']
                      +vista_report['nitrofs_relocation_bytes']+map_report['nitrofs_relocation_bytes'],
                      composed=dict(crane_arm_rom_sha256=mine, vista=vista_report, map=map_report))
    # Only the release composition is pinned (once its pins exist); --bare and --no-meter are candidate experiments.
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin.get('crane_arm') and meter and compose and pin[key] != report[key]:
            raise ValueError('Crane Row build differs from its immutable release pin')
    return result, report


def generate(output, source_path=PARENT_PATH, meter=True, compose=True):
    output, source_path = Path(output), Path(source_path)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source_path.read_bytes(), meter=meter, compose=compose)
    path = output/'Versioned.nds'
    validation = w.validate_rom(result, target=True)
    meta = json.loads(source_path.with_suffix('.build.json').read_text(encoding='utf-8'))
    ge = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(crane_arm=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
        output=str(path.resolve()), rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
        nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
        output_glob_sha256=w.sha256(result[ge['start']:ge['end']]), verified_resource_count=len(assets.resources(result)[0]))
    w.atomic_write(path, result, sources=(source_path,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v'+VERSION, release_version=VERSION)
    w.write_json(output/'gameplay_profile.json', recipe)
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'], runtime=report['runtime'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    p.add_argument('--no-meter', action='store_true', help='Leave the native boss meter and its shared finder untouched')
    p.add_argument('--bare', action='store_true', help='Skip the chained vista and map passes (hoist and cargo drops only)')
    a = p.parse_args()
    generate(a.out, a.source, not a.no_meter, not a.bare)
