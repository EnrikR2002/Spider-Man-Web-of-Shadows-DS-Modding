"""Copied-save Talon Pounce inputs, native reactions, terrain and follow-ups."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import hunter_kit_lab, kit_lab as k, vortex_forge_lab as v, wos_tool as w
from tools.freefall_lab import OPTIONS, audio_capture, save_audio


BASE, UNIT = k.p.BASE, 4096
POUNCE, QUICK, AIR_DODGE = 1 << 25, 1 << 26, 1 << 10
SKY_RAKE, BOARDING = 1 << 21, 1 << 24
CASES = ('range', 'rising', 'quick', 'early', 'hold', 'left', 'miss', 'red', 'unowned',
         'taps', 'coil-r', 'air-r', 'air-fall', 'release-r', 'swap', 'wall')
CANCEL = {'coil-r': 61, 'air-r': 89, 'air-fall': 89, 'release-r': 93}
RELEASE = {'quick': 63, 'early': 63, 'hold': 105, 'taps': 43}


def press(start, end, *buttons):
    return dict(start=start, end=end, buttons=list(buttons))


def sample(frame, ram, runtime):
    hero = k.observe_row(ram, frame, 0)
    player = k.p.sample(ram)
    actor = player['actor_address'] - BASE
    motion = player['motion_address'] - BASE
    wrapper = w.u32(ram, motion+0x58) - BASE
    slot = w.u32(ram, wrapper+0x29c)
    hero.update(form=w.u32(ram, actor+0x34),
                pad=struct.unpack_from('<H', ram, 0x02145a4a-BASE)[0],
                sca=w.u32(ram, wrapper+0x1c4+0x78*slot),
                floor=struct.unpack_from('<i', ram, motion+0x2ac)[0],
                pounce=struct.unpack_from('<9i', ram, runtime['state']-BASE) if runtime else (0,)*9)
    return hero, motion


def training(a, meta, digest):
    actual, before, copied = v.copy_current(a.out)
    runtime = meta.get('talon_pounce', {}).get('runtime')
    case = a.case
    aim = case in ('rising', 'air-r', 'air-fall', 'swap')
    face = -1 if case == 'left' else 1
    release = RELEASE.get(case, 83)
    gap = {'rising': 17, 'left': 22, 'range': 25, 'early': 5, 'taps': 5,
           'miss': 42, 'release-r': 22}.get(case, 22)
    inputs = [press(33, 37, 'Right' if face > 0 else 'Left'), press(40, release, 'Y')]
    if aim:
        inputs.append(press(release-4, release+8, 'Up'))
    if case == 'rising':
        inputs.append(press(98, 104, 'Y'))
    if case == 'taps':
        inputs.extend(press(f, f+3, 'Y') for f in (79, 120))
    if case == 'swap':
        inputs.append(press(89, 94, 'L'))
    if case in CANCEL:
        inputs.append(press(CANCEL[case], CANCEL[case]+5, 'R'))

    rows, pcm, rate, target = [], [], [], []
    buttons = set()
    audio_start = 37

    def observe(frame, lib):
        if frame < -10:
            return
        ptr, ram = k.ram_of(lib)
        enemies = k.enemies(ram)
        stage = max(37, release-3)
        if frame < stage+10:
            for e in enemies:
                if e['state'] in (0, 1, 2, 15) and (case != 'rising' or frame < release or e['actor'] not in target):
                    ctl = ptr+e['controller']-BASE
                    ct.memmove(ctl+0x14, bytes(4), 4)
                    ct.memmove(ctl+4, b'\1', 1)
        if frame < 0:
            return
        row, _ = sample(frame, ram, runtime)
        buttons.clear()
        if frame in range(4, 10) and row['form'] != int(case != 'red') and row['st'] != 59:
            buttons.add('L')
        if frame == stage:
            for i, e in enumerate(enemies):
                if i == 1:
                    target.append(e['actor'])
                else:
                    em = w.u32(ram, e['actor']-BASE+0x30)-BASE
                    k.teleport(ptr, ram, em, (18+12*i)*UNIT, row['pos'][1])
        if target:
            foe = next(e for e in enemies if e['actor'] == target[0])
            em = w.u32(ram, foe['actor']-BASE+0x30)-BASE
            if frame == stage or case == 'wall' and stage <= frame <= 105:
                x = 244*UNIT if case == 'wall' else row['pos'][0]+face*gap*UNIT
                y = row['pos'][1] + (0 if case in ('wall', 'rising') else UNIT)
                k.teleport(ptr, ram, em, x, y)
                ct.memmove(ptr+foe['actor']-BASE+0x18, bytes(8), 8)
                if frame == stage and case == 'rising':
                    ct.memmove(ptr+em+0x180, struct.pack('<I', int(face < 0)), 4)
                    ct.memmove(ptr+foe['controller']-BASE+0x14, bytes(4), 4)
                    ct.memmove(ptr+foe['controller']-BASE+4, b'\1', 1)
            if case == 'rising' and frame == release-1:
                k.teleport(ptr, ram, em, foe['position'][0], foe['position'][1]+5*UNIT)
                ct.memmove(ptr+foe['controller']-BASE+0x14, struct.pack('<I', 4), 4)
                ct.memmove(ptr+foe['controller']-BASE+4, b'\1', 1)
            row['foe'] = foe
        if frame == audio_start:
            rate[:] = audio_capture(lib, pcm)
        rows.append(row)

    original_rows = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else original_rows(path)
    bits = (0 if case == 'unowned' else POUNCE) | (QUICK if case == 'quick' else 0)
    clear = (0 if case == 'quick' else QUICK) | (POUNCE if case == 'unowned' else 0)
    if case == 'air-fall':
        clear |= AIR_DODGE
    if case == 'air-r':
        bits |= AIR_DODGE
    try:
        route, _ = k._run(a.rom, a.tag, inputs, frames=167, bits=bits, clear=clear, bits2=SKY_RAKE,
                          sparring=True, start_x=(220 if case == 'wall' else 100)*UNIT,
                          save=copied, caps=range(36, 153) if a.capture else (), extra_hook=observe,
                          core_options=OPTIONS, live_buttons=buttons)
    finally:
        k.rows_from = original_rows
    save_audio(a.out, pcm, rate[1])
    flight = [r for r in rows if r['pounce'][3] >= 3]
    coil = [r for r in rows if 1 <= r['pounce'][3] <= 2]
    contacts = [r['f'] for old, r in zip(rows, rows[1:]) if 'foe' in old and r['foe']['hp'] < old['foe']['hp']]
    hits = [f for f in contacts if rows[f]['pounce'][3] >= 3]
    checks = dict(battery_unchanged=actual.read_bytes() == before == copied.read_bytes(),
                  cleanup=rows[-1]['pounce'][3] == 0, trained_in_requested_form=rows[40]['form'] == int(case != 'red'))
    if case in ('red', 'unowned', 'taps') or not runtime:
        checks['native_path'] = not (flight or coil) and any(r['st'] == 46 for r in rows)
    elif case == 'early':
        checks['early_release_resumes_strike'] = bool(coil) and not flight and bool(contacts)
    elif case == 'coil-r':
        checks['r_ends_coil'] = bool(coil) and not flight and any(r['st'] in (53, 54, 57) for r in rows[61:66])
    else:
        checks['takeoff_on_release'] = bool(flight) and release <= flight[0]['f'] <= release+2
        checks['private_leap_drawn'] = bool(flight) and any(r['sca'] == runtime['values'][('HIGH' if aim else 'LOW')+'_SCA']
                                                          for r in flight)
        if case in CANCEL:
            wanted = 19 if case == 'air-fall' else 52
            checks['r_ends_attack'] = any(r['st'] == wanted and not r['pounce'][3]
                                          for r in rows[CANCEL[case]:CANCEL[case]+4])
            checks['no_late_hit'] = not hits and not contacts
        elif case == 'swap':
            checks['switch_ends_attack'] = not hits and not any(r['pounce'][3] for r in rows[93:])
        elif case == 'wall':
            checks['wall_blocks_motion_and_contact'] = (236*UNIT < max(r['pos'][0] for r in rows) < 237*UNIT and not contacts
                                                        and all(r['foe']['position'][0] > 240*UNIT for r in rows[83:104]))
        elif case == 'miss':
            checks['whiff_is_bounded'] = bool(flight) and not hits and 19*UNIT <= flight[-1]['pos'][0]-flight[0]['pos'][0] <= 25*UNIT
        elif case == 'quick':
            checks['half_charge_window'] = 8 <= rows[release-1]['pounce'][4] < 16
            checks['quick_coil'] = any(r['sca'] == runtime['values']['QUICK_SCA'] for r in coil)
        else:
            checks['single_pounce_contact'] = len(hits) == 1
            reaction = 42 if aim else 41
            checks['native_reaction'] = bool(hits) and any(r['foe']['state'] == reaction for r in rows[hits[0]:hits[0]+10])
            if aim:
                checks['chosen_sky_rake_hits'] = any(rows[f]['st'] == 51 and rows[f]['act'] in (1, 2, 3) for f in contacts if f not in hits)
            if case == 'hold':
                checks['stays_coiled_until_release'] = rows[release-2]['pounce'][4] == 16
            if case == 'left':
                checks['left_leap'] = bool(flight) and flight[-1]['pos'][0] < flight[0]['pos'][0]

    report = dict(passed=all(checks.values()), checks=checks, case=case, route=str(route), inputs=inputs, rows=rows,
                  contacts=contacts, pounce_contacts=hits, rom_sha256=digest, battery_sha256=w.sha256(before),
                  frame_offset=k.TRAINING_START, audio_start=audio_start, frame_rate=rate[0],
                  limits='Latest DSV copy and disposable training fixture. Player and enemies staged before combat. '
                         'Enemy idle/attack starts are held around setup. The rising target uses one native jump start. '
                         'The wall target is parked across the BSP. '
                         'All player movement, hit reactions and controls run through the engine.')
    return report


def boss(a, meta, digest):
    from tools import midnight_rework_lab as lab

    actual, before, copied = v.copy_current(a.out)
    runtime = meta['talon_pounce']['runtime']
    boarding = meta['boarding']['runtime']['state'] - BASE
    config = runtime['values']['BOSS_CONFIG']
    patch = a.out/'entry.json'
    words = ((0x020ed7ac, 1, 1, 0), (0x020ed7b4, 2, 0x46, 89),
             (0x020ed7dc, 2, 2, 1), (0x020ed7e0, 3, 0, 2))
    w.write_json(patch, [dict(addr=at, expect=struct.pack('<I', 0xe3a00000 | reg<<12 | old).hex(),
                              hex=struct.pack('<I', 0xe3a00000 | reg<<12 | new).hex())
                         for at, reg, old, new in words])
    buttons, rows, pcm, rate = set(), [], [], []
    attempt = -100
    last_hp = None
    contact = None
    latch = None
    last_flight = -100
    ride = a.case == 'boss'

    def observe(frame, lib):
        nonlocal attempt, last_hp, contact, latch, last_flight
        if frame < 0 and frame != -1300:
            return
        ptr, ram = k.ram_of(lib)
        stats = w.u32(ram, k.STATS_POINTER-BASE)-BASE
        if frame < 0:
            flags = int.from_bytes(ram[stats+0x1c:stats+0x44], 'little') & ~(1 << 147)
            ct.memmove(ptr+stats+0x1c, flags.to_bytes(40, 'little'), 40)
            return
        if frame == 0:
            rate[:] = audio_capture(lib, pcm)
        row, _ = sample(frame, ram, runtime)
        foe = next((e for e in k.enemies(ram) if e['hp'] > 0 and w.u32(ram, e['actor']-BASE+0x40) == config), None)
        phase = w.u32(ram, boarding+24)
        if foe and last_hp is not None and foe['hp'] < last_hp and row['pounce'][3] in (3, 4):
            contact = frame
        if foe:
            last_hp = foe['hp']
        if row['pounce'][3] == 4:
            last_flight = frame
        if latch is None and phase in (1, 2) and frame-last_flight <= 3:
            latch = frame
        buttons.clear()
        if not row['form']:
            if frame % 60 < 6:
                buttons.add('L')
        elif latch is not None:
            if 18 <= frame-latch < 24:
                buttons.add('Y')
            if frame-latch >= 40:
                buttons.add('R')
        elif ride or contact is None:
            dx = (foe['position'][0]-row['pos'][0])/UNIT if foe else 30
            age = frame-attempt
            direction = 'Right' if dx >= 0 else 'Left'
            if 0 <= age < 44:
                buttons.add('Y')
            if ride and 40 <= age < 78:
                buttons.update(('Up', direction))
            if age > 94 and row['st'] in (0, 1, 6):
                if not 12 <= abs(dx) <= 27:
                    buttons.add(direction if abs(dx) > 27 else ('Left' if dx >= 0 else 'Right'))
                elif foe:
                    attempt = frame
                    buttons.add('Y')
        row.update(foe=foe, boarding=phase, buttons=sorted(buttons), room=w.u32(ram, stats))
        rows.append(row)
        if latch is not None and frame >= latch+54 or not ride and contact is not None and frame >= contact+32:
            return 'stop'

    original_rows = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else original_rows(path)
    lab.JIT = True
    try:
        route, _ = lab.static_warp_runner(k._run)(a.rom, a.tag, [], frames=750, bits=POUNCE,
                       clear=QUICK, bits2=BOARDING, patch=str(patch), sparring=True, save=copied,
                       caps=range(0, 750) if a.capture else (), extra_hook=observe, live_buttons=buttons)
    finally:
        k.rows_from = original_rows
    save_audio(a.out, pcm, rate[1])
    response = rows[contact:contact+8] if contact is not None else []
    checks = dict(battery_unchanged=actual.read_bytes() == before == copied.read_bytes(),
                  native_boss_room=all(r['room'] == 89 for r in rows))
    if ride:
        checks['boarding_from_pounce'] = latch is not None and 0 <= latch-last_flight <= 3
        checks['rake_while_boarded'] = latch is not None and any(r['boarding'] == 3 for r in rows[latch:])
        checks['releases_on_r'] = latch is not None and rows[-1]['boarding'] == 0
    else:
        checks['heavy_contact'] = any(r['pounce'][8] for r in response)
        checks['boss_staggers'] = any(r['foe'] and r['foe']['state'] == 37 for r in response)
        checks['boss_stays_grounded'] = bool(response) and all(r['foe']['state'] not in (39, 41, 42, 44, 48, 49)
                                                              for r in response if r['foe'])
    return dict(passed=all(checks.values()), checks=checks, case=a.case, route=str(route),
                rom_sha256=digest, battery_sha256=w.sha256(before), rows=rows, contact=contact, latch=latch,
                frame_offset=k.TRAINING_START, audio_start=0, frame_rate=rate[0],
                limits='Latest DSV copy. Four private entry words, Conductor retry flag and disposable ownership. '
                       'Boss spawn, movement, combat and Boarding use native encounter inputs.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--case', choices=(*CASES, 'boss', 'boss-strike', 'shop'), required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--capture', action='store_true')
    a = parser.parse_args()
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        parser.error('Lab evidence belongs in work/')
    if a.case == 'shop':
        return hunter_kit_lab.shop(a, row=5, bit=25, price=225)
    digest = w.sha256(a.rom.read_bytes())
    meta = json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    if digest != meta['output_rom_sha256']:
        parser.error('ROM and adjacent build metadata differ')
    report = (boss if a.case.startswith('boss') else training)(a, meta, digest)
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'checks', 'route')}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
