"""Exact v0.34.1 post-pass: combo Down+A pure pull and scoped catch VFX cleanup."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import web_yank_fix as parent, hunter_kit as foundation, tasm_kit as kit, wos_tool as w
from tools.chapter_spectacle_combat import replace_once
from tools.chapter_renewal_combat import asm
from tools.crane_row import target
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors

PARENT = '1b7c36928363fcfc821a4a0024e777a3b22c0c2735888709278d3a4f561c0bfa'
PARENT_PATH = ROOT/'build/version-0.34.1-final/Versioned.nds'
VERSION, DATE = '0.34.2', '2026-10-25'


SHARED = ('ram_ok', 'owned', 'xy', 'active', 'unlink_target')


def shared_symbols(at, values):
    text = parent.source()
    for name in sorted(values, key=len, reverse=True):
        text = text.replace(name, f'0x{values[name]:08x}')
    code = asm(text+'\n.word '+','.join(SHARED), at)
    if code[:-4*len(SHARED)] != parent.runtime(at, values):
        raise ValueError('Published helper exports differ')
    return dict(zip(('SHARED_'+n.upper() for n in SHARED), struct.unpack('<5I',code[-20:])))


def source():
    frozen = parent.source()
    selector = frozen[frozen.index('select_target:\n'):frozen.index('node_entry:\n')]
    selector = replace_once(selector, 'select_distance:\n', 'select_distance:\n cmp r0,#0xd000\n blo select_next\n')
    selector = replace_once(selector, 'select_loop:\n', 'select_loop:\n ldr r0,[r7]\n bl selected_already\n cmp r0,#0\n bne select_next\n')
    wrappers = frozen[frozen.index('node_entry:\n'):frozen.index('update_entry:\n')]
    a,b = wrappers.index('active:'),wrappers.index('animation_entry:')
    wrappers = wrappers[:a]+'active:\n b SHARED_ACTIVE\n\n'+wrappers[b:]
    a,b = wrappers.index(' ldr r0,=STATE\n ldr r1,[r0,#120]\n'),wrappers.index('animation_out:\n')
    wrappers = wrappers[:a]+wrappers[b:]
    wrappers = wrappers[:wrappers.index('string_evade:')]
    line = frozen[frozen.index('line_make:'):frozen.index('unlink_target:')]
    line = replace_once(line, ' mov r5,r1\n', ' mov r5,r1\n str r2,[sp,#36]\n')
    line = replace_once(line, ' ldr r0,=STATE\n', ' ldr r0,[sp,#36]\n')
    reel = (ROOT/'tools/web_yank_fix.s').read_text()
    reel = replace_once(reel, 'reel:\n push {r4-r8,lr}\n mov r4,r0\n ldr r5,=STATE\n',
        'reel_single:\n push {r4-r8,lr}\n sub sp,sp,#8\n mov r4,r0\n mov r5,r1\n add r2,r2,r2,lsl #1\n mov r2,r2,lsl #10\n add r2,r2,#0x6000\n str r2,[sp]\n')
    reel = replace_once(reel, ' ldr r1,[r5,#120]\n orr r0,r0,r1\n', '')
    reel = replace_once(reel, ' addeq r7,r0,#0x6000\n subne r7,r0,#0x6000\n',
        ' ldr r3,[sp]\n addeq r7,r0,r3\n subne r7,r0,r3\n')
    reel = replace_once(reel, 'reel_out:\n pop {r4-r8,pc}\n', 'reel_out:\n add sp,sp,#8\n pop {r4-r8,pc}\n')
    vectors = '\n'.join(' b '+n for n in ('object_input','node_entry','animation_entry','update_entry','string_evade','generic_evade','reel_entry','effect_entry'))+'\n'
    helpers = '\n'.join(n+':\n b SHARED_'+n.upper() for n in ('ram_ok','owned','xy','unlink_target'))
    return vectors+Path(__file__).with_suffix('.s').read_text()+selector+wrappers+line+reel+helpers+'\n .ltorg\n'


def runtime(at, values):
    text = source()
    for name in sorted(values, key=len, reverse=True):
        text = text.replace(name, f'0x{values[name]:08x}')
    code = asm(text, at)
    errors = literal_errors(code, text)+native_branch_errors(code, text, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Pure Web Yank assembly: '+str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Pure Web Yank requires exact published v0.34.1')
    meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    rt = meta['hunter_kit']['runtime']
    h = w.parse_header(rom)
    arm = rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    off, end = kit.SOURCE+rt['entry']-kit.TARGET, len(arm)-36
    frozen = parent.runtime(rt['entry'], rt['values'])
    if arm[off:off+len(frozen)] != frozen or any(arm[off+len(frozen):end]):
        raise ValueError('Published firm-reel code/tail differs')
    from tools import midnight_voltage as extension
    # Reuse the allocator after checking this newer exact parent above.
    image = extension.Runtime.__new__(extension.Runtime)
    image.rom, image.header, image.arm = rom, h, arm
    image.new, image.end, image.data = bytearray(arm), end, bytearray()
    image.start = kit.TARGET+end-kit.SOURCE
    records = image.alloc(bytes(4*128))
    entry = image.alloc()
    values = dict(rt['values'], RECORDS=records, OLD_A=target(0x020b4da0,w.u32(arm,0xb4da0)),
        **shared_symbols(rt['entry'],rt['values']))
    code = runtime(entry,values)
    image.data.extend(code)
    hooks = [(0x020b4da0, kit.branch(0x020b4da0,meta['hunters_return']['runtime']['entry']),entry),
             (0x020b721c, kit.branch(0x020b721c,rt['entry']),0xe92d40f0),
             (0x0209543c,0xe1d202b2,entry+28)]
    hooks += [(row['site'],kit.branch(row['site'],rt['entry']+4*i),entry+4*i)
              for i,row in enumerate(rt['hooks']) if i]
    for site,expected,value in hooks:
        if w.u32(arm,site-kit.BASE)!=expected:
            raise ValueError(f'Pure Web Yank parent hook differs at {site:#x}')
        struct.pack_into('<I',image.new,site-kit.BASE,value if site==0x020b721c else kit.branch(site,value))
    result=image.finish()
    newh=w.parse_header(result)
    new=result[newh['arm9_offset']:newh['arm9_offset']+newh['arm9_size']]
    names, blobs = foundation.assets.resources(result)
    before = tuple(blobs)
    from tools.qol_suits_menu import StringSlots
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}',
            meta['hunter_kit']['text_id']+2: 'Down + \ue600: pull up to 5 distant foes.\nThen Y to attack; Up + \ue600 to lift.\nHeavy: zip close. \ue604 exits.'})
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    changed = [n for n, a, b in zip(names, before, blobs) if a != b]
    if changed != ['American.strings', 'English.strings']:
        raise ValueError('Unexpected pure-pull resource scope')
    result = w.rebuild_rom(result, {'Glob.bin': w.pack_glob(names, blobs)}, legacy_gaps=True)
    w.validate_rom(result, target=True)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new),
        runtime=dict(entry=entry, state=rt['state'], records=records, record_bytes=128, max_targets=5, bytes=len(code), source_offset=end+512, block_source_offset=end, values=values,
            hooks=[dict(site=s, old=e, value=v) for s,e,v in hooks], allocation_bytes=w.align_up(len(image.data),0x1000), remaining_zero_tail=w.align_up(len(image.data),0x1000)-len(image.data)),
        modified_resources=changed, binding='Ground/combo Down+A; native direction and queued A',
        min_target_distance_q12=13*4096, utility_damage_q12=0, native_effect_skip_site=0x0209543c,
        allocation_bytes=w.align_up(len(image.data),0x1000), player_kit_32k_unchanged=True,
        scope='Up to five independent weak targets/lines; pure pull/zip and native idle return; close targets skipped. No auto rake/launch. '
              'Native X restored; A/Up+A/air Down+A delegate. Native hit FX retained outside the owned zero-HP catch.')
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Pure Web Yank differs from immutable release pin')
    return result, report


def generate(output, source=PARENT_PATH):
    source, output = Path(source), Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):
        raise ValueError('Candidates belong in build/')
    result, report = apply_rom(source.read_bytes())
    path = output/'Versioned.nds'
    validation = w.validate_rom(result, target=True)
    meta = json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'))
    ge = next(e for e in validation['nitrofs'] if e['name'] == 'Glob.bin')
    meta.update(web_yank_combo=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
        output=str(path.resolve()), rom_size=len(result), used_rom_size=validation['header']['used_rom_size'],
        nitrofs=validation['nitrofs'], header_crc16=validation['header']['header_crc16'],
        output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path, result, sources=(source,))
    w.write_json(path.with_suffix('.build.json'), meta)
    recipe = json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v'+VERSION, release_version=VERSION)
    w.write_json(output/'gameplay_profile.json', recipe)
    w.write_json(output/'changes.json', report)
    print(json.dumps(dict(path=str(path), sha256=report['rom_sha256'], runtime=report['runtime'])), flush=True)
    return path


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--source', type=Path, default=PARENT_PATH)
    a = p.parse_args()
    generate(a.out, a.source)
