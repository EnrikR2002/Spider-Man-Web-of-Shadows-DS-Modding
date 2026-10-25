"""Exact v0.34.0 post-pass: firm grounded Web Yank and shorter authored recovery."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import hunter_kit as parent, tasm_kit as kit, wos_tool as w, web_yank_fix_art as art
from tools.chapter_spectacle_combat import replace_once
from tools.chapter_renewal_combat import asm
from tools.assemble_tasm_kit import literal_errors, native_branch_errors, self_branch_errors

PARENT = 'a1557f5ada6134cc459aa42ee3edcda72b74e3640fe9d711317264e3d8b022bb'
PARENT_PATH = ROOT/'build/version-0.34.0-final/Versioned.nds'
VERSION, DATE = '0.34.1', '2026-10-24'


def source():
    text = Path(parent.__file__).with_suffix('.s').read_text(encoding='utf-8')
    text = replace_once(text, ' b generic_evade\n', ' b generic_evade\n b reel\n')
    text = replace_once(text, ' str r6,[r7]\n', ''' str r6,[r7]
 add r1,r6,#4
 ldr r2,[r1]
 str r1,[r7,#112]
 str r2,[r7,#116]
 add r2,r7,#112
 str r2,[r1]
 ldr r0,[r6,#0x30]
 ldr r0,[r0,#0x180]
 str r0,[r7,#124]
''')
    text = replace_once(text, ' cmp r0,#0xd000\n movlo r0,#1\n', ' cmp r0,#0x8000\n movlo r0,#1\n')
    text = replace_once(text, ' bl update\n', ' bl update\n mov r0,r4\n bl reel\n')
    text = replace_once(text, ' str r0,[r7,#84]\n', ' str r0,[r7,#84]\n str r0,[r7,#120]\n')
    text = replace_once(text, ' ldr r0,[r0,#88]\n', ' ldr r1,[r0,#120]\n ldr r0,[r0,#88]\n orr r0,r0,r1\n')
    text = replace_once(text, ' moveq r1,#23\n movne r1,#11\n', ' moveq r1,#17\n movne r1,#7\n')
    text = replace_once(text, ' str r1,[sp,#8]\n', ''' str r1,[sp,#8]
 ldr r0,[r5,#120]
 cmp r0,#0
 bne update_line
 ldr r0,[r5,#88]
 cmp r0,#0
 bne update_line
 ldr r0,[r5,#80]
 cmp r0,#0
 beq arrival_pending
 cmp r10,#6
 blo arrival_pending
 mov r0,r11
 cmp r0,#0
 rsblt r0,r0,#0
 cmp r0,#0x7000
 bgt arrival_pending
 cmp r1,#0x8000
 bgt arrival_pending
 cmn r1,#0x8000
 blt arrival_pending
 bl stop_reel
 mov r0,#1
 str r0,[r5,#120]
 ldr r0,[r6,#0x2fc]
 orr r0,r0,#2
 str r0,[r6,#0x2fc]       // native action re-entry starts the arrival rake
 ldr r0,[r5,#52]
 cmp r0,#0
 movne r0,#0
 strne r0,[r4,#0x18]
 b update_out
arrival_pending:
''')
    text = replace_once(text, ' ldr r0,[r5,#88]\n cmp r0,#0\n moveq r1,#17\n',
        ' ldr r0,[r5,#88]\n ldr r1,[r5,#120]\n orr r0,r0,r1\n cmp r0,#0\n moveq r1,#17\n')
    text = replace_once(text, ' cmp r10,#4\n', ' cmp r10,#2\n')
    text = replace_once(text, ''' mov r0,r11
 cmp r0,#0
 rsblt r0,r0,#0
 cmp r0,#0xd000
 blo update_line
''', '')
    text = replace_once(text, ' mov r1,#0x21\n', ' mov r1,#0x16\n')
    text = replace_once(text, ' cmp r0,#0x2000\n movgt r0,#0x2000\n',
                        ' cmp r0,#0x5000\n movgt r0,#0x5000\n')
    text = replace_once(text, ''' ldr r1,[r5,#88]
 cmp r1,#0
 moveq r1,#18
 movne r1,#5
 cmp r10,r1
 movge r0,#0''', ''' ldr r1,[r5,#88]
 ldr r2,[r5,#120]
 orr r1,r1,r2
 cmp r1,#0
 movne r0,#0''')
    text = replace_once(text, '''update_strike:
 ldr r0,[r5,#88]
 cmp r0,#0
 moveq r1,#18
 movne r1,#5''', '''update_strike:
 ldr r0,[r5,#88]
 ldr r1,[r5,#120]
 orr r0,r0,r1
 cmp r0,#0
 beq update_out
 mov r1,#3''')
    text = replace_once(text, ' cmp r0,#0xa000          // native yank settles the victim 6..10 units ahead',
                        ' cmp r0,#0x9000          // six-unit reel stop, bounded contact reach')
    text = replace_once(text, ' mov r0,r8\n mov r2,#0x1000\n', ' bl stop_reel\n mov r0,r8\n mov r2,#0x1000\n')
    text = replace_once(text, ' streq r0,[r5,#68]\n', ' streq r0,[r5,#68]\n add r0,r5,#96\n bl WEB_RELEASE\n')
    text = replace_once(text, 'cleanup:\n', 'cleanup:\n bl stop_reel\n add r0,r5,#112\n bl unlink_target\n')
    return text.replace(' .ltorg\n', Path(__file__).with_suffix('.s').read_text(encoding='utf-8')+'\n .ltorg\n')


def runtime(at, values):
    text = source()
    for name, value in values.items():
        text = text.replace(name, f'0x{value:08x}')
    code = asm(text, at)
    errors = literal_errors(code, text)+native_branch_errors(code, text, at)+self_branch_errors(code)
    if errors:
        raise ValueError('Web Yank correction assembly: '+str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom) != PARENT:
        raise ValueError('Web Yank correction requires exact published v0.34.0')
    meta = json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    rt = meta['hunter_kit']['runtime']
    header = w.parse_header(rom)
    arm = rom[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
    off = kit.SOURCE+rt['entry']-kit.TARGET
    frozen = parent.runtime(rt['entry'], rt['values'])
    if arm[off:off+len(frozen)] != frozen:
        raise ValueError('Published Web Yank runtime differs')
    code = runtime(rt['entry'], rt['values'])
    end = len(arm)-36
    if off+len(code) > end or any(arm[off+len(frozen):end]):
        raise ValueError('Web Yank correction exceeds its private code page')
    new = bytearray(arm)
    new[off:end] = code+bytes(end-off-len(code))
    result, _ = kit.replace_arm9(rom, bytes(new))
    names, blobs = parent.assets.resources(result)
    before = tuple(blobs)
    from tools.animation_rig import AnimationRig
    from tools.kit_choreography import author
    from tools.gmb import Gmb
    from tools.grip_compression import CompressedBlob, encode_backrefs
    parents = AnimationRig.parse(blobs[names.index('spd.nsbmd')]).parents
    idle = Gmb.parse(CompressedBlob.parse(blobs[names.index('spd_Idle.gmb')]).decoded)
    from tools.sca import Sca
    for sca_name, gmb_name, clip in ((parent.EXTRAS[0], parent.EXTRAS[1], art.YANK),
                                     (parent.EXTRAS[2], parent.EXTRAS[3], art.RAKE)):
        template = Sca.parse(blobs[names.index(sca_name)])
        # Retain the native rig/static pools while deliberately shortening this private clip.
        raw = bytearray(blobs[names.index(sca_name)][:template.frames_start+clip.samples*template.frame_stride])
        struct.pack_into('<I', raw, 4, clip.samples)
        blobs[names.index(sca_name)], _ = author(bytes(raw), blobs[names.index('spd_Idle.sca')], parents, clip)
        gmb = struct.pack('<4H', idle.unknown_u16_00, clip.samples, len(idle.channels), idle.unknown_u16_06)
        for c in idle.channels:
            gmb += struct.pack('<hH', c.kind, c.unknown_u16_02)+b''.join(c.records[:clip.samples])
        assert Gmb.parse(gmb).to_bytes() == gmb
        blobs[names.index(gmb_name)] = encode_backrefs(gmb)
    from tools.qol_suits_menu import StringSlots
    import mod
    _, glob, _ = mod.load_clean()
    offsets, native_names, _ = w.parse_glob(glob)
    for name in ('American.strings', 'English.strings'):
        i, n = names.index(name), native_names.index(name)
        raw = StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i], {
            50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}'})
        blobs[i] = raw+bytes((len(before[i])-len(raw)) % 4)
    changed = [name for name, a, b in zip(names, before, blobs) if a != b]
    if set(changed) != {'American.strings', 'English.strings', *parent.EXTRAS}:
        raise ValueError('Unexpected Web Yank correction resource scope')
    result = w.rebuild_rom(result, {'Glob.bin': w.pack_glob(names, blobs)}, legacy_gaps=True)
    w.validate_rom(result, target=True)
    report = dict(version=VERSION, parent_sha256=PARENT, rom_sha256=w.sha256(result), arm9_sha256=w.sha256(new),
        runtime=dict(entry=rt['entry'], bytes=len(code), source_offset=off, remaining_zero_tail=end-off-len(code)),
        modified_resources=changed, samples=art.YANK.samples, rake_samples=art.RAKE.samples, cast_sample=2,
        arrival='Native action re-entry into the short rake at actual gap <=7 units', contact_sample=3,
        reel_stop_q12=6*4096, max_reel_velocity_q12=6*4096,
        allocation_bytes=0, player_kit_32k_unchanged=True,
        scope='Existing private Web Yank code/cast and version text only; native collision/gravity, '
              'shop, ownership, other moves, bindings, rooms, audio and save format preserved.')
    from tools import release_info
    pin = release_info.PROFILE_INFO.get('tasm-v'+VERSION, {})
    for key in ('rom_sha256', 'arm9_sha256'):
        if pin.get(key) and pin[key] != report[key]:
            raise ValueError('Web Yank correction differs from immutable release pin')
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
    meta.update(web_yank_fix=report, release_version=VERSION, release_date=DATE, output_rom_sha256=w.sha256(result),
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
