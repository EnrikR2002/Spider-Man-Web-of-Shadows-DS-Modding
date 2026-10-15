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
from tools import midnight_rooms, minimap_cbmp, room_catalog, room_doors, room_script, tasm_kit as kit, wos_tool as w
from tools.nitro_texture import TextureArchive
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects

BASE = 0x02000000
ML_BASE = kit.TARGET + kit.RESERVE          # 02157420, after the kit's reserve
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
LOCAL_FLAGS = (*range(268, 276), 138, 139, 251, 250, 249, 248, 247, 246, 245, *range(140, 150))
# Rooms above 91 cannot follow 0xB0+room (268.. are locals): their visited
# flags come from the top of the free pool, 165 downwards, and the map's
# visited test reads them through a stub (`visited_stub`). 150..165 are
# reserved for that and for flags authored rooms name themselves (ROOM_FLAGS).
VISITED_HIGH_FIRST, VISITED_HIGH = 92, 165
ROOM_FLAGS = {'substation_cleared': 150, 'signal_leech_defeated': 151}
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
ARM9_SHA256 = '117c9f7c21c6b2212e95aaf021b3537128de7d6b831cc328e7620021635d6da6'   # chapter over the kit ARM9 (pinned per release)
ENTRANCE = 'Sewer_Save02'
STATE_TEMPLATE = 'Test_Surfaces01'


def visited(index):
    """Visited flag of a chapter room: the native 0xB0+room rule up to room 91, then 165 downwards."""
    if index < VISITED_HIGH_FIRST: return VISITED_BASE + index
    flag = VISITED_HIGH - (index - VISITED_HIGH_FIRST)
    if flag <= max(ROOM_FLAGS.values(), default=149): raise ValueError('Visited flags exhausted')
    return flag


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
    # The Substation (v0.12.0): authored rooms (tools/midnight_rooms), behind a new door at the Yard's left end.
    Room(91, 'ML_Switchyard', midnight_rooms.SOURCE, 'authored', True),   # open yard at dusk: crew, containers, gantry
    Room(92, 'ML_RelayHall', midnight_rooms.SOURCE, 'authored', True),    # timed climb: catwalks that take turns being live
    Room(93, 'ML_Roof', midnight_rooms.SOURCE, 'authored', True),         # arena at night: three waves, replayable
    Room(94, 'ML_SignalCore', midnight_rooms.SOURCE, 'authored', True),   # Signal Leech machine boss
    Room(95, 'ML_ServiceBay', midnight_rooms.SOURCE, 'authored', False), # quiet Substation save/shop room
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
    # The Substation: Yard left wall <-> the Switchyard's right doorway.
    ('ML_Yard', 2): ('ML_Switchyard', 1), ('ML_Switchyard', 1): ('ML_Yard', 2),
    ('ML_Switchyard', 2): ('ML_RelayHall', 1), ('ML_RelayHall', 1): ('ML_Switchyard', 2),
    ('ML_RelayHall', 2): ('ML_Roof', 1), ('ML_Roof', 1): ('ML_RelayHall', 2),
    ('ML_Roof', 2): ('ML_SignalCore', 1), ('ML_SignalCore', 1): ('ML_Roof', 2),
    ('ML_Switchyard', 3): ('ML_ServiceBay', 1), ('ML_ServiceBay', 1): ('ML_Switchyard', 3),
}
# Exits built by add_yard_door/stage_yard/add_substation_door/midnight_rooms.stage, not by sanitize.
AUTHORED_EXITS = {('ML_Refuge', 2), ('ML_Yard', 1), ('ML_Yard', 2), ('ML_Switchyard', 1), ('ML_Switchyard', 2),
                  ('ML_RelayHall', 1), ('ML_RelayHall', 2), ('ML_Roof', 1), ('ML_Roof', 2), ('ML_SignalCore', 1),
                  ('ML_Switchyard', 3), ('ML_ServiceBay', 1)}
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
    'goal_leech': 'Substation 7 is past the Yard. Shut down Signal Leech beyond the control roof.',
    'sealed_grate': 'Sealed from below. The way down must be somewhere on the tracks.',
    'grate_clear': 'The grate is clear. Stand on it, open it with X and drop in with Down.',
    'way_up': 'The nest falls silent. Take the left passage: a shaft climbs back to the Stairs.',
    'yard': 'A freight yard above the line. Someone made camp here, and they have seen you.',
    **midnight_rooms.lines(),               # authored rooms: '<room>' on the first visit, '<room>_clear'
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
# --- The Substation (v0.12.0) -------------------------------------------------
# The Yard's left wall (x -264.75 at floor height) gains a door to the first
# authored room. The native metal barrel that stood 11 units from that wall
# pushed an arriving Spidey back toward the door: it moves along the floor.
SUBSTATION = {
    'room': 'ML_Switchyard', 'hub': 'ML_Yard',
    'door': midnight_rooms.Door('left', -264.75, 0.25, 2, 'Substation', inset=10),
    'barrel': {'kind': 0x23, 'x': round(-165 * 4096)},     # proto01's Smashable_MetalBarrel, from x -253.4
    'hub_door': {'source': 'Sewer_Map13', 'label': 'Door (Misc) 1', 'xyz': (round(-265.75 * 4096), 1024, 0)},
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
# Minimap fields at descriptor +0x28..+0x48 (area, map rectangle endpoints, room
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
    # Authored rooms: retain world bounds here; room_table derives map endpoints
    # from room_minimap's fitted collision plan, and supplies a private CBMP.
    'ML_Switchyard': (5, 450560, 323584, 589824, 393216, -10 * 4096, 84 * 4096, 250 * 4096, 0),
    'ML_RelayHall': (5, 450560, 323584, 589824, 393216, -10 * 4096, 140 * 4096, 120 * 4096, 0),
    'ML_Roof': (5, 450560, 323584, 589824, 393216, 0, 90 * 4096, 214 * 4096, 0),
    'ML_SignalCore': (5, 450560, 323584, 589824, 393216, 0, 70 * 4096, 104 * 4096, 0),
    'ML_ServiceBay': (5, 450560, 323584, 589824, 393216, 0, 42 * 4096, 84 * 4096, 0),
}
# --- Touch-screen map (v0.11.0) --------------------------------------------
# The chapter has its own map screen. The game's area table (16-byte rows at
# 0x0213B840: screen resource, area name string, room-list pointer, entry
# count) has a sixth row, area 5, that no room uses: screen GenericBGBot_4,
# name string 20 (' '), no list. Static init 0x02117F74 writes +0/+4 from two
# literals; +8/+12 are data. Chapter rooms carry area 5, the row names a new
# screen (the Sewer screen's frame and palettes, interior redrawn), the title
# "Midnight Line" and a room list in the chapter block. A room may have several
# list entries, one per palette its cells use (as the native Sewer_Map07 has).
# v0.7.0..v0.10.0 drew a small diagram into the Sewer screen instead (player
# 2026-10-11: it did not show how the rooms connect). See TECHNICAL "Chapter map".
MAP_SOURCE = 'MMSewer.cbmp'
MAP_SCREEN = 'zz_MMMidnight.cbmp'
MAP_TITLE = 'Midnight Line'
MAP_AREA = 5
AREA_ROWS = 0x0213B840                     # 16-byte rows: screen, name string, list, count
AREA_LITERALS = (0x0211802C, 0x02118030)   # row 5 screen resource and name string (static init)
AREA_NATIVE = (0x320, 0x14)                # GenericBGBot_4.cbmp, string 20
# The game gives areas above 4 no map: 0x020E3480 refuses the map views (modes
# 6..8) and 0x020E2194 opens the touch screen on the objectives page when the
# room's area is >= 5, and 0x020E361C ("is this area's map locked?", one
# map-item event per area 0..4) says "locked" for any other area. Lab
# 2026-10-12: with area 5 the Mini-Map button did nothing. Both bounds rise to
# 6 and the default arm answers "not locked", so area 5 always shows its map.
MAP_AREA_BOUNDS = ((0x020E21CC, 0xE3500005, 0xE3500006), (0x020E34B8, 0xE3500005, 0xE3500006))   # cmp r0,#5 -> #6
MAP_LOCKED_DEFAULT = (0x020E3724, 0xE3A00001, 0xE3A00000)   # mov r0,#1 -> mov r0,#0
ENTRY_SIZE = 20
STATE_COLORS = bytes((0xB6, 0xBA, 0xBB, 0xBF))   # every native entry: state colour sources
SLOT_DEFAULT = (0x1042, 0x3D89, 0xE6B2, 0x4E0E, 0xCA52)   # native slot colours in the file
MAP_INTERIOR = (3, 3, 28, 19)              # cells inside the panel border (x0, y0, x1, y1), 200 x 128 pixels
MAP_BORDER_SAMPLES = {'top': (6, 2), 'left': (2, 12), 'right': (28, 12), 'outer': (29, 12), 'bottom': (10, 19)}   # plain border cells
# Palettes whose free 5-colour slots (colours 1, 6, 11) may hold rooms: 1..3 and 0 (free in the Sewer screen) and
# the native Sewer rooms' own 6..10. Lab 2026-10-12, every room marked visited: rooms in palettes 14 and 15
# came out magenta or black and a visited room in palette 13 dark grey (it only looked right while current).
MAP_PALETTES = (1, 2, 3, 0, 8, 9, 10, 7, 6, 11, 12, 4, 5)
MAP_SLOTS_EXCLUDED = ()
FILL, EDGE = 2, 4                          # pixel roles inside a slot (0 = background)
# Room shapes in interior pixels, x right, y down: rectangles (x0, y0, x1, y1)
# and door links (drawn in the first-named room's colours). Every link leaves
# its two rooms on the sides their doors are on. The Gate's ceiling exit and
# the Stairs' floor grate are a matched pair of dotted arrows: the chapter's
# native door pairs do not fit one flat plan (TECHNICAL "Chapter map").
MAP_ROOMS = {
    'ML_Yard': [(7, 14, 31, 30)],
    'ML_Refuge': [(35, 18, 45, 28)],
    'ML_Stairs': [(49, 18, 103, 28), (49, 27, 57, 40)],
    'ML_Platform': [(63, 52, 123, 64), (107, 20, 123, 53)],
    'ML_Station': [(9, 50, 57, 64)],
    'ML_Entry': [(9, 72, 27, 84)],
    'ML_NestShaft': [(98, 66, 106, 98)],
    'ML_NestRest': [(108, 90, 116, 98)],
    'ML_NestThroat': [(118, 88, 126, 120)],
    'ML_NestSpan': [(128, 112, 190, 120)],
    'ML_NestHollow': [(192, 86, 200, 120)],
    'ML_NestGallery': [(174, 82, 190, 96)],
    'ML_NestShrine': [(164, 88, 172, 96)],
    'ML_Venom': [(144, 80, 162, 96)],
    'ML_NestGate': [(134, 66, 142, 96)],
    # The Substation, lower left: roof | relay hall | switchyard, as its doors run.
    'ML_Roof': [(24, 92, 42, 102)],
    'ML_SignalCore': [(4, 90, 20, 106)],
    'ML_RelayHall': [(46, 92, 58, 120)],
    'ML_Switchyard': [(62, 108, 94, 120)],
    'ML_ServiceBay': [(62, 94, 78, 104)],
}
MAP_LINKS = (                               # (room, other room, strip)
    ('ML_Yard', 'ML_Refuge', (31, 22, 35, 26)), ('ML_Refuge', 'ML_Stairs', (45, 22, 49, 26)),
    ('ML_Stairs', 'ML_Platform', (103, 21, 107, 25)), ('ML_Station', 'ML_Platform', (57, 58, 63, 62)),
    ('ML_Entry', 'ML_Station', (21, 64, 25, 72)), ('ML_NestShaft', 'ML_Platform', (100, 64, 104, 66)),
    ('ML_NestShaft', 'ML_NestRest', (106, 93, 108, 97)), ('ML_NestRest', 'ML_NestThroat', (116, 91, 118, 95)),
    ('ML_NestThroat', 'ML_NestSpan', (126, 115, 128, 119)), ('ML_NestSpan', 'ML_NestHollow', (190, 115, 192, 119)),
    ('ML_NestGallery', 'ML_NestHollow', (190, 91, 192, 95)), ('ML_NestShrine', 'ML_NestGallery', (172, 91, 174, 95)),
    ('ML_Venom', 'ML_NestShrine', (162, 91, 164, 95)), ('ML_NestGate', 'ML_Venom', (142, 91, 144, 95)),
    ('ML_Roof', 'ML_RelayHall', (42, 95, 46, 99)), ('ML_RelayHall', 'ML_Switchyard', (58, 114, 62, 118)),
    ('ML_SignalCore', 'ML_Roof', (20, 95, 24, 99)),
)
MAP_SHAFT_LINK = ('ML_NestGate', 'ML_Stairs')    # drawn as two dotted arrows, not as a line
# The Substation hangs off the Yard's left wall, where the panel ends: that door pair is two arrows as well
# (left of the Yard, right of the Switchyard).
MAP_DOOR_ARROWS = (('ML_Yard', 'ML_Switchyard'), ('ML_Switchyard', 'ML_ServiceBay'))
MAP_ARROWS = {                              # (room, pixels): dotted stub with an arrow head
    'ML_NestGate': [(138, 63), (138, 60), (138, 57), (137, 58), (139, 58), (136, 59), (140, 59)],     # up, above the Gate
    'ML_Stairs': [(53, 42), (53, 45), (53, 48), (52, 47), (54, 47), (51, 46), (55, 46)],             # down, under the stairwell
    'ML_Entry': [(8, 80), (7, 80), (6, 80), (5, 80), (4, 80), (5, 79), (5, 81), (6, 78), (6, 82)],     # left, to the Sewer
    'ML_Yard': [(6, 22), (5, 22), (4, 22), (3, 22), (2, 22), (3, 21), (3, 23), (4, 20), (4, 24)],     # left, to the Substation
    'ML_Switchyard': [(94, 114), (95, 114), (96, 114), (97, 114), (98, 114), (97, 113), (97, 115), (96, 112), (96, 116)],   # right, to the Yard
}
MAP_BRANCH_ARROWS={('ML_Switchyard','ML_ServiceBay'):[(61,111),(60,111),(59,111),(58,111),(59,110),(59,112)],
                   ('ML_ServiceBay','ML_Switchyard'):[(78,99),(79,99),(80,99),(81,99),(80,98),(80,100)]}


def map_arrows(room, other): return MAP_BRANCH_ARROWS.get((room,other),MAP_ARROWS.get(room,[]))
SAVE_ROOMS = {'ML_Refuge', 'ML_NestRest', 'ML_NestShrine','ML_ServiceBay'}
BOSS_ROOMS = {'ML_Venom', 'ML_SignalCore'}


def _map_pixels():
    """{(x, y): (room, role)} in interior pixels: outlined rooms, links, arrows, save dots, the boss cross."""
    out = {}
    for room, rects in MAP_ROOMS.items():
        inside = {(x, y) for x0, y0, x1, y1 in rects for x in range(x0, x1) for y in range(y0, y1)}
        for x, y in inside:
            edge = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if (x, y) in out: raise ValueError(f'Map rooms overlap at {x},{y}')
            out[(x, y)] = (room, EDGE if edge else FILL)
        x0, y0, x1, y1 = rects[0]
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        if room in SAVE_ROOMS:
            for dx, dy in ((-1, -1), (0, -1), (-1, 0), (0, 0)): out[(cx + dx, cy + dy)] = (room, EDGE)
        if room in BOSS_ROOMS:
            for k in range(-4, 4): out[(cx + k, cy + k)] = out[(cx - 1 - k, cy + k)] = (room, EDGE)
    for room, other, (x0, y0, x1, y1) in MAP_LINKS:
        for x in range(x0, x1):
            for y in range(y0, y1):
                if (x, y) in out: raise ValueError(f'Map link {room}-{other} overlaps a room at {x},{y}')
                out[(x, y)] = (room, EDGE)
    arrows=list(MAP_ARROWS.items())+[(room,pixels) for (room,other),pixels in MAP_BRANCH_ARROWS.items()]
    for room, pixels in arrows:
        for xy in pixels:
            if xy in out: raise ValueError(f'Map arrow of {room} overlaps at {xy}')
            out[xy] = (room, EDGE)
    return out


def _map_slots(screen, kept):
    """Free 5-colour slots (palette index of the first colour) per palette: unused by every kept cell."""
    used = {(e >> 12) * 16 + c for e in kept for c in set(screen.tile(e & 0x3FF)) if c}
    used.update(STATE_COLORS)                 # engine reads these source colours for every room state
    return {p: [p * 16 + b for b in (1, 6, 11) if not used & set(range(p * 16 + b, p * 16 + b + 5))
                and p * 16 + b not in MAP_SLOTS_EXCLUDED] for p in MAP_PALETTES}


def map_layout(raw):
    """(screen bytes, [(room name, slot, marker x, marker y)]) for the chapter map built from the Sewer screen."""
    screen = minimap_cbmp.Cbmp.parse(raw)
    cx0, cy0, cx1, cy1 = MAP_INTERIOR
    background = screen.screen[15 * screen.width + 3]
    cells = {(x, y): background for x in range(cx0, cx1) for y in range(cy0, cy1)}
    # Sewer rooms reach into the panel border: restore plain border cells.
    def sample(key): return screen.screen[MAP_BORDER_SAMPLES[key][1] * screen.width + MAP_BORDER_SAMPLES[key][0]]
    for x in range(cx0, cx1): cells[(x, cy0 - 1)], cells[(x, cy1)] = sample('top'), sample('bottom')
    for y in range(cy0, cy1): cells[(cx0 - 1, y)], cells[(cx1, y)], cells[(cx1 + 1, y)] = sample('left'), sample('right'), sample('outer')
    kept = [e for i, e in enumerate(screen.screen) if (i % screen.width, i // screen.width) not in cells] + [
        e for xy, e in cells.items() if not (cx0 <= xy[0] < cx1 and cy0 <= xy[1] < cy1)] + [background]
    free = _map_slots(screen, kept)
    pixels = _map_pixels()
    by_cell = {}
    for (x, y), (room, role) in pixels.items():
        if not (0 <= x < 8 * (cx1 - cx0) and 0 <= y < 8 * (cy1 - cy0)): raise ValueError('Map pixel outside the panel')
        by_cell.setdefault((cx0 + x // 8, cy0 + y // 8), {})[(x % 8, y % 8)] = (room, role)
    held = {p: {} for p in free}                 # palette -> {room: slot}
    tiles, entries = [], {}
    for cell in sorted(by_cell, key=lambda c: (c[1], c[0])):
        rooms = sorted({room for room, _ in by_cell[cell].values()})
        fits = [p for p in free if len(set(held[p]) | set(rooms)) <= len(free[p])]
        if not fits: raise ValueError(f'No map palette for cell {cell}: {rooms}')
        palette = max(fits, key=lambda p: (len(set(held[p]) & set(rooms)), -len(held[p])))
        for room in rooms:
            if room not in held[palette]: held[palette][room] = free[palette][len(held[palette])]
        ground = held[palette][rooms[0]] & 15       # a slot's first colour is the background and never changes
        tile = [ground] * 64
        for (px, py), (room, role) in by_cell[cell].items(): tile[py * 8 + px] = (held[palette][room] & 15) + role
        entries[cell] = (palette, len(tiles))
        tiles.append(tile)
    screen, first = screen.with_tiles(tiles)
    colors = {slot + i: value for rooms in held.values() for slot in rooms.values() for i, value in enumerate(SLOT_DEFAULT)}
    cells.update({cell: palette << 12 | first + n for cell, (palette, n) in entries.items()})
    listing = []
    for room in MAP_ROOMS:
        x0, y0, x1, y1 = MAP_ROOMS[room][0]
        for palette in sorted(p for p in held if room in held[p]):
            listing.append((room, held[palette][room], cx0 * 8 + (x0 + x1) // 2, cy0 * 8 + (y0 + y1) // 2))
    return screen.with_screen(cells).with_colors(colors).to_bytes(), listing


def map_entries(listing):
    """Area-list entries (20 bytes): room, record selector, type 0, slot first/last colour, colour sources, marker pixel."""
    return b''.join(struct.pack('<2I', BY_NAME[room].index, 1) + bytes((0, slot, slot + 4)) + STATE_COLORS
                    + bytes((x, y, 0, 0, 0)) for room, slot, x, y in listing)


# --- Strength dial (v0.11.0) -------------------------------------------------
# Kit table (tools/tasm_kit2.s k2_observe/k2_damage): per room, enemy health and
# damage-to-Spidey scale in 1/64ths. Lab 2026-10-11 (research save, stable
# a928843c): chapter sewer rooms hold enemies of 22k..37k health hitting for
# 4096; the Nest's symbiotes have 74k..106k and hit for 8192..9554. The Nest
# now ramps from about 0.6 to 0.8 of that instead of starting at the full gap
# (player 2026-10-11: "got my ass kicked"). The boss room keeps native values.
STRENGTH = {
    'ML_NestShaft': (38, 35), 'ML_NestThroat': (42, 38), 'ML_NestSpan': (45, 42),
    'ML_NestHollow': (48, 45), 'ML_NestGate': (51, 48),
    # The Substation's crews are early-story gangs: at native strength they were "too weak" (player,
    # 2026-10-13). Health 2.25 / 2.5 / 3 times native, damage to Spidey 1.4 / 1.5 / 1.6 times. The
    # Yard on the way there has the same Pier gang: 2 and 1.3 times (the agent's choice, one ramp).
    'ML_Yard': (128, 84), 'ML_Switchyard': (144, 90), 'ML_RelayHall': (160, 96), 'ML_Roof': (192, 104),
    'ML_SignalCore': (192, 104),
}


def strength_dial():
    """Bytes for the kit's dial table: (enemy health, damage) per room 76..115; 0 = native."""
    out = bytearray(2 * kit.DIAL_ROOMS)
    for name, (health, damage) in STRENGTH.items():
        index = BY_NAME[name].index - FIRST
        if not (0 <= index < kit.DIAL_ROOMS and 0 < health < 256 and 0 < damage < 256): raise ValueError('Strength dial range')
        out[2 * index:2 * index + 2] = bytes((health, damage))
    return bytes(out)


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
        return visited(room.index)
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


def state_record(template_raw, room, visited_flag=None):
    """Empty native state record whose init group marks the room visited."""
    parsed = RoomObjects.parse(template_raw)
    record, names = parsed.records[1], parsed.names[1]
    if Entities.parse(record.sections[0]).records or record.raw[3] != 1 or names.category_ends[:2] != (0, 1):
        raise ValueError('State template changed')
    flag = visited(room.index) if visited_flag is None else visited_flag
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


def build_room(source_obj, template_raw, room, source_index, names, local, *, visited_flag=None):
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
        state, state_names = state_record(template_raw, room, visited_flag)
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


# The Entry's first ceiling grate and the Platform's top trapdoor led to rooms
# the chapter does not have (their exit triggers are in SEALED). Spidey could
# still crawl in and find nothing (player 2026-10-11): both native grates are
# now locked shut, and the zone that opened the trapdoor from below is gone.
HATCHES = {'ML_Entry': {'door': 'Door (Sewer Grate Ceiling)'},
           'ML_Platform': {'door': 'Door (Sewer Grate Floor) 1', 'opener': 'Trigger (Main|Grate_Open)'}}


def close_hatch(raw, hatch):
    """Record 1: a dead hatch's grate locked from room load; its opening zone moved out of reach."""
    labels = list(room_script.names(raw, 1)[0][0])
    door = (0, _index(labels, hatch['door'], 'door') + 1)
    if 'opener' in hatch:
        parsed = RoomObjects.parse(raw)
        at = _index(labels, hatch['opener'], 'trigger')
        entity = bytearray(Entities.parse(parsed.records[1].sections[0]).records[at])
        struct.pack_into('<i', entity, 4, REMOVED_PICKUP_Y)
        raw = parsed.replace_section(1, 0, Entities.parse(parsed.records[1].sections[0]).replace_record(at, bytes(entity)))
    return room_script.extend_group(raw, 1, 0, [room_script.door(door, True)])


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


def add_substation_door(raw, door_native, spawn_template, sub=None):
    """Yard: an exit and arrival point at its left wall and a native door standing there."""
    sub = sub or SUBSTATION
    door = sub['door']
    raw = room_doors.add_exit(raw, room=BY_NAME[sub['room']].index, selector=1,
                              spawn=LINKS[(sub['hub'], 2)][1], **door.exit)
    raw = room_doors.add_spawn(raw, template=spawn_template, **door.spawn)
    parsed = RoomObjects.parse(raw)
    section0 = parsed.records[1].sections[0]
    barrels = [i for i, e in enumerate(Entities.parse(section0).records)
               if len(e) >= 24 and struct.unpack_from('<I', e, 12)[0] == OBJECT_TYPE and e[22] == sub['barrel']['kind']]
    if len(barrels) != 1: raise ValueError('Yard barrel changed')
    moved = bytearray(Entities.parse(section0).records[barrels[0]])
    struct.pack_into('<i', moved, 0, sub['barrel']['x'])
    raw = parsed.replace_section(1, 0, Entities.parse(section0).replace_record(barrels[0], bytes(moved)))
    entity = bytearray(_entity(door_native, 1, sub['hub_door']['label']))
    struct.pack_into('<3i', entity, 0, *sub['hub_door']['xyz'])
    raw, ag = room_script.append_batch(raw, 1, [(bytes(entity), 'Door (Substation)')], 'Substation Door')
    return room_script.extend_group(raw, 1, 0, [room_script.activate(ag=ag)])


def door_templates(asset):
    """(spawn, exit trigger) copied by rooms that have none of their own: the Refuge's native ones."""
    hub = asset(BY_NAME[YARD['hub']].source + '_app.obj')
    return room_doors.spawns(hub)[0], room_doors.exit_trigger(hub)


def stage_authored(raw, room, asset):
    """An authored room's object file (tools/midnight_rooms.stage with the chapter's links, flags and lines)."""
    spawn_template, exit_template = door_templates(asset)
    return midnight_rooms.stage(raw, room.name, asset, room_of=lambda n: BY_NAME[n].index, visited=visited(room.index),
                                spawn_template=spawn_template, exit_template=exit_template, links=LINKS, flags=ROOM_FLAGS,
                                say=lambda key: say(key) if key in LINES else None)


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
    power, nest, done, check, leech, post_nest = range(groups + 1, groups + 7)
    raw, _ = room_script.append_groups(raw, 1, [
        (EventGroup((say('goal_power'),)), 'Goal_Power'),
        (EventGroup((say('goal_nest'),)), 'Goal_Nest'),
        (EventGroup((say('goal_done'),)), 'Goal_Done'),
        (EventGroup((room_script.if_var(TRACK_POWER, '==', 0, then=room_script.action(eg=power),
                                        otherwise=room_script.action(eg=nest)),)), 'Goal_Check'),
        (EventGroup((say('goal_leech'),)), 'Goal_Leech'),
        (EventGroup((room_script.if_var(ROOM_FLAGS['signal_leech_defeated'], '==', 0, then=room_script.action(eg=leech),
                                        otherwise=room_script.action(eg=done)),)), 'Goal_Post_Nest')])
    return room_script.extend_group(raw, 1, 0, [room_script.if_var(completed, '==', 0, then=room_script.action(eg=check),
                                                                   otherwise=room_script.action(eg=post_nest))])


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


# Rooms with their own collision file (appended as zz_<room>.bsp) instead of the
# source room's: {room name: bytes}. Nothing ships with one yet; the lab proved
# a compiled tree this way (tools/room_collision.compile_boxes, TECHNICAL
# "Room compiler research").
COLLISION = {}
# Rooms with their own model (zz_<room>.nsbmd) and texture archive instead of
# the source room's model and graded textures: {room name: bytes}. Compiled
# rooms fill all three (tools/room_compiler, TECHNICAL "Room compiler").
MODELS = {}
TEXTURES = {}


MAP_VISITED_SITE = (0x020E1878, 0xE28750B0)  # add r5, r7, #0xB0: the map's visited flag of a listed room


def visited_stub(at):
    """(code + table bytes, replacement instruction) for the map's visited test.

    r5 = 0xB0 + r7 for rooms below 92, else a byte from the table that follows
    the code (one flag per room 92..). Called by `bl` from MAP_VISITED_SITE.
    """
    high = [visited(r.index) for r in ROOMS if r.index >= VISITED_HIGH_FIRST]
    code = (0xE3570000 | VISITED_HIGH_FIRST,      # cmp   r7, #92
            0x328750B0,                           # addlo r5, r7, #0xB0
            0x312FFF1E,                           # bxlo  lr
            0xE28F5008,                           # add   r5, pc, #8      (the table)
            0xE0855007,                           # add   r5, r5, r7
            0xE5555000 | VISITED_HIGH_FIRST,      # ldrb  r5, [r5, #-92]
            0xE12FFF1E)                           # bx    lr
    table = bytes(high) + bytes(-len(high) % 4)
    offset = (at - (MAP_VISITED_SITE[0] + 8)) >> 2
    return struct.pack(f'<{len(code)}I', *code) + table, 0xEB000000 | (offset & 0xFFFFFF)


def aligned(extras, start):
    """`extras` with a padding resource before each model or texture archive that would not start on a word."""
    out, at = {}, start
    for name, blob in extras.items():
        if name.endswith(('.nsbmd', '.nsbtx')) and at % 4:
            pad = bytes(-at % 4)
            out['zz_ml_alignment.bin' if not out else f'zz_ml_alignment{len(out)}.bin'] = pad
            at += len(pad)
        out[name] = blob
        at += len(blob)
    return out


def room_table(arm9, names, resources, first_string=None, listing=()):
    """Extended lookup + descriptors + model arrays + names + chapter map list (+ chapter messages) at ML_BASE.

    Returns (data, address of the chapter's area room list, address of the
    chapter message entries or None without `first_string`).
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
                         resources[room.name].get('bsp', source.bsp), resources[room.name]['objects'])
        struct.pack_into('<I', raw, 0x20, models_at + len(models))
        fields = MAP_FIELDS.get(room.name) or MAP_FIELDS.get(room.source)
        if room.name in midnight_rooms.AUTHORED:
            from tools import room_minimap
            # Plan bounds suffice for the native position transform; no assets
            # are consulted here, keeping table construction deterministic.
            from types import SimpleNamespace
            bounds=tuple(v/4096 for v in (fields[5],fields[8],fields[7],fields[6]))
            fields=room_minimap.projection(SimpleNamespace(bounds=bounds)).fields
        if fields:                       # the chapter's own map area; the other fields only feed the owned-map view
            struct.pack_into('<9i', raw, 0x28, MAP_AREA, *fields[1:])
        if 'detail_map' in resources[room.name]:struct.pack_into('<I',raw,0x4C,resources[room.name]['detail_map'])
        models += struct.pack('<I', resources[room.name].get('model', model))
        labels += room.name.encode('ascii') + b'\0'
        lookup.append(descriptors_at + len(descriptors))
        descriptors += raw
    data = struct.pack(f'<{len(lookup)}I', *lookup) + descriptors + models + labels
    data += bytes(-len(data) % 4)
    list_at = ML_BASE + len(data)
    data += map_entries(listing)
    messages_at = None
    if first_string is not None:
        messages_at = ML_BASE + len(data)
        data += message_entries(first_string)
    data += bytes(-len(data) % 4)
    stub, call = visited_stub(ML_BASE + len(data))
    stub_call = (MAP_VISITED_SITE[0], MAP_VISITED_SITE[1], call)
    data += stub
    # Fixed final 256 bytes hold the room-scoped core adapter and native data
    # copy. Keep this outside the kit code/state and the map/message tables.
    from tools import midnight_boss,roof_waves
    adapter_space = midnight_boss.ADAPTER_SPACE if resources['ML_SignalCore'].get('core_model') is not None else 0x100
    roof_offset=ML_SPACE-adapter_space-0x80
    roof,_=roof_waves.adapter(arm9,ML_BASE+roof_offset)
    if len(data)>roof_offset or len(roof)>0x80:raise ValueError('Chapter tables exceed Roof adapter space')
    data+=bytes(roof_offset-len(data))+roof
    boss_offset = ML_SPACE - adapter_space
    adapter, _ = midnight_boss.core_adapter(arm9, ML_BASE + boss_offset, resources['ML_SignalCore'].get('warning_model'),
                                           resources['ML_SignalCore'].get('core_model'))
    if len(data) > boss_offset or len(adapter) > adapter_space: raise ValueError('Chapter tables exceed reserved space')
    data += bytes(boss_offset - len(data)) + adapter
    return data + bytes(ML_SPACE - len(data)), list_at, messages_at, stub_call


def extend_arm9(rom, table, glob_count, *, save_rooms=True, map_area=None, messages=None, extra=()):
    """Grow the kit autoload by ML_SPACE, redirect the room lookup, count appended resources.

    `map_area` = (room list address, entry count, screen resource, title string)
    fills area row 5; `messages` (chapter message entries address) rewrites the
    message accessor and raises both message-id bounds to cover LINES. The
    kit's strength dial (zeros in the kit image) receives the chapter's values.
    """
    h = w.parse_header(rom)
    raw = rom[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]
    if w.sha256(raw) != kit.ARM9_SHA256: raise ValueError('Chapter requires the pinned kit ARM9')
    table_at = kit.SOURCE + kit.IMAGE
    if (struct.unpack_from('<3I', raw, table_at + 24) != (kit.TARGET, kit.IMAGE, 0)
            or w.u32(raw, kit.ARENA_LOWER) != kit.TARGET + kit.RESERVE or len(raw) != table_at + 36):
        raise ValueError('Unexpected kit autoload layout')
    dial_at = kit.KIT2_OFFSET + kit.DIAL_OFFSET
    image = bytearray(raw[kit.SOURCE:table_at] + bytes(kit.RESERVE - kit.IMAGE) + table)
    dial = strength_dial()
    if any(image[dial_at:dial_at + len(dial)]): raise ValueError('Kit strength dial is not empty')
    image[dial_at:dial_at + len(dial)] = dial
    image = bytes(image)
    new = bytearray(raw[:kit.SOURCE] + image + raw[table_at:table_at + 24]
                    + struct.pack('<3I', kit.TARGET, len(image), 0))
    new_table = kit.SOURCE + len(image)
    struct.pack_into('<2I', new, kit.TABLE_POINTERS, BASE + new_table, BASE + new_table + 36)
    struct.pack_into('<I', new, kit.ARENA_LOWER, kit.TARGET + len(image))
    patches = [(BASE + GLOB_COUNT, *glob_count), (LOOKUP_LITERAL, room_catalog.LOOKUP, ML_BASE), *extra]
    if map_area:
        row = AREA_ROWS + 16 * MAP_AREA
        list_at, count, screen, title = map_area
        patches += [(row + 8, 0, list_at), (row + 12, 0, count), MAP_LOCKED_DEFAULT, *MAP_AREA_BOUNDS,
                    (AREA_LITERALS[0], AREA_NATIVE[0], screen), (AREA_LITERALS[1], AREA_NATIVE[1], title)]
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
    used = {ENTRANCE + '_app.obj', STATE_TEMPLATE + '_app.obj', MAP_SOURCE, BREAKER_SOURCE + '_app.obj',
            YARD['gang']['source'] + '_app.obj', YARD['hub_door']['source'] + '_app.obj'}
    used.add(SUBSTATION['hub_door']['source'] + '_app.obj')
    for room in ROOMS:
        src = next(r for r in native if r.name == room.source)
        used |= {room.source + '_app.obj', names[src.texture]}
        if room.name in midnight_rooms.AUTHORED: used |= midnight_rooms.sources(room.name)
    for name in sorted(used):
        if w.sha256(asset(name)) != clean[name]: raise ValueError(f'Chapter source is not the clean native: {name}')
    extras, report, local = {}, {'rooms': {}}, dict(SHARED_FLAGS)
    template = asset(STATE_TEMPLATE + '_app.obj')
    models, textures, collisions = dict(MODELS), dict(TEXTURES), dict(COLLISION)
    spawn_template, _ = door_templates(asset)
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
                             visited(room.index))
            info['yard'] = {'gang_table': YARD['gang']['table'], 'spawn_units': [v / 4096 for v in YARD['spawn']['xyz']]}
        if room.name == YARD['hub']:
            obj = add_yard_door(obj, asset(YARD['hub_door']['source'] + '_app.obj'))
            info['yard_door'] = True
        if room.name == SUBSTATION['hub']:
            obj = add_substation_door(obj, asset(SUBSTATION['hub_door']['source'] + '_app.obj'), spawn_template)
            info['substation_door'] = True
        if room.name in midnight_rooms.AUTHORED:
            built = midnight_rooms.compiled(room.name, asset)
            models.setdefault(room.name, built.model)
            textures.setdefault(room.name, built.textures)
            collisions.setdefault(room.name, built.collision)
            obj = stage_authored(obj, room, asset)
            info['authored'] = {'quads': built.quads, 'textures': built.by_texture, 'model_bytes': len(built.model),
                                'texture_bytes': len(built.textures), 'collision_bytes': len(built.collision)}
        if room.name == GRATE['room']:
            opened = visited(BY_NAME[GRATE['opened_by']].index)
            obj = seal_grate(obj, opened)
            info['grate'] = {'locked_until_flag': opened}
        if room.name == BREAKER['room']:
            obj = add_breaker(obj, asset(BREAKER_SOURCE + '_app.obj'))
            info['breaker'] = {'flag': TRACK_POWER, 'switch_units': [v / 4096 for v in BREAKER['switch']]}
        if room.name == HINT_ROOM:
            obj = add_grate_hint(add_power_hint(obj))
            info['hint'] = ['live_tracks', 'grate_clear']
        if room.name in HATCHES:
            obj = close_hatch(obj, HATCHES[room.name])
            info['hatch_closed'] = HATCHES[room.name]['door']
        extras[f'zz_{room.name}_app.obj'] = obj
        extras[f'zz_{room.name}Textures.nsbtx'] = (bytes(textures[room.name]) if room.name in textures
                                                   else graded_textures(originals[src.texture], room.grade))
        report['rooms'][room.name] = {'index': room.index, 'source': room.source, **info}
    # The objective board needs the completion flag, allocated with the boss room.
    key = f'zz_{OBJECTIVE_ROOM}_app.obj'
    extras[key] = add_objectives(extras[key], local[COMPLETED])
    report['rooms'][OBJECTIVE_ROOM]['objectives'] = {'power': TRACK_POWER, 'completed': local[COMPLETED]}
    entrance = names.index(ENTRANCE + '_app.obj')
    blobs[entrance] = entrance_obj(asset(ENTRANCE + '_app.obj'), room_names)
    extras[MAP_SCREEN], listing = map_layout(asset(MAP_SOURCE))
    for name, model in models.items():
        extras[f'zz_{BY_NAME[name].name}.nsbmd'] = bytes(model)
    from tools import room_minimap
    for name,spec in midnight_rooms.AUTHORED.items():
        cores=((22,8),(46,8),(70,8)) if spec.boss else ()
        extras[f'zz_{name}_detail.cbmp'],_=room_minimap.build(asset(MAP_SOURCE),midnight_rooms.plan(name,asset),spec.doors,
                                                hazards=spec.hazards,cores=cores,save=spec.save)
    from tools import midnight_boss
    extras['zz_SignalWarning.nsbmd'] = midnight_boss.warning_model()
    extras['zz_RelayCore.nsbmd'] = midnight_boss.core_model()
    for name, collision in collisions.items():          # last: collision files need no alignment, models and textures do
        extras[f'zz_{BY_NAME[name].name}.bsp'] = bytes(collision)
    # Chapter lines: appended string slots (same index in both languages).
    from tools.qol_suits_menu import StringSlots, slot_count
    string_indices, firsts = [], set()
    for name in STRING_FILES:
        e = next(x for x in manifest['entries'] if x['name'] == name)
        index = names.index(name)
        firsts.add(slot_count(originals[index]))
        blobs[index] = StringSlots(clean_glob[e['offset']:e['offset'] + e['size']]).grown(
            originals[index], {}, appended=[*LINES.values(), MAP_TITLE])
        string_indices.append(index)
    if len(firsts) != 1: raise ValueError('String files differ in slot count')
    first_string, = firsts
    # Appended models and textures need a word-aligned start (the offset table
    # and the file list grow by whole words): padding goes into unreferenced
    # resources of its own, never into an asset. The strings and the map
    # screen are not word multiples, so the need changes with every new line.
    extras = aligned(extras, sum(map(len, blobs)))
    out_names, out_blobs = oscorp_resources.append_resources(names, blobs, extras)
    resources = {room.name: {'objects': out_names.index(f'zz_{room.name}_app.obj'),
                             'texture': out_names.index(f'zz_{room.name}Textures.nsbtx'),
                             **({'bsp': out_names.index(f'zz_{room.name}.bsp')} if room.name in collisions else {}),
                             **({'model': out_names.index(f'zz_{room.name}.nsbmd')} if room.name in models else {})}
                 for room in ROOMS}
    resources['ML_SignalCore']['warning_model'] = out_names.index('zz_SignalWarning.nsbmd')
    resources['ML_SignalCore']['core_model'] = out_names.index('zz_RelayCore.nsbmd')
    for name in midnight_rooms.AUTHORED:resources[name]['detail_map']=out_names.index(f'zz_{name}_detail.cbmp')
    at = 4 * (len(out_names) + 1)
    for name, blob in zip(out_names, out_blobs):        # the engine reads models and textures as words
        if name.startswith('zz_') and name.endswith(('.nsbmd', '.nsbtx')) and at % 4:
            raise ValueError(f'Appended resource is not word-aligned: {name}')
        at += len(blob)
    staged = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(out_names, out_blobs)})
    table, map_list, messages, stub_call = room_table(arm9, out_names, resources, first_string, listing)
    from tools import midnight_boss
    _, core_patch = midnight_boss.core_adapter(arm9, ML_BASE + ML_SPACE - midnight_boss.ADAPTER_SPACE, resources['ML_SignalCore']['warning_model'],
                                              resources['ML_SignalCore']['core_model'])
    from tools import roof_waves
    _,roof_patch=roof_waves.adapter(arm9,ML_BASE+ML_SPACE-midnight_boss.ADAPTER_SPACE-0x80)
    result, patches = extend_arm9(staged, table, (len(names), len(out_names)), save_rooms=save_rooms,
                                  map_area=(map_list, len(listing), out_names.index(MAP_SCREEN), first_string + len(LINES)),
                                  messages=messages, extra=(stub_call,core_patch,roof_patch))
    check = w.validate_rom(result, target=True)
    fs = next(e for e in check['nitrofs'] if e['name'] == 'Glob.bin')
    out_glob = result[fs['start']:fs['end']]
    out_offsets, checked_names, _ = w.parse_glob(out_glob)
    if checked_names != out_names: raise ValueError('Chapter archive names changed')
    for i, blob in enumerate(out_blobs):
        if out_glob[out_offsets[i]:out_offsets[i + 1]] != blob: raise ValueError(f'Resource mismatch: {out_names[i]}')
        if i < len(names) and i not in (entrance, table_index, *string_indices) and blob != originals[i]:
            raise ValueError(f'Native resource changed: {names[i]}')
    h = w.parse_header(result)
    digest = w.sha256(result[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']])
    if save_rooms and ARM9_SHA256 and digest != ARM9_SHA256: raise ValueError(f'Unexpected chapter ARM9: {digest}')
    report.update({'schema_version': 1, 'arm9_sha256': digest, 'resources': resources,
                   'arm9_patches': [{'address': hex(a), 'old': hex(o), 'new': hex(n)} for a, o, n in patches],
                   'save_rooms': save_rooms, 'added_resources': list(extras),
                   'map': {'area': MAP_AREA, 'screen': MAP_SCREEN, 'title': MAP_TITLE, 'entries': len(listing)},
                   'strength': {name: {'enemy_health': h / 64, 'damage': d / 64} for name, (h, d) in STRENGTH.items()},
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
