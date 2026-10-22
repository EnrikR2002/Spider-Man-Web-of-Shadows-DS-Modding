"""One complete Rail Skitter: planted gait, carried scythes and shared lifecycle stance."""
import math
import struct
from tools import creature_forge_motion as f, creature_forge_design as d
from tools import chapter_renewal_motion as modes, midnight_enemy_motion as contact
from tools.creature_forge_design import Move
from tools.rush_choreography import ROOT, IDENTITY, axis, mm, mv, add, sub
from tools.kit_choreography import safe_ik
from tools.sca import Sca
from tools.custom_formats import Xbd, Gab
from tools.actor_actions import ActorActions
from tools.animation_rig import AnimationRig

MOVES = (
    Move('Scythe cross', 55, 27, ((7, 10), (14, 18)), 'scissor', 12,
         ((5, 10, .85), (12, 18, .72)), (), 12),
    Move('Loaded switchback', 63, 29, ((13, 19),), 'feint', 25,
         ((2, 7, -.65), (10, 20, 1.7)), (), 13),
    Move('Railbound shear', 68, 32, ((10, 14), (22, 26)), 'shear', 25,
         ((4, 17, 1.25), (20, 26, .5)), ((4, 1.2),), 14),
)
REST = (2.75, 44., ((2.35, .95, 3.7), (-2.35, .95, 3.7)),
        ((1.45, .65, -1.85), (-1.45, .65, -1.85)))


def gait(q, stride=4.5, lift=.9):
    """Linear planted travel; C1 Hermite swing carries the foot over the floor."""
    q %= 1
    stance = .64
    if q <= stance:
        return (0., stride * (.5 - q / stance))
    u = (q - stance) / (1 - stance)
    a, b = -stride / 2, stride / 2
    tangent = -stride / stance * (1 - stance)
    z = (2*u**3 - 3*u*u + 1)*a + (u**3 - 2*u*u + u)*tangent
    z += (-2*u**3 + 3*u*u)*b + (u**3 - u*u)*tangent
    return lift * math.sin(math.pi*u)**2, z


def pose(idle, parents, source='Idle', frame=0, frames=1, move=None):
    mode = modes.mode(source)
    p = f.Pose(idle, parents)
    p.r[0], p.t[0] = IDENTITY, (0., 0., 0.)
    for _, lower, end in d.arms('hLpr'):
        for joint in (lower, end):
            p.t[joint] = tuple(v * 1.55 for v in p.t[joint])
    root, lean, hh, ff = REST
    hands, feet = list(hh), list(ff)
    end = max(1, frames - 1)
    t = frame / end
    yaw = roll = chest = head = jaw = 0.
    curve = lambda keys, when=frame: f.curve(keys, when)
    if move is not None:
        first, last = move.contacts[0][0], move.contacts[-1][1]
        load = curve(((0, 0), (first-4, 1), (first+2, -.25), (last+3, .1), (end, 0)))
        root -= .43 * load
        lean += 9 * load
        head = -5 * curve(((0, 0), (first-2, 1), (first+4, -.2), (end, 0)))
        jaw = 15 * max(0, load)
        if move.kind == 'scissor':
            keys = [(0, 0)]
            for i, (a, b) in enumerate(move.contacts):
                sign = 1 if i % 2 == 0 else -1
                keys.extend(((a-4, -sign*17), (a+2, sign*27), (b+2, sign*13)))
            keys.append((end, 0))
            yaw = curve(keys)
            chest = .35 * curve(keys, max(0, frame-1.2))
            roll = yaw * .1
            for i, side in enumerate((1, -1)):
                a, b = move.contacts[i]
                hands[i] = curve(((0, hh[i]), (a-4, (side*3.1, 2.6, .8)),
                    (a+1, (-side*.1, 1.5, 6.0)), (b+3, (-side*1.8, .75, 4.2)),
                    (end, hh[i])))
                feet[i] = add(ff[i], (0, .34*f.pulse(frame, a-4, b+4), .65*f.pulse(frame, a-4, b+5)))
        elif move.kind == 'feint':
            yaw = curve(((0, 0), (7, -14), (14, 23), (20, 10), (end, 0)))
            chest = curve(((0, 0), (9, -7), (17, 9), (end, 0)))
            lean += curve(((0, 0), (7, 8), (15, -8), (22, 4), (end, 0)))
            for i, side in enumerate((1, -1)):
                hands[i] = curve(((0, hh[i]), (7-i, (side*2.2, .75, 1.4)),
                    (13+i, (side*1.4, 2.1, 6.0)), (21+i, (side*2.6, .65, 4.6)),
                    (end, hh[i])))
                feet[i] = add(ff[i], (0, .65*f.pulse(frame, 7+i*2, 22+i*2), -.75*f.pulse(frame, 6, 19)))
        else:
            air = f.pulse(frame, 4, 21)
            lean += curve(((0, 0), (4, 12), (10, -17), (18, 7), (25, 14), (end, 0)))
            yaw = curve(((0, 0), (5, -12), (11, 21), (19, -14), (25, 15), (end, 0)))
            root -= .34*f.pulse(frame, 21, 29)
            chest = -5*air
            for i, side in enumerate((1, -1)):
                hands[i] = curve(((0, hh[i]), (4, (side*2.2, .65, 2.3)),
                    (8, (side*3.1, 4.2, 1.4)), (12, (side*.3, 1.6, 5.8)),
                    (18, (side*2.9, 2.7, 2.2)), (24, (side*.7, .75, 5.1)),
                    (end, hh[i])))
                feet[i] = add(ff[i], (0, 1.15*air, -.8*air))
        # The scapulae and scythes are carried with the thorax. Contact is crossed
        # with momentum; curves do not stop or ease to zero at every pose key.
        center = (0, root, 0)
        carry = mm(axis('z', roll*.5), axis('y', yaw*.6))
        hands = [add(center, mv(carry, sub(h, center))) for h in hands]
    elif mode in ('walk', 'run'):
        u = frame / max(1, frames)
        phase = math.tau*u
        stride = 4.6 if mode == 'run' else 3.8
        for i in range(2):
            dy, dz = gait(u+i*.5, stride)
            feet[i] = add(ff[i], (0, dy, dz))
            dy, dz = gait(u+i*.5+.5, stride, .75)
            hands[i] = add(hh[i], (0, dy, dz))
        root += .07*(1-math.cos(phase*2))
        roll = 1.3*math.sin(phase)
        yaw = 2.1*math.sin(phase)
        chest = -yaw*.45
        head = -.7*math.sin(phase-.25)
    elif mode in ('knockdown', 'prone', 'rise', 'rise_attack', 'death', 'launch', 'tumble'):
        if mode == 'knockdown':
            down = math.sin(t*math.pi/2)
        elif mode in ('rise', 'rise_attack'):
            rise_t = min(1, t/(.64 if mode == 'rise_attack' else 1))
            down = 1-(3*rise_t*rise_t-2*rise_t**3)
        elif mode == 'death':
            down = 1-(1-t)**3
        elif mode == 'launch':
            down = .35+.45*math.sin(t*math.pi/2)
        elif mode == 'tumble':
            down = .8
            roll = 13*math.sin(math.tau*t)
        else:
            down = 1
        root += (.95-root)*down
        lean += (80-lean)*down
        yaw, head = 8*down, -9*down
        for i, side in enumerate((1, -1)):
            hands[i] = tuple(a+(b-a)*down for a, b in zip(hh[i], (side*2.7, .45, 3.5)))
            feet[i] = tuple(a+(b-a)*down for a, b in zip(ff[i], (side*1.8, .5, -1.9)))
        if mode == 'rise_attack':
            swipe = f.pulse(frame, frames*.64, frames*.96)
            yaw += 22*swipe
            hands[0] = add(hands[0], (-1.4*swipe, 1.2*swipe, 2.2*swipe))
    elif mode == 'recoil':
        hit = math.sin(math.pi*t)*(1-.35*t)
        root -= .3*hit
        lean -= 16*hit
        yaw, head, jaw = 8*hit, -8*hit, 8*hit
        hands = [add(h, (0, .3*hit, -.65*hit)) for h in hands]
    elif mode == 'land':
        settle = math.sin(math.pi*t)**2
        root -= .5*settle
        lean += 7*settle
        hands = [add(h, (0, -.25*settle, .35*settle)) for h in hands]
    elif mode == 'bound':
        root -= .2
        hands = [(x*.55, y+.6, z-.7) for x, y, z in hands]
        head = 2*math.sin(math.tau*t)
    elif mode in ('air', 'coil'):
        tuck = min(1, t*1.5) if mode == 'coil' else 1
        root -= .3*tuck
        hands = [add(h, (0, .4*tuck, -.3*tuck)) for h in hands]
        feet = [add(h, (0, .75*tuck, -.4*tuck)) for h in feet]
    else:
        breath = math.sin(math.tau*t)
        root += .025*breath
        head = .6*breath
        hands = [add(h, (0, .025*breath, 0)) for h in hands]
    p.t[1] = (0., root, 0.)
    p.r[1] = mm(axis('z', roll), mm(axis('y', yaw*.55), mm(axis('x', lean), ROOT)))
    p.r[2], p.r[3], p.r[4] = axis('x', chest*.3), axis('y', chest*.4), axis('z', head)
    for i, (a, b, e) in enumerate(((20, 21, 22), (24, 25, 26))):
        side = 1 if i == 0 else -1
        safe_ik(p, a, b, e, feet[i], (side*3, 2, -2), (side, 0, 1))
        p.world_rotation(e, IDENTITY)
    for i, (a, b, e) in enumerate(d.arms('hLpr')):
        side = 1 if i == 0 else -1
        safe_ik(p, a, b, e, hands[i], (side*4.6, 3.1, -1.2), (side, 0, -1))
        flex = -13*math.sin(math.pi*t)**2 if move else 4
        p.world_rotation(e, mm(axis('y', side*7*math.sin(math.pi*t)**2 if move else 0), axis('x', flex)))
        for j in (e+1, e+2):
            if j < 19:
                p.r[j] = mm(axis('z', -6*math.sin(math.pi*t)**2), p.r[j])
    _, points = p.fk()
    f.locate(p, 19, add(points[5], (0, -.35, 1.0)), axis('x', -jaw))
    p.forge_scale = {}
    for i, joint in enumerate((23, 27)):
        # Brief wrist-bound arcs supplement the physical claw. No floor-wide
        # ring implies damage beyond the native authored melee volume.
        visible = move and i < len(move.contacts) and move.contacts[i][0]-1 <= frame < move.contacts[i][1]+1
        if visible:
            _, points = p.fk()
            f.locate(p, joint, add(points[d.arms('hLpr')[i][2]], (0, 0, .8)), axis('x', 55))
            scale = (.43, .32, .72)
        else:
            f.locate(p, joint, (0, -24, 0))
            scale = (.01, .01, .01)
        p.forge_scale[joint] = tuple(round(v*4096) for v in (*scale, *(1/v for v in scale)))
    return p


def prepare(native, names, parent):
    xbd = Xbd.parse(native('hLpr.xbd'), names)
    idle = Sca.parse(native('hLpr_Idle.sca'))
    parents = AnimationRig.parse(native('hLpr.nsbmd')).parents
    actions = ActorActions.parse(xbd.raw, names)
    selected = {next(b['name'] for b in actions.lookup(m.action).bindings if b['tag'] == 0): m for m in MOVES}
    extras, clips = {}, []
    for i, binding in enumerate(xbd.bindings):
        if binding['tag'] != 0:
            continue
        name = binding['name']
        target = 'zz_F22_skitter_' + name
        old = Sca.parse(parent(target))
        mode = modes.mode(name)
        move = selected.get(name)
        if move is None and mode in ('strike', 'slam', 'pounce', 'ranged'):
            move = MOVES[2 if mode == 'ranged' else 1 if mode in ('slam', 'pounce') else 0]
        n = move.samples if move else {'idle': 40, 'walk': 20, 'run': 18,
            'recoil': 10, 'knockdown': 12, 'prone': 20, 'rise': 22, 'death': 28,
            'land': 12, 'coil': 12, 'air': 12, 'bound': 20}.get(mode, old.frame_count)
        if mode == 'rise_attack':
            n = old.frame_count  # Native get-up contact/event clocks remain exact.
        poses = [pose(idle, parents, name, j, n, move) for j in range(n)]
        extras[target] = f.encode(native(name), poses)
        stop = next((j for j in range(i+1, len(xbd.bindings)) if xbd.bindings[j]['tag'] == 0), len(xbd.bindings))
        for part in xbd.bindings[i+1:stop]:
            extension = '.gmb' if part['tag'] == 3 else '.gab'
            name2 = target[:-4] + extension
            if part['tag'] == 3:
                template = parent(name2) if mode == 'rise_attack' else native(part['name'])
                extras[name2] = contact.geometry(template, poses, move, 'skitter')
            elif part['tag'] == 4 and move:
                events = b''.join(struct.pack('<3H', *event) for a, b in move.contacts
                                  for event in ((a, 1, 1), (b, 1, 5))) + b'\xff'*6
                extras[name2] = events + bytes(-len(events) % 4)
                Gab.parse(extras[name2])
        clips.append({'resource': target, 'mode': mode, 'samples': n,
                      'move': move.name if move else None,
                      'contacts': move.contacts if move else ()})
    return extras, clips, pose(idle, parents)
