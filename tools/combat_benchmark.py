"""Serial crowd-combat comparisons in disposable melonDS instances.

Host retro_run times are not DeSmuME FPS. Spidey update cadence is measured
separately; hit-stop, menus and scheduling can affect it. Original ROMs and
copied research saves are read only. No emulator save state is loaded.
"""
from __future__ import annotations

import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import statistics
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import crash_hunt, kit_lab, tasm_kit, wos_tool as w

MODES = {
    'interpreter': {b'melonds_jit_enable': b'disabled'},
    'jit': {b'melonds_jit_enable': b'enabled'},
    'jit-threaded': {b'melonds_jit_enable': b'enabled', b'melonds_threaded_renderer': b'enabled'},
}
SCENES = ('solo-idle', 'solo-combo', 'sparring-idle', 'sparring-combo', 'arena-combo')


def validate_tick_hook(rom):
    header = w.parse_header(rom)
    site = 0x02073B5C
    expected = tasm_kit.branch(site, tasm_kit.KIT_BASE + 0x14)
    if w.u32(rom, header['arm9_offset'] + site - 0x02000000) != expected:
        raise ValueError('Actor cadence requires the TASM per-update hook')


def cadence(ticks):
    """Observed actor updates per emulated 60 Hz frame, with unsigned wrap."""
    if len(ticks) < 2:
        raise ValueError('At least two tick samples required')
    deltas = [(b - a) & 0xFFFFFFFF for a, b in zip(ticks, ticks[1:])]
    if any(d > 16 for d in deltas):
        raise ValueError('Update counter reset (room transition or unsupported ROM)')
    gaps, gap = [], 0
    for d in deltas:
        if d:
            gaps.append(gap)
            gap = 0
        else:
            gap += 1
    gaps.append(gap)
    return {'updates': sum(deltas), 'emulated_frames': len(deltas),
            'updates_per_60_frames': 60 * sum(deltas) / len(deltas),
            'longest_no_update_frames': max(gaps),
            'no_update_frames': sum(d == 0 for d in deltas)}


def worker(args):
    scene, mode = args.worker.split(':')
    validate_tick_hook(args.rom.read_bytes())
    ticks, hud_ticks = [], []

    def sample_tick(rel, lib):
        if rel >= 0:
            ptr = lib.retro_get_memory_data(2)
            ticks.append(struct.unpack('<I', c.string_at(ptr + kit_lab.KIT_STATE - 0x02000000, 4))[0])
            hud_ticks.append(struct.unpack('<I', c.string_at(ptr + 0x0215242C - 0x02000000, 4))[0])

    inputs = crash_hunt.fight_script(args.seed, args.frames) if scene.endswith('combo') else []
    solo = scene.startswith('solo-')
    rom = kit_lab.solo_rom(args.rom) if solo else args.rom
    save = kit_lab.ARENA_SAVE if scene == 'arena-combo' else kit_lab.TRAINING_SAVE
    before = hashlib.sha256(save.read_bytes()).hexdigest()
    dest, rows = kit_lab._run(rom, args.label, inputs, frames=args.frames,
                             arena=scene == 'arena-combo', sparring=not solo,
                             tx=crash_hunt.LEDGE[0], ty=crash_hunt.LEDGE[1],
                             bits=0xFEF00, refill=scene == 'arena-combo',
                             extra_hook=sample_tick, timing=True, core_options=MODES[mode],
                             caps=[args.frames // 2, args.frames - 1])
    if hashlib.sha256(save.read_bytes()).hexdigest() != before:
        raise ValueError('Source save changed during benchmark')
    timing = json.loads((dest / 'frame-timing.json').read_text())
    boot = json.loads((dest / 'boot.json').read_text())
    useful = [r for r in rows if r['f'] >= 0]
    w.write_json(dest / 'kit-ticks.json', ticks)
    w.write_json(dest / 'hud-ticks.json', hud_ticks)
    result = {'scene': scene, 'mode': mode, 'seed': args.seed,
              'rom_sha256': boot['rom_sha256'], 'battery_sha256': before,
              'evidence': dest.relative_to(ROOT).as_posix(), 'cadence': cadence(ticks),
              'hud_cadence': cadence(hud_ticks),
              'timing': {k: v for k, v in timing.items() if k != 'frame_ms'},
              'live_enemy_count_median': statistics.median(sum(e[0] > 0 for e in r['en']) for r in useful),
              'player_states': sorted({r['st'] for r in useful if r['st'] is not None}),
              'player_actions': sorted({r['act'] for r in useful}),
              'core_options': boot['options']}
    w.write_json(dest / 'combat-benchmark.json', result)
    print('BENCHMARK_RESULT ' + json.dumps(result), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('rom', type=Path)
    ap.add_argument('--frames', type=int, default=1800)
    ap.add_argument('--rounds', type=int, default=2)
    ap.add_argument('--seed', type=int, default=600)
    ap.add_argument('--scenes', default=','.join(SCENES))
    ap.add_argument('--modes', default='interpreter,jit')
    ap.add_argument('--out', type=Path, default=ROOT / 'work/performance/combat.json')
    ap.add_argument('--worker', choices=[f'{s}:{m}' for s in SCENES for m in MODES])
    ap.add_argument('--label')
    args = ap.parse_args(argv)
    if not 60 <= args.frames <= 6000 or not 1 <= args.rounds <= 5:
        raise ValueError('Invalid bounded benchmark range')
    if args.worker:
        worker(args)
        return 0
    scenes, modes = args.scenes.split(','), args.modes.split(',')
    if any(s not in SCENES for s in scenes) or any(m not in MODES for m in modes):
        raise ValueError('Unknown scene or mode')
    w.safe_output(args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    original_rom = hashlib.sha256(args.rom.read_bytes()).hexdigest()
    runs = []
    for round_id in range(args.rounds):
        for scene in scenes:
            for mode in modes if round_id % 2 == 0 else modes[::-1]:
                label = f'perf-{scene}-{mode}-{args.seed + round_id}'
                log = args.out.parent / f'{label}.log'
                with log.open('w', encoding='utf-8') as stream:
                    subprocess.run([sys.executable, str(Path(__file__).resolve()), str(args.rom),
                                    '--frames', str(args.frames), '--seed', str(args.seed + round_id),
                                    '--worker', f'{scene}:{mode}', '--label', label],
                                   stdout=stream, stderr=subprocess.STDOUT, check=True, cwd=ROOT)
                marker = next(line for line in reversed(log.read_text().splitlines())
                              if line.startswith('BENCHMARK_RESULT '))
                result = json.loads(marker[len('BENCHMARK_RESULT '):])
                runs.append(result)
                w.write_json(args.out, {'source_rom_sha256': original_rom, 'runs': runs,
                    'limitation': 'melonDS host processing and actor cadence; not DeSmuME FPS. '
                                  'Live host workload and story spawn variation can affect comparisons.'})
                print(scene, mode, 'mean', round(result['timing']['mean_ms'], 3),
                      'p95', round(result['timing']['p95_ms'], 3),
                      'actor updates/60 frames', round(result['cadence']['updates_per_60_frames'], 2),
                      flush=True)
    if hashlib.sha256(args.rom.read_bytes()).hexdigest() != original_rom:
        raise ValueError('Source ROM changed during benchmark')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
