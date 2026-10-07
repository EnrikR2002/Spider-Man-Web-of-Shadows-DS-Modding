"""Midnight Line lab: chapter checks plus the earlier foundation experiments.

Chapter checks on a built ROM (default build/midnight-line/chapter.nds; the
build itself is tools/midnight_chapter.py): `tour` rides every door once,
`save-test` saves in the Refuge and Continues, `ambush` fights in ML_Service
(`--native` runs the Sewer_Map02 control). They use copied batteries, a lab
warp through the Test Upgrades entry and teleports; stage-platform/probe-room
are superseded research. Nothing here publishes or edits a real battery.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import mod
from tools import room_catalog, room_collision, room_objects, wos_tool as w

OUT = ROOT / 'work/midnight-line'
BUILD = ROOT / 'build/midnight-line'


def survey():
    rom, glob, manifest = mod.load_clean()
    at, _, _, size = struct.unpack_from('<4I', rom, 0x20)
    entries = manifest['entries']
    names = [e['name'] for e in entries]
    def blob(index):
        e = entries[index]
        return glob[e['offset']:e['offset'] + e['size']]
    rows = []
    for room in room_catalog.parse(rom[at:at + size], names):
        objects = room_objects.RoomObjects.parse(blob(room.objects))
        collision = room_collision.RoomCollision.parse(blob(room.bsp))
        rows.append({'index': room.index, 'name': room.name, 'descriptor': hex(room.address),
                     'texture': names[room.texture], 'bsp': names[room.bsp], 'objects': names[room.objects],
                     'minimap': names[room.minimap], 'object_count': len(objects.records),
                     'node_count': len(collision.nodes), 'list_count': len(collision.lists),
                     'object_roundtrip': objects.to_bytes() == blob(room.objects),
                     'bsp_roundtrip': collision.to_bytes() == blob(room.bsp),
                     'labels': [list(block.labels) for block in objects.names]})
    report = {'schema_version': 1, 'original_sha256': w.sha256(rom), 'lookup': hex(room_catalog.LOOKUP),
              'confidence': 'Envelope and lookup structures; labels are advisory, event semantics unknown', 'rooms': rows}
    w.write_json(OUT / 'room-survey.json', report)
    return report


def stage_collision():
    rom, glob, manifest = mod.load_clean()
    e = next(e for e in manifest['entries'] if e['name'] == 'Test_Combat01.bsp')
    raw = glob[e['offset']:e['offset'] + e['size']]
    parsed = room_collision.RoomCollision.parse(raw)
    if parsed.nodes[1] != (240 * 4096 + 1, 0x40000000, 8, 1):
        raise ValueError('Training BSP fixture changed')
    new = parsed.replace_unknown_word0(1, 180 * 4096 + 1)
    names = [x['name'] for x in manifest['entries']]
    blobs = [glob[x['offset']:x['offset'] + x['size']] for x in manifest['entries']]
    blobs[e['index']] = new
    candidate = w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(names, blobs)})
    path = BUILD / 'collision-wall-180.nds'
    w.atomic_write(path, candidate)
    report = {'schema_version': 1, 'status': 'staged-unqualified', 'original_sha256': w.sha256(rom),
              'candidate': str(path), 'candidate_sha256': w.sha256(candidate), 'resource': e['name'],
              'changed_node': 1, 'old_word0': parsed.nodes[1][0], 'new_word0': 180 * 4096 + 1,
              'hypothesis': 'word0 contains boundary coordinate plus low flag bits; changing 240 to 180 moves the right wall'}
    w.write_json(OUT / 'collision-stage.json', report)
    return report


def empty_training_group(objects, *, repair_init=False):
    """Bounded training-group experiment; retains base objects and unknown bytes.

    Both native 0x0d commands refer to the removed entity in runtime bank 1.
    Keeping only opcode 0x15 retains native Test Upgrades initialization. This
    is not a general entity deletion or reference-repair algorithm.
    """
    from tools.room_entities import Entities
    from tools.room_events import Events
    parsed = room_objects.RoomObjects.parse(objects)
    if len(parsed.records) != 3: raise ValueError('Expected three training object records')
    old_count = len(Entities.parse(parsed.records[2].sections[0]).records)
    names = parsed.names[2]
    if not old_count or old_count != names.category_ends[0] or any(
            not name.startswith('Character (Practice Dummy)') for name in names.labels[:old_count]):
        raise ValueError('Expected the bounded training dummy group')
    objects = parsed.replace_section(2,0,b'\x04\0\x04\0')
    changed = room_objects.RoomObjects.parse(objects)
    block = bytearray(changed.names[2].raw[:20])
    name_block = changed.names[2]
    struct.pack_into('<I',block,0,len(name_block.raw)-old_count*32)
    struct.pack_into('<7H',block,6,*(n-old_count for n in name_block.category_ends))
    block.extend(name_block.raw[20+old_count*32:])
    objects = changed.header + b''.join(r.raw for r in changed.records) + changed.between + b''.join(
        n.raw if i!=2 else bytes(block) for i,n in enumerate(changed.names))
    changed = room_objects.RoomObjects.parse(objects)
    if repair_init:
        events=Events.parse(changed.records[2].sections[1],changed.records[2].raw[3])
        if len(events.groups)!=1 or tuple(c.opcode for c in events.groups[0].commands)!=(0x15,0x0D,0x0D):
            raise ValueError('Training initialization commands changed')
        if tuple(c.operand for c in events.groups[0].commands[1:])!=(b'\0\x01\0\x01',b'\0\x01\x02\x01'):
            raise ValueError('Training dummy references changed')
        objects=changed.replace_section(2,1,events.omit_commands(0,(1,2)))
    return objects


def stage_platform(native_model=False, native_objects=True, challenge_group1=False, omit_dummy=False, empty_dummy=False, save_objects=False, repair_empty_init=False):
    from tools import model_geometry, oscorp_resources
    source = ROOT / 'build/Spider-Man-WoS-modded.nds'
    rom = source.read_bytes()
    source_hash = w.sha256(rom)
    expected = 'fd7e4420f97645dd55011504843ce62f068d1276234c3cd781931c85bb1eb193'
    if source_hash != expected: raise ValueError('Platform experiment requires the pinned v0.5.0 ROM')
    report = w.validate_rom(rom, target=True)
    entry = next(e for e in report['nitrofs'] if e['name'] == 'Glob.bin')
    glob = rom[entry['start']:entry['end']]
    offsets, names, _ = w.parse_glob(glob)
    blobs = [glob[a:z] for a,z in zip(offsets, offsets[1:])]
    def asset(name): return blobs[names.index(name)]
    model = asset('Test_Combat01.nsbmd') if native_model else model_geometry.platform_model(asset('Test_Combat01.nsbmd'))
    collision = room_collision.RoomCollision.parse(asset('Test_Combat01.bsp')).replace_unknown_word0(1, 180 * 4096 + 1)
    # Challenge OBJ is a minimal native setup containing Spidey and no dummy.
    objects = asset('Test_Combat01_app.obj') if native_objects else asset('Test_Challenge01_app.obj')
    if repair_empty_init and not empty_dummy: raise ValueError('Initialization repair requires --empty-dummy')
    if save_objects:
        if native_objects or omit_dummy or empty_dummy or challenge_group1:
            raise ValueError('Save-room object control must be isolated')
        objects = asset('Sewer_Save02_app.obj')
    parsed_objects = room_objects.RoomObjects.parse(objects)
    if omit_dummy:
        if not native_objects: raise ValueError('Dummy omission requires native OBJ')
        objects = parsed_objects.omit_record(2)
    if empty_dummy:
        if not native_objects or omit_dummy: raise ValueError('Empty-group experiment requires intact native OBJ')
        objects = empty_training_group(objects,repair_init=repair_empty_init)
    if challenge_group1:
        if native_objects: raise ValueError('Group experiment requires challenge OBJ')
        at = parsed_objects.records[1].offset + 4
        if struct.unpack_from('<I',objects,at)[0] != 0: raise ValueError('Challenge object header changed')
        edited = bytearray(objects)
        struct.pack_into('<I',edited,at,0x100)
        objects = bytes(edited)
        room_objects.RoomObjects.parse(objects)
    extras = {'zz_ml_platform.nsbmd': model, 'zz_ml_platform.bsp': collision,
              'zz_ml_platform_app.obj': objects, 'zz_ml_platformTextures.nsbtx': asset('Test_Combat01Textures.nsbtx')}
    # The accepted archive ends on a halfword boundary. Appended models need a
    # word-aligned start; a dedicated unreferenced padding resource preserves
    # every existing resource byte and avoids padding opaque asset payloads.
    padding = -len(glob) % 4
    if padding: extras = {'zz_ml_alignment.bin': bytes(padding), **extras}
    expanded_names, expanded_blobs = oscorp_resources.append_resources(names, blobs, extras)
    result = bytearray(w.rebuild_rom(rom, {'Glob.bin': w.pack_glob(expanded_names, expanded_blobs)}))
    arm9_at = struct.unpack_from('<I', result, 0x20)[0]
    if struct.unpack_from('<I', result, arm9_at + 0x77F8)[0] != len(names):
        raise ValueError('Native Glob resource count differs from parsed archive')
    struct.pack_into('<I', result, arm9_at + 0x77F8, len(expanded_names))
    checked = w.validate_rom(bytes(result), target=True)
    e = next(e for e in checked['nitrofs'] if e['name'] == 'Glob.bin')
    outglob = result[e['start']:e['end']]
    outoffs, outnames, table = w.parse_glob(outglob)
    if outnames != expanded_names: raise ValueError('Namespace append verification failed')
    for i, blob in enumerate(blobs):
        if i != table and bytes(outglob[outoffs[i]:outoffs[i+1]]) != blob:
            raise ValueError('An original resource changed')
    variant = ('native' if native_model else 'authored') + '-' + ('native' if native_objects else 'challenge')
    if challenge_group1: variant += '-group1'
    if omit_dummy: variant += '-no-dummy'
    if empty_dummy: variant += '-empty-group'
    if repair_empty_init: variant += '-repaired-init'
    if save_objects: variant += '-save-objects'
    path = BUILD / ('platform-' + variant + '.nds')
    w.atomic_write(path, bytes(result), sources=(source,))
    resources = {key: outnames.index(name) for key,name in {
        'model':'zz_ml_platform.nsbmd', 'bsp':'zz_ml_platform.bsp',
        'objects':'zz_ml_platform_app.obj', 'texture':'zz_ml_platformTextures.nsbtx'}.items()}
    record = {'schema_version':1, 'status':'development-shell-unqualified', 'source_sha256':source_hash,
              'candidate':str(path), 'candidate_sha256':w.sha256(result), 'resources':resources,
              'preserved_original_resources':len(names)-1, 'added_resources':list(extras),
              'variant':variant, 'limitations':'Native debug materials, no station events/exits/enemy or production loader'}
    w.write_json(OUT / 'platform-stage.json', record)
    w.write_json(OUT / ('platform-stage-' + record['candidate_sha256'][:8] + '.json'), record)
    return record


def collision_probe(mode):
    from tools import kit_lab as k
    rom = mod.DEFAULT_ROM if mode == 'control' else BUILD / 'collision-wall-180.nds'
    dest, rows = k.run(rom, 'ml-wall-' + mode, [{'start': 0, 'end': 240, 'buttons': ['Right']}],
                       frames=260, bits=0, start_x=120 * 4096, caps=(0, 120, 250), rams=(250,))
    positions = [r['pos'][0] for r in rows if r.get('pos')]
    if not positions: raise ValueError('No player observations')
    report = {'mode': mode, 'trace': str(dest / 'observations.json'),
              'maximum_x_q12': max(positions), 'last_x_q12': positions[-1],
              'captures': [str(p) for p in sorted(dest.glob('frame-*.png'))]}
    w.write_json(OUT / ('collision-' + mode + '.json'), report)
    return report


def room_probe_child(authored=False, exercise_return=False, mode=2, story_context=False):
    from tools import kit_lab as k, room_extension
    stage = json.loads((OUT / 'platform-stage.json').read_text()) if authored else None
    rom = Path(stage['candidate']) if authored else ROOT / 'build/Spider-Man-WoS-modded.nds'
    data = rom.read_bytes()
    source_hash = w.sha256(data)
    if authored and source_hash != stage['candidate_sha256']:
        raise ValueError('Staged room candidate hash changed')
    at, _, _, size = struct.unpack_from('<4I', data, 0x20)
    # Verify actual kit reservation before writing the disposable fixture.
    arm9 = data[at:at + size]
    if struct.unpack_from('<I', arm9, 0xFF374)[0] != room_extension.LIMIT:
        raise ValueError('Player ROM does not have the expected kit reservation')
    fs = next(e for e in w.validate_rom(data, target=True)['nitrofs'] if e['name'] == 'Glob.bin')
    _, names, _ = w.parse_glob(data[fs['start']:fs['end']])
    resources = json.loads((OUT / 'platform-stage.json').read_text())['resources'] if authored else None
    patches = room_extension.probe_image(arm9, names, resources,mode=mode,test_context=not story_context)
    applied = []
    def hook(frame, lib):
        if frame == 120:
            from tools.crash_hunt import serialize, describe
            state = serialize(lib)
            w.atomic_write(OUT / ('platform-' + stage['variant'] + '.state' if authored else 'room-registration.state'), state)
            w.write_json(OUT / ('platform-' + stage['variant'] + '-cpu.json' if authored else 'room-registration-cpu.json'), describe(state, k.ram_of(lib)[1]))
        if frame != -2500: return
        import ctypes as c
        ptr, ram = k.ram_of(lib)
        for patch in patches:
            at = patch['addr'] - 0x02000000
            new, expected = bytes.fromhex(patch['hex']), bytes.fromhex(patch['expect'])
            if ram[at:at + len(expected)] != expected:
                raise ValueError(f"Room fixture expectation failed at {patch['addr']:x}")
            c.memmove(ptr + at, new, len(new))
            applied.append(hex(patch['addr']))
    label = 'ml-platform-shell' if authored else 'ml-room-registration'
    if mode != 2: label += '-mode' + str(mode)
    if story_context: label += '-story-context'
    inputs = [{'start':20, 'end':50, 'buttons':['Right']},
              {'start':60, 'end':90, 'buttons':['Left']},
              {'start':100, 'end':104, 'buttons':['B']}]
    if exercise_return:
        inputs += [{'start':160, 'end':166, 'buttons':['Start']},
                   {'start':220, 'end':226, 'buttons':['Down']},
                   {'start':260, 'end':266, 'buttons':['Down']},
                   {'start':300, 'end':306, 'buttons':['Down']},
                   {'start':340, 'end':346, 'buttons':['A']},
                   {'start':390, 'end':396, 'buttons':['A']}]
        label += '-return'
    caps = (0,120,200,450) if exercise_return else (0,120,250)
    dest, rows = k._run(rom, label, inputs, frames=500 if exercise_return else 260, bits=0, caps=caps,
                       rams=(120,450) if exercise_return else (120,), probe=(k.KIT_STATE,4), extra_hook=hook, core_options=k.NO_JIT)
    if w.sha256(rom.read_bytes()) != source_hash: raise ValueError('Probe source ROM changed')
    ram = (dest / 'ram-03150.bin').read_bytes()
    stats = struct.unpack_from('<I', ram, k.STATS_POINTER - 0x02000000)[0] - 0x02000000
    report = {'schema_version': 1, 'status': 'probe-only', 'applied': applied,
              'entry_mode':mode, 'test_context':not story_context,
              'rom_sha256': source_hash, 'source_rom_unchanged': True,
              'current_room': struct.unpack_from('<I', ram, stats)[0],
              'expected_room': room_extension.FIRST, 'player_present': any(r.get('pos') for r in rows),
              'captures': [str(x) for x in sorted(dest.glob('frame-*.png'))],
              'trace': str(dest / 'observations.json'),
              'limit': 'Authored development shell' if authored else 'Cloned native room resources; no authored station, transitions or save validation'}
    checks = {'room_76': report['current_room'] == room_extension.FIRST,
              'player_present': report['player_present'],
              'kit_updates_continue': len({r['probe'][0] for r in rows if r.get('probe')}) > 60,
              **input_motion_checks(rows),
              'captures_not_black': all(capture_not_black(Path(p)) for p in report['captures'])}
    report['checks'] = checks
    if exercise_return:
        final_ram = (dest / 'ram-03480.bin').read_bytes()
        stats_at = struct.unpack_from('<I', final_ram, k.STATS_POINTER - 0x02000000)[0] - 0x02000000
        report['return_room'] = struct.unpack_from('<I',final_ram,stats_at)[0]
        # Capture the result even if the exploratory menu sequence didn't select
        # Return. A pause screenshot is evidence, not a successful transition.
        checks['return_to_native_room'] = report['return_room'] < 75
    report['passed'] = all(checks.values())
    report['status'] = 'probe-passed' if report['passed'] else 'probe-failed'
    out = OUT / ('platform-probe.json' if authored else 'room-registration.json')
    w.write_json(out, report)
    if authored:
        w.write_json(OUT / ('platform-probe-' + stage['candidate_sha256'][:8] + '-mode' + str(mode)
                            + ('-story-context' if story_context else '') + '.json'), report)
    print('ML_ROOM_REPORT ' + str(out), flush=True)


def input_motion_checks(rows):
    """Require scripted horizontal responses and jump state; falling is insufficient."""
    def xs(first,last): return [r['pos'][0] for r in rows if first<=r['f']<=last and r.get('pos')]
    before,right,left=xs(0,15),xs(50,60),xs(90,99)
    return {'movement_responds':bool(before and right and left and
                                     max(right)-before[0]>2*4096 and max(right)-min(left)>2*4096),
            'jump_responds':any(100<=r['f']<=125 and r.get('st')==15 for r in rows)}


def capture_not_black(path):
    """Check the harness's RGB PNG captures, not arbitrary imported images."""
    data = path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('Invalid PNG capture')
    at, compressed = 8, bytearray()
    while at < len(data):
        length = struct.unpack_from('>I',data,at)[0]
        tag = data[at+4:at+8]
        if tag == b'IDAT': compressed.extend(data[at+8:at+8+length])
        at += length+12
    return any(zlib.decompress(compressed))


TOUR_SETTLE, TOUR_STEP_LIMIT = 60, 420


def tour_plan(rom_path):
    """Door centres and expected arrivals for midnight_chapter.TOUR, read from the ROM."""
    from tools import midnight_chapter as ch, room_doors
    from tools.room_entities import Entities
    data = Path(rom_path).read_bytes()
    fs = next(e for e in w.validate_rom(data, target=True)['nitrofs'] if e['name'] == 'Glob.bin')
    glob = data[fs['start']:fs['end']]
    offsets, names, _ = w.parse_glob(glob)
    def obj(room):
        name = ('zz_' + room if room in ch.BY_NAME else room) + '_app.obj'
        i = names.index(name)
        return glob[offsets[i]:offsets[i + 1]]
    def index(room): return ch.BY_NAME[room].index if room in ch.BY_NAME else 65
    steps = []
    for room, group in ch.TOUR:
        raw = obj(room)
        parsed = room_objects.RoomObjects.parse(raw)
        trigger = next(e for e in Entities.parse(parsed.records[0].sections[0]).records
                       if len(e) == 28 and struct.unpack_from('<I', e, 12)[0] == 7 and e[27] == group + 1)
        dest = next(x for x in room_doors.exits(raw) if x.record == 0 and x.group == group)
        dest_name = next((r.name for r in ch.ROOMS if r.index == dest.room), ch.ENTRANCE)
        spawn = next(s for s in room_doors.spawns(obj(dest_name)) if s.spawn_id == dest.spawn)
        steps.append({'room': room, 'room_index': index(room), 'group': group,
                      'trigger': list(struct.unpack_from('<2i', trigger)), 'dest': dest_name,
                      'dest_index': dest.room, 'spawn': dest.spawn, 'spawn_xy': [spawn.x, spawn.y]})
    return steps


def tour_child(rom_path):
    """One run: warp into the entrance room, then ride every chapter door once."""
    import ctypes as c
    from tools import kit_lab as k, player_trace as p
    rom = Path(rom_path)
    source_hash = w.sha256(rom.read_bytes())
    steps = tour_plan(rom)
    warp = OUT / 'tour-warp.json'
    m = lambda reg, v: struct.pack('<I', 0xE3A00000 | (reg << 12) | v).hex()
    w.write_json(warp, [{'addr': 0x020ED7AC, 'hex': m(1, 0), 'expect': m(1, 1)},     # story context
                        {'addr': 0x020ED7B4, 'hex': m(2, 65), 'expect': m(2, 0x46)},  # Sewer_Save02
                        {'addr': 0x020ED7DC, 'hex': m(2, 1), 'expect': m(2, 2)},      # record 1
                        {'addr': 0x020ED7E0, 'hex': m(3, 1), 'expect': m(3, 0)}])     # spawn 1
    state = {'step': 0, 'since': None, 'teleported': False, 'arrivals': [], 'error': None, 'last': None}
    def room_of(ram):
        stats = struct.unpack_from('<I', ram, k.STATS_POINTER - p.BASE)[0] - p.BASE
        return struct.unpack_from('<I', ram, stats)[0]
    def hook(frame, lib):
        if frame < 0 or state['error'] or state['step'] > len(steps): return
        ptr, ram = k.ram_of(lib)
        try: sample = p.sample(ram)
        except ValueError: return                       # loading: no live Spidey
        room, step = room_of(ram), state['step']
        here = steps[step]['room_index'] if step < len(steps) else steps[-1]['dest_index']
        position = sample['position_q12_candidate']
        if step and room == steps[step - 1]['dest_index'] and state['since'] is None:
            state['since'] = frame
            state['arrivals'].append({'frame': frame, 'room': room, 'previous': state['last']})
        if not step and room == here and state['since'] is None: state['since'] = frame
        state['last'] = position
        if state['since'] is None: return
        arrival = state['arrivals'][-1] if step else {}
        # The spawn placement appears within a few frames (sometimes after a
        # default-position frame); native entry then walks Spidey ~12 units in
        # from side doors or drops him from overhead ones.
        if step and frame - state['since'] < 20 and position not in ([0, 0], arrival['previous']):
            arrival.setdefault('early', []).append(position)
        if step and frame - state['since'] == TOUR_SETTLE - 1:
            arrival['settled'] = position
        if step == len(steps):
            if frame - state['since'] >= TOUR_SETTLE: state['step'] += 1
            return
        if frame - state['since'] > TOUR_STEP_LIMIT:
            state['error'] = f'step {step} ({steps[step]["room"]} group {steps[step]["group"]}) did not transition'
        elif room == here and frame - state['since'] == TOUR_SETTLE:
            k.teleport(ptr, ram, sample['motion_address'] - p.BASE, *steps[step]['trigger'])
            state['teleported'] = True
        elif room != here and state['teleported']:
            state.update(step=step + 1, since=None, teleported=False)
    frames = (TOUR_SETTLE + 120) * (len(steps) + 1) + 200
    dest, rows = k._run(rom, 'ml-chapter-tour', [], frames=frames, bits=0, patch=str(warp), caps=tuple(range(0, frames, 30)),
                        rams=(frames - 10,), extra_hook=hook, core_options=k.NO_JIT, sparring=True)
    if w.sha256(rom.read_bytes()) != source_hash: raise ValueError('Tour source ROM changed')
    results = []
    for step, arrival in zip(steps, [a for a in state['arrivals'] if 'settled' in a]):
        # Sampled positions sit ~5 units above the spawn origin.
        near = lambda xy: bool(xy) and abs(xy[0] - step['spawn_xy'][0]) <= 4096 and abs(xy[1] - step['spawn_xy'][1]) <= 6 * 4096
        results.append({**step, 'arrival': arrival, 'room_ok': arrival['room'] == step['dest_index'],
                        'spawn_ok': any(map(near, arrival.get('early', []))) or near(arrival['settled'])})
    captures = sorted(dest.glob('frame-*.png'))
    checks = {'all_doors_taken': len(results) == len(steps) and not state['error'],
              'arrival_rooms': all(r['room_ok'] for r in results) and len(results) == len(steps),
              'arrival_spawns': all(r['spawn_ok'] for r in results) and len(results) == len(steps),
              'captures_not_black': bool(captures) and sum(capture_not_black(x) for x in captures) > len(captures) // 2}
    final = (dest / f'ram-{k.TRAINING_START + frames - 10:05d}.bin').read_bytes()
    stats = struct.unpack_from('<I', final, k.STATS_POINTER - p.BASE)[0] - p.BASE
    flags = int.from_bytes(final[stats + 0x1C:stats + 0x44], 'little')
    from tools import midnight_chapter as ch
    checks['visited_flags_set'] = all(flags >> (ch.VISITED_BASE + r.index) & 1 for r in ch.ROOMS)
    checks['no_other_chapter_flags'] = not any(flags >> f & 1 for f in ch.FREE_FLAGS
                                               if f not in {ch.VISITED_BASE + r.index for r in ch.ROOMS})
    report = {'schema_version': 1, 'rom_sha256': source_hash, 'source_rom_unchanged': True,
              'checks': checks, 'passed': all(checks.values()), 'error': state['error'], 'steps': results,
              'trace': str(dest / 'observations.json'), 'captures': [str(x) for x in captures],
              'limit': 'Lab warp into the entrance room and teleports onto door triggers; walking routes are separate'}
    w.write_json(OUT / 'chapter-tour.json', report)
    w.write_json(OUT / f'chapter-tour-{source_hash[:8]}.json', report)
    print('ML_ROOM_REPORT ' + str(OUT / 'chapter-tour.json'), flush=True)


def ambush_child(rom_path, seed=11, native=False):
    """ML_Service ambush: starts once, its chapter flag persists, the doors reopen.

    Lab fixtures: warp, Spidey placed at the ambush trigger, Spidey kept alive
    and enemy HP capped at 1 so random kit fighting finishes the wave.
    """
    import ctypes as c
    from tools import crash_hunt, kit_lab as k, midnight_chapter as ch, player_trace as p
    rom = Path(rom_path)
    source_hash = w.sha256(rom.read_bytes())
    service, switching = ch.BY_NAME['ML_Service'].index, ch.BY_NAME['ML_Switching'].index
    flag = 268                                     # Sewer_Map02 ambush flag 0x42, remapped
    if native:                                     # control: the source room itself
        service, switching, flag = 52, 53, 0x42
    m = lambda reg, v: struct.pack('<I', 0xE3A00000 | (reg << 12) | v).hex()
    warp = OUT / 'ambush-warp.json'
    w.write_json(warp, [{'addr': 0x020ED7AC, 'hex': m(1, 0), 'expect': m(1, 1)},
                        {'addr': 0x020ED7B4, 'hex': m(2, service), 'expect': m(2, 0x46)},
                        {'addr': 0x020ED7DC, 'hex': m(2, 1), 'expect': m(2, 2)},
                        {'addr': 0x020ED7E0, 'hex': m(3, 1), 'expect': m(3, 0)}])
    exit_door = [int(341.2 * 4096), int(-75.7 * 4096)] if native else next(
        s for s in tour_plan(rom) if s['room'] == 'ML_Service' and s['group'] == 2)['trigger']
    fight = 3600
    inputs = OUT / 'ambush-inputs.json'
    w.write_json(inputs, crash_hunt.fight_script(seed, fight))
    state = {'flag_frame': None, 'max_enemies': 0, 'clear_since': None, 'left_at': None, 'room_after': None}
    def stats_of(ram):
        return struct.unpack_from('<I', ram, k.STATS_POINTER - p.BASE)[0] - p.BASE
    def hook(frame, lib):
        if frame < 0: return
        ptr, ram = k.ram_of(lib)
        stats = stats_of(ram)
        if not 0 <= stats < len(ram) - 0x98: return
        room = struct.unpack_from('<I', ram, stats)[0]
        flags = int.from_bytes(ram[stats + 0x1C:stats + 0x44], 'little')
        if state['flag_frame'] is None and flags >> flag & 1: state['flag_frame'] = frame
        try: sample = p.sample(ram)
        except ValueError: return
        if frame == 30 and room == service:      # ambush trigger at x~170.7
            k.teleport(ptr, ram, sample['motion_address'] - p.BASE, 168 * 4096, 12 * 4096)
        live = [e for e in k.enemies(ram) if e['hp'] > 0 and e['state'] != 6]
        state['max_enemies'] = max(state['max_enemies'], len(live))
        if frame % 10 == 0 and frame <= fight:
            hp = struct.unpack_from('<I', ram, sample['actor_address'] - p.BASE + 0xE4)[0] - p.BASE
            if 0 <= hp < len(ram) - 0x90:        # keep Spidey alive
                top = struct.unpack_from('<i', ram, hp + 0x88)[0]
                c.memmove(ptr + hp + 0x84, struct.pack('<i', top), 4)
            for e in live:                        # one hit finishes each enemy
                if e['hp'] > 1: c.memmove(ptr + e['actor'] - p.BASE + 0x44, struct.pack('<i', 1), 4)
        if state['flag_frame'] is not None and frame > 200 and not live and state['max_enemies']:
            state['clear_since'] = state['clear_since'] or frame
        else:
            state['clear_since'] = None if live else state['clear_since']
        # Doors reopen some time after the wave: try the exit every 120 frames,
        # parking Spidey on the floor beside it in between (no void falls).
        if frame >= fight and room == service and state['room_after'] is None:
            phase = (frame - fight) % 120
            if phase == 0:
                k.teleport(ptr, ram, sample['motion_address'] - p.BASE, *exit_door)
                state['left_at'] = frame
            elif phase == 40:
                k.teleport(ptr, ram, sample['motion_address'] - p.BASE, exit_door[0] - 24 * 4096, exit_door[1] + 4 * 4096)
        if state['left_at'] is not None and room != service and state['room_after'] is None:
            state['room_after'] = room
    frames = fight + 1300
    label = ('ml-ambush-native-' if native else 'ml-ambush-') + str(seed)
    dest, rows = k._run(rom, label, str(inputs), frames=frames, bits=0xFEF00, patch=str(warp),
                        caps=tuple(range(0, frames, 150)), rams=(frames - 10,), extra_hook=hook,
                        core_options=k.NO_JIT, sparring=True)
    final = (dest / f'ram-{k.TRAINING_START + frames - 10:05d}.bin').read_bytes()
    stats = stats_of(final)
    flags = int.from_bytes(final[stats + 0x1C:stats + 0x44], 'little')
    chapter = [i for i in ch.FREE_FLAGS if flags >> i & 1]
    # Fights here are not deterministic: whether the "Unblock Doors" group runs
    # (incrementing the ambush flag) varies between runs, natively too.
    checks = {'enemies_spawned': state['max_enemies'] > 0,
              'exit_works_after_fight': state['room_after'] == switching,
              'only_chapter_flags_written': native or set(chapter) <= {flag, *(ch.VISITED_BASE + r.index for r in ch.ROOMS)},
              'rom_unchanged': w.sha256(rom.read_bytes()) == source_hash}
    report = {'schema_version': 1, 'rom_sha256': source_hash, 'seed': seed, 'checks': checks,
              'passed': all(checks.values()), **state, 'ambush_flag_set': state['flag_frame'] is not None,
              'chapter_flags': chapter,
              'trace': str(dest / 'observations.json'), 'captures': [str(x) for x in sorted(dest.glob('frame-*.png'))],
              'limit': 'Lab warp/teleports, Spidey kept alive and enemy HP capped at 1; not a balance test'}
    name = ('chapter-ambush-native' if native else 'chapter-ambush') + f'-seed{seed}'
    w.write_json(OUT / f'{name}.json', report)
    w.write_json(OUT / f'{name}-{source_hash[:8]}.json', report)
    print('ML_ROOM_REPORT ' + str(OUT / f'{name}.json'), flush=True)


def refuge_save_child(rom_path, label):
    """Save at the ML_Refuge save point (copied battery), then boot it and Continue."""
    import ctypes as c
    from tools import emulator_smoke as emu, kit_lab as k, player_trace as p
    from tools import midnight_chapter as ch
    rom = Path(rom_path)
    source_hash = w.sha256(rom.read_bytes())
    refuge = ch.BY_NAME['ML_Refuge'].index
    m = lambda reg, v: struct.pack('<I', 0xE3A00000 | (reg << 12) | v).hex()
    warp = [{'addr': 0x020ED7AC, 'hex': m(1, 0), 'expect': m(1, 1)},
            {'addr': 0x020ED7B4, 'hex': m(2, refuge), 'expect': m(2, 0x46)},
            {'addr': 0x020ED7DC, 'hex': m(2, 1), 'expect': m(2, 2)},
            {'addr': 0x020ED7E0, 'hex': m(3, 0), 'expect': m(3, 0)}]
    start = k.TRAINING_START
    prefix = [r for r in json.loads((ROOT / 'reference/combat-inputs/oscorp-owned.json').read_text()) if r['start'] < 3000]
    # X opens Save Options at the sphere; A = Save, A = Yes (frames reviewed).
    script = prefix + [{'start': start + a, 'end': start + a + 6, 'buttons': [b]} for a, b in ((220, 'X'), (280, 'A'), (360, 'A'))]
    save = k.TRAINING_SAVE
    save_hash = w.sha256(save.read_bytes())
    def hook(frame, lib):
        if frame in (60, start - 40): k.apply_patches(lib, warp, frame == 60)
    done = start + 640
    first = emu.run(rom, done, {start + 100, start + 300, start + 420, start + 600}, save_path=save, script=script,
                    label=label + '-save', frame_hook=hook, ram_captures={start + 600}, battery_captures={done - 10},
                    core_options=k.NO_JIT)
    battery = next(first.glob(f'battery-{done - 10:05d}.*'))
    ram = (first / f'ram-{start + 600:05d}.bin').read_bytes()
    stats = struct.unpack_from('<I', ram, k.STATS_POINTER - p.BASE)[0] - p.BASE
    saved_room = struct.unpack_from('<I', ram, stats)[0]
    reload_script = [r for r in prefix if r['start'] < 1400]           # title + Continue only
    second = emu.run(rom, 2400, {1500, 1800, 2300}, save_path=battery, script=reload_script,
                     label=label + '-reload', ram_captures={1800, 2300}, core_options=k.NO_JIT)
    rows = {}
    for f in (1800, 2300):
        ram = (second / f'ram-{f:05d}.bin').read_bytes()
        stats = struct.unpack_from('<I', ram, k.STATS_POINTER - p.BASE)[0] - p.BASE
        if not 0 <= stats <= len(ram) - 0x98:          # rejected save: no game state
            rows[f] = {'room': None, 'player': False, 'chapter_flags': []}
            continue
        try: present = bool(p.sample(ram))
        except ValueError: present = False
        flags = int.from_bytes(ram[stats + 0x1C:stats + 0x44], 'little')
        rows[f] = {'room': struct.unpack_from('<I', ram, stats)[0], 'player': present,
                   'chapter_flags': [i for i in ch.FREE_FLAGS if flags >> i & 1]}
    captures = [str(x) for x in sorted(first.glob('frame-*.png')) + sorted(second.glob('frame-*.png'))]
    checks = {'saved_in_refuge': saved_room == refuge,
              'continue_restores_refuge': rows[2300]['room'] == refuge,
              'player_after_continue': rows[2300]['player'],
              'refuge_visited_flag_saved': ch.VISITED_BASE + refuge in rows[2300]['chapter_flags'],
              'source_battery_unchanged': w.sha256(save.read_bytes()) == save_hash,
              'rom_unchanged': w.sha256(rom.read_bytes()) == source_hash}
    report = {'schema_version': 1, 'rom_sha256': source_hash, 'checks': checks, 'passed': all(checks.values()),
              'saved_room': saved_room, 'reload': rows, 'battery': str(battery), 'captures': captures,
              'limit': 'Copied research battery; lab warp into the refuge'}
    w.write_json(OUT / f'{label}.json', report)
    w.write_json(OUT / f'{label}-{source_hash[:8]}.json', report)
    print('ML_ROOM_REPORT ' + str(OUT / f'{label}.json'), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('survey')
    for name in ('tour', '_tour-child', 'save-test', '_save-child', 'ambush', '_ambush-child'):
        lab = sub.add_parser(name)
        lab.add_argument('--rom', default=str(BUILD / 'chapter.nds'))
        lab.add_argument('--native', action='store_true', help='ambush: control in native Sewer_Map02')
        lab.add_argument('--seed', type=int, default=11, help='ambush: fight input seed')
    sub.add_parser('stage-collision')
    platform = sub.add_parser('stage-platform')
    platform.add_argument('--native-model', action='store_true')
    objects = platform.add_mutually_exclusive_group()
    objects.add_argument('--native-objects', dest='object_source', action='store_const',const='native')
    objects.add_argument('--challenge-objects', dest='object_source', action='store_const',const='challenge')
    objects.add_argument('--save-objects', dest='object_source', action='store_const',const='save')
    platform.set_defaults(object_source='native')
    platform.add_argument('--challenge-group1', action='store_true')
    platform.add_argument('--omit-dummy', action='store_true')
    platform.add_argument('--empty-dummy', action='store_true')
    platform.add_argument('--repair-empty-init', action='store_true',
                          help='Remove both initialization references to the deleted dummy')
    for name in ('probe-room', '_room-child'):
        child = sub.add_parser(name)
        child.add_argument('--authored', action='store_true')
        child.add_argument('--exercise-return', action='store_true')
        child.add_argument('--story-context',action='store_true',
                           help='Clear the Test Upgrades context flag; its Return menu is unavailable')
        child.add_argument('--mode',type=int,choices=(0,1,2),default=2,
                           help='OBJ record selected alongside base record 0 (disposable RAM)')
    probe = sub.add_parser('probe-collision')
    probe.add_argument('mode', choices=('control', 'candidate'))
    args = parser.parse_args()
    if args.command == 'survey':
        r = survey()
        print(f"75 rooms surveyed; {sum(x['object_count'] for x in r['rooms'])} object records; exact round trips")
    elif args.command == 'stage-collision': print(json.dumps(stage_collision(), indent=2))
    elif args.command == 'stage-platform':
        print(json.dumps(stage_platform(args.native_model,args.object_source=='native',args.challenge_group1,
                                        args.omit_dummy,args.empty_dummy,args.object_source=='save',args.repair_empty_init),indent=2))
    elif args.command == '_room-child': room_probe_child(args.authored,args.exercise_return,args.mode,args.story_context)
    elif args.command == '_tour-child': tour_child(args.rom)
    elif args.command == '_save-child':
        refuge_save_child(args.rom, 'chapter-save' if Path(args.rom).name == 'chapter.nds' else 'chapter-save-' + Path(args.rom).stem)
    elif args.command == '_ambush-child': ambush_child(args.rom, args.seed, native=args.native)
    elif args.command in ('tour', 'save-test', 'ambush'):
        child = {'tour': '_tour-child', 'save-test': '_save-child', 'ambush': '_ambush-child'}[args.command]
        done = subprocess.run([sys.executable, str(Path(__file__)), child, '--rom', args.rom,
                               *(['--native'] if args.native else []), '--seed', str(args.seed)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
        lines = [s[s.index('ML_ROOM_REPORT '):] for s in done.stdout.splitlines() if 'ML_ROOM_REPORT ' in s]
        if done.returncode or not lines:
            w.atomic_write(OUT / f'chapter-{args.command}-error.log', done.stdout.encode('utf-8'))
            raise ValueError(f'Chapter {args.command} failed; inspect work/midnight-line/chapter-{args.command}-error.log')
        report = json.loads(Path(lines[-1][15:]).read_text())
        print(json.dumps({key: report.get(key) for key in ('rom_sha256', 'checks', 'passed', 'error')}, indent=2))
    elif args.command == 'probe-room':
        done = subprocess.run([sys.executable, str(Path(__file__)), '_room-child',
                              *(['--authored'] if args.authored else []),
                              *(['--exercise-return'] if args.exercise_return else []),
                              *(['--story-context'] if args.story_context else []), '--mode',str(args.mode)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
        # The native core buffers stdout and can interleave its text with ours.
        lines = [s[s.index('ML_ROOM_REPORT '):] for s in done.stdout.splitlines() if 'ML_ROOM_REPORT ' in s]
        if done.returncode or not lines:
            w.atomic_write(OUT / 'room-registration-error.log', done.stdout.encode('utf-8'))
            raise ValueError('Room registration failed; inspect work/midnight-line/room-registration-error.log')
        print(Path(lines[-1][15:]).read_text())
    else: print(json.dumps(collision_probe(args.mode), indent=2))


if __name__ == '__main__': main()
