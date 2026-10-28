"""Crane Row cargo drops: the crane delivers the Freight, Dry Dock and Crown crews.

A hook lowers a container into the room, it lands, bursts open and the crew
spawns from it; the crane then lifts the empty shell away. Everything is the
published harmless world-object path (a model record per kind, the native
get/set-position calls the hoist hook already uses) plus the rooms' own event
scripts and native spawners. The container is scenery behind the hero: it has no
collision and no damage, and no player or enemy position is ever written.
"""
import math
import struct
from tools import midnight_rooms as mr, room_script as s, crane_boss as cb, chapter_spectacle_events as ev
from tools import chapter_spectacle_audio as audio, chapter_spectacle_art as art, room_compiler as rc
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
from tools.chapter_renewal_combat import asm
from tools.room_entities import Entities
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects

DROP = 0x12B                 # 0 hanging, 1 lowering, 2 lifting; free in every drop room
CLOSED, OPEN = cb.HOOK, cb.SHIELD
GET_POSITION, SET_POSITION = 0x02069D54, 0x02069CE4
U = 4096
HANG = 74                    # container bottom above the landing deck while it waits
SPEED = 1.6                  # units per frame lowering and lifting
LAND_FRAMES = math.ceil(HANG/SPEED)+4
BURST_FRAMES = 30            # a plain spawner at the open container stays live this long: one arrival
BURST_BOX = (56, 30)
LIFT_FRAMES = 170            # the empty shell stays this long after the burst
CLEAR_FRAMES = 90
RISE = round(SPEED*U)
# room: (name, landing x, deck y, gate (x, y, height) or None, crew batch, progress flag)
ROOMS = {
    97: ('AR_FreightExchange', 244, 0, (212, 60, 120), 'Dock Crew', 144),
    100: ('AR_DryDock', 214, 68, (176, 75, 60), 'Dock Crew', 145),
    105: ('AR_CraneCrown', 164, 16, None, 'Crown Hunters', 146),
}
MODELS = ('zz_CD38_closed.nsbmd', 'zz_CD38_open.nsbmd')


def assembled(text, at):
    code = asm(text, at)
    errors = literal_errors(code, text)+native_branch_errors(code, text, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Cargo drop assembly: '+str(errors))
    return code


def table(rooms=ROOMS):
    """Rows of (room, hanging y, deck y, lowering speed), Q12, ended by a zero room."""
    rows = [struct.pack('<4i', room, (cfg[2]+HANG)*U, cfg[2]*U, RISE) for room, cfg in rooms.items()]
    return b''.join(rows)+bytes(16)


def drop_motion(at, old, rows):
    """Move the container along its own vertical line; every other object is the published tick."""
    return assembled(f'''
        push {{r0-r8,r12,lr}}
        sub sp,sp,#0x14
        mov r4,r0
        ldr r2,[r4,#0x10c]
        cmp r2,#{CLOSED}
        cmpne r2,#{OPEN}
        bne native
        ldrb r2,[r4,#0x168]
        cmp r2,#0
        bne native
        ldr r2,lit0_stats
        ldr r2,[r2]
        cmp r2,#0
        beq native
        ldr r2,[r2]
        ldr r5,lit2_rows
    find:
        ldr r3,[r5]
        cmp r3,#0
        beq native
        cmp r3,r2
        beq found
        add r5,r5,#16
        b find
    found:
        ldr r6,lit1_manager
        ldr r6,[r6]
        cmp r6,#0
        beq native
        ldrb r6,[r6,#0x{0x99+DROP:x}]
        ldr r2,[r4,#0x10c]
        ldr r8,lit3_rise
        cmp r2,#{CLOSED}
        bne lifted
        cmp r6,#1
        ldreq r7,[r5,#8]
        ldrne r7,[r5,#4]
        b move
    lifted:
        cmp r6,#2
        ldreq r7,[r5,#4]
        ldrne r7,[r5,#8]
    move:
        mov r0,sp
        mov r1,r4
        bl 0x{GET_POSITION:08x}
        ldr r0,[sp,#4]
        sub r1,r7,r0
        cmp r1,r8
        movgt r1,r8
        rsb r2,r8,#0
        cmp r1,r2
        movlt r1,r2
        add r0,r0,r1
        str r0,[sp,#4]
        mov r0,r4
        mov r1,sp
        bl 0x{SET_POSITION:08x}
    native:
        add sp,sp,#0x14
        pop {{r0-r8,r12,lr}}
        b 0x{old:08x}
lit0_stats: .word 0x02145c5c
lit1_manager: .word 0x02145c34
lit2_rows: .word 0x{rows:x}
lit3_rise: .word {RISE}
    ''', at)


def mesh(open_):
    """A container hanging from a spreader and hook, origin at the centre of its base, behind the hero."""
    faces = []
    def box(x0, y0, z0, x1, y1, z1, col, sides='front top left right under'):
        for q in rc.box(x0, y0, z0, x1, y1, z1, rc.Look('none'), 1, sides):
            c = tuple(min(31, round(v*q.shade)) for v in col)
            faces.append((sum(v << (5*i) for i, v in enumerate(c)), tuple((*p, 0, 0) for p in q.corners)))
    rust, dark, steel, gold, black, glow = (21, 8, 6), (13, 5, 4), (10, 14, 17), (30, 22, 6), (2, 3, 5), (31, 21, 7)
    if open_:
        box(-19, 0, -18, 19, 1.8, -6, rust)                      # floor and roof stay; the long side is gone
        box(-19, 18.2, -18, 19, 20, -6, rust)
        box(-19, 1.8, -18, 19, 18.2, -17, black, 'front')        # dark cavity
        box(-17, 1.8, -17, 17, 2.6, -7, glow, 'top')             # something hot inside
        for x in (-19, 17.2):box(x, 0, -18, x+1.8, 20, -6, dark)  # the two ends
        for x in (-19.4, 19.4):                                   # doors flung toward the viewer
            quad = ((x, 20, -6), (x, 0, -6), (x+(5.5 if x > 0 else -5.5), 0, 6), (x+(5.5 if x > 0 else -5.5), 20, 6))
            faces.append((sum(v << (5*i) for i, v in enumerate(dark)), tuple((*p, 0, 0) for p in quad)))
            faces.append((sum(v << (5*i) for i, v in enumerate(dark)), tuple((*p, 0, 0) for p in quad[::-1])))
    else:
        box(-19, 0, -18, 19, 20, -6, rust)
        for x in range(-16, 17, 4):box(x-.6, 1.6, -6, x+.6, 18.4, -5.4, dark, 'front left right')
        box(-19, 0, -6, 19, 1.6, -5.2, steel, 'front top')
        box(-19, 18.4, -6, 19, 20, -5.2, steel, 'front top')
        for x in (-19, 17.6):box(x, 0, -6, x+1.4, 20, -5, gold, 'front left right')
        box(-.5, 1.6, -5.4, .5, 18.4, -5, black, 'front')
    box(-22, 20, -16, 22, 22.4, -8, steel)                        # spreader
    for x in (-18, 18):box(x-1.5, 22.4, -13, x+1.5, 27, -11, gold)
    for sign in (-1, 1):                                          # stays to the hook
        quad = ((sign*19, 22.4, -12), (sign*17.6, 22.4, -12), (sign*.4, 30, -12), (sign*1.8, 30, -12))
        faces.append((sum(v << (5*i) for i, v in enumerate(steel)), tuple((*p, 0, 0) for p in quad)))
        faces.append((sum(v << (5*i) for i, v in enumerate(steel)), tuple((*p, 0, 0) for p in quad[::-1])))
    box(-4, 28, -14, 4, 34, -9, gold)
    box(-1.2, 34, -12.6, 1.2, 160, -10.4, steel)                  # the cable runs off the top of the room
    return art.mesh('CD38_'+('open' if open_ else 'closed'), faces)


def models():
    return {MODELS[0]: mesh(False), MODELS[1]: mesh(True)}


def world_rows(rooms, closed, opened):
    """World-data rows (room, kind, flag, off record, on record): both states show the same model."""
    return b''.join(struct.pack('<5I', room, kind, DROP, record, record)
                    for room in rooms for kind, record in ((CLOSED, closed), (OPEN, opened)))


def _placed(blob, kind, xy):
    e = mr._placed(mr._native_entity(blob('proto01_app.obj'), 'Object (Hazard_Electric)'), xy)
    e[22], e[23] = kind, 0
    return bytes(e)


def script(raw, room, blob):
    """Wire one room's crew to arrive by crane; every other group and batch is the published one."""
    name, x, deck, gate, crew, progress = ROOMS[room]
    sounds = audio.IDS
    batches = s.names(raw, 1)[2]
    if crew not in batches or any(b.startswith('Cargo Drop') for b in batches):
        raise ValueError('Published crew batch differs: '+name)
    crew_ag = batches.index(crew)
    # The crew's native spawner is untouched: it keeps its whole-room zone and its clear callback.
    parsed = RoomObjects.parse(raw)
    base = Entities.parse(parsed.records[1].sections[0]).records[sum(s.counts(raw, 1)[0][:crew_ag])]
    if len(base) != 28 or struct.unpack_from('<I', base, 12)[0] != 4:
        raise ValueError('Published crew spawner differs: '+name)
    burst_ag = None
    if room != 105:
        # The native crew spawner arrives from off-screen; a plain one spawns in the opened cargo at once.
        plain = bytearray(base)
        struct.pack_into('<2i', plain, 0, x*U, (deck+22)*U)
        struct.pack_into('<2H', plain, 16, *BURST_BOX)
        plain[23:28] = bytes((0, 0, 0, base[26], 0))
        raw, burst_ag = s.append_batch(raw, 1, [(bytes(plain), 'EnemySpawner (Cargo Burst)')], 'Cargo Burst')
    raw, closed = s.append_batch(raw, 1, [(_placed(blob, CLOSED, (x, deck+HANG)), 'Object (Cargo Drop)')], 'Cargo Drop')
    raw, opened = s.append_batch(raw, 1, [(_placed(blob, OPEN, (x, deck)), 'Object (Cargo Drop Open)')], 'Cargo Drop Open')
    first = s.counts(raw, 1)[1]+1
    order = ('Drop_Arm', 'Drop_Begin', 'Drop_Land', 'Drop_Rise', 'Drop_Clear', 'Drop_Burst_Stop')
    ids = {n: first+i for i, n in enumerate(order)}
    gate_ag = None
    if gate:
        trigger = s.trigger(gate[0]*U, gate[1]*U, (8, gate[2]), ids['Drop_Begin'])
        raw, gate_ag = s.append_batch(raw, 1, [(trigger, 'Trigger (Cargo Drop)')], 'Cargo Drop Gate')
    begin = [s.set_var(DROP, 1), ev.sound(sounds['hoist-tell']), s.activate(eg=ids['Drop_Land'], frames=LAND_FRAMES)]
    if gate_ag is not None:begin.insert(0, s.deactivate(ag=gate_ag))
    groups = (
        ('Drop_Arm', (s.activate(ag=closed), *( (s.activate(ag=gate_ag),) if gate_ag is not None else ()))),
        ('Drop_Begin', tuple(begin)),
        ('Drop_Land', (ev.sound(sounds['hoist-impact']), s.deactivate(ag=closed), s.activate(ag=opened),
                       ev.sound(sounds['motor-open']), s.activate(ag=crew_ag),
                       *((s.activate(ag=burst_ag), s.activate(eg=ids['Drop_Burst_Stop'], frames=BURST_FRAMES))
                         if burst_ag is not None else ()),
                       s.activate(eg=ids['Drop_Rise'], frames=LIFT_FRAMES))),
        ('Drop_Rise', (s.set_var(DROP, 2), s.activate(eg=ids['Drop_Clear'], frames=CLEAR_FRAMES))),
        ('Drop_Clear', (s.deactivate(ag=opened),)),
        ('Drop_Burst_Stop', (s.deactivate(ag=burst_ag),) if burst_ag is not None else ()))
    raw, got = s.append_groups(raw, 1, [(EventGroup(commands), n) for n, commands in groups])
    if got != first:raise ValueError('Drop group ids moved')
    if room == 105:
        # The first crew is the published one; the hunters are the cargo.
        def reinforce(commands):
            late = [c for c in commands if c.opcode == 0x1C and c.operand[2:6] == s.action(ag=crew_ag)]
            if len(late) != 1:raise ValueError('Published reinforcement call differs')
            return tuple(s.activate(ag=closed) if c is late[0] else c for c in commands) + (
                s.set_var(DROP, 1), ev.sound(sounds['hoist-tell']), s.activate(eg=ids['Drop_Land'], frames=LAND_FRAMES))
        raw = ev.rewrite(raw, 1, 'Crown_Reinforcements', reinforce)
    else:
        def reroute(commands):
            hit = [c for c in commands if c.opcode == 0x1D and struct.unpack_from('<H', c.operand)[0] == progress]
            if len(hit) != 1 or hit[0].operand[6:10] != s.action(ag=crew_ag):raise ValueError('Published crew start differs')
            return tuple(Command(c.opcode, c.operand[:6]+s.action(eg=ids['Drop_Arm'])+c.operand[10:]) if c is hit[0] else c
                         for c in commands)
        raw = ev.rewrite(raw, 1, '<EG_INIT>', reroute)
    return s.extend_group(raw, 1, 0, [s.set_var(DROP, 0)], prepend=True)
