"""Exact v0.30.3 post-pass: conditional Vortex, Conductor armor and raw HP damage."""
from pathlib import Path
import argparse
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import wos_tool as w,tasm_kit as kit,spider2099 as assets
from tools import midnight_voltage as extension,vortex_forge_art as art
from tools.assemble_tasm_kit import literal_errors,native_branch_errors,self_branch_errors

PARENT='4a282d637be8bb277dbf8a36c86a6dc9ff69820ca377d6cb1b8abc406816472c'
VERSION='0.31.0';DATE='2026-10-22'
PARENT_PATH=ROOT/'build/version-0.30.3-final/Versioned.nds'
SYMBOLS=('web_try','web_node','web_update','web_hit','web_line','k2_owned','k2_damage','h_yank')


def kit_symbols():
    """Resolve original symbols without changing/reassembling the shipped kit."""
    sys.path.insert(0,str(ROOT/'work/research-libs'))
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
    src=(ROOT/'tools/tasm_kit2.s').read_text()
    ks=Ks(KS_ARCH_ARM,KS_MODE_ARM)
    raw=bytes(ks.asm(src,kit.KIT2_BASE)[0])
    if raw!=kit.code_bytes(2):raise ValueError('Original second kit source differs from its frozen code')
    raw=bytes(ks.asm(src+'\n.word '+','.join(SYMBOLS),kit.KIT2_BASE)[0])
    return dict(zip(SYMBOLS,struct.unpack_from('<'+str(len(SYMBOLS))+'I',raw,len(raw)-4*len(SYMBOLS))))


def runtime(at,state,boss,symbols):
    sys.path.insert(0,str(ROOT/'work/research-libs'))
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
    src=Path(__file__).with_suffix('.s').read_text()
    for key,value in dict(STATE=state,BOSS_CONFIG=boss,WEB_LINE=symbols['web_line'],
                          WEB_HIT=symbols['web_hit'],K2_OWNED=symbols['k2_owned'],OLD_YANK=symbols['h_yank']).items():
        src=src.replace(key,f'0x{value:08x}')
    raw=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(src,at)[0])
    errors=literal_errors(raw,src)+native_branch_errors(raw,src,at)+self_branch_errors(raw)
    if errors:raise ValueError('Vortex adapter assembly: '+str(errors))
    return raw


class Runtime(extension.Runtime):
    def __init__(self,rom):
        if w.sha256(rom)!=PARENT:raise ValueError('Vortex Forge requires exact published v0.30.3')
        self.rom=rom;self.header=w.parse_header(rom);h=self.header
        self.arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];self.new=bytearray(self.arm)
        self.end=len(self.arm)-36;self.start=kit.TARGET+self.end-kit.SOURCE;self.data=bytearray()


def scale_motion(raw):
    from tools.sca import Sca
    from tools.sca_author import repack_samples,sample
    a=Sca.parse(raw)
    translations={j:tuple(tuple(round(v*art.SCALE) for v in sample(a,j,f,'translation'))
                              for f in range(a.frame_count)) for j in range(a.joint_count)}
    return repack_samples(raw,translations=translations)


def apply_rom(rom):
    rt=Runtime(rom);symbols=kit_symbols()
    meta=json.loads(PARENT_PATH.with_suffix('.build.json').read_text())
    boss=meta['creature_forge']['creatures']['conductor']['config']
    state=rt.alloc(bytes(256));entry=rt.alloc();code=runtime(entry,state,boss,symbols);rt.data.extend(code)
    names,blobs=assets.resources(rom);before=tuple(blobs)
    import mod
    _,glob,_=mod.load_clean();o,nn,_=w.parse_glob(glob)
    def native(n):i=nn.index(n);return glob[o[i]:o[i+1]]
    from tools import midnight_finale_motion as motion
    from tools.sca import Sca
    from tools.animation_rig import AnimationRig
    pose=motion.pose(Sca.parse(native('brt_Idle.sca')),AnimationRig.parse(native('brt.nsbmd')).parents,'conductor','brt')
    model,mesh=art.model(native('brt.nsbmd'),pose);model,texture=art.direct_texture(model)
    blobs[names.index('zz_F22_conductor.nsbmd')]=model
    motions=[]
    for i,n in enumerate(names):
        if n.startswith('zz_F22_conductor_') and n.endswith('.sca'):
            blobs[i]=scale_motion(blobs[i]);motions.append(n)
    if not motions:raise ValueError('Missing private Conductor lifecycle/motion resources')
    from tools.kit_choreography import author
    slam,frames=author(native('spd_GroundAttack14.sca'),native('spd_Idle.sca'),
                      AnimationRig.parse(native('spd.nsbmd')).parents,art.VORTEX)
    blobs[names.index('zz_kit_WebSlam.sca')]=slam
    from tools.qol_suits_menu import StringSlots
    # Shop indices are derived from the established rows, preserving purchase IDs.
    vortex_text=kit.STRING_COUNT+kit.SHOP_TEXTS.index(kit.SHOP_ROWS[-1][-1])
    for name in ('American.strings','English.strings'):
        i=names.index(name);blobs[i]=StringSlots(native(name)).grown(blobs[i],{
            50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}',
            vortex_text:'Web an enemy with \ue602 or Dragnet.\nDown + \ue601: tether catapult + slam.\n\ue604 cancels. Needs a webbed enemy.'})
    for i,raw in enumerate(blobs):
        if raw!=before[i]:blobs[i]=raw+bytes((len(before[i])-len(raw))%4)
    from tools import oscorp_resources
    from tools.actor_resources import ModelSheet
    extra={}
    if sum(map(len,blobs))%4:extra['zz_V31_align.bin']=bytes(-sum(map(len,blobs))%4)
    extra['zz_V31_Conductor.nsbtx']=texture
    names,blobs=oscorp_resources.append_resources(names,blobs,extra)
    sheet_id=names.index('model_sheet.xbd');sheet=ModelSheet.parse(blobs[sheet_id]);group=meta['creature_forge']['creatures']['conductor']['group']
    if sheet.groups[group][2]!=names.index('zz_F22_Atlas.nsbtx'):raise ValueError('Conductor texture group differs')
    edited=bytearray(blobs[sheet_id]);struct.pack_into('<H',edited,sheet.start+group*6+4,names.index('zz_V31_Conductor.nsbtx'))
    blobs[sheet_id]=bytes(edited);ModelSheet.parse(blobs[sheet_id])
    if w.u32(rt.new,oscorp_resources.COUNT_OFFSET)!=len(before):raise ValueError('Resource count changed')
    struct.pack_into('<I',rt.new,oscorp_resources.COUNT_OFFSET,len(names))
    changed=[n for n,a,b in zip(names,before,blobs) if a!=b]
    allowed={'zz_F22_conductor.nsbmd','zz_kit_WebSlam.sca','American.strings','English.strings','GlobFiles.txt','model_sheet.xbd',*motions}
    if set(changed)!=allowed:raise ValueError('Unexpected resource scope '+str(set(changed)^allowed))
    result=rt.finish({'Glob.bin':w.pack_glob(names,blobs)})
    h=w.parse_header(result);start=h['arm9_offset'];arm=bytearray(result[start:start+h['arm9_size']])
    patches={symbols['web_try']:entry,symbols['web_node']:entry+4,symbols['web_update']:entry+8,0x02151920:entry+12}
    offset=lambda a:kit.SOURCE+a-kit.TARGET
    patch_log=[]
    for at,target in patches.items():
        off=offset(at);old=w.u32(arm,off);struct.pack_into('<I',arm,off,kit.branch(at,target))
        if at==0x02151920 and old!=0xe92d500c:raise ValueError('Cheap HUD filter prologue changed')
        patch_log.append(dict(address=at,old=old,target=target))
    off=0xb6030
    if w.u32(arm,off)!=kit.branch(0x020b6030,kit.KIT2_BASE+0x1c):raise ValueError('Native web-hold hook changed')
    struct.pack_into('<I',arm,off,kit.branch(0x020b6030,entry+16))
    patch_log.append(dict(address=0x020b6030,target=entry+16))
    # Native r0 is old HP - full incoming damage, BEFORE the clamp into r3.
    off=offset(symbols['k2_damage'])+4
    if w.u32(arm,off)!=0xe0514003:raise ValueError('Unexpected native Vitality damage reconstruction')
    struct.pack_into('<I',arm,off,0xe0514000)
    patch_log.append(dict(address=symbols['k2_damage']+4,old=0xe0514003,new=0xe0514000))
    result,_=kit.replace_arm9(result,bytes(arm));w.validate_rom(result,target=True)
    log=dict(version=VERSION,parent_sha256=PARENT,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(arm),
        modified_resources=changed,added_resources=list(extra),conductor_texture=dict(format=7,pixel_bytes=8192,dimensions=[64,64],shared_creature_atlas_unchanged=True),conductor_model=mesh,conductor_motion_scale=art.SCALE,
        conductor_motion_count=len(motions),runtime=dict(start=rt.start,state=state,entry=entry,bytes=len(code),symbols=symbols),
        patches=patch_log,player_kit_reserve=kit.RESERVE,native_boss_attacks_and_collision_preserved=True,
        rooms_audio_purchases_save_format_preserved=True,
        health_fix='Scale old HP minus raw native remaining r0, then clamp once.',
        vortex='Owned Red Down+Y captures up to four actual native webbed targets; continuous velocity-driven catapult and slam; R interrupts.')
    from tools import release_info
    pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
    for key in ('rom_sha256','arm9_sha256'):
        if pin.get(key) and pin[key]!=log[key]:raise ValueError('Vortex Forge differs from immutable release pin')
    return result,log


def generate(output,source=PARENT_PATH):
    source,output=Path(source),Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidates belong in build/')
    result,log=apply_rom(source.read_bytes());path=output/'Versioned.nds';v=w.validate_rom(result,target=True)
    meta=json.loads(source.with_suffix('.build.json').read_text());ge=next(e for e in v['nitrofs'] if e['name']=='Glob.bin')
    meta.update(vortex_forge=log,release_version=VERSION,release_date=DATE,output_rom_sha256=w.sha256(result),
                output=str(path.resolve()),rom_size=len(result),used_rom_size=v['header']['used_rom_size'],
                nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'],output_glob_sha256=w.sha256(result[ge['start']:ge['end']]))
    meta['verified_resource_count']=len(assets.resources(result)[0])
    w.atomic_write(path,result,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION)
    w.write_json(output/'gameplay_profile.json',recipe);w.write_json(output/'changes.json',log)
    print(json.dumps(dict(path=str(path),sha256=log['rom_sha256'],boss_motion_count=log['conductor_motion_count'],mesh=log['conductor_model'])),flush=True)
    return path


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--source',type=Path,default=PARENT_PATH)
    a=p.parse_args();generate(a.out,a.source)
