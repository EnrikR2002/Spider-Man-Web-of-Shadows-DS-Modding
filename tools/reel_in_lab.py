"""Copied-latest-battery Reel In, chosen Sky Rake, native inputs and interruption controls."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import kit_lab as k, vortex_forge_lab as v, wos_tool as w


def run(a):
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Reel In evidence belongs in work/')
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text(encoding='utf-8'))
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; remeasure current player')
    boot = (Path(profile['captures'])/'ram-03500.bin').read_bytes()
    hero = k.p.sample(boot)['actor_address']-k.p.BASE
    form = 0 if a.case == 'red' else 1
    inputs = [] if w.u32(boot, hero+0x34) == form else [dict(start=4, end=10, buttons=['L'])]
    mirror = a.case in ('mirror', 'wall')
    inputs.append(dict(start=30, end=36, buttons=['Left' if mirror else 'Right']))
    if a.case == 'extend':
        inputs.append(dict(start=60, end=66, buttons=['Up', 'A']))
    if a.case not in ('ground', 'ground-a'):
        inputs.append(dict(start=96 if a.case == 'extend' else 60,
                           end=128 if a.case == 'extend' else 92, buttons=['B']))
    if a.case == 'extend':
        inputs.append(dict(start=112, end=118, buttons=['Y']))
    chord = ['A'] if a.case in ('air-a', 'ground-a') else ['X'] if a.case == 'air-x' else ['Down', 'A'] if a.case == 'air-down-a' else ['Up', 'A']
    activation = 128 if a.case == 'extend' else 112 if a.case == 'falling' else 76
    inputs.append(dict(start=activation, end=125 if a.case == 'hold' else activation+6, buttons=chord))
    if a.case in ('cancel', 'cancel-no-air-dodge'):
        inputs.append(dict(start=86, end=92, buttons=['R']))
    if a.case == 'swap':
        inputs.append(dict(start=86, end=92, buttons=['L']))
    if a.case in ('regular', 'mirror', 'near', 'hold', 'wall', 'below', 'below-behind'):
        inputs += [dict(start=t, end=t+6, buttons=['Y']) for t in (98, 114, 130, 146)]
    if a.case == 'extend':
        inputs += [dict(start=t, end=t+6, buttons=['Y']) for t in (150, 166, 182, 198)]
    meta = json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    private = meta.get('reel_in')
    native_case = a.case in ('unowned', 'no-parent', 'red', 'whiff', 'ground', 'ground-a', 'air-a', 'air-down-a', 'air-x')
    if not private and not native_case:
        raise ValueError('Feature cases require Reel In candidate metadata')
    state = private['runtime']['state']-k.p.BASE if private else None
    rows, selected, pcm, rate = [], [], [], [0]

    def hook(frame, lib):
        if frame < -20:
            return
        ptr, ram = k.ram_of(lib)
        if -20 <= frame < 75:
            for e in k.enemies(ram):
                if e['controller'] and e['state'] in (0, 1, 2, 15):
                    ct.memmove(ptr+e['controller']-k.p.BASE+0x14, bytes(4), 4)
                    ct.memmove(ptr+e['controller']-k.p.BASE+4, b'\x01', 1)
        if frame == 58:
            px, py = k.p.sample(ram)['position_q12_candidate']
            enemies = sorted(k.enemies(ram), key=lambda e: abs(e['position'][0]-px))
            side = -1 if mirror else 1
            for i, e in enumerate(enemies):
                gap = (90 if a.case == 'whiff' else 0 if a.case == 'below' else
                       -6 if a.case == 'below-behind' else 6 if a.case == 'near' else a.distance) if i == 0 else -75-10*i
                if a.case == 'extend' and i < 2:
                    gap = 7 if i == 0 else 32
                mot = w.u32(ram, e['actor']-k.p.BASE+0x30)-k.p.BASE
                k.teleport(ptr, ram, mot, px+round(gap*side*4096), py+246)
                if i == 0:
                    selected.append(e['actor'])
                if i == 0 or (a.case == 'extend' and i == 1):
                    ct.memmove(ptr+e['actor']-k.p.BASE+0x44, struct.pack('<2i', 196608, 196608), 8)
        if frame < 0:
            return
        sample = k.p.sample(ram)
        mot, actor = sample['motion_address']-k.p.BASE, sample['actor_address']-k.p.BASE
        ctl = w.u32(ram, mot+0x1f8)-k.p.BASE
        if frame == 86:
            if a.case in ('hurt', 'death'):
                ct.memmove(ptr+ctl+0x14, struct.pack('<I', 63), 4)
                ct.memmove(ptr+ctl+4, b'\x01', 1)
                if a.case == 'death':
                    stats = w.u32(ram, actor+0xe8)-k.p.BASE
                    ct.memmove(ptr+stats+0x78, bytes(4), 4)
            if a.case == 'room':
                stats = w.u32(ram, actor+0xe8)-k.p.BASE
                ct.memmove(ptr+stats-12, struct.pack('<I', w.u32(ram, stats-12)+1), 4)
            if a.case == 'form':
                ct.memmove(ptr+actor+0x34, bytes(4), 4)
            if a.case == 'target-dead':
                ct.memmove(ptr+selected[0]-k.p.BASE+0x44, bytes(4), 4)
        if frame == 60:
            info = (ct.c_byte*40)()
            lib.retro_get_system_av_info.argtypes = [ct.c_void_p]
            lib.retro_get_system_av_info(ct.byref(info))
            rate[0] = round(struct.unpack_from('<d', bytes(info), 32)[0])
            lib._wos_audio_sink = lambda f, data: pcm.append(data) if k.TRAINING_START+60 <= f < k.TRAINING_START+180 else None
        rows.append(dict(frame=frame, state=w.u32(ram, ctl+0x14), action=w.u32(ram, mot+0x258),
            clock=w.u32(ram, mot+0x178), pos=sample['position_q12_candidate'],
            floor_normal_y=struct.unpack_from('<i', ram, mot+0x2ac)[0],
            velocity=list(struct.unpack_from('<2i', ram, actor+0x18)),
            reel=list(struct.unpack_from('<32I', ram, state)) if state is not None else [0]*32, enemies=k.enemies(ram)))

    native = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    try:
        route, obs = k._run(a.rom, a.tag, inputs, frames=260 if a.case == 'extend' else 210, bits=0,
            clear=1 << 10 if a.case == 'cancel-no-air-dodge' else 0,
            clear2=(1 << 19) | (1 << 20),
            bits2=((0 if a.case == 'no-parent' else 1 << 19) |
                   (0 if a.case == 'unowned' else 1 << 20) | (1 << 21)),
            sparring=True, start_x=(224 if a.case == 'wall' else 100)*4096, save=copied,
            caps=tuple(range(58, 248)) if a.case == 'extend' else tuple(range(58, 180)) if a.case in ('regular', 'mirror', 'near', 'wall', 'hold', 'below', 'below-behind', 'falling')
                 else (74, 80, 86, 90, 120, 170), rams=(75, 86, 102, 170), extra_hook=hook,
            core_options={b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'})
    finally:
        k.rows_from = native
    if rate[0] and pcm:
        with wave.open(str(a.out/'mixed.wav'), 'wb') as audio:
            audio.setparams((2, 2, rate[0], 0, 'NONE', 'not compressed'))
            audio.writeframes(b''.join(pcm))
    focus = next((r['reel'][2]-4 for r in rows if r['reel'][6] and r['reel'][2]), selected[0])
    foes = [next((e for e in r['enemies'] if e['actor'] == focus), None) for r in rows]
    active = [r for r in rows if r['reel'][6]]
    arrivals = [r for r in active if r['reel'][12]]
    losses = [dict(frame=i, state=rows[i]['state'], action=rows[i]['action'], hp=e['hp'],
                   fixture=a.case == 'target-dead' and 86 <= i <= 88 and e['hp'] == 0)
              for i, e in enumerate(foes) if i > 75 and e and foes[i-1] and e['hp'] < foes[i-1]['hp']]
    checks = dict(actual_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before,
        cleanup_complete=all(rows[-1]['reel'][i] == 0 for i in (0, 1, 2, 6, 24, 28)),
        collision_bounds=all(3.4*4096 <= r['pos'][0] <= 237*4096 for r in rows))
    if native_case:
        checks['no_reel_started'] = not active
    else:
        checks['reel_started_once'] = rows[-1]['reel'][15] == 1
        checks['scarlet_line_lived'] = any(r['reel'][24] for r in active)
        if a.case in ('regular', 'mirror', 'near', 'hold', 'wall', 'below', 'below-behind', 'extend'):
            checks['actual_airborne_arrival'] = any(r['state'] == 51 and e and e['state'] == 39 and
                abs(e['position'][0]-r['pos'][0]) <= 9*4096 and
                abs(e['position'][1]-r['pos'][1]) <= 8*4096 for r, e in zip(rows, foes) if r in arrivals)
            checks['chosen_air_y_damages'] = any(d['frame'] >= activation and d['state'] == 51 and 1 <= d['action'] <= 4 for d in losses)
            if a.case == 'extend':
                starts = [i for i, r in enumerate(rows) if r['reel'][6] and i and not rows[i-1]['reel'][6]]
                checks['extends_a_real_native_air_combo'] = any(rows[i-1]['state'] == 51 and
                    1 <= rows[i-1]['action'] <= 4 for i in starts)
        elif a.case == 'falling':
            contact = next((r['frame'] for r in rows if r['frame'] > 112 and r['floor_normal_y'] > 0), None)
            checks['native_landing_releases'] = contact is not None and any(r['state'] == 24 and not r['reel'][6]
                for r in rows if contact <= r['frame'] <= contact+2)
        else:
            checks['interruption_releases'] = not any(r['reel'][6] for r in rows if r['frame'] >= 89)
            if a.case in ('cancel', 'cancel-no-air-dodge'):
                checks['r_leaves_native_air_state'] = any(r['state'] != 51 for r in rows if 86 <= r['frame'] <= 89)
        checks['utility_zero_damage'] = not any(rows[d['frame']]['reel'][6] and not d['fixture'] for d in losses)
    report = dict(passed=all(checks.values()), case=a.case, checks=checks,
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before), route=str(route),
        sequence=k.seq(obs), damage=losses, rows=rows,
        limits='Latest actual DSV copy; normal Continue/Test Upgrades. Disposable ownership/form, initial hero/target '
        'layout and target HP, idle-enemy prefix through74. Subsequent movement/AI/hits are native; '
        'named interruption cases inject one RAM interruption. Training heals/immortality apply. '
        'No research save adoption, campaign balance, player verdict or hardware pacing claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'case', 'checks', 'damage', 'route')}), flush=True)
    return 0 if report['passed'] else 1


def boss(a):
    """Jump/reel/rake the live Conductor; never move or change the enemy in RAM."""
    import os
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge, midnight_rework_lab as lab
    from tools import midnight_walk as mw, owned_player_lab
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Reel In evidence belongs in work/')
    actual, before, copied = v.copy_current(a.out)
    os.environ['WOS_CHAPTER_LAB_SAVE'] = str(copied)
    owned_player_lab.install(a.owned)
    q.configure_rooms(a.rom)
    forge.OUT, q.OUT, q.RUN_TAG = a.out, a.out, ''  # The label already carries the tag; keep native core paths short.
    forge.install(a.rom, 6)
    meta = json.loads(a.rom.with_suffix('.build.json').read_text())
    config = meta['creature_forge']['creatures']['conductor']['config']
    private = meta['reel_in']['runtime']['state']-k.p.BASE
    native, rows, started = lab.Walker.tick, [], [-1000]

    def tick(self, frame, lib):
        if frame == -1100:  # Current Test Upgrades entry is at1980, before the legacy2040 flag fixture.
            ptr, ram = k.ram_of(lib)
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            flags = int.from_bytes(ram[stats+0x1c:stats+0x44], 'little') & ~(1 << 147)
            ct.memmove(ptr+stats+0x1c, flags.to_bytes(40, 'little'), 40)
        native(self, frame, lib)
        if frame < 0:
            return
        ptr, ram = k.ram_of(lib)
        if frame == 0:
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            ct.memmove(ptr+stats+0x14, struct.pack('<I', w.u32(ram, stats+0x14) | (7 << 19)), 4)
        current = self.last_state
        if not current or not current.pos:
            return
        if frame in (82, 84, 86, 94, 96, 98):
            w.atomic_write(a.out/f'pose-{frame:03}.ram', ram)
        self.buttons.clear()
        foes = [e for e in current.enemies if w.u32(ram, e['actor']-k.p.BASE+0x40) == config]
        reel = list(struct.unpack_from('<32I', ram, private))
        if not current.black:
            if frame % 60 < 6:
                self.buttons.add('L')
        elif foes:
            e = min(foes, key=lambda e: abs(e['position'][0]/4096-current.pos[0]))
            dx = e['position'][0]/4096-current.pos[0]
            facing = k.p.sample(ram)['facing_candidate']
            age = frame-started[0]
            if a.case != 'boss' and frame < 160:
                self.buttons.add('Right')
                if frame % 50 < 10:
                    self.buttons.add('B')
            elif age < 96:
                if age < 6:
                    self.buttons.add('B')
                cast_start = 4 if a.case != 'boss' else 14
                if cast_start <= age < cast_start+6:
                    self.buttons.update(('Up', 'A'))
                if reel[6] and reel[12] and a.case == 'boss':
                    self.buttons.add('Y')
                elif not reel[6] and 38 <= age < 90 and (age-38) % 16 < 6:
                    self.buttons.add('Y')
            elif abs(dx) > (34 if a.case != 'boss' else 24) or facing != int(dx >= 0):
                self.buttons.add('Right' if dx >= 0 else 'Left')
            elif current.state in (0, 1) and age >= 130 and frame < 850:
                started[0] = frame
                self.buttons.add('B')
        elif current.pos[0] < 100:
            self.buttons.add('Right')
        sample = k.p.sample(ram)
        mot = sample['motion_address']-k.p.BASE
        line = reel[24]-4-k.p.BASE if reel[24] else None
        rows.append(dict(frame=frame, state=current.state, action=w.u32(ram, mot+0x258),
            pos=sample['position_q12_candidate'], reel=reel, enemies=foes,
            line_offset=list(struct.unpack_from('<2i', ram, line+0x80)) if line is not None else None))

    lab.Walker.tick = tick
    native_prefix = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native_prefix(path)
    try:
        route = q.run(a.rom, a.tag, 'ML_Venom', 2, [mw.wait(1000)], combat=True, heal=True)
    finally:
        lab.Walker.tick = native
        k.rows_from = native_prefix
    previous, drops = {}, []
    for r in rows:
        for e in r['enemies']:
            if e['actor'] in previous and e['hp'] < previous[e['actor']]:
                drops.append(dict(frame=r['frame'], state=r['state'], action=r['action'],
                    reel_active=r['reel'][6], hp=e['hp']))
            previous[e['actor']] = e['hp']
    active = [r for r in rows if r['reel'][6]]
    checks = dict(reel_starts=bool(active), scarlet_line=any(r['reel'][24] for r in active),
        heavy_zip=any(r['reel'][13] and r['reel'][14] for r in active),
        actual_arrival=any(r['reel'][12] for r in active),
        utility_zero_damage=not any(d['reel_active'] for d in drops),
        chosen_air_y_damages=any(d['state'] == 51 and 1 <= d['action'] <= 4 and not d['reel_active'] for d in drops),
        heavy_never_launched=all(e['state'] not in (39, 42, 44, 45, 46, 48, 49) for r in rows for e in r['enemies']),
        source_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before,
        cleanup_complete=bool(rows) and all(rows[-1]['reel'][i] == 0 for i in (0, 1, 2, 6, 24, 28)))
    if a.case == 'boss-airborne':
        checks['line_follows_visible_leap'] = any(r['line_offset'] and r['line_offset'][1] > 8*4096
            and any(e['action'] in (38, 111) for e in r['enemies']) for r in active)
    report = dict(passed=all(checks.values()), case=a.case, checks=checks, route=route['captures'], damage=drops, rows=rows,
        pose_fixture=meta.get('pose_fixture'),
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before),
        limits='Copied latest actual DSV, measured player, disposable room arrival/ownership, cleared already-earned '
        'boss flag147 and player healing. Subsequent L/B/Up+A/Y/directions, boss HP/position/state/AI and collision '
        'are native except an explicitly declared pose_fixture in diagnostic ROM metadata. No enemy position/HP/velocity/clock '
        'writes. No save adoption, native mini-boss coverage, victory or balance claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'checks', 'damage', 'route')}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--owned', type=Path, required=True)
    p.add_argument('--tag', required=True)
    p.add_argument('--distance', type=float, default=30)
    p.add_argument('--case', default='regular', choices=('regular', 'mirror', 'near', 'wall', 'hold', 'below', 'below-behind', 'falling', 'extend',
        'unowned', 'no-parent', 'red', 'whiff', 'ground', 'ground-a', 'air-a', 'air-down-a', 'air-x', 'cancel',
        'cancel-no-air-dodge', 'swap', 'hurt', 'death', 'room', 'form', 'target-dead', 'boss', 'boss-airborne', 'shop'))
    a = p.parse_args()
    if a.case == 'shop':
        from tools.hunter_kit_lab import shop
        sys.exit(shop(a, row=9, bit=84, price=150))
    sys.exit(boss(a) if a.case.startswith('boss') else run(a))
