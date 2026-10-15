#!/usr/bin/env python3
"""Freeze/crash hunt: random crowd fights in the story arena with crash snapshots.

  run SEED [--rom R --frames N --tx X --ty Y]   one fight (child process friendly)
  batch FIRST LAST [--jobs J ...]               many seeds in parallel; one line per event
  regs STATE.bin [--ram RAM.bin]                 ARM9 registers, pre-exception SP/LR, DTCM stack

A fight presses random Y strings, R taps, held R (Enhanced Dodge chains), A/B/X,
held A then Y (Dragnet and its yank), Y, Y, pause, Y... (Vortex) and Left/Right;
enemies and Spidey are refilled to max HP so the crowd never ends. Odd seeds hold
the combo meter at tier 5 (Overclock).
When the kit tick (one per Spidey update) stops for 60 frames outside the tutorial
popup (Spidey state 75), the emulator state and main RAM are saved under
work/crash/. A data abort shows as CPU mode 0x17 with PC 0xFFFF0108 (BIOS vector);
the halted idle wait at 0x020FFA30 is a menu/pause, not a crash. Everything uses
copied saves and disposable emulator RAM (tools/kit_lab.py). TECHNICAL "Freeze
root cause and crash hunting" has the v0.4.0 findings.
"""
from __future__ import annotations
import argparse
import ctypes as c
import json
import random
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'work/crash'
KIT_TICK = 0x02154C20
LEDGE = (55000, 376880)        # sewer ledge where the v0.4.0 freezes reproduced most
DEFAULT_ROM = ROOT / 'build/Spider-Man-WoS-modded.nds'


def fight_script(seed, frames):
    """Deterministic random crowd-fight inputs ({start,end,buttons} rows)."""
    rng = random.Random(seed)
    rows, f = [], 10
    while f < frames - 20:
        kind = rng.random()
        d = rng.choice([[], [], ['Left'], ['Right']])
        if kind < 0.45:      # Y strings
            for _ in range(rng.randint(2, 8)):
                rows.append({'start': f, 'end': f + 3, 'buttons': ['Y'] + d}); f += rng.randint(4, 9)
        elif kind < 0.75:    # R taps, sometimes with Y
            for _ in range(rng.randint(1, 4)):
                rows.append({'start': f, 'end': f + 3, 'buttons': ['R'] + (['Y'] if rng.random() < 0.3 else []) + d})
                f += rng.randint(3, 8)
        elif kind < 0.9:     # held R (Enhanced Dodge chain) with Y presses inside
            n = rng.randint(20, 90)
            rows.append({'start': f, 'end': f + n, 'buttons': ['R'] + d})
            for k in range(f + 4, f + n, rng.randint(5, 12)):
                rows.append({'start': k, 'end': k + 2, 'buttons': ['Y']})
            f += n + rng.randint(1, 6)
        elif kind < 0.94:    # jump / web / object
            rows.append({'start': f, 'end': f + 4, 'buttons': [rng.choice(['A', 'B', 'X'])] + d})
            f += rng.randint(6, 14)
        elif kind < 0.97:    # Dragnet: A kept held, then the yank or something else, then Vortex presses
            n = rng.randint(34, 70)
            rows.append({'start': f, 'end': f + n, 'buttons': ['A'] + d}); f += n + rng.randint(2, 20)
            rows.append({'start': f, 'end': f + 3, 'buttons': [rng.choice(['Y', 'Y', 'Y', 'A', 'R', 'B'])]}); f += rng.randint(16, 26)
            for _ in range(rng.randint(0, 4)):
                rows.append({'start': f, 'end': f + 3, 'buttons': ['Y']}); f += rng.randint(14, 30)
        else:                # Vortex: pause or buffered Down+Y; four web steps
            direct = rng.choice((False, True))
            gaps = (16, rng.randint(16,26) if direct else rng.randint(40,56),
                    rng.randint(20,30), rng.randint(20,30), rng.randint(20,30), rng.randint(20,40))
            for index,gap in enumerate(gaps):
                rows.append({'start': f, 'end': f + 3, 'buttons': ['Y','Down'] if direct and index==2 else ['Y']})
                f += gap
    return rows


def serialize(lib):
    lib.retro_serialize_size.restype = c.c_size_t
    lib.retro_serialize.argtypes = [c.c_void_p, c.c_size_t]
    lib.retro_serialize.restype = c.c_bool
    n = lib.retro_serialize_size()
    buf = c.create_string_buffer(n)
    if not lib.retro_serialize(buf, n): raise ValueError('Emulator state serialization failed')
    return buf.raw


def run(seed, rom, frames=4000, at=LEDGE):
    """One fight; prints 'STALL rel state file' lines and 'DONE seed'."""
    from tools import kit_lab, player_trace as p
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = OUT / f'inputs_{seed}.json'
    inputs.write_text(json.dumps(fight_script(seed, frames)))
    st = {'last': None, 'since': 0, 'done': False}

    def hook(rel, lib):
        if rel < 0: return
        ptr = lib.retro_get_memory_data(2)
        tick = struct.unpack('<I', c.string_at(ptr + KIT_TICK - p.BASE, 4))[0]
        if tick != st['last']:
            st.update(last=tick, since=rel, done=False)
            return
        if rel - st['since'] != 60 or st['done']: return
        st['done'] = True
        ram = c.string_at(ptr, 4 * 1024 * 1024)
        try:
            o = p.sample(ram)
            state = o['controller']['state_id_candidate'] if o['controller'] else None
        except ValueError:
            state = None
        if state == 75: return              # tutorial popup pause
        name = OUT / f'stall_{seed}_{st["since"]}'
        name.with_suffix('.state').write_bytes(serialize(lib))
        name.with_suffix('.ram').write_bytes(ram)
        print('STALL', st['since'], state, name.with_suffix('.state'), flush=True)

    kit_lab._run(str(rom), f'crash_{seed}', str(inputs), frames=frames, bits=0xFEF00, bits2=0x7FC00, arena=True,
                 tx=at[0], ty=at[1], refill=True, extra_hook=hook, caps=[frames - 1],
                 tier=5 if seed % 2 else None)   # bits2: every shop row of the second block; odd seeds: Overclock's tier
    print('DONE', seed, flush=True)


def batch(first, last, jobs, rom, frames, at):
    """Parallel fights in child processes (the core prints thousands of log lines)."""
    from concurrent.futures import ThreadPoolExecutor

    def one(seed):
        cmd = [sys.executable, str(Path(__file__).resolve()), 'run', str(seed), '--rom', str(rom),
               '--frames', str(frames), '--tx', str(at[0]), '--ty', str(at[1])]
        done = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              text=True, errors='replace')
        lines = [x for x in done.stdout.splitlines() if x.startswith(('STALL', 'DONE'))]
        return seed, lines or [f'ERROR exit {done.returncode}']
    events = 0
    with ThreadPoolExecutor(jobs) as ex:
        for seed, lines in ex.map(one, range(first, last + 1)):
            for line in lines:
                if not line.startswith('DONE'): events += 1
                print(seed, line, flush=True)
    return events


def arm9_registers(state):
    """melonDS savestate 'ARM9' section: halted, R0-R15, CPSR and banked SVC/ABT/IRQ (SP, LR, SPSR)."""
    i = state.find(b'ARM9')
    if i < 0: raise ValueError('No ARM9 section in the emulator state')
    w = struct.unpack_from('<39I', state, i + 4)
    return {'halted': w[4], 'r': list(w[5:21]), 'cpsr': w[21], 'fiq': list(w[22:30]),
            'svc': list(w[30:33]), 'abt': list(w[33:36]), 'irq': list(w[36:39])}


def dtcm(state):
    """The 16 KiB ARM9 DTCM (0x027E0000) is the tail of the 'CP15' section."""
    i = state.find(b'CP15')
    if i < 0: raise ValueError('No CP15 section in the emulator state')
    return state[i:i + struct.unpack_from('<I', state, i + 4)[0]][-0x4000:]


def describe(state, ram=None):
    regs = arm9_registers(state)
    mode = regs['cpsr'] & 0x1F
    lines = [f"halted {regs['halted']} cpsr {regs['cpsr']:#x} pc {regs['r'][15]:#010x} lr {regs['r'][14]:#010x}",
             'r0-r12 ' + ' '.join(f'{x:#x}' for x in regs['r'][:13])]
    sp = regs['r'][13]
    if mode == 0x17:   # abort: the fault is at LR-8; the interrupted SP/LR are banked
        sp, lr = regs['abt'][0], regs['abt'][1]
        lines.append(f"DATA ABORT at {regs['r'][14] - 8:#010x}; interrupted sp {sp:#x} lr {lr:#010x}")
    if 0x027E0000 <= sp < 0x027E4000:
        mem, base = dtcm(state), 0x027E0000
    elif ram is not None and 0x02000000 <= sp < 0x02400000:
        mem, base = ram, 0x02000000
    else:
        return lines
    words = struct.unpack_from(f'<{min(128, (len(mem) - (sp - base)) // 4)}I', mem, sp - base)
    code = [f'{sp + 4 * k:#x}:{v:#010x}' for k, v in enumerate(words) if 0x02000000 <= v < 0x02110000
            or 0x02152C20 <= v < 0x02154B20]
    lines.append('stack code words ' + ' '.join(code[:24]))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('run', 'batch'):
        s = sub.add_parser(name)
        s.add_argument('first', type=int)
        if name == 'batch':
            s.add_argument('last', type=int); s.add_argument('--jobs', type=int, default=6)
        s.add_argument('--rom', default=str(DEFAULT_ROM)); s.add_argument('--frames', type=int, default=4000)
        s.add_argument('--tx', type=int, default=LEDGE[0]); s.add_argument('--ty', type=int, default=LEDGE[1])
    s = sub.add_parser('regs'); s.add_argument('state'); s.add_argument('--ram', default=None)
    a = ap.parse_args(argv)
    try:
        if a.cmd == 'run':
            run(a.first, a.rom, a.frames, (a.tx, a.ty))
        elif a.cmd == 'batch':
            return 1 if batch(a.first, a.last, a.jobs, a.rom, a.frames, (a.tx, a.ty)) else 0
        else:
            ram = Path(a.ram).read_bytes() if a.ram else None
            print('\n'.join(describe(Path(a.state).read_bytes(), ram)))
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
