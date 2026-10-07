"""Midnight Line chapter build: five appended rooms reached by a native door.

Production post-pass over a kit ROM (stable v0.5.0 for development). Nothing
here runs in disposable RAM: the room table, descriptors, rooms, textures and
the entrance are stored in the ROM. See TECHNICAL "Midnight Line chapter build".

Rooms 76..80 are sanitized clones of the native subway section of the sewers:
record 0 (Spidey, exits, camera, ambience) is kept with exits retargeted and
story writes removed; record 1 (story state, enemies, pickups) is replaced by
the empty native Test_Surfaces01 state record plus a visited flag. Textures get
a palette grade. Sewer_Save02 gains a right-wall doorway and a return spawn.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import room_catalog, room_doors, tasm_kit as kit, wos_tool as w
from tools.nitro_texture import TextureArchive
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects

BASE = 0x02000000
ML_BASE = kit.TARGET + kit.RESERVE          # 02155420, after the kit's reserve
ML_SPACE = 0x800                            # autoloaded; main arena starts after it
FIRST = room_catalog.COUNT + 1              # 75 stays the native invalid sentinel
LOOKUP_LITERAL = 0x02084AC8                 # literal of lookup 0x02084AB4
SAVE_ROOM_CHECK = 0x02085720                # cmp r1,#75 in saved-block validation
RELOAD_ROOM_CHECK = 0x020D64B8              # cmp r1,#75 in current-room reload
CMP_R1 = 0xE3510000
GLOB_COUNT = 0x77F8                         # ARM9 Glob resource count
VISITED_BASE = 0xB0                         # native rule: room r sets flag 0xB0+r
FLAG_LIMIT = 0x123                          # flags 0..0x122; higher ids are scalars
FREE_FLAGS = range(251, 276)                # no event/code reference, unset in 62 saves
# Chapter allocation: 252..256 visited (0xB0 + room, the native rule);
# 257..259 milestones; 260..267 puzzle state; 268..275 remapped room-local
# flags of cloned encounters. 251 stays unassigned.
MILESTONE_FLAGS = {'main_power_restored': 257, 'completed': 258, 'teaser_seen': 259}
LOCAL_FLAGS = range(268, 276)
SET_VAR, INC_VAR, DEC_VAR, IF_VAR = 0x26, 0x25, 0x24, 0x1D
MESSAGE = 0x15
STABLE_SHA256 = 'fd7e4420f97645dd55011504843ce62f068d1276234c3cd781931c85bb1eb193'
ARM9_SHA256 = 'efab33e0f8154f6ad76fcf453c70d9d7146165b83e04ee1d4ea2cfd6b1b7b621'   # chapter over the kit ARM9
ENTRANCE = 'Sewer_Save02'
STATE_TEMPLATE = 'Test_Surfaces01'


@dataclass(frozen=True)
class Room:
    index: int
    name: str
    source: str
    grade: str
    encounters: bool      # keep the source's sanitized record 1 (spawners, ambush)


ROOMS = (
    Room(76, 'ML_Platform', 'Sewer_Map03', 'midnight', False),   # tracks: quiet arrival
    Room(77, 'ML_Refuge', 'Sewer_Save03', 'emergency', False),   # combat-free save room
    Room(78, 'ML_Service', 'Sewer_Map02', 'midnight', True),     # station: ambush
    Room(79, 'ML_Switching', 'Sewer_Map13', 'midnight', True),   # stairs: three spawners
    Room(80, 'ML_Gallery', 'Sewer_Map01', 'midnight', True),     # upper route: mini-boss
)
BY_NAME = {r.name: r for r in ROOMS}
# (room, record-0 exit group) -> (destination, spawn id). A spawn is the arrival
# point beside the door that leads back. Arrival facing right means that door
# is on the left; links join right-side exits to left-side arrivals so a held
# direction carries Spidey into the room instead of straight back out.
# Loop: Platform -> Service -> Switching -> Gallery -> Platform alcove;
# the Refuge is up the Platform's top-right stairs. Gallery group 3 is an
# overhead exit, the one left-to-left pairing.
LINKS = {
    ('ML_Platform', 1): (ENTRANCE, 2),
    ('ML_Platform', 2): ('ML_Service', 1), ('ML_Service', 1): ('ML_Platform', 2),
    ('ML_Platform', 3): ('ML_Gallery', 2), ('ML_Gallery', 1): ('ML_Platform', 3),
    ('ML_Platform', 4): ('ML_Refuge', 1), ('ML_Refuge', 1): ('ML_Platform', 5),
    ('ML_Service', 2): ('ML_Switching', 1), ('ML_Switching', 1): ('ML_Service', 2),
    ('ML_Switching', 3): ('ML_Gallery', 3), ('ML_Gallery', 2): ('ML_Switching', 3),
    ('ML_Switching', 2): ('ML_Gallery', 1), ('ML_Gallery', 3): ('ML_Switching', 2),
}
# Lab route that takes every directed link exactly once, entrance to exit.
TOUR = ((ENTRANCE, 2), ('ML_Platform', 2), ('ML_Service', 2), ('ML_Switching', 3), ('ML_Gallery', 1),
        ('ML_Platform', 4), ('ML_Refuge', 1), ('ML_Platform', 3), ('ML_Gallery', 3), ('ML_Switching', 2),
        ('ML_Gallery', 2), ('ML_Switching', 1), ('ML_Service', 1), ('ML_Platform', 1))
# Sewer_Save02: right wall reaches x=56.47; mirrors the native left exit.
ENTRANCE_DOOR = {'center': (61 * 4096, 4 * 4096, 0), 'size': (12, 24), 'spawn': 1,
                 'trigger_name': 'Trigger (Main|Exit_Midnight)', 'group_name': 'Exit_Midnight_Line'}
RETURN_SPAWN = {'spawn_id': 2, 'xyz': (44 * 4096, 2 * 4096, 0), 'facing': 'left'}
# Unreachable placement for pickups that must not be duplicated.
REMOVED_PICKUP_Y = -4000 * 4096
PICKUP_TYPE = 13
GRADES = {   # (desaturation, (r, g, b) gain, lift in 5-bit units)
    'midnight': (0.55, (0.42, 0.58, 0.82), (0.0, 0.3, 0.9)),
    'emergency': (0.45, (0.85, 0.60, 0.36), (0.6, 0.2, 0.0)),
}


def grade_palette(raw, grade):
    desat, gain, lift = GRADES[grade]
    out = bytearray(raw)
    for i in range(0, len(raw) - 1, 2):
        c = struct.unpack_from('<H', raw, i)[0]
        rgb = (c & 31, (c >> 5) & 31, (c >> 10) & 31)
        luma = 0.30 * rgb[0] + 0.59 * rgb[1] + 0.11 * rgb[2]
        new = [min(31, max(0, round((v + (luma - v) * desat) * g + l)))
               for v, g, l in zip(rgb, gain, lift)]
        struct.pack_into('<H', out, i, (c & 0x8000) | new[0] | new[1] << 5 | new[2] << 10)
    return bytes(out)


def graded_textures(raw, grade):
    archive = TextureArchive.parse(raw)
    palette = raw[archive.palette_start:archive.palette_start + archive.palette_size]
    return archive.replace_palette(grade_palette(palette, grade))


def _var_target(var, room, source_index, local):
    """Map a source variable into the chapter, or None for a native scalar.

    Visited flags follow the native 0xB0+room rule. Any other flag becomes a
    chapter-private flag (LOCAL_FLAGS, allocated in first-use order), so cloned
    ambushes persist without touching native progress. Ids >= 0x123 are
    mission/difficulty scalars and ability bits: callers drop writes to them.
    """
    if var == VISITED_BASE + source_index: return VISITED_BASE + room.index
    if var >= FLAG_LIMIT: return None
    if local is None: raise ValueError(f'{room.name}: unexpected story flag {var:#x} in record 0')
    if (room.name, var) not in local:
        used = set(local.values())
        free = [f for f in LOCAL_FLAGS if f not in used]
        if not free: raise ValueError('Chapter local flags exhausted')
        local[(room.name, var)] = free[0]
    return local[(room.name, var)]


def sanitize(events, room, source_index, names, local=None):
    """Retarget exits; drop messages and every write outside the chapter flags."""
    groups, dropped = [], []
    for g, group in enumerate(events.groups):
        commands = []
        for command in group.commands:
            op, operand = command.opcode, command.operand
            if op == room_doors.GO_TO_ROOM:
                if local is not None: raise ValueError(f'{room.name}: exit outside record 0')
                if (room.name, g) not in LINKS: raise ValueError(f'{room.name} exit group {g} has no link')
                dest, spawn = LINKS[(room.name, g)]
                index = BY_NAME[dest].index if dest in BY_NAME else names.index(dest)
                commands.append(Command(op, bytes([index, 1, spawn]) + operand[3:]))
            elif op == MESSAGE:
                dropped.append((g, op))
            elif op in (SET_VAR, INC_VAR, DEC_VAR, IF_VAR):
                target = _var_target(struct.unpack_from('<H', operand)[0], room, source_index, local)
                if target is not None:
                    commands.append(Command(op, struct.pack('<H', target) + operand[2:]))
                elif op == IF_VAR:
                    commands.append(command)      # reading native scalars is harmless
                else:
                    dropped.append((g, op))
            else:
                commands.append(command)
        groups.append(EventGroup(tuple(commands)))
    count = 2 * len(groups) + sum(1 + len(x.commands) for x in groups)
    return Events(tuple(groups), bytes(-count % 4)), dropped


def state_record(template_raw, room):
    """Empty native state record whose init group marks the room visited."""
    parsed = RoomObjects.parse(template_raw)
    record, names = parsed.records[1], parsed.names[1]
    if Entities.parse(record.sections[0]).records or record.raw[3] != 1 or names.category_ends[:2] != (0, 1):
        raise ValueError('State template changed')
    flag = VISITED_BASE + room.index
    if flag not in FREE_FLAGS: raise ValueError('Visited flag outside the chapter allocation')
    events = Events((EventGroup((Command(SET_VAR, struct.pack('<HBB', flag, 1, 0)),)),), b'')
    return record.replace_section(1, events.to_bytes()), names.raw


def _hide_pickups(section0):
    """Move upgrade orbs out of reach: a clone must not grant a second upgrade."""
    moved = []
    for i, entity in enumerate(Entities.parse(section0).records):
        if struct.unpack_from('<I', entity, 12)[0] == PICKUP_TYPE:
            changed = bytearray(entity)
            struct.pack_into('<i', changed, 4, REMOVED_PICKUP_Y)
            section0 = Entities.parse(section0).replace_record(i, bytes(changed))
            moved.append(i)
    return section0, moved


def build_room(source_obj, template_raw, room, source_index, names, local):
    """Record 0 sanitized; record 1 sanitized (encounters) or the empty state record."""
    parsed = RoomObjects.parse(source_obj)
    if len(parsed.records) != 2: raise ValueError(f'{room.source}: expected two records')
    result, report = source_obj, {}
    for r in range(2 if room.encounters else 1):
        record = RoomObjects.parse(result).records[r]
        events, dropped = sanitize(Events.parse(record.sections[1], record.raw[3]), room, source_index,
                                   names, local if r else None)
        section0, moved = _hide_pickups(record.sections[0])
        result = RoomObjects.parse(result).replace_section(r, 0, section0)
        result = RoomObjects.parse(result).replace_section(r, 1, events.to_bytes())
        report[f'record{r}'] = {'dropped_commands': dropped, 'moved_pickups': moved}
    if not room.encounters:
        base = RoomObjects.parse(result)
        state, state_names = state_record(template_raw, room)
        header = bytearray(base.header)
        end = len(header) + len(base.records[0].raw) + len(state)
        struct.pack_into('<2I', header, 4, end, end + len(base.between))
        result = bytes(header) + base.records[0].raw + state + base.between + base.names[0].raw + state_names
        report['record1'] = 'empty state record'
    RoomObjects.parse(result)
    return result, report


def entrance_obj(raw, names):
    platform = BY_NAME['ML_Platform']
    door = dict(ENTRANCE_DOOR)
    spawn = door.pop('spawn')
    result = room_doors.add_exit(raw, room=platform.index, selector=1, spawn=spawn, **door)
    return room_doors.add_spawn(result, **RETURN_SPAWN)


def room_table(arm9, names, resources):
    """Extended lookup + descriptors + model arrays + names at ML_BASE."""
    native = room_catalog.parse(arm9, names)
    by_name = {r.name: r for r in native}
    descriptors_at = ML_BASE + 4 * (FIRST + len(ROOMS))
    models_at = descriptors_at + room_catalog.SIZE * len(ROOMS)
    labels_at = models_at + 4 * len(ROOMS)
    lookup = [r.address for r in native] + [0]
    descriptors, models, labels = bytearray(), bytearray(), bytearray()
    for i, room in enumerate(ROOMS):
        if room.index != FIRST + i: raise ValueError('Chapter rooms must be contiguous')
        source = by_name[room.source]
        raw = bytearray(source.raw)
        count, model_array = struct.unpack_from('<I', raw, 0x10)[0], struct.unpack_from('<I', raw, 0x20)[0]
        if count != 1: raise ValueError(f'{room.source}: expected one room model')
        model = struct.unpack_from('<I', arm9, model_array - BASE)[0]
        if not names[model].endswith('.nsbmd'): raise ValueError('Model array mismatch')
        struct.pack_into('<4I', raw, 0, labels_at + len(labels), resources[room.name]['texture'],
                         source.bsp, resources[room.name]['objects'])
        struct.pack_into('<I', raw, 0x20, models_at + len(models))
        models += struct.pack('<I', model)
        labels += room.name.encode('ascii') + b'\0'
        lookup.append(descriptors_at + len(descriptors))
        descriptors += raw
    data = struct.pack(f'<{len(lookup)}I', *lookup) + descriptors + models + labels
    data += bytes(-len(data) % 4)
    if len(data) > ML_SPACE: raise ValueError('Chapter tables exceed reserved space')
    return data + bytes(ML_SPACE - len(data))




def extend_arm9(rom, table, glob_count, *, save_rooms=True):
    """Grow the kit autoload by ML_SPACE, redirect the room lookup, count appended resources."""
    h = w.parse_header(rom)
    raw = rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
    if w.sha256(raw) != kit.ARM9_SHA256: raise ValueError('Chapter requires the pinned kit ARM9')
    table_at = kit.SOURCE + kit.IMAGE
    if (struct.unpack_from('<3I', raw, table_at + 24) != (kit.TARGET, kit.IMAGE, 0)
            or w.u32(raw, kit.ARENA_LOWER) != kit.TARGET + kit.RESERVE or len(raw) != table_at + 36):
        raise ValueError('Unexpected kit autoload layout')
    image = raw[kit.SOURCE:table_at] + bytes(kit.RESERVE - kit.IMAGE) + table
    new = bytearray(raw[:kit.SOURCE] + image + raw[table_at:table_at + 24]
                    + struct.pack('<3I', kit.TARGET, len(image), 0))
    new_table = kit.SOURCE + len(image)
    struct.pack_into('<2I', new, kit.TABLE_POINTERS, BASE + new_table, BASE + new_table + 36)
    struct.pack_into('<I', new, kit.ARENA_LOWER, kit.TARGET + len(image))
    patches = [(BASE + GLOB_COUNT, *glob_count), (LOOKUP_LITERAL, room_catalog.LOOKUP, ML_BASE)]
    if save_rooms:
        limit = FIRST + len(ROOMS)
        patches += [(SAVE_ROOM_CHECK, CMP_R1 | 0x4B, CMP_R1 | limit),
                    (RELOAD_ROOM_CHECK, CMP_R1 | 0x4B, CMP_R1 | limit)]
    for address, old, value in patches:
        if w.u32(new, address - BASE) != old: raise ValueError(f'Patch site differs: {address:08X}')
        struct.pack_into('<I', new, address - BASE, value)
    return kit.replace_arm9(rom, bytes(new))[0], patches


def apply_rom(rom, *, save_rooms=True):
    """Chapter stage over a kit ROM; returns (rom, report). Sources must be clean natives."""
    from tools import oscorp_resources
    import mod
    fs = next(e for e in w.validate_rom(rom, target=True)['nitrofs'] if e['name'] == 'Glob.bin')
    glob = rom[fs['start']:fs['end']]
    offsets, names, table_index = w.parse_glob(glob)
    originals = [glob[a:z] for a, z in zip(offsets, offsets[1:])]
    blobs = list(originals)
    def asset(name): return originals[names.index(name)]
    h = w.parse_header(rom)
    arm9 = rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
    native = room_catalog.parse(arm9, names)
    room_names = [r.name for r in native]
    clean = {e['name']: e['sha256'] for e in mod.load_clean()[2]['entries']}
    used = {ENTRANCE + '_app.obj', STATE_TEMPLATE + '_app.obj'}
    for room in ROOMS:
        src = next(r for r in native if r.name == room.source)
        used |= {room.source + '_app.obj', names[src.texture]}
    for name in sorted(used):
        if w.sha256(asset(name)) != clean[name]: raise ValueError(f'Chapter source is not the clean native: {name}')
    extras, report, local = {}, {'rooms': {}}, {}
    template = asset(STATE_TEMPLATE + '_app.obj')
    for room in ROOMS:
        src = next(r for r in native if r.name == room.source)
        obj, info = build_room(asset(room.source + '_app.obj'), template, room, src.index, room_names, local)
        extras[f'zz_{room.name}_app.obj'] = obj
        extras[f'zz_{room.name}Textures.nsbtx'] = graded_textures(originals[src.texture], room.grade)
        report['rooms'][room.name] = {'index': room.index, 'source': room.source, **info}
    entrance = names.index(ENTRANCE + '_app.obj')
    blobs[entrance] = entrance_obj(asset(ENTRANCE + '_app.obj'), room_names)
    # Appended models/textures need a word-aligned start; keep the padding in
    # its own unreferenced resource rather than inside an asset.
    padding = -len(glob) % 4
    if padding: extras = {'zz_ml_alignment.bin': bytes(padding), **extras}
    out_names, out_blobs = oscorp_resources.append_resources(names, blobs, extras)
    resources = {room.name: {'objects': out_names.index(f'zz_{room.name}_app.obj'),
                             'texture': out_names.index(f'zz_{room.name}Textures.nsbtx')} for room in ROOMS}
    staged = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(out_names, out_blobs)})
    result, patches = extend_arm9(staged, room_table(arm9, out_names, resources),
                                  (len(names), len(out_names)), save_rooms=save_rooms)
    check = w.validate_rom(result, target=True)
    fs = next(e for e in check['nitrofs'] if e['name'] == 'Glob.bin')
    out_glob = result[fs['start']:fs['end']]
    out_offsets, checked_names, _ = w.parse_glob(out_glob)
    if checked_names != out_names: raise ValueError('Chapter archive names changed')
    for i, blob in enumerate(out_blobs):
        if out_glob[out_offsets[i]:out_offsets[i + 1]] != blob: raise ValueError(f'Resource mismatch: {out_names[i]}')
        if i < len(names) and i not in (entrance, table_index) and blob != originals[i]:
            raise ValueError(f'Native resource changed: {names[i]}')
    h = w.parse_header(result)
    digest = w.sha256(result[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']])
    if save_rooms and ARM9_SHA256 and digest != ARM9_SHA256: raise ValueError(f'Unexpected chapter ARM9: {digest}')
    report.update({'schema_version': 1, 'arm9_sha256': digest, 'resources': resources,
                   'arm9_patches': [{'address': hex(a), 'old': hex(o), 'new': hex(n)} for a, o, n in patches],
                   'save_rooms': save_rooms, 'added_resources': list(extras),
                   'local_flags': {f'{room}:{var:#x}': flag for (room, var), flag in sorted(local.items())}})
    return result, report


def build(source=None, output=None, *, save_rooms=True):
    """Development candidate from the pinned stable v0.5.0 ROM (build/midnight-line/)."""
    source = Path(source or ROOT / 'build/Spider-Man-WoS-modded.nds')
    rom = source.read_bytes()
    if w.sha256(rom) != STABLE_SHA256: raise ValueError('Chapter build requires the pinned v0.5.0 ROM')
    result, report = apply_rom(rom, save_rooms=save_rooms)
    path = Path(output or ROOT / 'build/midnight-line/chapter.nds')
    w.atomic_write(path, result, sources=(source,))
    report.update({'status': 'development-candidate', 'source_sha256': STABLE_SHA256,
                   'candidate': str(path), 'candidate_sha256': w.sha256(result)})
    w.write_json(ROOT / 'work/midnight-line/chapter-build.json', report)
    return report


if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=None)
    parser.add_argument('--no-save-rooms', action='store_true', help='Control: keep native room checks at 75')
    args = parser.parse_args()
    print(json.dumps(build(output=args.out, save_rooms=not args.no_save_rooms), indent=2))
