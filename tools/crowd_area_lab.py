"""Copied-save, disposable-RAM tests of the shared area replay with real enemies.

Invokes the compiled helper once after an actual native Spidey hit has supplied
its template. Compares actual enemy HP/reaction with native single-target replay.
Bad pointers/captures and immunity are synthetic RAM controls, never real saves.
"""
from __future__ import annotations

import argparse
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import crowd_backend as b, kit_lab as lab, tasm_kit as kit, wos_tool as w

HARNESS = kit.KIT_STATE + 0x400
CONFIG = HARNESS + 0x200
FAKE = HARNESS + 0x300
CASES = ('native', 'area', 'excluded', 'out-of-range', 'stale-template',
         'missing-template', 'wrong-attacker', 'stale-slot', 'bad-actor', 'bad-motion',
         'immune', 'negative-reach', 'multi', 'native-immune')
MODES = {'native': 1, 'stale-template': 2, 'missing-template': 3,
         'wrong-attacker': 4, 'stale-slot': 5, 'bad-actor': 6, 'bad-motion': 7, 'immune': 8, 'native-immune': 9}


def bowling_worker(rom, out, mode):
    """Exercise the real Skyjack landing caller, with two copied-RAM bystanders."""
    result = {'mode': mode, 'done': False}
    patched = mode == 'candidate'
    digest = w.sha256(bytes.fromhex((out / 'candidate.hex').read_text()))[:8]

    def hook(rel, lib):
        if rel < 0 or result['done']: return
        ptr, ram = lab.ram_of(lib)
        offset = kit.KIT_STATE - kit.BASE
        active, primary, spike = struct.unpack_from('<3i', ram, offset + 0x330)
        telemetry = struct.unpack_from('<I', ram, offset + 0x374)[0]
        if result.get('armed'):
            if telemetry != result['telemetry_before']:
                result.update(done=True, impact_frame=rel, telemetry_after=telemetry,
                              hp_after={str(actor): struct.unpack_from('<i', ram, actor - kit.BASE + 0x44)[0]
                                        for actor in result['victims']})
                result['reactions_after'] = {str(e['actor']): [e['state'], e['action']]
                                            for e in lab.enemies(ram) if e['actor'] in result['victims']}
                return
            # Hold just the bystanders idle until impact so their attack AI
            # cannot confound the comparison. Primary/native flight stays intact.
            for e in lab.enemies(ram):
                if e['actor'] in result['victims']:
                    c.memmove(ptr + e['controller'] - kit.BASE + 0x14, struct.pack('<I', 0), 4)
            return
        if not active or spike != -1: return
        enemies = lab.enemies(ram)
        target = next(e for e in enemies if e['actor'] == primary)
        player = lab.p.sample(ram)
        others = [e for e in enemies if e['actor'] != primary]
        if len(others) != 3: raise ValueError('Bowling needs three live bystanders')
        victims = others[:2]
        for dx, e in zip((-3 * 4096, 3 * 4096, 50 * 4096), others):
            motion = struct.unpack_from('<I', ram, e['actor'] - kit.BASE + 0x30)[0] - kit.BASE
            lab.teleport(ptr, ram, motion, target['position'][0] + dx, 20607)
            c.memmove(ptr + e['actor'] - kit.BASE + 0x18, bytes(8), 8)
        result.update(armed=True, armed_frame=rel, primary_actor=primary,
                      player_actor=player['actor_address'], victims=[e['actor'] for e in victims],
                      victim_indices=[enemies.index(e) for e in victims],
                      telemetry_before=telemetry,
                      hp_before={str(e['actor']): e['hp'] for e in victims})

    dest, _ = lab._run(rom, f'cb-bowling-{digest}-{mode}', lab.rows_from(lab.INPUTS / 'vault.json'),
                       frames=220, bits=0xFEF00, sparring=True, start_x=120 * 4096,
                       place=((21 * 4096, 205), (60 * 4096, 205), (-60 * 4096, 205), (90 * 4096, 205)),
                       patch=out / 'patch.json' if patched else None, extra_hook=hook,
                       caps=(120, 160, 219))
    result['evidence'] = str(dest)
    w.write_json(out / f'bowling-{mode}.json', result)
    if not result['done']: raise ValueError('Native Skyjack bowling fixture did not reach impact')


def run_bowling(rom, out):
    for mode in ('control', 'candidate'):
        print('Integrated Skyjack bowling', mode, flush=True)
        with (out / f'bowling-{mode}.log').open('w', encoding='utf-8') as stream:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '--rom', str(rom),
                            '--out', str(out), '--case', 'bowling-' + mode],
                           stdout=stream, stderr=subprocess.STDOUT, check=True, cwd=ROOT)
    return summarize_bowling(out)


def summarize_bowling(out):
    pair = {m: json.loads((out / f'bowling-{m}.json').read_text()) for m in ('control', 'candidate')}
    for run in pair.values():
        run['hp_losses_q12'] = sorted(hp - run['hp_after'][actor] for actor, hp in run['hp_before'].items())
        run['native_results_and_attempts'] = run['telemetry_after'] - run['telemetry_before']
        rows = json.loads((Path(run['evidence']) / 'observations.json').read_text())
        indices = run.get('victim_indices')
        if indices is None:
            # Early reports lacked actor indices. This fixture has three untouched
            # 8-HP bystanders in address order; its first two are the victims.
            armed = next(r for r in rows if r['f'] == run['armed_frame'])
            bystanders = [i for i, e in enumerate(armed['en']) if e[0] == 32768]
            if len(bystanders) != 3 or set(run['hp_before'].values()) != {32768}:
                raise ValueError('Cannot reconstruct early bowling fixture actor indices')
            indices = bystanders[:2]
        reaction = next(r for r in rows if r['f'] == run['impact_frame'] + 4)
        run['reaction_after_native_commit'] = [reaction['en'][i][2:] for i in indices]
    control, candidate = pair['control'], pair['candidate']
    checks = {'control_bowls_two_targets': control['native_results_and_attempts'] == 2 + 8 * 256,
              'candidate_bowls_two_targets': candidate['native_results_and_attempts'] == 2 + 8 * 256,
              'control_damages_both': len(control['hp_losses_q12']) == 2 and min(control['hp_losses_q12']) > 0,
              'candidate_matches_native_hp': candidate['hp_losses_q12'] == control['hp_losses_q12'],
              'control_knocks_down_both': all(r[0] == 41 for r in control['reaction_after_native_commit']),
              'candidate_matches_native_reactions': sorted(candidate['reaction_after_native_commit']) ==
                                                    sorted(control['reaction_after_native_commit'])}
    report = {'checks': checks, 'passed': all(checks.values()), 'runs': pair,
              'scope': 'Real Skyjack caller with copied-RAM bystanders; not player feel/performance acceptance.'}
    w.write_json(out / 'bowling-coverage.json', report)
    return report


def wall_worker(rom, out, mode):
    """Move an established, native Skyjack juggle beside the right wall in RAM."""
    result = {'mode': mode, 'armed': False}

    def hook(rel, lib):
        if rel != 60: return
        ptr, ram = lab.ram_of(lib)
        player = lab.p.sample(ram)
        active, primary = struct.unpack_from('<2I', ram, kit.KIT_STATE - kit.BASE + 0x330)
        if not active or not player['controller'] or player['controller']['state_id_candidate'] not in (19, 51):
            raise ValueError('Wall fixture requires an established native Skyjack juggle')
        target = next(e for e in lab.enemies(ram) if e['actor'] == primary)
        target_motion = struct.unpack_from('<I', ram, primary - kit.BASE + 0x30)[0] - kit.BASE
        lab.teleport(ptr, ram, player['motion_address'] - kit.BASE,
                     236 * 4096, player['position_q12_candidate'][1])
        lab.teleport(ptr, ram, target_motion, 235 * 4096, target['position'][1])
        result.update(armed=True, armed_frame=rel, primary_actor=primary)

    digest = w.sha256(bytes.fromhex((out / 'candidate.hex').read_text()))[:8]
    dest, _ = lab._run(lab.solo_rom(rom), f'cb-wall-{digest}-{mode}',
                       lab.rows_from(lab.INPUTS / 'vault.json'), frames=220, bits=0xFEF00,
                       patch=out / 'patch.json' if mode == 'candidate' else None,
                       probe=(kit.KIT_STATE + 0x330, 16), extra_hook=hook, caps=(80, 120, 219))
    result['evidence'] = str(dest)
    w.write_json(out / f'wall-{mode}.json', result)
    if not result['armed']: raise ValueError('Wall fixture never armed')


def run_wall(rom, out):
    for mode in ('control', 'candidate'):
        print('Active Skyjack beside wall', mode, flush=True)
        with (out / f'wall-{mode}.log').open('w', encoding='utf-8') as stream:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '--rom', str(rom),
                            '--out', str(out), '--case', 'wall-' + mode],
                           stdout=stream, stderr=subprocess.STDOUT, check=True, cwd=ROOT)
    return {m: json.loads((out / f'wall-{m}.json').read_text()) for m in ('control', 'candidate')}


def unique_signature(code, words):
    pattern = struct.pack('<' + 'I' * len(words), *words)
    if code.count(pattern) != 1:
        raise ValueError('Compiled helper signature changed or is ambiguous')
    return kit.KIT_BASE + code.index(pattern)


def invocation_patch(out):
    code = bytes.fromhex((out / 'candidate.hex').read_text())
    area = unique_signature(code, (0xE92D4FF0, 0xE24DD014))
    replay = unique_signature(code, (0xE92D4010, 0xE24DD010, 0xE1A04000))
    word = struct.unpack_from('<I', code, 0x14)[0]
    if word & 0xFF000000 != 0xEA000000:
        raise ValueError('Kit per-update entry is not the expected ARM branch')
    delta = word & 0xFFFFFF
    if delta & 0x800000: delta -= 0x1000000
    update = kit.KIT_BASE + 0x14 + 8 + 4 * delta
    source = f'''  b lab_update
lab_update:
  push {{r0-r12,lr}}
  mrs r12,cpsr
  push {{r11,r12}}
  ldr r11,lit_config
  ldr r0,[r11]
  cmp r0,#1
  bne lab_out
  ldr r0,[r4]
  ldr r1,lit_spidey
  cmp r0,r1
  bne lab_out
  ldr r10,lit_kit
  ldr r8,[r11,#40]
  cmp r8,#2
  ldreq r0,[r10]
  subeq r0,r0,#100
  streq r0,[r10,#0x36c]
  cmp r8,#3
  moveq r0,#0
  streq r0,[r10,#0x370]
  cmp r8,#4
  ldreq r0,[r11,#48]
  streq r0,[r10,#0x370]
  cmp r8,#5
  ldreq r1,[r11,#44]
  ldreq r0,[r10]
  subeq r0,r0,#2
  streq r0,[r1,#12]
  cmp r8,#6
  ldreq r1,[r11,#44]
  moveq r0,#0x60000
  streq r0,[r1]
  cmp r8,#7
  ldreq r1,[r11,#44]
  ldreq r0,lit_fake
  streq r0,[r1]
  cmp r8,#8
  cmpne r8,#9
  bne lab_dispatch
  ldr r0,[r11,#48]
  ldr r0,[r0,#0x30]
  ldr r0,[r0,#0x1f8]
  mov r1,#51
  str r1,[r0,#0x14]
  mov r1,#0
  str r1,[r0,#8]
lab_dispatch:
  cmp r8,#1
  cmpne r8,#9
  bne lab_area
  ldr r0,[r11,#48]
  bl 0x{replay:08x}
  mov r1,r0
  mov r0,#1
  ldr r2,[r11,#48]
  b lab_save
lab_area:
  sub sp,sp,#8
  ldr r0,[r11,#4]
  str r0,[sp]
  ldr r0,[r11,#24]
  str r0,[sp,#4]
  ldr r0,[r11,#8]
  ldr r1,[r11,#12]
  ldr r2,[r11,#16]
  ldr r3,[r11,#20]
  bl 0x{area:08x}
  add sp,sp,#8
lab_save:
  str r0,[r11,#28]
  str r1,[r11,#32]
  str r2,[r11,#36]
  mov r0,#2
  str r0,[r11]
lab_out:
  pop {{r11,r12}}
  msr cpsr_f,r12
  pop {{r0-r12,lr}}
  b 0x{update:08x}
lit_config: .word 0x{CONFIG:08x}
lit_kit: .word 0x{kit.KIT_STATE:08x}
lit_spidey: .word 0x0212e3f0
lit_fake: .word 0x{FAKE:08x}
  .ltorg
'''
    harness = b.assemble(source, base=HARNESS)
    if len(harness) > CONFIG - HARNESS:
        raise ValueError('Invocation harness overlaps fixture configuration')
    patch = json.loads((out / 'patch.json').read_text())
    patch.extend([{'addr': HARNESS, 'expect': bytes(len(harness)).hex(), 'hex': harness.hex()},
                  {'addr': CONFIG, 'expect': bytes(64).hex(), 'hex': bytes(64).hex()},
                  {'addr': kit.KIT_BASE + 0x14, 'expect': code[0x14:0x18].hex(),
                   'hex': struct.pack('<I', kit.branch(kit.KIT_BASE + 0x14, HARNESS)).hex()}])
    path = out / 'invocation-patch.json'
    (out / 'invocation.s').write_text(source)
    w.write_json(path, patch)
    return path


def worker(rom, out, case):
    patch = invocation_patch(out)
    result = {'case': case, 'done': False}

    def hook(rel, lib):
        if rel < 0: return
        ptr, ram = lab.ram_of(lib)
        flag = struct.unpack_from('<I', ram, CONFIG - kit.BASE)[0]
        if flag == 2 and not result['done']:
            attempts, codes, last = struct.unpack_from('<3I', ram, CONFIG - kit.BASE + 28)
            hp = struct.unpack_from('<i', ram, result['target_actor'] - kit.BASE + 0x44)[0]
            target = next(e for e in lab.enemies(ram) if e['actor'] == result['target_actor'])
            result.update(done=True, dispatch_frame=rel, attempts=attempts, native_result_sum=codes,
                          last_actor=last, hp_after_q12=hp, hp_loss_q12=result['hp_before_q12'] - hp,
                          target_state_after=target['state'], target_action_after=target['action'])
            result['hp_after_by_actor'] = {str(actor): struct.unpack_from('<i', ram, actor - kit.BASE + 0x44)[0]
                                           for actor in result['target_actors']}
        if result.get('armed') or result['done']: return
        captured, attacker, kind, strength = (struct.unpack_from('<I', ram, kit.KIT_STATE - kit.BASE + off)[0]
                                             for off in (0x36C, 0x370, 0x380, 0x384))
        if not captured or not attacker: return
        player = lab.p.sample(ram)
        if attacker != player['actor_address']: return
        live = [e for e in lab.enemies(ram) if e['hp'] > 0]
        if len(live) != 4: raise ValueError('Fixture must retain four live training enemies')
        target = max(live, key=lambda e: e['position'][0])
        primary = min(live, key=lambda e: abs(e['position'][0] - player['position_q12_candidate'][0]))
        if target['actor'] == primary['actor']:
            raise ValueError('Target fixture is not separated from native contact')
        slots = [kit.KIT_STATE + 0x20 + 16 * i for i in range(12)
                 if struct.unpack_from('<I', ram, kit.KIT_STATE - kit.BASE + 0x20 + 16 * i)[0] == target['actor']]
        if len(slots) != 1: raise ValueError('Fixture target must occupy one registry slot')
        x, y = target['position']
        targets = [target]
        if case == 'multi':
            targets = sorted(live, key=lambda e: e['position'][0])[-2:]
            if any(e['actor'] == primary['actor'] for e in targets):
                raise ValueError('Multiple targets must be separated from native contact')
            x = sum(e['position'][0] for e in targets) // 2
        if case == 'out-of-range': x += 20 * 4096
        excluded = target['actor'] if case == 'excluded' else primary['actor']
        reach = -1 if case == 'negative-reach' else 4 * 4096
        if case == 'multi': reach = 20 * 4096
        values = (1, excluded, x, y, reach, 6 * 4096, 60, 0, 0, 0,
                  MODES.get(case, 0), slots[0], target['actor'], 0, 0, 0)
        c.memmove(ptr + CONFIG - kit.BASE, struct.pack('<16I', *(v & 0xFFFFFFFF for v in values)), 64)
        fake = bytearray(64)
        struct.pack_into('<I', fake, 0, lab.ENEMY_VTABLE)
        struct.pack_into('<I', fake, 0x30, 0x60000)
        c.memmove(ptr + FAKE - kit.BASE, bytes(fake), len(fake))
        result.update(armed=True, armed_frame=rel, target_actor=target['actor'],
                      primary_actor=primary['actor'], hp_before_q12=target['hp'],
                      target_state_before=target['state'], attack_kind=kind,
                      attack_strength_q12=strength, capture_tick=captured,
                      target_actors=[e['actor'] for e in targets],
                      hp_before_by_actor={str(e['actor']): e['hp'] for e in targets})

    dest, rows = lab._run(rom, 'cb-area-coverage-' + case, [{'start': 20, 'end': 24, 'buttons': ['Y']}],
                         frames=160, patch=patch, sparring=True, start_x=135 * 4096,
                         place=((6 * 4096, 205), (40 * 4096, 205), (-50 * 4096, 205), (70 * 4096, 205)),
                         extra_hook=hook, caps=(60, 120, 159))
    result['evidence'] = str(dest)
    w.write_json(out / f'coverage-{case}.json', result)
    if not result['done']: raise ValueError('Native capture/invocation fixture did not complete')
    print('AREA_RESULT ' + json.dumps(result), flush=True)


def run_suite(rom, out):
    for case in CASES:
        print('Area coverage', case, flush=True)
        log = out / f'coverage-{case}.log'
        with log.open('w', encoding='utf-8') as stream:
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '--rom', str(rom),
                            '--out', str(out), '--case', case], stdout=stream,
                           stderr=subprocess.STDOUT, check=True, cwd=ROOT)
    return summarize(out)


def summarize(out):
    runs = [json.loads((out / f'coverage-{case}.json').read_text()) for case in CASES]
    by_case = {r['case']: r for r in runs}
    native, area = by_case['native'], by_case['area']
    checks = {'all_fixtures_completed': all(r['done'] for r in runs),
              'native_replay_takes_hit': native['native_result_sum'] == 4 and native['hp_loss_q12'] > 0,
              'area_matches_native_hp_loss': area['hp_loss_q12'] == native['hp_loss_q12'] > 0,
              'area_matches_native_reaction': (area['target_state_after'], area['target_action_after']) ==
                                             (native['target_state_after'], native['target_action_after']),
              'area_dispatches_one_target': area['attempts'] == 1 and area['native_result_sum'] == 4,
              'templates_match': (area['attack_kind'], area['attack_strength_q12']) ==
                                 (native['attack_kind'], native['attack_strength_q12']),
              'native_immunity_control': by_case['native-immune']['native_result_sum'] == 1 and by_case['native-immune']['hp_loss_q12'] == 0,
              'immunity_respected': by_case['immune']['native_result_sum'] == by_case['native-immune']['native_result_sum'] == 1
                                   and by_case['immune']['hp_loss_q12'] == 0}
    for case in ('excluded', 'out-of-range', 'stale-template', 'missing-template', 'wrong-attacker', 'stale-slot', 'negative-reach'):
        checks[case + '_skipped'] = by_case[case]['attempts'] == 0 and by_case[case]['hp_loss_q12'] == 0
    for case in ('bad-actor', 'bad-motion'):
        checks[case + '_rejected'] = by_case[case]['native_result_sum'] == 0 and by_case[case]['hp_loss_q12'] == 0
    multi = by_case['multi']
    checks['multi_dispatches_two_targets'] = multi['attempts'] == 2 and multi['native_result_sum'] == 8
    checks['multi_matches_native_loss_per_target'] = all(
        before - multi['hp_after_by_actor'][actor] == native['hp_loss_q12'] > 0
        for actor, before in multi['hp_before_by_actor'].items())
    report = {'checks': checks, 'passed': all(checks.values()), 'runs': runs,
              'limitation': 'Copied-save API fixtures; not a player feel/performance test or future contact deduplication proof.'}
    w.write_json(out / 'area-coverage.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=CASES + ('bowling-control', 'bowling-candidate', 'wall-control', 'wall-candidate'), required=True)
    args = parser.parse_args()
    if args.case.startswith('bowling-'):
        bowling_worker(args.rom, args.out, args.case.removeprefix('bowling-'))
    elif args.case.startswith('wall-'):
        wall_worker(args.rom, args.out, args.case.removeprefix('wall-'))
    else:
        worker(args.rom, args.out, args.case)


if __name__ == '__main__':
    main()
