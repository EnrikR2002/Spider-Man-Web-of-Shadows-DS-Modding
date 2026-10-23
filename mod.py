#!/usr/bin/env python3
"""One-command, deterministic personal mod workflow for Spider-Man WoS DS CS5E."""
from __future__ import annotations
import argparse
import csv
import fnmatch
import json
import sys
from pathlib import Path
from tools import wos_tool as w

ROOT = Path(__file__).resolve().parent
DEFAULT_ROM = ROOT / 'original/Spider-Man - Web of Shadows (USA) (En,Fr).nds'
CLEAN_SHA256 = '61a6ed6e67fcce5cc63843fafeb0c0e6072bb750f552d5ff5d690cda02ea9203'


def project_path(value):
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_clean(path=DEFAULT_ROM):
    rom = Path(path).read_bytes()
    report = w.validate_rom(rom, target=True)
    if report['sha256'] != CLEAN_SHA256:
        raise ValueError('Clean ROM SHA256 differs from the validated baseline. Use your untouched CS5E dump; see README.md.')
    e = report['nitrofs'][0]
    glob = rom[e['start']:e['end']]
    manifest = w.glob_manifest(glob)
    with (ROOT / 'reference/glob_manifest.csv').open(encoding='utf-8', newline='') as stream:
        reference = list(csv.DictReader(stream))
    if len(reference) != len(manifest['entries']): raise ValueError('Reference manifest count differs from clean Glob')
    for a, b in zip(reference, manifest['entries']):
        if (int(a['index']), a['name'], int(a['size']), int(a['offset'], 16), a['magic_hex']) != (
                b['index'], b['name'], b['size'], b['offset'], b['magic_hex']):
            raise ValueError(f'Reference manifest differs from clean resource: {b["name"]}')
    return rom, glob, manifest


def overlay_files(directory: Path, names: list[str], *, added_names=()) -> dict[str, bytes]:
    """Only exact manifest names; no hidden ignored replacement files."""
    directory = directory.resolve()
    if not directory.is_dir(): raise ValueError(f'Overlay directory does not exist: {directory}')
    names=[*names,*added_names]
    mapping = {name.casefold(): name for name in names}
    out = {}
    for path in sorted(directory.rglob('*'), key=lambda p: p.relative_to(directory).as_posix()):
        if path.is_symlink() or not path.resolve().is_relative_to(directory):
            raise ValueError(f'Overlay symlink/path escape is unsupported: {path}')
        if path.is_dir(): continue
        name = w.safe_name(path.relative_to(directory).as_posix())
        # README is the only project-owned non-asset allowed here.
        if name == 'README.md': continue
        if name not in names:
            hint = mapping.get(name.casefold())
            raise ValueError(f'Unknown overlay asset: {name}' + (f'; use exact filename {hint}' if hint else ''))
        if name == 'GlobFiles.txt': raise ValueError('GlobFiles.txt is protected: adding/renaming resources is not supported')
        out[name] = path.read_bytes()
    return out


def create_build(rom: bytes, glob: bytes, manifest: dict, overlay: dict[str, bytes], *, rebound=False, gameplay_profile=None):
    from tools import oscorp_resources as expansion, release_info, tasm_kit
    entries = manifest['entries']
    names = [e['name'] for e in entries]
    extras=expansion.EXTRA_NAMES if gameplay_profile in (expansion.PROFILE, *release_info.PROFILES, tasm_kit.PROFILE) else ()
    if tasm_kit.uses_kit(gameplay_profile):
        extras=(*extras,*tasm_kit.EXTRA_NAMES)
        if len(entries)+len(expansion.EXTRA_NAMES)!=tasm_kit.PARENT_COUNT: raise ValueError('Kit routes expect the Rush additions first')
    if set(overlay) - set([*names,*extras]) or 'GlobFiles.txt' in overlay: raise ValueError('Invalid overlay mapping')
    if extras:expansion.validate_extra(overlay)
    blobs, replacements, identical = [], [], []
    for e in entries:
        old = glob[e['offset']:e['offset'] + e['size']]
        new = overlay.get(e['name'], old)
        blobs.append(new)
        if new != old:
            replacements.append({'index': e['index'], 'name': e['name'], 'old_size': len(old),
                                 'new_size': len(new), 'old_sha256': e['sha256'], 'new_sha256': w.sha256(new)})
        elif e['name'] in overlay: identical.append(e['name'])
    added=[]
    if extras:
        names,blobs=expansion.append_resources(names,blobs,{name:overlay[name] for name in extras})
        for i,name in enumerate(extras,start=len(entries)):
            added.append({'index':i,'name':name,'size':len(overlay[name]),'sha256':w.sha256(overlay[name])})
        table=manifest['name_table_index'];e=entries[table]
        replacements.append({'index':table,'name':e['name'],'old_size':e['size'],'new_size':len(blobs[table]),
                             'old_sha256':e['sha256'],'new_sha256':w.sha256(blobs[table]),'generated':True})
    new_glob = w.pack_glob(names, blobs)
    result = w.rebuild_rom(rom, {'Glob.bin': new_glob})
    from tools.combat_profile import apply_rom
    release = release_info.PROFILE_INFO.get(gameplay_profile, {})
    parent_profile = release.get('compose_parent', gameplay_profile)
    result, combat_edits = apply_rom(result, rebound if gameplay_profile is None else parent_profile)
    # Re-read every resource from the resulting ROM and compare exact bytes.
    report = w.validate_rom(result, target=True)
    ge = report['nitrofs'][0]
    checked = result[ge['start']:ge['end']]
    offsets, checked_names, _ = w.parse_glob(checked)
    if checked_names != names: raise ValueError('Build verification: changed filename table')
    for i, blob in enumerate(blobs):
        if checked[offsets[i]:offsets[i + 1]] != blob: raise ValueError(f'Build verification failed: {names[i]}')
    chapter = None
    crane = None
    if release_info.PROFILE_INFO.get(gameplay_profile, {}).get('chapter'):
        # Final verified stage: Midnight Line appends its rooms and grows the
        # kit autoload; it proves every other resource unchanged itself.
        from tools import midnight_chapter
        result, chapter = midnight_chapter.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = report['nitrofs'][0]
        new_glob = result[ge['start']:ge['end']]
    if release.get('crane'):
        from tools import crane_row
        result, crane = crane_row.apply_rom(result, version=release.get('crane_parent',release['version']),include_creatures=release.get('creatures',False))
        report = w.validate_rom(result, target=True)
        ge = report['nitrofs'][0]
        new_glob = result[ge['start']:ge['end']]
    midnight_rework = None
    if release.get('midnight_rework'):
        from tools import midnight_rework as rework
        result, midnight_rework = rework.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    chapter_renewal = None
    if release.get('chapter_renewal'):
        from tools import chapter_renewal as renewal
        result, chapter_renewal = renewal.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    creature_forge = None
    if release.get('creature_forge'):
        from tools import creature_forge as forge
        result, creature_forge = forge.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    creature_texture_fix = None
    if release.get('creature_texture_fix'):
        from tools import creature_texture_fix as texture_fix
        result, creature_texture_fix = texture_fix.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    chapter_spectacle = None
    if release.get('chapter_spectacle'):
        from tools import chapter_spectacle as spectacle
        result, chapter_spectacle = spectacle.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    midnight_rebuild = None
    if release.get('midnight_rebuild'):
        from tools import midnight_rebuild as rebuild
        result, midnight_rebuild = rebuild.apply_rom(result,full_motion=True,voices=True,rooms=True)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    midnight_encore = None
    if release.get('midnight_encore'):
        from tools import midnight_encore as encore
        result, midnight_encore = encore.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    midnight_voltage = None
    if release.get('midnight_voltage'):
        from tools import midnight_voltage as voltage
        result, midnight_voltage = voltage.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    midnight_finale = None
    if release.get('midnight_finale'):
        from tools import midnight_finale as finale
        result, midnight_finale = finale.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    midnight_reliability = None
    if release.get('midnight_reliability'):
        from tools import midnight_reliability as reliability
        result, midnight_reliability = reliability.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    chapter_finish = None
    if release.get('chapter_finish'):
        from tools import chapter_finish as finish
        result, chapter_finish = finish.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    spider2099 = None
    if release.get('spider2099'):
        from tools import spider2099 as future_suit
        result, spider2099 = future_suit.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    spider2099_polish = None
    if release.get('spider2099_polish'):
        from tools import spider2099_polish as future_polish
        result, spider2099_polish = future_polish.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    spider2099_movie = None
    if release.get('spider2099_movie'):
        from tools import spider2099_movie as future_movie
        result, spider2099_movie = future_movie.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    spider2099_enemy_texture = None
    if release.get('spider2099_enemy_texture'):
        from tools import spider2099_enemy_texture as enemy_texture
        result, spider2099_enemy_texture = enemy_texture.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    vortex_forge = None
    if release.get('vortex_forge'):
        from tools import vortex_forge as vortex
        result, vortex_forge = vortex.apply_rom(result)
        report = w.validate_rom(result, target=True)
        ge = next(e for e in report['nitrofs'] if e['name']=='Glob.bin')
        new_glob = result[ge['start']:ge['end']]
    log = {'schema_version': 1, 'clean_rom_sha256': w.sha256(rom), 'output_rom_sha256': w.sha256(result),
           'clean_glob_sha256': manifest['sha256'], 'output_glob_sha256': w.sha256(new_glob),
           'rom_size': len(result), 'used_rom_size': report['header']['used_rom_size'],
           'combat_data_edits': combat_edits,
           'header_crc16': report['header']['header_crc16'], 'nitrofs': report['nitrofs'],
           'replaced_assets': replacements, 'identical_overlays': identical,
           'added_assets':added, 'midnight_line': chapter, 'crane_row': crane, 'midnight_rework': midnight_rework,
           'chapter_renewal':chapter_renewal, 'creature_forge':creature_forge, 'creature_texture_fix':creature_texture_fix, 'chapter_spectacle':chapter_spectacle,
           'midnight_rebuild':midnight_rebuild, 'midnight_encore':midnight_encore, 'midnight_voltage':midnight_voltage, 'midnight_finale':midnight_finale, 'midnight_reliability':midnight_reliability, 'chapter_finish':chapter_finish, 'spider2099':spider2099, 'spider2099_polish':spider2099_polish, 'spider2099_movie':spider2099_movie, 'spider2099_enemy_texture':spider2099_enemy_texture,
           'vortex_forge':vortex_forge,
           'verified_resource_count': len(w.parse_glob(new_glob)[1]), 'unchanged_resource_count': len(names) - len(replacements)-len(added)}
    if gameplay_profile in release_info.PROFILES:
        release = release_info.PROFILE_INFO[gameplay_profile]
        log['release_version'] = release['version']
        log['release_date'] = release['date']
    return result, new_glob, log


def build_output(value):
    path = w.safe_output(project_path(value))
    if not path.is_relative_to((ROOT / 'build').resolve()): raise ValueError('Build outputs must be inside build/')
    if path.suffix.lower() != '.nds': raise ValueError('ROM output must have .nds extension')
    return path


def verify_roundtrip(rom, glob, manifest, extracted: Path):
    blobs = []
    if not extracted.is_dir(): raise ValueError('Extract first: python mod.py extract')
    for e in manifest['entries']:
        path = extracted / e['name']
        if not path.resolve().is_relative_to(extracted.resolve()): raise ValueError('Extraction path escape')
        data = path.read_bytes()
        if len(data) != e['size'] or w.sha256(data) != e['sha256']:
            raise ValueError(f'Extracted resource differs from clean ROM: {e["name"]}; put edits in mods/')
        blobs.append(data)
    rebuilt_glob = w.pack_glob([e['name'] for e in manifest['entries']], blobs)
    rebuilt_rom = w.rebuild_rom(rom, {'Glob.bin': rebuilt_glob})
    if glob != rebuilt_glob or rom != rebuilt_rom: raise ValueError('Unmodified round trip is not byte-identical')
    # Exercise the full extracted-directory/manifest repacker too.
    if w.repack_directory(extracted) != glob: raise ValueError('Directory repacker differs from clean Glob')
    report = {'schema_version': 1, 'clean_rom_sha256': w.sha256(rom), 'roundtrip_rom_sha256': w.sha256(rebuilt_rom),
              'glob_sha256': w.sha256(glob), 'glob_byte_identical': True, 'rom_byte_identical': True,
              'different_byte_count': 0, 'differing_ranges': [], 'validated_rom': w.validate_rom(rebuilt_rom, target=True),
              'resource_manifest': manifest}
    w.atomic_write(ROOT / 'build/roundtrip/Glob.bin', rebuilt_glob, (DEFAULT_ROM,))
    w.atomic_write(ROOT / 'build/roundtrip/Spider-Man-WoS-unmodified.nds', rebuilt_rom, (DEFAULT_ROM,))
    w.write_json(ROOT / 'reference/roundtrip_report.json', report)
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sp = ap.add_subparsers(dest='command', required=True)
    for command in ('build', 'extract', 'list', 'find', 'verify', 'experiment'):
        p = sp.add_parser(command)
        p.add_argument('--rom', default=str(DEFAULT_ROM), help='Untouched validated CS5E ROM')
        if command in ('build', 'verify'):
            p.add_argument('--mods', default='mods', help='Overlay directory, relative to project')
            p.add_argument('-o', '--out', default='build/Spider-Man-WoS-modded.nds')
            p.add_argument('--gameplay-profile', default='reference/gameplay_profile.json',
                           help='Known gameplay recipe, or original for an unpatched engine')
        if command == 'extract': p.add_argument('-o', '--out', default='work')
        if command in ('list', 'find'):
            if command == 'find': p.add_argument('query', help='Case-insensitive filename substring or glob pattern')
            p.add_argument('--ext', help='Extension filter, e.g. xbd')
            p.add_argument('--json', action='store_true')
        if command == 'verify':
            p.add_argument('--round-trip', action='store_true', help='Verify all extracted resources and byte-identical no-op rebuild')
            p.add_argument('--extracted', default='work/glob')
        if command == 'experiment': p.add_argument('action', choices=['green-suit', 'revert'])
    args = ap.parse_args(argv)
    try:
        rom_path = project_path(args.rom)
        rom, glob, manifest = load_clean(rom_path)
        if args.command == 'extract':
            out = project_path(args.out)
            # Keep work outside original, mods, and build. Preflight all conflicts.
            resolved = w.safe_output(out)
            if resolved in (ROOT.resolve(), (ROOT / 'mods').resolve(), (ROOT / 'build').resolve()):
                raise ValueError('Choose a dedicated extraction directory, e.g. work/')
            for e in manifest['entries']:
                path = out / 'glob' / e['name']
                if path.exists() and path.read_bytes() != glob[e['offset']:e['offset'] + e['size']]:
                    raise ValueError(f'Extraction would overwrite edits: {path}; use a new -o directory')
            w.extract_rom(rom, out / 'rom'); w.unpack_glob(glob, out / 'glob')
            print(f'Extracted 2 NitroFS files and {len(manifest["entries"])} resources to {out}')
        elif args.command in ('list', 'find'):
            query = getattr(args, 'query', '').casefold()
            ext = '.' + args.ext.lstrip('.').casefold() if args.ext else None
            entries = [e for e in manifest['entries'] if (not ext or Path(e['name']).suffix.casefold() == ext)
                       and (not query or query in e['name'].casefold() or fnmatch.fnmatchcase(e['name'].casefold(), query))]
            if args.json: print(json.dumps(entries, indent=2))
            else:
                for e in entries: print(f'{e["index"]:4d} {e["size"]:9d} {e["name"]}')
                print(f'{len(entries)} matching resources')
        elif args.command == 'verify' and args.round_trip:
            verify_roundtrip(rom, glob, manifest, project_path(args.extracted))
            print('PASS: 3,733 resource hashes, Glob and full ROM byte-identical; FAT/bounds/header CRC valid.')
        elif args.command in ('build', 'verify'):
            output = build_output(args.out)
            if output.resolve() == rom_path.resolve(): raise ValueError('Output would overwrite input ROM')
            from tools.combat_profile import load_recipe
            from tools import release_info
            profile = project_path(args.gameplay_profile)
            from tools import oscorp_resources as expansion, tasm_kit
            added_names=()
            if profile.exists():
                candidate_recipe=json.loads(profile.read_text(encoding='utf-8'))
                if isinstance(candidate_recipe,dict) and candidate_recipe.get('profile') in (expansion.PROFILE, *release_info.PROFILES, tasm_kit.PROFILE):
                    added_names=expansion.EXTRA_NAMES
                if isinstance(candidate_recipe,dict) and tasm_kit.uses_kit(candidate_recipe.get('profile')):
                    added_names=(*added_names,*tasm_kit.EXTRA_NAMES)
            overlay = overlay_files(project_path(args.mods), [e['name'] for e in manifest['entries']],added_names=added_names)
            if args.gameplay_profile == 'original':
                gameplay = False
            elif profile.exists():
                gameplay = load_recipe(profile, overlay)
            elif args.gameplay_profile == 'reference/gameplay_profile.json':
                gameplay = False
            else:
                raise ValueError('Gameplay profile does not exist')
            result, new_glob, log = create_build(rom, glob, manifest, overlay, gameplay_profile=gameplay)
            if args.command == 'build':
                log['overlay_directory'] = Path(args.mods).as_posix()
                log['output'] = Path(args.out).as_posix()
                # Validate everything before publishing output; replace atomically.
                w.atomic_write(output, result, (rom_path,))
                w.atomic_write(output.with_suffix('.Glob.bin'), new_glob, (rom_path,))
                w.write_json(output.with_suffix('.build.json'), log)
                print(f'Built {output}: {len(log["replaced_assets"])} changed assets; {len(result):,} bytes')
                print(f'SHA256 {log["output_rom_sha256"]}; log {output.with_suffix(".build.json")}')
            else:
                candidate = output.read_bytes()
                w.validate_rom(candidate, target=True)
                if candidate != result: raise ValueError('ROM does not match clean source + current overlay; rebuild it')
                print(f'PASS: ROM exactly matches current overlay; {log["verified_resource_count"]} resources verified; SHA256 {w.sha256(candidate)}')
        elif args.command == 'experiment':
            from tools import nitro_texture
            e = next(e for e in manifest['entries'] if e['name'] == 'spd.nsbtx')
            original = glob[e['offset']:e['offset'] + e['size']]
            changed, report = nitro_texture.green_suit(original)
            dest = ROOT / 'mods/spd.nsbtx'
            if args.action == 'green-suit':
                if dest.exists() and dest.read_bytes() != changed: raise ValueError('mods/spd.nsbtx already has a different edit; move it before this experiment')
                w.atomic_write(dest, changed, (rom_path,))
                w.write_json(ROOT / 'build/green-suit-experiment.json', report)
                nitro_texture.preview(original, ROOT / 'build/green-suit-before.png')
                nitro_texture.preview(changed, ROOT / 'build/green-suit-after.png')
                print(f'Created one reversible overlay: {dest}; now run python mod.py build')
            else:
                if dest.exists():
                    current = dest.read_bytes()
                    if current != changed: raise ValueError('Overlay differs from the experiment; refusing to remove your edit')
                    w.safe_output(dest).unlink()
                print('Experiment overlay removed; run python mod.py build to rebuild without it')
    except (OSError, ValueError, KeyError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
