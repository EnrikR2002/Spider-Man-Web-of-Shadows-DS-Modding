"""Copied-current-battery native Talon Lift/jump/rake/catch, release and fallback controls."""
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
        raise ValueError('Meteor Catch evidence belongs in work/')
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text())
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; remeasure the current player')
    boot = (Path(profile['captures'])/'ram-03500.bin').read_bytes()
    hero = k.p.sample(boot)['actor_address']-k.p.BASE
    form, mirror = int(a.case != 'red'), a.case == 'mirror'
    inputs = [] if w.u32(boot, hero+0x34) == form else [dict(start=4, end=10, buttons=['L'])]
    inputs.append(dict(start=30, end=36, buttons=['Left' if mirror else 'Right']))
    if a.case not in ('ground-a', 'ground-target', 'low'):
        inputs += [dict(start=60, end=66, buttons=['Up', 'A'])]
    if a.case != 'ground-a':
        inputs += [dict(start=60 if a.case == 'low' else 96, end=66 if a.case == 'low' else 128, buttons=['B'])]
    if a.case not in ('ground-a', 'ground-target', 'whiff', 'behind', 'low'):
        inputs += [dict(start=112, end=118, buttons=['Y'])]
    chord = ['Down', 'A'] if a.case == 'air-down-a' else ['Up', 'A'] if a.case == 'air-up-a' else ['X'] if a.case == 'air-x' else ['A']
    activation = 76 if a.case == 'low' else 128
    inputs.append(dict(start=activation, end=180 if a.case == 'hold' else activation+(2 if a.case == 'tap' else 6), buttons=chord))
    if a.case in ('cancel', 'cancel-no-air-dodge', 'cancel-land-no-air-dodge'):
        inputs.append(dict(start=180 if a.case == 'cancel-land-no-air-dodge' else 138,
                           end=186 if a.case == 'cancel-land-no-air-dodge' else 144, buttons=['R']))
    if a.case == 'swap':
        inputs.append(dict(start=138, end=144, buttons=['L']))
    if a.case == 'followup':
        inputs.append(dict(start=180, end=186, buttons=['Up', 'A']))
    meta = json.loads(a.rom.with_suffix('.build.json').read_text())
    private = meta.get('meteor_catch')
    native_case = a.case in ('unowned', 'no-parent', 'red', 'whiff', 'behind', 'ground-target', 'ground-a', 'air-down-a', 'air-up-a', 'air-x')
    if not private and not native_case:
        raise ValueError('Feature cases require Meteor Catch candidate metadata')
    state = private['runtime']['state']-k.p.BASE if private else None
    rows, selected, pcm, rate = [], [], [], [0]

    def hook(frame, lib):
        if frame < -20:
            return
        ptr, ram = k.ram_of(lib)
        if -20 <= frame < 75:
            for enemy in k.enemies(ram):
                if enemy['controller'] and enemy['state'] in (0, 1, 2, 15):
                    ct.memmove(ptr+enemy['controller']-k.p.BASE+0x14, bytes(4), 4)
                    ct.memmove(ptr+enemy['controller']-k.p.BASE+4, b'\x01', 1)
        if frame == 58:
            px, py = k.p.sample(ram)['position_q12_candidate']
            enemies = sorted(k.enemies(ram), key=lambda e: abs(e['position'][0]-px))
            side = -1 if mirror else 1
            for i, enemy in enumerate(enemies):
                gap = (90 if a.case == 'whiff' else -12 if a.case == 'behind' else a.distance) if i == 0 else -75-10*i
                mot = w.u32(ram, enemy['actor']-k.p.BASE+0x30)-k.p.BASE
                k.teleport(ptr, ram, mot, px+round(gap*side*4096), py+(16*4096 if a.case == 'low' and i == 0 else 246))
                if i == 0:
                    selected.append(enemy['actor'])
                    ct.memmove(ptr+enemy['actor']-k.p.BASE+0x44, struct.pack('<2i', 196608, 196608), 8)
                    if a.case == 'low':
                        ct.memmove(ptr+enemy['controller']-k.p.BASE+0x14, struct.pack('<I', 48), 4)
                        ct.memmove(ptr+enemy['controller']-k.p.BASE+4, b'\x01', 1)
                        ct.memmove(ptr+enemy['actor']-k.p.BASE+0x1c, bytes(4), 4)
                        ct.memmove(ptr+mot+0x2a0, bytes(1), 1)
                        ct.memmove(ptr+mot+0x2a8, bytes(12), 12)
        if frame < 0:
            return
        sample = k.p.sample(ram)
        mot, actor = sample['motion_address']-k.p.BASE, sample['actor_address']-k.p.BASE
        ctl = w.u32(ram, mot+0x1f8)-k.p.BASE
        if frame == 126 and a.case == 'lethal':
            ct.memmove(ptr+selected[0]-k.p.BASE+0x44, struct.pack('<I', 0x1800), 4)
            from tools import tasm_kit
            for enemy in k.enemies(ram):
                at = enemy['actor']-k.p.BASE+0x88
                ct.memmove(ptr+at, struct.pack('<I', w.u32(ram, at) & ~4), 4)
            ct.memmove(ptr+tasm_kit.KIT_STATE-k.p.BASE+0x2f0, bytes(8), 8)
        if frame == 138 and a.case in ('hurt', 'death', 'room', 'form', 'target-dead', 'target-reaction'):
            if a.case in ('hurt', 'death'):
                ct.memmove(ptr+ctl+0x14, struct.pack('<I', 63), 4)
                ct.memmove(ptr+ctl+4, b'\x01', 1)
                if a.case == 'death':
                    stats = w.u32(ram, actor+0xe8)-k.p.BASE
                    ct.memmove(ptr+stats+0x78, bytes(4), 4)
            elif a.case == 'room':
                stats = w.u32(ram, actor+0xe8)-k.p.BASE
                ct.memmove(ptr+stats-12, struct.pack('<I', w.u32(ram, stats-12)+1), 4)
            elif a.case == 'form':
                ct.memmove(ptr+actor+0x34, bytes(4), 4)
            elif a.case == 'target-dead':
                ct.memmove(ptr+selected[0]-k.p.BASE+0x44, bytes(4), 4)
            else:
                target = w.u32(ram, state+8)-4-k.p.BASE
                controller = w.u32(ram, w.u32(ram, target+0x30)-k.p.BASE+0x1f8)-k.p.BASE
                ct.memmove(ptr+controller+0x14, struct.pack('<I', 42), 4)
        if frame == 58:
            info = (ct.c_byte*40)()
            lib.retro_get_system_av_info.argtypes = [ct.c_void_p]
            lib.retro_get_system_av_info(ct.byref(info))
            rate[0] = round(struct.unpack_from('<d', bytes(info), 32)[0])
            lib._wos_audio_sink = lambda f, data: pcm.append(data) if k.TRAINING_START+100 <= f < k.TRAINING_START+230 else None
        enemies = k.enemies(ram)
        for enemy in enemies:
            em = w.u32(ram, enemy['actor']-k.p.BASE+0x30)-k.p.BASE
            enemy['floor_normal_y'] = struct.unpack_from('<i', ram, em+0x2ac)[0]
            enemy['velocity'] = list(struct.unpack_from('<2i', ram, enemy['actor']-k.p.BASE+0x18))
        rows.append(dict(frame=frame, state=w.u32(ram, ctl+0x14), action=w.u32(ram, mot+0x258),
            clock=w.u32(ram, mot+0x178), pos=sample['position_q12_candidate'], facing=sample['facing_candidate'],
            floor_normal_y=struct.unpack_from('<i', ram, mot+0x2ac)[0],
            velocity=list(struct.unpack_from('<2i', ram, actor+0x18)),
            meteor=list(struct.unpack_from('<32I', ram, state)) if state is not None else [0]*32, enemies=enemies))

    native = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    try:
        route, observations = k._run(a.rom, a.tag, inputs, frames=270, bits=0,
            clear=1 << 10 if a.case in ('cancel-no-air-dodge', 'cancel-land-no-air-dodge') else 0,
            clear2=(1 << 21) | (1 << 22), bits2=(0 if a.case == 'no-parent' else 1 << 21) | (0 if a.case == 'unowned' else 1 << 22),
            sparring=True, start_x=(224 if a.case == 'wall' else 100)*4096, save=copied,
            caps=tuple(range(58 if a.case == 'low' else 105, 245)) if a.case in ('regular', 'mirror', 'wall', 'hold', 'followup', 'low') else (125, 134, 140, 160, 200, 260),
            rams=(127, 138, 160, 176, 184, 220), extra_hook=hook,
            core_options={b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'})
    finally:
        k.rows_from = native
    if rate[0] and pcm:
        with wave.open(str(a.out/'mixed.wav'), 'wb') as audio:
            audio.setparams((2, 2, rate[0], 0, 'NONE', 'not compressed'))
            audio.writeframes(b''.join(pcm))
    active = [r for r in rows if r['meteor'][6]]
    focus = next((r['meteor'][2]-4 for r in active if r['meteor'][2]), selected[0])
    foes = [next((e for e in r['enemies'] if e['actor'] == focus), None) for r in rows]
    drops = [dict(frame=i, hp=e['hp'], phase=rows[i]['meteor'][6], state=e['state'],
                  at_impact=any(r['meteor'][12] > rows[i-1]['meteor'][12] for r in rows[i:i+3]))
             for i, e in enumerate(foes) if i >= activation and e and foes[i-1] and e['hp'] < foes[i-1]['hp']]
    checks = dict(actual_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before,
        cleanup_complete=all(rows[-1]['meteor'][i] == 0 for i in (0, 1, 2, 6, 28)),
        collision_bounds=all(3.4*4096 <= r['pos'][0] <= 237*4096 for r in rows))
    if native_case:
        checks['no_meteor_started'] = not active
    else:
        checks['catch_started_once'] = rows[-1]['meteor'][15] == 1
        checks['native_air_entry'] = any((r['state'] == 15 if a.case == 'low' else r['state'] == 51 and 1 <= r['action'] <= 4)
            for r in rows if activation-16 <= r['frame'] < activation)
        interrupted = a.case in ('cancel', 'cancel-no-air-dodge', 'cancel-land-no-air-dodge', 'swap', 'hurt', 'death', 'room', 'form', 'target-dead', 'target-reaction')
        if interrupted:
            late = a.case == 'cancel-land-no-air-dodge'
            checks['interruption_releases'] = not any(r['meteor'][6] for r in rows if r['frame'] >= (183 if late else 141))
            checks['no_impact_after_release'] = rows[-1]['meteor'][12] == (rows[180]['meteor'][12] if late else 0)
            if late:
                checks['native_ground_evade_without_paid_air_dodge'] = any(r['state'] in (53, 54, 57) for r in rows if 180 <= r['frame'] <= 190)
        else:
            impacts = [r for r in rows if r['meteor'][12]]
            checks['one_actual_floor_impact'] = rows[-1]['meteor'][12] == 1 and any(e and e['floor_normal_y'] > 0
                for r, e in zip(rows, foes) if impacts and impacts[0]['frame']-2 <= r['frame'] <= impacts[0]['frame'])
            checks['actual_impact_hp_loss'] = any(d['at_impact'] for d in drops)
            if a.case == 'lethal':
                checks['native_lethal_impact_cleans_up'] = any(e is None or e['hp'] <= 0 for r, e in zip(rows, foes) if r['frame'] > 180)
            else:
                checks['one_small_bounce'] = any(r['meteor'][12] and e and e['state'] == 41 and 0 < e['velocity'][1] <= 0x1800
                    for r, e in zip(rows, foes))
            checks['no_damage_during_grab'] = not any(d['phase'] in (1, 2) and not d['at_impact'] for d in drops)
            if a.case == 'followup':
                checks['chosen_talon_lift_continues'] = any(r['state'] == 45 and r['frame'] > 165 for r in rows)
                checks['single_chosen_lift_hits_bounced_foe'] = any(d['frame'] > impacts[0]['frame']
                    and rows[d['frame']]['state'] == 45 for d in drops) if impacts else False
    report = dict(passed=all(checks.values()), case=a.case, checks=checks, damage=drops, rows=rows,
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before), route=str(route), sequence=k.seq(observations),
        limits='Latest actual DSV copy, normal Continue/Test Upgrades. Disposable ownership/form, initial layout/target HP '
        'and idle-enemy prefix through74; launch/jump/rake/catch then use native inputs, AI, damage, gravity and collision. '
        'The low case begins with a disclosed falling-foe position/state/velocity fixture at58, then a real small B jump and A; '
        'lethal presets target HP at126 and clears training immortality flags/counters before native A; '
        'named interruption cases inject one RAM event. '
        'Training heals/immortality apply. No save adoption, '
        'campaign balance, player verdict or hardware pacing claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'case', 'checks', 'damage', 'route')}), flush=True)
    return 0 if report['passed'] else 1


def boss(a):
    """Real-input air A against the native Conductor; no boss motion/HP/state fixture."""
    import os
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge, midnight_rework_lab as lab
    from tools import midnight_walk as mw, owned_player_lab
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Meteor Catch evidence belongs in work/')
    actual, before, copied = v.copy_current(a.out)
    os.environ['WOS_CHAPTER_LAB_SAVE'] = str(copied)
    owned_player_lab.install(a.owned)
    q.configure_rooms(a.rom)
    forge.OUT, q.OUT, q.RUN_TAG = a.out, a.out, ''
    forge.install(a.rom, 6)
    meta = json.loads(a.rom.with_suffix('.build.json').read_text())
    feature = meta.get('meteor_catch')
    state = feature['runtime']['state']-k.p.BASE if feature else None
    config = meta['hunter_kit']['runtime']['values']['BOSS_CONFIG']
    native, rows, started = lab.Walker.tick, [], [-1000]

    def tick(self, frame, lib):
        if frame == -1100:
            ptr, ram = k.ram_of(lib)
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            flags = int.from_bytes(ram[stats+0x1c:stats+0x44], 'little') & ~(1<<147)
            ct.memmove(ptr+stats+0x1c, flags.to_bytes(40, 'little'), 40)
        native(self, frame, lib)
        if frame < 0:
            return
        ptr, ram = k.ram_of(lib)
        if frame == 0:
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            ct.memmove(ptr+stats+0x14, struct.pack('<I', w.u32(ram, stats+0x14) | 3<<21), 4)
        current = self.last_state
        if not current or not current.pos:
            return
        foes = [e for e in current.enemies if w.u32(ram, e['actor']-k.p.BASE+0x40) == config]
        self.buttons.clear()
        if not current.black:
            if frame % 60 < 6:
                self.buttons.add('L')
        elif not foes:
            self.buttons.add('Right')
        else:
            enemy = min(foes, key=lambda e: abs(e['position'][0]/4096-current.pos[0]))
            dx = enemy['position'][0]/4096-current.pos[0]
            age = frame-started[0]
            facing = k.p.sample(ram)['facing_candidate']
            if age < 32:
                if age < 8:
                    self.buttons.add('B')
                if 12 <= age < 18:
                    self.buttons.add('A')
            elif abs(dx) > 8 or facing != int(dx >= 0):
                self.buttons.add('Right' if dx >= 0 else 'Left')
            elif current.state in (0, 1) and age >= 90:
                started[0] = frame
                self.buttons.add('B')
        sample = k.p.sample(ram)
        mot = sample['motion_address']-k.p.BASE
        rows.append(dict(frame=frame, state=current.state, action=w.u32(ram, mot+0x258),
            pos=sample['position_q12_candidate'], buttons=sorted(self.buttons), enemies=foes,
            meteor=list(struct.unpack_from('<32I', ram, state)) if state is not None else [0]*32))

    lab.Walker.tick = tick
    native_prefix = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native_prefix(path)
    try:
        route = q.run(a.rom, a.tag, 'ML_Venom', 2, [mw.wait(700)], combat=True, heal=True)
    finally:
        lab.Walker.tick = native
        k.rows_from = native_prefix
    checks = dict(actual_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before,
        real_boss_encounter=any(r['enemies'] for r in rows),
        native_air_a_requested=any('A' in r['buttons'] and r['state'] in (15, 19) for r in rows),
        no_heavy_catch=not any(r['meteor'][6] for r in rows),
        heavy_never_launched=all(e['state'] not in (39, 42, 44, 45, 46, 48, 49) for r in rows for e in r['enemies']))
    report = dict(passed=all(checks.values()), case='boss', checks=checks, rows=rows, route=route['captures'],
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before),
        limits='Latest actual Battery copy, measured ownership/XP, disposable room arrival, cleared already-earned '
        'boss flag147, Meteor/Sky Rake RAM bits and player healing. Approach/B/A/L inputs, boss AI, HP, poses '
        'and collision are native; no boss position/HP/state/velocity writes. No victory or difficulty claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'checks', 'route')}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--owned', type=Path, required=True)
    p.add_argument('--tag', required=True)
    p.add_argument('--distance', type=float, default=7)
    p.add_argument('--case', default='regular', choices=('regular', 'mirror', 'wall', 'hold', 'tap', 'followup', 'low', 'lethal', 'unowned', 'no-parent', 'red',
        'whiff', 'behind', 'ground-target', 'ground-a', 'air-down-a', 'air-up-a', 'air-x', 'cancel', 'cancel-no-air-dodge', 'cancel-land-no-air-dodge', 'swap',
        'hurt', 'death', 'room', 'form', 'target-dead', 'target-reaction', 'boss', 'shop'))
    a = p.parse_args()
    if a.case == 'shop':
        from tools.hunter_kit_lab import shop
        sys.exit(shop(a, row=10, bit=86, price=200))
    sys.exit(boss(a) if a.case == 'boss' else run(a))
