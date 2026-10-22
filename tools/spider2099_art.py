"""Bounded classic 2099 art on CS5E's native player rig and GPU geometry.

Original skin, bone/SBC records and opaque bytes are retained. The body paint is
baked in bind space; appended fins, fingertips and an open web mantle use native
stored matrices. No animation, collision, material tint or combat event is edited.
"""
from dataclasses import dataclass
from pathlib import Path
import math
import struct

from tools import wos_tool as w
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive, dictionary
from tools.movie_suit import segment_distance
from tools.rush_choreography import add, sub, mv, mm, transpose
from tools.crane_creature_art import packets

MODEL_SHA = 'ba962799336fa58de2c78880e11ccc33ca1e769c846fe64c9a7f8ed5b4189879'
TEXTURE_SHA = '6a0a3b690f51498eeba3e1b50b24f972b0d28546482dd391e25e57443e53ce74'
SIZE = 128
COUNTS = {0: 0, 0x14: 1, 0x1b: 3, 0x20: 1, 0x21: 1, 0x22: 1,
          0x23: 2, 0x24: 1, 0x25: 1, 0x26: 1, 0x27: 1, 0x28: 1,
          0x40: 1, 0x41: 0}
IDENTITY = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))


def gpu_commands(raw):
    model = ModelGeometry.parse(raw)
    if len(model.shapes) != 1:
        raise ValueError('Expected single native player shape')
    shape = model.shapes[0]
    at, end = shape.start, shape.start + shape.length
    while at < end:
        ops = raw[at:at+4]
        at += 4
        for op in ops:
            if op not in COUNTS or at + COUNTS[op]*4 > end:
                raise ValueError('Unsupported or truncated player GPU command')
            args = struct.unpack_from('<' + 'I'*COUNTS[op], raw, at)
            yield op, args
            at += COUNTS[op]*4
    if at != end:
        raise ValueError('GPU stream framing differs')


def bind_matrices(raw):
    """CS5E player-only, unscaled native bind transforms; no general rig editor."""
    rig = AnimationRig.parse(raw)
    if len(rig.names) != 37:
        raise ValueError('Expected native 37-node player rig')
    rotations, positions = [], []
    for joint, at in enumerate(rig.object_offsets):
        flags, m0 = struct.unpack_from('<Hh', raw, at)
        if not flags & 4:
            raise ValueError('Scaled bind nodes are outside this bounded author')
        cursor = at + 4
        t = (0., 0., 0.)
        if not flags & 1:
            t = tuple(v/4096 for v in struct.unpack_from('<3i', raw, cursor))
            cursor += 12
        r = IDENTITY
        if flags & 8:
            a, b = (v/4096 for v in struct.unpack_from('<2h', raw, cursor))
            form = flags >> 4 & 15
            if form > 8:
                raise ValueError('Unknown pivot form')
            row, col = form % 3, form // 3
            matrix = [[0.]*3 for _ in range(3)]
            matrix[row][col] = -1. if flags & 256 else 1.
            rows = [i for i in range(3) if i != row]
            cols = [i for i in range(3) if i != col]
            # apicula src/nitro/rotation.rs is authoritative here: the old
            # nsbmd_docs prose swaps a/b in c/d and produces singular matrices.
            c = -b if flags & 512 else b
            d = -a if flags & 1024 else a
            for (i, j), value in zip(((rows[0], cols[0]), (rows[0], cols[1]),
                                      (rows[1], cols[0]), (rows[1], cols[1])), (a, c, b, d)):
                matrix[i][j] = value
            r = tuple(tuple(v) for v in matrix)
        elif not flags & 2:
            v = [m0/4096] + [x/4096 for x in struct.unpack_from('<8h', raw, cursor)]
            r = tuple(tuple(v[i+3*j] for j in range(3)) for i in range(3))
        parent = rig.parents[joint]
        rotations.append(r if parent is None else mm(rotations[parent], r))
        positions.append(t if parent is None else add(positions[parent], mv(rotations[parent], t)))
    slots = {}
    for _, op, args in rig.node_records:
        if op == 5:
            break
        if op in (0x26, 0x66):
            slots[args[3]] = args[0]
    return rig, rotations, positions, slots


@dataclass(frozen=True)
class Vertex:
    position: tuple
    uv: tuple
    slot: int
    local: tuple


def mesh(raw):
    """Decode the native non-weighted stored-matrix triangle/quad strips."""
    _, rotations, positions, slots = bind_matrices(raw)
    faces, pending = [], []
    # The player's SBC restores the head matrix immediately before SHP 0.
    slot, uv, xyz, mode = 3, (0., 0.), [0., 0., 0.], None
    signed = lambda v, bits: (v & ((1 << bits)-1)) - ((1 << bits) if v & (1 << (bits-1)) else 0)
    for op, args in gpu_commands(raw):
        if op == 0x14:
            slot = args[0]
        elif op == 0x22:
            uv = (signed(args[0], 16)/16, signed(args[0] >> 16, 16)/16)
        elif op == 0x40:
            mode, pending = args[0], []
        elif op == 0x41:
            mode, pending = None, []
        elif 0x23 <= op <= 0x28:
            if op == 0x23:
                xyz = [signed(args[0], 16)/4096, signed(args[0] >> 16, 16)/4096,
                       signed(args[1], 16)/4096]
            elif op == 0x24:
                xyz = [signed(args[0] >> (i*10), 10)/64 for i in range(3)]
            elif op in (0x25, 0x26, 0x27):
                axes = {0x25: (0, 1), 0x26: (0, 2), 0x27: (1, 2)}[op]
                for i, axis in enumerate(axes):
                    xyz[axis] = signed(args[0] >> (i*16), 16)/4096
            else:
                xyz = [xyz[i] + signed(args[0] >> (i*10), 10)/4096 for i in range(3)]
            if slot not in slots or mode not in (0, 1, 2, 3):
                raise ValueError('Unsupported native vertex matrix/primitive')
            joint = slots[slot]
            p = add(positions[joint], mv(rotations[joint], xyz))
            pending.append(Vertex(p, uv, slot, tuple(xyz)))
            n = len(pending)
            if mode == 0 and n % 3 == 0:
                faces.append(tuple(pending[-3:]))
            elif mode == 1 and n % 4 == 0:
                a, b, c, d = pending[-4:]
                faces.extend(((a, b, c), (a, c, d)))
            elif mode == 2 and n >= 3:
                a, b, c = pending[-3:]
                faces.append((a, b, c) if n % 2 else (b, a, c))
            elif mode == 3 and n >= 4 and n % 2 == 0:
                a, b, c, d = pending[-4:]
                faces.extend(((a, b, d), (a, d, c)))
    return faces


def inside(x, y, poly):
    result = False
    for (ax, ay), (bx, by) in zip(poly, (*poly[1:], poly[0])):
        if (ay > y) != (by > y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            result = not result
    return result


def paint(p):
    """Broad anatomical shading and angular markings, without stock web noise."""
    x, y, z = p
    ax = abs(x)
    # A restrained painted sheen remains blue in dark rooms; no noisy dithering.
    sheen = .5 + .5*math.cos(x*1.4 + z*.7)
    shade = .70 + .30*sheen
    blue = tuple(round(v*shade) for v in (5, 12, 25))
    if y < 3.1:
        blue = tuple(round(v*shade) for v in (4, 9, 21))
    color = blue
    red = False
    # Mask: red pointed eye fields, swept up the temples; no stock white lenses.
    if y > 8.6:
        red = z > -.05 and inside(ax, y, ((.07, 9.30), (.34, 9.72), (.70, 10.02),
            (.64, 9.40), (.48, 9.05), (.18, 9.13)))
        # Tapered red brow toward the crown, opening into the temple hooks.
        red |= z > .02 and inside(ax, y, ((.48, 9.62), (.68, 10.05), (.77, 9.75), (.64, 9.20)))
    # Skull with real negative-space sockets, triangular nose and separated teeth.
    if ax < 1.55 and 5.45 < y < 8.55 and abs(z) > .25:
        front = z > 0
        skull = inside(ax, y, ((0, 8.10), (.32, 8.08), (.48, 7.90), (.43, 7.58),
            (.28, 7.42), (.26, 7.12), (0, 7.04)))
        if front:
            socket = inside(ax, y, ((.09, 7.82), (.37, 7.90), (.31, 7.65), (.12, 7.66)))
            nose = ax < .055 and 7.39 < y < 7.59
            tooth_gap = 7.05 < y < 7.27 and (.065 < ax < .10 or .175 < ax < .205)
            skull &= not (socket or nose or tooth_gap)
        red |= skull
        # Four bold angular legs on either side, continuing around the rib cage.
        for line in (((.26, 7.95), (.80, 8.20), (1.37, 7.93)),
                     ((.34, 7.72), (.88, 7.88), (1.32, 7.48)),
                     ((.28, 7.48), (.69, 7.22), (.94, 6.27)),
                     ((.18, 7.22), (.43, 6.90), (.51, 5.82))):
            red |= min(segment_distance(ax, y, line[0], line[1]),
                       segment_distance(ax, y, line[1], line[2])) < .095
    # Chevron cuffs and narrow toe flashes retain a predominantly blue suit.
    if 3.15 < ax < 4.25 and 5.8 < y < 7.45:
        red |= ax > 3.55 + .18*math.sin(y*5)
    if y < 1.0:
        red |= y < .30 and z > .28
    if red:
        color = tuple(round(v*(.85+.15*sheen)) for v in (30, 3, 6))
    return color


def artwork(raw):
    """Bake UV-space I8 artwork from native bind-space triangles, 4x pixel count."""
    from tools.suit_uv_inspect import barycentric
    faces = mesh(raw)
    points = [None]*(SIZE*SIZE)
    for face in faces:
        pts = [(v.uv[0]*2, v.uv[1]*2) for v in face]
        for y in range(max(0, math.floor(min(v[1] for v in pts))), min(SIZE, math.ceil(max(v[1] for v in pts)))):
            for x in range(max(0, math.floor(min(v[0] for v in pts))), min(SIZE, math.ceil(max(v[0] for v in pts)))):
                weights = barycentric((x+.5, y+.5), *pts)
                if weights:
                    points[y*SIZE+x] = tuple(sum(weights[j]*face[j].position[k] for j in range(3)) for k in range(3))
    colors = [paint(p) if p else None for p in points]
    # Extend each island into unused texels to prevent seams under hardware sampling.
    for _ in range(3):
        previous = list(colors)
        for y in range(SIZE):
            for x in range(SIZE):
                i = y*SIZE+x
                if previous[i] is None:
                    neighbors = [previous[ny*SIZE+nx] for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                                 if 0 <= nx < SIZE and 0 <= ny < SIZE and previous[ny*SIZE+nx] is not None]
                    if neighbors:
                        colors[i] = neighbors[0]
    colors = [c or (3, 7, 17) for c in colors]
    # Native unused bottom/right texels: uniform swatches for added geometry.
    # Keep these outside all original islands, verified by the geometry test.
    swatches = ((30, 3, 6), (20, 1, 4), (8, 13, 23), (3, 5, 11))
    for j, c in enumerate(swatches):
        for y in range(124, 128):
            for x in range(j*4, j*4+4):
                colors[y*SIZE+x] = c
    palette = sorted(set(colors))
    if len(palette) > 256:
        raise ValueError('Authored palette exceeds I8')
    lookup = {c: i for i, c in enumerate(palette)}
    indices = bytes(lookup[c] for c in colors)
    pal = b''.join(struct.pack('<H', r | g << 5 | b << 10) for r,g,b in palette)
    return indices, pal + bytes(512-len(pal)), points


def texture(raw, indices, palette):
    if w.sha256(raw) != TEXTURE_SHA:
        raise ValueError('2099 requires exact native Black atlas')
    source = TextureArchive.parse(raw)
    if len(source.textures) != 1 or (source.textures[0]['width'], source.textures[0]['height'], source.textures[0]['format']) != (64,64,4):
        raise ValueError('Expected native black I8 atlas')
    if len(raw) != 4772 or source.palette_start != 4260 or len(indices) != SIZE*SIZE or len(palette) != 512:
        raise ValueError('Unexpected native atlas framing')
    out = bytearray(raw[:164] + indices + palette)
    delta = SIZE*SIZE-4096
    struct.pack_into('<I', out, 8, len(out))
    struct.pack_into('<I', out, 24, len(out)-20)
    struct.pack_into('<H', out, 32, SIZE*SIZE//8)
    for at in (0x24, 0x28, 0x38):
        struct.pack_into('<I', out, 20+at, w.u32(raw,20+at)+delta)
    params = w.u32(raw,0x64)
    struct.pack_into('<I',out,0x64,(params & ~((7<<20)|(7<<23))) | 4<<20 | 4<<23)
    TextureArchive.parse(out)
    return bytes(out)


def model(raw):
    if w.sha256(raw) != MODEL_SHA:
        raise ValueError('2099 requires exact native Black model')
    geometry = ModelGeometry.parse(raw)
    rig, rotations, positions, slots = bind_matrices(raw)
    commands = []
    for op, args in gpu_commands(raw):
        if op == 0x22:
            u,v = struct.unpack('<hh', struct.pack('<I', args[0]))
            args = (struct.unpack('<I', struct.pack('<hh', u*2,v*2))[0],)
        commands.append((op,args))
    # A triangle records its own stored matrix before EACH vertex; the web
    # mantle can bend between chest/scapula/pelvis without changing the skeleton.
    additions = []
    def face(vertices, swatch):
        additions.append((tuple(vertices), swatch))
    def local(slot, point):
        j = slots[slot]
        return mv(transpose(rotations[j]),sub(point,positions[j]))
    def world_face(slot, verts, swatch):
        face([(slot,local(slot,v)) for v in verts],swatch)
    for side, slot in ((-1,15),(1,6)):
        j = slots[slot]
        wrist = positions[19 if side == -1 else 9]
        elbow = positions[j]
        # Three swept, diamond-section crimson fins on each forearm.
        for f, length in ((.22,.43),(.48,.54),(.73,.43)):
            c = tuple(elbow[k]+(wrist[k]-elbow[k])*f for k in range(3))
            a = add(c,(side*.19,.13,-.19))
            b = add(c,(-side*.17,-.10,-.17))
            tip = add(c,(-side*.12,.06,-.22-length))
            ridge = add(c,(0,.075,-.29))
            for vs, swatch in (((a,b,tip),0),((b,a,ridge),1),((a,tip,ridge),0),((tip,b,ridge),1)):
                world_face(slot,vs,swatch)
    # Small hooked fingertips follow the native end-finger bones.
    native = mesh(raw)
    for slot in (9,11,12,18,20,21):
        vs = [v.local for face_ in native for v in face_ if v.slot == slot]
        if not vs:
            raise ValueError('Missing native fingertip geometry')
        direction = -1 if slot < 13 else 1
        end = min(v[0] for v in vs) if direction < 0 else max(v[0] for v in vs)
        cy = sum(v[1] for v in vs)/len(vs)
        cz = sum(v[2] for v in vs)/len(vs)
        a,b,c = (end,cy-.055,cz-.055),(end,cy+.055,cz+.055),(end+direction*.20,cy-.10,cz+.035)
        face(((slot,a),(slot,b),(slot,c)),3)
        face(((slot,b),(slot,a),(slot,c)),2)
    # Short open lattice mantle: empty gaps are actual holes, no opaque sheet.
    # Its upper points follow the shoulder blades; the lower points follow root.
    for side, shoulder in ((-1,13),(1,4)):
        outline = [(shoulder,(side*1.13,8.12,-.36)), (2,(side*.95,7.45,-.83)),
                   (1,(side*.72,6.65,-.96)), (1,(side*.28,6.32,-1.01)),
                   (2,(0.,7.98,-.64))]
        def thread(a,b,width=.026):
            (sa,pa),(sb,pb) = a,b
            for sign in (-1,1):
                va=add(pa,(sign*width,0,0));vb=add(pb,(sign*width,0,0))
                if sign == -1:
                    corners=[(sa,local(sa,va)),(sb,local(sb,vb))]
                else:
                    corners += [(sb,local(sb,vb)),(sa,local(sa,va))]
            face((corners[0],corners[1],corners[2]),2)
            face((corners[0],corners[2],corners[3]),2)
            face((corners[2],corners[1],corners[0]),2)
            face((corners[3],corners[2],corners[0]),2)
        for a,b in zip(outline,(*outline[1:],outline[0])):
            thread(a,b)
        for i in (1,2,3):
            thread(outline[4],outline[i],.018)
    for vs, swatch in additions:
        commands.append((0x40,(0,)))
        u,v = (swatch*4+1.5)*16,125.5*16
        commands.append((0x22,(round(u)|(round(v)<<16),)))
        for slot,p in vs:
            values = tuple(round(q*4096) for q in p)
            if any(not -32768 <= q <= 32767 for q in values):
                raise ValueError('Added vertex exceeds native Q12 range')
            x,y,z = values
            commands.extend(((0x14,(slot,)),(0x23,((x&65535)|(y&65535)<<16,z&65535))))
        commands.append((0x41,()))
    out = bytearray(geometry.replace_streams([packets(commands)],
        vertices=w.u16(raw,geometry.model+36)+len(additions)*3,
        quads=w.u16(raw,geometry.model+38)+len(additions)))
    mats = geometry.model+w.u32(raw,geometry.model+8)
    entries = dictionary(raw,mats+4,4)
    if len(entries) != 1:
        raise ValueError('Expected one native player material')
    at = mats+w.u32(entries[0][1],0)
    if struct.unpack_from('<2H',raw,at+32) != (64,64):
        raise ValueError('Expected native material dimensions')
    struct.pack_into('<2H',out,at+32,SIZE,SIZE)
    # Counts are triangle additions, while the original quads/strips stay exact.
    struct.pack_into('<H',out,geometry.model+40,w.u16(raw,geometry.model+40)+len(additions))
    struct.pack_into('<H',out,geometry.model+42,w.u16(raw,geometry.model+42))
    parsed = AnimationRig.parse(out)
    if parsed.parents != rig.parents or parsed.node_records != rig.node_records:
        raise ValueError('2099 changed native rig/SBC')
    return bytes(out), {'fin_count':6,'claw_tips':6,'added_triangles':len(additions),
                        'texture_size':[SIZE,SIZE],'native_rig_unchanged':True}


def render(raw, tex, path, yaw=0, size=(480,600), *, faces=None):
    """Private unlit geometry preview; actual in-engine captures qualify lighting."""
    from PIL import Image
    from tools.suit_uv_inspect import barycentric
    faces = mesh(raw) if faces is None else faces
    archive = TextureArchive.parse(tex)
    t = archive.textures[0]
    palette = [tuple((w.u16(tex,archive.palette_start+i*2)>>s&31)*255//31 for s in (0,5,10)) for i in range(256)]
    indices = tex[t['offset']:t['offset']+t['size']]
    if t['format'] == 3:
        indices = bytes(v for pair in ((b & 15,b >> 4) for b in indices) for v in pair)
    elif t['format'] != 4:
        raise ValueError('Player preview supports I4/I8 only')
    pixels = [palette[v] for v in indices]
    width,height = size
    output = bytearray((16,21,32)*(height*width))
    depths = [-math.inf]*(height*width)
    angle=math.radians(yaw)
    def turn(p):
        x,y,z=p
        return x*math.cos(angle)+z*math.sin(angle),y,z*math.cos(angle)-x*math.sin(angle)
    for face in faces:
        q=[turn(v.position) for v in face]
        pts=[(width/2+x*width/11,height-35-y*(height-60)/10.5) for x,y,z in q]
        x0=max(0,math.floor(min(p[0] for p in pts)));x1=min(width,math.ceil(max(p[0] for p in pts)))
        y0=max(0,math.floor(min(p[1] for p in pts)));y1=min(height,math.ceil(max(p[1] for p in pts)))
        if x0>=x1 or y0>=y1:continue
        a,b,c=pts
        det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det)<1e-8:continue
        for y in range(y0,y1):
            for x in range(x0,x1):
                weights=barycentric((x+.5,y+.5),*pts)
                if not weights:continue
                depth=sum(weights[j]*q[j][2] for j in range(3));i=y*width+x
                if depth <= depths[i]:continue
                u=sum(weights[j]*face[j].uv[0] for j in range(3))
                v=sum(weights[j]*face[j].uv[1] for j in range(3))
                at=max(0,min(t['height']-1,int(v)))*t['width']+max(0,min(t['width']-1,int(u)))
                if t['params'] & 0x2000 and indices[at] == 0:
                    continue
                pixel=pixels[at]
                output[i*3:i*3+3]=bytes(pixel);depths[i]=depth
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Image.frombytes('RGB',(width,height),bytes(output)).save(path)
