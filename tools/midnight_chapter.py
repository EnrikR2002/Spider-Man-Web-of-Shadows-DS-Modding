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
from tools import minimap_cbmp, room_catalog, room_doors, room_script, tasm_kit as kit, wos_tool as w
from tools.nitro_texture import TextureArchive
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects

BASE = 0x02000000
ML_BASE = kit.TARGET + kit.RESERVE          # 02155420, after the kit's reserve
ML_SPACE = 0x1000                           # autoloaded; main arena starts after it
FIRST = room_catalog.COUNT + 1              # 75 stays the native invalid sentinel
LOOKUP_LITERAL = 0x02084AC8                 # literal of lookup 0x02084AB4
SAVE_ROOM_CHECK = 0x02085720                # cmp r1,#75 in saved-block validation
RELOAD_ROOM_CHECK = 0x020D64B8              # cmp r1,#75 in current-room reload
CMP_R1 = 0xE3510000
GLOB_COUNT = 0x77F8                         # ARM9 Glob resource count
VISITED_BASE = 0xB0                         # native rule: room r sets flag 0xB0+r
FLAG_LIMIT = 0x123                          # flags 0..0x122; higher ids are scalars
# Flags with no event or code reference that no save sets. 251..275 sit
# after the native visited flags (0xB0+room); 245..250 are the visited flags
# of the unreachable debug rooms 69..74, whose OBJs never set them.
# 138..165 have no event or code reference either and are unset in 21 save
# slots up to mission 47 (TECHNICAL "Content toolbox research").
FREE_FLAGS = (*range(138, 166), *range(245, 276))
# Chapter allocation: visited 0xB0+room (252..265 for rooms 76..89, the native
# rule the map relies on); LOCAL_FLAGS hold room-local flags of cloned
# encounters, allocated in first-use order (Station/Platform keep 268..271
# from v0.6.1). The Venom room's reward flag doubles as "chapter completed".
# 266/267 held the Span's seal flag and the Hollow's red-floor flag, which
# nothing writes since v0.8.1; those two now take 138/139 so that 266/267 are
# the visited flags of rooms 90/91. Every other allocation keeps its number.
LOCAL_FLAGS = (*range(268, 276), 138, 139, 251, 250, 249, 248, 247, 246, 245, *range(140, 166))
# Per-room scratch bytes (0x127..0x130, e.g. the Venom room's platform and
# timer states): writes are kept, like the native room's.
ROOM_SCRATCH = range(0x127, 0x131)
# Story prerequisites of a boss trigger, read as "already met": the variable
# maps to the room's own visited flag, which its init sets first.
PREREQUISITES = {('ML_Venom', 0xAA)}      # Sewer_Map06 mini-boss defeated
SET_VAR, INC_VAR, DEC_VAR, IF_VAR = 0x26, 0x25, 0x24, 0x1D
MESSAGE = 0x15
DELAY = 0x1C                                # u16 frames, u8 action group (+4), u8 event group (+5), 1-based
GRANT = 0x1F                                # "<ability> obtained!": grants a native story ability
SPAWN_PICKUP = 0x07                         # spawns a pickup; operand +26 = 1-based group run on pickup
STABLE_SHA256 = 'fd7e4420f97645dd55011504843ce62f068d1276234c3cd781931c85bb1eb193'
ARM9_SHA256 = 'c6e2992a21cb365d00e3575ae89a46933241aa99f86bd975efec16d902c96b2c'   # chapter over the kit ARM9 (pinned per release)
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
    Room(76, 'ML_Entry', 'Sewer_Map01', 'midnight', True),       # arrival from the sewer
    Room(77, 'ML_Refuge', 'Sewer_Save04', 'emergency', False),   # combat-free save room
    Room(78, 'ML_Station', 'Sewer_Map02', 'midnight', True),     # station hall: ambush
    Room(79, 'ML_Stairs', 'Sewer_Map13', 'midnight', True),      # stairs: three spawners
    Room(80, 'ML_Platform', 'Sewer_Map03', 'midnight', True),    # tracks: red suits, hazards
    # The Nest (v0.7.0): symbiote rooms under the line, reached through the
    # tracks' floor grate and climbing out into the Stairs. Native Hive pairs.
    Room(81, 'ML_NestShaft', 'Hive_Map07', 'nest', True),       # drop-in shaft: fliers
    Room(82, 'ML_NestRest', 'Hive_Save02', 'nest', True),       # save point
    Room(83, 'ML_NestThroat', 'Hive_Map06', 'nest', True),      # climb: fliers, ichor locks
    Room(84, 'ML_NestSpan', 'Hive_Map05', 'nest', True),        # long hall: two waves
    Room(85, 'ML_NestHollow', 'Hive_Map04', 'nest', True),      # ambush, ichor locks
    Room(86, 'ML_NestGallery', 'Hive_Map03', 'nest', False),    # quiet climb (Venom scene removed)
    Room(87, 'ML_NestShrine', 'Hive_Save02', 'nest', True),     # second save point
    Room(88, 'ML_NestGate', 'Hive_Map02', 'nest', True),        # ambush, then up to the Stairs
    Room(89, 'ML_Venom', 'Downtown_Map14', 'nest', True),       # boss: Venom, ichor gates, platforms
    # The Yard (v0.9.0): the unused prototype warehouse, behind a new door in the Refuge.
    Room(90, 'ML_Yard', 'proto01', 'dusk', True),               # side room: gang camp, crates to throw
)
BY_NAME = {r.name: r for r in ROOMS}
# (room, record-0 exit group) -> (destination, spawn id). A spawn is the arrival
# point beside the destination's door back. Every link joins opposite door
# kinds (left<->right, up<->down; tests check this from trigger/spawn geometry),
# so leaving through a ceiling hatch always arrives through a floor grate.
# Station<->Entry, Station<->Platform, Stairs<->Refuge and every link inside
# the Nest are native pairs.
LINKS = {
    ('ML_Entry', 2): (ENTRANCE, 2),
    ('ML_Entry', 1): ('ML_Station', 1), ('ML_Station', 1): ('ML_Entry', 2),
    ('ML_Station', 2): ('ML_Platform', 1), ('ML_Platform', 1): ('ML_Station', 2),
    ('ML_Platform', 3): ('ML_Stairs', 3), ('ML_Stairs', 3): ('ML_Platform', 3),
    ('ML_Stairs', 2): ('ML_Refuge', 1), ('ML_Refuge', 1): ('ML_Stairs', 2),
    # Tracks floor grate down into the Nest shaft; the Gate's ceiling exit
    # comes back up through the Stairs' floor grate.
    ('ML_Platform', 2): ('ML_NestShaft', 2), ('ML_NestShaft', 1): ('ML_Platform', 2),
    ('ML_NestShaft', 2): ('ML_NestRest', 1), ('ML_NestRest', 1): ('ML_NestShaft', 1),
    ('ML_NestRest', 2): ('ML_NestThroat', 2), ('ML_NestThroat', 1): ('ML_NestRest', 2),
    ('ML_NestThroat', 2): ('ML_NestSpan', 2), ('ML_NestSpan', 2): ('ML_NestThroat', 1),
    ('ML_NestSpan', 1): ('ML_NestHollow', 2), ('ML_NestHollow', 1): ('ML_NestSpan', 1),
    ('ML_NestHollow', 2): ('ML_NestGallery', 2), ('ML_NestGallery', 1): ('ML_NestHollow', 1),
    ('ML_NestGallery', 2): ('ML_NestShrine', 2), ('ML_NestShrine', 2): ('ML_NestGallery', 1),
    # Venom's arena sits between the Shrine and the Gate (its upper-left exit is sealed).
    ('ML_NestShrine', 1): ('ML_Venom', 2), ('ML_Venom', 1): ('ML_NestShrine', 1),
    ('ML_Venom', 2): ('ML_NestGate', 2), ('ML_NestGate', 1): ('ML_Venom', 1),
    ('ML_NestGate', 2): ('ML_Stairs', 1), ('ML_Stairs', 1): ('ML_NestGate', 1),
    # Authored doors (no native pair): Refuge left wall <-> the Yard's right tunnel.
    ('ML_Refuge', 2): ('ML_Yard', 1), ('ML_Yard', 1): ('ML_Refuge', 2),
}
AUTHORED_EXITS = {('ML_Refuge', 2), ('ML_Yard', 1)}        # built by add_yard_door/stage_yard, not by sanitize
# Surplus native exits (both ceiling hatches whose floor partners now lead into
# the Nest): the trigger moves out of reach, so the door is a dead hatch.
SEALED = {('ML_Entry', 3), ('ML_Platform', 4), ('ML_Venom', 3)}
# --- Power puzzle (v0.8.0) --------------------------------------------------
# The Platform clone keeps the native ElecBoilerCheck: while the flag cloned
# from Sewer_Map04's switch (0x27) is clear, the boiler sitting on the Nest
# grate is electrified and cannot be lifted, so the grate stays locked. A
# breaker in the Stairs (Sewer_Map04's Switch + Button Press pair, the room
# the Platform's trapdoor leads to, as natively) sets that shared flag; then
# lifting/throwing the boiler unlocks the grate (native Lift_Object_Die) and
# X on the grate drops into the Nest. See TECHNICAL "Power puzzle".
TRACK_POWER = 269                           # set = track power cut (breaker thrown)
SHARED_FLAGS = {('ML_Platform', 0x27): TRACK_POWER}
BREAKER_SOURCE = 'Sewer_Map04'
BREAKER = {'room': 'ML_Stairs', 'switch': (211 * 4096, 87 * 4096 + 2048, 0), 'trigger_dx': 4 * 4096,
           'trigger_dy': -3 * 4096, 'trigger_size': (8, 10)}
SWITCH_THROW, SWITCH_THROWN = 0x19, 0x64    # native switch animations (Sewer_Map04 Switch_Throw/Thrown)
SOUND = 0x22                                # one-shot sound effect (u16 id)
BREAKER_SOUND = 0xBC                        # native switch-throw sound
# --- Chapter dialogue (v0.8.0) ----------------------------------------------
# Touch-screen messages with new ids from 0xC4 (the native table at 0x0211C214
# has 196 entries of 44 bytes). The accessor 0x020D0F64 (table + id * 44) is
# rewritten in place, same size, to read ids >= 0xC4 from a short table in the
# chapter block, and both id bounds rise to cover the new ids. Each line is an
# appended slot of English/American.strings; the 1049-word zero prefix stays
# (the loader 0x0200694C only skips it). See TECHNICAL "Chapter dialogue".
MESSAGE_TABLE, MESSAGE_FIRST, MESSAGE_SIZE = 0x0211C214, 0xC4, 44
MESSAGE_ACCESSOR = 0x020D0F64
ACCESSOR_NATIVE = (0xE92D000F, 0xE59D2004, 0xE59F3010, 0xE3A0102C, 0xE0213192, 0xE5801000, 0xE28DD010,
                   0xE12FFF1E, MESSAGE_TABLE)
MESSAGE_BOUNDS = (0x020DFCFC, 0x020DFDD8)   # cmp r1,#0xC4 before blt/bhs: valid ids are below it
STRING_FILES = ('English.strings', 'American.strings')
LINES = {
    'live_tracks': 'The tracks are live. Cut the power before touching that boiler.',
    'breaker': 'Track power cut. The boiler on the tracks can be moved now.',
    # Refuge objective board, one line by progress (shown on entering the Refuge).
    'goal_power': 'Objective: cut the track power. The breaker is on the Stairs.',
    'goal_nest': 'Objective: something nests under the tracks. Move the boiler and go down.',
    'goal_done': 'The Midnight Line is quiet. For now.',
    'sealed_grate': 'Sealed from below. The way down must be somewhere on the tracks.',
    'grate_clear': 'The grate is clear. Stand on it, open it with X and drop in with Down.',
    'way_up': 'The nest falls silent. Take the left passage: a shaft climbs back to the Stairs.',
    'yard': 'A freight yard above the line. Someone made camp here, and they have seen you.',
}
# --- The Yard (v0.9.0) -------------------------------------------------------
# proto01 is a textured prototype warehouse yard no story room leads to: one
# model, its own BSP and textures, no spawn table or exits, Spidey and every
# object in record 1's first batch. The clone gains a spawn and an exit in the
# tunnel at its right end, loses its test orbs/pickups and the two red test
# objects standing in that tunnel, and gets a Pier gang spawner. The Refuge
# gains the matching door in its left wall. See TECHNICAL "The Yard".
YARD = {
    'room': 'ML_Yard', 'hub': 'ML_Refuge',
    'spawn': {'spawn_id': 1, 'xyz': (160 * 4096, 42 * 4096, 0), 'facing': 'left'},
    # The tunnel wall is at x 175 and Spidey stops 3.5 short of it: the box must reach in to 172.
    'exit': {'center': (178 * 4096, 48 * 4096, 0), 'size': (12, 24),
             'trigger_name': 'Trigger (Main|Exit_Refuge)', 'group_name': 'Exit_Refuge'},
    # Refuge wall at x 0.5: Spidey stands at 4 against it, so the box reaches to x 2 (touched below 5.5).
    'hub_spawn': {'spawn_id': 2, 'xyz': (10 * 4096, 2 * 4096, 0), 'facing': 'right'},
    'hub_exit': {'center': (-4 * 4096, 6 * 4096, 0), 'size': (12, 24),
                 'trigger_name': 'Trigger (Main|Exit_Yard)', 'group_name': 'Exit_Yard'},
    'hub_door': {'source': 'Sewer_Map13', 'label': 'Door (Misc) 1', 'xyz': (-2048, 0, 0)},   # a native left sewer door
    # Object kinds moved away: red test floor and wall in the exit tunnel, two ichor test gates on the
    # floor, the electric and fire hazard test objects by the left wall.
    'removed_kinds': (0x09, 0x30, 0x0C, 0x0D, 0x11, 0x13),
    'removed_triggers': 'Ichor Test',                       # the X prompts that dissolved those gates
    'pickup_chain': 'New Event',                            # test groups that respawn ability pickups
    'gang': {'source': 'Pier_Map04', 'table': 0x08, 'xyz': (-110 * 4096, 2 * 4096, 0), 'box': (300, 120)},
}
SPAWNER_TYPE = 4
OBJECTIVE_ROOM = 'ML_Refuge'
COMPLETED = ('ML_Venom', 0xAB)              # boss reward flag (local allocation) = chapter completed
# --- Walkable routes (v0.8.1) ------------------------------------------------
# The Nest runs the Hive rooms against their native direction and the boss
# arena from its exit side, and the chapter never grants the boss's native
# reward, Sledgehammer Slam (story ability 314, bit 5). So no clone may need
# it: the red ichor floors only that ability breaks are never activated (the
# room's own "already smashed" state). Player 2026-10-11: sealed in the Gate
# between its ichor ceiling and such a floor. See TECHNICAL "Chapter routes".
OBJECT_TYPE = 14
SLEDGEHAMMER_FLOOR = 0x09                   # object kind (entity +22): Floor_Smashable/Floor_SmashableIchor
# Hive ambushes seal both doors with ichor crystals until the wave is dead and
# the cracked crystal is hit. Walked for real, that strands Spidey: enemies
# reposition into the door corridor behind a crystal (Throat, lab), a seal that
# starts at the native entrance comes after the enemies are gone (Gate), and
# the wave stays below a floor he could not pass (Gate, the player's report).
# The Nest keeps every fight but never runs the sealing group; the boss arena
# is the one sealed fight.
SEAL_GROUP = 'Door_Lock'
UNSEALED = ('ML_NestShaft', 'ML_NestThroat', 'ML_NestSpan', 'ML_NestHollow', 'ML_NestGate')
# The boss arena is entered from a lower exit corridor instead of the upper
# door: its ichor walls rise when the fight starts (natively at room load,
# closing the corridors), the fight starts when Spidey is inside the arena
# (natively also on a 450-frame timer, which sealed him in the corridor).
BOSS = {'room': 'ML_Venom', 'walls': 'Ichor Walls', 'route': 'Route 1', 'start': 'Boss Trigger',
        'fight': 'Gate_Spawn', 'reward': 'Reward_Pickup', 'timer_frames': 450,
        'trigger': (90 * 4096, 65 * 4096), 'trigger_size': (90, 140)}
GATE_GROW = 0x8D                            # native ichor gate/wall rise animation (Door_Lock, Gate_Spawn)
# The Stairs' floor grate is the way *out* of the Nest (the Gate's ceiling
# exit). It stays locked until the Gate has been reached from below, so the
# Nest is always entered through the tracks and the boss cannot be skipped to.
GRATE = {'room': 'ML_Stairs', 'door': 'Door (Sewer Grate Floor)', 'opened_by': 'ML_NestGate',
         'trigger': (-10 * 4096, 6 * 4096), 'trigger_size': (16, 12)}


def message_id(key):
    return MESSAGE_FIRST + list(LINES).index(key)


def say(key, frames=0):
    """0x15 operand: u16 display time (0 = native default), message id, lookup flag, continuation group."""
    return Command(MESSAGE, struct.pack('<HBBBxxx', frames, message_id(key), 0, 0))


def message_accessor(chapter_table):
    """Same-size accessor: ids below 0xC4 read the native table, others the chapter table."""
    return (0xE35100C4,                     # cmp   r1, #0xC4
            0x359F3010,                     # ldrlo r3, [pc, #0x10]  native table
            0x259F3010,                     # ldrhs r3, [pc, #0x10]  chapter table - 0xC4 * 44
            0xE3A0202C,                     # mov   r2, #0x2C
            0xE0223291,                     # mla   r2, r1, r2, r3
            0xE5802000,                     # str   r2, [r0]
            0xE12FFF1E,                     # bx    lr
            MESSAGE_TABLE, chapter_table - MESSAGE_FIRST * MESSAGE_SIZE)


def message_entries(first_string):
    """44-byte entries: string index, no voice (-1, -1), nine unused extra ids."""
    return b''.join(struct.pack('<IHH', first_string + i, 0xFFFF, 0xFFFF) + struct.pack('<9I', *[0x7FFFFFFF] * 9)
                    for i in range(len(LINES)))


def _tour():
    """Lab route taking every directed link once, entrance to entrance (Hierholzer)."""
    out = {}
    for (room, group), (dest, _) in sorted(LINKS.items()):
        out.setdefault(room, []).append((group, dest))
    out.setdefault(ENTRANCE, []).append((2, 'ML_Entry'))
    stack, walk = [(ENTRANCE, None)], []
    while stack:
        room, via = stack[-1]
        if out.get(room):
            group, dest = out[room].pop(0)
            stack.append((dest, (room, group)))
        else:
            walk.append(via)
            stack.pop()
    return tuple(x for x in reversed(walk) if x)


TOUR = _tour()


# Sewer_Save02: right wall reaches x=56.47; mirrors the native left exit.
ENTRANCE_DOOR = {'center': (61 * 4096, 4 * 4096, 0), 'size': (12, 24), 'room': 'ML_Entry', 'spawn': 3,
                 'trigger_name': 'Trigger (Main|Exit_Midnight)', 'group_name': 'Exit_Midnight_Line'}
RETURN_SPAWN = {'spawn_id': 2, 'xyz': (44 * 4096, 2 * 4096, 0), 'facing': 'left'}
# A copy of the room's native "Door (empty)" doorway (record 1) marks the way in.
DOORWAY = {'x': 54 * 4096, 'name': 'Door (empty) Midnight'}
# Unreachable placement for pickups that must not be duplicated.
REMOVED_PICKUP_Y = -4000 * 4096
PICKUP_TYPE = 13
# Minimap fields at descriptor +0x28..+0x48 (area, piece position, size, room
# bounds), filled at boot for native rooms 0..74 only. Values read from RAM of
# the sources in a running game; the chapter's own block keeps static copies.
MAP_FIELDS = {
    'Sewer_Map01': (2, 221184, 180224, 917504, 548864, -122880, -40960, 1105920, -696320),
    'Sewer_Map02': (2, 4096, 131072, 966656, 466944, -573440, 327680, 1310720, -327680),
    'Sewer_Map03': (2, 81920, 421888, 991232, 442368, -20480, 122880, 1761280, 81920),
    'Sewer_Map13': (2, 172032, 176128, 737280, 323584, -81920, 614400, 1024000, 327680),
    'Sewer_Save04': (2, 450560, 323584, 589824, 393216, 0, 102400, 245760, 0),
    'Hive_Map02': (4, 454656, 167936, 548864, 622592, -163840, 798720, 0, 0),
    'Hive_Map03': (4, 368640, 217088, 716800, 438272, 122880, 389120, 737280, 0),
    'Hive_Map04': (4, 516096, 102400, 610304, 544768, -81920, 798720, 81920, 20480),
    'Hive_Map05': (4, 106496, 262144, 942080, 409600, -1638400, 163840, 0, -122880),
    'Hive_Map06': (4, 479232, 102400, 569344, 561152, -163840, 798720, 0, 0),
    'Hive_Map07': (4, 450560, 163840, 540672, 618496, 0, 798720, 163840, 0),
    'Hive_Save02': (4, 450560, 323584, 589824, 393216, 0, 102400, 245760, 0),
    'Downtown_Map14': (3, 335872, 237568, 704512, 446464, 40960, 450560, 696320, 81920),
    # proto01 has no native values (area 5, zeros): the Refuge's map piece, its own collision bounds
    # as (x min, y max, x max, y min), the layout Sewer_Save04's values show.
    'proto01': (5, 450560, 323584, 589824, 393216, -270 * 4096, 110 * 4096, 175 * 4096, 0),
}
# --- Touch-screen map (v0.7.0) ---------------------------------------------
# The Sewer area screen gains a subway-style diagram of the chapter in its empty
# lower-left corner; the Sewer area room list (20-byte entries) is relocated
# into the chapter block with one entry per chapter room so the native code
# shows visited/current rooms. See TECHNICAL "Minimap screens and area room lists".
MAP_SCREEN = 'MMSewer.cbmp'
SEWER_AREA = 2
AREA_ROWS = 0x0213B840                     # 16-byte rows: screen, map var, list, count
SEWER_LIST, SEWER_COUNT = 0x0211FE38, 18
ENTRY_SIZE = 20
STATE_COLORS = bytes((0xB6, 0xBA, 0xBB, 0xBF))   # every native entry: state colour sources
# 5-colour room slots (first colour = background) that no Sewer screen tile
# uses: palettes 1..3 (magenta fill), Sewer_Map13's spare third slot 0xAB,
# palette 0 beyond its backdrop colour, and one slot of the grey palette 13.
MAP_SLOTS = (0x11, 0x16, 0x1B, 0x21, 0x26, 0x2B, 0x31, 0x36, 0x3B, 0xAB, 0x06, 0x0B, 0xD6, 0xDB, 0x01)
SLOT_DEFAULT = (0x1042, 0x3D89, 0xE6B2, 0x4E0E, 0xCA52)   # native slot colours in the file
# Diagram cells (screen tile column, row) per room; links join cell edges.
DIAGRAM = {
    'ML_Entry': ((3, 15), (4, 15)), 'ML_Station': ((5, 15),), 'ML_Platform': ((6, 15),),
    'ML_Stairs': ((11, 15), (7, 15), (8, 15), (9, 15), (10, 15)), 'ML_Refuge': ((12, 15),),
    'ML_NestShaft': ((6, 16),), 'ML_NestRest': ((6, 17),), 'ML_NestThroat': ((6, 18),),
    'ML_NestSpan': ((7, 18), (8, 18)), 'ML_NestHollow': ((9, 18),), 'ML_NestGallery': ((10, 18),),
    'ML_NestShrine': ((11, 18),), 'ML_Venom': ((11, 17),), 'ML_NestGate': ((11, 16),),
    'ML_Yard': ((12, 16), (13, 16)),
}
SAVE_ROOMS = {'ML_Refuge', 'ML_NestRest', 'ML_NestShrine'}
DIAGRAM_TRACK = {(7, 15), (8, 15), (9, 15), (10, 15)}   # Platform<->Stairs line drawn as Stairs
BOSS_ROOMS = {'ML_Venom'}
DIAGRAM_STUB = (3, 15)                            # line out to the Sewer (drawn as Entry)


def _diagram_tiles():
    """{cell: 64 pixel roles (0 background, 2 fill, 4 edge/line)} for the chapter diagram."""
    cells = {cell: room for room, cs in DIAGRAM.items() for cell in cs}
    linked = {frozenset((room, dest)) for (room, _), (dest, _) in LINKS.items()}
    out = {}
    for (x, y), room in cells.items():
        px = [0] * 64
        def put(i, j, role): px[j * 8 + i] = role
        line = (x, y) in DIAGRAM_TRACK or (x, y) == DIAGRAM_STUB
        wide = len(DIAGRAM[room]) == 2 and not line
        if line:
            for i in range(2 if (x, y) == DIAGRAM_STUB else 0, 8):
                put(i, 3, 4); put(i, 4, 4)
            if (x, y) == DIAGRAM_STUB:           # arrow head pointing back to the Sewer
                for i, j in ((0, 3), (0, 4), (1, 2), (1, 3), (1, 4), (1, 5), (2, 1), (2, 6)): put(i, j, 4)
        else:
            left_open = wide and cells.get((x - 1, y)) == room
            right_open = wide and cells.get((x + 1, y)) == room
            lo, hi = (0 if left_open else 1), (7 if right_open else 6)
            for j in range(1, 7):
                for i in range(lo, hi + 1):
                    edge = j in (1, 6) or (i == 1 and not left_open) or (i == 6 and not right_open)
                    put(i, j, 4 if edge else 2)
            if room in SAVE_ROOMS:                # save point: a dot in the middle
                for i, j in ((3, 3), (4, 3), (3, 4), (4, 4)): put(i, j, 4)
            if room in BOSS_ROOMS:                # boss: a cross
                for k in range(2, 6): put(k, k, 4); put(7 - k, k, 4)
            for dx, dy, at in ((1, 0, 7), (-1, 0, 0), (0, 1, 7), (0, -1, 0)):
                other = cells.get((x + dx, y + dy))
                if other is None or other == room and wide: continue
                if other != room and frozenset((room, other)) not in linked and (x + dx, y + dy) not in DIAGRAM_TRACK:
                    continue
                for w in (3, 4):
                    if dx: put(at, w, 4)
                    else: put(w, at, 4)
        out[(x, y)] = px
    return out


def map_screen(raw):
    """MMSewer.cbmp with the chapter diagram; native cells/colours elsewhere unchanged."""
    screen = minimap_cbmp.Cbmp.parse(raw)
    background = screen.screen[DIAGRAM_STUB[1] * screen.width + DIAGRAM_STUB[0]]
    tiles, cells, colors = [], {}, {}
    slot_of = dict(zip(DIAGRAM, MAP_SLOTS))
    for room, slot in slot_of.items():
        for i, value in enumerate(SLOT_DEFAULT): colors[slot + i] = value
    for (x, y), roles in sorted(_diagram_tiles().items(), key=lambda t: (t[0][1], t[0][0])):
        if screen.screen[y * screen.width + x] != background: raise ValueError(f'Map cell {x},{y} is not empty')
        room = next(r for r, cs in DIAGRAM.items() if (x, y) in cs)
        slot = slot_of[room]
        base = slot & 0x0F                          # colour index of the slot's background
        cells[(x, y)] = len(tiles)
        tiles.append([base + r for r in roles])
    used = {(e >> 12) * 16 + c for e in screen.screen for c in set(screen.tile(e & 0x3FF)) if c}
    if used & set(colors) or {i for i in colors if i >> 4 == 0xB}:
        raise ValueError('Map colour slot is in use')
    screen, first = screen.with_tiles(tiles)
    entries = {xy: (slot_of[next(r for r, cs in DIAGRAM.items() if xy in cs)] >> 4) << 12 | first + n
               for xy, n in cells.items()}
    return screen.with_screen(entries).with_colors(colors).to_bytes()


def map_entries():
    """Area-list entries (20 bytes) for the chapter rooms, in DIAGRAM order."""
    out = b''
    for room, slot in zip(DIAGRAM, MAP_SLOTS):
        x, y = DIAGRAM[room][0]
        out += (struct.pack('<2I', BY_NAME[room].index, 1) + bytes((0, slot, slot + 4)) + STATE_COLORS
                + bytes((x * 8 + 4, y * 8 + 4, 0, 0, 0)))
    return out


GRADES = {   # (desaturation, (r, g, b) gain, lift in 5-bit units)
    'midnight': (0.55, (0.42, 0.58, 0.82), (0.0, 0.3, 0.9)),
    'emergency': (0.45, (0.85, 0.60, 0.36), (0.6, 0.2, 0.0)),
    'nest': (0.30, (0.62, 0.80, 0.86), (0.2, 0.5, 0.7)),
    'dusk': (0.45, (0.56, 0.68, 0.92), (0.5, 0.7, 1.3)),      # the Yard: night blue, lifted so its dark tunnel reads
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
    mission/difficulty scalars and ability bits: callers drop writes to them;
    per-room scratch bytes pass through.
    """
    if var == VISITED_BASE + source_index or (room.name, var) in PREREQUISITES:
        return VISITED_BASE + room.index
    if var in ROOM_SCRATCH: return var
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
                if (room.name, g) in SEALED: dest, spawn = ENTRANCE, RETURN_SPAWN['spawn_id']   # unreachable trigger
                elif (room.name, g) not in LINKS: raise ValueError(f'{room.name} exit group {g} has no link')
                else: dest, spawn = LINKS[(room.name, g)]
                index = BY_NAME[dest].index if dest in BY_NAME else names.index(dest)
                commands.append(Command(op, bytes([index, 1, spawn]) + operand[3:]))
            elif op == GRANT:
                dropped.append((g, op))           # native story ability/collectible reward: never granted here
            elif op == SPAWN_PICKUP:
                # A boss's reward orb is a native collectible (taking it would mark
                # the real one collected). Run its pickup group directly instead.
                dropped.append((g, op))
                commands.append(Command(DELAY, bytes((0, 0, 0, 0, 0, operand[26], 0, 0))))
            elif op == MESSAGE:
                # Dialogue/VO is story text; operand +4 is the 1-based group
                # the dialogue continues with, so keep that as a 0-frame delay.
                dropped.append((g, op))
                if operand[4]: commands.append(Command(DELAY, bytes((0, 0, 0, 0, 0, operand[4], 0, 0))))
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


def _seal_exits(section0, room):
    """Move the triggers of SEALED exit groups out of reach (record 0)."""
    sealed = {g for r, g in SEALED if r == room.name}
    moved = []
    for i, entity in enumerate(Entities.parse(section0).records):
        if (len(entity) == 28 and struct.unpack_from('<I', entity, 12)[0] == room_doors.TRIGGER_TYPE
                and entity[27] - 1 in sealed):
            changed = bytearray(entity)
            struct.pack_into('<i', changed, 4, REMOVED_PICKUP_Y)
            section0 = Entities.parse(section0).replace_record(i, bytes(changed))
            moved.append(entity[27] - 1)
    if sorted(moved) != sorted(sealed): raise ValueError(f'{room.name}: sealed exits {sealed} not found')
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
        sealed = []
        if r == 0: section0, sealed = _seal_exits(section0, room)
        result = RoomObjects.parse(result).replace_section(r, 0, section0)
        result = RoomObjects.parse(result).replace_section(r, 1, events.to_bytes())
        report[f'record{r}'] = {'dropped_commands': dropped, 'moved_pickups': moved, 'sealed_exits': sealed}
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


def add_breaker(raw, switch_room, breaker=None):
    """Append the track-power breaker to a built room's record 1.

    New AG 'Breaker' = copies of the native switch and its Button Press trigger
    (pressing it runs Breaker_Throw); the init shows the thrown pose once the
    flag is set. Existing AG/entity/EG indices are unchanged (append only).
    """
    breaker = breaker or BREAKER
    native = RoomObjects.parse(switch_room)
    labels = native.names[1].labels
    entities = Entities.parse(native.records[1].sections[0]).records
    switch = bytearray(next(e for i, e in enumerate(entities) if labels[i] == 'Object (Switch)'))
    trigger = bytearray(next(e for i, e in enumerate(entities) if labels[i] == 'Trigger (Button Press)'))
    if trigger[26] != 0 or struct.unpack_from('<I', trigger, 12)[0] != room_doors.TRIGGER_TYPE:
        raise ValueError('Breaker trigger template changed')
    _, groups = room_script.counts(raw, 1)
    x, y, z = breaker['switch']
    struct.pack_into('<3i', switch, 0, x, y, z)
    struct.pack_into('<3i', trigger, 0, x + breaker['trigger_dx'], y + breaker['trigger_dy'], z)
    struct.pack_into('<2H', trigger, 20, *breaker['trigger_size'])
    trigger[27] = groups + 1                                  # Breaker_Throw (1-based)
    raw, ag = room_script.append_batch(raw, 1, [(bytes(switch), 'Object (Switch) Breaker'),
                                                (bytes(trigger), 'Trigger (Breaker Press)')], 'Breaker')
    throw = EventGroup((room_script.animate(ag, 1, SWITCH_THROW), room_script.set_var(TRACK_POWER, 1),
                        Command(SOUND, struct.pack('<HH', BREAKER_SOUND, 0)), say('breaker')))
    thrown = EventGroup((room_script.animate(ag, 1, SWITCH_THROWN),))
    raw, first = room_script.append_groups(raw, 1, [(throw, 'Breaker_Throw'), (thrown, 'Breaker_Thrown')])
    # As Sewer_Map04's init: the switch always; its trigger only while the
    # power is on, otherwise the thrown pose.
    return room_script.extend_group(raw, 1, 0, [
        room_script.activate(entity=(ag, 1)),
        room_script.if_var(TRACK_POWER, '==', 0, then=room_script.action(entity=(ag, 2)),
                           otherwise=room_script.action(eg=first + 1))])


def _index(labels, name, what):
    if labels.count(name) != 1: raise ValueError(f'Expected one {what} named {name!r}')
    return labels.index(name)


def _drop_activations(raw, batches):
    """Record 1 without any command that only activates one of `batches` (AG indices)."""
    def drop(_, command):
        if command.opcode == room_script.DEACTIVATE: return False        # switching it off stays harmless
        hits = [a for a in room_script.actions(command) if room_script.targets(a) & batches]
        if not hits: return False
        others = [a for a in room_script.actions(command) if a not in hits and any(a)]
        if others or any(a[3] or len(room_script.targets(a)) != 1 for a in hits):
            raise ValueError('Activation is combined with other actions')
        return True
    return room_script.drop_commands(raw, 1, drop)


def open_hammer_floors(raw):
    """Record 1 with its Sledgehammer Slam floors never activated; returns (raw, floors removed)."""
    batches = Entities.parse(RoomObjects.parse(raw).records[1].sections[0]).batches
    def floor(e): return len(e) >= 24 and struct.unpack_from('<I', e, 12)[0] == OBJECT_TYPE and e[22] == SLEDGEHAMMER_FLOOR
    floors = {b for b, batch in enumerate(batches) if any(floor(e) for e in batch.records)}
    if any(not floor(e) for b in floors for e in batches[b].records): raise ValueError('Mixed hammer-floor batch')
    count = sum(len(batches[b].records) for b in floors)
    if not floors: return raw, 0
    raw, removed = _drop_activations(raw, floors)
    if len(removed) not in (len(floors), count): raise ValueError('Hammer floor activations changed')
    return raw, count


def unseal(raw, group=SEAL_GROUP):
    """Record 1 without any command that runs the door-sealing group; its enemies still spawn."""
    seal = _index(room_script.names(raw, 1)[1], group, 'event group') + 1
    def drop(_, command):
        runs = [a for a in room_script.actions(command) if command.opcode != room_script.DEACTIVATE and a[3] == seal]
        if runs and any(a[3] not in (0, seal) for a in room_script.actions(command)):
            raise ValueError('Seal is combined with another event group')
        return bool(runs)
    raw, removed = room_script.drop_commands(raw, 1, drop)
    if len(removed) != 1: raise ValueError('Door seal call changed')
    return raw


def stage_boss(raw, boss=None):
    """Boss arena entered from an exit corridor: walls rise with the fight, which starts inside the arena."""
    boss = boss or BOSS
    _, egs, ags = room_script.names(raw, 1)
    walls, route, start, fight, reward = (_index(labels, boss[key], key) for labels, key in (
        (ags, 'walls'), (egs, 'route'), (egs, 'start'), (egs, 'fight'), (egs, 'reward')))
    wall_count = room_script.counts(raw, 1)[0][walls]
    raise_walls = room_script.activate(ag=walls)
    def drop(g, command):
        if g == route and command == raise_walls: return True
        return (g == start and command.opcode == IF_VAR
                and struct.unpack_from('<H', command.operand, 2)[0] == boss['timer_frames'])
    raw, removed = room_script.drop_commands(raw, 1, drop)
    if sorted(g for g, _ in removed) != sorted((route, start)): raise ValueError('Boss room script changed')
    x, y = boss['trigger']
    raw, arena = room_script.append_batch(raw, 1, [(room_script.trigger(x, y, boss['trigger_size'], fight + 1),
                                                    'Trigger (Arena Entered)')], 'Arena Trigger')
    raw = room_script.extend_group(raw, 1, start, [room_script.activate(ag=arena)])
    raw = room_script.extend_group(raw, 1, fight, [
        room_script.deactivate(ag=arena), raise_walls,
        *(room_script.animate(walls, n + 1, GATE_GROW) for n in range(wall_count))])
    return room_script.extend_group(raw, 1, reward, [say('way_up')])


def seal_grate(raw, opened, grate=None):
    """Stairs record 1: the floor grate stays locked until flag `opened`; standing on it shows a hint once."""
    grate = grate or GRATE
    entities, _, _ = room_script.names(raw, 1)
    door = (0, _index(entities[0], grate['door'], 'door') + 1)
    _, groups = room_script.counts(raw, 1)
    sealed, hint = groups + 1, groups + 2
    x, y = grate['trigger']
    raw, ag = room_script.append_batch(raw, 1, [(room_script.trigger(x, y, grate['trigger_size'], hint),
                                                 'Trigger (Sealed Grate)')], 'Sealed Grate')
    raw, _ = room_script.append_groups(raw, 1, [
        (EventGroup((room_script.door(door, True), room_script.activate(ag=ag))), 'Grate_Sealed'),
        (EventGroup((say('sealed_grate'), room_script.deactivate(entity=(ag, 1)))), 'Grate_Hint')])
    return room_script.extend_group(raw, 1, 0, [room_script.if_var(opened, '==', 0, then=room_script.action(eg=sealed))])


def _entity(raw, record, label):
    """The entity named `label` in a native room record."""
    parsed = RoomObjects.parse(raw)
    labels = parsed.names[record].labels
    entities = Entities.parse(parsed.records[record].sections[0]).records
    return entities[_index(list(labels[:len(entities)]), label, 'entity')]


def stage_yard(raw, hub_native, gang_native, visited, yard=None):
    """proto01 as a chapter room: arrival and exit in the right tunnel, no test objects, a gang, a visited flag."""
    yard = yard or YARD
    parsed = RoomObjects.parse(raw)
    section0, moved = parsed.records[1].sections[0], []
    for i, entity in enumerate(Entities.parse(section0).records):
        if len(entity) >= 24 and struct.unpack_from('<I', entity, 12)[0] == OBJECT_TYPE and entity[22] in yard['removed_kinds']:
            changed = bytearray(entity)
            struct.pack_into('<i', changed, 4, REMOVED_PICKUP_Y)
            section0 = Entities.parse(section0).replace_record(i, bytes(changed))
            moved.append(i)
    if len(moved) != len(yard['removed_kinds']): raise ValueError('Yard test objects changed')
    _, egs, _ = room_script.names(raw, 1)
    prompts = {g + 1 for g, name in enumerate(egs) if name.startswith(yard['removed_triggers'])}
    for i, entity in enumerate(Entities.parse(section0).records):
        if len(entity) == 28 and struct.unpack_from('<I', entity, 12)[0] == room_doors.TRIGGER_TYPE and entity[27] in prompts:
            changed = bytearray(entity)
            struct.pack_into('<i', changed, 4, REMOVED_PICKUP_Y)
            section0 = Entities.parse(section0).replace_record(i, bytes(changed))
            moved.append(i)
    if len(moved) != len(yard['removed_kinds']) + len(prompts) or len(prompts) != 2: raise ValueError('Yard test prompts changed')
    raw = parsed.replace_section(1, 0, section0)
    chain = {g + 1 for g, name in enumerate(egs) if name.startswith(yard['pickup_chain'])}
    raw, removed = room_script.drop_commands(raw, 1, lambda g, c: g == 0 and any(a[3] in chain for a in room_script.actions(c)))
    if len(removed) != 1: raise ValueError('Yard pickup chain changed')
    raw = room_doors.add_spawn(raw, template=room_doors.spawns(hub_native)[0], **yard['spawn'])
    hub = BY_NAME[yard['hub']]
    raw = room_doors.add_exit(raw, room=hub.index, selector=1, spawn=yard['hub_spawn']['spawn_id'],
                              template=room_doors.exit_trigger(hub_native), **yard['exit'])
    gang = yard['gang']
    spawner = bytearray(next(e for e in Entities.parse(RoomObjects.parse(gang_native).records[1].sections[0]).records
                             if len(e) == 28 and struct.unpack_from('<I', e, 12)[0] == SPAWNER_TYPE
                             and e[22] == gang['table'] and not any(e[23:])))
    struct.pack_into('<3i', spawner, 0, *gang['xyz'])
    struct.pack_into('<2H', spawner, 16, *gang['box'])
    raw, ag = room_script.append_batch(raw, 1, [(bytes(spawner), 'EnemySpawner (Yard Gang)')], 'Yard Gang')
    raw, hint = room_script.append_groups(raw, 1, [(EventGroup((say('yard'),)), 'Yard_Seen')])
    return room_script.extend_group(raw, 1, 0, [
        room_script.activate(ag=ag), room_script.if_var(visited, '==', 0, then=room_script.action(eg=hint)),
        room_script.set_var(visited, 1)])


def add_yard_door(raw, door_native, yard=None):
    """Refuge: an exit and arrival point at its left wall, and a native sewer door standing there."""
    yard = yard or YARD
    raw = room_doors.add_exit(raw, room=BY_NAME[yard['room']].index, selector=1, spawn=yard['spawn']['spawn_id'],
                              **yard['hub_exit'])
    raw = room_doors.add_spawn(raw, **yard['hub_spawn'])
    door = bytearray(_entity(door_native, 1, yard['hub_door']['label']))
    struct.pack_into('<3i', door, 0, *yard['hub_door']['xyz'])
    raw, ag = room_script.append_batch(raw, 1, [(bytes(door), 'Door (Yard)')], 'Yard Door')
    return room_script.extend_group(raw, 1, 0, [room_script.activate(ag=ag)])


HINT_ROOM = 'ML_Platform'


def add_power_hint(raw):
    """Platform record 1: while the track power is on, entering shows the live-tracks hint."""
    raw, eg = room_script.append_groups(raw, 1, [(EventGroup((say('live_tracks'),)), 'Live_Tracks_Hint')])
    return room_script.extend_group(raw, 1, 0, [room_script.if_var(TRACK_POWER, '==', 0,
                                                                   then=room_script.action(eg=eg))])


BOILER_GROUP = 'Lift_Object_Die'            # native: runs when the thrown boiler breaks; unlocks the grate


def add_grate_hint(raw):
    """Platform record 1: smashing the boiler also says how the grate works (9-unit pit, see TECHNICAL)."""
    group = _index(room_script.names(raw, 1)[1], BOILER_GROUP, 'event group')
    return room_script.extend_group(raw, 1, group, [say('grate_clear')])


def add_objectives(raw, completed):
    """Refuge record 1: on entry, one objective line chosen by the completion and power flags.

    Completion is tested first: v0.7.0 players could beat the boss through the
    Stairs grate without ever cutting the power.
    """
    _, groups = room_script.counts(raw, 1)
    power, nest, done, check = range(groups + 1, groups + 5)
    raw, _ = room_script.append_groups(raw, 1, [
        (EventGroup((say('goal_power'),)), 'Goal_Power'),
        (EventGroup((say('goal_nest'),)), 'Goal_Nest'),
        (EventGroup((say('goal_done'),)), 'Goal_Done'),
        (EventGroup((room_script.if_var(TRACK_POWER, '==', 0, then=room_script.action(eg=power),
                                        otherwise=room_script.action(eg=nest)),)), 'Goal_Check')])
    return room_script.extend_group(raw, 1, 0, [room_script.if_var(completed, '==', 0, then=room_script.action(eg=check),
                                                                   otherwise=room_script.action(eg=done))])


def entrance_obj(raw, names):
    door = dict(ENTRANCE_DOOR)
    spawn, room = door.pop('spawn'), BY_NAME[door.pop('room')]
    result = room_doors.add_exit(raw, room=room.index, selector=1, spawn=spawn, **door)
    result = room_doors.add_spawn(result, **RETURN_SPAWN)
    native = RoomObjects.parse(raw)
    names = native.names[1].labels
    template = next(e for i, e in enumerate(Entities.parse(native.records[1].sections[0]).records)
                    if names[i].startswith('Door (empty)'))
    doorway = bytearray(template)
    struct.pack_into('<i', doorway, 0, DOORWAY['x'])
    return room_doors.append_entity(result, 1, bytes(doorway), DOORWAY['name'])


def room_table(arm9, names, resources, first_string=None):
    """Extended lookup + descriptors + model arrays + names + Sewer map list (+ chapter messages) at ML_BASE.

    Returns (data, address of the relocated Sewer area room list, address of
    the chapter message entries or None without `first_string`).
    """
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
        if room.source in MAP_FIELDS:    # Sewer area: the chapter is drawn on the Sewer screen
            struct.pack_into('<9i', raw, 0x28, SEWER_AREA, *MAP_FIELDS[room.source][1:])
        models += struct.pack('<I', model)
        labels += room.name.encode('ascii') + b'\0'
        lookup.append(descriptors_at + len(descriptors))
        descriptors += raw
    data = struct.pack(f'<{len(lookup)}I', *lookup) + descriptors + models + labels
    data += bytes(-len(data) % 4)
    list_at = ML_BASE + len(data)
    native = arm9[SEWER_LIST - BASE:SEWER_LIST - BASE + ENTRY_SIZE * SEWER_COUNT]
    if [struct.unpack_from('<I', native, i * ENTRY_SIZE)[0] for i in (0, SEWER_COUNT - 1)] != [51, 67]:
        raise ValueError('Sewer area list moved')
    data += native + map_entries()
    messages_at = None
    if first_string is not None:
        messages_at = ML_BASE + len(data)
        data += message_entries(first_string)
    if len(data) > ML_SPACE: raise ValueError('Chapter tables exceed reserved space')
    return data + bytes(ML_SPACE - len(data)), list_at, messages_at


def extend_arm9(rom, table, glob_count, *, save_rooms=True, map_list=None, messages=None):
    """Grow the kit autoload by ML_SPACE, redirect the room lookup, count appended resources.

    `messages` (chapter message entries address) rewrites the message accessor
    and raises both message-id bounds to cover LINES.
    """
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
    if map_list:
        row = AREA_ROWS + 16 * SEWER_AREA
        patches += [(row + 8, SEWER_LIST, map_list), (row + 12, SEWER_COUNT, SEWER_COUNT + len(ROOMS))]
    if save_rooms:
        limit = FIRST + len(ROOMS)
        patches += [(SAVE_ROOM_CHECK, CMP_R1 | 0x4B, CMP_R1 | limit),
                    (RELOAD_ROOM_CHECK, CMP_R1 | 0x4B, CMP_R1 | limit)]
    if messages:
        if MESSAGE_FIRST + len(LINES) > 0xFF: raise ValueError('Message ids are bytes')
        patches += [(MESSAGE_ACCESSOR + 4 * i, old, value)
                    for i, (old, value) in enumerate(zip(ACCESSOR_NATIVE, message_accessor(messages)))]
        patches += [(at, CMP_R1 | MESSAGE_FIRST, CMP_R1 | (MESSAGE_FIRST + len(LINES))) for at in MESSAGE_BOUNDS]
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
    _, clean_glob, manifest = mod.load_clean()
    clean = {e['name']: e['sha256'] for e in manifest['entries']}
    used = {ENTRANCE + '_app.obj', STATE_TEMPLATE + '_app.obj', MAP_SCREEN, BREAKER_SOURCE + '_app.obj',
            YARD['gang']['source'] + '_app.obj', YARD['hub_door']['source'] + '_app.obj'}
    for room in ROOMS:
        src = next(r for r in native if r.name == room.source)
        used |= {room.source + '_app.obj', names[src.texture]}
    for name in sorted(used):
        if w.sha256(asset(name)) != clean[name]: raise ValueError(f'Chapter source is not the clean native: {name}')
    extras, report, local = {}, {'rooms': {}}, dict(SHARED_FLAGS)
    template = asset(STATE_TEMPLATE + '_app.obj')
    for room in ROOMS:
        src = next(r for r in native if r.name == room.source)
        obj, info = build_room(asset(room.source + '_app.obj'), template, room, src.index, room_names, local)
        if room.encounters and room.name != YARD['room']:       # the Yard's red test objects are moved away instead
            obj, info['hammer_floors_removed'] = open_hammer_floors(obj)
        if room.name in UNSEALED:
            obj = unseal(obj)
            info['unsealed'] = SEAL_GROUP
        if room.name == BOSS['room']:
            obj = stage_boss(obj)
            info['boss'] = {'arena_trigger_units': [v / 4096 for v in BOSS['trigger']], 'size': list(BOSS['trigger_size'])}
        if room.name == YARD['room']:
            obj = stage_yard(obj, asset(BY_NAME[YARD['hub']].source + '_app.obj'), asset(YARD['gang']['source'] + '_app.obj'),
                             VISITED_BASE + room.index)
            info['yard'] = {'gang_table': YARD['gang']['table'], 'spawn_units': [v / 4096 for v in YARD['spawn']['xyz']]}
        if room.name == YARD['hub']:
            obj = add_yard_door(obj, asset(YARD['hub_door']['source'] + '_app.obj'))
            info['yard_door'] = True
        if room.name == GRATE['room']:
            opened = VISITED_BASE + BY_NAME[GRATE['opened_by']].index
            obj = seal_grate(obj, opened)
            info['grate'] = {'locked_until_flag': opened}
        if room.name == BREAKER['room']:
            obj = add_breaker(obj, asset(BREAKER_SOURCE + '_app.obj'))
            info['breaker'] = {'flag': TRACK_POWER, 'switch_units': [v / 4096 for v in BREAKER['switch']]}
        if room.name == HINT_ROOM:
            obj = add_grate_hint(add_power_hint(obj))
            info['hint'] = ['live_tracks', 'grate_clear']
        extras[f'zz_{room.name}_app.obj'] = obj
        extras[f'zz_{room.name}Textures.nsbtx'] = graded_textures(originals[src.texture], room.grade)
        report['rooms'][room.name] = {'index': room.index, 'source': room.source, **info}
    # The objective board needs the completion flag, allocated with the boss room.
    key = f'zz_{OBJECTIVE_ROOM}_app.obj'
    extras[key] = add_objectives(extras[key], local[COMPLETED])
    report['rooms'][OBJECTIVE_ROOM]['objectives'] = {'power': TRACK_POWER, 'completed': local[COMPLETED]}
    entrance = names.index(ENTRANCE + '_app.obj')
    blobs[entrance] = entrance_obj(asset(ENTRANCE + '_app.obj'), room_names)
    map_index = names.index(MAP_SCREEN)
    blobs[map_index] = map_screen(asset(MAP_SCREEN))
    # Chapter lines: appended string slots (same index in both languages).
    from tools.qol_suits_menu import StringSlots, slot_count
    string_indices, firsts = [], set()
    for name in STRING_FILES:
        e = next(x for x in manifest['entries'] if x['name'] == name)
        index = names.index(name)
        firsts.add(slot_count(originals[index]))
        blobs[index] = StringSlots(clean_glob[e['offset']:e['offset'] + e['size']]).grown(
            originals[index], {}, appended=list(LINES.values()))
        string_indices.append(index)
    if len(firsts) != 1: raise ValueError('String files differ in slot count')
    first_string, = firsts
    # Appended models/textures need a word-aligned start; keep the padding in
    # its own unreferenced resource rather than inside an asset.
    padding = -len(glob) % 4
    if padding: extras = {'zz_ml_alignment.bin': bytes(padding), **extras}
    out_names, out_blobs = oscorp_resources.append_resources(names, blobs, extras)
    resources = {room.name: {'objects': out_names.index(f'zz_{room.name}_app.obj'),
                             'texture': out_names.index(f'zz_{room.name}Textures.nsbtx')} for room in ROOMS}
    staged = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(out_names, out_blobs)})
    table, map_list, messages = room_table(arm9, out_names, resources, first_string)
    result, patches = extend_arm9(staged, table, (len(names), len(out_names)), save_rooms=save_rooms,
                                  map_list=map_list, messages=messages)
    check = w.validate_rom(result, target=True)
    fs = next(e for e in check['nitrofs'] if e['name'] == 'Glob.bin')
    out_glob = result[fs['start']:fs['end']]
    out_offsets, checked_names, _ = w.parse_glob(out_glob)
    if checked_names != out_names: raise ValueError('Chapter archive names changed')
    for i, blob in enumerate(out_blobs):
        if out_glob[out_offsets[i]:out_offsets[i + 1]] != blob: raise ValueError(f'Resource mismatch: {out_names[i]}')
        if i < len(names) and i not in (entrance, map_index, table_index, *string_indices) and blob != originals[i]:
            raise ValueError(f'Native resource changed: {names[i]}')
    h = w.parse_header(result)
    digest = w.sha256(result[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']])
    if save_rooms and ARM9_SHA256 and digest != ARM9_SHA256: raise ValueError(f'Unexpected chapter ARM9: {digest}')
    report.update({'schema_version': 1, 'arm9_sha256': digest, 'resources': resources,
                   'arm9_patches': [{'address': hex(a), 'old': hex(o), 'new': hex(n)} for a, o, n in patches],
                   'save_rooms': save_rooms, 'added_resources': list(extras),
                   'messages': {key: {'id': message_id(key), 'string': first_string + i, 'text': text}
                                for i, (key, text) in enumerate(LINES.items())},
                   'local_flags': {f'{room}:{var:#x}': flag for (room, var), flag in sorted(local.items())}})
    return result, report


def build(source=None, output=None, *, save_rooms=True):
    """Development candidate from the kept v0.5.0 kit ROM (build/midnight-line/)."""
    source = Path(source or ROOT / 'build/releases' / STABLE_SHA256 / 'Spider-Man-WoS-modded.nds')
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
