"""Room compiler: one list of boxes gives a room's collision file, its model and its texture archive.

A room is a 2-D plan (x right, y up) of solid boxes inside `bounds`; everything
outside the bounds is solid too. The same boxes give
- the collision tree (`room_collision.compile_boxes`), and
- the visible faces: the top, underside and sides of every solid where it
  meets empty space (across the play depth -DEPTH..DEPTH), a cut face toward
  the camera, and a back wall behind the empty space.
Looks name a texture of the room's own archive, which may hold textures
borrowed from any native archive and painted ones. Scenery quads and boxes
(`Room.scenery`) are drawn only; they never collide.
Proven in the running game: TECHNICAL "Room compiler".
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
import struct

from tools import nitro_build as nb, room_collision as rc

INF = rc.INF
DEPTH = 25.0                         # native rooms: play space is |z| < 25
MAX_TEXELS = 1024                    # texture coordinates are s16 in 1/16 texel: stay well inside +-2048


@dataclass(frozen=True)
class Look:
    texture: str                     # texture name in the room's archive
    size: tuple = (32.0, 32.0)       # world units covered by one repeat (across, down)
    tint: tuple = (31, 31, 31)       # vertex colour (5-bit r, g, b) before the face's own shade


@dataclass(frozen=True)
class Solid:
    x0: float
    y0: float
    x1: float
    y1: float
    surface: int = rc.PLAIN
    top: Look | None = None          # None: the room's theme
    side: Look | None = None
    under: Look | None = None
    front: Look | None = None
    hidden: bool = False             # collision only (an invisible wall or ceiling)
    depth: float = DEPTH             # the visible body reaches from the back wall to this z (collision is always full depth)


@dataclass(frozen=True)
class Quad:
    """Scenery: four corners, counter-clockwise as seen by the viewer, with texture repeats per corner."""
    look: Look
    corners: tuple
    repeats: tuple = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0))
    shade: float = 1.0


@dataclass(frozen=True)
class Panel:
    """Back wall look for a rectangle of the plan (later panels paint over earlier ones).

    `look` None leaves the back wall open there: scenery placed behind it (a
    far skyline) shows through.
    """
    x0: float
    y0: float
    x1: float
    y1: float
    look: Look | None
    shade: float = 0.7
    anchor: tuple | None = None      # world point where the texture's top-left corner sits (default: world origin)
    mirror: bool = False             # flip the texture left to right (hides the seam between repeats of a picture)


SHADES = {'top': 1.0, 'side': 0.78, 'under': 0.5, 'front': 0.3, 'body': 0.62}   # 'body': front of a free-standing solid


@dataclass(frozen=True)
class Room:
    name: str
    bounds: tuple                    # x0, y0, x1, y1 of the interior
    theme: dict                      # looks: top, side, under, front, back
    solids: tuple = ()
    panels: tuple = ()
    scenery: tuple = ()
    textures: tuple = ()             # nb.Texture
    palettes: tuple = ()             # nb.Palette, named <texture>_pl
    shell_surface: int = rc.PLAIN    # surface of the outer walls, floor and ceiling
    sky: float | None = None         # outdoor room: nothing is drawn above this height (walls, ceiling, back wall)
    hidden_shell: tuple = ()         # outer solids that are collision only: 'left', 'right', 'below', 'above'
    margin: float = 40.0             # how far the outer solids are drawn beyond the bounds
    shades: dict = field(default_factory=lambda: dict(SHADES))
    back_shade: float = 0.7


@dataclass(frozen=True)
class Compiled:
    model: bytes
    textures: bytes
    collision: bytes
    quads: int
    by_texture: dict


def shell(room):
    """The four outer solids closing a room (left, right, below, above)."""
    x0, y0, x1, y1 = room.bounds
    s = room.shell_surface
    h = room.hidden_shell
    return (Solid(-INF, -INF, x0, INF, s, hidden='left' in h), Solid(x1, -INF, INF, INF, s, hidden='right' in h),
            Solid(x0, -INF, x1, y0, s, hidden='below' in h), Solid(x0, y1, x1, INF, s, hidden='above' in h))


def all_solids(room): return (*shell(room), *room.solids)


def collision(room, slab=DEPTH):
    return rc.compile_boxes([(s.x0, s.y0, s.x1, s.y1, s.surface) for s in all_solids(room)], slab)


def box(x0, y0, z0, x1, y1, z1, look, shade=1.0, faces='front top left right'):
    """Scenery box: the chosen faces as quads, mapped with the look's repeat size."""
    if not (x0 < x1 and y0 < y1 and z0 < z1): raise ValueError('Scenery box has no volume')
    su, sv = look.size
    def face(corners, across, down, factor):
        return Quad(look, corners, ((0, 0), (0, down / sv), (across / su, down / sv), (across / su, 0)), shade * factor)
    out = []
    if 'front' in faces: out.append(face(((x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1)), x1 - x0, y1 - y0, 1.0))
    if 'top' in faces: out.append(face(((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)), x1 - x0, z1 - z0, 1.0))
    if 'left' in faces: out.append(face(((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)), z1 - z0, y1 - y0, 0.8))
    if 'right' in faces: out.append(face(((x1, y1, z1), (x1, y0, z1), (x1, y0, z0), (x1, y1, z0)), z1 - z0, y1 - y0, 0.65))
    if 'under' in faces: out.append(face(((x0, y0, z1), (x0, y0, z0), (x1, y0, z0), (x1, y0, z1)), x1 - x0, z1 - z0, 0.5))
    return out


def backdrop(look, x0, x1, y0, y1, z=-170.0, tile=90.0, shade=1.0, mirror=True, sky=0.0, ground=0.0):
    """Scenery: a picture repeated along a far wall (native skylines stand at z -171, about 90 units a
    tile, so they drift slowly behind the room instead of hanging on its back wall). Every second
    tile is mirrored so the seams match. Above it the picture's top fifth (sky only) goes on for
    `sky` units, folded back and forth so it has no seam, and below it its bottom row for `ground`
    units: a high jump or a high platform does not show where the picture ends."""
    out, x, n = [], x0, 0
    while x < x1 - 1e-6:
        a, b = (1.0, 0.0) if mirror and n % 2 else (0.0, 1.0)
        out.append(Quad(look, ((x, y1, z), (x, y0, z), (x + tile, y0, z), (x + tile, y1, z)),
                        ((a, 0.0), (a, 1.0), (b, 1.0), (b, 0.0)), shade))
        band, y, fold = (y1 - y0) / 5, y1, True
        while y < y1 + sky - 1e-6:
            v0, v1 = (0.2, 0.0) if fold else (0.0, 0.2)        # texture v at the strip's top and bottom
            out.append(Quad(look, ((x, y + band, z), (x, y, z), (x + tile, y, z), (x + tile, y + band, z)),
                            ((a, v0), (a, v1), (b, v1), (b, v0)), shade))
            y += band; fold = not fold
        if ground:
            out.append(Quad(look, ((x, y0, z), (x, y0 - ground, z), (x + tile, y0 - ground, z), (x + tile, y0, z)),
                            ((a, 0.97), (a, 0.99), (b, 0.99), (b, 0.97)), shade))
        x += tile; n += 1
    return out


def _cuts(lo, hi, step):
    """lo..hi split at multiples of `step` kept under the texture coordinate limit."""
    n = max(1, math.ceil((hi - lo) / step - 1e-9))
    return [lo + (hi - lo) * i / n for i in range(n + 1)]


def _plan_faces(room):
    """Faces of the plan as (look, kind, a, b, z0, z1, shade, anchor).

    kind 'top'/'under': a = (x0, x1), b = y; 'left'/'right' (the side of the
    solid the face is on): a = x, b = (y0, y1); 'front'/'back': a = rectangle
    (x0, y0, x1, y1) at z1. A solid with `depth` below DEPTH stands free: its
    faces stop at that z, its front face sits there, and the surface it
    stands on is drawn on in front of it (kind 'apron', not walkable). Where
    it touches a deeper solid sideways or from below, that solid's side or
    underside is drawn on in front of it too (kinds 'left_fill',
    'right_fill', 'under_fill'): without them the gap showed the black
    behind the room (v0.12.0 catwalk ends and doorway corners).
    """
    bx0, by0, bx1, by1 = room.bounds
    m = room.margin
    top_limit = by1 + m if room.sky is None else room.sky
    view = (bx0 - m, by0 - m, bx1 + m, top_limit)
    solids = [s for s in all_solids(room)]
    def clip(s): return (max(s.x0, view[0]), max(s.y0, view[1]), min(s.x1, view[2]), min(s.y1, view[3]))
    xs = sorted({view[0], view[2], *(v for s in solids for v in (clip(s)[0], clip(s)[2]) if view[0] <= v <= view[2])})
    ys = sorted({view[1], view[3], *(v for s in solids for v in (clip(s)[1], clip(s)[3]) if view[1] <= v <= view[3])})
    for p in room.panels:
        xs = sorted({*xs, *(v for v in (p.x0, p.x1) if view[0] < v < view[2])})
        ys = sorted({*ys, *(v for v in (p.y0, p.y1) if view[1] < v < view[3])})
    def owner(i, j):
        cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
        for n, s in enumerate(solids):
            if s.x0 <= cx <= s.x1 and s.y0 <= cy <= s.y1: return n
        return None
    nx, ny = len(xs) - 1, len(ys) - 1
    grid = [[owner(i, j) for j in range(ny)] for i in range(nx)]
    def look_of(n, kind):
        return getattr(solids[n], kind) or room.theme[kind]
    def depth(n): return min(solids[n].depth, DEPTH)
    shades = room.shades
    out = []
    # Horizontal faces: runs along x for each y line between a solid and an empty cell.
    for j in range(ny + 1):
        for kind, solid_j, empty_j in (('top', j - 1, j), ('under', j, j - 1)):
            if not (0 <= solid_j < ny and 0 <= empty_j < ny): continue
            run = None
            for i in range(nx + 1):
                n = grid[i][solid_j] if i < nx and grid[i][empty_j] is None else None
                if n is not None and solids[n].hidden: n = None
                if run and (n != run[0]):
                    out.append((look_of(run[0], kind), kind, (run[1], xs[i]), ys[j], -DEPTH, depth(run[0]), shades[kind], None))
                    run = None
                if n is not None and not run: run = (n, xs[i])
    # Vertical faces: runs along y for each x line.
    for i in range(nx + 1):
        for kind, solid_i, empty_i in (('right', i - 1, i), ('left', i, i - 1)):
            if not (0 <= solid_i < nx and 0 <= empty_i < nx): continue
            run = None
            for j in range(ny + 1):
                n = grid[solid_i][j] if j < ny and grid[empty_i][j] is None else None
                if n is not None and solids[n].hidden: n = None
                if run and (n != run[0]):
                    out.append((look_of(run[0], 'side'), kind, xs[i], (run[1], ys[j]), -DEPTH, depth(run[0]), shades['side'], None))
                    run = None
                if n is not None and not run: run = (n, ys[j])
    # Fills: two solids of different depth side by side or stacked. The deeper one's face goes on in front of the other.
    def visible(n): return n is not None and not solids[n].hidden
    for i in range(1, nx):
        run = None
        for j in range(ny + 1):
            a, b = (grid[i - 1][j], grid[i][j]) if j < ny else (None, None)
            key = (a, b) if visible(a) and visible(b) and a != b and depth(a) != depth(b) else None
            if run and key != run[0]:
                a0, b0 = run[0]
                deep, kind = (a0, 'right_fill') if depth(a0) > depth(b0) else (b0, 'left_fill')
                out.append((look_of(deep, 'side'), kind, xs[i], (run[1], ys[j]), min(depth(a0), depth(b0)), depth(deep), shades['side'], None))
                run = None
            if key and not run: run = (key, ys[j])
    for j in range(1, ny):
        run = None
        for i in range(nx + 1):
            lower, upper = (grid[i][j - 1], grid[i][j]) if i < nx else (None, None)
            key = (lower, upper) if visible(lower) and visible(upper) and lower != upper and depth(upper) > depth(lower) else None
            if run and key != run[0]:
                out.append((look_of(run[0][1], 'under'), 'under_fill', (run[1], xs[i]), ys[j], depth(run[0][0]), depth(run[0][1]), shades['under'], None))
                run = None
            if key and not run: run = (key, xs[i])
    # Faces toward the camera and the back wall: one rectangle per row run of one solid or one panel.
    def panel_of(i, j):
        cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
        return next((n for n in reversed(range(len(room.panels)))
                     if room.panels[n].x0 <= cx <= room.panels[n].x1 and room.panels[n].y0 <= cy <= room.panels[n].y1), None)
    for j in range(ny):
        run = None
        for i in range(nx + 1):
            if i == nx: key = 'end'
            elif grid[i][j] is None: key = ('back', panel_of(i, j))
            elif solids[grid[i][j]].hidden: key = 'hidden'
            else: key = ('front', grid[i][j])
            if run and key != run[0]:
                rect = (run[1], ys[j], xs[i], ys[j + 1])
                if run[0] != 'hidden' and run[0][0] == 'front':
                    n = run[0][1]
                    if depth(n) < DEPTH:
                        out.append((solids[n].front or look_of(n, 'side'), 'front', rect, None, None, depth(n), shades['body'], None))
                    else: out.append((look_of(n, 'front'), 'front', rect, None, None, DEPTH, shades['front'], None))
                elif run[0] != 'hidden':
                    panel = None if run[0][1] is None else room.panels[run[0][1]]
                    if panel and panel.look is None: pass
                    elif panel: out.append((panel.look, 'back', rect, None, None, -DEPTH, panel.shade, panel))
                    elif room.theme.get('back'): out.append((room.theme['back'], 'back', rect, None, None, -DEPTH, room.back_shade, None))
                run = None
            if key != 'end' and not run: run = (key, xs[i])
    # Aprons: what a free-standing solid stands on continues in front of it.
    for n, s in enumerate(solids):
        if s.hidden or depth(n) >= DEPTH: continue
        for i in range(nx):
            if not (s.x0 <= (xs[i] + xs[i + 1]) / 2 <= s.x1): continue
            j = next((j for j in range(ny) if ys[j + 1] == s.y0), None)
            below = grid[i][j] if j is not None else None
            if below is None or solids[below].hidden or depth(below) <= depth(n): continue
            out.append((look_of(below, 'top'), 'apron', (xs[i], xs[i + 1]), s.y0, depth(n), depth(below), shades['top'], None))
    return out


def surfaces(room):
    """Visible plan surfaces inside the bounds: ('top' | 'under', x0, x1, y) and ('wall_left' | 'wall_right', x, y0, y1).

    'wall_left' is a wall on the left of open space (it faces right).
    """
    bx0, by0, bx1, by1 = room.bounds
    out = []
    for _, kind, a, b, *_ in _plan_faces(room):
        if kind in ('top', 'under'):
            x0, x1 = max(a[0], bx0), min(a[1], bx1)
            if x0 < x1 and by0 <= b <= by1: out.append((kind, x0, x1, b))
        elif kind in ('left', 'right'):
            y0, y1 = max(b[0], by0), min(b[1], by1)
            if y0 < y1 and bx0 <= a <= bx1: out.append(('wall_right' if kind == 'left' else 'wall_left', a, y0, y1))
    return out


def _normal(corners):
    e1 = [q - p for p, q in zip(corners[0], corners[1])]
    e2 = [q - p for p, q in zip(corners[1], corners[2])]
    return (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])


def _emit(room, sizes):
    """{texture: [(colour, [(x, y, z, s, t) * 4])]} for the whole room; every quad is counter-clockwise for its viewer."""
    by_texture = {}
    missing = {f[0].texture for f in _plan_faces(room)} | {q.look.texture for q in room.scenery}
    if missing - set(sizes): raise ValueError(f'Looks name textures the room does not hold: {sorted(missing - set(sizes))}')
    def add(look, corners, texels, shade, facing=None):
        w, h = sizes[look.texture]
        base_s = math.floor(min(t[0] for t in texels) / w) * w
        base_t = math.floor(min(t[1] for t in texels) / h) * h
        colour = sum(min(31, max(0, round(c * shade))) << (5 * k) for k, c in enumerate(look.tint))
        if facing is not None:
            axis, sign = facing
            normal = _normal(corners)
            if normal[axis] * sign <= 0 or any(normal[k] for k in range(3) if k != axis): raise ValueError('Face winding is wrong')
        by_texture.setdefault(look.texture, []).append(
            (colour, [(*p, t[0] - base_s, t[1] - base_t) for p, t in zip(corners, texels)]))
    D = DEPTH
    for look, kind, a, b, z0, z1, shade, anchor in _plan_faces(room):
        w, h = sizes[look.texture]
        su, sv = look.size
        step_u, step_v = su * MAX_TEXELS / w, sv * MAX_TEXELS / h
        if kind in ('top', 'under', 'apron', 'under_fill'):
            y, under = b, kind.startswith('under')
            for x0, x1 in zip(_cuts(*a, step_u), _cuts(*a, step_u)[1:]):
                corners = ((x0, y, z0), (x0, y, z1), (x1, y, z1), (x1, y, z0))
                texels = [(p[0] / su * w, (p[2] + D) / sv * h) for p in corners]
                if under: corners, texels = corners[::-1], texels[::-1]
                add(look, corners, texels, shade, (1, -1 if under else 1))
        elif kind in ('left', 'right', 'left_fill', 'right_fill'):
            x, right = a, kind.startswith('right')
            for y0, y1 in zip(_cuts(*b, step_v), _cuts(*b, step_v)[1:]):
                corners = ((x, y1, z0), (x, y0, z0), (x, y0, z1), (x, y1, z1))      # faces -x (the solid is on the right)
                texels = [((p[2] + D) / su * w, -p[1] / sv * h) for p in corners]
                if right: corners, texels = corners[::-1], texels[::-1]            # solid on the left: faces +x
                add(look, corners, texels, shade, (0, 1 if right else -1))
        else:
            ox, oy = (anchor.anchor if anchor else None) or (0.0, 0.0)
            flip = -1 if anchor and anchor.mirror else 1
            xs, ys = _cuts(a[0], a[2], step_u), _cuts(a[1], a[3], step_v)
            for x0, x1 in zip(xs, xs[1:]):
                for y0, y1 in zip(ys, ys[1:]):
                    corners = ((x0, y1, z1), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1))
                    add(look, corners, [(flip * (p[0] - ox) / su * w, (oy - p[1]) / sv * h) for p in corners], shade, (2, 1))
    for q in room.scenery:
        if not any(_normal(q.corners)): raise ValueError('Scenery quad has no area')
        w, h = sizes[q.look.texture]
        add(q.look, q.corners, [(u * w, v * h) for u, v in q.repeats], q.shade)
    return by_texture


def _stream(faces, scale):
    """GPU command stream of textured, coloured quads (vertex units = world units * 4096 / scale)."""
    commands, last = [(0x40, (1,))], None
    for colour, vertices in faces:
        if colour != last:
            commands.append((0x20, (colour,))); last = colour
        for x, y, z, s, t in vertices:
            st = [round(v * 16) for v in (s, t)]
            xyz = [round(v * 4096 * 4096 / scale) for v in (x, y, z)]
            if any(not -32768 <= v < 32768 for v in (*st, *xyz)): raise ValueError('Vertex or texture coordinate out of range')
            commands.append((0x22, ((st[0] & 65535) | (st[1] & 65535) << 16,)))
            commands.append((0x23, ((xyz[0] & 65535) | (xyz[1] & 65535) << 16, xyz[2] & 65535)))
    commands.append((0x41, ()))
    commands += [(0, ())] * (-len(commands) % 4)
    out = bytearray()
    for at in range(0, len(commands), 4):
        group = commands[at:at + 4]
        out += bytes(op for op, _ in group)
        for _, params in group: out += struct.pack(f'<{len(params)}I', *params)
    return bytes(out)


def compile_room(room):
    """Model, texture archive and collision file of a room description."""
    names = [t.name for t in room.textures]
    if len(set(names)) != len(names): raise ValueError('Duplicate texture names')
    if {p.name for p in room.palettes} != {n + '_pl' for n in names}: raise ValueError('Every texture needs its <name>_pl palette')
    sizes = {t.name: (t.width, t.height) for t in room.textures}
    by_texture = _emit(room, sizes)
    used = [n for n in names if n in by_texture]
    extent = max(abs(v) for faces in by_texture.values() for _, vertices in faces for p in vertices for v in p[:3])
    scale = next((s for s in (64, 128, 256, 512) if extent < 8 * s - 1), None)
    if scale is None: raise ValueError('Room is larger than the vertex range')
    scale_q12 = scale * 4096
    points = [p[:3] for faces in by_texture.values() for _, vertices in faces for p in vertices]
    lo = [min(p[k] for p in points) for k in range(3)]
    hi = [max(p[k] for p in points) for k in range(3)]
    quads = sum(len(f) for f in by_texture.values())
    if quads > 1800: raise ValueError(f'{quads} quads: over the budget of one room')
    textures = tuple(t for t in room.textures if t.name in by_texture)
    palettes = tuple(p for p in room.palettes if p.name[:-3] in by_texture)
    materials = tuple(nb.Material(f'm_{n}'[:16], n, n + '_pl', nb.material_record(*sizes[n])) for n in used)
    model = nb.RoomModel(
        name=room.name[:16], node='world_root', node_data=bytes((0x07, 0xF8, 0x00, 0x10)), materials=materials,
        streams=tuple(_stream(by_texture[n], scale_q12) for n in used), draw=tuple((i, i) for i in range(len(used))),
        scale=scale_q12, counts=(quads * 4, quads, 0, quads),
        box=tuple(round(v * 4096 / scale) for v in (*lo, *(h - l for l, h in zip(lo, hi)))), box_scale=scale_q12)
    return Compiled(nb.room_model(model), nb.texture_archive(textures, palettes), collision(room), quads,
                    {n: len(by_texture[n]) for n in used})


# --- textures ------------------------------------------------------------------
def borrow(archive, name, rename=None):
    """(Texture, Palette) copied from a native texture archive, optionally under a new name."""
    textures, palettes = nb.archive_parts(archive)
    texture = next(t for t in textures if t.name == name)
    palette = next(p for p in palettes if p.name == name + '_pl')
    new = rename or name
    return (nb.Texture(new, texture.width, texture.height, texture.format, texture.data, texture.index, texture.flags, texture.extra),
            nb.Palette(new + '_pl', palette.data, palette.flag))


def _quantize(pixels, colours):
    """Median cut: (palette [(r, g, b) 5-bit], index per pixel)."""
    boxes = [list(set(pixels))]
    while len(boxes) < colours:
        best, spread, axis = None, 0, 0
        for n, group in enumerate(boxes):
            if len(group) < 2: continue
            for k in range(3):
                values = [c[k] for c in group]
                d = max(values) - min(values)
                if d * len(group) ** 0.5 > spread: best, spread, axis = n, d * len(group) ** 0.5, k
        if best is None: break
        group = sorted(boxes.pop(best), key=lambda c: c[axis])
        boxes += [group[:len(group) // 2], group[len(group) // 2:]]
    palette, lookup = [], {}
    for n, group in enumerate(boxes):
        palette.append(tuple(round(sum(c[k] for c in group) / len(group)) for k in range(3)))
        for c in group: lookup[c] = n
    return palette, [lookup[p] for p in pixels]


def paint(name, width, height, pixels, colours=16):
    """(Texture, Palette) from 5-bit (r, g, b) pixels in rows: 16 colours (format 3) or 256 (format 4)."""
    if colours not in (16, 256) or len(pixels) != width * height: raise ValueError('paint needs width*height pixels and 16 or 256 colours')
    palette, index = _quantize([tuple(p) for p in pixels], colours)
    palette += [(0, 0, 0)] * (colours - len(palette))
    if colours == 16: data = bytes(index[i] | index[i + 1] << 4 for i in range(0, len(index), 2))
    else: data = bytes(index)
    raw = b''.join(struct.pack('<H', r | g << 5 | b << 10) for r, g, b in palette)
    return nb.Texture(name, width, height, 3 if colours == 16 else 4, data), nb.Palette(name + '_pl', raw)
