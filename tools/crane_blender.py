"""Build a private Ballast Blender study over the exact published v0.40.0 ROM.

The native rig, material, texture and quad budget remain intact. This is a
research candidate, not a release or a replacement for the stable playtest ROM.
"""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import model_bridge as bridge, spider2099 as assets, wos_tool as w
from tools.crane_creature_art import packets
from tools.spider2099_art import gpu_commands

PARENT = 'bf9b63a95bff3c1edfea1e3f8acbc4503a9521fb87bdcb333a87bedfef9fd0c6'
MODEL = 'zz_F22_ballast.nsbmd'
TEXTURE = 'zz_C40_ballast.nsbtx'
BLENDER = Path('C:/Program Files/Blender Foundation/Blender 4.5/blender.exe')


def rewrite(raw, texture, glb):
    """Apply the edited rigid vertices and new quads to the native quad stream."""
    imported, result_texture, report = bridge.import_glb(glb, raw, texture)
    if result_texture != texture or report['collapsed_weight_vertices'] or report['ancestor_remapped_vertices']:
        raise ValueError('The study must retain the texture and rigid bone bindings')
    old = bridge.triangles(raw)
    if any(len(set(face)) != 3 for face in old):
        raise ValueError('Unexpected degenerate Ballast topology')
    edited = bridge.triangles(imported)
    if len(edited) < len(old) or (len(edited) - len(old)) % 2:
        raise ValueError('Expected the existing faces followed by added quads')
    base, extra = edited[:len(old)], edited[len(old):]
    mapping = {}
    for source_face, target_face in zip(old, base):
        for source, target in zip(source_face, target_face):
            if (source[0], source[2]) != (target[0], target[2]):
                raise ValueError('Existing topology, UV or bone changed')
            if source in mapping and mapping[source] != target[1]:
                raise ValueError('A shared vertex was split inconsistently')
            mapping[source] = target[1]

    _, _, _, _, _, slot = bridge.template(raw)
    uv, commands = (0, 0), []
    changed = 0
    for op, args in gpu_commands(raw):
        if op == 0x14:
            slot = args[0]
        elif op == 0x22:
            uv = (bridge._signed(args[0], 16), bridge._signed(args[0] >> 16, 16))
        elif op == 0x23:
            p = (bridge._signed(args[0], 16), bridge._signed(args[0] >> 16, 16), bridge._signed(args[1], 16))
            q = mapping.get((slot, p, uv), p)
            changed += q != p
            args = ((q[0] & 65535) | (q[1] & 65535) << 16, q[2] & 65535)
        elif 0x24 <= op <= 0x28:
            raise ValueError('Ballast must use VTX_16 commands')
        commands.append((op, args))
    shape = bridge.ModelGeometry.parse(raw).shapes[0]
    stream = packets(commands)
    if len(stream) != shape.length or shape.start + shape.length != len(raw):
        raise ValueError('Unexpected Ballast GPU stream framing')
    additions = []
    for i in range(0, len(extra), 2):
        a, b = extra[i:i + 2]
        if a[0] != b[0] or a[2] != b[1] or len({v[0] for v in (*a, *b)}) != 1:
            raise ValueError('Expected a rigid triangulated quad')
        quad = (a[0], a[1], a[2], b[2])
        additions.extend(((0x14, (quad[0][0],)), (0x40, (1,))))
        for _, (x, y, z), (u, v) in quad:
            additions.extend(((0x22, ((u & 65535) | (v & 65535) << 16,)),
                              (0x23, ((x & 65535) | (y & 65535) << 16, z & 65535))))
        additions.append((0x41, ()))
    tail = packets(additions) if additions else b''
    out = bytearray(raw[:shape.start] + stream + tail)
    geometry = bridge.ModelGeometry.parse(raw)
    if tail:
        struct.pack_into('<I', out, 8, len(out))
        struct.pack_into('<I', out, geometry.block + 4, len(out) - geometry.block)
        struct.pack_into('<I', out, geometry.model, len(out) - geometry.model)
        struct.pack_into('<I', out, shape.header + 12, len(stream) + len(tail))
        vertices, polygons, triangles, quads = struct.unpack_from('<4H', raw, geometry.model + 36)
        if triangles:
            raise ValueError('Expected a quad-only Ballast model')
        count = len(extra) // 2
        struct.pack_into('<4H', out, geometry.model + 36, vertices + 4 * count, polygons + count, 0, quads + count)
    imported_geometry = bridge.ModelGeometry.parse(imported)
    out[geometry.model + 44:geometry.model + 56] = imported[imported_geometry.model + 44:imported_geometry.model + 56]
    if bridge.triangles(out) != edited:
        raise ValueError('Edited quad stream differs from Blender')
    return bytes(out), {'changed_vertices': changed, 'added_quads': len(extra) // 2}


def replace_old_armor(raw):
    """Remove the old shoulder plates and duplicate wrist blades replaced in Blender."""
    geometry = bridge.ModelGeometry.parse(raw)
    shape = geometry.shapes[0]
    _, rig, _, _, slots, slot = bridge.template(raw)
    if shape.start + shape.length != len(raw):
        raise ValueError('Expected the final shape at the end of the model')
    commands, out, visited, removed = list(gpu_commands(raw)), [], set(), []
    i = 0
    while i < len(commands):
        op, args = commands[i]
        if op == 0x14:
            slot = args[0]
        name = rig.names[slots[slot]].split(':')[-1]
        target = name in ('Shoulder_L', 'Shoulder_R', 'Wrist_L', 'Wrist_R') and name not in visited
        if op == 0x40 and target:
            visited.add(name)
            end = next((j for j in range(i + 1, len(commands)) if commands[j][0] == 0x41), None)
            if end is None:
                raise ValueError('Unterminated Ballast quad group')
            body = commands[i + 1:end]
            count = 17 if name.startswith('Shoulder') else 15
            if args != (1,) or len(body) != 8 * count or any(
                    body[j][0] != (0x22 if j % 2 == 0 else 0x23) for j in range(len(body))):
                raise ValueError('Unexpected Ballast quad group')
            drop = range(12, 17) if count == 17 else range(10, 15)
            out.append(commands[i])
            for k in range(count):
                if k in drop:
                    removed.append((slot, k))
                else:
                    out.extend(body[k * 8:k * 8 + 8])
            out.append(commands[end])
            i = end + 1
            continue
        out.append(commands[i])
        i += 1
    if len(removed) != 20 or len(visited) != 4:
        raise ValueError('Expected twenty replaced Ballast quads')
    stream = packets(out)
    result = bytearray(raw[:shape.start] + stream)
    struct.pack_into('<I', result, 8, len(result))
    struct.pack_into('<I', result, geometry.block + 4, len(result) - geometry.block)
    struct.pack_into('<I', result, geometry.model, len(result) - geometry.model)
    struct.pack_into('<I', result, shape.header + 12, len(stream))
    vertices, polygons, triangles, quads = struct.unpack_from('<4H', raw, geometry.model + 36)
    struct.pack_into('<4H', result, geometry.model + 36, vertices - 80, polygons - 20, triangles, quads - 20)
    faces, expected, seen = bridge.triangles(raw), [], {}
    for i in range(0, len(faces), 2):
        slot = faces[i][0][0]
        index = seen.get(slot, 0)
        seen[slot] = index + 1
        if (slot, index) not in removed:
            expected.extend(faces[i:i + 2])
    if bridge.triangles(result) != expected:
        raise ValueError('The surviving Ballast geometry differs')
    return bytes(result)


def sculpt(raw, texture, blender=BLENDER):
    """Use the local Blender process; keep intermediate game derivatives private."""
    scratch = (ROOT / 'work/crane-models').resolve()
    if not scratch.is_relative_to(ROOT.resolve()):
        raise ValueError('Blender scratch directory must remain in the workspace')
    scratch.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='blender-', dir=scratch))
    source, edited = folder / 'source.glb', folder / 'edited.glb'
    source.write_bytes(bridge.export_glb(raw, texture, MODEL))
    try:
        versions = subprocess.run([str(blender), '--version'], check=True, capture_output=True, text=True).stdout.splitlines()
        if not versions or not versions[0].startswith('Blender '):
            raise ValueError('The selected program did not report a Blender version')
        version = versions[0]
        subprocess.run([str(blender), '--background', '--factory-startup', '--python-exit-code', '1',
                        '--python', str(ROOT / 'tools/crane_blender_art.py'), '--', str(source), str(edited)],
                       check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        raise RuntimeError('Blender sculpt failed: ' + (error.stderr + error.stdout)[-4000:]) from error
    model, report = rewrite(raw, texture, edited.read_bytes())
    if report['added_quads'] != 20:
        raise ValueError('Expected twenty Blender armor quads')
    model = replace_old_armor(model)
    before, after = bridge.ModelGeometry.parse(raw), bridge.ModelGeometry.parse(model)
    if raw[before.model + 36:before.model + 44] != model[after.model + 36:after.model + 44]:
        raise ValueError('Ballast polygon or vertex budget changed')
    return model, {**report, 'removed_quads': 20, 'model_bytes': [len(raw), len(model)], 'blender_version': version}


def candidate(parent, output, blender=BLENDER):
    parent, output = Path(parent), Path(output).resolve()
    research = (ROOT / 'build/crane-models').resolve()
    if (not research.is_relative_to(ROOT.resolve()) or not output.is_relative_to(research)
            or output.suffix.lower() != '.nds'):
        raise ValueError('Research ROM must be an .nds under build/crane-models/')
    rom = parent.read_bytes()
    if w.sha256(rom) != PARENT:
        raise ValueError('Ballast research requires exact published v0.40.0')
    names, blobs = assets.resources(rom)
    original = tuple(blobs)
    index = names.index(MODEL)
    blobs[index], report = sculpt(blobs[index], blobs[names.index(TEXTURE)], blender)
    if [name for name, a, b in zip(names, original, blobs) if a != b] != [MODEL]:
        raise ValueError('Unexpected modified resources')
    result = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(names, blobs)}, legacy_gaps=True)
    validation = w.validate_rom(result, target=True)
    entry = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta = json.loads(parent.with_suffix('.build.json').read_text(encoding='utf-8'))
    report.update(parent_sha256=PARENT, rom_sha256=w.sha256(result), modified_resources=[MODEL])
    meta.update(crane_blender_study=report, output=str(output), output_rom_sha256=report['rom_sha256'],
                output_glob_sha256=w.sha256(result[entry['start']:entry['end']]),
                rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
                nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'])
    w.atomic_write(output, result, sources=(parent,))
    w.write_json(output.with_suffix('.build.json'), meta)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--parent', type=Path, default=ROOT / 'build/Spider-Man-WoS-modded.nds')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--blender', type=Path, default=BLENDER)
    args = parser.parse_args()
    print(json.dumps(candidate(args.parent, args.out, args.blender), indent=2))


if __name__ == '__main__':
    main()
