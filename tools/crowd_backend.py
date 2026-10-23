"""Stage isolated crowd-backend RAM patches over the pinned published kit.

No ROM, player save, primary kit source or pinned hex is changed. Keystone is
the existing optional research dependency. Emulator comparisons use copied saves
and kit_lab's JIT-disabled patches. Concurrent player tests need explicit opt-in;
Windows workers can be pinned to one logical CPU at below-normal priority.
"""
from __future__ import annotations

import argparse
import ctypes as c
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import tasm_kit as kit, wos_tool as w

VARIANTS = ('area', 'sky-velocity', 'combined')
AREA_START = '  add r7,r8,#0x20\n  mov r3,#12\nsky_bowl:\n'
AREA_END = 'sky_reset:\n'
INCLUDE_AT = '// ---------------------------------------------------------------- Leapfrog\n'
AREA_CALL = '''  mov r0,r4
  mov r1,r5
  mov r2,#0x8000
  mov r3,#0x6000
  sub sp,sp,#8
  str r6,[sp]
  mov r7,#60
  str r7,[sp,#4]
  bl kit_area_hit
  add sp,sp,#8
  ldr r3,[r8,#0x374]
  add r3,r3,r1,lsl #8
  add r3,r3,r0
  str r3,[r8,#0x374]
  cmp r0,#0
  strne r2,[r8,#0x378]
'''
POSITION_DRIFT = '''  ldr r1,[r5,#0x7c]
  add r1,r1,r2
  str r1,[r5,#0x7c]
  b sky_out
'''
VELOCITY_DRIFT = '''  // The native physics/collision pass applies this update's drift.
  str r2,[r4,#0x18]
  b sky_out
'''


def candidate_source(source, variant):
    if variant == 'combined':
        return candidate_source(candidate_source(source, 'sky-velocity'), 'area')
    if variant == 'area':
        if source.count(AREA_START) != 1 or source.count(AREA_END) != 1 or source.count(INCLUDE_AT) != 1:
            raise ValueError('Published Skyjack/insert anchors changed')
        first, last = source.index(AREA_START), source.index(AREA_END)
        if first >= last:
            raise ValueError('Skyjack source boundaries changed')
        source = source[:first] + AREA_CALL + source[last:]
        helper = (ROOT / 'tools/crowd_hits.s').read_text(encoding='utf-8')
        return source.replace(INCLUDE_AT, helper + '\n' + INCLUDE_AT, 1)
    if variant == 'sky-velocity':
        if source.count(POSITION_DRIFT) != 1:
            raise ValueError('Published Skyjack drift anchor changed')
        return source.replace(POSITION_DRIFT, VELOCITY_DRIFT, 1)
    raise ValueError('Unknown isolated backend variant')


def assemble(source, base=kit.KIT_BASE):
    sys.path.insert(0, str(ROOT / 'work/research-libs'))
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, base)[0])
    from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors
    errors = literal_errors(code, source) + native_branch_errors(code, source, base=base) + self_branch_errors(code)
    body = [line.split('//')[0].strip() for line in source.splitlines()]
    body = [line for line in body if line]
    if not body or body[-1] != '.ltorg' or body.count('.ltorg') != 1:
        errors.append('one final literal pool required')
    if errors:
        raise ValueError('Invalid assembled kit: ' + '; '.join(errors[:3]))
    if len(code) > kit.ROUTE_OFFSET or len(code) % 4:
        raise ValueError('Candidate overlaps animation route table')
    return code


def refresh_validation(out, report):
    """Keep the staging record aligned with the separate retained test reports."""
    coverage = {}
    for name in ('area', 'sky', 'bowling'):
        path = out / f'{name}-coverage.json'
        if path.is_file():
            result = json.loads(path.read_text())
            coverage[name] = {'passed': result['passed'], 'passed_checks': sum(result['checks'].values()),
                              'total_checks': len(result['checks']), 'report': str(path)}
    report['coverage'] = coverage
    required = {'area': ('area',), 'sky-velocity': ('sky',), 'combined': ('sky', 'bowling')}[report['variant']]
    if report.get('qualification', {}).get('passed') and all(coverage.get(n, {}).get('passed') for n in required):
        report['status'] = 'staged and agent-qualified; unpublished; player feel/performance untested'
    w.write_json(out / 'stage.json', report)
    return report


def stage(variant, out=None):
    published_source = (ROOT / 'tools/tasm_kit.s').read_text(encoding='utf-8')
    published_code = kit.code_bytes()
    if assemble(published_source) != published_code:
        raise ValueError('Published source no longer reproduces pinned kit bytes')
    source = candidate_source(published_source, variant)
    code = assemble(source)
    digest = w.sha256(code)
    out = Path(out or ROOT / 'work/kit/crowd-backend' / f'{variant}-{digest[:8]}')
    w.safe_output(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'candidate.s').write_text(source, encoding='utf-8')
    (out / 'candidate.hex').write_text(code.hex() + '\n', encoding='ascii')
    expected = (published_code + bytes(kit.ROUTE_OFFSET - len(published_code)))[:len(code)]
    w.write_json(out / 'patch.json', [{'addr': kit.KIT_BASE, 'expect': expected.hex(), 'hex': code.hex()}])
    report = {'variant': variant, 'published_code_sha256': kit.CODE_SHA256,
              'candidate_code_sha256': digest, 'published_bytes': len(published_code),
              'candidate_bytes': len(code), 'route_table_offset': kit.ROUTE_OFFSET,
              'literal_and_native_branch_checks': 'passed',
              'status': 'assembled; emulator qualification pending',
              'scope': ('Composition after isolated checks; no player ROM/save/primary-source changes.'
                        if variant == 'combined' else 'One isolated RAM experiment; no ROM/save/primary-source changes.')}
    qualification = out / 'qualification.json'
    if qualification.is_file():
        previous = json.loads(qualification.read_text())
        report['qualification'] = {'passed': previous['passed'], 'passed_checks': sum(previous['checks'].values()),
                                   'total_checks': len(previous['checks']), 'report': str(qualification)}
        report['status'] = 'existing kit checks passed; targeted coverage pending' if previous['passed'] else 'qualification failed'
    refresh_validation(out, report)
    return out, report


def sky_metrics(dest):
    rows = [r for r in json.loads((Path(dest) / 'observations.json').read_text()) if r['f'] >= 0]
    evade = [r for r in rows if r['f'] >= 91 and r['st'] in (52, 53, 54, 55, 57)]
    return {'hp_loss_q12': 65536 - min(r['en'][0][0] for r in rows),
            'min_x': min(r['pos'][0] for r in rows), 'max_x': max(r['pos'][0] for r in rows),
            'cancel_frame': evade[0]['f'] if evade else None,
            'evade_moves_left': any(r['vel'][0] < 0 for r in evade),
            'sky_active_frames': sum(r['probe'][0] != 0 for r in rows),
            'sky_cleared_by_end': rows[-1]['probe'][0] == 0}


def summarize_sky(out):
    """Recalculate acceptance from retained observations without another emulator run."""
    path = out / 'sky-coverage.json'
    report = json.loads(path.read_text())
    cases = report['cases']
    for pair in cases.values():
        for entry in pair.values():
            entry.update(sky_metrics(entry['evidence']))
            entry.pop('sky_cleared_after_cancel', None)
    checks = {'open_control_hits_connect': cases['open']['control']['hp_loss_q12'] >= 3 * 4096,
              'open_air_hits_preserved': cases['open']['candidate']['hp_loss_q12'] >= 3 * 4096,
              'wall_bounds_respected': cases['wall']['candidate']['max_x'] <= 968577 + 64,
              'wall_control_uses_skyjack': cases['wall']['control'].get('armed', False) and cases['wall']['control']['sky_active_frames'] > 0,
              'wall_candidate_uses_skyjack': cases['wall']['candidate'].get('armed', False) and cases['wall']['candidate']['sky_active_frames'] > 0,
              'cancel_control_enters_evade': cases['cancel']['control']['cancel_frame'] is not None,
              'cancel_candidate_enters_evade': cases['cancel']['candidate']['cancel_frame'] is not None
                                               and cases['cancel']['candidate']['cancel_frame'] <= 96,
              'cancel_candidate_moves_left': cases['cancel']['candidate']['evade_moves_left'],
              'cancel_candidate_eventually_releases_sky': cases['cancel']['candidate']['sky_cleared_by_end']}
    # Air Reflex may preserve the Skyjack latch to resume a combo. The drift
    # correction must not override evade movement; the latch must clear by idle.
    report.update(checks=checks, passed=all(checks.values()))
    w.write_json(path, report)
    return report


def sky_coverage(rom, variant, out):
    from tools import kit_lab as lab
    cases = {}
    # Web Vault launches forward ~10 units. The established ~21-unit gap
    # connects the air chain; a 6-unit gap makes the unchanged control overshoot.
    for name, options in (('open', {}), ('cancel', {})):
        inputs = lab.rows_from(lab.INPUTS / 'vault.json')
        if name == 'cancel': inputs += [{'start': 91, 'end': 94, 'buttons': ['R', 'Left']}]
        pair = {}
        for mode in ('control', 'candidate'):
            print('Sky coverage', name, mode, flush=True)
            dest, _ = lab.run(rom, f'cb-sky-{variant}-{name}-{mode}', inputs, frames=220,
                                 bits=0xFEF00, probe=(kit.KIT_STATE + 0x330, 16),
                                 patch=str(out / 'patch.json') if mode == 'candidate' else None,
                                 caps=[80, 120, 219], **options)
            pair[mode] = {'evidence': str(dest), 'fixture': options}
        cases[name] = pair
    from tools import crowd_area_lab
    cases['wall'] = crowd_area_lab.run_wall(rom, out)
    report = {'cases': cases, 'source_rom_sha256': w.sha256(Path(rom).read_bytes()),
              'candidate_code_sha256': w.sha256(bytes.fromhex((out / 'candidate.hex').read_text())),
              'scope': 'Copied-save open/wall/interrupt comparisons; no player ROM/save writes or player feel claim.'}
    w.write_json(out / 'sky-coverage.json', report)
    return summarize_sky(out)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant', choices=VARIANTS)
    parser.add_argument('--qualify', action='store_true', help='Run copied-save kit checks; live player session needs the explicit concurrency flag')
    parser.add_argument('--rom', type=Path, default=ROOT / 'build/Spider-Man-WoS-modded.nds')
    parser.add_argument('--allow-player-session', action='store_true', help='Explicitly requested concurrent copied-save checks; no player save or ROM writes')
    parser.add_argument('--cpu-core', type=int, help='Windows: pin this process/children to one logical CPU, below-normal priority')
    parser.add_argument('--area-coverage', action='store_true', help='Real-actor area replay versus native replay, plus guarded invalid/immunity cases')
    parser.add_argument('--sky-coverage', action='store_true', help='Paired open/wall/cancel Skyjack checks')
    parser.add_argument('--bowling-coverage', action='store_true', help='Integrated native Skyjack caller versus the shared helper')
    parser.add_argument('--wall-coverage', action='store_true', help='Rerun the active wall fixture and resummarize retained Skyjack coverage')
    args = parser.parse_args(argv)
    profile = None
    if args.cpu_core is not None:
        if os.name != 'nt' or not 0 <= args.cpu_core < 64:
            raise ValueError('Background affinity requires a Windows logical CPU 0..63')
        kernel = c.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = c.c_void_p
        kernel.GetProcessAffinityMask.argtypes = [c.c_void_p, c.POINTER(c.c_size_t), c.POINTER(c.c_size_t)]
        kernel.SetProcessAffinityMask.argtypes = [c.c_void_p, c.c_size_t]
        kernel.SetPriorityClass.argtypes = [c.c_void_p, c.c_uint32]
        handle = kernel.GetCurrentProcess()
        allowed, system = c.c_size_t(), c.c_size_t()
        if not kernel.GetProcessAffinityMask(handle, c.byref(allowed), c.byref(system)):
            raise c.WinError(c.get_last_error())
        mask = 1 << args.cpu_core
        if not mask & allowed.value:
            raise ValueError('Requested logical CPU is outside process affinity')
        if not kernel.SetProcessAffinityMask(handle, mask) or not kernel.SetPriorityClass(handle, 0x4000):
            raise c.WinError(c.get_last_error())
        profile = {'logical_cpu': args.cpu_core, 'affinity_mask': mask, 'priority': 'below-normal'}
        print('Background profile:', profile, flush=True)
    out, report = stage(args.variant)
    report['background_profile'] = profile
    report['concurrent_player_session_allowed'] = args.allow_player_session
    w.write_json(out / 'stage.json', report)
    print(out / 'patch.json')
    print(f"{report['candidate_bytes']} bytes; literal/native branch checks passed; {report['status']}")
    if args.wall_coverage:
        if args.variant not in ('sky-velocity', 'combined') or args.qualify or args.area_coverage or args.sky_coverage or args.bowling_coverage:
            raise ValueError('Wall coverage is a separate velocity/composed experiment')
        from tools import crowd_area_lab, playtest
        if not args.allow_player_session: playtest.assert_closed()
        pair = crowd_area_lab.run_wall(args.rom, out)
        coverage = out / 'sky-coverage.json'
        if coverage.is_file():
            existing = json.loads(coverage.read_text())
            existing['cases']['wall'] = pair
            w.write_json(coverage, existing)
            result = summarize_sky(out)
            refresh_validation(out, report)
            print(f"Sky coverage: {sum(result['checks'].values())}/{len(result['checks'])}")
            return 0 if result['passed'] else 1
        return 0
    if args.bowling_coverage:
        if args.variant not in ('area', 'combined') or args.qualify or args.area_coverage or args.sky_coverage:
            raise ValueError('Bowling coverage is a separate area/composed experiment')
        from tools import crowd_area_lab, playtest
        if not args.allow_player_session: playtest.assert_closed()
        result = crowd_area_lab.run_bowling(args.rom, out)
        refresh_validation(out, report)
        print(f"Bowling coverage: {sum(result['checks'].values())}/{len(result['checks'])}")
        return 0 if result['passed'] else 1
    if args.sky_coverage:
        if args.variant not in ('sky-velocity', 'combined') or args.qualify or args.area_coverage:
            raise ValueError('Sky coverage is a separate velocity/composed experiment')
        from tools import playtest
        if not args.allow_player_session: playtest.assert_closed()
        result = sky_coverage(args.rom, args.variant, out)
        refresh_validation(out, report)
        print(f"Sky coverage: {sum(result['checks'].values())}/{len(result['checks'])}")
        return 0 if result['passed'] else 1
    if args.area_coverage:
        if args.variant != 'area' or args.qualify:
            raise ValueError('Area coverage is a separate area-only experiment')
        from tools import crowd_area_lab, playtest
        if not args.allow_player_session: playtest.assert_closed()
        result = crowd_area_lab.run_suite(args.rom, out)
        refresh_validation(out, report)
        print(f"Area coverage: {sum(result['checks'].values())}/{len(result['checks'])}")
        return 0 if result['passed'] else 1
    if args.qualify:
        from tools import kit_lab, playtest
        if not args.allow_player_session:
            playtest.assert_closed()
        result = kit_lab.qualify(args.rom, patch=out / 'patch.json',
                                 label_prefix=f"cb-{args.variant}-{report['candidate_code_sha256'][:8]}-",
                                 out=out / 'qualification.json',
                                 progress=lambda label: print('Tracing', label, flush=True))
        print(f"Qualification: {sum(result['checks'].values())}/{len(result['checks'])}")
        report['qualification'] = {'passed': result['passed'], 'passed_checks': sum(result['checks'].values()),
                                   'total_checks': len(result['checks']), 'report': str(out / 'qualification.json')}
        report['status'] = 'existing kit checks passed; targeted coverage pending' if result['passed'] else 'qualification failed'
        refresh_validation(out, report)
        return 0 if result['passed'] else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
