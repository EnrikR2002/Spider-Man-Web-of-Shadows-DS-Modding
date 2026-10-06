#!/usr/bin/env python3
"""Red-kit research lab: emulator traces, story arena, qualification, previews, disassembly.

All runs use the pinned melonDS core (tools/emulator_smoke.py), a COPIED battery
and disposable emulator RAM; nothing is written to a real save. Outputs go to
build/boot-tests/<rom>-<hash>/<label>/ (observations.json, trace.txt, frames)
and work/kit/ (previews, sheets, qualification evidence).

  trace ROM LABEL INPUTS [--frames N --bits B --clear-bits B --enemy-state F0:F1:S
                          --patch P.json --probe ADDR:LEN --cap a,b --ram a,b --near U]
      Training room ("Test Upgrades" dummy); --near U starts Spidey U units left of it. INPUTS frames are relative to
      control start (frame 3030). Red bits are OR-ed in 20 frames before start.
  arena ROM LABEL INPUTS [--tx X --ty Y ...]
      Sewer room left of the story save with live symbiotes; Spidey is teleported
      (all position copies) onto the floor. Spawns vary between runs.
  qualify ROM          kit checks (23) incl. native/Black parity vs the
                       stable parent; writes work/kit/evidence.json.
  preview CLIP [marks] stick-figure sheet of a tools/kit_clips.py clip.
  sheet DIR [x0,y0,x1,y1 scale cols]  contact sheet of captured frames.
  disasm ADDR [N] | xrefs ADDR | words VALUE   clean ARM9 (work/rom/arm9.bin).
  patch OUT.json CODEADDR SRC.s HOOK=TARGET...  runtime RAM patch for --patch.
Inputs: reference/combat-inputs/kit/*.json ({start,end,buttons} rows).
"""
from __future__ import annotations
import argparse
import ctypes as c
import glob as globlib
import json
import math
import os
from pathlib import Path
import struct
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import emulator_smoke as emu, player_trace as p  # noqa: E402
from tools.nitro_texture import png_rgb  # noqa: E402

INPUTS = ROOT / 'reference/combat-inputs/kit'
TRAINING_SAVE = ROOT / 'work/save-backups/before-clarity/save.dsv'
ARENA_SAVE = ROOT / 'work/save-backups/before-v0-1-1-dsv-3f65dfac03240acf4fe444ceeac93b70cc1a9f67fc574a6669bfba18fed06bf2/save.dsv'
TRAINING_START, ARENA_START = 3030, 2000
ENEMY_VTABLE = 0x021301D0          # NormalEnemy
STATS_POINTER = 0x02145C5C         # stats: +0xC ability bits, +0x44 XP
NO_JIT = {b'melonds_jit_enable': b'disabled'}   # runtime RAM patches need JIT off


def rows_from(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def ram_of(lib):
    ptr = lib.retro_get_memory_data(2)
    return ptr, c.string_at(ptr, 4 * 1024 * 1024)


def enemies(ram):
    """Live NormalEnemy actors: hp/max at +0x44, motion at +0x30 (see TECHNICAL)."""
    needle, out, pos = struct.pack('<I', ENEMY_VTABLE), [], 0
    while (at := ram.find(needle, pos)) >= 0:
        pos = at + 4
        if at % 4 or at + 0x90 > len(ram): continue
        hp, maximum = struct.unpack_from('<2i', ram, at + 0x44)
        motion = struct.unpack_from('<I', ram, at + 0x30)[0] - p.BASE
        if not 0 < motion < len(ram) - 0x300 or motion % 4 or not 0 < maximum < 0x1000000: continue
        xy = [struct.unpack_from('<i', ram, motion + b)[0] + struct.unpack_from('<i', ram, motion + l)[0]
              for b, l in ((0x7C, 0x160), (0x80, 0x164))]
        ctl = struct.unpack_from('<I', ram, motion + 0x1F8)[0]
        state = struct.unpack_from('<I', ram, ctl - p.BASE + 0x14)[0] if ctl else None
        out.append({'actor': p.BASE + at, 'hp': hp, 'max': maximum, 'position': xy, 'controller': ctl,
                    'state': state, 'action': struct.unpack_from('<I', ram, motion + 0x254)[0]})
    return out


def observe_row(ram, frame, start, probe=None):
    try:
        o = p.sample(ram)
    except ValueError:
        return None
    ctr = o['controller']
    actor = o['actor_address'] - p.BASE
    row = {'f': frame - start, 'st': ctr['state_id_candidate'] if ctr else None, 'act': o['action_id_candidate'],
           'gmb': o['gmb_id'], 'clock': o['event_clock_candidate'], 'pos': o['position_q12_candidate'],
           'face': o['facing_candidate'], 'vel': list(struct.unpack_from('<2i', ram, actor + 0x18)),
           'en': [(e['hp'], e['position'], e['state'], e['action']) for e in enemies(ram)]}
    if ctr:
        ca = ctr['address'] - p.BASE
        row.update({'prev': struct.unpack_from('<I', ram, ca + 0x18)[0], 'node': struct.unpack_from('<i', ram, ca + 0x80)[0],
                    'f64': struct.unpack_from('<I', ram, ca + 0x64)[0], 'lock': list(struct.unpack_from('<8b', ram, ca + 0x88)),
                    'cancel': ram[actor + 0x28], 'repeats': struct.unpack_from('<b', ram, ca + 0x93)[0],
                    'target': struct.unpack_from('<I', ram, ca + 0x54)[0]})
    if probe:
        address, length = probe
        row['probe'] = list(struct.unpack_from(f'<{length // 4}i', ram, address - p.BASE))
    return row


def write_trace(dest, rows):
    last = None
    with open(dest / 'trace.txt', 'w', encoding='utf-8') as f:
        for r in rows:
            key = (r['st'], r['act'], r.get('node'), r['face'], r['en'][0][0] if r['en'] else None)
            if key != last:
                f.write(f"{r['f']:5d} st={r['st']} act={r['act']} node={r.get('node')} face={r['face']} "
                        f"pos={r['pos']} vel={r['vel']} en={r['en'][:3]}\n")
                last = key


def apply_patches(lib, patches, verify):
    ptr = lib.retro_get_memory_data(2)
    for row in patches:
        data = bytes.fromhex(row['hex']); at = row['addr'] - p.BASE
        if verify and 'expect' in row:
            current = c.string_at(ptr + at, len(bytes.fromhex(row['expect'])))
            if current != bytes.fromhex(row['expect']):
                raise ValueError(f'Patch site {row["addr"]:#x} differs: {current.hex()}')
        c.memmove(ptr + at, data, len(data))


def set_bits(lib, bits, clear):
    ptr, ram = ram_of(lib)
    stats = struct.unpack_from('<I', ram, STATS_POINTER - p.BASE)[0] - p.BASE
    old = struct.unpack_from('<I', ram, stats + 0xC)[0]
    c.memmove(ptr + stats + 0xC, struct.pack('<I', (old | bits) & ~clear), 4)


def run(rom, label, inputs, **options):
    """Run in a child process (the core prints thousands of log lines); return (dir, rows)."""
    import subprocess
    request = {'rom': str(Path(rom).resolve()), 'label': label,
               'inputs': inputs if isinstance(inputs, list) else str(inputs), 'options': options}
    done = subprocess.run([sys.executable, str(Path(__file__).resolve()), '_child', json.dumps(request)],
                          cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    marker = [line for line in done.stdout.splitlines() if line.startswith('KITLAB_DEST ')]
    if done.returncode or not marker:
        tail = [line for line in done.stdout.splitlines() if 'error' in line.lower()][-3:]
        raise ValueError(f'Emulator run {label} failed: {tail}')
    dest = Path(marker[-1][12:])
    path = dest / 'observations.json'
    return dest, json.loads(path.read_text()) if path.exists() else []


def _run(rom, label, inputs, *, frames=600, bits=0xFE000, clear=0, enemy_state=None, patch=None, probe=None,
        caps=(), rams=(), arena=False, tx=120000, ty=40922, save=None, near=None):
    """One disposable emulator run; returns (output directory, observation rows)."""
    rom = Path(rom).resolve()
    rel = rows_from(inputs) if not isinstance(inputs, list) else inputs
    if arena:
        start = ARENA_START
        prefix = rows_from(INPUTS / 'story_entry.json')
        save = Path(save or ARENA_SAVE)
    else:
        start = TRAINING_START
        prefix = [r for r in rows_from(ROOT / 'reference/combat-inputs/oscorp-owned.json') if r['start'] < 3000]
        save = Path(save or TRAINING_SAVE)
    if not save.is_file():
        raise ValueError(f'Copied research save missing: {save} (use --save with a private snapshot copy)')
    script = prefix + [{'start': r['start'] + start, 'end': r['end'] + start, 'buttons': r['buttons']} for r in rel]
    patches = rows_from(patch) if patch else []

    def hook(frame, lib):
        if patches and frame in (60, start - 40):
            apply_patches(lib, patches, frame == 60)
        if not arena and frame == 2040:      # menu fixture: enough XP for the scripted purchase
            ptr, ram = ram_of(lib)
            stats = struct.unpack_from('<I', ram, STATS_POINTER - p.BASE)[0] - p.BASE
            c.memmove(ptr + stats + 0x44, struct.pack('<I', 2000), 4)
        if frame == start - 20:
            set_bits(lib, bits, clear)
            ptr, ram = ram_of(lib)
            if not arena:   # training dummy: generous HP so a run never kills it
                for e in enemies(ram):
                    c.memmove(ptr + e['actor'] - p.BASE + 0x44, struct.pack('<2i', 65536, 65536), 8)
                if near is not None and enemies(ram):   # stand `near` (Q12) left of the dummy
                    tx = enemies(ram)[0]['position'][0] - near
                    ty = struct.unpack_from('<i', ram, p.sample(ram)['motion_address'] - p.BASE + 0x80)[0] +                         struct.unpack_from('<i', ram, p.sample(ram)['motion_address'] - p.BASE + 0x164)[0]
            if arena or near is not None:   # teleport: base position plus every actor position copy
                o = p.sample(ram); mot = o['motion_address'] - p.BASE; act = o['actor_address'] - p.BASE
                lx, ly = struct.unpack_from('<2i', ram, mot + 0x160)
                c.memmove(ptr + mot + 0x7C, struct.pack('<2i', tx - lx, ty - ly), 8)
                for off in (0x148, 0x180, 0x210, 0x2CC):
                    c.memmove(ptr + act + off, struct.pack('<2i', tx, ty), 8)
        if enemy_state and start + enemy_state[0] <= frame < start + enemy_state[1]:
            ptr, ram = ram_of(lib)
            for e in enemies(ram):
                if e['controller']:
                    c.memmove(ptr + e['controller'] - p.BASE + 0x14, struct.pack('<I', enemy_state[2]), 4)

    def observe(frame, lib):
        if frame < start - 20: return None
        return observe_row(ram_of(lib)[1], frame, start, probe)

    dest = emu.run(rom, start + frames, {start + x for x in caps}, save_path=save, script=script, label=label,
                   frame_hook=hook, observer=observe, ram_captures={start + x for x in rams}, core_options=NO_JIT)
    path = dest / 'observations.json'
    rows = json.loads(path.read_text()) if path.exists() else []
    write_trace(dest, rows)
    return dest, rows


# ------------------------------------------------------------------ qualification
def seq(rows):
    out, last = [], None
    for r in rows:
        k = (r['st'], r['act'], r['face'])
        if k != last: out.append((r['f'],) + k + (r['pos'][0],)); last = k
    return out


def same_behavior(a, b):
    """Same state/action/facing/position sequence up to one constant frame phase (<=2).

    Growing the Glob shifts load timing by an emulator frame; behavior is unchanged."""
    if len(a) != len(b) or any(x[1:] != y[1:] for x, y in zip(a, b)): return False
    shifts = {x[0] - y[0] for x, y in zip(a[1:], b[1:])}
    return len(shifts) <= 1 and all(abs(s) <= 2 for s in shifts)


def spin_hits(rows):
    """Number of HP drops of the first enemy across consecutive rows."""
    return sum(1 for x, y in zip(rows, rows[1:]) if y['en'][0][0] < x['en'][0][0])


def first(rows, cond):
    return next((r for r in rows if cond(r)), None)


def qualify(rom, parent=ROOT / 'build/releases/bcc6974a08b899a2def261b550b8bf9a31b005e201c7c4e276fc46dbf3e5d842/Spider-Man-WoS-modded.nds'):
    """Measured expectations for the kit (v0.2.0 + v0.2.1 spin); parent = v0.1.1 for native parity."""
    def go(label, name, frames, **kw): return run(rom, label, INPUTS / f'{name}.json', frames=frames, **kw)[1]
    ck = {}
    o = go('q_reflex', 'reflex', 300)
    d = first(o, lambda r: r['f'] >= 30 and r['st'] == 53)
    ck['reflex_cancels_snap_within_2_frames'] = bool(d and d['f'] <= 32)
    roll = first(o, lambda r: r['f'] >= 112 and r['st'] == 57)
    ck['reflex_left_turns_and_rolls'] = bool(roll and roll['face'] == 0 and roll['f'] <= 114)
    o = go('q_resume', 'reflexres', 160)
    ck['reflex_resume_continues_node_13'] = bool(first(o, lambda r: 67 < r['f'] < 110 and r['st'] == 46 and r['node'] == 13))
    o = go('q_split', 'split', 380)
    n15 = first(o, lambda r: r['node'] == 15 and r['st'] == 46)
    ck['split_turns_to_enemy_behind'] = bool(n15 and n15['face'] == 0)
    spin = [r for r in o if r['node'] == 16 and r['f64'] & 0x8000]
    ck['spin_repeat_active'] = len(spin) > 20
    ck['spin_steers_left'] = bool(spin and min(r['pos'][0] for r in spin) < spin[0]['pos'][0] - 40000)
    ck['split_and_spin_damage'] = o[-1]['en'][0][0] < 65536
    # v0.2.1: every spin contact lands on a lone enemy (aim per contact, glide into reach)
    o = go('q_spin_reach', 'spinreach', 330, near=6 * 4096)
    spin = [r for r in o if r['node'] == 16 and r['f64'] & 0x8000]
    ck['spin_every_contact_hits'] = len(spin) > 60 and spin_hits(spin) >= 12
    o = go('q_spin_glide', 'spinglide', 300, near=6 * 4096)
    late = [r for r in o if r['f'] >= 140 and r['node'] == 16 and r['f64'] & 0x8000]
    ck['spin_survives_back_steer_and_glides_back'] = len(late) > 60 and spin_hits(late) >= 8
    sweep = [r for r in o if r['node'] == 17 and r['act'] == 62]
    ck['spin_exit_keeps_sweep_in_reach'] = bool(sweep and sweep[-1]['en'][0][0] < sweep[0]['en'][0][0])
    o = go('q_perch', 'perch2', 320)
    pounds = [r for r in o if r['st'] == 51 and r['act'] == 130]
    ck['perch_pounds'] = len(pounds) > 20
    ck['perch_held_on_target'] = bool(pounds) and all(abs(r['pos'][1] - (r['en'][0][1][1] + 0x7000)) < 0x2000 for r in pounds[2:10])
    ck['perch_damage'] = min(r['en'][0][0] for r in o) <= 65536 - 4 * 3072
    o = go('q_leap', 'webkick', 120)
    end, beg = o[-1], first(o, lambda r: r['st'] == 42)
    ck['leapfrog_damage'] = end['en'][0][0] < 65536
    ck['leapfrog_faces_target'] = (end['face'] == 1) == (end['en'][0][1][0] > end['pos'][0])
    ck['leapfrog_swaps_sides'] = bool(beg and (beg['en'][0][1][0] > beg['pos'][0]) != (end['en'][0][1][0] > end['pos'][0]))
    o = go('q_sky', 'vault', 220)
    spike = first(o, lambda r: r['act'] == 4 and r['st'] == 51)
    ck['skyjack_air_hits_connect'] = min(r['en'][0][0] for r in o) <= 65536 - 3 * 4096
    landed = first(o, lambda r: spike and r['f'] > spike['f'] and r['en'][0][1][1] < 25000)
    ck['skyjack_spike_lands_target_fast'] = bool(spike and landed and landed['f'] - spike['f'] < 40)
    o = go('q_sense', 'sense', 160, enemy_state=(60, 76, 15))
    s = first(o, lambda r: r['st'] == 46 and r['node'] == 14)
    ck['sense_counter_behind_attacker'] = bool(s and s['f'] <= 72 and (s['pos'][0] > s['en'][0][1][0]) == (s['face'] == 0))
    ck['sense_counter_damage'] = o[-1]['en'][0][0] < 65536
    for label, name, frames, kw in (('q_gate', 'gate', 260, {'bits': 0, 'clear': 0xFE000}),
                                    ('q_snare_off', 'snare', 200, {'bits': 0, 'clear': 0xFE000}),
                                    ('q_black', 'black', 300, {})):
        mine = seq(go(label, name, frames, **kw))
        base = seq(run(parent, label + '_p', INPUTS / f'{name}.json', frames=frames, **kw)[1])
        ck[f'native_identical_{label}'] = same_behavior(mine, base)
    report = {'rom': str(rom), 'parent': str(parent), 'checks': ck, 'passed': all(ck.values())}
    out = ROOT / 'work/kit/evidence.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1))
    return report


# ------------------------------------------------------------------ images
BONES = [(1, 2), (2, 3), (3, 4), (4, 5), (3, 6), (6, 7), (7, 8), (8, 9), (3, 16), (16, 17), (17, 18), (18, 19),
         (1, 26), (26, 27), (27, 28), (28, 29), (1, 30), (30, 31), (31, 32), (32, 33)]
LEFT, RIGHT = {6, 7, 8, 9, 26, 27, 28, 29}, {16, 17, 18, 19, 30, 31, 32, 33}


def preview(frames, path, cols=10, cell=128, scale=10., marks=()):
    """Side view (Z right, Y up) over front view; Spidey's left blue, right red."""
    rows = (len(frames) + cols - 1) // cols; W, H = cols * cell, rows * cell * 2
    img = bytearray(b'\x10\x10\x18' * (W * H))
    def px(x, y, col):
        if 0 <= x < W and 0 <= y < H: i = (y * W + x) * 3; img[i:i + 3] = bytes(col)
    def line(x0, y0, x1, y1, col):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for k in range(n + 1):
            t = k / n; x = round(x0 + (x1 - x0) * t); y = round(y0 + (y1 - y0) * t)
            for dx in (0, 1):
                for dy in (0, 1): px(x + dx, y + dy, col)
    for i, pos in enumerate(frames):
        cx, cy = (i % cols) * cell, (i // cols) * cell * 2
        for view, oy in ((0, 0), (1, cell)):
            ground = cy + oy + cell - 8
            line(cx + 2, ground, cx + cell - 3, ground, (150, 120, 40) if i in marks else (60, 60, 70))
            ox = cx + cell // 2
            for a, b in BONES:
                ha = pos[a][2] if view == 0 else -pos[a][0]; hb = pos[b][2] if view == 0 else -pos[b][0]
                col = (80, 140, 255) if b in LEFT else (255, 90, 90) if b in RIGHT else (235, 235, 235)
                line(ox + ha * scale, ground - pos[a][1] * scale, ox + hb * scale, ground - pos[b][1] * scale, col)
            h = pos[5]; hx = h[2] if view == 0 else -h[0]
            for a in range(0, 360, 20):
                px(round(ox + hx * scale + 3 * math.cos(math.radians(a))), round(ground - h[1] * scale + 3 * math.sin(math.radians(a))), (255, 220, 120))
        for k in range(i % 10 + 1): px(cx + 3 + k * 3, cy + 3, (255, 255, 0))
    Path(path).write_bytes(png_rgb(W, H, bytes(img)))


def preview_clip(name, marks=()):
    import mod
    from tools.animation_rig import AnimationRig
    from tools.sca import Sca
    from tools import kit_clips, kit_choreography as kc
    _, glob, manifest = mod.load_clean()
    e = {x['name']: x for x in manifest['entries']}
    def clean(n): return glob[e[n]['offset']:e[n]['offset'] + e[n]['size']]
    rig = kc.Rig(Sca.parse(clean('spd_Idle.sca')), AnimationRig.parse(clean('spd.nsbmd')).parents)
    clip = kit_clips.CLIPS[name]
    path = ROOT / f'work/kit/clip-{name}.png'
    path.parent.mkdir(parents=True, exist_ok=True)
    preview(rig.bake(clip)[2], path, cols=min(clip.samples, 10), marks=marks)
    return path


def read_png(path):
    d = Path(path).read_bytes(); i = 8; w = h = 0; idat = b''
    while i < len(d):
        n = struct.unpack('>I', d[i:i + 4])[0]; t = d[i + 4:i + 8]; chunk = d[i + 8:i + 8 + n]
        if t == b'IHDR': w, h = struct.unpack('>II', chunk[:8])
        if t == b'IDAT': idat += chunk
        i += 12 + n
    raw = zlib.decompress(idat); stride = w * 3 + 1; rows = []; prev = bytearray(w * 3)
    for y in range(h):
        f = raw[y * stride]; line = bytearray(raw[y * stride + 1:(y + 1) * stride])
        for x in range(len(line)):
            a = line[x - 3] if x >= 3 else 0; b = prev[x]; cc = prev[x - 3] if x >= 3 else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + b) & 255
            elif f == 3: line[x] = (line[x] + (a + b) // 2) & 255
            elif f == 4:
                pp = a + b - cc; pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - cc)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else (b if pb <= pc else cc))) & 255
        rows.append(bytes(line)); prev = line
    return w, h, rows


def sheet(paths, out, box=(0, 0, 256, 192), scale=1, cols=8):
    """Crop each capture to box (top screen by default), scale, and tile."""
    x0, y0, x1, y1 = box; w, h = (x1 - x0) * scale, (y1 - y0) * scale
    imgs = [read_png(q) for q in paths]; nrows = (len(imgs) + cols - 1) // cols
    W, H = w * cols, h * nrows; canvas = [bytearray(W * 3) for _ in range(H)]
    for k, (_, _, rows) in enumerate(imgs):
        cx, cy = (k % cols) * w, (k // cols) * h
        for y in range(y1 - y0):
            src = rows[y0 + y]; line = bytearray()
            for x in range(x0, x1): line += src[x * 3:x * 3 + 3] * scale
            for s in range(scale): canvas[cy + y * scale + s][cx * 3:(cx + w) * 3] = line
    Path(out).write_bytes(png_rgb(W, H, b''.join(bytes(r) for r in canvas)))


# ------------------------------------------------------------------ ARM9 research
def _capstone():
    sys.path.insert(0, str(ROOT / 'work/research-libs'))
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM); md.skipdata = True
    return md


def clean_arm9():
    path = ROOT / 'work/rom/arm9.bin'
    if not path.is_file(): raise ValueError('work/rom/arm9.bin missing: run python mod.py extract')
    return path.read_bytes()


def disasm(address, count=60):
    a9, md = clean_arm9(), _capstone()
    out = []
    for i in md.disasm(a9[address - p.BASE:address - p.BASE + 4 * count], address):
        s = f'{i.address:08x}: {i.mnemonic:8s} {i.op_str}'
        if i.mnemonic.startswith('ldr') and '[pc, #' in i.op_str:
            off = int(i.op_str.split('#')[-1].rstrip(']'), 0)
            s += f'   ; ={struct.unpack_from("<I", a9, i.address + 8 + off - p.BASE)[0]:#x}'
        out.append(s)
    return '\n'.join(out)


def xrefs(target):
    a9 = clean_arm9(); res = []
    for off in range(0, len(a9) - 4, 4):
        word = struct.unpack_from('<I', a9, off)[0]
        if (word >> 25) & 7 == 5 and word >> 28 != 0xF:
            d = word & 0xFFFFFF
            if d & 0x800000: d -= 0x1000000
            if p.BASE + off + 8 + d * 4 == target: res.append(p.BASE + off)
    return res


def words(value):
    a9 = clean_arm9()
    return [p.BASE + o for o in range(0, len(a9) - 4, 4) if struct.unpack_from('<I', a9, o)[0] == value]


def make_patch(out, code_address, source, hooks):
    """Assemble SRC at CODE_ADDRESS (start it with a branch table) plus hook branches."""
    sys.path.insert(0, str(ROOT / 'work/research-libs'))
    from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
    from tools.combat_feedback import branch
    a9 = clean_arm9()
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(Path(source).read_text(), code_address)[0])
    rows = [{'addr': code_address, 'hex': code.hex(), 'expect': '00' * len(code)}]
    for hook, target in hooks:
        rows.append({'addr': hook, 'hex': struct.pack('<I', branch(hook, target)).hex(),
                     'expect': a9[hook - p.BASE:hook - p.BASE + 4].hex()})
    Path(out).write_text(json.dumps(rows, indent=1))
    return len(code)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('trace', 'arena'):
        s = sub.add_parser(name); s.add_argument('rom'); s.add_argument('label'); s.add_argument('inputs')
        s.add_argument('--frames', type=int, default=600); s.add_argument('--bits', default='0xFE000')
        s.add_argument('--clear-bits', default='0'); s.add_argument('--enemy-state', default='')
        s.add_argument('--patch', default=''); s.add_argument('--probe', default='')
        s.add_argument('--cap', default=''); s.add_argument('--ram', default=''); s.add_argument('--save', default=None)
        s.add_argument('--tx', type=int, default=120000); s.add_argument('--ty', type=int, default=40922)
        s.add_argument('--near', type=float, default=None, help='training: start this many units left of the dummy')
    s = sub.add_parser('_child'); s.add_argument('request')
    s = sub.add_parser('qualify'); s.add_argument('rom'); s.add_argument('--parent', default=None)
    s = sub.add_parser('preview'); s.add_argument('clip'); s.add_argument('marks', nargs='?', default='')
    s = sub.add_parser('sheet'); s.add_argument('dir'); s.add_argument('--box', default='0,0,256,192')
    s.add_argument('--scale', type=int, default=1); s.add_argument('--cols', type=int, default=8)
    s.add_argument('--out', default=str(ROOT / 'work/kit/sheet.png'))
    s = sub.add_parser('disasm'); s.add_argument('address'); s.add_argument('count', nargs='?', type=int, default=60)
    s = sub.add_parser('xrefs'); s.add_argument('address')
    s = sub.add_parser('words'); s.add_argument('value')
    s = sub.add_parser('patch'); s.add_argument('out'); s.add_argument('code_address'); s.add_argument('source')
    s.add_argument('hooks', nargs='*', help='HOOK=TARGET (hex)')
    a = ap.parse_args(argv)
    try:
        if a.cmd in ('trace', 'arena'):
            inputs = Path(a.inputs) if Path(a.inputs).suffix else INPUTS / f'{a.inputs}.json'
            probe = tuple(int(x, 0) for x in a.probe.split(':')) if a.probe else None
            state = tuple(int(x, 0) for x in a.enemy_state.split(':')) if a.enemy_state else None
            dest, rows = run(a.rom, a.label, inputs, frames=a.frames, bits=int(a.bits, 0), clear=int(a.clear_bits, 0),
                             enemy_state=state, patch=a.patch or None, probe=probe, save=a.save,
                             caps=[int(x) for x in a.cap.split(',') if x], rams=[int(x) for x in a.ram.split(',') if x],
                             arena=a.cmd == 'arena', tx=a.tx, ty=a.ty,
                             near=None if a.near is None else round(a.near * 4096))
            print(dest / 'trace.txt')
        elif a.cmd == '_child':
            req = json.loads(a.request)
            opts = req['options']
            for key in ('caps', 'rams', 'enemy_state', 'probe'):
                if opts.get(key) is not None: opts[key] = tuple(opts[key])
            dest, _ = _run(req['rom'], req['label'], req['inputs'], **opts)
            print('KITLAB_DEST ' + str(dest), flush=True)
        elif a.cmd == 'qualify':
            report = qualify(a.rom, *( [a.parent] if a.parent else []))
            print(json.dumps(report, indent=1)); return 0 if report['passed'] else 1
        elif a.cmd == 'preview':
            print(preview_clip(a.clip, tuple(int(x) for x in a.marks.split(',') if x)))
        elif a.cmd == 'sheet':
            paths = sorted(globlib.glob(os.path.join(a.dir, 'frame-*.png')))
            sheet(paths, a.out, tuple(int(x) for x in a.box.split(',')), a.scale, a.cols); print(a.out)
        elif a.cmd == 'disasm': print(disasm(int(a.address, 0), a.count))
        elif a.cmd == 'xrefs': print('\n'.join(hex(x) for x in xrefs(int(a.address, 0))))
        elif a.cmd == 'words': print('\n'.join(hex(x) for x in words(int(a.value, 0))))
        elif a.cmd == 'patch':
            hooks = [tuple(int(v, 0) for v in h.split('=')) for h in a.hooks]
            print(make_patch(a.out, int(a.code_address, 0), a.source, hooks), 'bytes')
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr); return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
