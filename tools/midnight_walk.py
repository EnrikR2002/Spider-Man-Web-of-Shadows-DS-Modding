"""Midnight Line walk tests: scripted play through real doors on a built ROM.

`python tools/midnight_walk.py run NAME [--rom R]` runs one route of ROUTES in
the emulator lab (copied research battery, disposable RAM) and writes
work/midnight-line/walk-NAME.json plus frames under build/boot-tests/.
`python tools/midnight_walk.py all [--rom R]` runs every route (parallel).

A route is a list of steps. Movement, presses and door use are real inputs;
rooms change through the game's own exit triggers and arrivals, so ambushes,
locks and spawns behave as for the player. Lab fixtures are named as such:
- warp: the first room is entered through the Test Upgrades warp;
- place: Spidey is put at a point (used where a climb is not scripted);
- fight: enemies are capped at 1 HP and Spidey mashes Y, turning to the nearest one
  (gather=True also moves them onto him; it broke wave counting in the lab);
- park: enemies are held at a far point while one move is tested;
- boss: the mini-boss (hp, max) pair is capped at 1 HP;
- Spidey's health is refilled and his ability word mirrors the player's
  battery (story abilities 0..4, no Sledgehammer Slam).
Earlier door tours teleported onto triggers and missed rooms that cannot be
crossed on foot (TECHNICAL "Chapter routes"); route points are checked against
the collision tree by tests.
"""
from __future__ import annotations
import argparse
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import midnight_chapter as ch, wos_tool as w

OUT = ROOT / 'work/midnight-line'
U = 4096
PLAYER_ABILITIES = 0x180FFFDF     # player battery 2026-10-07 (stats +0xC): story bits 0..4, kit owned, no bit 5
DOOR_TIMEOUT, SETTLE = 480, 45
RADIUS = 3.5                      # Spidey's half width against walls (measured)


# --- steps -------------------------------------------------------------------
def wait(frames): return ('wait', frames)
def hold(buttons, frames): return ('hold', tuple(buttons.split('+')), frames)
def place(x, y): return ('place', x, y)
def drop(x, y):
    """place, then a real jump: a placed Spidey keeps his old stance (standing in the air, clinging to no wall)."""
    return [place(x, y), hold('B', 3), wait(3)]
def put(x, y):
    """drop, then wait until he stands (idle) again."""
    return [*drop(x, y), ('settle', 150)]
def grate(label, name, x, y=3):
    """Floor grate: stand on its centre, X opens it, Down drops in.

    The pit is 9 units wide and Spidey 7: only within a unit of the centre does
    he fall when it opens; anywhere else he stands on the rim until Down (lab).
    """
    return [*put(x, y), until(label + '_x', in_room(name), 100, 'tapX', fatal=False),
            until(label, in_room(name), 300, 'Down')]
def door(group): return ('door', group)
def mark(label): return ('mark', label)
def boss(max_hp): return ('boss', max_hp)
def fixtures(**on): return ('fixtures', on)
def check(label, cond): return ('check', label, cond)
def until(label, cond, timeout=600, buttons='', fatal=True):
    """Hold `buttons` until cond(state). 'mash' mashes Y; 'tapA', 'tapL', ... tap that button every 45 frames."""
    return ('until', label, cond, timeout, tuple(filter(None, buttons.split('+'))), fatal)
def leave(label, name, way, timeout=900, fatal=True):
    """Hold `way` and mash Y until the next room (walks to the door through whatever attacks him)."""
    return ('until', label, in_room(name), timeout, (way, 'mash'), fatal)
def walk(label, x, timeout=600, fatal=True):
    """Hold Left/Right until Spidey's x passes `x` (release there; momentum carries a little further)."""
    return ('walk', label, x, timeout, fatal)
def fall(label, y, timeout=300):
    """Wait (no input) until Spidey is below `y`."""
    return until(label, lambda s: s.pos is not None and s.pos[1] < y, timeout)
def in_room(name):
    cond = lambda s: s.room == ch.BY_NAME[name].index and s.pos is not None
    cond.room = name                  # lets tests follow a route from room to room
    return cond
def flag(number): return lambda s: bool(s.flags >> number & 1)


def trigger_of(objects, group):
    """Centre (Q12) of the record-0 exit trigger running `group`."""
    from tools.room_entities import Entities
    from tools.room_objects import RoomObjects
    record = RoomObjects.parse(objects).records[0]
    hits = [e for e in Entities.parse(record.sections[0]).records
            if len(e) == 28 and struct.unpack_from('<I', e, 12)[0] == 7 and e[27] == group + 1]
    if len(hits) != 1: raise ValueError(f'Exit group {group} has no single trigger')
    return struct.unpack_from('<2i', hits[0])


def rom_objects(rom_path):
    """{chapter room index: OBJ bytes} of a built ROM."""
    data = Path(rom_path).read_bytes()
    fs = next(e for e in w.validate_rom(data, target=True)['nitrofs'] if e['name'] == 'Glob.bin')
    glob = data[fs['start']:fs['end']]
    offsets, names, _ = w.parse_glob(glob)
    out = {}
    for room in ch.ROOMS:
        i = names.index(f'zz_{room.name}_app.obj')
        out[room.index] = glob[offsets[i]:offsets[i + 1]]
    return out


class Walker:
    """Runs the steps from a frame hook; `buttons` is the live input set."""

    def __init__(self, steps, objects):
        self.steps, self.objects = list(steps), objects
        self.i = self.t = 0
        self.buttons = set()
        self.report = {'checks': [], 'arrivals': [], 'marks': [], 'steps': [], 'trace': [], 'aborted': None}
        self.on = {'fight': True, 'alive': True, 'gather': False, 'park': None}
        self.boss_max = None
        self.scratch = {}

    # -- game state
    def read(self, frame, ram):
        from tools import kit_lab as k, player_trace as p
        stats = struct.unpack_from('<I', ram, k.STATS_POINTER - p.BASE)[0] - p.BASE
        if not 0 <= stats < len(ram) - 0x98: return None
        s = SimpleNamespace(frame=frame, room=struct.unpack_from('<I', ram, stats)[0],
                            flags=int.from_bytes(ram[stats + 0x1C:stats + 0x44], 'little'),
                            pos=None, sample=None, enemies=[], state=None, black=ram[stats + 0x53])
        try: sample = p.sample(ram)
        except ValueError: return s
        s.sample = sample
        s.pos = tuple(v / U for v in sample['position_q12_candidate'])
        s.state = sample['controller']['state_id_candidate'] if sample['controller'] else None
        s.enemies = [e for e in k.enemies(ram) if e['hp'] > 0 and e['state'] != 6]
        return s

    def record(self, label, passed, s, **extra):
        self.report['checks'].append({'check': label, 'passed': bool(passed), 'frame': s.frame, 'room': s.room,
                                      'pos': [round(v, 1) for v in s.pos] if s.pos else None,
                                      'enemies': len(s.enemies), **extra})

    def tick(self, frame, lib):
        from tools import kit_lab as k, player_trace as p
        if frame < 0 or self.report['aborted'] or self.i >= len(self.steps):
            self.buttons.clear(); return
        ptr, ram = k.ram_of(lib)
        s = self.read(frame, ram)
        if s is None: return
        self.fixtures(s, ptr, ram)
        if frame % 60 == 0 and s.pos:                        # coarse trace: position and live enemies
            self.report['trace'].append([frame, s.room, round(s.pos[0], 1), round(s.pos[1], 1),
                                         [[e['hp'], round(e['position'][0] / U), round(e['position'][1] / U)] for e in s.enemies]])
        for _ in range(16):                                  # several instant steps may finish in one frame
            if self.i >= len(self.steps): break
            step = self.steps[self.i]
            if self.t == 0: self.report['steps'].append({'step': self.i, 'kind': step[0], 'frame': frame, 'room': s.room,
                                                         'label': step[1] if isinstance(step[1], str) else None})
            done = getattr(self, 'do_' + step[0])(step, s, ptr, ram)
            if not done:
                self.t += 1; break
            self.i, self.t = self.i + 1, 0
            self.buttons.clear()
            if self.report['aborted']: break
        if self.on['fight'] and s.pos and (s.enemies or self.scratch.get('boss_alive')):
            if frame % 8 < 3: self.buttons.add('Y')          # lab fixture: mash, turning to the nearest enemy
            else: self.buttons.discard('Y')
            near = min(s.enemies, key=lambda e: abs(e['position'][0] / U - s.pos[0]) + abs(e['position'][1] / U - s.pos[1]),
                       default=None)
            if near and frame % 24 < 2 and not self.buttons & {'Left', 'Right'} and abs(near['position'][1] / U - s.pos[1]) < 12:
                self.buttons.add('Right' if near['position'][0] / U > s.pos[0] else 'Left')

    def fixtures(self, s, ptr, ram):
        from tools import kit_lab as k, player_trace as p
        if s.sample is None: return
        if self.on['alive'] and s.frame % 10 == 0:
            hp = struct.unpack_from('<I', ram, s.sample['actor_address'] - p.BASE + 0xE4)[0] - p.BASE
            if 0 <= hp < len(ram) - 0x90:
                c.memmove(ptr + hp + 0x84, struct.pack('<i', struct.unpack_from('<i', ram, hp + 0x88)[0]), 4)
        if self.on['fight'] and s.frame % 12 == 0:
            for n, e in enumerate(s.enemies):
                if e['hp'] > 1: c.memmove(ptr + e['actor'] - p.BASE + 0x44, struct.pack('<i', 1), 4)
                if self.on['gather']: self.move(e, s.pos, ptr, ram)   # optional: also move them onto Spidey
        if self.on['park'] and s.frame % 6 == 0:             # lab fixture: enemies held away from a move under test
            for e in s.enemies: self.move(e, self.on['park'], ptr, ram)
        if self.boss_max and s.frame % 12 == 0:              # mini-boss: (hp, max) pair like NormalEnemy +0x44
            needle, at, alive = struct.pack('<i', self.boss_max), 0, False
            while (at := ram.find(needle, at + 1)) > 0:
                hp = struct.unpack_from('<i', ram, at - 4)[0]
                if at % 4 or not 0 < hp <= self.boss_max: continue
                alive = True
                if hp > 1:
                    c.memmove(ptr + at - 4, struct.pack('<i', 1), 4)
                    self.report.setdefault('boss_capped', s.frame)
                mot = struct.unpack_from('<I', ram, at - 0x48 + 0x30)[0] - p.BASE
                if 0 < mot < len(ram) - 0x300 and mot % 4 == 0 and struct.unpack_from('<I', ram, mot)[0] == at - 0x48 + p.BASE:
                    k.teleport(ptr, ram, mot, int((s.pos[0] + 4) * U), int(s.pos[1] * U))
                    self.report.setdefault('boss_gathered', s.frame)
            self.scratch['boss_alive'] = alive

    @staticmethod
    def move(enemy, xy, ptr, ram):
        """Lab placement of one enemy; a half-freed actor (wild coordinates) is left alone."""
        from tools import kit_lab as k, player_trace as p
        mot = struct.unpack_from('<I', ram, enemy['actor'] - p.BASE + 0x30)[0] - p.BASE
        if not 0 < mot < len(ram) - 0x300 or any(abs(v) > 4000 * U for v in enemy['position']): return
        try: k.teleport(ptr, ram, mot, int(xy[0] * U), int(xy[1] * U))
        except struct.error: pass

    # -- steps
    def do_wait(self, step, s, ptr, ram): return self.t >= step[1]

    def do_hold(self, step, s, ptr, ram):
        if self.t >= step[2]: return True
        self.buttons.clear(); self.buttons.update(step[1]); return False

    def do_settle(self, step, s, ptr, ram):
        return self.t >= step[1] or (self.t >= 20 and s.state == 0)

    def do_place(self, step, s, ptr, ram):
        from tools import kit_lab as k, player_trace as p
        if s.sample is None: return self.timeout(step, s, 300, 'place needs a live Spidey')
        k.teleport(ptr, ram, s.sample['motion_address'] - p.BASE, int(step[1] * U), int(step[2] * U))
        return True

    def do_mark(self, step, s, ptr, ram):
        self.report['marks'].append({'mark': step[1], 'frame': s.frame, 'room': s.room,
                                     'pos': [round(v, 1) for v in s.pos] if s.pos else None})
        return True

    def do_boss(self, step, s, ptr, ram):
        self.boss_max = step[1]; return True

    def do_fixtures(self, step, s, ptr, ram):
        self.on.update(step[1]); return True

    def do_check(self, step, s, ptr, ram):
        self.record(step[1], step[2](s), s); return True

    def do_until(self, step, s, ptr, ram):
        _, label, cond, timeout, buttons, fatal = step
        if cond(s):
            self.record(label, True, s, frames=self.t); return True
        if self.t >= timeout:
            self.record(label, False, s, frames=self.t)
            if fatal: self.report['aborted'] = label
            return True
        self.buttons.difference_update(('Left', 'Right', 'Up', 'Down', 'A', 'B', 'X', 'L', 'R'))
        self.buttons.update(b for b in buttons if b != 'mash' and not b.startswith('tap'))
        if 'mash' in buttons:
            if self.t % 8 < 3: self.buttons.add('Y')
            else: self.buttons.discard('Y')
        for n, b in enumerate(b for b in buttons if b.startswith('tap')):   # tapX: 5 frames every 45, staggered
            if (self.t + n * 12) % 45 < 5: self.buttons.add(b[3:])
        return False

    def do_walk(self, step, s, ptr, ram):
        _, label, x, timeout, fatal = step
        if s.pos is None: return self.timeout(step, s, timeout, label, fatal)
        if self.t == 0: self.scratch['dir'] = 'Right' if x > s.pos[0] else 'Left'
        way = self.scratch['dir']
        if (s.pos[0] >= x) if way == 'Right' else (s.pos[0] <= x):
            self.record(label, True, s, frames=self.t); return True
        if self.t >= timeout: return self.timeout(step, s, timeout, label, fatal)
        self.buttons.difference_update(('Left', 'Right'))
        self.buttons.add(way)
        return False

    def do_door(self, step, s, ptr, ram):
        from tools import kit_lab as k, player_trace as p
        if self.t == 0:
            if s.sample is None or s.room not in self.objects: return self.timeout(step, s, 0, f'door {step[1]}')
            x, y = trigger_of(self.objects[s.room], step[1])
            k.teleport(ptr, ram, s.sample['motion_address'] - p.BASE, x, y)
            self.scratch.update(origin=s.room, since=None)
            return False
        if s.room != self.scratch['origin'] and s.pos is not None:
            if self.scratch['since'] is None: self.scratch['since'] = self.t
            if self.t - self.scratch['since'] >= SETTLE:
                self.report['arrivals'].append({'from': self.scratch['origin'], 'group': step[1], 'room': s.room,
                                                'frame': s.frame, 'pos': [round(v, 1) for v in s.pos]})
                return True
            return False
        return self.timeout(step, s, DOOR_TIMEOUT, f'door {step[1]} of room {self.scratch["origin"]}') if self.t >= DOOR_TIMEOUT else False

    def timeout(self, step, s, limit, label, fatal=True):
        if self.t < limit: return False
        self.record(label, False, s, frames=self.t)
        if fatal: self.report['aborted'] = label
        return True


# --- routes ------------------------------------------------------------------
def room(name): return ch.BY_NAME[name].index


def local_flag(name, var):
    """Chapter flag a clone's native variable is remapped to (build order allocation)."""
    from tools import midnight_line
    return midnight_line.ch_local_flags()[(name, var)]


BOSS_MAX_HP = 2048000             # Mini-Boss 06 (TECHNICAL "The Nest and the boss room")
black = lambda s: s.black == 1
red = lambda s: s.black == 0


def descend(label, centre, gap):
    """Real walk down a Hive shaft (40 wide around `centre`) from its upper platform level.

    Template (collision scan): platform at 130 and 34 (centre +-10), ledge at
    96..100 with one 9-unit gap at the `gap` wall (-1 left, +1 right), wedge
    under that gap (top 62), floor near 0. An ichor blob sits mid-platform at
    34, so Spidey leaves that platform on the side he landed on.
    """
    edge = centre + gap * 14           # inside the 9-unit gap beside the wall
    return [walk(f'{label}_off_the_platform', edge), fall(f'{label}_through_the_ledge_gap', 90),
            fall(f'{label}_onto_the_wedge', 75), walk(f'{label}_off_the_wedge', centre - gap * 5),
            fall(f'{label}_past_the_wedge', 50), walk(f'{label}_off_the_low_platform', centre - gap * 14),
            fall(f'{label}_to_the_floor', 20), wait(40)]          # land before steering: Right in the air grabs the wall


def routes():
    """{name: (start room, start spawn, preset flags, steps)}. Coordinates are world units.

    Each route starts with the lab warp and immediately takes a real door, so
    every room under test is entered the way the player enters it. Fights are
    not deterministic between runs: steps wait on conditions, never on frames.
    """
    power, boiler = ch.TRACK_POWER, local_flag('ML_Platform', 0x62)
    wall_a, wall_b = local_flag('ML_NestSpan', 0x7F), local_flag('ML_NestSpan', 0x80)
    completed = local_flag(*ch.COMPLETED)
    seals = [local_flag(name, var) for name, var in (('ML_NestShaft', 0x3B), ('ML_NestThroat', 0x3A),
                                                     ('ML_NestSpan', 0x39), ('ML_NestHollow', 0x38), ('ML_NestGate', 0x37))]
    unsealed = lambda s: not any(s.flags >> f & 1 for f in seals)
    bx, by, _ = ch.BREAKER['switch']
    breaker = ((bx + ch.BREAKER['trigger_dx']) / U + 2, (by + ch.BREAKER['trigger_dy']) / U + 1.5)
    out = {}
    # Way in: the Stairs grate is sealed, the breaker cuts the power, the boiler
    # comes off the Platform grate and X on it drops into the Shaft.
    out['way-in'] = ('ML_Stairs', 3, (), [
        wait(60), fixtures(fight=False, park=(300, 125)), *put(-10, 5), mark('on-sealed-grate'),
        hold('X', 6), wait(90), hold('Down', 20), wait(60),
        check('stairs_grate_sealed_before_the_loop', in_room('ML_Stairs')), mark('sealed-grate-hint'),
        *put(*breaker), hold('Left', 3), until('breaker_cuts_track_power', flag(power), 300, 'tapX'), wait(60),
        door(3), check('stairs_to_platform', in_room('ML_Platform')),
        fixtures(park=(60, 40)), *put(272, 3), hold('Right', 6), wait(20),
        until('boiler_destroyed', flag(boiler), 900, 'tapX'), wait(60),      # X lifts, X throws
        *grate('grate_drops_into_the_shaft', 'ML_NestShaft', 285), wait(SETTLE), mark('shaft-arrival'),
    ])
    # Descent on foot: tracks grate -> Shaft -> Rest -> Throat -> Span. Fliers attack all the way;
    # no door may seal (the Throat's sealed exit with its enemies behind it was a lab softlock).
    out['descent'] = ('ML_Platform', 1, (power, boiler), [
        wait(60), fixtures(park=(60, 40)), *grate('platform_grate_to_shaft', 'ML_NestShaft', 285),
        fixtures(park=None), wait(SETTLE), mark('shaft'),
        # Shaft (Hive_Map07, centre 20): pedestal, funnel, then the template.
        walk('shaft_off_the_pedestal', 6), fall('shaft_to_the_funnel', 172), walk('shaft_into_the_funnel', 19.5),
        fall('shaft_onto_the_platform', 150), *descend('shaft', 20, -1),
        leave('shaft_to_rest', 'ML_NestRest', 'Right'), wait(SETTLE), mark('rest'),
        until('rest_to_throat', in_room('ML_NestThroat'), 600, 'Right'), wait(SETTLE), mark('throat'),
        # Throat (Hive_Map06, centre -20): enters at funnel level from the top-left door.
        walk('throat_into_the_funnel', -20.5), fall('throat_onto_the_platform', 150), *descend('throat', -20, +1),
        leave('throat_to_span', 'ML_NestSpan', 'Right'), wait(SETTLE), mark('span'),
        check('descent_never_seals', unsealed),
    ])
    # Span and Hollow: both red walls fall to Bulldozer Dash (black suit, A on the ground), the Hollow
    # is open where its red floor was, then Gallery and Shrine on foot.
    out['span-hollow'] = ('ML_NestThroat', 1, (), [
        wait(30), leave('throat_to_span', 'ML_NestSpan', 'Right'), wait(SETTLE), mark('span'), wait(240),
        fixtures(fight=False, park=(-330, -30)), *put(-268, 18),
        until('black_suit', black, 400, 'tapL'), mark('span-wall-a'),
        until('span_wall_a_dashed', flag(wall_a), 900, 'Right+tapA'),
        until('span_wall_b_dashed', flag(wall_b), 1200, 'Right+tapA'), wait(30),
        until('red_suit', red, 400, 'tapL', fatal=False), walk('span_into_the_right_chamber', -128, 600, fatal=False),
        *put(-12, 5), fixtures(fight=True, park=None),
        leave('span_to_hollow', 'ML_NestHollow', 'Right'), fixtures(fight=False, park=(0, 140)), wait(SETTLE), mark('hollow'),
        check('arrived_in_the_hollow', in_room('ML_NestHollow')),
        *drop(-15, 106), fall('hollow_gap_without_red_floor', 88), wait(30), fixtures(park=(0, 8)),
        *put(-18, 166), check('hollow_top_reached', in_room('ML_NestHollow')),
        until('hollow_to_gallery', in_room('ML_NestGallery'), 600, 'Left'), fixtures(fight=True, park=None),
        wait(SETTLE), mark('gallery'),
        until('gallery_to_shrine', in_room('ML_NestShrine'), 1200, 'Left'), wait(SETTLE), mark('shrine'),
        check('span_and_hollow_never_seal', unsealed),
    ])
    # Boss room entered from the lower-right corridor: nothing starts or locks outside the arena,
    # the alcove floors are gone, the walls rise with the fight and fall with the boss.
    out['boss'] = ('ML_NestShrine', 2, (), [
        wait(30), until('shrine_to_boss_room', in_room('ML_Venom'), 600, 'Left'), wait(SETTLE), mark('boss-corridor'),
        wait(500), until('boss_corridor_door_still_open', in_room('ML_NestShrine'), 300, 'Right'), wait(SETTLE),
        until('back_into_the_boss_room', in_room('ML_Venom'), 600, 'Left'), wait(SETTLE),
        *drop(160, 49), fall('right_alcove_without_red_floor', 36), wait(30),
        *drop(152.5, 49), mark('boss-wall-opening'), walk('into_the_arena', 137, 300), wait(150),
        mark('boss-fight'), until('walls_seal_the_way_back', lambda s: s.pos and s.pos[0] < 148.5, 240, 'Right', fatal=False),
        wait(120), check('arena_sealed_during_the_fight', lambda s: s.pos and s.pos[0] < 149),
        boss(BOSS_MAX_HP), until('boss_defeated', flag(completed), 3600), wait(300), mark('boss-dead'),
        *drop(27.5, 52), walk('through_the_left_wall_opening', 23.5, 300),    # steer in the air: the wall top is 6 wide
        wait(60), until('left_alcove_without_red_floor', lambda s: s.pos is not None and s.pos[1] < 36, 600, 'tapRight'),
        wait(30),                                 # the pit is 9 wide and he lands on its far rim: short steps back find it
        until('boss_room_to_gate', in_room('ML_NestGate'), 600, 'Left'), wait(SETTLE), mark('gate'),
    ])
    # Way out: Gate from below (boss already beaten), its gap and unsealed top, out through the neck
    # into the Stairs, and the Stairs grate now works as a shortcut back down.
    out['way-out'] = ('ML_Venom', 1, (completed,), [
        wait(30), until('boss_room_to_gate', in_room('ML_NestGate'), 600, 'Left'), wait(SETTLE), mark('gate'),
        fixtures(fight=False, park=(-20, 8)), wait(30),
        *drop(-5, 106), fall('gate_gap_without_red_floor', 88), wait(30),
        *put(-20, 186), wait(240), mark('gate-top'), check('gate_never_seals', unsealed),
        check('still_in_the_gate', in_room('ML_NestGate')),
        # Out through the neck on the wall: run off the pedestal into the right wall, then crawl up.
        until('gate_cling_to_the_wall', lambda s: s.state == 7, 240, 'Right'),
        until('gate_neck_to_stairs', in_room('ML_Stairs'), 400, 'Up'), wait(SETTLE), mark('stairs'),
        fixtures(park=(300, 125)), wait(30), *grate('stairs_grate_open_after_the_loop', 'ML_NestGate', -10, 5),
        wait(SETTLE), mark('gate-from-above'),
        fixtures(park=(-20, 8)), wait(240), check('gate_does_not_seal_from_above', in_room('ML_NestGate')),
        walk('gate_top_pedestal_edge', -6, 300), fall('gate_top_open_below', 172),
    ])
    # The Yard: through the Refuge's new left door into the warehouse tunnel, down into the yard,
    # the gang appears, and back out the same door (then on to the Stairs: the Refuge is no trap).
    out['yard'] = ('ML_Refuge', 0, (), [
        wait(40), until('refuge_to_yard', in_room('ML_Yard'), 400, 'Left'), wait(SETTLE), mark('yard-arrival'),
        check('yard_arrival_in_the_tunnel', lambda s: s.pos is not None and 135 < s.pos[0] < 172 and 40 < s.pos[1] < 56),
        walk('yard_out_of_the_tunnel', 60, 900), wait(60), mark('yard-slope'),
        walk('yard_across_the_floor', -150, 1500, fatal=False), mark('yard-floor'),
        until('yard_gang_appears', lambda s: bool(s.enemies), 600, fatal=False), wait(300), mark('yard-fight'),
        fixtures(fight=False, park=(-250, 5)), wait(30), *put(150, 45),
        until('yard_to_refuge', in_room('ML_Refuge'), 400, 'Right'), fixtures(park=None), wait(SETTLE), mark('refuge-back'),
        check('refuge_arrival_at_the_new_door', lambda s: s.pos is not None and s.pos[0] < 25),
        until('refuge_to_stairs', in_room('ML_Stairs'), 600, 'Right'),
    ])
    return out


# --- runner ------------------------------------------------------------------
def run_child(rom_path, name, spec=None, tag=''):
    """One emulator run of route `name` (or of `spec` = (start room, spawn, preset flags, steps))."""
    from tools import kit_lab as k, player_trace as p
    rom = Path(rom_path)
    source_hash = w.sha256(rom.read_bytes())
    start_room, spawn, preset, steps = spec or routes()[name]
    walker = Walker(steps, rom_objects(rom))
    m = lambda reg, v: struct.pack('<I', 0xE3A00000 | (reg << 12) | v).hex()
    warp = OUT / f'walk-{name}-warp.json'
    w.write_json(warp, [{'addr': 0x020ED7AC, 'hex': m(1, 0), 'expect': m(1, 1)},
                        {'addr': 0x020ED7B4, 'hex': m(2, room(start_room)), 'expect': m(2, 0x46)},
                        {'addr': 0x020ED7DC, 'hex': m(2, 1), 'expect': m(2, 2)},
                        {'addr': 0x020ED7E0, 'hex': m(3, spawn), 'expect': m(3, 0)}])
    done = {'preset': False, 'end': None}
    budget = sum(s[1] if s[0] in ('wait', 'settle') else s[2] if s[0] == 'hold' else s[3] if s[0] in ('until', 'walk') else
                 DOOR_TIMEOUT + SETTLE if s[0] == 'door' else 1 for s in steps) + 120      # worst case; stops when done

    def hook(frame, lib):
        if preset and not done['preset'] and frame + k.TRAINING_START >= 2040:   # before the warp: room init sees them
            ptr, ram = k.ram_of(lib)
            stats = struct.unpack_from('<I', ram, k.STATS_POINTER - p.BASE)[0] - p.BASE
            if 0 <= stats < len(ram) - 0x98:
                flags = int.from_bytes(ram[stats + 0x1C:stats + 0x44], 'little')
                for f in preset: flags |= 1 << f
                c.memmove(ptr + stats + 0x1C, flags.to_bytes(40, 'little'), 40)
                done['preset'] = True
        walker.tick(frame, lib)
        if done['end'] is None and (walker.i >= len(walker.steps) or walker.report['aborted']): done['end'] = frame
        if done['end'] is not None and frame >= done['end'] + 60: return 'stop'

    dest, _ = k._run(rom, f'walk-{name}{tag}', [], frames=budget, bits=PLAYER_ABILITIES, clear=~PLAYER_ABILITIES & 0xFFFFFFFF,
                     patch=str(warp), caps=tuple(range(0, budget, 30)), rams=(), extra_hook=hook,
                     core_options=k.NO_JIT, sparring=True, live_buttons=walker.buttons)
    report = walker.report
    finished = walker.i >= len(walker.steps) and not report['aborted']
    report.update({'schema_version': 1, 'route': name, 'rom_sha256': source_hash, 'finished': finished,
                   'end_frame': done['end'], 'passed': finished and all(x['passed'] for x in report['checks']),
                   'rom_unchanged': w.sha256(rom.read_bytes()) == source_hash, 'captures': str(dest),
                   'frame_offset': k.TRAINING_START,
                   'limit': 'Lab warp into the first room; place/fight/boss fixtures as documented in tools/midnight_walk.py'})
    w.write_json(OUT / f'walk-{name}{tag}.json', report)
    w.write_json(OUT / f'walk-{name}{tag}-{source_hash[:8]}.json', report)
    print('ML_WALK_REPORT ' + str(OUT / f'walk-{name}{tag}.json'), flush=True)


def run(rom, name, tag=''):
    """One route in a child process; `tag` keeps the report and frames of this try (e.g. '-try2')."""
    done = subprocess.run([sys.executable, str(Path(__file__)), '_child', name, '--rom', str(rom), f'--tag={tag}'],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
    lines = [s for s in done.stdout.splitlines() if 'ML_WALK_REPORT ' in s]
    if done.returncode or not lines:
        w.atomic_write(OUT / f'walk-{name}{tag}-error.log', done.stdout.encode('utf-8'))
        raise ValueError(f'Walk {name} failed; inspect work/midnight-line/walk-{name}{tag}-error.log')
    return json.loads((OUT / f'walk-{name}{tag}.json').read_text())


def rooms_of(start, steps):
    """[(room name, step)] following a route statically: an `until` on in_room moves on, a `door` takes its link."""
    current, out = start, []
    for step in steps:
        out.append((current, step))
        if step[0] == 'door': current = ch.LINKS[(current, step[1])][0]
        elif step[0] == 'until' and hasattr(step[2], 'room'): current = step[2].room
    return out


def summary(report):
    failed = [x['check'] for x in report['checks'] if not x['passed']]
    return {'route': report['route'], 'passed': report['passed'], 'finished': report['finished'],
            'checks': len(report['checks']), 'failed': failed, 'aborted': report['aborted'],
            'arrivals': [(a['from'], a['room']) for a in report['arrivals']]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('run', 'all', 'list', '_child'))
    parser.add_argument('name', nargs='?')
    parser.add_argument('--rom', default=str(ROOT / 'build/midnight-line/chapter.nds'))
    parser.add_argument('--jobs', type=int, default=5)
    parser.add_argument('--tag', default='', help='suffix of the report and capture names')
    parser.add_argument('--tries', type=int, default=3, help='all: reruns of a failing route (fights vary between runs)')
    args = parser.parse_args(argv)
    if args.command == 'list':
        for name, (start, spawn, preset, steps) in routes().items(): print(f'{name}: from {start}, {len(steps)} steps')
    elif args.command == '_child': run_child(args.rom, args.name, tag=args.tag)
    elif args.command == 'run': print(json.dumps(summary(run(args.rom, args.name, args.tag))))
    else:
        from concurrent.futures import ThreadPoolExecutor
        results, pending, attempts = {}, list(routes()), {}
        for attempt in range(1, args.tries + 1):
            def attempt_route(n):
                try: return run(args.rom, n, '' if attempt == 1 else f'-try{attempt}')
                except ValueError as error:                   # the emulator run itself failed: counts as a failed try
                    return {'route': n, 'passed': False, 'finished': False, 'checks': [], 'arrivals': [],
                            'aborted': str(error)}
            with ThreadPoolExecutor(args.jobs) as pool:
                reports = list(pool.map(attempt_route, pending))
            for name, report in zip(pending, reports):
                attempts.setdefault(name, []).append([x['check'] for x in report['checks'] if not x['passed']] or report['aborted'])
                results[name] = report
            pending = [n for n in pending if not results[n]['passed']]
            if not pending: break
        rom_hash = w.sha256(Path(args.rom).read_bytes())
        overall = {'schema_version': 1, 'rom_sha256': rom_hash, 'passed': not pending,
                   'routes': {n: {**summary(r), 'failed_attempts': [a for a in attempts[n] if a]} for n, r in results.items()},
                   'limit': 'A route passes when one run passes every check; earlier failed runs are listed (fights vary)'}
        w.write_json(OUT / 'walk-all.json', overall)
        w.write_json(OUT / f'walk-all-{rom_hash[:8]}.json', overall)
        for n, r in overall['routes'].items(): print(json.dumps(r))
        return 0 if overall['passed'] else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
