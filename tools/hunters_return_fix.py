"""Exact v0.32 post-pass: per-victim launch and replaced-player cleanup."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import hunters_return as parent,wos_tool as w,tasm_kit as kit
from tools.assemble_tasm_kit import literal_errors,native_branch_errors,self_branch_errors

PARENT='4ab044d0e258e84d195774d4e3ee95a5d22ddc778600986d235490847f00e556'
PARENT_PATH=ROOT/'build/version-0.32.0-final/Versioned.nds'
VERSION='0.32.1'
DATE='2026-10-23'


def old_symbols(at,values):
    sys.path.insert(0,str(ROOT/'work/research-libs'))
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
    source=Path(parent.__file__).with_suffix('.s').read_text(encoding='utf-8')
    for key,value in values.items():source=source.replace(key,f'0x{value:08x}')
    code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(source+'\n.ltorg\n.word rake_contact,update_entry',at)[0])
    if code[:-8]!=parent.runtime(at,values):raise ValueError('Frozen Hunter symbol export differs')
    return dict(zip(('OLD_RAKE','OLD_UPDATE'),struct.unpack('<2I',code[-8:])))


def runtime(at,values):
    sys.path.insert(0,str(ROOT/'work/research-libs'))
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
    source=Path(__file__).with_suffix('.s').read_text(encoding='utf-8')
    for key,value in values.items():source=source.replace(key,f'0x{value:08x}')
    code=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(source,at)[0])
    errors=literal_errors(code,source)+native_branch_errors(code,source,at)+self_branch_errors(code)
    if errors:raise ValueError('Hunter correction assembly: '+str(errors))
    return code


def apply_rom(rom):
    if w.sha256(rom)!=PARENT:raise ValueError('Hunter correction requires exact published v0.32.0')
    meta=json.loads(PARENT_PATH.with_suffix('.build.json').read_text(encoding='utf-8'))
    old=meta['hunters_return']['runtime'];header=w.parse_header(rom)
    arm=rom[header['arm9_offset']:header['arm9_offset']+header['arm9_size']]
    offset=lambda at:kit.SOURCE+at-kit.TARGET if at>=kit.TARGET else at-0x02000000
    frozen=parent.runtime(old['entry'],old['values'])
    if arm[offset(old['entry']):offset(old['entry'])+len(frozen)]!=frozen:
        raise ValueError('Published Hunter runtime differs')
    at=old['entry']+len(frozen)
    values=dict(old_symbols(old['entry'],old['values']),STATE=old['state'],OLD_CONTACT=old['values']['OLD_CONTACT'])
    code=runtime(at,values);start=offset(at);end=len(arm)-36
    if start+len(code)>end or any(arm[start:end]):raise ValueError('Hunter correction tail is occupied')
    new=bytearray(arm);new[start:start+len(code)]=code
    hooks=((0x02078628,kit.branch(0x02078628,old['entry']+8),at),
           (0x0207866c,0xe59d0004,at+4),
           (old['entry']+12,kit.branch(old['entry']+12,values['OLD_UPDATE']),at+8))
    for site,expected,target in hooks:
        if w.u32(new,offset(site))!=expected:raise ValueError(f'Hunter correction hook differs at {site:#x}')
        struct.pack_into('<I',new,offset(site),kit.branch(site,target))
    result,_=kit.replace_arm9(rom,bytes(new))
    names,blobs=parent.assets.resources(result);before=tuple(blobs)
    from tools.qol_suits_menu import StringSlots
    import mod
    _,glob,_=mod.load_clean();offsets,native_names,_=w.parse_glob(glob)
    for name in ('American.strings','English.strings'):
        i=names.index(name);n=native_names.index(name)
        raw=StringSlots(glob[offsets[n]:offsets[n+1]]).grown(blobs[i],{
            50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i]=raw+bytes((len(before[i])-len(raw))%4)
    changed=[name for name,a,b in zip(names,before,blobs) if a!=b]
    if changed!=['American.strings','English.strings']:raise ValueError('Unexpected correction resource scope')
    result=w.rebuild_rom(result,{'Glob.bin':w.pack_glob(names,blobs)},legacy_gaps=True)
    w.validate_rom(result,target=True)
    report=dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(new),
        modified_resources=changed,runtime=dict(entry=at,bytes=len(code),values=values,hooks=[dict(site=s,old=e,target=t) for s,e,t in hooks],
        allocation_bytes=0,remaining_zero_tail=end-start-len(code)),
        per_victim_restore='Save in unused native argument copies; restore after native credit, before the victim loop advances.',
        player_cleanup='A current native player replacing the cached owner clears the old move without dereferencing it.',
        assets_purchases_save_format_and_other_runtime_preserved=True)
    from tools import release_info
    pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
    for key in ('rom_sha256','arm9_sha256'):
        if pin.get(key) and pin[key]!=report[key]:raise ValueError('Hunter correction differs from immutable release pin')
    return result,report


def generate(output,source=PARENT_PATH):
    source,output=Path(source),Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    result,report=apply_rom(source.read_bytes());path=output/'Versioned.nds';v=w.validate_rom(result,target=True)
    meta=json.loads(source.with_suffix('.build.json').read_text(encoding='utf-8'))
    ge=next(e for e in v['nitrofs'] if e['name']=='Glob.bin')
    meta.update(hunters_return_fix=report,release_version=VERSION,release_date=DATE,output_rom_sha256=w.sha256(result),
        output=str(path.resolve()),rom_size=len(result),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],
        header_crc16=v['header']['header_crc16'],output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    w.atomic_write(path,result,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text(encoding='utf-8'))
    recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe);w.write_json(output/'changes.json',report)
    print(json.dumps(dict(path=str(path),sha256=report['rom_sha256'],runtime=report['runtime'])),flush=True)
    return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--source',type=Path,default=PARENT_PATH);a=p.parse_args();generate(a.out,a.source)
