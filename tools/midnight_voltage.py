"""Exact0.25 post-pass for audible creatures and an evasive Conductor."""
import argparse,json,struct,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import wos_tool as w,tasm_kit as kit,crane_row as crane,creature_forge as forge
from tools.chapter_renewal_combat import asm
PARENT='0817ec91a44f85a31135f4d99ef90452dd8c30870689e803743b3594ddadb314'
VERSION='0.26.0';DATE='2026-10-19'
offset=forge.offset


class Runtime:
    def __init__(self,rom):
        if w.sha256(rom)!=PARENT:raise ValueError('Voltage requires exact published0.25')
        self.rom=rom;self.header=w.parse_header(rom);h=self.header
        self.arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];self.new=bytearray(self.arm)
        self.end=len(self.arm)-36;self.start=kit.TARGET+self.end-kit.SOURCE;self.data=bytearray()
    def alloc(self,raw=b''):
        self.data.extend(bytes(-len(self.data)%4));at=self.start+len(self.data);self.data.extend(raw);return at
    def hook(self,site,target,link=False):struct.pack_into('<I',self.new,site-0x02000000,crane.branch(site,target,link=link))
    def finish(self,replacements=None):
        space=(len(self.data)+0xfff)//0x1000*0x1000;arm=self.arm;new=self.new;end=self.end
        if w.u32(arm,kit.TABLE_POINTERS)!=0x02000000+end or struct.unpack_from('<3I',arm,end+24)!=(kit.TARGET,end-kit.SOURCE,0):raise ValueError('Autoload contract')
        new=new[:end]+bytes(space)+new[end:end+24]+struct.pack('<3I',kit.TARGET,end-kit.SOURCE+space,0)
        struct.pack_into('<2I',new,kit.TABLE_POINTERS,0x02000000+end+space,0x02000000+end+space+36)
        struct.pack_into('<I',new,kit.ARENA_LOWER,self.start+space);new[offset(self.start):offset(self.start)+len(self.data)]=self.data
        if new[kit.SOURCE:kit.SOURCE+kit.RESERVE]!=arm[kit.SOURCE:kit.SOURCE+kit.RESERVE]:raise ValueError('Player kit changed')
        result=w.rebuild_rom(self.rom,replacements) if replacements else self.rom
        result,_=kit.replace_arm9(result,bytes(new));w.validate_rom(result,target=True);return result


def sound_pulse(at,table,play,old,sound):
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        ldr r1,[r0]
        ldr r2,controller
        cmp r1,r2
        bne done
        ldr r1,stats
        ldr r1,[r1]
        cmp r1,#0
        beq done
        ldr r1,[r1]
        cmp r1,#65
        bne done
        ldr r4,table
        ldr r1,[r4]
        add r1,r1,#1
        str r1,[r4]
        ldr r2,[r4,#4]
        add r2,r2,#1
        cmp r2,#120
        strlo r2,[r4,#4]
        blo done
        mov r2,#0
        str r2,[r4,#4]
        ldr r0,sound
        cmp r0,#0
        blne #0x{play:x}
    done:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        b #0x{old:x}
    controller: .word 0x021352a4
    stats: .word 0x02145c5c
    table: .word 0x{table:x}
    sound: .word {sound}
    ''',at)


def sound_result(at,table,trampoline):
    return asm(f'''
        push {{r4-r8,lr}}
        mov r5,r1
        bl #0x{trampoline:x}
        ldr r4,table
        ldr r6,[r4]
        add r7,r6,#1
        str r7,[r4]
        and r6,r6,#127
        add r4,r4,#4
        add r4,r4,r6,lsl #4
        ldr r7,[r5]
        str r7,[r4]
        ldr r7,[r5,#4]
        str r7,[r4,#4]
        ldr r7,[r5,#8]
        str r7,[r4,#8]
        str r0,[r4,#12]
        pop {{r4-r8,pc}}
    table: .word 0x{table:x}
    ''',at)


def diagnostic(source,output,sound=776,linear=False,gain=1,fixed=False):
    source=Path(source);output=Path(output);rt=Runtime(source.read_bytes());meta=json.loads(source.with_suffix('.build.json').read_text())
    f=meta['creature_forge']['runtime'];capture=forge.parent.combat.capture_hero(f['capture'],f['hero']);play=f['capture']+len(capture)
    counter=rt.alloc(bytes(8));log=rt.alloc(bytes(4+128*16));trampoline=rt.alloc(asm('push {r3,r4,r5,lr}\nb #0x0203dd58',rt.start+len(rt.data)))
    result_at=rt.alloc();rt.data.extend(sound_result(result_at,log,trampoline));rt.hook(0x0203dd54,result_at)
    old=crane.target(0x020776bc,w.u32(rt.arm,0x776bc));pulse=rt.alloc();rt.data.extend(sound_pulse(pulse,counter,play,old,sound));rt.hook(0x020776bc,pulse)
    replacements=None
    if linear or fixed:
        from tools.midnight_voltage_audio import linear_bank,sound_data
        e=next(e for e in w.nitrofs_entries(rt.rom) if e['name']=='sound_data.sdat')
        replacements={'sound_data.sdat':sound_data(rt.rom[e['start']:e['end']]) if fixed else linear_bank(rt.rom[e['start']:e['end']],gain)}
    raw=rt.finish(replacements);path=output/'Probe.nds';w.atomic_write(path,raw,sources=(source,))
    meta['voltage_sound_probe']=dict(sound=sound,counter=counter,log=log,linear=linear,gain=gain,fixed=fixed);meta['output_rom_sha256']=w.sha256(raw)
    w.write_json(path.with_suffix('.build.json'),meta);print(json.dumps(dict(path=str(path),sha256=w.sha256(raw),probe=meta['voltage_sound_probe'])));return path


def apply_rom(rom,*,audio=True,boss=True,muted=False):
    rt=Runtime(rom);meta=json.loads((ROOT/'build/version-0.25.0-final/Versioned.build.json').read_text());report=dict(version=VERSION,parent_sha256=PARENT)
    e=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');glob=rom[e['start']:e['end']];offsets,names,_=w.parse_glob(glob)
    blobs=[glob[a:b] for a,b in zip(offsets,offsets[1:])];before=tuple(blobs);changed=[];replacements={}
    if boss:
        import mod
        from tools import midnight_voltage_motion as motion,midnight_voltage_combat as combat
        from tools import midnight_voltage_art as art,creature_forge_art,creature_texture_fix
        from tools.sca import Sca
        from tools.animation_rig import AnimationRig
        from tools.actor_actions import ActorActions
        _,native_glob,_=mod.load_clean();no,nn,_=w.parse_glob(native_glob)
        def native(name):i=nn.index(name);return native_glob[no[i]:no[i+1]]
        key=w.sha256(b''.join((ROOT/'tools'/n).read_bytes() for n in ('midnight_voltage_motion.py','midnight_encore_motion.py','creature_forge_motion.py')))
        cache=ROOT/'work/midnight-voltage/motion-cache'/(key+'.zip')
        if cache.exists():
            with zipfile.ZipFile(cache) as z:
                info=json.loads(z.read('manifest.json'));extras={n:z.read(n) for n in z.namelist() if n!='manifest.json'};clips=info['clips']
            if info['hashes']!={n:w.sha256(v) for n,v in extras.items()}:raise ValueError('Voltage cache integrity')
        else:
            print('AUTHOR electronic symbiote',flush=True);extras,clips=motion.prepare(native,nn);cache.parent.mkdir(exist_ok=True,parents=True)
            with zipfile.ZipFile(cache,'w',zipfile.ZIP_DEFLATED) as z:
                for n,v in extras.items():z.writestr(n,v)
                z.writestr('manifest.json',json.dumps(dict(clips=clips,hashes={n:w.sha256(v) for n,v in extras.items()})))
        # Keep the complete published lifecycle, including the get-up attack's
        # synchronized native GMB/GAB. This pass owns locomotion and programs.
        lifecycle={clip['resource'][:-4]+ext for clip in clips if clip['move'] is None and clip['mode'] not in ('idle','walk','run') for ext in ('.sca','.gmb','.gab')}
        extras={name:value for name,value in extras.items() if name not in lifecycle}
        added={n:v for n,v in extras.items() if n not in names}
        if added:
            from tools import oscorp_resources
            if any(not n.startswith('zz_F22_conductor_') or not n.endswith('.gab') for n in added):raise ValueError('Unexpected new actor resource')
            names,blobs=oscorp_resources.append_resources(names,blobs,added);changed.append('GlobFiles.txt')
            struct.pack_into('<I',rt.new,forge.chapter.GLOB_COUNT,len(names))
        for name,payload in extras.items():
            i=names.index(name);blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(name)
        neutral=motion.pose(Sca.parse(native('brt_Idle.sca')),AnimationRig.parse(native('brt.nsbmd')).parents)
        neutral.rebuild_style='conductor';model,art_report=creature_forge_art.model('conductor','brt',native('brt.nsbmd'),neutral,sculpt_type=art.Electrical)
        model,_=creature_texture_fix.fix_model(model);i=names.index('zz_F22_conductor.nsbmd');blobs[i]=model+bytes((len(blobs[i])-len(model))%4);changed.append(names[i])
        i=names.index('zz_F22_conductor.xbd');actions=ActorActions.parse(blobs[i],names);action=actions.lookup(74);xbd=bytearray(blobs[i])
        if action.flags!=16:raise ValueError('Counter carrier flags changed')
        xbd[action.offset+4]=24
        sca_name=next(b['name'] for b in action.bindings if b['tag']==0)
        for binding in action.bindings:
            if binding['tag']==4 and sca_name[:-4]+'.gab' in added:struct.pack_into('<h',xbd,binding['offset'],names.index(sca_name[:-4]+'.gab'))
        blobs[i]=bytes(xbd);ActorActions.parse(blobs[i],names);changed.append(names[i])
        f=meta['creature_forge']['runtime'];config=meta['creature_forge']['creatures']['conductor']['config']
        rows=[]
        for j,move in enumerate(motion.MOVES):
            drive=rt.alloc(b''.join(struct.pack('<3i',a,b,round(v*4096)) for a,b,v in move.drives)+struct.pack('<3i',0x7fffffff,0,0))
            jump=rt.alloc(b''.join(struct.pack('<2i',a,round(v*4096)) for a,v in move.jumps)+struct.pack('<2i',0x7fffffff,0))
            cue_id=653+35+18+min(j,3)
            events=([(0,708)] if j>=4 else [])+[(a,cue_id) for a,b in move.contacts]
            cue=rt.alloc(b''.join(struct.pack('<2i',a,sound) for a,sound in events)+struct.pack('<2i',0x7fffffff,0))
            rows.append(struct.pack('<8I',move.action,move.samples-1,move.cooldown,drive,jump,cue,24+(j%4),round(move.reach*4096)))
        table=rt.alloc(b''.join(rows));record=offset(f['records'])+6*16;struct.pack_into('<2I',rt.new,record+4,table,len(rows))
        state=rt.alloc(bytes(48));old_hp=crane.target(0x02049304,w.u32(rt.arm,0x49304));hp=rt.alloc();rt.data.extend(combat.damage(hp,old_hp,state,config));rt.hook(0x02049304,hp)
        capture=forge.parent.combat.capture_hero(f['capture'],f['hero']);play=f['capture']+len(capture)
        think=rt.alloc();rt.data.extend(forge.combat.think(think,f['records'],f['slots'],f['attack_counters'],f['hero'],f['hero']-4,f['move_counters'],play,653,
            rewrite=lambda source:combat.decisions(source,meta['chapter_spectacle']['runtime']['navigation'],meta['midnight_encore']['runtime']['poise'],state,table,f['hero'])))
        struct.pack_into('<I',rt.new,forge.combat.THINK_SLOT-0x02000000,think)
        second=rt.alloc();rt.data.extend(combat.secondary(second,w.u32(rt.arm,forge.combat.SECOND_SLOT-0x02000000),f['slots'],config));struct.pack_into('<I',rt.new,forge.combat.SECOND_SLOT-0x02000000,second)
        update=rt.alloc();rt.data.extend(combat.update(update,w.u32(rt.arm,forge.combat.UPDATE_SLOT-0x02000000),f['slots'],config,f['hero'],state));struct.pack_into('<I',rt.new,forge.combat.UPDATE_SLOT-0x02000000,update)
        report.update(boss=dict(clips=clips,programs=[vars(m) for m in motion.MOVES],model=art_report,lifecycle_preserved=True),runtime=dict(state=state,table=table,damage=hp,think=think,secondary=second,update=update),appended_resources={n:w.sha256(v) for n,v in added.items()})
    from tools.qol_suits_menu import StringSlots
    import mod
    _,native_glob,_=mod.load_clean();no,nn,_=w.parse_glob(native_glob)
    for name in forge.chapter.STRING_FILES:
        i=names.index(name);ni=nn.index(name);payload=StringSlots(native_glob[no[ni]:no[ni+1]]).grown(blobs[i],{50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}'})
        blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(name)
    replacements['Glob.bin']=w.pack_glob(names,blobs)
    if audio:
        from tools.midnight_voltage_audio import sound_data
        e=next(e for e in w.nitrofs_entries(rom) if e['name']=='sound_data.sdat');replacements['sound_data.sdat']=sound_data(rom[e['start']:e['end']],muted=muted)
    result=rt.finish(replacements)
    assert all(old==new for name,old,new in zip(names,before,blobs) if name not in changed)
    report.update(rom_sha256=w.sha256(result),modified_resources=changed,audio=audio,muted_fixture=muted,player_kit_preserved=True)
    h=w.parse_header(result);report['arm9_sha256']=w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']])
    if audio and boss and not muted:
        from tools import release_info
        pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
        for key in ('rom_sha256','arm9_sha256'):
            if pin.get(key) and pin[key]!=report[key]:raise ValueError('Voltage differs from immutable release pin')
    return result,report


def generate(output,source=None,**options):
    output=Path(output);source=Path(source) if source else ROOT/'build/version-0.25.0-final/Versioned.nds'
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidate must stay in build/')
    raw,report=apply_rom(source.read_bytes(),**options);path=output/'Versioned.nds';meta=json.loads(source.with_suffix('.build.json').read_text())
    meta['midnight_voltage']=report;meta.update(release_version=VERSION,release_date=DATE,output_rom_sha256=w.sha256(raw),output=str(path.resolve()))
    v=w.validate_rom(raw,target=True);meta.update(rom_size=len(raw),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'])
    w.atomic_write(path,raw,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION);w.write_json(output/'gameplay_profile.json',recipe)
    print(json.dumps(dict(candidate=str(path),sha256=report['rom_sha256'],runtime=report.get('runtime'))));return path


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'build/version-0.25.0-final/Versioned.nds');p.add_argument('--sound-probe',type=int);p.add_argument('--out',type=Path,required=True);p.add_argument('--linear',action='store_true');p.add_argument('--gain',type=float,default=1);p.add_argument('--fixed',action='store_true');p.add_argument('--no-audio',action='store_true');p.add_argument('--audio-only',action='store_true');p.add_argument('--mute-owned',action='store_true');a=p.parse_args()
    if a.sound_probe is not None:diagnostic(a.source,a.out,a.sound_probe,a.linear,a.gain,a.fixed)
    else:generate(a.out,a.source,audio=not a.no_audio,boss=not a.audio_only,muted=a.mute_owned)
