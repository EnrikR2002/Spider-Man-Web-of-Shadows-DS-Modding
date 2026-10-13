"""Authored chapter rooms: places built from nothing with the room compiler.

Each room is a plan (tools/room_compiler.Room: boxes, looks, scenery) and a
short object script (doors, camera, enemies, props, timed hazards, waves). The
chapter build (tools/midnight_chapter) compiles the plan into the room's
model, texture archive and collision file and stages the object file from the
empty native debug room Test_Surfaces01. Textures are borrowed from native
archives of districts the player has already seen (never Hive_Map08..10 or
Downtown_Map13/14). See TECHNICAL "Room compiler" and "The Substation".
"""
from __future__ import annotations
from dataclasses import dataclass
import struct

from tools import room_author, room_compiler as rcm, room_doors, room_script
from tools.room_compiler import Look, Panel, Room, Solid
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup
from tools.room_objects import RoomObjects

SOURCE = 'Test_Surfaces01'                  # descriptor and empty object file every authored room starts from
U = 4096
# Exit box: centred 3.5 units behind the wall, 12 wide, so it reaches 2.5 units into the doorway. In a doorway
# Spidey stopped 4.4 to 4.65 units from the wall (lab 2026-10-12; 3.5 at walls elsewhere): a box reaching only
# 1.5 overlapped him by 0.6 and one walk in a dozen did not fire.
REACH = 3.5
EXIT_SIZE = (12, 24)
WAVE_GUARDS = (0x12A, 0x12B, 0x12C)         # per-room scratch bytes: wave 2 started, wave 3 started, waves cleared
WAVE_TIMEOUT = 5400                         # frames (90 s) after which the next wave starts even if nobody reported the last one beaten
SPAWNER_TYPE, OBJECT_TYPE = 4, 14
NO_CLING = 1                                # collision surface value: a wall or ceiling Spidey cannot hold on to
HAZARD = ('proto01', 'Object (Hazard_Electric)')   # native electric arc object (a point; hurts on contact)
SOUND = 0x22
SWITCH_SOUND = 0xBC                         # native switch-throw sound (the breaker uses it)


@dataclass(frozen=True)
class Door:
    """A side door: the wall Spidey walks into at floor height, and where he arrives."""
    side: str                               # 'left' or 'right' wall of the room
    wall: float                             # x of that wall
    floor: float
    spawn_id: int
    label: str                              # names the trigger and its exit group
    inset: float = 12.0                     # arrival point, measured from the wall

    @property
    def exit(self):
        x = self.wall - REACH if self.side == 'left' else self.wall + REACH
        return {'center': (round(x * U), round((self.floor + 6) * U), 0), 'size': EXIT_SIZE,
                'trigger_name': f'Trigger (Main|Exit_{self.label})', 'group_name': f'Exit_{self.label}'}

    @property
    def spawn(self):
        x = self.wall + self.inset if self.side == 'left' else self.wall - self.inset
        return {'spawn_id': self.spawn_id, 'xyz': (round(x * U), round((self.floor + 2) * U), 0),
                'facing': 'right' if self.side == 'left' else 'left'}


@dataclass(frozen=True)
class Gang:
    """An enemy spawner copied from a native room: (source room, enemy table id), centre and zone box.

    `tier` is spawner byte +26 (0..2 in native rooms; what it selects is unknown).
    """
    source: str
    table: int
    xy: tuple
    box: tuple
    label: str
    tier: int = 0


@dataclass(frozen=True)
class Prop:
    """A native object (smashable, liftable) copied by its label from a native room's record 1."""
    source: str
    label: str
    xy: tuple
    name: str


@dataclass(frozen=True)
class Authored:
    name: str
    plan: object                            # blob -> room_compiler.Room
    archives: tuple                         # native texture archives the plan borrows from
    doors: tuple
    camera: tuple                           # camera polygons (world units)
    area: tuple = ()                        # x0, y0, x1, y1 holding the anchor points
    spawn_top: float = 12.0                 # floor anchors (where enemies appear) only on floors up to this height
    gangs: tuple = ()                       # spawners that are live from the start
    waves: tuple = ()                       # spawners run one after another: each starts when the one before is beaten
    cleared: str | None = None              # chapter flag name set when the last wave is beaten
    props: tuple = ()
    hazards: tuple = ()                     # phases of electric arcs, each a tuple of (x, y); one phase is live at a time
    hazard_period: int = 100                # frames each phase stays live
    hazard_rest: int = 0                    # frames with nothing live between two phases
    lines: tuple = ()                       # (key, text): 'first' on the first visit, 'clear' when the waves are beaten


def _borrowed(blob, wanted):
    """Textures and palettes for {archive: [names]} (a (source name, new name) pair renames)."""
    textures, palettes = [], []
    for archive, names in wanted.items():
        raw = blob(archive + 'Textures.nsbtx')
        for name in names:
            source, new = name if isinstance(name, tuple) else (name, name)
            texture, palette = rcm.borrow(raw, source, new)
            textures.append(texture); palettes.append(palette)
    return tuple(textures), tuple(palettes)


def _shutter(look, x, floor, facing_right):
    """A shutter at the end of a doorway: one quad on the wall at x."""
    y0, y1 = floor, floor + 14
    corners = ((x, y1, -9), (x, y0, -9), (x, y0, 9), (x, y1, 9)) if facing_right else ((x, y1, 9), (x, y0, 9), (x, y0, -9), (x, y1, -9))
    return rcm.Quad(look, corners, ((0, 0), (0, 1), (1, 1), (1, 0)), 0.9)


# --- The Substation 1: Switchyard ---------------------------------------------
# An open yard at dusk between two brick buildings: a loading dock, stacked
# containers, a transformer block and a steel gantry over them, pylons and the
# skyline behind a fence. A doorway at each end.
SWITCHYARD_TEXTURES = {
    'Pier_Map02': ['skyline01', 'skyline02', 'skyline03', 'Fconcrete02', 'wcutaway01'],
    'Pier_Map01': ['FAsph01', 'Pbeam01', 'gdoor01', 'corugated02'],
    'Pier_Map08': ['corugated01'],
    'Downtown_Map06': ['Build2', 'brick01'],
    'Downtown_Map01': ['Metal2'],
    'Downtown_Map03': ['vent01'],
    'Downtown_Map02': ['Grate', 'WarningStrip'],
}


def switchyard(blob):
    textures, palettes = _borrowed(blob, SWITCHYARD_TEXTURES)
    dusk = (31, 28, 31)
    asphalt = Look('FAsph01', (32, 32), dusk)
    dock = Look('Fconcrete02', (28, 25), dusk)
    stripe = Look('WarningStrip', (10, 10))
    container, container2 = Look('corugated01', (40, 14), dusk), Look('corugated01', (24, 13), (27, 30, 31))
    fence = Look('corugated02', (32, 20), (22, 20, 24))
    brick, facade = Look('brick01', (32, 32), dusk), Look('Build2', (22, 22), dusk)
    metal, vent = Look('Metal2', (24, 20), dusk), Look('vent01', (12, 12))
    plate, beam = Look('Grate', (16, 16), dusk), Look('Pbeam01', (12, 3))
    cut = Look('wcutaway01', (8, 8))
    door = Look('gdoor01', (16, 14))
    theme = {'top': asphalt, 'side': facade, 'under': beam, 'front': cut, 'back': fence}
    solids = (
        Solid(-10, 16, 0, 84, side=facade, under=cut, front=brick),    # building over the left doorway
        Solid(240, 16, 250, 84, side=facade, under=cut, front=brick),  # building over the right doorway
        Solid(22, 0, 58, 10, top=dock, side=stripe),                   # loading dock (clear of the left doorway)
        Solid(92, 0, 132, 14, top=container, side=container, depth=14),           # container
        Solid(100, 14, 124, 27, top=container2, side=container2, depth=8),         # second container on top
        Solid(172, 0, 196, 20, top=vent, side=metal, depth=10),                    # transformer
        Solid(60, 42, 176, 45, top=plate, side=beam, under=beam, front=beam),          # gantry
        Solid(0, 30, 18, 33, top=plate, side=beam, under=beam, front=beam),            # fire escape, left
        Solid(214, 34, 240, 37, top=plate, side=beam, under=beam, front=beam),         # fire escape, right
    )
    sky = [Panel(22 + 64 * i, 20, 86 + 64 * i, 84, Look(f'skyline0{i + 1}', (64, 64)), 1.0, anchor=(22 + 64 * i, 84)) for i in range(3)]
    panels = (Panel(-10, 20, 22, 84, brick, 0.6), Panel(214, 20, 250, 84, brick, 0.6), *sky)
    pylon = Look('Pbeam01', (4, 16), (16, 16, 20))
    scenery = []
    for x in (70, 166):                                               # pylons behind the yard, in front of the fence
        scenery += rcm.box(x - 2, 0, -23, x + 2, 76, -19, pylon, 0.9, 'front left right')
        scenery += rcm.box(x - 14, 60, -23, x + 14, 62, -19, pylon, 0.9, 'front top under')
        scenery += rcm.box(x - 10, 70, -23, x + 10, 72, -19, pylon, 0.9, 'front top under')
    wire = Look('Pbeam01', (64, 64), (4, 4, 6))
    for y, x0, x1 in ((61, -10, 56), (61, 84, 152), (61, 180, 250), (71, -10, 60), (71, 80, 156), (71, 176, 250)):
        scenery.append(rcm.Quad(wire, ((x0, y + 0.3, -21), (x0, y, -21), (x1, y, -21), (x1, y + 0.3, -21))))
    scenery += [_shutter(door, -9.9, 0, True), _shutter(door, 249.9, 0, False)]
    return Room('ML_Switchyard', (-10, 0, 250, 84), theme, solids, panels, tuple(scenery), textures, palettes,
                hidden_shell=('above',), margin=30.0)


# --- The Substation 2: Relay Hall -----------------------------------------------
# A tall machine hall with smooth steel walls nobody can climb. Five catwalks
# zigzag up to a door at the top left; arcs run along four of them, two at a
# time, so the climb is timed. A cable crew waits on the floor.
RELAY_TEXTURES = {
    'Downtown_Map02': ['FloorTileFull', 'DarkConcrete', 'wirewall', 'WireBunch', 'FuseBox', 'Grate', 'WarningStrip', 'Metal'],
    'Downtown_Map01': ['screens01', 'officeCLights'],
    'Downtown_Map06': ['pipe01', 'pipe03'],
    'Pier_Map02': ['wcutaway01'],
    'Pier_Map01': ['gdoor01'],
}
# Tops 18 apart: a held jump rises 27 units, a tapped one 10 (lab 2026-10-12).
RELAY_CATWALKS = ((60, 16, 110, 20), (0, 34, 50, 38), (60, 52, 110, 56), (0, 70, 50, 74), (60, 88, 110, 92))
RELAY_TOP = (0, 106, 34, 110)               # ledge in front of the upper door
RELAY_HEIGHT = 140


def relay_hall(blob):
    textures, palettes = _borrowed(blob, RELAY_TEXTURES)
    cool = (25, 29, 31)
    tiles = Look('FloorTileFull', (24, 24), cool)
    steel = Look('Metal', (16, 16), (26, 29, 31))
    concrete = Look('DarkConcrete', (48, 48), cool)
    plate, stripe = Look('Grate', (16, 16), cool), Look('WarningStrip', (8, 4))
    lights = Look('officeCLights', (30, 30))
    cut, door = Look('wcutaway01', (8, 8)), Look('gdoor01', (16, 14))
    theme = {'top': tiles, 'side': steel, 'under': lights, 'front': cut, 'back': concrete}
    walk = dict(top=plate, side=stripe, under=steel, front=stripe, depth=14)
    top, door_floor = RELAY_HEIGHT, RELAY_TOP[3]
    solids = (
        Solid(110, 16, 120, top, NO_CLING, side=steel, under=cut, front=steel),               # wall over the lower right doorway
        Solid(-10, 0, 0, door_floor, NO_CLING, top=tiles, side=steel, front=steel),           # wall under the upper left doorway
        Solid(-10, door_floor + 16, 0, top, NO_CLING, side=steel, under=cut, front=steel),    # and over it
        *(Solid(*box, **walk) for box in RELAY_CATWALKS),
        Solid(*RELAY_TOP, **walk),
    )
    grid, cables = Look('wirewall', (32, 32), cool), Look('WireBunch', (16, 32))
    screens, fuse = Look('screens01', (20, 20)), Look('FuseBox', (10, 10))
    panels = [Panel(34, 0, 86, top, grid, 0.55)]                         # a lattice of machinery up the middle
    for y in (40, 76, 112):                                            # banks of monitors and a fuse box by each pair of catwalks
        panels += [Panel(8, y, 28, y + 20, screens, 0.95, anchor=(8, y + 20)),
                   Panel(92, y - 18, 102, y - 8, fuse, 0.9, anchor=(92, y - 8))]
    panels += [Panel(54, 0, 66, top, cables, 0.8, anchor=(54, top))]
    copper, pipe = Look('pipe01', (8, 16)), Look('pipe03', (6, 16))
    scenery = []
    for x, look in ((3, copper), (30, pipe), (88, pipe), (106, copper)):   # pipes up the back wall
        scenery += rcm.box(x, 0, -25, x + 4, top, -21, look, 0.9, 'front left right')
    scenery += [_shutter(door, 119.9, 0, False), _shutter(door, -9.9, door_floor, True)]
    return Room('ML_RelayHall', (-10, 0, 120, top), theme, solids, tuple(panels), tuple(scenery), textures, palettes,
                shell_surface=NO_CLING, margin=24.0)


def _rail(box):
    """Arc positions along a catwalk: every 10 units, leaving its ends free."""
    x0, _, x1, top = box
    return tuple((x, top + 1) for x in range(int(x0) + 10, int(x1) - 9, 10))


# --- The Substation 3: Control Roof ---------------------------------------------
# The substation's roof at night: an open arena between a stairwell hut and a
# taller building, two vent blocks to fight around, the city behind a parapet.
# Three waves, each from another district, start when the one before is beaten.
ROOF_TEXTURES = {
    'Residential_Map01': ['skyline04'],
    'Downtown_Map06': ['TopFloor', 'Build3', 'brick01', 'Street'],
    'Downtown_Map03': ['vent01'],
    'Downtown_Map01': ['Metal2'],
    'Downtown_Map02': ['WarningStrip', 'Stucco'],
    'Pier_Map01': ['Pbeam01', 'gdoor01'],
    'Pier_Map02': ['wcutaway01'],
}


def control_roof(blob):
    textures, palettes = _borrowed(blob, ROOF_TEXTURES)
    night = (24, 26, 31)
    roof = Look('TopFloor', (32, 32), (31, 31, 31))
    pad = Look('Street', (40, 25), night)
    brick, tower = Look('brick01', (32, 32), night), Look('Build3', (24, 24), night)
    metal, vent = Look('Metal2', (20, 12), night), Look('vent01', (10, 10), night)
    stripe, parapet = Look('WarningStrip', (8, 4)), Look('Stucco', (32, 10), (14, 16, 22))
    cut, door, beam = Look('wcutaway01', (8, 8)), Look('gdoor01', (16, 14)), Look('Pbeam01', (4, 16), (14, 14, 20))
    theme = {'top': roof, 'side': tower, 'under': cut, 'front': cut, 'back': parapet}
    solids = (
        Solid(180, 16, 214, 90, side=brick, under=cut, front=brick),   # stairwell hut: a covered passage to the door
        Solid(70, 0, 110, 3, top=pad, side=stripe),                    # low pad in the middle
        Solid(30, 0, 48, 12, top=vent, side=metal, depth=10),          # vent block, left
        Solid(132, 0, 150, 12, top=vent, side=metal, depth=10),        # vent block, right
    )
    sky = Look('skyline04', (64, 64))
    panels = [Panel(-64 + 64 * i, 10, 64 * i, 74, sky, 1.0, anchor=(-64 + 64 * i, 74), mirror=bool(i % 2)) for i in range(5)]
    scenery = []
    for x in (60, 120):                                               # antenna masts on the parapet
        scenery += rcm.box(x - 1, 10, -24, x + 1, 64, -22, beam, 0.9, 'front left right')
        scenery += rcm.box(x - 7, 50, -24, x + 7, 51.5, -22, beam, 0.9, 'front top under')
    scenery += rcm.box(8, 10, -25, 24, 30, -17, metal, 0.8, 'front top left right')     # water tank
    scenery.append(_shutter(door, 213.9, 0, False))
    return Room('ML_Roof', (0, 0, 214, 90), theme, solids, tuple(panels), tuple(scenery), textures, palettes,
                hidden_shell=('above',), margin=30.0, sky=80)


AUTHORED = {
    'ML_Switchyard': Authored(
        'ML_Switchyard', switchyard, tuple(SWITCHYARD_TEXTURES),
        doors=(Door('right', 250, 0, 1, 'Yard'), Door('left', -10, 0, 2, 'Relay')),
        camera=(((20, 62), (20, 0), (220, 0), (220, 62)),), area=(4, 0, 236, 80),
        gangs=(Gang('Pier_Map04', 0x08, (120, 28), (180, 60), 'Switchyard Crew'),),
        props=(Prop('proto01', 'Object (Smashable_MetalBarrel)', (150, 0), 'Barrel'),
               Prop('proto01', 'Object (Smashable_MetalBarrel)', (158, 0), 'Barrel 2'),
               Prop('proto01', 'Object (Smashable_TrashCan)', (70, 0), 'Trash Can')),
        lines=(('first', 'Oscorp Substation 7 feeds the Midnight Line. The crew guarding it looks paid.'),)),
    'ML_RelayHall': Authored(
        'ML_RelayHall', relay_hall, tuple(RELAY_TEXTURES),
        doors=(Door('right', 120, 0, 1, 'Switchyard'), Door('left', -10, RELAY_TOP[3], 2, 'Roof')),
        camera=(((20, RELAY_HEIGHT - 22), (20, 0), (90, 0), (90, RELAY_HEIGHT - 22)),), area=(4, 0, 106, RELAY_HEIGHT - 4), spawn_top=4,
        gangs=(Gang('Sewer_Map03', 0x0E, (58, 12), (100, 24), 'Cable Crew'),),
        hazards=(_rail(RELAY_CATWALKS[1]) + _rail(RELAY_CATWALKS[3]), _rail(RELAY_CATWALKS[2]) + _rail(RELAY_CATWALKS[4])),
        hazard_period=90, hazard_rest=50,
        lines=(('first', 'The relay hall. Steel walls give no grip. The catwalks take turns being live.'),)),
    'ML_Roof': Authored(
        'ML_Roof', control_roof, tuple(ROOF_TEXTURES),
        # The door sits at the end of a 34-unit passage so that a fight does not spill out of the room
        # (leaving restarts the waves). No anchors in the passage: nobody appears there.
        doors=(Door('right', 214, 0, 1, 'Relay'),),
        camera=(((20, 52), (20, 0), (186, 0), (186, 52)),), area=(4, 0, 176, 70), spawn_top=4,
        # The zone covers the whole roof: a spawner starts only once Spidey stands well inside its box
        # (lab: 6 units inside was not enough, 10 was).
        waves=(Gang('Pier_Map04', 0x08, (100, 20), (240, 60), 'Wave 1'),
               Gang('Sewer_Map03', 0x0E, (100, 20), (240, 60), 'Wave 2'),
               Gang('Residential_Map09', 0x0C, (100, 20), (240, 60), 'Wave 3')),
        cleared='substation_cleared',
        props=(Prop('proto01', 'Object (Smashable_MetalBarrel)', (16, 0), 'Barrel'),
               Prop('proto01', 'Object (Smashable_MetalBarrel)', (62, 0), 'Barrel 2')),
        lines=(('first', 'The control roof. They knew you were coming: three crews, one after another.'),
               ('clear', 'Substation 7 is yours. The roof is open whenever you want another round.'))),
}

_cache = {}
LAB = {}                                    # lab switches (never set in a release build): see work/rooms/wave_exp.py


def compiled(name, blob):
    """room_compiler.Compiled for an authored room (cached per process)."""
    if name not in _cache: _cache[name] = rcm.compile_room(AUTHORED[name].plan(blob))
    return _cache[name]


def plan(name, blob): return AUTHORED[name].plan(blob)


def lines():
    """{message key: text} of every authored room ('<room>' for the first visit, '<room>_<key>' otherwise)."""
    return {name if key == 'first' else f'{name}_{key}': text for name, spec in AUTHORED.items() for key, text in spec.lines}


def sources(name):
    """Native resources an authored room is made from (the build checks they are clean)."""
    spec = AUTHORED[name]
    return ({a + 'Textures.nsbtx' for a in spec.archives} | {g.source + '_app.obj' for g in (*spec.gangs, *spec.waves)}
            | {p.source + '_app.obj' for p in spec.props} | ({HAZARD[0] + '_app.obj'} if spec.hazards else set()))


def _native_entity(raw, label):
    parsed = RoomObjects.parse(raw)
    labels = parsed.names[1].labels
    entities = Entities.parse(parsed.records[1].sections[0]).records
    matches = [e for e, n in zip(entities, labels) if n == label]
    if len(matches) != 1: raise ValueError(f'Expected one native entity named {label!r}')
    return matches[0]


def _placed(entity, xy):
    out = bytearray(entity)
    struct.pack_into('<3i', out, 0, round(xy[0] * U), round(xy[1] * U), 0)
    return out


def _spawner(blob, gang, dead_group=0):
    """A native plain spawner of the gang's table at its place; `dead_group` (1-based) runs when its wave is beaten."""
    native = blob(gang.source + '_app.obj')
    spawner = _placed(next(e for e in Entities.parse(RoomObjects.parse(native).records[1].sections[0]).records
                           if len(e) == 28 and struct.unpack_from('<I', e, 12)[0] == SPAWNER_TYPE
                           and e[22] == gang.table), gang.xy)
    struct.pack_into('<2H', spawner, 16, *gang.box)
    # +23 2 and +24 1 as on every native ambush spawner that names a group; plain spawners carry zeros.
    mode = LAB.get('wave_bytes', (2, 1))
    spawner[23:28] = bytes((*mode, dead_group, gang.tier, 0)) if dead_group else bytes((0, 0, 0, gang.tier, 0))
    return bytes(spawner)


def stage(raw, name, blob, *, room_of, visited, spawn_template, exit_template, say=None, links=None, flags=None):
    """Object file of an authored room from the sanitized empty room `raw`.

    Doors become exits (record 0 groups 1.. in door order) to `links[(name,
    group)]` = (room name, spawn id) and arrival spawns. Record 1 gains one
    batch for the props and one per gang, wave and hazard phase. Its init
    group starts them, marks the room visited and shows the first-visit line
    once.
    """
    spec = AUTHORED[name]
    say = say or (lambda key: None)
    for group, door in enumerate(spec.doors, 1):
        dest, spawn = links[(name, group)]
        raw = room_doors.add_spawn(raw, template=spawn_template, **door.spawn)
        raw = room_doors.add_exit(raw, room=room_of(dest), selector=1, spawn=spawn, template=exit_template, **door.exit)
    raw = room_author.set_camera(raw, spec.camera)
    room = plan(name, blob)
    tree = rcm.rc.RoomCollision.parse(compiled(name, blob).collision)
    points = room_author.plan_anchors(rcm.surfaces(room), spec.area or room.bounds, floor_top=spec.spawn_top,
                                      solid=lambda x, y: tree.solid_at(x, y) is not None)
    raw = room_author.set_anchors(raw, points)
    if room_script.counts(raw, 1) != ((0,), 1): raise ValueError('Authored rooms start from an empty state record')
    init, groups = [], []                                   # groups: (EventGroup, name), ids follow the init group
    if spec.props:                                          # batch 0 (live from the start) stays empty: every batch is started here
        props = [(bytes(_placed(_native_entity(blob(p.source + '_app.obj'), p.label), p.xy)), f'Object ({p.name})') for p in spec.props]
        raw, ag = room_script.append_batch(raw, 1, props, 'Props')
        init.append(room_script.activate(ag=ag))
    def group_id(index): return 2 + index
    for gang in spec.gangs:
        raw, ag = room_script.append_batch(raw, 1, [(_spawner(blob, gang), f'EnemySpawner ({gang.label})')], gang.label)
        init.append(room_script.activate(ag=ag))
    if spec.waves:
        first = len(groups)                                 # groups first..: start of wave 2.., then the clear group
        wave_ags = []
        for n, gang in enumerate(spec.waves):
            raw, ag = room_script.append_batch(raw, 1, [(_spawner(blob, gang, group_id(first + n)), f'EnemySpawner ({gang.label})')], gang.label)
            wave_ags.append(ag)
        # Each step is a guard group (runs its "go" group once: a scratch byte remembers) and the go group.
        # A wave starts when the one before reports beaten or, failing that, WAVE_TIMEOUT after it started:
        # one lab fight in a dozen never reported its second wave beaten (cause not found).
        if len(spec.waves) - 1 > len(WAVE_GUARDS) - 1: raise ValueError('More waves than guard bytes')
        steps = len(wave_ags)                               # wave 2.., then the clear step
        def guard_id(step): return group_id(first + step)
        def go_id(step): return group_id(first + steps + step)
        for step in range(steps):
            groups.append((EventGroup((room_script.if_var(WAVE_GUARDS[step], '==', 0, then=room_script.action(eg=go_id(step))),)),
                           f'Wave_{step + 2}' if step < steps - 1 else 'Waves_Clear'))
        for step, ag in enumerate(wave_ags[1:]):
            marks = [room_script.set_var(LAB['wave_flags'][step], 1)] if LAB.get('wave_flags') else []
            go = [room_script.set_var(WAVE_GUARDS[step], 1), *marks, room_script.activate(ag=ag, frames=45)]
            if step < steps - 2: go.append(room_script.activate(eg=guard_id(step + 1), frames=WAVE_TIMEOUT))
            groups.append((EventGroup(tuple(go)), f'Wave_{step + 2}_Go'))
        done = [room_script.set_var(WAVE_GUARDS[steps - 1], 1), Command(SOUND, struct.pack('<HH', SWITCH_SOUND, 0))]
        if spec.cleared: done.append(room_script.set_var(flags[spec.cleared], 1))
        if say(f'{name}_clear'): done.append(say(f'{name}_clear'))
        groups.append((EventGroup(tuple(done)), 'Waves_Clear_Go'))
        init += [room_script.set_var(guard, 0) for guard in WAVE_GUARDS[:steps]]
        init += [room_script.activate(ag=wave_ags[0], frames=30), room_script.activate(eg=guard_id(0), frames=WAVE_TIMEOUT)]
    if spec.hazards:
        arc = _native_entity(blob(HAZARD[0] + '_app.obj'), HAZARD[1])
        phase_ags = []
        for n, phase in enumerate(spec.hazards):
            raw, ag = room_script.append_batch(raw, 1, [(bytes(_placed(arc, xy)), f'Object (Arc {n + 1}.{i + 1})') for i, xy in enumerate(phase)],
                                               f'Arcs {n + 1}')
            phase_ags.append(ag)
        first = len(groups)                                 # two groups per phase: live, then rest
        for n, ag in enumerate(phase_ags):
            rest, after = group_id(first + 2 * n + 1), group_id(first + 2 * ((n + 1) % len(phase_ags)))
            groups.append((EventGroup((room_script.activate(ag=ag), room_script.activate(eg=rest, frames=spec.hazard_period))),
                           f'Arcs_{n + 1}_Live'))
            groups.append((EventGroup((room_script.deactivate(ag=ag), room_script.activate(eg=after, frames=spec.hazard_rest))),
                           f'Arcs_{n + 1}_Rest'))
        init.append(room_script.activate(eg=group_id(first), frames=30))
    if say(name):
        groups.append((EventGroup((say(name),)), 'First_Visit'))
        init.append(room_script.if_var(visited, '==', 0, then=room_script.action(eg=group_id(len(groups) - 1))))
    if groups:
        raw, first_id = room_script.append_groups(raw, 1, groups)
        if first_id != group_id(0): raise ValueError('Authored group ids moved')
    init.append(room_script.set_var(visited, 1))
    return room_script.extend_group(raw, 1, 0, init)
