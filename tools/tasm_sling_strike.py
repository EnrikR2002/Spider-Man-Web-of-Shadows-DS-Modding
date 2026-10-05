"""Paid aerial zip/kick fly-by and full training-target refill, exact CS5E."""
import argparse
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import combat_hud as h, wos_tool as w
from tools.combat_feedback import branch

ARM9_SHA256 = '761feb4416bb80eb815c3d0d287265ae31b39ed5578dffd86005cce4badc3306'
CODE_SHA256 = 'a2f168a4db19363ca25b37c7f91d63e378b5291426d2f878bf2a687a3f1589d9'
SOURCE_OFFSET = 0x1439A0 + 0x1B00
PATCHES = {
    0x728F0: (0xE5911000, branch(0x020728F0, 0x02150F20), 'paid_zip_kick_animation'),
    0x9515C: (0xEBFED051, branch(0x0209515C, 0x02151120) | 0x01000000, 'paid_zip_kick_hp_budget'),
    0x73B5C: (0xE3A02000, branch(0x02073B5C, 0x02151320), 'paid_kick_collision_steps'),
    0x49330: (0xD3A00028, 0xD5920048, 'training_refill_native_max_hp'),
    0x1449C0: (0xE3A02F5E, 0xE3A02F6E, 'own_hud_clear_extended_sling_state'),
}
TEXT_EDITS = {
    189: 'Sling Strike', 190: 'Sling Strike',
    191: 'In mid-air, press \ue602 near an enemy.\nZip in and kick through them.',
}


def code_bytes():
    raw = bytes.fromhex(Path(__file__).with_name('sling_strike.hex').read_text(encoding='utf-8'))
    if len(raw) != 0x600 or w.sha256(raw) != CODE_SHA256:
        raise ValueError('Sling Strike code differs from validated source')
    return raw


def apply_rom(rom):
    header = w.parse_header(rom)
    start, size = header['arm9_offset'], header['arm9_size']
    raw = rom[start:start + size]
    if w.sha256(raw) != h.ARM9_SHA256:
        raise ValueError('Sling Strike requires the exact compact HUD profile')
    changed = bytearray(rom)
    log = []
    for at, (old, new, field) in PATCHES.items():
        if struct.unpack_from('<I', raw, at)[0] != old:
            raise ValueError(f'Native Sling/QoL instruction differs: {field}')
        struct.pack_into('<I', changed, start + at, new)
        log.append({'arm9_offset': at, 'field': field, 'old': old, 'new': new})
    code = code_bytes()
    if any(raw[SOURCE_OFFSET:SOURCE_OFFSET + len(code)]):
        raise ValueError('Sling stubs overlap existing HUD extension code')
    changed[start + SOURCE_OFFSET:start + SOURCE_OFFSET + len(code)] = code
    log.append({'field': 'paid_zip_stubs', 'source_offset': SOURCE_OFFSET,
                'destination': 0x02150F20, 'size': len(code), 'sha256': CODE_SHA256})
    digest = w.sha256(changed[start:start + size])
    if digest != ARM9_SHA256:
        raise ValueError(f'Unexpected Sling Strike ARM9: {digest}')
    return bytes(changed), log


def generate(base_mods='mods', output='build/hud-sling'):
    import mod
    from tools import combat_readability as q
    root = w.safe_output(mod.project_path(output))
    if not root.is_relative_to((mod.ROOT / 'build').resolve()):
        raise ValueError('Candidates belong in build/')
    rom, glob, manifest = mod.load_clean()
    overlays = mod.overlay_files(mod.project_path(base_mods),
                                 [e['name'] for e in manifest['entries']])
    # Retain every accepted overlay. Required hashes guard the full composition.
    from tools import combat_profile as cp
    cp.load_recipe(mod.ROOT / 'reference/gameplay_profile.json', overlays)
    q.compose(glob, manifest, overlays, TEXT_EDITS)
    for name, data in overlays.items():
        w.atomic_write(root / 'mods' / name, data, (mod.DEFAULT_ROM,))
    w.write_json(root / 'gameplay_profile.json', {
        'schema_version': 1, 'profile': 'tasm-sling-strike',
        'required_overlays': {name: w.sha256(data) for name, data in overlays.items()}})
    result, _, log = mod.create_build(rom, glob, manifest, overlays,
                                     gameplay_profile='tasm-sling-strike')
    path = root / 'SlingStrike.nds'
    w.atomic_write(path, result, (mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'), log)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mods', default='mods')
    parser.add_argument('--out', default='build/hud-sling')
    args = parser.parse_args()
    try: print(generate(args.mods, args.out))
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
