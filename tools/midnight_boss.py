"""Signal Leech: a room-local machine encounter, guarded OBJ script and scoped core data.

Native core data are copied verbatim except health; private harmless warning
and beacon copies select authored meshes. No common-enemy or player hook is
changed here. All delayed work rechecks the live attempt.
"""
from __future__ import annotations
import struct
from tools import room_script as s
from tools.room_events import Command, EventGroup

ROOM = 'ML_SignalCore'
ROOM_ID = 94
CORE_KIND, CORE_HEALTH = 0x21, 12 * 4096
WARNING_KIND = 0x12                          # native electric variant, unused in room placements
MARKER_KIND = 0x13                           # private harmless core marker in room 94 only
ADAPTER_CODE_SIZE = 108
ADAPTER_SPACE = 0x140
LEGACY_CODE_SIZE = 88
DATA_BASE, ACCESSOR = 0x02138FD8, 0x020D1610
RUN, COUNT = 0x127, 0x128
DEAD = (0x129, 0x12A, 0x12B)
CUT, USED, STEP = 0x12C, 0x12D, 0x12E
ADDS = (0x12F, 0x130)
CORE_X = (22, 46, 70)
LANE_HALF = 9
ARC_OFFSETS = (-4, 4)
WARNING = (108, 96, 84)
LIVE = (60, 66, 72)
REST = (60, 48, 36)
POWER_CUT = 300
SOURCES = {'Hive_Map03_app.obj', 'Sewer_Map04_app.obj', 'Downtown_Map14_app.obj',
           'proto01_app.obj', 'Pier_Map04_app.obj', 'Sewer_Map03_app.obj', 'Residential_Map09_app.obj'}


def warning_model():
    """Original untextured, one-node signal panel; no native asset is replaced."""
    from tools import nitro_build as nb, room_compiler as rc
    faces = []
    def panel(x0, y0, x1, y1, z, colour):
        vertices = ((x0, y1, z, 0, 0), (x0, y0, z, 0, 0), (x1, y0, z, 0, 0), (x1, y1, z, 0, 0))
        faces.append((sum(c << (5 * i) for i, c in enumerate(colour)), vertices))
    # The light occupies the lane itself, below the cores rather than
    # covering them. Side posts leave the actual attack target unobscured.
    panel(-LANE_HALF, -.8, LANE_HALF, .5, 18, (31, 26, 2))
    for x in (-7.5, 7.5):
        panel(x - .8, .5, x + .8, 3.7, 1, (31, 26, 2))
        panel(x - .35, 1.6, x + .35, 3.2, 1.1, (3, 3, 4))
    faces.append((sum(c << (5 * i) for i, c in enumerate((31, 26, 2))),
                  ((-LANE_HALF, -.75, -20, 0, 0), (-LANE_HALF, -.75, 18, 0, 0),
                   (LANE_HALF, -.75, 18, 0, 0), (LANE_HALF, -.75, -20, 0, 0))))
    model = nb.RoomModel('SignalWarning', 'signal_root', bytes((7, 248, 0, 16)),
                         (nb.Material('signal', None, None, nb.material_record(8, 8, texture_param=0)),),
                         (rc._stream(faces, 8 * 4096),), ((0, 0),), 8 * 4096,
                         (len(faces) * 4, len(faces), 0, len(faces)), (-4608, -410, -10240, 9216, 2304, 19456), 8 * 4096)
    # s16 bounding box fields use the model's vertex scale. Scale 8 keeps
    # the full-depth floor light inside the native coordinate limits.
    return nb.room_model(model)


def core_model():
    """Bright faceted relay mounted directly on the smashable actor's origin."""
    from tools import nitro_build as nb, room_compiler as rc
    faces = []
    def face(points, colour):
        faces.append((sum(c << (5 * i) for i, c in enumerate(colour)),
                      tuple((*p, 0, 0) for p in points)))
    # All front faces point toward +z. A pale frame and hot pink diamond
    # remain legible against the blue room without a texture dependency.
    face(((-3, 6, 0), (-3, 0, 0), (3, 0, 0), (3, 6, 0)), (7, 9, 14))
    face(((-2.7, 5.7, .1), (-2.7, .3, .1), (2.7, .3, .1), (2.7, 5.7, .1)), (31, 28, 31))
    face(((-2.2, 5.2, .2), (-2.2, .8, .2), (2.2, .8, .2), (2.2, 5.2, .2)), (5, 3, 8))
    face(((0, 5, .3), (-2, 3, .3), (0, 1, .3), (2, 3, .3)), (31, 5, 23))
    face(((0, 4, .4), (-1, 3, .4), (0, 2, .4), (1, 3, .4)), (31, 31, 31))
    model = nb.RoomModel('RelayCore', 'relay_root', bytes((7, 248, 0, 16)),
                         (nb.Material('relay', None, None, nb.material_record(8, 8, texture_param=0)),),
                         (rc._stream(faces, 4 * 4096),), ((0, 0),), 4 * 4096,
                         (len(faces) * 4, len(faces), 0, len(faces)), (-3072, 0, 0, 6144, 6144, 410), 4 * 4096)
    return nb.room_model(model)


def core_adapter(arm9, at, warning_resource=None, core_resource=None):
    """ARM accessor replacement + private native data copies, scoped to room 94.

    The accessor normally returns DATA_BASE + kind*64. Its replacement keeps
    every argument register and writes the data pointer through r0's output slot.
    Native current health is initialized from data+0x14 into object+0x110.
    """
    native = arm9[DATA_BASE - 0x02000000 + CORE_KIND * 64:DATA_BASE - 0x02000000 + (CORE_KIND + 1) * 64]
    if len(native) != 64 or struct.unpack_from('<I', native, 20)[0] != 4096:
        raise ValueError('Native ichor core data changed')
    data = bytearray(native)
    struct.pack_into('<I', data, 20, CORE_HEALTH)
    warning = bytearray(arm9[DATA_BASE - 0x02000000 + WARNING_KIND * 64:DATA_BASE - 0x02000000 + (WARNING_KIND + 1) * 64])
    if len(warning) != 64 or struct.unpack_from('<I', warning)[0] != 0x4000:
        raise ValueError('Native electric warning data changed')
    # 0x020699A0..AC checks flags 0x6000 before environmental damage. The
    # warning keeps its native animation/visual binding and clears that bit.
    struct.pack_into('<I', warning, 0, 0)
    if warning_resource is not None:
        # Data+4 >= 0xB6 selects the native static-renderable path
        # (0x02068FA0..C4); +8 is its model resource, no animation needed.
        struct.pack_into('<2I', warning, 4, 0xB6, warning_resource)
    marker = bytearray(warning)
    if core_resource is not None:
        struct.pack_into('<2I', marker, 4, 0xB6, core_resource)
    else:
        # Read-only audits must still reproduce v0.14.0/v0.15.0 tables
        # from their recorded resource maps. New builds always supply a beacon.
        words = (0xE92D500F, 0xE3510021, 0x0A000001, 0xE3510012, 0x1A00000A,
                 0xE59F2034, 0xE5922000, 0xE3520000, 0x0A000006, 0xE5922000,
                 0xE352005E, 0x1A000003, 0xE3510021, 0x028F201C, 0x128F2058,
                 0xEA000001, 0xE59F200C, 0xE0822301, 0xE5802000, 0xE8BD900F,
                 0x02145C5C, DATA_BASE)
        code = struct.pack('<22I', *words) + data + warning
        offset = (at - ACCESSOR - 8) // 4
        return code, (ACCESSOR, 0xE92D000F, 0xEA000000 | (offset & 0xFFFFFF))
    words = (0xE92D500F,                         # push {r0-r3,ip,lr}
             0xE3510000 | CORE_KIND, 0x0A000003,
             0xE3510000 | WARNING_KIND, 0x0A000001,
             0xE3510000 | MARKER_KIND, 0x1A00000D,
             0xE59F2040, 0xE5922000, 0xE3520000, 0x0A000009,
             0xE5922000, 0xE3520000 | ROOM_ID, 0x1A000006,
             0xE3510000 | CORE_KIND, 0x028F2028,
             0xE3510000 | WARNING_KIND, 0x028F2060,
             0xE3510000 | MARKER_KIND, 0x028F2098, 0xEA000001,
             0xE59F200C, 0xE0822301,            # native table + kind*64
             0xE5802000, 0xE8BD900F,            # str r2,[r0] / pop {r0-r3,ip,pc}
             0x02145C5C, DATA_BASE)
    code = struct.pack('<27I', *words) + data + warning + marker
    offset = (at - ACCESSOR - 8) // 4
    return code, (ACCESSOR, 0xE92D000F, 0xEA000000 | (offset & 0xFFFFFF))


def stage(raw, blob, defeated, say):
    """Append a dedicated state machine to an authored room's record 1."""
    from tools import midnight_rooms as mr
    groups = {}
    _, old_count = s.counts(raw, 1)
    def gid(name):
        if name not in groups: groups[name] = None
        return old_count + list(groups).index(name) + 1
    def group(name, commands):
        gid(name)
        if groups[name] is not None: raise ValueError('Duplicate boss group: ' + name)
        groups[name] = EventGroup(tuple(commands))
    def call(name, frames=0): return s.activate(eg=gid(name), frames=frames)
    def test(var, op, value, yes, no=None):
        return s.if_var(var, op, value, then=s.action(eg=gid(yes)), otherwise=s.action(eg=gid(no)) if no else bytes(4))
    def running(name, commands, *, power=False):
        group(name, [test(RUN, '==', 1, name + '_Check')])
        group(name + '_Check', [test(defeated, '==', 0, name + ('_Power' if power else '_Go'))])
        if power: group(name + '_Power', [test(CUT, '==', 0, name + '_Go')])
        group(name + '_Go', commands)
    def batch(name, entries):
        nonlocal raw
        raw, ag = s.append_batch(raw, 1, entries, name)
        return ag
    def placed(source, label, xy, callback=0, z=0):
        e = mr._placed(mr._native_entity(blob(source + '_app.obj'), label), xy)
        struct.pack_into('<i', e, 8, round(z * mr.U))
        e[23] = callback                         # never inherit a native story callback
        return bytes(e)
    cores = [batch(f'Core {i + 1}', [(placed('Hive_Map03', 'Object (Smashable_IchorBlob) 1', (x, 8), gid(f'Core_{i + 1}')),
                                      f'Object (Relay Core {i + 1})')]) for i, x in enumerate(CORE_X)]
    markers = []
    for i, x in enumerate(CORE_X):
        e = bytearray(placed(*mr.HAZARD, (x, 1.5), z=1))
        e[22] = MARKER_KIND
        markers.append(batch(f'Core {i + 1} Beacon', [(bytes(e), f'Object (Core {i + 1} Beacon)')]))
    gate = batch('Arena Seal', [(placed('Downtown_Map14', 'Object (Gate_Ichor_Wall) 1', (82, 0)), 'Object (Arena Seal)')])
    start = batch('Arena Entry', [(s.trigger(64 * mr.U, 6 * mr.U, (4, 16), gid('Start')), 'Trigger (Arena Entered)')])
    # The unused native electric variant has private harmless data in this
    # room. Blinking arcs warn; kind 0x11's steady live arcs keep native damage.
    lamps, arcs = [], []
    for i, x in enumerate(CORE_X):
        warning_entries = []
        for j, xx in enumerate((x,)):
            e = bytearray(placed(*mr.HAZARD, (xx, 1)))
            e[22] = WARNING_KIND
            warning_entries.append((bytes(e), f'Object (Warning {i + 1}.{j + 1})'))
        lamps.append(batch(f'Lane {i + 1} Warning', warning_entries))
        arcs.append(batch(f'Lane {i + 1} Arc', [(placed(*mr.HAZARD, (xx, 1)), f'Object (Arc {i + 1}.{j + 1})')
                                              for j, xx in enumerate(x + d for d in ARC_OFFSETS)]))
    switch = mr._placed(mr._native_entity(blob('Sewer_Map04_app.obj'), 'Object (Switch)'), (60, 1))
    switch[23] = 0
    trigger = mr._placed(mr._native_entity(blob('Sewer_Map04_app.obj'), 'Trigger (Button Press)'), (58, 5))
    struct.pack_into('<2H', trigger, 20, 12, 16)
    trigger[27] = gid('Breaker')
    breaker = batch('Emergency Breaker', [(bytes(switch), 'Object (Emergency Breaker)'), (bytes(trigger), 'Trigger (Breaker Press)')])
    gangs = (mr.Gang('Pier_Map04', 0x08, (44, 20), (72, 48), 'Leech Crew 1'),
             mr.Gang('Sewer_Map03', 0x0E, (44, 20), (72, 48), 'Leech Crew 2'),
             mr.Gang('Residential_Map09', 0x0C, (44, 20), (72, 48), 'Leech Crew 3'))
    adds = [batch(g.label, [(mr._spawner(blob, g), 'EnemySpawner (' + g.label + ')')]) for g in gangs]
    sound = Command(0x22, struct.pack('<HH', mr.SWITCH_SOUND, 0))
    dark = [s.deactivate(ag=a) for a in (*lamps, *arcs)]
    group('Idle', [s.activate(ag=start), s.activate(entity=(breaker, 1))])
    group('Cleared', [*dark, s.deactivate(ag=gate), s.deactivate(ag=start), s.deactivate(entity=(breaker, 2))])
    group('Start', [test(RUN, '==', 0, 'Start_Check')])
    group('Start_Check', [test(defeated, '==', 0, 'Begin')])
    group('Begin', [s.set_var(RUN, 1), s.deactivate(ag=start), s.activate(ag=gate), s.animate(gate, 1, 0x8D),
                    Command(0x15, bytes(8)),    # clear the arrival hint for the fight
                    *(s.activate(ag=a) for a in (*cores, *markers)), s.activate(entity=(breaker, 2)),
                    call('Crew_1', 30), call('Next', 60)])
    running('Crew_1', [s.activate(ag=adds[0])])
    for i, guard in enumerate(DEAD):
        running(f'Core_{i + 1}', [test(guard, '==', 0, f'Credit_{i + 1}')])
        group(f'Credit_{i + 1}', [s.set_var(guard, 1), s.deactivate(ag=markers[i]),
                                 Command(s.INC_VAR, struct.pack('<HBB', COUNT, 1, 0)), call('Progress')])
    group('Progress', [test(COUNT, '>=', 3, 'Victory', 'Progress_Check')])
    group('Progress_Check', [test(COUNT, '==', 1, 'Crew_2_Once', 'Crew_3_Once')])
    for n, guard in enumerate(ADDS, 2):
        group(f'Crew_{n}_Once', [test(guard, '==', 0, f'Crew_{n}_Queue')])
        group(f'Crew_{n}_Queue', [s.set_var(guard, 1), call(f'Crew_{n}', 45)])
        running(f'Crew_{n}', [s.activate(ag=adds[n - 1])])
    group('Victory', [s.set_var(RUN, 0), s.set_var(defeated, 1), *dark, s.deactivate(ag=gate),
                      *(s.deactivate(ag=a) for a in markers),
                      s.deactivate(ag=start), s.deactivate(entity=(breaker, 2)),
                      *(s.deactivate(ag=a) for a in adds), sound, say(ROOM + '_clear'), call('Victory_Message_End', 240)])
    group('Victory_Message_End', [test(defeated, '==', 1, 'Message_Clear')])
    group('Message_Clear', [Command(0x15, bytes(8))])
    running('Breaker', [test(USED, '==', 0, 'Breaker_Throw')])
    group('Breaker_Throw', [s.set_var(USED, 1), s.set_var(CUT, 1), *dark, s.animate(breaker, 1, 0x19),
                            s.deactivate(entity=(breaker, 2)), sound, call('Power_Return', POWER_CUT)])
    running('Power_Return', [s.set_var(CUT, 0)])
    # Only Next -> Live -> Rest -> Next owns the scheduler. The breaker
    # never starts another loop; Next polls it while the existing chain waits.
    running('Next', [test(CUT, '==', 0, 'Phase', 'Power_Wait')])
    group('Power_Wait', [call('Next', 60)])
    group('Phase', [test(COUNT, '==', 0, 'Phase_1', 'Phase_Check')])
    group('Phase_Check', [test(COUNT, '==', 1, 'Phase_2', 'Phase_3')])
    patterns = (((0,), (1,), (2,)), ((0, 1), (1, 2), (0, 2)), ((0, 2), (1,), (0, 2)))
    for phase, choices in enumerate(patterns):
        prefix = f'P{phase + 1}'
        group(f'Phase_{phase + 1}', [test(STEP, '==', 0, prefix + '_0_Warn', prefix + '_Select')])
        group(prefix + '_Select', [test(STEP, '==', 1, prefix + '_1_Warn', prefix + '_2_Warn')])
        for step, lanes in enumerate(choices):
            key = f'{prefix}_{step}'
            lit = [s.activate(ag=lamps[i]) for i in lanes]
            unlit = [s.deactivate(ag=lamps[i]) for i in lanes]
            running(key + '_Warn', [*dark, *lit, sound,
                                     call(key + '_Blink_Off', 16), call(key + '_Blink_On', 32),
                                     call(key + '_Blink_Off', 48), call(key + '_Blink_On', 56),
                                     call(key + '_Live', WARNING[phase])], power=True)
            running(key + '_Blink_Off', unlit, power=True)
            running(key + '_Blink_On', lit, power=True)
            running(key + '_Live', [test(CUT, '==', 0, key + '_Live_On', key + '_Rest')])
            group(key + '_Live_On', [*unlit, *(s.activate(ag=arcs[i]) for i in lanes), call(key + '_Rest', LIVE[phase])])
            running(key + '_Rest', [*dark, s.set_var(STEP, (step + 1) % 3), call('Next', REST[phase])])
    # The empty source's init group is already repaired by the chapter stage.
    if any(value is None for value in groups.values()): raise ValueError('Unresolved boss group')
    raw, first = s.append_groups(raw, 1, [(g, name) for name, g in groups.items()])
    if first != old_count + 1: raise ValueError('Boss group ids moved')
    return s.extend_group(raw, 1, 0, [*(s.set_var(v, 0) for v in range(RUN, ADDS[-1] + 1)),
                                     test(defeated, '==', 0, 'Idle', 'Cleared')], prepend=True)
