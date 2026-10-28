"""Long Arm harbour vista post-pass: the arena opens onto the bay.

The published hoist room hides the water behind a steel slab and two tall
pillars. This pass replaces only that scenery with see-through lattice towers and
a rail, and fills the empty bay with a far container quay and a moored freighter.
Everything is scenery behind the actor plane: the room's solids, so its collision
file, doors, anchors, objects and scripts stay exactly the published ones.

It rebuilds the room's model and texture pair from the published plan, so it
chains after any Crane Row build whose room model still is the published one and
is idempotent.
"""
import argparse
from dataclasses import replace
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import wos_tool as w, spider2099 as assets, tasm_kit as kit, midnight_voltage as extension
from tools import room_compiler as rc, crane_art as art, chapter_spectacle_rooms as rooms

ROOM = 106
MODEL, TEXTURE, COLLISION = (f'zz_R21_AR_LongArm{e}' for e in ('.nsbmd', '.nsbtx', '.bsp'))
MAX_QUADS = 480          # the busiest published room (Dry Dock) has 531

STEEL32 = rc.Look('HarborSteel', (32, 32))
DARK = art.DARK
SHIP = rc.Look('HarborShip', (64, 32))
STONE = rc.Look('HarborStone', (64, 64))
RED = rc.Look('HarborRed', (48, 48))
BLUE = rc.Look('HarborBlue', (48, 48))
HULL = art.HULL


def published_occluders():
    """The slab and tall pillars exactly as the published room builds them."""
    slab = rc.box(318, 0, -22, 386, 24, -12, art.STEEL, 1, 'front left right top')
    pillars = [q for x in (302, 402) for q in rc.box(x, 0, -42, x+6, 92, -34, STEEL32, .78, 'front top left right under')]
    return slab, pillars


def lattice(x, top=92):
    """A see-through tower: two legs, zig-zag bracing and a floodlight bank."""
    out = []
    for dx in (0, 4.6):
        out += rc.box(x+dx, 0, -41, x+dx+1.4, top, -38, STEEL32, .7, 'front left right')
    for n, y in enumerate(range(0, top-14, 14)):
        a, b = (x+1.4, x+4.6) if n % 2 else (x+4.6, x+1.4)
        out.append(art.bar(a, y, b, y+14, -39.5, 1, art.AMBER))
    out.append(art.face(art.LAMP, x-2, top-2, x+8, top+4, -37.5, 1))
    return out


def rail(x0, x1, step=12):
    """Posts and two rails along the deck edge, in place of the slab."""
    out = []
    for x in range(x0, x1+1, step):
        out += rc.box(x, 0, -21.5, x+1.4, 10, -20, art.STEEL, .85, 'front left right top')
    for y, width in ((10, 1.4), (5, 1.0)):
        out.append(art.bar(x0, y, x1+1.4, y, -20.8, width, art.AMBER))
    return out


def far_quay():
    """A low far pier with container stacks and lamps on the left half; the arena side stays open water."""
    out = rc.box(0, -4, -76, 246, 3, -58, STONE, .6, 'front top')
    stacks = ((10, 34, 2, RED), (58, 24, 1, BLUE), (92, 36, 2, RED), (140, 26, 1, BLUE),
              (178, 30, 2, BLUE), (216, 22, 1, RED))
    for x, width, height, look in stacks:
        top = 3+7*height
        out += rc.box(x, 3, -72, x+width, top, -62, look, .55, 'front top left right')
        out.append(art.face(art.LAMP, x+width/2-1.5, top+1, x+width/2+1.5, top+3.5, -61.8, 1))
    for x in (48, 132, 208):
        out.append(art.bar(x, 3, x, 30, -66, .9, art.STEEL))
        out.append(art.face(art.LAMP, x-3, 28, x+3, 32, -65.8, 1))
    return out


def freighter(x0=252, x1=416, z=-96):
    """A moored bulk carrier broadside to the camera, bow to the right, bridge toward the left."""
    out = [rc.Quad(SHIP, ((x0-4, 20, z), (x0+10, -4, z), (x1-12, -4, z), (x1+10, 20, z)), ((0, 0), (0, 1), (7, 1), (7, 0)), 1)]
    # Red waterline paint, a deck-edge rail and a row of lit portholes.
    out.append(rc.Quad(RED, ((x0+6.5, 4, z+.05), (x0+10, -4, z+.05), (x1-12, -4, z+.05), (x1-5, 4, z+.05)), shade=.95))
    out.append(art.face(art.EDGE, x0-4, 19, x1+10, 21.2, z+.1, 1))
    out.append(art.bar(x0-4, 23.5, x1+10, 23.5, z+.2, .7, art.STEEL))
    for lx in range(x0+14, x1-24, 13):
        out.append(art.face(art.LAMP, lx, 9.5, lx+2.4, 12, z+.12, 1))
    for x in range(x0+58, x1-30, 38):
        for y, look in ((20, RED), (27, BLUE)):
            out += rc.box(x, y, z-4, x+32, y+7, z+2, look, .62, 'front top left right')
    bx = x0+6
    out += rc.box(bx, 20, z-5, bx+34, 42, z+2, HULL, .8, 'front top left right')
    out += rc.box(bx+6, 42, z-3, bx+28, 50, z, HULL, .85, 'front top left right')
    out += rc.box(bx+12, 50, z-2, bx+19, 62, z-1, art.AMBER, .9, 'front top left right')
    for lx in range(bx+3, bx+31, 7):
        out.append(art.face(art.LAMP, lx, 32, lx+4, 36, z+2.1, 1))
        out.append(art.face(art.LAMP, lx+1, 44, lx+4, 47, z+.1, 1))
    for x in (x1-70, x1-34):
        out.append(art.bar(x, 27, x, 58, z+1, 1.2, art.STEEL))
    out.append(art.bar(x1-70, 58, x1-34, 58, z+1, 1, art.STEEL))
    out.append(art.face(art.LAMP, x1-54, 56, x1-50, 60, z+1.2, 1))
    return out


def vista(plan):
    slab, pillars = published_occluders()
    scenery = list(plan.scenery)
    for q in (*slab, *pillars):
        if q not in scenery:raise ValueError('Published Long Arm occluder differs')
        scenery.remove(q)
    new = [*lattice(302), *lattice(402), *rail(316, 388), *far_quay(), *freighter()]
    return replace(plan, scenery=tuple(scenery+new))


def native_plan():
    import mod
    _, glob, _ = mod.load_clean()
    offsets, names, _ = w.parse_glob(glob)
    return rooms.geometry(ROOM, lambda n: glob[offsets[names.index(n)]:offsets[names.index(n)+1]])


def apply_rom(rom):
    names, blobs = assets.resources(rom)
    before = tuple(blobs)
    plan = native_plan()
    old, new_plan = rc.compile_room(plan), vista(plan)
    new = rc.compile_room(new_plan)
    if new.collision != old.collision:raise ValueError('Vista changed the room collision')
    if new.quads > MAX_QUADS:raise ValueError(f'Vista has {new.quads} quads')
    for name, was, now in ((MODEL, old.model, new.model), (TEXTURE, old.textures, new.textures)):
        i = names.index(name)
        if before[i][:len(was)] != was and before[i][:len(now)] != now:raise ValueError('Room is not the published Long Arm')
        blobs[i] = now+bytes((len(before[i])-len(now)) % 4)
    if blobs[names.index(COLLISION)][:len(old.collision)] != old.collision:raise ValueError('Collision resource differs')
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    rt = extension.Runtime.__new__(extension.Runtime)
    rt.rom, rt.header, rt.arm, rt.new = rom, h, arm, bytearray(arm)
    rt.end, rt.data = len(arm)-36, bytearray()
    rt.start = kit.TARGET+rt.end-kit.SOURCE
    result = rt.finish()
    packed = w.pack_glob(names, blobs)
    ge = next(e for e in w.nitrofs_entries(result) if e['name'] == 'Glob.bin')
    growth = w.align_up(len(packed)-ge['size'])
    hh = w.parse_header(result)
    if growth > 0:
        import struct
        if hh['used_rom_size']+growth > len(result) or any(x not in (0, 255) for x in result[-growth:]):
            raise ValueError('Insufficient verified cart padding')
        staged = bytearray(result[:ge['end']]+bytes(growth)+result[ge['end']:-growth])
        for e in w.nitrofs_entries(result):
            if e['start'] >= ge['end']:
                struct.pack_into('<2I', staged, hh['fat_offset']+e['id']*8, e['start']+growth, e['end']+growth)
        struct.pack_into('<I', staged, 0x80, hh['used_rom_size']+growth)
        struct.pack_into('<H', staged, 0x15e, w.crc16(staged[:0x15e]))
        result = bytes(staged)
    result = w.rebuild_rom(result, {'Glob.bin': packed})
    w.validate_rom(result, target=True)
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if not set(changed) <= {MODEL, TEXTURE}:raise ValueError('Unexpected vista resource scope')
    hh = w.parse_header(result)
    return result, dict(parent_sha256=w.sha256(rom), rom_sha256=w.sha256(result),
        arm9_sha256=w.sha256(result[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']]),
        modified_resources=changed, nitrofs_relocation_bytes=max(growth, 0),
        quads=dict(published=old.quads, vista=new.quads), collision_identical=True)


def generate(output, source):
    output, source = Path(output), Path(source)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output/'Versioned.nds'
    w.atomic_write(path, result, sources=(source,))
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'], quads=report['quads'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True, help='Any Crane Row ROM whose Long Arm model is the published one')
    a = p.parse_args()
    generate(a.out, a.source)
