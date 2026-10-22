"""Scoped Rail Skitter resources and native-clock attack descriptors."""
import struct
import json
import zipfile
from pathlib import Path
from tools import wos_tool as w
from tools import chapter_finish_motion as motion, creature_forge as forge
from tools import midnight_finale_art as art, creature_forge_art as base_art
from tools import creature_texture_fix
from tools.rush_choreography import add


def model(template, neutral):
    s = art.Sculpt(template, neutral)
    p = s.p
    # A single low thorax, tucked abdomen and broad snout form one readable
    # predator. Four planted limbs remain separated from the body silhouette.
    c = add(p[3], (0, .1, -.2))
    base_art.Sculpt.loft(s, 3, add(c, (0, 0, -1.7)), add(c, (0, .1, 1.2)),
        ((0, .45, .45), (.3, 1.3, .9), (.72, 1.45, 1.0), (1, .8, .6)), 0, 6)
    s.tissue(1, add(p[1], (0, .1, -1.6)), p[2], .82, 3)
    for i, (a, b, e) in enumerate((*art.arms('hLpr'), (20, 21, 22), (24, 25, 26))):
        hand = i < 2
        s.tissue(a, p[a], p[b], .41 if hand else .34, 3)
        s.tissue(b, p[b], p[e], .5 if hand else .31, 0)
        palm = add(p[e], (0, -.12, .65 if hand else .25))
        s.tissue(e, p[e], palm, .27, 0)
        if hand:
            side = 1 if i == 0 else -1
            # Swept closed cutting edge, with a clear hook rather than several
            # tiny decorative needles. The joint turns the entire scythe.
            base_art.Sculpt.loft(s, e, add(palm, (side*.12, .1, 0)),
                add(palm, (side*.15, .6, 2.9)),
                ((0, .36, .22), (.48, .48, .18), (.82, .22, .12), (1, .015, .015)), 13, 4)
        else:
            s.claw(e, palm, add(palm, (0, -.15, .85)), .17, 13)
    head = add(p[5], (0, -.08, .65))
    base_art.Sculpt.loft(s, 5, add(head, (0, 0, -.65)), add(head, (0, 0, 1.4)),
        ((0, .75, .5), (.38, 1.05, .72), (.8, .85, .45), (1, .4, .25)), 0, 6)
    for side in (-1, 1):
        cx = head[0] + side*1.1
        vertices = tuple(add((cx, head[1], head[2]), q)
                         for q in ((0, .05, .05), (0, -.03, 1.1), (0, .37, .9), (0, .48, .02)))
        s.face(5, 9, tuple(reversed(vertices)) if side > 0 else vertices)
        s.side_panel(19, add(p[19], (side*.7, -.03, .45)), .2, .7, 3)
    for joint in (23, 27):
        s.ring(joint, 9)
    raw, report = s.finish()
    if report['quads'] > 360:
        raise ValueError('Skitter mesh exceeds the accepted crowd budget')
    raw, _ = creature_texture_fix.fix_model(raw)
    report.update(direction='Low joined thorax, large side eyes and two carried hooked scythes; native tint and shared atlas retained')
    return raw, report


def authored(names, native, parent):
    root = Path(__file__).resolve().parents[1]
    dependencies = ('chapter_finish_motion.py', 'chapter_finish_skitter.py',
                    'creature_forge_motion.py', 'midnight_enemy_motion.py',
                    'midnight_finale_art.py', 'creature_forge_art.py')
    key = w.sha256(b''.join((root/'tools'/name).read_bytes() for name in dependencies))
    cache = root/'work/chapter-finish'/('skitter-cache-'+key+'.zip')
    if cache.exists():
        with zipfile.ZipFile(cache) as source:
            info = json.loads(source.read('manifest.json'))
            extras = {name: source.read(name) for name in source.namelist() if name != 'manifest.json'}
        if info['hashes'] != {name: w.sha256(raw) for name, raw in extras.items()}:
            raise ValueError('Skitter authoring cache integrity failed')
        return extras, info['clips'], info['model']
    extras, clips, neutral = motion.prepare(native, names, parent)
    mesh, mesh_report = model(native('hLpr.nsbmd'), neutral)
    extras['zz_F22_skitter.nsbmd'] = mesh
    cache.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(cache, 'w', zipfile.ZIP_DEFLATED) as target:
        for name, raw in extras.items():
            target.writestr(name, raw)
        target.writestr('manifest.json', json.dumps({'clips': clips, 'model': mesh_report,
            'hashes': {name: w.sha256(raw) for name, raw in extras.items()}}))
    return extras, clips, mesh_report


def apply(runtime, meta, names, blobs, native, parent):
    extras, clips, mesh_report = authored(names, native, parent)
    changed = []
    for name, raw in extras.items():
        if name not in names:
            raise ValueError('Skitter pass cannot change the binding namespace: ' + name)
        i = names.index(name)
        blobs[i] = raw + bytes((len(blobs[i]) - len(raw)) % 4)
        changed.append(name)
    rows = []
    for i, move in enumerate(motion.MOVES):
        drive = runtime.alloc(b''.join(struct.pack('<3i', a, b, round(speed*4096))
                                      for a, b, speed in move.drives) + struct.pack('<3i', 0x7fffffff, 0, 0))
        jump = runtime.alloc(b''.join(struct.pack('<2i', a, round(speed*4096)) for a, speed in move.jumps)
                             + struct.pack('<2i', 0x7fffffff, 0))
        cues = runtime.alloc(b''.join(struct.pack('<2i', a, 653+35+9+i) for a, _ in move.contacts)
                             + struct.pack('<2i', 0x7fffffff, 0))
        rows.append(struct.pack('<8I', move.action, move.samples-1, move.cooldown,
                                drive, jump, cues, 12+i, round(move.reach*4096)))
    table = runtime.alloc(b''.join(rows))
    records = meta['creature_forge']['runtime']['records']
    struct.pack_into('<2I', runtime.new, forge.offset(records)+3*16+4, table, len(rows))
    return {'modified_resources': changed, 'clips': clips, 'model': mesh_report,
            'programs': [vars(m) for m in motion.MOVES], 'table': table,
            'ownership': 'Only the already-private Skitter resources and descriptor row change; other actor bindings remain exact.'}
