"""Copied-current-save Talon Lift contacts, manual follow-up and isolation."""
import argparse
import ctypes as ct
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import kit_lab as k, vortex_forge_lab as v, wos_tool as w


def run(a):
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):
        raise ValueError('Talon lab evidence must stay in work/')
    actual, before, copied = v.copy_current(a.out)
    profile = json.loads(a.owned.read_text())
    if w.sha256(before) != profile['source_sha256']:
        raise ValueError('Actual battery changed; measure current player again')
    boot = (Path(profile['captures'])/'ram-03500.bin').read_bytes()
    hero = k.p.sample(boot)['actor_address'] - 0x02000000
    desired = 0 if a.case == 'red' else 1
    inputs = []
    if w.u32(boot, hero+0x34) != desired:
        inputs.append(dict(start=4, end=10, buttons=['L']))
    manual = a.case in ('manual', 'manual-mirror')
    mirror = a.case in ('mirror', 'wall', 'manual-mirror')
    inputs.extend((dict(start=30, end=36, buttons=['Left' if mirror else 'Right']),
                   dict(start=60, end=66, buttons=['Up', 'A'])))
    if manual:
        inputs.extend((dict(start=96, end=128, buttons=['B']), dict(start=112, end=118, buttons=['Y'])))
    if a.case == 'cancel':
        inputs.append(dict(start=66, end=72, buttons=['R']))
    if a.case == 'swap':
        inputs.extend((dict(start=66, end=72, buttons=['L']), dict(start=110, end=116, buttons=['L'])))
    if a.case == 'air':
        inputs.append(dict(start=48, end=54, buttons=['B']))
    if a.case == 'traversal':
        inputs[-1]['buttons'] = ['A']
        inputs.extend((dict(start=105, end=111, buttons=['B']), dict(start=121, end=127, buttons=['Down', 'A'])))
    meta = json.loads(a.rom.with_suffix('.build.json').read_text())
    resource = meta.get('talon_lift', {}).get('sca_id', 3506)
    appearance = meta['hunters_return']['shared_model']
    rows = []

    def hook(frame, lib):
        ptr, ram = k.ram_of(lib)
        if -20 <= frame < 70:
            for enemy in k.enemies(ram):
                if enemy['controller'] and enemy['state'] in (0, 1, 2, 15):
                    # Re-enter idle: writing only state0 leaves an old attack's live hitbox.
                    ct.memmove(ptr+enemy['controller']-0x02000000+0x14, bytes(4), 4)
                    ct.memmove(ptr+enemy['controller']-0x02000000+4, b'\x01', 1)
        if frame < 0:
            return
        sample = k.p.sample(ram)
        actor = sample['actor_address'] - 0x02000000
        mot = sample['motion_address'] - 0x02000000
        wrapper = w.u32(ram, mot+0x58) - 0x02000000
        model = w.u32(ram, wrapper+0x14) - 0x02000000
        slot = w.u32(ram, wrapper+0x29c)
        if slot not in (0, 1):
            raise ValueError('Unexpected native SCA blend slot')
        rows.append(dict(frame=frame, form=w.u32(ram, actor+0x34),
            sca=w.u32(ram, wrapper+0x1c4+0x78*slot),
            shape=list(struct.unpack_from('<2I', ram, model+appearance['shape_offset']+8)),
            texture_format=w.u32(ram, model+appearance['material_offset']+20)>>26&7,
            enemies=k.enemies(ram)))

    native = k.rows_from
    k.rows_from = lambda path: v.current_prefix(path) if str(path).endswith('oscorp-owned.json') else native(path)
    dx = -70 if a.case == 'whiff' else -7 if mirror else 7
    clear = 1<<21 if a.case == 'unowned' else 0
    try:
        route, obs = k._run(a.rom, a.tag, inputs, frames=190, bits=0 if clear else 1<<21, clear=clear,
            sparring=True, start_x=(5 if a.case == 'wall' else 100)*4096,
            place=((dx*4096, 246), (-80*4096, 246), (-85*4096, 246)), save=copied,
            caps=tuple(range(56, 125, 2)), rams=(66, 75, 99, 118), extra_hook=hook,
            core_options={b'melonds_jit_enable': b'enabled', b'melonds_jit_block_size': b'12'})
    finally:
        k.rows_from = native
    active = [r for r in obs if r['st'] == 45 and r['act'] == 128]
    drawn = [rows[r['f']] for r in active]
    selected = bool(drawn) and all(r['sca'] == resource for r in drawn)
    origin = next(r['pos'] for r in obs if r['f'] == 0)
    target = min(rows[0]['enemies'], key=lambda e: abs(e['position'][0]-origin[0])+abs(e['position'][1]-origin[1]))['actor']
    foes = [next(e for e in row['enemies'] if e['actor'] == target) for row in rows]
    damage = [dict(frame=i, hp=enemy['hp']) for i, enemy in enumerate(foes)
              if i >= 60 and enemy['hp'] < foes[i-1]['hp']]
    launched = any(e['state'] == 39 for e in foes[60:])
    jump = any(r['st'] == 15 for r in obs if r['f'] >= 60)
    checks = dict(source_battery_unchanged=actual.read_bytes() == before and copied.read_bytes() == before)
    blocked = a.case in ('unowned', 'red', 'air', 'traversal')
    if blocked:
        checks['no_talon_route'] = not active
        if a.case == 'traversal':
            checks['native_dash_and_air_slam'] = any(r['st'] == 44 for r in obs) and any(r['st'] == 35 for r in obs) and any(r['st'] == 36 for r in obs)
    else:
        checks['private_clip_selected'] = selected
        checks['black_draw_and_texture'] = bool(drawn) and all(r['form'] == 1 and r['texture_format'] == 4 and
            r['shape'] == appearance['trailer'][6:8] for r in drawn)
        if a.case == 'cancel':
            checks['early_native_r_exit'] = any(66 <= r['f'] <= 70 and r['st'] in (52, 53, 54, 55, 57) for r in obs)
            checks['no_hit_after_cancel'] = not damage and not launched
        elif a.case == 'swap':
            checks['native_suit_switch_recovers'] = rows[-1]['form'] == 0 and obs[-1]['st'] not in (45, 63)
        elif a.case in ('whiff', 'wall'):
            checks['grounded_whiff_recovers'] = not jump and any(r['f'] > 95 and r['st'] == 0 for r in obs)
        else:
            checks['native_hp_loss_and_launch'] = bool(damage) and launched
            checks['manual_b_only'] = jump if manual else not jump
            if manual:
                checks['air_y_followup'] = any(r['st'] == 51 and 1 <= r['act'] <= 4 for r in obs)
                checks['air_y_damages_launched_target'] = len(damage) >= 2
        checks['native_collision_bounds'] = all(3.4*4096 <= r['pos'][0] <= 237*4096 for r in obs)
    report = dict(passed=all(checks.values()), case=a.case, checks=checks, rom_sha256=w.sha256(a.rom.read_bytes()),
        route=str(route), source_battery_sha256=w.sha256(before), target_actor=target, damage=damage, launched=launched,
        sequence=k.seq(obs), rows=rows,
        limits='Latest actual DSV copy, ordinary Continue/Test Upgrades. Disposable initial form, purchase bit21, '
        'positions and idle enemy prefix through70; native AI/contact/damage/reactions afterward. Training '
        'healing/immortality apply. No actual save writes or campaign-balance/DeSmuME-pacing claim.')
    w.write_json(a.out/'result.json', report)
    print(json.dumps({key: report[key] for key in ('passed', 'case', 'checks', 'route')}), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--owned', type=Path, required=True)
    p.add_argument('--case', choices=('regular', 'manual', 'manual-mirror', 'mirror', 'wall', 'whiff', 'cancel', 'unowned', 'red', 'air', 'swap', 'traversal'), default='regular')
    p.add_argument('--tag', required=True)
    sys.exit(run(p.parse_args()))
