"""Generate an isolated purchased Rebound experiment, preserving native hit data."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mod
from tools import wos_tool as w
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.sca import Sca
from tools.qol_suits_menu import StringSlots

ASSET = 'spd_GrapplePullAttackKick.gmb'
RECOIL_Q12 = (0, 0, 0, 0, 0, -4096, -10240, -16384, -20480)
POSE_ASSET = 'spd_GrapplePullAttackKick.sca'
POSE_KEYS = ((5, -5), (6, -11), (7, -16), (8, -12))
TEXT_EDITS = {183: 'Rebound', 184: 'Rebound',
              185: 'Grapple an enemy, then press \ue601.\nKick and recoil. Less enemy knockback.'}


def pose(raw):
    animation = Sca.parse(raw)
    if (animation.frame_count, animation.joint_count, animation.frame_stride) != (9, 37, 704):
        raise ValueError('Unexpected Web Kick skeletal profile')
    result = raw
    for frame, angle in POSE_KEYS:
        result = Sca.parse(result).rotate_joint(3, frame, 'x', angle)
    return result


def text_overlay(clean, current):
    profile = StringSlots(clean)
    edits = {i: profile.decode(current, i) for i in range(len(profile.texts))
             if profile.decode(current, i) != profile.texts[i]}
    edits.update(TEXT_EDITS)
    return profile.replace(edits)


def recoil(raw):
    wrapped = CompressedBlob.parse(raw)
    parsed = Gmb.parse(wrapped.decoded)
    if parsed.record_count != 9 or [(c.kind, c.unknown_u16_02) for c in parsed.channels] != [(3,0), (3,1), (3,0), (0,0)]:
        raise ValueError('Unexpected native Web Kick GMB profile')
    if any(parsed.channels[0].words(f)[2] for f in range(9)):
        raise ValueError('Native Web Kick already has nonzero root displacement')
    changed = parsed.raw
    for frame, value in enumerate(RECOIL_Q12):
        changed = Gmb.parse(changed).replace_word(0, frame, 2, value)
    # The hitbox, event tag, active windows, duration and unknown channels stay exact.
    start = parsed.channels[1].offset
    if changed[start:] != parsed.raw[start:]: raise ValueError('Recoil modified non-root channels')
    return wrapped.replace_decoded(changed)


def generate(base_mods='mods', output='build/tasm-research/rebound-motion'):
    root = w.safe_output(mod.project_path(output))
    if not root.is_relative_to((mod.ROOT/'build').resolve()): raise ValueError('Experiments belong in build/')
    rom, glob, manifest = mod.load_clean()
    names = [e['name'] for e in manifest['entries']]
    overlays = mod.overlay_files(mod.project_path(base_mods), names)
    entry = next(e for e in manifest['entries'] if e['name'] == ASSET)
    raw = glob[entry['offset']:entry['offset']+entry['size']]
    changed = recoil(raw)
    if ASSET in overlays and overlays[ASSET] not in (raw, changed): raise ValueError('Existing Web Kick edit needs an explicit merge')
    overlays[ASSET] = changed
    for name in (POSE_ASSET, 'American.strings', 'English.strings'):
        entry = next(e for e in manifest['entries'] if e['name'] == name)
        clean = glob[entry['offset']:entry['offset']+entry['size']]
        current = overlays.get(name, clean)
        if name == POSE_ASSET:
            altered = pose(clean)
            if current not in (clean, altered): raise ValueError('Existing skeletal edit needs an explicit merge')
            overlays[name] = altered
        else:
            overlays[name] = text_overlay(clean, current)
    for name, data in overlays.items(): w.atomic_write(root/'mods'/name, data, (mod.DEFAULT_ROM,))
    recipe = {'schema_version': 1, 'profile': 'tasm-rebound',
              'required_overlays': {name: w.sha256(overlays[name]) for name in
                  (ASSET, POSE_ASSET, 'spd.xbd', 'American.strings', 'English.strings')}}
    w.write_json(root/'gameplay_profile.json', recipe)
    build, _, log = mod.create_build(rom, glob, manifest, overlays, rebound=True)
    path = root/'Rebound.nds'
    w.atomic_write(path, build, (mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'), log)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mods', default='mods'); parser.add_argument('--out', default='build/tasm-research/rebound-motion')
    args = parser.parse_args(argv)
    try:
        print(generate(args.mods, args.out))
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__': main()
