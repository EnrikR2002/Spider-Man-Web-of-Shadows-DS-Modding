"""Copied-current-save Web Yank contacts, prompt/ownership controls and cleanup."""
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
        raise ValueError('Hunter kit lab evidence must stay in work/')
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text(encoding='utf-8'))
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; measure current player again')
    boot = (Path(profile['captures'])/'ram-03500.bin').read_bytes()
    hero = k.p.sample(boot)['actor_address']-k.p.BASE
    desired = 0 if a.case == 'red' else 1
    inputs = [] if w.u32(boot, hero+0x34) == desired else [dict(start=4, end=10, buttons=['L'])]
    mirror = a.case == 'mirror'
    inputs.append(dict(start=30, end=36, buttons=['Left' if mirror else 'Right']))
    inputs.append(dict(start=60, end=145 if a.case == 'hold' else 66,
                       buttons=['Up', 'X'] if a.case == 'up' else ['X']))
    if a.case == 'cancel':
        inputs.append(dict(start=70, end=76, buttons=['R']))
    if a.case == 'swap':
        inputs.append(dict(start=70, end=76, buttons=['L']))
    if a.case == 'air':
        inputs.append(dict(start=46, end=76, buttons=['B']))
    if a.case == 'followup':
        inputs.append(dict(start=94, end=100, buttons=['Y']))
    if a.case == 'repeat':
        inputs += [dict(start=t, end=t+6, buttons=['X']) for t in (115, 165, 215)]
    if a.case == 'moving':
        inputs.append(dict(start=30, end=75, buttons=['Right']))
    meta = json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    rt = meta['hunter_kit']['runtime']
    state = rt['state']-k.p.BASE
    rows, injected, pcm, rate = [], False, [], [0]

    def hook(frame, lib):
        nonlocal injected
        ptr, ram = k.ram_of(lib)
        if frame == 58:
            # One pre-input layout fixture; actual cast distance/trajectory are recorded afterward.
            sample = k.p.sample(ram)
            px, py = sample['position_q12_candidate']
            fighters = sorted(k.enemies(ram), key=lambda e: abs(e['position'][0]-(px+dx*4096)))
            for e, gap in zip(fighters, (dx, -75*side, -85*side, -95*side)):
                motion = w.u32(ram, e['actor']-k.p.BASE+0x30)-k.p.BASE
                k.teleport(ptr, ram, motion, px+round(gap*4096), py+246)
            ptr, ram = k.ram_of(lib)
        if a.case in ('regular', 'mirror', 'close', 'up', 'followup') and frame == 50:
            info = (ct.c_byte*40)()
            lib.retro_get_system_av_info.argtypes = [ct.c_void_p]
            lib.retro_get_system_av_info(ct.byref(info))
            rate[0] = round(struct.unpack_from('<d', bytes(info), 32)[0])
            lib._wos_audio_sink = lambda f, data: pcm.append(data) if k.TRAINING_START+50 <= f < k.TRAINING_START+140 else None
        if a.case in ('regular', 'mirror', 'close', 'up', 'followup') and 50 <= frame < 140 and frame % 2 == 0:
            video, pixel = lib._wos_video
            w.atomic_write(a.out/'motion'/f'frame-{(frame-50)//2:03d}.png', k.emu.frame_png(video, pixel))
        if -20 <= frame < 70:
            for enemy in k.enemies(ram):
                if enemy['controller'] and enemy['state'] in (0, 1, 2, 15):
                    ct.memmove(ptr+enemy['controller']-k.p.BASE+0x14, bytes(4), 4)
                    ct.memmove(ptr+enemy['controller']-k.p.BASE+4, b'\x01', 1)
        if frame < 0:
            return
        private = list(struct.unpack_from('<32I', ram, state))
        if frame == 73 and private[6] and a.case in ('hurt', 'stale'):
            if a.case == 'hurt':
                ct.memmove(ptr+private[1]-k.p.BASE+0x14, struct.pack('<I', 63), 4)
                ct.memmove(ptr+private[1]-k.p.BASE+4, b'\x01', 1)
            else:
                # Change the captured identity, preserving native intrusive links and actors.
                ct.memmove(ptr+state+20, bytes(4), 4)
            injected = True
        sample = k.p.sample(ram)
        mot = sample['motion_address']-k.p.BASE
        wrapper = w.u32(ram, mot+0x58)-k.p.BASE
        slot = w.u32(ram, wrapper+0x29c)
        rows.append(dict(frame=frame, private=private, hero_weak_head=w.u32(ram, sample['actor_address']-k.p.BASE+4),
            form=w.u32(ram, sample['actor_address']-k.p.BASE+0x34),
            hero_pos=sample['position_q12_candidate'], hero_state=sample['controller']['state_id_candidate'],
            sca=w.u32(ram, wrapper+0x1c4+0x78*slot), enemies=k.enemies(ram)))

    native = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    dx = 6 if a.case == 'close' else 110 if a.case == 'whiff' else getattr(a, 'distance', 42)
    if mirror:
        dx = -dx
    side = -1 if mirror else 1
    try:
        route, obs = k._run(a.rom, a.tag, inputs, frames=290 if a.case == 'repeat' else 180, bits=0,
            bits2=0 if a.case == 'unowned' else 1<<19, clear2=1<<19, sparring=True,
            start_x=100*4096, place=tuple((round(d*4096), 246) for d in (dx, -75*side, -85*side, -95*side)),
            save=copied, caps=tuple(range(60, 112, 4)), rams=(62, 74, 98), extra_hook=hook,
            core_options={b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'})
    finally:
        k.rows_from = native
    maximum = lambda word: max(r['private'][word] for r in rows)
    starts, yanks, strikes, heavies = maximum(15), maximum(16), maximum(17), maximum(18)
    target_refs = [r['private'][2]-4 for r in rows if r['private'][2]]
    target = target_refs[0] if target_refs else None
    foes = [next((e for e in r['enemies'] if e['actor'] == target), None) for r in rows]
    damage = [dict(frame=i, hp=e['hp']) for i, e in enumerate(foes)
              if i and e and foes[i-1] and e['hp'] < foes[i-1]['hp']]
    active = [r for r in rows if r['private'][6] == 2]
    pull_sample = next((r for r in rows if r['private'][20]), None)
    pull_distance = None
    if pull_sample:
        pose = next(r for r in obs if r['f'] == pull_sample['frame'])
        foe = next((e for e in pull_sample['enemies'] if e['actor'] == target), None)
        if foe:
            pull_distance = abs(foe['position'][0]-pose['pos'][0])/4096
    checks = dict(actual_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before,
                  cleanup_complete=rows[-1]['private'][6] == rows[-1]['private'][2] == rows[-1]['private'][24] == 0)
    if a.case in ('unowned', 'red', 'whiff', 'air'):
        checks['no_custom_activation'] = starts == 0
    else:
        checks['owned_black_cast'] = starts >= 1
        checks['private_clip_selected'] = any(r['sca'] == rt['values'].get('SHORT_SCA', rt['values']['YANK_SCA'])
            if r['private'][22] else r['sca'] == rt['values']['YANK_SCA'] for r in active)
        if a.case in ('cancel', 'swap', 'hurt', 'stale'):
            checks['no_rake_after_interruption'] = strikes == 0 and not damage
            if a.case == 'cancel':
                checks['native_r_exit'] = any(70 <= r['f'] <= 76 and r['st'] in (52, 53, 54, 55, 57) for r in obs)
            if a.case in ('hurt', 'stale'):
                checks['fixture_applied'] = injected
        else:
            checks['actual_rake_damage'] = strikes >= 1 and bool(damage)
            if a.case == 'up':
                checks['rake_launches'] = any(e and e['state'] == 39 for e in foes[70:])
            if a.case != 'close':
                checks['native_yank_zip_or_close_strike'] = yanks >= 1 or heavies >= 1 or (pull_distance is not None and pull_distance < 13)
    placement = []
    if meta.get('web_yank_fix') and a.case in ('regular', 'mirror', 'up', 'hold', 'followup', 'moving'):
        checks['genuine_distant_reel'] = yanks >= 1 and pull_distance is not None and pull_distance >= 13
        checks['arrival_rake_clip_selected'] = any(r['private'][30] and r['sca'] == rt['values']['SHORT_SCA'] for r in rows)
        for r, foe in zip(rows, foes):
            if foe and r['private'][23] and not r['private'][21]:
                placement.append(dict(frame=r['frame'], dx=(foe['position'][0]-r['hero_pos'][0])/4096,
                                      dy=(foe['position'][1]-r['hero_pos'][1])/4096, state=foe['state']))
        checks['upright_reel_without_floor_bounce'] = bool(placement) and all(r['state'] == 37 and abs(r['dy']) < 1 for r in placement)
        contact = next((r for r in rows if r['private'][21]), None)
        foe = next((e for e in contact['enemies'] if e['actor'] == target), None) if contact else None
        signed_gap = (foe['position'][0]-contact['hero_pos'][0])/4096 * side if foe else None
        checks['arrival_in_front_at_rake'] = signed_gap is not None and 4 <= signed_gap <= 9
        if a.case == 'followup':
            checks['native_y_followup_before_old_recovery'] = any(94 <= r['f'] < 109 and r['st'] == 46 and r['act'] != 49 for r in obs) and len(damage) >= 2
    if meta.get('web_yank_fix'):
        checks['hero_weak_reference_unlinked_at_exit'] = all(r['hero_weak_head'] != rt['state']+112 for r in rows if r['private'][6] == 0)
        if a.case == 'repeat':
            checks['repeated_native_casts'] = starts >= 3 and strikes >= 3 and len(damage) >= 3
    report = dict(case=a.case, passed=all(checks.values()), checks=checks, starts=starts, yanks=yanks, strikes=strikes, heavies=heavies,
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before), target=target, damage=damage,
        route=str(route), sequence=k.seq(obs), rows=rows, placement=placement, distance_at_pull_sample=pull_distance,
        limits='Latest actual DSV copy, ordinary Continue/Test Upgrades; disposable new bit83, initial positions, '
        'training XP fixture, one enemy layout at frame58 and idle enemy re-entry through frame69. Native AI/contact/reactions afterward. '
        'Hurt/stale cases label their one private-RAM interruption; training healing applies. '
        'No actual save writes, campaign balance, player acceptance or DeSmuME/hardware pacing claim.')
    w.write_json(a.out/'result.json', report)
    if pcm:
        with wave.open(str(a.out/'motion.wav'), 'wb') as stream:
            stream.setnchannels(2)
            stream.setsampwidth(2)
            stream.setframerate(rate[0])
            stream.writeframes(b''.join(pcm))
    print(json.dumps({key: report[key] for key in ('case', 'passed', 'checks', 'starts', 'yanks', 'strikes', 'route')}), flush=True)
    return 0 if report['passed'] else 1


def boss(a):
    """Live Conductor heavy rule; initial arrival/purchase and player healing are fixtures."""
    import os
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge, midnight_rework_lab as lab
    from tools import midnight_walk as mw, owned_player_lab
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Hunter kit lab evidence must stay in work/')
    actual, before, copied = v.copy_current(a.out)
    os.environ['WOS_CHAPTER_LAB_SAVE'] = str(copied)
    owned_player_lab.install(a.owned)
    q.configure_rooms(a.rom)
    forge.OUT = a.out
    q.OUT = a.out
    q.RUN_TAG = '-'+a.tag
    forge.install(a.rom, 6)
    meta = json.loads(a.rom.with_suffix('.build.json').read_text(encoding='utf-8'))
    private = meta['hunter_kit']['runtime']['state']-k.p.BASE
    config = meta['hunter_kit']['runtime']['values']['BOSS_CONFIG']
    native, rows, cast_at = lab.Walker.tick, [], [-1000]

    def tick(self, frame, lib):
        if frame == -990:
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
            ct.memmove(ptr+stats+0x14, struct.pack('<I', w.u32(ram, stats+0x14) | 1<<19), 4)
        current = self.last_state
        if not current or not current.pos:
            return
        self.buttons.clear()
        if not current.black:
            if frame % 60 < 6:
                self.buttons.add('L')
        foes = [e for e in current.enemies if w.u32(ram, e['actor']-k.p.BASE+0x40) == config]
        if current.black:
            if foes:
                dx = foes[0]['position'][0]/4096-current.pos[0]
                player = k.p.sample(ram)
                face = player['facing_candidate']
                desired = int(dx >= 0)
                if abs(dx) > 34 or face != desired:
                    self.buttons.add('Right' if desired else 'Left')
                elif current.state in (0, 1, 4, 5, 6) and frame-cast_at[0] >= 90:
                    self.buttons.add('X')
                    cast_at[0] = frame
                elif 0 < frame-cast_at[0] < 6:
                    self.buttons.add('X')
            elif current.pos[0] < 100:
                self.buttons.add('Right')
        rows.append(dict(frame=frame, private=list(struct.unpack_from('<32I', ram, private)),
            hero_pos=current.pos, hero_state=current.state, hp=current.hp, black=current.black, enemies=foes))

    lab.Walker.tick = tick
    try:
        route = q.run(a.rom, a.tag, 'ML_Venom', 2, [mw.wait(600)], combat=True, heal=True)
    finally:
        lab.Walker.tick = native
    live = [r for r in rows if r['enemies']]
    drops = [dict(frame=r['frame'], hp=r['enemies'][0]['hp']) for i, r in enumerate(live)
             if i and r['enemies'][0]['hp'] < live[i-1]['enemies'][0]['hp']]
    checks = dict(heavy_zip_used=any(r['private'][18] for r in rows), actual_boss_hp_loss=bool(drops),
        boss_never_launched_or_yanked=all(e['state'] not in (39, 44, 45, 46, 48, 49) for r in live for e in r['enemies']),
        source_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before)
    report = dict(passed=all(checks.values()), checks=checks, route=route, drops=drops, rows=rows,
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before),
        limits='Latest actual battery copy and measured current ownership/XP. Initial room arrival, cleared '
        'already-earned boss flag147, bit83 and '
        'player healing are disposable fixtures. Boss AI, player approach/X/L, movement and actual HP loss '
        'are native; no boss state/position/HP fixture, no victory, balance or player-acceptance claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps(dict(passed=report['passed'], checks=checks, drops=drops)), flush=True)
    return 0 if report['passed'] else 1


def shop(a):
    """Real purchase, refund, repurchase, save and fresh Continue on a private battery."""
    from tools import emulator_smoke as emu, hunter_kit as h
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Hunter kit lab evidence must stay in work/')
    actual, before, copied = v.copy_current(a.out)
    script = [r for r in v.current_prefix(None) if r['start'] <= 1620]
    def press(button, frame):
        return dict(start=frame, end=frame+6, buttons=[button])
    script += [press(button, frame) for frame, button in
               ((1800, 'X'), (1860, 'Down'), (1920, 'A'), (2200, 'R'), (2260, 'R'))]
    script += [press('Down', 2340+40*i) for i in range(7)]
    script += [press(button, frame) for frame, button in (
        (2660, 'A'), (2700, 'A'), (2800, 'A'), (2840, 'A'), (2940, 'A'), (2980, 'A'),
        (3100, 'B'), (3160, 'B'), (3220, 'X'), (3280, 'A'), (3360, 'A'), (3440, 'A'))]
    marks = {1740: 'before', 2620: 'row', 2760: 'bought', 2900: 'refunded', 3040: 'rebought', 3579: 'saved'}
    seen = {}
    def observe(frame, lib):
        if frame not in marks:
            return
        _, ram = k.ram_of(lib)
        stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
        seen[marks[frame]] = dict(words=list(struct.unpack_from('<3I', ram, stats+12)),
            xp=w.u32(ram, stats+0x44), room=w.u32(ram, stats), hp=w.u32(ram, stats+0x84))
    route = emu.run(a.rom.resolve(), 3580, set(marks), save_path=copied, script=script,
        label=a.tag+'-buy', frame_hook=observe, battery_captures={3579},
        core_options={b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'})
    earned = a.out/'purchased.sav'
    w.atomic_write(earned, (route/'battery-03579.sav').read_bytes(), sources=(actual, copied))
    reloaded = {}
    def continued(frame, lib):
        if frame == 3500:
            _, ram = k.ram_of(lib)
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            reloaded.update(words=list(struct.unpack_from('<3I', ram, stats+12)), xp=w.u32(ram, stats+0x44),
                room=w.u32(ram, stats), hp=w.u32(ram, stats+0x84))
    fresh = emu.run(a.rom.resolve(), 3560, {3500}, save_path=earned,
        script=[r for r in v.current_prefix(None) if r['start'] <= 1620], label=a.tag+'-continue',
        frame_hook=continued, core_options={b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'})
    base = seen['before']
    words = [*base['words']]
    words[2] |= 1<<19
    checks = dict(native_purchase=seen['bought']['words'] == words and seen['bought']['xp'] == base['xp']-h.PRICE,
        native_refund=seen['refunded']['words'] == base['words'] and seen['refunded']['xp'] == base['xp'],
        native_repurchase=seen['rebought']['words'] == words and seen['rebought']['xp'] == base['xp']-h.PRICE,
        fresh_continue_keeps_purchase=reloaded.get('words') == words and reloaded.get('xp') == base['xp']-h.PRICE,
        native_checkpoint_and_hp=reloaded.get('room') == base['room'] and reloaded.get('hp') == base['hp'],
        actual_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before)
    report = dict(passed=all(checks.values()), checks=checks, observations=seen, continued=reloaded,
        buy_route=str(route), continue_route=str(fresh), earned_save=str(earned),
        rom_sha256=w.sha256(a.rom.read_bytes()), source_battery_sha256=w.sha256(before),
        limits='Latest actual DSV copy; ordinary Continue, native shop inputs, refund/repurchase and in-game save. '
        'No purchase/XP/room/HP RAM writes; the earned SRAM snapshot stays private in work/. '
        'No research save adoption or player-acceptance claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps(dict(passed=report['passed'], checks=checks, observations=seen, continued=reloaded)), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--owned', type=Path, required=True)
    p.add_argument('--case', choices=('regular', 'mirror', 'up', 'close', 'unowned', 'red', 'whiff', 'air',
                                     'cancel', 'swap', 'hurt', 'stale', 'hold', 'followup', 'repeat', 'moving', 'boss', 'shop'), default='regular')
    p.add_argument('--distance', type=float, default=42, help='Pre-input training enemy gap in units; actual cast gap is measured')
    p.add_argument('--tag', required=True)
    a = p.parse_args()
    sys.exit(boss(a) if a.case == 'boss' else shop(a) if a.case == 'shop' else run(a))
