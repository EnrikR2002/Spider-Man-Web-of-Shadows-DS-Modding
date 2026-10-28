"""Copied-latest-battery Boarding input, native boss attack and save controls."""
import argparse
import ctypes as ct
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import kit_lab as k, wos_tool as w, vortex_forge_lab as v


def minis(ram):
    """Bounded live MiniBoss layout; no NormalEnemy health or registry assumption."""
    out, pos = [], 0
    while (at := ram.find(struct.pack('<I', 0x0212ce38), pos)) >= 0:
        pos = at+4
        if at % 4 or at+0x104 > len(ram) or w.u32(ram, at+8) != 0x0212ce54:
            continue
        mo = w.u32(ram, at+0x30)-k.p.BASE
        if mo % 4 or not 0 < mo < len(ram)-0x310 or w.u32(ram, mo) != at+k.p.BASE:
            continue
        ctl = w.u32(ram, mo+0x1f8)-k.p.BASE
        if ctl % 4 or not 0 < ctl < len(ram)-0xb0 or w.u32(ram, ctl) != 0x02133c18 or w.u32(ram, ctl+0x44) != at+k.p.BASE:
            continue
        hp, maximum = struct.unpack_from('<2i', ram, at+0xfc)
        if not 0 < hp <= maximum < 0x1000000:
            continue
        out.append(dict(actor=at+k.p.BASE, hp=hp, max=maximum, controller=ctl+k.p.BASE,
            state=w.u32(ram, ctl+0x14), action=w.u32(ram, mo+0x258),
            position=[sum(struct.unpack_from('<i', ram, mo+o)[0] for o in pair)
                      for pair in ((0x7c, 0x160), (0x80, 0x164))]))
    return out


def mini_fixture(rom, subtype=0, wall=False):
    """Start the original native encounter; the separate wall target is a parked fixture."""
    import mod
    from types import SimpleNamespace
    from tools import room_catalog, room_objects, room_entities, room_script, spider2099
    from tools import midnight_walk as mw, midnight_chapter as ch
    clean, _, _ = mod.load_clean()
    hh = w.parse_header(clean)
    names, blobs = spider2099.resources(clean)
    arena = ('Sewer_Map09', 'Pier_Map08', 'Sewer_Map06', 'Downtown_Map14')[subtype]
    entry = next(r for r in room_catalog.parse(clean[hh['arm9_offset']:hh['arm9_offset']+hh['arm9_size']], names)
                 if r.name == ('Test_Combat01' if wall else arena))
    original_boss = room_objects.RoomObjects.parse(blobs[names.index(arena+'_app.obj')])
    kind = (0x29, 0x2a, 0x2c, 0x2d)[subtype]
    enemy = bytearray(next(e for e in room_entities.Entities.parse(original_boss.records[1].sections[0]).records
                          if len(e) == 24 and w.u32(e, 12) == 2 and e[22] == kind))
    x, y = struct.unpack_from('<2i', enemy)
    if wall:
        obj = room_objects.RoomObjects.parse(blobs[entry.objects])
        raw, _ = room_script.drop_commands(obj.raw, 1, lambda group, command: group == 0)
        struct.pack_into('<2i', enemy, 0, 244*4096, 5*4096)
        enemy[23] = 0
        raw, ag = room_script.append_batch(raw, 1, [(bytes(enemy), 'Character (Boarding Fixture)')], 'Boarding Fixture')
        raw = room_script.extend_group(raw, 1, 0, [room_script.activate(ag=ag)])
        layout = (234*4096, 5*4096)
    else:
        nb = original_boss.names[1]
        groups = nb.labels[nb.category_ends[0]:nb.category_ends[1]]
        starts = [room_script.activate(eg=groups.index(name)+1) for name in
                  ('Boss Trigger', 'Gate_Spawn', 'Miniboss_Spawn') if name in groups]
        raw = room_script.extend_group(original_boss.raw, 1, 0, starts)
        layout = (x-12*4096, y+5*4096)
    source = rom.read_bytes()
    nn, bb = spider2099.resources(source)
    bb[nn.index(entry.name+'_app.obj')] = raw
    result = w.rebuild_rom(source, {'Glob.bin': w.pack_glob(nn, bb)})
    if wall:
        # Idle data alone lets the native thinker start an attack between callbacks.
        from tools import tasm_kit as kit
        metadata = json.loads(rom.with_suffix('.build.json').read_text())['boarding']['runtime']
        at = w.align_up(metadata['entry']+metadata['bytes'], 16)
        offset = kit.SOURCE+at-kit.TARGET
        h = w.parse_header(result)
        staged = bytearray(result)
        code_offset = h['arm9_offset']+offset
        if any(staged[code_offset:code_offset+8]) or at+8 > metadata['start']+metadata['allocation_bytes']:
            raise ValueError('No verified wall-fixture scratch tail')
        staged[code_offset:code_offset+8] = struct.pack('<2I', 0xe3a00000, 0xe12fff1e)
        struct.pack_into('<I', staged, h['arm9_offset']+0x133c18+0xa8, at)
        result = bytes(staged)
        w.validate_rom(result, target=True)
    path = ROOT/'build/boarding-fixtures'/f'{w.sha256(source)[:8]}-mini{subtype}{"-wall" if wall else ""}.nds'
    w.atomic_write(path, result, sources=(rom,))
    w.atomic_write(path.with_suffix('.build.json'), rom.with_suffix('.build.json').read_bytes())
    ch.BY_NAME = {**ch.BY_NAME, 'NativeMini': SimpleNamespace(index=entry.index)}
    original = mw.rom_objects
    mw.rom_objects = lambda p: {**original(p), entry.index: raw}
    return path, dict(room=entry.index, layout=layout)


def run(a):
    from tools import chapter_renewal_lab as q, creature_forge_lab as forge
    from tools import midnight_rework_lab as lab, midnight_walk as mw, owned_player_lab
    actual, before, copied = v.copy_current(a.out)
    os.environ['WOS_CHAPTER_LAB_SAVE'] = str(copied)
    owned_player_lab.install(a.owned)
    source_rom = a.rom
    fixture = None
    if a.command == 'mini':
        a.rom, fixture = mini_fixture(a.rom, a.subtype, a.case == 'wall')
    q.configure_rooms(a.rom)
    q.OUT = forge.OUT = a.out
    q.RUN_TAG = '-'+a.tag
    forge.install(a.rom, a.capture_every)
    meta = json.loads(a.rom.with_suffix('.build.json').read_text())
    state = meta['boarding']['runtime']['state']-k.p.BASE
    yank_state = meta['boarding']['runtime']['values']['YANK_STATE']-k.p.BASE
    boss_config = meta['boarding']['runtime']['values']['BOSS_CONFIG']
    original, rows, started, attempt, faults = lab.Walker.tick, [], [-1], [-100], []
    previous_phase, completed, retry_after = [0], [False], [0]
    placed, hp_fixture, ride_rakes = [False], [False], [0]
    accepted_tears, accepted_rakes = set(), set()

    def tick(self, frame, lib):
        if a.case == 'wall' and frame >= -1100:
            ptr, ram = k.ram_of(lib)
            for enemy in minis(ram):
                k.teleport(ptr, ram, w.u32(ram, enemy['actor']-k.p.BASE+0x30)-k.p.BASE, 244*4096, 5*4096)
                ct.memmove(ptr+enemy['actor']-k.p.BASE+0x18, bytes(8), 8)
                ct.memmove(ptr+enemy['controller']-k.p.BASE+0x14, bytes(4), 4)
                ct.memmove(ptr+enemy['controller']-k.p.BASE+4, b'\x01', 1)
        if a.command == 'mini' and -850 <= frame < 0:
            ptr, ram = k.ram_of(lib)
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            if 0 < stats < len(ram)-0x98:
                ct.memmove(ptr+stats+0x84, struct.pack('<I', 77824), 4)
                if w.u32(ram, stats) == fixture['room'] and not placed[0]:
                    sample = k.p.sample(ram)
                    k.teleport(ptr, ram, sample['motion_address']-k.p.BASE, *fixture['layout'])
                    placed[0] = True
        if a.command == 'mini' and frame == -20:
            ptr, ram = k.ram_of(lib)
            sample = k.p.sample(ram)
            k.teleport(ptr, ram, sample['motion_address']-k.p.BASE, *fixture['layout'])
        if frame == -1100:
            ptr, ram = k.ram_of(lib)
            stats = w.u32(ram, k.STATS_POINTER-k.p.BASE)-k.p.BASE
            flags = int.from_bytes(ram[stats+0x1c:stats+0x44], 'little') & ~(1 << 147)
            if a.command == 'mini':
                flags &= ~(1 << (167, 168, 170, 171)[a.subtype])
                if a.subtype == 2:
                    flags &= ~(1 << 100)
                if a.subtype == 3:
                    flags &= ~((1 << 83) | (1 << 84))
            ct.memmove(ptr+stats+0x1c, flags.to_bytes(40, 'little'), 40)
        original(self, frame, lib)
        if frame < 0:
            return
        ptr, ram = k.ram_of(lib)
        sample = k.p.sample(ram)
        hero = sample['actor_address']-k.p.BASE
        motion = sample['motion_address']-k.p.BASE
        ctl = w.u32(ram, motion+0x1f8)-k.p.BASE
        stats = w.u32(ram, hero+0xe8)-k.p.BASE
        if frame == 0:
            bits = w.u32(ram, stats+8) & ~(1 << 24)
            if a.case != 'unowned':
                bits |= 1 << 24
            ct.memmove(ptr+stats+8, struct.pack('<I', bits), 4)
            if a.case == 'cancel-no-air-dodge':
                ct.memmove(ptr+stats, struct.pack('<I', w.u32(ram, stats) & ~0x400), 4)
        foes = minis(ram) if a.command == 'mini' else [e for e in k.enemies(ram)
                if w.u32(ram, e['actor']-k.p.BASE+0x40) == boss_config and e['hp'] > 0]
        private = list(struct.unpack_from('<64I', ram, state))
        yank = list(struct.unpack_from('<32I', ram, yank_state))
        if rows and private[12] > rows[-1]['private'][12]:
            if private[17] > rows[-1]['private'][17]:
                accepted_tears.add(private[15])
            if private[16] > rows[-1]['private'][16]:
                accepted_rakes.add(private[15])
        if a.case == 'mirror' and a.command == 'conductor' and foes and not faults:
            nearest = min(foes, key=lambda e: abs(e['position'][0]-sample['position_q12_candidate'][0]))
            k.teleport(ptr, ram, motion, nearest['position'][0]+18*4096, nearest['position'][1])
            faults.append(-1)
        if private[6] and previous_phase[0] == 0:
            started[0] = frame
            ride_rakes[0] = private[16]
        if private[6] == 0 and previous_phase[0] and a.case in ('regular', 'mirror', 'rake', 'zip', 'combo', 'lethal'):
            escaped = private[15] in accepted_tears and any(r['phase'] == 5 and r['private'][15] == private[15] for r in rows)
            raked = a.case == 'rake' and private[15] in accepted_rakes
            if escaped or raked:
                completed[0] = True
            else:
                started[0] = -1
                retry_after[0] = frame+12
        previous_phase[0] = private[6]
        age = frame-started[0] if started[0] >= 0 else -1
        self.buttons.clear()
        black = w.u32(ram, hero+0x34) == 1
        desired_form = a.case != 'red'
        if black != desired_form:
            if frame % 60 < 6:
                self.buttons.add('L')
        elif private[6]:
            if a.case in ('cancel', 'cancel-no-air-dodge') and age >= 24:
                self.buttons.add('R')
            elif a.case == 'swap' and age >= 24:
                self.buttons.add('L')
            elif private[6] == 6:
                target = next((e for e in foes if e['actor']+4 == private[2]), None)
                if target:
                    self.buttons.add('Right' if target['position'][0] >= sample['position_q12_candidate'][0] else 'Left')
            elif a.case == 'wall':
                self.buttons.add('Right')
                if private[6] == 2:
                    self.buttons.add('Y')
            elif a.case not in ('shake', 'hold', 'unowned', 'red'):
                rake = a.case == 'rake' or a.case in ('combo', 'mirror') and private[16] == ride_rakes[0]
                if rake and private[6] == 2:
                    self.buttons.add('Y')
                if not rake and private[6] == 2:
                    self.buttons.add('A')
        elif foes and started[0] < 0 and not completed[0] and frame >= retry_after[0]:
            nearest = min(foes, key=lambda e: abs(e['position'][0]-sample['position_q12_candidate'][0]))
            dx = (nearest['position'][0]-sample['position_q12_candidate'][0])/4096
            dy = (nearest['position'][1]-sample['position_q12_candidate'][1])/4096
            toward = 'Right' if dx >= 0 else 'Left'
            self.buttons.add(toward)
            if a.case == 'zip' and a.command == 'conductor':
                self.buttons.clear()
                desired = int(dx >= 0)
                if yank[0] == sample['actor_address'] and yank[6]:
                    self.buttons.add(toward)
                elif abs(dx) > 40 or sample['facing_candidate'] != desired:
                    self.buttons.add(toward)
                elif abs(dx) < 14:
                    self.buttons.add('Left' if dx >= 0 else 'Right')
                elif frame % 24 < 6:
                    self.buttons.update(('Down', 'A'))
            elif a.command == 'mini' and a.case in ('regular', 'mirror', 'rake', 'combo'):
                self.buttons.clear()
                hero_state = w.u32(ram, ctl+0x14)
                if nearest['state'] in (63, 67, 68) and hero_state in (15, 19, 51):
                    self.buttons.add(toward)
                elif hero_state in (0, 1, 4, 5, 6, 24):
                    if dy < -12:
                        way = toward if abs(dx) > 7 else 'Right' if frame//90 % 2 else 'Left'
                        self.buttons.add(way)
                    elif abs(dx) > 7:
                        self.buttons.add(toward)
                    elif frame-attempt[0] >= 70:
                        attempt[0] = frame
                air_age = frame-attempt[0]
                if 0 <= air_age < 8:
                    self.buttons.add('B')
                if hero_state in (15, 19, 51) and air_age >= 8:
                    if dy < -14 and frame % 30 < 6:
                        self.buttons.update(('Down', 'A'))
                    elif dy > 18 and frame % 30 < 8:
                        self.buttons.add('B')
                    elif abs(dy) <= 18 and air_age % 20 < 14:
                        self.buttons.add('Y')
                if hero_state in (7, 8, 9, 29):
                    self.buttons.update(('Down',) if dy < 0 else ('Up',))
                if hero_state in (63, 65, 67, 68, 74, 75, 77, 79) and frame % 30 < 6:
                    self.buttons.add('R')
            elif a.case == 'zip' and abs(dx) > 7:
                self.buttons.update(('Down', 'A'))
            elif abs(dx) < 16 and frame-attempt[0] >= 70 and w.u32(ram, ctl+0x14) in (0, 1, 4, 5, 6, 24):
                attempt[0] = frame
            if a.case != 'zip' and 0 <= frame-attempt[0] < 10:
                self.buttons.add('B')
        elif not foes and a.command == 'conductor' and started[0] < 0 and sample['position_q12_candidate'][0] < 100*4096:
            self.buttons.add('Right')
        if private[6] and age == 24 and a.case in ('hurt', 'death', 'room', 'form', 'target-dead', 'target-stale'):
            if a.case in ('hurt', 'death'):
                ct.memmove(ptr+ctl+0x14, struct.pack('<I', 63), 4)
                ct.memmove(ptr+ctl+4, b'\x01', 1)
                if a.case == 'death':
                    ct.memmove(ptr+stats+0x78, bytes(4), 4)
            elif a.case == 'room':
                ct.memmove(ptr+stats-12, struct.pack('<I', w.u32(ram, stats-12)+1), 4)
            elif a.case == 'form':
                ct.memmove(ptr+hero+0x34, bytes(4), 4)
            elif foes:
                enemy = next((e for e in foes if e['actor']+4 == private[2]), foes[0])
                at = enemy['actor']-k.p.BASE
                if a.case == 'target-dead':
                    ct.memmove(ptr+at+(0xfc if a.command == 'mini' else 0x44), bytes(4), 4)
                else:
                    ct.memmove(ptr+state+16, bytes(4), 4)
            faults.append(frame)
        if a.case == 'lethal' and private[6] and not hp_fixture[0]:
            enemy = next((e for e in foes if e['actor']+4 == private[2]), None)
            if enemy:
                ct.memmove(ptr+enemy['actor']-k.p.BASE+(0xfc if a.command == 'mini' else 0x44), struct.pack('<I', 4096), 4)
                hp_fixture[0] = True
        flags = int.from_bytes(ram[stats+0x10:stats+0x38], 'little')
        rows.append(dict(frame=frame, phase=private[6], private=private, state=w.u32(ram, ctl+0x14),
            actor=sample['actor_address'], yank=yank,
            pos=sample['position_q12_candidate'], velocity=list(struct.unpack_from('<2i', ram, hero+0x18)),
            action=w.u32(ram, motion+0x258), clock=w.u32(ram, motion+0x178),
            gab=w.u32(ram, motion+0x16c), buttons=sorted(self.buttons), enemies=foes,
            victory=bool(flags & (1 << 147))))

    lab.Walker.tick = tick
    prefix = k.rows_from
    def current_inputs(path):
        rows = v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else prefix(path)
        if a.command == 'mini' and str(path).endswith('oscorp-owned.json'):
            rows += [dict(start=f, end=f+6, buttons=['A']) for f in (2280, 2400, 2520, 2640, 2760, 2880)]
        return rows
    k.rows_from = current_inputs
    try:
        route = q.run(a.rom, a.tag, 'NativeMini' if a.command == 'mini' else 'ML_Venom',
                      0 if a.command == 'mini' else 2, [mw.wait(a.frames)], combat=True, heal=True)
    finally:
        lab.Walker.tick, k.rows_from = original, prefix
    active = [r for r in rows if r['phase']]
    kicking = [r for r in rows if r['phase'] == 5 and r['private'][15] in accepted_tears]
    before_kick = next((rows[i-1]['pos'] for i, r in enumerate(rows)
        if i and r['phase'] == 5 and r['private'][15] in accepted_tears), None)
    focus = next((r['private'][2]-4 for r in active if r['private'][2]), None)
    damage = []
    for i, row in enumerate(rows[1:], 1):
        previous = next((e for e in rows[i-1]['enemies'] if e['actor'] == focus), None)
        enemy = next((e for e in row['enemies'] if e['actor'] == focus), None)
        if previous and enemy and enemy['hp'] < previous['hp']:
            damage.append(dict(frame=row['frame'], amount=previous['hp']-enemy['hp'],
                ride=row['private'][15],
                authored_hit=any(rows[j]['private'][12] > rows[j-1]['private'][12]
                    for j in range(max(1, i-2), min(len(rows), i+3)))))
    checks = dict(actual_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before,
        real_target=any(r['enemies'] for r in rows),
        owned_gate=not active if a.case in ('unowned', 'red') else bool(active),
        cleanup_complete=not rows[-1]['phase'] if a.case != 'hold' else True)
    if a.case in ('regular', 'mirror', 'combo', 'lethal'):
        checks.update(chosen_rip=bool(rows[-1]['private'][17]),
            native_hp_hit=any(d['authored_hit'] and d['amount'] == 0x2000 for d in damage),
            kick_off_native_escape=bool(kicking) and all(not r['private'][2] for r in kicking)
                and any(r['velocity'][0] or r['velocity'][1] for r in kicking)
                and any(r['pos'] != before_kick for r in kicking))
    if a.case in ('combo', 'mirror'):
        checks['rake_then_tear_in_one_ride'] = any(a['amount'] == 4096 and a['authored_hit'] and
            b['amount'] == 8192 and b['authored_hit'] and a['ride'] == b['ride'] and a['frame'] < b['frame']
            for a in damage for b in damage)
    if a.case == 'lethal':
        checks['native_hp_hit'] = hp_fixture[0] and bool(rows[-1]['private'][12])
        checks['native_victory_at_tear'] = any(r['victory'] and rows[i]['private'][17] > rows[max(0, i-3)]['private'][17]
            for i, r in enumerate(rows))
    if a.command == 'mini':
        checks['single_native_boss'] = all(len(r['enemies']) <= 1 for r in rows)
    if a.case == 'rake':
        checks.update(chosen_rake=bool(rows[-1]['private'][16]),
            native_hp_hit=any(d['authored_hit'] and d['amount'] == 0x1000 for d in damage))
    if a.case == 'shake':
        checks['native_attack_shakes_off'] = bool(rows[-1]['private'][18])
    if a.case == 'zip' and a.command == 'conductor':
        checks['native_heavy_yank_handoff'] = any(r['phase'] == 1 and not r['yank'][6]
            and any(p['yank'][0] == r['actor'] and p['yank'][6] and p['yank'][13] == 1
                and p['yank'][2] == r['private'][2] and p['yank'][18] > 0
                for p in rows[max(0, i-4):i]) for i, r in enumerate(rows))
        checks['native_yank_line_existed'] = any(r['yank'][6] and r['yank'][13] == 1 and r['yank'][24] for r in rows)
        checks['no_jump_substitution'] = not any('B' in r['buttons'] for r in rows)
    if a.case == 'zip' and a.command == 'mini':
        checks['native_mini_zip_then_latch'] = any(r['phase'] == 6 for r in rows) and any(r['phase'] == 1 for r in rows)
    if faults and faults[0] >= 0:
        checks['fault_releases'] = not any(r['phase'] for r in rows if r['frame'] >= faults[0]+3)
    if a.case == 'wall':
        checks.update(no_damage_through_wall=not rows[-1]['private'][12],
            active_close_wall_separation=any(r['phase'] and e['actor']+4 == r['private'][2]
                and 6*4096 < abs(e['position'][0]-r['pos'][0]) <= 9*4096
                and abs(e['position'][1]+10*4096-r['pos'][1]) < 8*4096 for r in rows for e in r['enemies']),
            fresh_strike_in_hold=any(r['phase'] == 2 and 'Y' in r['buttons'] and 'Y' not in rows[i-1]['buttons']
                for i, r in enumerate(rows) if i),
            separation_releases_before_attack=bool(active) and not any(r['phase'] in (3, 4) for r in rows),
            native_wall_stops_player=max(r['pos'][0] for r in rows) < 240*4096,
            target_remains_across_wall=any(e['position'][0] > 240*4096 for r in rows for e in r['enemies']))
    report = dict(passed=all(checks.values()), checks=checks, damage=damage, case=a.case, target=a.command, rows=rows,
        rom_sha256=w.sha256(source_rom.read_bytes()), fixture_sha256=w.sha256(a.rom.read_bytes()),
        source_battery_sha256=w.sha256(before), route=route['captures'], audio=str(a.out/(a.tag+'-'+a.tag+'.wav')),
        limits='Latest actual DSV copy, measured current ownership/XP, compiled initial room arrival, '
        'disposable Boarding bit and player healing. Mini uses its own original native arena, placement, '
        'encounter script and pre-input player layouts; dialogue is dismissed with A and the defeated '
        'flag is reset in disposable RAM. Wall uses a parked native '
        'target across Test_Combat01 boundary, with a precompiled idle-only thinker for that fixture; '
        'only that target is parked during the move. Otherwise '
        'approach/jump/Y/A/R/L, boss AI, HP, gravity and collision remain native. '
        'Named hurt/death/room/form/target fault cases inject only that interruption after boarding; '
        'lethal alone sets the linked boss to one HP once before the real tear. '
        'No research save adoption, campaign entrance, victory, difficulty or player-acceptance claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps(dict(passed=report['passed'], checks=checks, starts=rows[-1]['private'][15],
        rakes=rows[-1]['private'][16], rips=rows[-1]['private'][17], shakes=rows[-1]['private'][18], route=report['route'])), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('conductor', 'mini', 'shop'))
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--owned', type=Path, required=True)
    p.add_argument('--tag', required=True)
    p.add_argument('--case', default='regular', choices=('regular', 'mirror', 'wall', 'rake', 'combo', 'lethal', 'zip', 'hold', 'shake', 'cancel', 'cancel-no-air-dodge', 'swap',
        'unowned', 'red', 'hurt', 'death', 'room', 'form', 'target-dead', 'target-stale'))
    p.add_argument('--subtype', type=int, choices=range(4), default=0)
    p.add_argument('--frames', type=int, default=650)
    p.add_argument('--capture-every', type=int, default=6)
    a = p.parse_args()
    a.rom, a.out, a.owned = a.rom.resolve(), a.out.resolve(), a.owned.resolve()
    if not a.out.is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Boarding evidence belongs in work/')
    if a.command == 'shop':
        from tools.hunter_kit_lab import shop
        sys.exit(shop(a, row=11, bit=88, price=275))
    sys.exit(run(a))
