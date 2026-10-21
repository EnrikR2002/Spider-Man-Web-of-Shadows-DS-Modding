"""Exact0.26 post-pass: combo openings, creature anatomy/motion and encounter ramp."""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import midnight_voltage as prior,wos_tool as w,tasm_kit as kit,crane_row as crane,creature_forge as forge
from tools import midnight_finale_motion as motion,midnight_finale_art as art,midnight_finale_combat as combat
from tools import midnight_voltage_combat as voltage,creature_texture_fix
from tools.sca import Sca
from tools.animation_rig import AnimationRig

VERSION='0.27.0';DATE='2026-10-19';PARENT='21bd1b19c8b8f74f24fca06e238204dac0f78b02630e04629fd8ae78f978a947'
offset=forge.offset
# Native cost budgets (Warden costs2): teach pursuit, then mix ranged pressure
# with a heavy, then a larger late wave. Sanctuaries/return corridor stay calm.
RAMP={78:((21,20,21,36),(8,3)),81:((36,21,20,21),(8,3)),
      83:((21,20,36,21),(7,3)),86:((36,20,21,36,21,20),(12,4))}


class Runtime(prior.Runtime):
    def __init__(self,rom):
        if w.sha256(rom)!=PARENT:raise ValueError('Finale requires exact published0.26')
        self.rom=rom;self.header=w.parse_header(rom);h=self.header
        self.arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];self.new=bytearray(self.arm)
        self.end=len(self.arm)-36;self.start=kit.TARGET+self.end-kit.SOURCE;self.data=bytearray()


def authored(native,names,style,stem,published):
    deps=('midnight_finale_motion.py','midnight_encore_motion.py','midnight_enemy_motion.py','creature_forge_motion.py')
    key=w.sha256(b''.join((ROOT/'tools'/n).read_bytes() for n in deps))
    path=ROOT/'work/midnight-flow/motion-cache'/(style+'-'+key+'.zip')
    if path.exists():
        with zipfile.ZipFile(path) as z:
            info=json.loads(z.read('manifest.json'));extras={n:z.read(n) for n in z.namelist() if n!='manifest.json'}
        if info['hashes']!={n:w.sha256(v) for n,v in extras.items()}:raise ValueError('Finale cache integrity')
        return extras,info['clips']
    print('AUTHOR '+style,flush=True);extras,clips=motion.prepare(native,names,style,stem,published)
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,v in extras.items():z.writestr(n,v)
        z.writestr('manifest.json',json.dumps(dict(clips=clips,hashes={n:w.sha256(v) for n,v in extras.items()})))
    return extras,clips


def apply_rom(rom,*,pilot=False):
    rt=Runtime(rom);meta=json.loads((ROOT/'build/version-0.26.0-final/Versioned.build.json').read_text())
    e=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');g=rom[e['start']:e['end']];o,names,_=w.parse_glob(g)
    blobs=[g[a:b] for a,b in zip(o,o[1:])];before=tuple(blobs)
    import mod
    _,ng,_=mod.load_clean();no,nn,_=w.parse_glob(ng)
    def native(n):i=nn.index(n);return ng[no[i]:no[i+1]]
    def published(n):return before[names.index(n)]
    changed=[];creatures={};f=meta['creature_forge']['runtime']
    for index,(style,stem,group,cfg) in enumerate(forge.parent.PRIVATE_STYLES):
        if style not in motion.STYLES or pilot and style!='conductor':continue
        extras,clips=authored(native,nn,style,stem,published)
        for n,payload in extras.items():
            if n not in names:raise ValueError('Unexpected new binding '+n)
            i=names.index(n);blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(n)
        neutral=motion.pose(Sca.parse(native(stem+'_Idle.sca')),AnimationRig.parse(native(stem+'.nsbmd')).parents,style,stem)
        model,model_report=art.model(style,stem,native(stem+'.nsbmd'),neutral);model,_=creature_texture_fix.fix_model(model)
        n='zz_F22_'+style+'.nsbmd';i=names.index(n);blobs[i]=model+bytes((len(blobs[i])-len(model))%4);changed.append(n)
        rows=[]
        for j,move in enumerate(motion.MOVES[style]):
            drive=rt.alloc(b''.join(struct.pack('<3i',a,b,round(v*4096)) for a,b,v in move.drives)+struct.pack('<3i',0x7fffffff,0,0))
            jump=rt.alloc(b''.join(struct.pack('<2i',a,round(v*4096)) for a,v in move.jumps)+struct.pack('<2i',0x7fffffff,0))
            impact=18+j if style=='conductor' else 9+(index-3)*3+j
            events=([(0,708)] if style=='conductor' and j>=4 else [])+[(a,653+35+min(impact,21)) for a,b in move.contacts]
            cue=rt.alloc(b''.join(struct.pack('<2i',a,sound) for a,sound in events)+struct.pack('<2i',0x7fffffff,0))
            rows.append(struct.pack('<8I',move.action,move.samples-1,move.cooldown,drive,jump,cue,index*4+j%4,round(move.reach*4096)))
        table=rt.alloc(b''.join(rows));struct.pack_into('<2I',rt.new,offset(f['records'])+index*16+4,table,len(rows))
        if style=='conductor':boss_table=table
        creatures[style]=dict(clips=clips,model=model_report,programs=[vars(m) for m in motion.MOVES[style]])
    state=rt.alloc(bytes(48));cfg=meta['creature_forge']['creatures']['conductor']['config']
    old=crane.target(0x02049304,w.u32(rt.arm,0x49304));hp=rt.alloc();rt.data.extend(voltage.damage(hp,old,state,cfg,hit_threshold=4,window=100));rt.hook(0x02049304,hp)
    capture=forge.parent.combat.capture_hero(f['capture'],f['hero']);play=f['capture']+len(capture)
    think=rt.alloc();rt.data.extend(forge.combat.think(think,f['records'],f['slots'],f['attack_counters'],f['hero'],f['hero']-4,f['move_counters'],play,653,
        rewrite=lambda source:combat.decisions(source,meta['chapter_spectacle']['runtime']['navigation'],meta['midnight_encore']['runtime']['poise'],state,boss_table,f['hero'])))
    struct.pack_into('<I',rt.new,forge.combat.THINK_SLOT-0x02000000,think)
    second=rt.alloc();rt.data.extend(combat.secondary(second,meta['chapter_spectacle']['runtime']['secondary'],f['slots'],cfg));struct.pack_into('<I',rt.new,forge.combat.SECOND_SLOT-0x02000000,second)
    update=rt.alloc();rt.data.extend(voltage.update(update,f['update'],f['slots'],cfg,f['hero'],state,gap=21,rake_first=14,rake_second=24,wheel_gap=21))
    struct.pack_into('<I',rt.new,forge.combat.UPDATE_SLOT-0x02000000,update)
    ramp={}
    if not pilot:
        scripted=meta['chapter_spectacle']['scripted_runtime'];roster=scripted['roster_table'];goals=scripted['goal_table']
        for room,(pattern,budget) in RAMP.items():
            ptr=rt.alloc(bytes(pattern));found=False
            for row in range(40):
                off=offset(roster)+row*12;rid=w.u32(rt.arm,off)
                if not rid:break
                if rid==room:struct.pack_into('<2I',rt.new,off+4,ptr,len(pattern));found=True;break
            if not found:raise ValueError('Missing roster room')
            for row in range(40):
                off=offset(goals)+row*20;rid=w.u32(rt.arm,off)
                if not rid:raise ValueError('Missing goal room')
                if rid==room:
                    old_goal=w.u32(rt.arm,off+4);raw=bytearray(rt.arm[offset(old_goal):offset(old_goal)+24])
                    struct.pack_into('<2I',raw,0,budget[0]*4096,budget[1]*4096);ptr=rt.alloc(raw)
                    struct.pack_into('<I',rt.new,off+4,ptr);break
            ramp[str(room)]=dict(pattern=pattern,total_cost=budget[0],live_cost=budget[1])
    from tools.qol_suits_menu import StringSlots
    for n in forge.chapter.STRING_FILES:
        i=names.index(n);payload=StringSlots(native(n)).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(n)
    result=rt.finish({'Glob.bin':w.pack_glob(names,blobs)})
    assert all(a==b for n,a,b in zip(names,before,blobs) if n not in changed)
    h=w.parse_header(result)
    report=dict(version=VERSION,parent_sha256=PARENT,pilot=pilot,creatures=creatures,ramp=ramp,modified_resources=sorted(set(changed)),
        runtime=dict(state=state,table=boss_table,damage=hp,think=think,secondary=second,update=update,start=rt.start,used=len(rt.data)),
        boss_rules=dict(pressure_hits=4,pressure_window=100,counter_cooldown=72,ordinary_attacks_stagger=True,standing_hurt_state=37,armoured_action=74),
        player_kit_preserved=True,room_resources_unchanged=True,sound_data_preserved=True,rom_sha256=w.sha256(result),
        arm9_sha256=w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]))
    if not pilot:
        from tools import release_info
        pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
        for key in ('rom_sha256','arm9_sha256'):
            if pin.get(key) and pin[key]!=report[key]:raise ValueError('Finale differs from immutable release pin')
    return result,report


def generate(output,source=None,**options):
    output=Path(output);source=Path(source) if source else ROOT/'build/version-0.26.0-final/Versioned.nds'
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidate must stay in build/')
    raw,report=apply_rom(source.read_bytes(),**options);path=output/'Versioned.nds';meta=json.loads(source.with_suffix('.build.json').read_text())
    meta['midnight_finale']=report;meta.update(release_version=VERSION,release_date=DATE,output_rom_sha256=w.sha256(raw),output=str(path.resolve()))
    v=w.validate_rom(raw,target=True);meta.update(rom_size=len(raw),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'])
    glob_entry=next(e for e in v['nitrofs'] if e['name']=='Glob.bin')
    meta['output_glob_sha256']=w.sha256(raw[glob_entry['start']:glob_entry['end']])
    w.atomic_write(path,raw,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION);w.write_json(output/'gameplay_profile.json',recipe)
    print(json.dumps(dict(candidate=str(path),sha256=report['rom_sha256'],runtime=report['runtime'])));return path


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--source',type=Path);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    generate(a.out,a.source,pilot=a.pilot)
