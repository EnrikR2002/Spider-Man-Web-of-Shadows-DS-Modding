"""Authoring pieces of a room's object file that the door and script tools do not cover.

Camera regions: section 4 of record 0 holds polygons (world units, Q12) the
camera's look-at point is kept inside; the camera sits at Spidey's x and
y + 4, 60 units in front of the play plane. Layout: one u16 offset per
polygon, one u8 point count per polygon, zero padding to a word, then 20-byte
points (x, y and three zero words). Native rooms inset the room by 20 units on
the left and right and not at all above and below. A room with no polygon
(the debug rooms) has a free camera. See TECHNICAL "Room compiler".
"""
from __future__ import annotations
import struct

from tools.room_objects import RoomObjects

POINT = 20
VIEW_INSET = 20.0                # native rooms: polygon = room narrowed by 20 units on each side


# --- Anchor points -------------------------------------------------------------
# Section 3 of record 0: 20-byte points (x, y, z, 0, kind) in entity-batch
# framing. Kinds as laid out in the native training room: 1 on a floor (2 above
# it), 2 beside a left wall, 3 beside a right wall, 4 under a ceiling, 5 in open
# air. Enemy spawners place their enemies on them: a room without them spawns
# nobody (lab 2026-10-12, TECHNICAL "Room compiler").
FLOOR, LEFT_WALL, RIGHT_WALL, CEILING, AIR = 1, 2, 3, 4, 5


def anchors(raw):
    """[(x, y, kind)] of record 0's first anchor batch (world units)."""
    section = RoomObjects.parse(raw).records[0].sections[3]
    if not section: return []
    total, head, count = struct.unpack_from('<HBB', section)
    if any(n != POINT for n in section[4:4 + count]): raise ValueError('Unexpected anchor record size')
    out = []
    for i in range(count):
        x, y, _, zero, kind = struct.unpack_from('<5i', section, head + POINT * i)
        if zero: raise ValueError('Anchor carries an unknown word')
        out.append((x / 4096, y / 4096, kind))
    return out


def anchor_section(points):
    points = list(points)
    if not points: return b''
    if len(points) > 255: raise ValueError('Too many anchor points for one batch')
    head = (4 + len(points) + 3) // 4 * 4
    out = struct.pack('<HBB', head + POINT * len(points), head, len(points)) + bytes((POINT,)) * len(points)
    out += bytes(head - len(out))
    for x, y, kind in points:
        if kind not in (FLOOR, LEFT_WALL, RIGHT_WALL, CEILING, AIR): raise ValueError('Unknown anchor kind')
        out += struct.pack('<5i', round(x * 4096), round(y * 4096), 0, 0, kind)
    return out


def set_anchors(raw, points):
    result = RoomObjects.parse(raw).replace_section(0, 3, anchor_section(points))
    if len(anchors(result)) != len(list(points)): raise ValueError('Anchor points did not survive')
    return result


def plan_anchors(surfaces, area, spacing=20.0, solid=None, floor_top=None):
    """Anchor points for a compiled plan: `surfaces` from room_compiler.surfaces, inside `area` (x0, y0, x1, y1).

    Floors up to `floor_top` (enemies appear on floor points; a gang put on a
    high platform stays there) get a point every `spacing` units (2 above), ceilings likewise (4
    below), walls every `spacing` up their height (3.5 off the wall) and open
    air a row of points half way up wherever `solid(x, y)` says it is free.
    """
    ax0, ay0, ax1, ay1 = area
    def steps(lo, hi, inset):
        lo, hi = lo + inset, hi - inset
        if hi < lo: return []
        n = max(1, round((hi - lo) / spacing))
        return [lo + (hi - lo) * i / n for i in range(n + 1)] if hi > lo else [lo]
    points = []
    for kind, a, b, c in surfaces:
        if kind == 'top':
            if floor_top is not None and c > floor_top: continue
            points += [(x, c + 2, FLOOR) for x in steps(max(a, ax0), min(b, ax1), 4) if ay0 <= c <= ay1 - 10]
        elif kind == 'under':
            points += [(x, c - 4, CEILING) for x in steps(max(a, ax0), min(b, ax1), 4) if ay0 + 10 <= c <= ay1]
        elif ax0 <= a <= ax1:
            side, x = (LEFT_WALL, a + 3.5) if kind == 'wall_left' else (RIGHT_WALL, a - 3.5)
            points += [(x, y, side) for y in steps(max(b, ay0), min(c, ay1), 6)]
    if solid:
        y = (ay0 + ay1) / 2
        points += [(x, y, AIR) for x in steps(ax0, ax1, 10) if not solid(x, y) and not solid(x, y - 6) and not solid(x, y + 6)]
    return points


def camera(raw):
    """Camera polygons of a room's object file: a tuple of tuples of (x, y) in world units."""
    section = RoomObjects.parse(raw).records[0].sections[4]
    if not section: return ()
    first = struct.unpack_from('<H', section)[0]
    count = next((n for n in range(1, 16) if (3 * n + 3) // 4 * 4 == first), None)
    if count is None: raise ValueError('Unexpected camera header')
    offsets = struct.unpack_from(f'<{count}H', section)
    sizes = section[2 * count:3 * count]
    if any(section[3 * count:first]): raise ValueError('Camera header padding is not zero')
    out, at = [], first
    for offset, size in zip(offsets, sizes):
        if offset != at: raise ValueError('Camera polygons are not contiguous')
        points = []
        for i in range(size):
            x, y, *rest = struct.unpack_from('<5i', section, at + POINT * i)
            if any(rest): raise ValueError('Camera point carries unknown words')
            points.append((x / 4096, y / 4096))
        out.append(tuple(points))
        at += POINT * size
    if at != len(section): raise ValueError('Camera section has trailing bytes')
    return tuple(out)


def camera_section(polygons):
    polygons = [list(p) for p in polygons]
    if not polygons: return b''
    if len(polygons) > 15 or any(not 2 <= len(p) <= 255 for p in polygons): raise ValueError('Camera polygon limits exceeded')
    head = (3 * len(polygons) + 3) // 4 * 4
    offsets, at = [], head
    for p in polygons:
        offsets.append(at)
        at += POINT * len(p)
    out = struct.pack(f'<{len(polygons)}H', *offsets) + bytes(len(p) for p in polygons)
    out += bytes(head - len(out))
    for p in polygons:
        for x, y in p: out += struct.pack('<5i', round(x * 4096), round(y * 4096), 0, 0, 0)
    return out


def set_camera(raw, polygons):
    """Replace the camera polygons of record 0."""
    result = RoomObjects.parse(raw).replace_section(0, 4, camera_section(polygons))
    if camera(result) != tuple(tuple((round(x * 4096) / 4096, round(y * 4096) / 4096) for x, y in p) for p in polygons):
        raise ValueError('Camera polygons did not survive')
    return result


def room_camera(bounds, inset=VIEW_INSET):
    """The native rule for a rectangular room: narrowed by `inset` left and right, full height."""
    x0, y0, x1, y1 = bounds
    if x1 - x0 <= 2 * inset:                       # a narrow shaft: the camera rides its centre line
        mid = (x0 + x1) / 2
        return ((mid - 0.5, y1), (mid - 0.5, y0), (mid + 0.5, y0), (mid + 0.5, y1))
    return ((x0 + inset, y1), (x0 + inset, y0), (x1 - inset, y0), (x1 - inset, y1))
