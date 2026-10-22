"""Copied-save qualification for final-ROM Skyjack and native Freight roof pursuit."""
from pathlib import Path
import argparse
import ctypes as ct
import json
import struct
import sys
import os
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import kit_lab as k, tasm_kit as kit, wos_tool as w, playtest


def copied_save(out):
    out.mkdir(parents=True, exist_ok=True)
    actual = playtest.current_save()
    before = actual.read_bytes()
    copy = out / 'latest-player-copy.dsv'
    copy.write_bytes(before)
    k.TRAINING_SAVE = copy
    return actual, before


def sky(rom, out, case):
    actual, before = copied_save(out)
    inputs = k.rows_from(k.INPUTS / 'vault.json')
    if 'cancel' in case:
        inputs += [{'start': 91, 'end': 107, 'buttons': ['R', 'Left']}]
    fixture = {'armed': False}
    def hook(frame, lib):
        if 'wall' not in case or frame != 60:
            return
        ptr, ram = k.ram_of(lib)
        player = k.p.sample(ram)
        active, actor = struct.unpack_from('<2I', ram, kit.KIT_STATE-kit.BASE+0x330)
        if not active or not player['controller'] or player['controller']['state_id_candidate'] not in (19, 51):
            raise ValueError('Wall fixture requires a native established Skyjack juggle')
        enemy = next(e for e in k.enemies(ram) if e['actor'] == actor)
        motion = w.u32(ram, actor-kit.BASE+0x30)-kit.BASE
        x, ex = (236, 235) if 'right' in case else (4, 5)
        k.teleport(ptr, ram, player['motion_address']-kit.BASE, x*4096, player['position_q12_candidate'][1])
        k.teleport(ptr, ram, motion, ex*4096, enemy['position'][1])
        fixture.update(armed=True, frame=frame, player_x=x, enemy_x=ex,
                       scope='One disposable RAM placement of an already-active juggle; subsequent movement uses the actual ROM code and native physics.')
    label = 'finish-' + case + '-' + w.sha256(rom.read_bytes())[:8]
    evidence, _ = k._run(k.solo_rom(rom), label, inputs, frames=340, bits=0xFEF00,
                         extra_hook=hook, probe=(kit.KIT_STATE+0x330, 16), caps=(60, 80, 120, 339))
    rows = [r for r in json.loads((evidence / 'observations.json').read_text()) if r['f'] >= 0]
    active = [r for r in rows if r['f'] >= 60 and r['probe'][0]]
    evade = [r for r in rows if r['f'] >= 91 and r['st'] in (52, 53, 54, 55, 57)]
    checks = {'save_unchanged': actual.read_bytes() == before, 'skyjack_armed': bool(active)}
    if 'wall' not in case or 'cancel' in case:
        checks['latch_releases'] = rows[-1]['probe'][0] == 0
    if case == 'sky-open':
        checks['native_air_contacts'] = min(r['en'][0][0] for r in rows) <= 65536-3*4096
    elif 'cancel' in case:
        checks['native_evade'] = bool(evade)
        checks['evade_keeps_direction'] = any(r['vel'][0] < 0 for r in evade)
    if 'wall' in case:
        checks['wall_fixture_armed'] = fixture['armed']
        checks['native_wall_bound'] = (max(r['pos'][0] for r in active) <= 968577+64 if 'right' in case
                                       else min(r['pos'][0] for r in active) >= 14463-64)
    report = {'rom_sha256': w.sha256(rom.read_bytes()), 'case': case, 'passed': all(checks.values()),
              'checks': checks, 'fixture': fixture, 'evidence': str(evidence),
              'metrics': {'min_x': min(r['pos'][0] for r in active), 'max_x': max(r['pos'][0] for r in active),
                          'first_evade': evade[0]['f'] if evade else None,
                          'latch_at_end': rows[-1]['probe'][0]},
              'limits': 'Latest copied battery; temporary paid training bits and one native dummy. Wall setup is explicitly disposable RAM. No runtime code patch, real save write or player feel claim.'}
    w.write_json(out / (case+'.json'), report)
    print(json.dumps(report), flush=True)
    return report['passed']


def freight(rom, out, frames=1500, roof_x=80, bait=False, roof_y=25, owned=None):
    actual, before = copied_save(out)
    if owned:
        from tools import owned_player_lab
        owned_player_lab.install(owned)
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge
    from tools import midnight_rework_lab as lab, midnight_walk as mw, crane_walk as cw, crane_rooms
    meta = json.loads(rom.with_suffix('.build.json').read_text())
    rt = meta['chapter_spectacle']['scripted_runtime']
    raw = rom.read_bytes()
    h = w.parse_header(raw)
    arm = raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    from tools.creature_forge import offset
    pattern = next(w.u32(arm, offset(rt['roster_table'])+i*12+4) for i in range(40)
                   if w.u32(arm, offset(rt['roster_table'])+i*12) == 97)
    forge.OUT = out
    q.OUT, q.RUN_TAG = out, '-fr-'+w.sha256(raw)[:6]+'-'+w.sha256(str(out.resolve()).encode())[:4]
    forge.install(rom, 12)
    native_run = k._run
    def isolate(*args, **options):
        previous = options['extra_hook']
        def hook(frame, lib):
            if frame+k.TRAINING_START >= 2040:
                ptr, ram = k.ram_of(lib)
                ct.memmove(ptr+pattern-kit.BASE, bytes((36,)*4), 4)
                for i in range(40):
                    at = rt['goal_table']-kit.BASE+i*20
                    if w.u32(ram, at) == 97:
                        for column in (4, 8, 12):
                            ct.memmove(ptr+w.u32(ram, at+column)-kit.BASE, struct.pack('<2I', 8192, 8192), 8)
                        break
                    if not w.u32(ram, at):
                        raise ValueError('Freight goal missing')
            return previous(frame, lib)
        options['extra_hook'] = hook
        return native_run(*args, **options)
    isolate._midnight_static = True
    k._run = isolate
    class RoofWalker(lab.Walker):
        def do_bait_under(self, step, state, ptr, ram):
            self.buttons.clear()
            foes = [e for e in state.enemies if e['hp'] > 0]
            if foes and state.pos and state.pos[1] < 8:
                e = foes[0]
                if e['position'][1]/4096 < 2 and abs(e['position'][0]/4096-state.pos[0]) < 24:
                    self.record('native_ballast_baited_below_roof', True, state, enemy_position=e['position'])
                    return True
            if self.t >= step[1]:
                self.record('native_ballast_baited_below_roof', False, state)
                return True
            return False

        def do_roof_hold(self, step, state, ptr, ram):
            self.buttons.clear()
            nav = meta.get('chapter_finish', {}).get('crane', {}).get('navigation_state')
            if nav and state.frame % 8 == 0:
                rows = [struct.unpack_from('<8I', ram, nav-kit.BASE+i*32) for i in range(32)]
                self.report.setdefault('finish_navigation', []).append({'frame': state.frame,
                    'rows': [row for row in rows if row[0]]})
            foes = [e for e in state.enemies if e['hp'] > 0]
            if foes and state.pos:
                e = foes[0]
                y = e['position'][1]/4096
                self.scratch['roof_initial_hp'] = self.scratch.get('roof_initial_hp', state.hp)
                if y >= roof_y-3 and abs(y-state.pos[1]) < 10:
                    self.scratch['roof_reached'] = True
                if self.scratch.get('roof_reached') and state.hp < self.scratch['roof_initial_hp']:
                    self.record('ballast_reaches_roof_and_hits', True, state, enemy_position=e['position'],
                                native_damage=True, enemy_hp_fixture=False)
                    return True
            if self.t >= step[1] or state.hp <= 0:
                self.record('ballast_reaches_roof_and_hits', False, state,
                            reached=self.scratch.get('roof_reached', False))
                return True
            return False
    cw.cr = crane_rooms
    cw.install()
    cw.OUT, lab.OUT, mw.OUT = out, out, out
    cw.Walker = RoofWalker
    RoofWalker.combat, RoofWalker.heal = True, False
    approach = [('travel', 72, 1600), ('bait_under', 1200), ('travel', 100, 1600)] if bait else []
    if roof_y > 25:
        approach += [('land', 68, 25, 1600)]
    if roof_y > 47:
        approach += [('land', 100, 47, 1600)]
    label = 'roof'+q.RUN_TAG
    result = cw.run(rom, label, 'AR_FreightExchange', 1,
        [mw.wait(90), *approach, ('land', roof_x, roof_y, 1600), mw.wait(60), ('roof_hold', frames), mw.wait(30)])
    checks = result.get('checks', [])
    report = {'rom_sha256': w.sha256(raw), 'passed': result['passed'] and actual.read_bytes() == before,
              'checks': checks, 'raw_report': str(out / ('walk-'+label+'.json')),
              'captures': result.get('captures'), 'roof_x': roof_x, 'roof_y': roof_y,
              'owned_profile': str(owned) if owned else None, 'bait_route': bait, 'source_battery_unchanged': actual.read_bytes() == before,
              'limits': 'Copied latest battery and initial native room arrival, isolated one Ballast cost budget. Player reaches the roof with native jump/steer input. No player/enemy position, HP or state placement; no player refills during observation.'}
    w.write_json(out / 'freight-roof.json', report)
    print(json.dumps(report), flush=True)
    return report['passed']


def skitter_lifecycle(rom, out, owned=None):
    actual, before = copied_save(out)
    if owned:
        from tools import owned_player_lab
        owned_player_lab.install(owned)
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge
    from tools import midnight_rework_lab as lab, midnight_walk as mw
    from tools.creature_forge import offset
    meta = json.loads(rom.with_suffix('.build.json').read_text())
    rt = meta['chapter_spectacle']['scripted_runtime']
    raw = rom.read_bytes()
    h = w.parse_header(raw)
    arm = raw[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    pattern = next(w.u32(arm, offset(rt['roster_table'])+i*12+4) for i in range(40)
                   if w.u32(arm, offset(rt['roster_table'])+i*12) == 78)
    forge.OUT = out
    q.OUT, q.RUN_TAG = out, '-sl-'+w.sha256(raw)[:6]+'-'+w.sha256(str(out.resolve()).encode())[:4]
    forge.install(rom, 4)
    native_run = k._run
    pcm, rate = [], [0]
    def isolate(*args, **options):
        previous = options['extra_hook']
        def hook(frame, lib):
            if frame+k.TRAINING_START >= 2040:
                ptr, ram = k.ram_of(lib)
                ct.memmove(ptr+pattern-kit.BASE, bytes((21,)*4), 4)
                for i in range(40):
                    at = rt['goal_table']-kit.BASE+i*20
                    if w.u32(ram, at) == 78:
                        for column in (4, 8, 12):
                            ct.memmove(ptr+w.u32(ram, at+column)-kit.BASE, struct.pack('<2I', 4096, 4096), 8)
                        break
                    if not w.u32(ram, at):
                        raise ValueError('Terminal goal missing')
            if frame >= 0 and not rate[0]:
                info = (ct.c_byte*40)()
                lib.retro_get_system_av_info.argtypes = [ct.c_void_p]
                lib.retro_get_system_av_info(ct.byref(info))
                rate[0] = round(struct.unpack_from('<d', bytes(info), 32)[0])
                lib._wos_audio_sink = lambda f, data: pcm.append(data) if f >= k.TRAINING_START else None
            return previous(frame, lib)
        options['extra_hook'] = hook
        return native_run(*args, **options)
    isolate._midnight_static = True
    k._run = isolate
    def lifecycle(self, step, state, ptr, ram):
        self.buttons.clear()
        stats = w.u32(ram, k.STATS_POINTER-kit.BASE)-kit.BASE
        xp = w.u32(ram, stats+0x44)
        if 'life_hp' not in self.scratch:
            self.scratch.update(life_hp=state.hp, life_xp=xp, life_phase='observe', life_states=[], life_dead=0)
        self.report.setdefault('life_currency', []).append({'frame': state.frame, 'hp': state.hp, 'xp': xp})
        enemies = [e for e in state.enemies if e['hp'] > 0]
        if self.t >= step[1] or state.hp <= 0:
            self.record('skitter_native_lifecycle_clear', False, state,
                        phase=self.scratch['life_phase'], states=self.scratch['life_states'])
            return True
        if not enemies:
            if not self.scratch['life_states']:
                if state.pos and state.pos[0] < 140:
                    self.buttons.add('Right')
                return False
            self.scratch['life_dead'] += 1
            if self.scratch['life_dead'] >= 160:
                states = self.scratch['life_states']
                self.record('skitter_native_lifecycle_clear', self.scratch['life_phase'] == 'finish'
                    and any(s in states for s in (48, 49, 50)) and 51 in states and xp > self.scratch['life_xp'],
                    state, states=states, xp_before=self.scratch['life_xp'], xp_after=xp,
                    owned_profile=str(owned) if owned else None, enemy_hp_fixture=False, player_healing=False)
                return True
            point = self.scratch.get('life_last_enemy_x')
            if point is not None and state.pos and abs(point-state.pos[0]) > 2:
                self.buttons.add('Right' if point > state.pos[0] else 'Left')
            return False
        self.scratch['life_dead'] = 0
        enemy = enemies[0]
        self.scratch['life_last_enemy_x'] = enemy['position'][0]/4096
        if enemy['state'] not in self.scratch['life_states']:
            self.scratch['life_states'].append(enemy['state'])
        phase = self.scratch['life_phase']
        dx = enemy['position'][0]/4096-state.pos[0]
        dy = enemy['position'][1]/4096-state.pos[1]
        if phase == 'observe':
            if state.hp < self.scratch['life_hp']:
                self.scratch['life_phase'] = 'launch'
            elif abs(dx) > 7:
                self.buttons.add('Right' if dx > 0 else 'Left')
        elif phase == 'launch':
            if enemy['state'] in (38, 39, 40, 41, 42, 43, 44, 45, 48, 49, 50):
                self.scratch['life_phase'] = 'rise'
            elif abs(dx) > 6:
                self.buttons.add('Right' if dx > 0 else 'Left')
            elif state.frame % 12 < 4:
                self.buttons.update(('Up', 'Y'))
        elif phase == 'rise':
            if 51 in self.scratch['life_states'] and enemy['state'] in (0, 1, 2, 3, 15):
                self.scratch['life_phase'] = 'finish'
            elif abs(dx) > 10 and abs(dy) < 12:
                self.buttons.add('Right' if dx > 0 else 'Left')
        else:
            from tools.crane_creature_lab import pursuit_buttons
            self.buttons.update(pursuit_buttons(state.frame, state, enemy, False))
        return False
    lab.Walker.do_skitter_lifecycle = lifecycle
    result = q.run(rom, 'life'+q.RUN_TAG, 'ML_Station', 1,
                   [mw.wait(90), ('travel', 100, 1800), ('skitter_lifecycle', 5000), mw.wait(30)], combat=True, heal=False)
    if pcm:
        with wave.open(str(out/'skitter-live.wav'), 'wb') as stream:
            stream.setparams((2, 2, rate[0], 0, 'NONE', 'not compressed'))
            stream.writeframes(b''.join(pcm))
    audio_path = out/'skitter-live.wav' if pcm else out/(result['route']+'.wav')
    if not audio_path.exists():
        raise ValueError('Lifecycle driver did not retain its in-game PCM')
    report = {'rom_sha256': w.sha256(raw), 'passed': result['passed'] and actual.read_bytes() == before,
              'checks': result.get('checks'), 'captures': result.get('captures'),
              'raw_report': str(out/('walk-'+result['route']+'.json')),
              'audio': str(audio_path), 'source_battery_unchanged': actual.read_bytes() == before,
              'limits': 'Latest copied save, isolated native single-Skitter budget and initial native room arrival. Native launch, fall/get-up, base-string kill and currency; no HP or position fixtures, no player refills. Current-owned values restored once in disposable RAM when --owned is supplied.'}
    w.write_json(out/'skitter-lifecycle.json', report)
    print(json.dumps(report), flush=True)
    return report['passed']


def campaign(rom, out, case, owned=None, black=False, save=None):
    actual, before = copied_save(out)
    if owned:
        from tools import owned_player_lab
        owned_player_lab.install(owned)
    os.environ['WOS_CHAPTER_LAB_OUT'] = str(out.resolve())
    from tools import midnight_rebuild_lab
    sys.argv = [str(ROOT/'tools/midnight_rebuild_lab.py'), case,
                '--rom', str(rom), '--tag=-f29', '--capture-every', '12']
    if case == 'hoist-save':
        sys.argv.append('--no-heal')
    if black:
        sys.argv.append('--black')
    if save:
        sys.argv.extend(('--save', str(save)))
    status = midnight_rebuild_lab.main()
    unchanged = actual.read_bytes() == before
    report = {'rom_sha256': w.sha256(rom.read_bytes()), 'case': case,
              'passed': status == 0 and unchanged, 'source_battery_unchanged': unchanged,
              'owned_profile': str(owned) if owned else None,
              'scope': 'Existing native hoist/earned-save/Continue driver, copied actual battery; no actual save writes.'}
    w.write_json(out/'campaign-control.json', report)
    return report['passed']


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('case', choices=('sky-open', 'sky-cancel', 'sky-right-wall', 'sky-left-wall',
                                    'sky-right-wall-cancel', 'sky-left-wall-cancel', 'freight-roof',
                                    'skitter-lifecycle', 'hoist-save', 'arm-continue', 'arm-retry-continue'))
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--frames', type=int, default=1500)
    p.add_argument('--roof-x', type=float, default=80)
    p.add_argument('--roof-y', type=float, default=25)
    p.add_argument('--bait', action='store_true')
    p.add_argument('--owned', type=Path)
    p.add_argument('--black', action='store_true')
    p.add_argument('--save', type=Path)
    a = p.parse_args()
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Evidence must stay in work/')
    if a.case == 'freight-roof':
        passed = freight(a.rom, a.out, a.frames, a.roof_x, a.bait, a.roof_y, a.owned)
    elif a.case == 'skitter-lifecycle':
        passed = skitter_lifecycle(a.rom, a.out, a.owned)
    elif a.case.startswith('sky-'):
        passed = sky(a.rom, a.out, a.case)
    else:
        passed = campaign(a.rom, a.out, a.case, a.owned, a.black, a.save)
    raise SystemExit(0 if passed else 1)
