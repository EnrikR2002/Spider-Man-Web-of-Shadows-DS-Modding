"""Broaden the published cape-free 2099 mesh without changing its rig or atlas."""
import math
import struct

from tools import spider2099_art as art, spider2099_sculpt as sculpt, wos_tool as w
from tools.model_geometry import ModelGeometry
from tools.rush_choreography import add, sub, mul, dot, length, mv


def model(raw):
    rig, rotations, positions, slots = art.bind_matrices(raw)
    inverses = [sculpt.inverse(r) for r in rotations]
    segments = ((7, 8, .30), (8, 9, .13), (17, 18, .30), (18, 19, .13))

    def morph(p):
        x, y, z = p
        upper = math.exp(-((y - 7.55) / 1.02) ** 4)
        weight = max(0., min(1., (2.25 - abs(x)) / 1.0))
        q = (x * (1 + .20 * upper * weight), y,
             -.25 + (z + .25) * (1 + .25 * upper * weight))
        if abs(x) > 1.25 and y > 5.8:
            choices = []
            for a, b, bulk in segments:
                axis = sub(positions[b], positions[a])
                f = max(0., min(1., dot(sub(p, positions[a]), axis) / dot(axis, axis)))
                center = add(positions[a], mul(axis, f))
                choices.append((length(sub(p, center)), f, center, bulk))
            distance, f, center, bulk = min(choices)
            if distance < 1.8:
                arm = add(center, mul(sub(p, center), 1 + bulk * math.sin(math.pi * f) ** .65))
                blend = max(0., min(1., (abs(x) - 1.25) / .65))
                q = add(mul(q, 1 - blend), mul(arm, blend))
        return q

    vertices = iter(sculpt.native_vertices(raw))
    commands, points = [], []
    for op, args in art.gpu_commands(raw):
        if 0x23 <= op <= 0x28:
            v = next(vertices)
            p = morph(v.position)
            j = slots[v.slot]
            xyz = tuple(round(x * 4096) for x in mv(inverses[j], sub(p, positions[j])))
            if any(not -32768 <= x <= 32767 for x in xyz):
                raise ValueError('2099 muscle sculpt exceeds native vertex bounds')
            x, y, z = xyz
            op, args = 0x23, ((x & 65535) | (y & 65535) << 16, z & 65535)
            points.append(p)
        commands.append((op, args))
    g = ModelGeometry.parse(raw)
    counts = struct.unpack_from('<4H', raw, g.model + 36)
    out = bytearray(g.replace_streams([art.packets(commands)], vertices=counts[0], quads=counts[1]))
    struct.pack_into('<4H', out, g.model + 36, *counts)
    scale = w.u32(raw, g.model + 56) / 4096
    lo = [math.floor(min(p[k] for p in points) / scale * 4096) - 2 for k in range(3)]
    hi = [math.ceil(max(p[k] for p in points) / scale * 4096) + 2 for k in range(3)]
    struct.pack_into('<6h', out, g.model + 44, *lo, *(hi[k] - lo[k] for k in range(3)))
    return bytes(out), dict(triangles=len(art.mesh(out)), native_rig_unchanged=True,
        atlas_unchanged=True, cape=False, physique='Fuller chest/back, deltoids, biceps and forearms; waist, height and native joint pivots retained.')
