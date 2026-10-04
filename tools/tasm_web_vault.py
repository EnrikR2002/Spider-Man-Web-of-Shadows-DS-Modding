"""Compose purchased Web Vault with the accepted Rebound and cosmetic overlays."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w
from tools import tasm_rebound as tr
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.qol_suits_menu import StringSlots
from tools.sca import Sca

ASSET = 'spd_GrapplePullBack.gmb'
POSE_ASSET = 'spd_GrapplePullBack.sca'
ADVANCE_Q12 = (0, 0, 0, 8192, 24576, 40960, 40960, 40960, 40960)
POSE_KEYS = ((3, 4), (4, 9), (5, 14))
TEXT_EDITS = {186: 'Web Vault', 187: 'Web Vault',
              188: 'Press up on \xbf while grappling.\nLaunch and vault after the enemy.'}


def advance(raw):
    wrapped = CompressedBlob.parse(raw)
    original = Gmb.parse(wrapped.decoded)
    if original.record_count != 9 or [(c.kind,c.unknown_u16_02) for c in original.channels] != [(3,0),(3,1),(3,0),(0,0)]:
        raise ValueError('Unexpected native Web Launch GMB profile')
    if any(original.channels[0].words(f)[2] for f in range(9)):
        raise ValueError('Native Web Launch already has root displacement')
    changed = original.raw
    for frame, value in enumerate(ADVANCE_Q12):
        changed = Gmb.parse(changed).replace_word(0, frame, 2, value)
    if changed[original.channels[1].offset:] != original.raw[original.channels[1].offset:]:
        raise ValueError('Vault changed non-root channels')
    return wrapped.replace_decoded(changed)


def pose(raw):
    original = Sca.parse(raw)
    if (original.frame_count,original.joint_count,original.frame_stride) != (9,37,612):
        raise ValueError('Unexpected native Web Launch skeleton')
    changed = raw
    for frame, angle in POSE_KEYS:
        changed = Sca.parse(changed).rotate_joint(3, frame, 'x', angle)
    return changed


def text_overlay(clean, current):
    slots = StringSlots(clean)
    edits = {i: slots.decode(current,i) for i in range(len(slots.texts))
             if slots.decode(current,i) != slots.texts[i]}
    edits.update(tr.TEXT_EDITS)
    edits.update(TEXT_EDITS)
    return slots.replace(edits)


def generate(base_mods='mods', output='build/tasm-web-vault'):
    root = w.safe_output(mod.project_path(output))
    if not root.is_relative_to((mod.ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    rom, glob, manifest = mod.load_clean()
    names = [e['name'] for e in manifest['entries']]
    overlays = mod.overlay_files(mod.project_path(base_mods),names)
    transforms = {tr.ASSET: tr.recoil, tr.POSE_ASSET: tr.pose, ASSET: advance, POSE_ASSET: pose}
    for name, transform in transforms.items():
        entry = next(e for e in manifest['entries'] if e['name']==name)
        clean = glob[entry['offset']:entry['offset']+entry['size']]
        changed = transform(clean)
        if overlays.get(name,clean) not in (clean,changed):
            raise ValueError(f'Existing overlay needs an explicit merge: {name}')
        overlays[name] = changed
    for name in ('American.strings','English.strings'):
        entry = next(e for e in manifest['entries'] if e['name']==name)
        clean = glob[entry['offset']:entry['offset']+entry['size']]
        overlays[name] = text_overlay(clean,overlays.get(name,clean))
    for name,data in overlays.items():
        w.atomic_write(root/'mods'/name,data,(mod.DEFAULT_ROM,))
    recipe = {'schema_version':1,'profile':'tasm-web-vault',
              'required_overlays':{name:w.sha256(overlays[name]) for name in
                 (*transforms,'spd.xbd','American.strings','English.strings')}}
    w.write_json(root/'gameplay_profile.json',recipe)
    build,_,log = mod.create_build(rom,glob,manifest,overlays,gameplay_profile='tasm-web-vault')
    path = root/'WebVault.nds'
    w.atomic_write(path,build,(mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'),log)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mods',default='mods'); parser.add_argument('--out',default='build/tasm-web-vault')
    args = parser.parse_args(argv)
    try: print(generate(args.mods,args.out))
    except (OSError,ValueError) as exc:
        print(f'error: {exc}',file=sys.stderr); return 1
    return 0


if __name__=='__main__': raise SystemExit(main())
