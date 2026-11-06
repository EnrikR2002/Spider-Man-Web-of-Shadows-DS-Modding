"""Copied-save Freefall inputs, native land/rebound traces and capture."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import hunter_kit_lab, kit_lab as k, vortex_forge_lab as v, wos_tool as w


UNIT = 4096
BASE = k.p.BASE
REBOUND, AIR_DODGE = 1 << 22, 1 << 10
HEIGHTS = {'medium': 26, 'high': 60, 'followup': 26}
CASES = ('low', 'medium', 'high', 'mirror', 'followup', 'red', 'unowned',
         'cancel', 'cancel-no-air-dodge', 'cancel-land', 'cancel-land-back')
SCENES = {'boss': (89, 2, 147), 'floor': (10, 2, 0x6c), 'floor-locked': (10, 2, 0x6c)}
OPTIONS = {b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'}


def audio_capture(lib, pcm):
    av = (ct.c_byte * 40)()
    lib.retro_get_system_av_info.argtypes = [ct.c_void_p]
    lib.retro_get_system_av_info(ct.byref(av))
    lib._wos_audio_sink = lambda frame, data: pcm.append(data)
    return struct.unpack_from('<2d', bytes(av), 24)


def save_audio(out, pcm, rate):
    if pcm:
        with wave.open(str(out / 'mixed.wav'), 'wb') as audio:
            audio.setparams((2, 2, round(rate), 0, 'NONE', 'not compressed'))
            audio.writeframes(b''.join(pcm))


def training(a):
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text(encoding='utf-8'))
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; remeasure the player')
    boot = (Path(profile['captures']) / 'ram-03500.bin').read_bytes()
    black = a.case != 'red'
    live_form = w.u32(boot, k.p.sample(boot)['actor_address'] - BASE + 0x34)
    direction = -1 if a.case == 'mirror' else 1
    added_height = HEIGHTS.get(a.case, 0)
    press = 86 if added_height else 72
    buttons = [] if live_form == black else [dict(start=4, end=10, buttons=['L'])]
    buttons += [dict(start=32, end=36, buttons=['Right' if direction > 0 else 'Left']),
                dict(start=57, end=88, buttons=['B']),
                dict(start=press, end=press + 5, buttons=['Down', 'A'])]
    if a.case == 'followup':
        buttons.append(dict(start=155, end=163, buttons=['Up', 'A']))
    cancel_at = {'cancel': 78, 'cancel-no-air-dodge': 78, 'cancel-land': 100, 'cancel-land-back': 100}.get(a.case)
    if cancel_at is not None:
        buttons.append(dict(start=cancel_at, end=cancel_at + 5, buttons=['Left', 'R'] if a.case.endswith('-back') else ['R']))
    meta = json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    runtime = meta.get('freefall', {}).get('runtime')
    private = {runtime['values'][key] for key in ('DIVE_SCA', 'LAND_SCA')} if runtime else set()
    state = runtime['state'] - BASE if runtime else None
    rows, pcm, audio_rate, targets = [], [], [0., 0.], []

    def observe(frame, lib):
        ptr, ram = k.ram_of(lib)
        enemies = k.enemies(ram)
        if frame < (147 if added_height else 112):
            for e in enemies:
                if e['controller'] and e['state'] in (0, 1, 2, 15):
                    ctl = ptr + e['controller'] - BASE
                    ct.memmove(ctl + 0x14, bytes(4), 4)
                    ct.memmove(ctl + 4, b'\1', 1)
        if frame < 0:
            return
        player = k.p.sample(ram)
        actor, motion = player['actor_address'] - BASE, player['motion_address'] - BASE
        x, y = player['position_q12_candidate']
        if frame == 69:
            fighters = enemies[1:4]  # Native dummy is the first placement; use the three sparring Brutes.
            if len(fighters) != 3:
                raise ValueError('Expected three sparring opponents')
            offsets = {'high': (9, 30, -30), 'mirror': (28, 36, -32)}.get(
                a.case, (4 if added_height else 3, 9, -8))
            for e, offset in zip(fighters, offsets):
                em = w.u32(ram, e['actor'] - BASE + 0x30) - BASE
                k.teleport(ptr, ram, em, x + direction * offset * UNIT, e['position'][1])
                targets.append(e['actor'])
        if added_height and frame == press - 1:
            k.teleport(ptr, ram, motion, x, y + added_height * UNIT)
        if frame == 55:
            audio_rate[:] = audio_capture(lib, pcm)
        wrapper = w.u32(ram, motion + 0x58) - BASE
        slot = w.u32(ram, wrapper + 0x29c)
        for e in enemies:
            e['vy'] = struct.unpack_from('<i', ram, e['actor'] - BASE + 0x1c)[0]
        rows.append(dict(frame=frame, form=w.u32(ram, actor + 0x34),
                         sca=w.u32(ram, wrapper + 0x1c4 + 0x78 * slot),
                         floor=struct.unpack_from('<i', ram, motion + 0x2ac)[0],
                         extent=struct.unpack_from('<3I', ram, motion + 0x2c0),
                         freefall=struct.unpack_from('<IiiI', ram, state) if state is not None else (),
                         enemies=enemies))

    original_rows = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else original_rows(path)
    clear = REBOUND if a.case == 'unowned' else AIR_DODGE if a.case.startswith(('cancel-no-', 'cancel-land')) else 0
    try:
        route, observations = k._run(a.rom, a.tag, buttons, frames=198,
            bits=REBOUND if a.case != 'unowned' else 0, clear=clear,
            sparring=True, start_x=100 * UNIT, save=copied, caps=range(56, 185) if a.capture else (),
            extra_hook=observe, core_options=OPTIONS)
    finally:
        k.rows_from = original_rows
    save_audio(a.out, pcm, audio_rate[1])
    motion = {r['f']: r for r in observations}
    dive = next((r for r in observations if r['st'] == 35), None)
    land = next((r for r in observations if r['st'] == 36), None)
    drawn = {r['sca'] for r in rows} & private
    hp, contacts = {}, []
    for r in rows:
        for e in r['enemies']:
            old = hp.setdefault(e['actor'], e['hp'])
            if e['hp'] < old:
                contacts.append(dict(frame=r['frame'], actor=e['actor'], hp=e['hp'], loss=old-e['hp'],
                                     state=e['state'], vy=e['vy']))
                hp[e['actor']] = e['hp']
    checks = dict(battery_unchanged=actual.read_bytes() == before == copied.read_bytes(),
                  cleanup=not runtime or rows[-1]['freefall'][0] == rows[-1]['freefall'][3] == 0)
    if black:
        checks['real_air_slam'] = dive is not None and press <= dive['f'] <= press + 3
    owned = bool(runtime and black and a.case != 'unowned')
    if owned and cancel_at is not None:
        expected = {'cancel': 52, 'cancel-no-air-dodge': 19, 'cancel-land': 53, 'cancel-land-back': 54}[a.case]
        checks['native_r_exit'] = any(motion[f]['st'] == expected for f in range(cancel_at, cancel_at + 4))
        checks['no_post_cancel_damage'] = all(hit['frame'] < cancel_at for hit in contacts)
    else:
        if black:
            checks['native_floor_landing'] = land is not None and any(r['floor'] > 0 for r in rows[land['f']:land['f']+4])
        else:
            checks['native_red_air_attack'] = any(press <= r['f'] <= press + 8 and r['st'] == 30 for r in observations)
        checks['private_clips'] = drawn == private if owned else not drawn
    if owned and cancel_at is None:
        bonus = max(r['freefall'][2] for r in rows)
        checks['height_bonus'] = (0 < bonus < UNIT if a.case in ('medium', 'followup') else
                                  bonus == UNIT if a.case == 'high' else bonus == 0)
        slam_hits = [hit for hit in contacts if motion[hit['frame']]['st'] == 36]
        if a.case == 'mirror':
            checks['left_facing_whiff_recovers'] = dive is not None and dive['face'] == 0 and not slam_hits
        else:
            checks['native_rebound'] = any(hit['actor'] == targets[0] and hit['vy'] > 0 for hit in slam_hits)
        expected = 0x47c3 + (0x47c3 * bonus >> 11)
        checks['scaled_radius'] = any(r['extent'] == (expected, 0x1ef1, expected) for r in rows)
        if a.case == 'followup':
            checks['juggle_after_rebound'] = bool(slam_hits) and any(
                hit['actor'] == targets[0] and hit['frame'] > slam_hits[0]['frame'] and motion[hit['frame']]['st'] == 45
                for hit in contacts)
    if a.case == 'high':
        checks['extended_range_at_nine_units'] = bool(contacts) == owned
    report = dict(passed=all(checks.values()), checks=checks, case=a.case, inputs=buttons, route=str(route),
                  rom_sha256=w.sha256(a.rom.read_bytes()), battery_sha256=w.sha256(before), frame_rate=audio_rate[0],
                  dive=dive, land=land, contacts=contacts, targets=targets, rows=rows,
                  limits='Latest DSV copy. Training room, disposable ownership and approach fixtures. '
                         'Medium and high preset the air start before the button; the dive, landing, hits and recovery run natively.')
    w.write_json(a.out / 'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'checks', 'contacts', 'route')}), flush=True)
    return 0 if report['passed'] else 1


def scene(a):
    """Use native arrivals, enemy AI and stage objects with a four-word lab entry."""
    from tools import midnight_rework_lab as lab

    actual, before, copied = v.copy_current(a.out)
    room, spawn, flag = SCENES[a.case]
    boss = a.case == 'boss'
    meta = json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    runtime = meta.get('freefall', {}).get('runtime')
    config = meta['creature_forge']['creatures']['conductor']['config']
    patch = a.out / 'entry.json'
    words = ((0x020ed7ac, 1, 1, 0), (0x020ed7b4, 2, 0x46, room),
             (0x020ed7dc, 2, 2, 1), (0x020ed7e0, 3, 0, spawn))
    w.write_json(patch, [dict(addr=at, expect=struct.pack('<I', 0xe3a00000 | reg << 12 | old).hex(),
                             hex=struct.pack('<I', 0xe3a00000 | reg << 12 | new).hex())
                         for at, reg, old, new in words])
    rows, pcm, rate, buttons = [], [], [0., 0.], set()
    jumped, attempt = -1000, -1
    hit_at = None
    last_hp = None
    hits = []

    def observe(frame, lib):
        nonlocal jumped, attempt, hit_at, last_hp
        if frame < 0 and frame != -1300:
            return
        ptr, ram = k.ram_of(lib)
        stats = w.u32(ram, k.STATS_POINTER - BASE) - BASE
        flags = int.from_bytes(ram[stats+0x1c:stats+0x44], 'little')
        if frame < 0:
            ct.memmove(ptr+stats+0x1c, (flags & ~(1 << flag)).to_bytes(40, 'little'), 40)
            return
        if frame == 0:
            rate[:] = audio_capture(lib, pcm)
        hero = k.p.sample(ram)
        actor = hero['actor_address'] - BASE
        motion = hero['motion_address'] - BASE
        state = hero['controller']['state_id_candidate']
        x, y = (q / UNIT for q in hero['position_q12_candidate'])
        black = w.u32(ram, actor+0x34) == 1
        foes = [e for e in k.enemies(ram) if w.u32(ram, e['actor']-BASE+0x40) == config and e['hp'] > 0] if boss else []
        foe = foes[0] if foes else None
        if foe and last_hp is not None and foe['hp'] < last_hp and state == 36:
            hits.append(dict(frame=frame, loss=last_hp-foe['hp'], reaction=foe['state']))
        if foe and hits and frame - hits[-1]['frame'] <= 4 and foe['state'] == 37:
            hit_at = hits[-1]['frame']
        if foe:
            last_hp = foe['hp']
        buttons.clear()
        if not black:
            if frame % 60 < 6:
                buttons.add('L')
        elif boss and hit_at is None:
            age = frame - jumped
            dx = foe['position'][0] / UNIT - x if foe else 20
            cast = (47, 54, 30, 55, 39, 23)[attempt % 6]
            if 0 <= age < cast:
                if age < min(cast - 4, 40):
                    buttons.add('B')
                if abs(dx) > 3:
                    buttons.add('Right' if dx > 0 else 'Left')
            elif cast <= age < cast + 7:
                buttons.update(('Down', 'A'))
            elif age >= 110 and state in (0, 1):
                if abs(dx) > 7:
                    buttons.add('Right' if dx > 0 else 'Left')
                else:
                    jumped = frame
                    attempt += 1
                    buttons.add('B')
        elif not boss:
            if 48 <= frame < 74:
                buttons.add('B')
            if 63 <= frame < 68:
                buttons.update(('Down', 'A'))
        wrapper = w.u32(ram, motion+0x58) - BASE
        slot = w.u32(ram, wrapper+0x29c)
        rows.append(dict(frame=frame, room=w.u32(ram, stats), black=black, pos=(x, y),
                         state=state, sca=w.u32(ram, wrapper+0x1c4+0x78*slot),
                         flag=bool(flags >> flag & 1), buttons=sorted(buttons), boss=foe,
                         freefall=struct.unpack_from('<IiiI', ram, runtime['state']-BASE) if runtime else ()))
        if hit_at is not None and frame >= hit_at + 50:
            return 'stop'

    original_rows = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else original_rows(path)
    lab.JIT = True
    frames = 1400 if boss else 182
    try:
        route, observations = lab.static_warp_runner(k._run)(a.rom, a.tag, [], frames=frames,
            bits=REBOUND, clear=1 << 5 if a.case == 'floor-locked' else 0, patch=str(patch),
            sparring=True, save=copied, caps=range(0, frames) if a.capture else (),
            extra_hook=observe, live_buttons=buttons)
    finally:
        k.rows_from = original_rows
    save_audio(a.out, pcm, rate[1])
    checks = dict(native_room=all(r['room'] == room for r in rows),
                  real_slam=any(r['state'] == 35 for r in rows) and any(r['state'] == 36 for r in rows),
                  battery_unchanged=actual.read_bytes() == before == copied.read_bytes())
    if boss:
        checks['boss_hp_loss_on_slam'] = bool(hits)
        checks['boss_stagger'] = hit_at is not None
        checks['boss_not_launched'] = hit_at is not None and all(r['boss']['state'] not in (39, 41, 44, 48, 49)
                                                               for r in rows[hit_at:hit_at+20] if r['boss'])
    else:
        checks['story_gate'] = not rows[0]['flag'] and rows[-1]['flag'] == (a.case == 'floor')
    report = dict(passed=all(checks.values()), checks=checks, case=a.case, route=str(route), hit_at=hit_at, hits=hits,
                  rom_sha256=w.sha256(a.rom.read_bytes()), battery_sha256=w.sha256(before), frame_rate=rate[0],
                  rows=rows, limits='Latest DSV copy, four entry words, one cleared room flag and disposable ownership. '
                                    'Native arrival, boss AI, movement, contact and breakable object logic.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'checks', 'hit_at', 'route')}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--owned', type=Path, required=True)
    parser.add_argument('--case', choices=(*CASES, *SCENES, 'shop'), required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    if not args.out.resolve().is_relative_to((ROOT / 'work').resolve()):
        parser.error('Lab evidence belongs in work/')
    if args.case == 'shop':
        sys.exit(hunter_kit_lab.shop(args, row=2, bit=22, price=150))
    sys.exit(scene(args) if args.case in SCENES else training(args))
