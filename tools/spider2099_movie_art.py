"""Cape-free Spider-Verse 2099 skin on the preserved native player rig.

Author in bind space, bake into the native UV islands, and emit only appearance
data. The native skeleton, SBC, material lighting and all animations stay exact.
"""
from collections import defaultdict
import math
import struct

from tools import spider2099_art as art, spider2099_sculpt as sculpt, wos_tool as w
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.rush_choreography import add, sub, mul, dot, cross, unit, length, mv

SIZE = 128


class Anatomy(sculpt.Anatomy):
    def morph(self, p):
        x, y, z = p
        ax = abs(x)
        # Continuous shoulders/chest taper, with the waist and joint pivots kept.
        upper = math.exp(-((y - 7.55) / .98) ** 4)
        weight = max(0., min(1., (1.95 - ax) / .78))
        q = (x * (1 + .43 * upper * weight), y,
             -.25 + (z + .25) * (1 + .36 * upper * weight))
        if 6.8 < y < 8.4 and z > -.15:
            pec = .23 * math.exp(-((ax - .60) / .60) ** 2 - ((y - 7.65) / .48) ** 2)
            q = add(q, (0, 0, pec * weight))
        trap = .16 * math.exp(-((y - 8.12) / .33) ** 2 - ((ax - .60) / .53) ** 2)
        q = add(q, (0, trap, 0))
        if ax > 1.18 and y > 5.8:
            distance, f, center, kind, _ = self.arm(p)
            if distance < .95:
                envelope = math.sin(math.pi * f) ** .8
                scale = 1.08 + (.64 if kind == 'upper' else .17) * envelope
                arm = add(center, mul(sub(p, center), scale))
                blend = max(0., min(1., (ax - 1.18) / .52))
                q = add(mul(q, 1 - blend), mul(arm, blend))
        if 3.25 < y < 5.3:
            candidates = []
            for hip, knee in ((26, 27), (30, 31)):
                axis = sub(self.positions[knee], self.positions[hip])
                f = max(0., min(1., dot(sub(p, self.positions[hip]), axis) / dot(axis, axis)))
                center = add(self.positions[hip], mul(axis, f))
                candidates.append((length(sub(p, center)), f, center))
            distance, f, center = min(candidates)
            if distance < .8:
                q = add(center, mul(sub(p, center), 1 + .18 * math.sin(math.pi * f)))
        # Narrower jaw/crown, with no changes to head/neck bind transforms.
        if y > 8.65:
            jaw = math.exp(-((y - 8.9) / .24) ** 2)
            q = (x * (.96 - .11 * jaw), y, -.55 + (z + .55) * .96)
        return q


def ribbon(x, y, points, widths):
    """Tapered graphic stroke; avoids rounded blobs at the narrow spider tips."""
    for a, b, wa, wb in zip(points, points[1:], widths, widths[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = max(0., min(1., ((x-a[0])*dx + (y-a[1])*dy) / (dx*dx + dy*dy)))
        if math.hypot(x-a[0]-t*dx, y-a[1]-t*dy) < wa + (wb-wa)*t:
            return True
    return False


def red_marking(p, anatomy):
    x, y, z = p
    ax = abs(x)
    if y > 8.65:
        if z < -.32:
            return False
        field = art.inside(ax, y, ((.075, 8.74), (.10, 9.14), (.075, 9.40),
            (.36, 9.67), (.45, 9.99), (.60, 9.78), (.57, 9.18), (.25, 8.93), (.16, 8.73)))
        eye = art.inside(ax, y, ((.15, 9.33), (.49, 9.59), (.47, 9.23), (.25, 9.13)))
        return field and not eye
    red = False
    if ax < 1.60 and 5.40 < y < 8.45 and (z > -.36 or z < -.66):
        # The movie's angular spider replaces the classic skull and small legs.
        red |= ribbon(ax, y, ((.18, 7.15), (.76, 7.65), (.40, 8.12)), (.055, .065, .030))
        red |= ribbon(ax, y, ((.31, 7.13), (1.05, 7.66), (.66, 8.19)), (.060, .070, .030))
        red |= art.inside(ax, y, ((0, 8.06), (.16, 7.69), (0, 7.40)))
        thorax = art.inside(ax, y, ((0, 7.32), (.26, 7.12), (.23, 6.93), (0, 6.82)))
        hole = art.inside(ax, y, ((0, 7.22), (.085, 7.12), (0, 7.02)))
        red |= thorax and not hole
        red |= ribbon(ax, y, ((.12, 6.99), (.20, 6.77), (.11, 6.58)), (.055, .050, .008))
        red |= ribbon(ax, y, ((.25, 7.02), (.42, 6.65), (.43, 6.15), (.27, 5.88)), (.055, .055, .040, .008))
        red |= ribbon(ax, y, ((.43, 7.10), (.66, 6.68), (.63, 6.20), (.42, 5.89)), (.060, .060, .040, .008))
    # Broad red shoulder caps and the collar's rising chevrons wrap around sides.
    if .52 < ax < 1.36 and 7.95 < y < 8.48:
        red |= abs(y - (8.49 - ax * .35)) < .105
    if ax > 1.18 and 5.8 < y < 8.35:
        distance, f, center, kind, _ = anatomy.arm(p)
        if distance < .85:
            if kind == 'upper':
                red |= f < .58 and y > center[1] - .24
            else:
                # A slim red dorsal bracer leaves the forearm predominantly navy.
                red |= .12 < f < .92 and z < center[2] - .16 and y > center[1] - .10
                red |= .71 < f < .85 and z > center[2] + .12
    if ax > 3.50 and 5.8 < y < 7.25:
        red |= z > .03 and y < 6.55 + (ax-3.7)*.20
    # Red V marks below each knee, then a narrow sole/toe accent.
    if 2.80 < y < 3.48 and z > -.18:
        center = .88 + (3.34 - y) * .185
        dx = abs(ax - center)
        red |= dx < .38 and abs(y - (2.92 + dx * 1.40)) < .075
    if y < .16 and z > -.60:
        red = True
    return red


def color(p, normal, anatomy):
    red = red_marking(p, anatomy)
    light = .25 + .75 * max(0., dot(normal, unit((-.35, .75, 1.))))
    if abs(p[0]) < 1.20 and 6.8 < p[1] < 8.1 and p[2] > -.05:
        light -= .12 * math.exp(-((p[1] - 7.32) / .10) ** 2)
        light -= .10 * math.exp(-(p[0] / .10) ** 2)
    light = max(.15, min(1., light))
    if red:
        return (round(24 + 7 * light), round(1 + 2 * light), round(3 + 3 * light))
    # Dark navy with clean cobalt edge lighting, readable against dark DS rooms.
    rim = max(0., abs(normal[0]) - .30) * .70
    return (round(1 + light), round(1 + 3 * light + 6 * rim),
            round(4 + 8 * light + 22 * rim))


def artwork(raw):
    from tools.suit_uv_inspect import barycentric
    a = Anatomy(raw)
    normals = defaultdict(lambda: (0., 0., 0.))
    for face in a.faces:
        p, q, r = (v.position for v in face)
        n = cross(sub(q, p), sub(r, p))
        for v in face:
            key = sculpt._key(v.position)
            normals[key] = add(normals[key], n)
    normals = {k: unit(n) if length(n) > 1e-8 else (0, 0, 1) for k, n in normals.items()}
    colors = [None] * (SIZE * SIZE)
    covered = set()
    for original, face in zip(a.original, a.faces):
        pts = [(v.uv[0] * 2, v.uv[1] * 2) for v in original]
        for y in range(max(0, math.floor(min(p[1] for p in pts))), min(SIZE, math.ceil(max(p[1] for p in pts)))):
            for x in range(max(0, math.floor(min(p[0] for p in pts))), min(SIZE, math.ceil(max(p[0] for p in pts)))):
                weights = barycentric((x + .5, y + .5), *pts)
                if weights:
                    p = tuple(sum(weights[j] * original[j].position[k] for j in range(3)) for k in range(3))
                    n = tuple(sum(weights[j] * normals[sculpt._key(face[j].position)][k] for j in range(3)) for k in range(3))
                    colors[y * SIZE + x] = color(p, unit(n), a)
                    covered.add((x, y))
    for _ in range(3):
        before = list(colors)
        for y in range(SIZE):
            for x in range(SIZE):
                if before[y * SIZE + x] is None:
                    nearby = [before[ny * SIZE + nx] for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1))
                              if 0 <= nx < SIZE and 0 <= ny < SIZE and before[ny * SIZE + nx] is not None]
                    if nearby:
                        colors[y * SIZE + x] = nearby[0]
    colors = [c or (2, 4, 10) for c in colors]
    for swatch, c in enumerate(((31, 2, 5), (20, 1, 3), (31, 4, 7), (3, 7, 16))):
        for y in range(124, 128):
            for x in range(swatch * 4, swatch * 4 + 4):
                if (x, y) in covered:
                    raise ValueError('Blade swatch overlaps a native body UV island')
                colors[y * SIZE + x] = c
    palette = sorted(set(colors))
    if len(palette) > 256:
        raise ValueError('Movie suit exceeds the native I8 palette')
    lookup = {c: i for i, c in enumerate(palette)}
    indices = bytes(lookup[c] for c in colors)
    pal = b''.join(struct.pack('<H', r | g << 5 | b << 10) for r, g, b in palette)
    return indices, pal + bytes(512 - len(pal)), {
        'colors': len(palette), 'storage_format': 'I8', 'texture_size': [128, 128],
        'pixel_pool_bytes': 16384, 'transparent_texels': 0,
        'design': 'Navy/cobalt body, negative-space red mask, angular chest spider, red shoulder caps, bracers and knee chevrons; no cape atlas.'}


def texture(raw, indices, palette):
    out = bytearray(art.texture(raw, indices, palette))
    # Declare actual original dimensions; palette zero is an opaque navy color.
    struct.pack_into('<I', out, 0x68, (w.u32(raw, 0x68) & ~0x3fffff) | SIZE | (SIZE << 11))
    struct.pack_into('<I', out, 0x64, w.u32(out, 0x64) & ~(1 << 29))
    return bytes(out)


def model(raw):
    a = Anatomy(raw)
    g = ModelGeometry.parse(raw)
    commands, points = [], []
    emitted = iter(sculpt.native_vertices(raw))

    def vertex(slot, p):
        xyz = tuple(round(v * 4096) for v in a.local(slot, p))
        if any(not -32768 <= v <= 32767 for v in xyz):
            raise ValueError('Movie sculpt exceeds native Q12 vertex bounds')
        x, y, z = xyz
        return (0x23, ((x & 65535) | (y & 65535) << 16, z & 65535))

    for op, args in art.gpu_commands(raw):
        if op == 0x22:
            u, v = struct.unpack('<hh', struct.pack('<I', args[0]))
            args = (struct.unpack('<I', struct.pack('<hh', u * 2, v * 2))[0],)
        if 0x23 <= op <= 0x28:
            v = next(emitted)
            p = a.morph(v.position)
            points.append(p)
            commands.append(vertex(v.slot, p))
        else:
            commands.append((op, args))
    additions, mounts = [], []

    def solid(slot, ps, swatch):
        additions.append((slot, tuple(ps), (swatch * 4 + 1.5, 125.5)))

    for slot, elbow, wrist in ((6, 8, 9), (15, 18, 19)):
        origin = a.positions[elbow]
        axis = sub(a.positions[wrist], origin)
        direction = unit(axis)
        dorsal = unit(sub((0, 0, -1), mul(direction, dot((0, 0, -1), direction))))
        across = unit(cross(direction, dorsal))
        for f, height, sweep in ((.22, .70, .29), (.50, .56, .25), (.77, .40, .21)):
            center = add(origin, mul(axis, f))
            radius = a.surface(slot, center, dorsal)
            roots = []
            for sign in (-1, 1):
                root = add(center, mul(direction, sign * .15))
                t = a.surface(slot, root, dorsal)
                roots.append(add(add(root, mul(dorsal, t - .010)), mul(across, sign * .045)))
            left, right = roots
            tip = add(add(center, mul(dorsal, radius + height)), mul(direction, -sweep))
            ridge = add(add(center, mul(dorsal, radius + .12)), mul(across, .08))
            for ps, swatch in (((left, right, tip), 0), ((right, left, ridge), 1),
                               ((left, tip, ridge), 2), ((tip, right, ridge), 0)):
                solid(slot, ps, swatch)
            mounts.append({'slot': slot, 'fraction': f, 'surface_radius': radius,
                           'visible_height': height, 'base_world': add(center, mul(dorsal, radius)),
                           'tip_world': tip, 'sweep_toward_elbow': True})
    for slot in (9, 11, 12, 18, 20, 21):
        vs = [v for face in a.original for v in face if v.slot == slot]
        sign = -1 if slot < 13 else 1
        end = (min if sign < 0 else max)(v.local[0] for v in vs)
        cy = sum(v.local[1] for v in vs) / len(vs)
        cz = sum(v.local[2] for v in vs) / len(vs)
        local = ((end, cy-.05, cz-.05), (end, cy+.05, cz+.05), (end+sign*.15, cy-.08, cz+.03))
        j = a.slots[slot]
        ps = [a.morph(add(a.positions[j], mv(a.rotations[j], p))) for p in local]
        solid(slot, ps, 2)
        solid(slot, reversed(ps), 1)
    for slot, ps, (u, v) in additions:
        commands.append((0x40, (0,)))
        for p in ps:
            commands.extend(((0x14, (slot,)), (0x22, (round(u*16) | round(v*16) << 16,)), vertex(slot, p)))
        commands.append((0x41, ()))
        points.extend(ps)
    out = bytearray(g.replace_streams([art.packets(commands)],
        vertices=w.u16(raw, g.model+36)+len(additions)*3,
        quads=w.u16(raw, g.model+38)+len(additions)))
    struct.pack_into('<2H', out, g.model+40, w.u16(raw, g.model+40)+len(additions), w.u16(raw, g.model+42))
    from tools.spider2099_visual import material
    struct.pack_into('<2H', out, material(out)+32, SIZE, SIZE)
    scale = w.u32(raw, g.model+56) / 4096
    lo = [math.floor(min(p[k] for p in points) / scale * 4096)-2 for k in range(3)]
    hi = [math.ceil(max(p[k] for p in points) / scale * 4096)+2 for k in range(3)]
    struct.pack_into('<6h', out, g.model+44, *lo, *(hi[k]-lo[k] for k in range(3)))
    rig = AnimationRig.parse(out)
    if (rig.names, rig.parents, rig.node_records) != (a.rig.names, a.rig.parents, a.rig.node_records):
        raise ValueError('Movie sculpt changed native rig')
    return bytes(out), {'native_body_triangles': 480, 'added_triangles': len(additions),
        'total_triangles': 480+len(additions), 'forearm_blades': mounts, 'talon_tips': 6,
        'cape': {'triangles': 0, 'removed': True}, 'native_rig_unchanged': True,
        'physique': 'Broader chest/lats/traps and deltoids, athletic thighs, tapered waist and narrower jaw; native pivots unchanged.'}
