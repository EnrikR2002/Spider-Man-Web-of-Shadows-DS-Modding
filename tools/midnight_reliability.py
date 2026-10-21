"""Exact0.27 diagnostics and the next guarded Midnight composition."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import midnight_voltage as prior,wos_tool as w,tasm_kit as kit,crane_row as crane,creature_forge as forge
from tools.chapter_renewal_combat import asm

PARENT='1b1e4e37d48f4a5661b77ac10032e694d1985347b7eb0f70fdd5d828226cdc4d'
VERSION='0.28.0';DATE='2026-10-19';offset=forge.offset
RAMP={78:((21,20,21,36),(9,3),(13,20,11)),81:((36,20,21,21),(11,5),(15,22,12)),
      83:((36,21,20,21),(13,5),(16,24,13)),86:((36,20,21,21,20),(16,5),(18,26,15))}


class Runtime(prior.Runtime):
    def __init__(self,rom):
        if w.sha256(rom)!=PARENT:raise ValueError('Reliability requires exact published0.27')
        self.rom=rom;self.header=w.parse_header(rom);h=self.header
        self.arm=rom[h['arm9_offset']:h['arm9_offset']+h['arm9_size']];self.new=bytearray(self.arm)
        self.end=len(self.arm)-36;self.start=kit.TARGET+self.end-kit.SOURCE;self.data=bytearray()


def goal_observer(at,old,log,table):
    """Read constructor requests and their actual selected production budgets."""
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        ldr r2,stats
        ldr r2,[r2]
        cmp r2,#0
        beq native
        ldr r2,[r2]
        cmp r2,#76
        blo native
        cmp r2,#90
        bhs native
        ldr r3,table
    find:
        ldr r4,[r3]
        cmp r4,#0
        beq native
        cmp r4,r2
        beq found
        add r3,r3,#20
        b find
    found:
        cmp r1,#14
        ldreq r3,[r3,#8]
        ldrne r3,[r3,#4]
        ldr r0,log
        ldr r4,[r0]
        cmp r4,#64
        bhs native
        add r4,r4,#1
        str r4,[r0]
        sub r4,r4,#1
        add r0,r0,#4
        add r0,r0,r4,lsl #4
        str r2,[r0]
        str r1,[r0,#4]
        ldr r2,[r3]
        str r2,[r0,#8]
        ldr r2,[r3,#4]
        str r2,[r0,#12]
    native:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        b #0x{old:x}
    stats: .word 0x02145c5c
    log: .word 0x{log:x}
    table: .word 0x{table:x}
    ''',at)


def diagnostic(output,source=None):
    source=Path(source) if source else ROOT/'build/version-0.27.0-final/Versioned.nds';output=Path(output)
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Probe must stay in build/')
    rt=Runtime(source.read_bytes());meta=json.loads(source.with_suffix('.build.json').read_text())
    log=rt.alloc(bytes(4+64*16));site=0x0204c15c;old=crane.target(site,w.u32(rt.arm,site-0x02000000));at=rt.alloc()
    rt.data.extend(goal_observer(at,old,log,meta['chapter_spectacle']['scripted_runtime']['goal_table']));rt.hook(site,at,link=True)
    raw=rt.finish();path=output/'Probe.nds';w.atomic_write(path,raw,sources=(source,))
    meta['midnight_reliability_probe']=dict(goal_log=log);meta['output_rom_sha256']=w.sha256(raw);w.write_json(path.with_suffix('.build.json'),meta)
    print(json.dumps(dict(path=str(path),sha256=w.sha256(raw),log=log)));return path


def apply_rom(rom,*,pilot=False):
    from tools import midnight_reliability_combat as c,midnight_voltage_combat as voltage
    from tools import midnight_finale_motion as motion
    rt=Runtime(rom);meta=json.loads((ROOT/'build/version-0.27.0-final/Versioned.build.json').read_text())
    f=meta['creature_forge']['runtime'];cfgs=meta['creature_forge']['creatures'];boss=cfgs['conductor']['config'];warden=cfgs['warden']['config']
    state=rt.alloc(bytes(80))
    life=rt.alloc();rt.data.extend(c.lifecycle(life,crane.target(0x020776bc,w.u32(rt.arm,0x776bc)),state,f['slots']));rt.hook(0x020776bc,life)
    old_table=meta['midnight_finale']['runtime']['table'];table=rt.alloc(rt.arm[offset(old_table):offset(old_table)+6*32]);empty=rt.alloc(struct.pack('<2I',0x7fffffff,0))
    for i in (4,5):
        cue=rt.alloc(struct.pack('<8I',0,708,12,709,29,709,0x7fffffff,0))
        struct.pack_into('<I',rt.data,table-rt.start+i*32,136)
        struct.pack_into('<2I',rt.data,table-rt.start+i*32+16,empty,cue)
    struct.pack_into('<2I',rt.new,offset(f['records'])+6*16+4,table,6)
    def rows(values):return rt.alloc(b''.join(struct.pack('<3I',*v) for v in values)+struct.pack('<3I',0xffffffff,0,0))
    guarded=[(m.action,a,min(b,a+3)) for m in motion.BOSS[:4] for a,b in m.contacts]
    ward=[(m.action,max(0,a-3),b) for m in motion.MOVES['warden'] for a,b in m.contacts]
    ranges=[(m.action,a,b) for m in motion.BOSS[:4] for a,b in m.contacts]
    guard_table=rows(guarded);ward_table=rows(ward);contact_table=rows(ranges)
    guard=rt.alloc();rt.data.extend(c.interval(guard,guard_table));wc=rt.alloc();rt.data.extend(c.interval(wc,ward_table));contact=rt.alloc();rt.data.extend(c.interval(contact,contact_table))
    check=rt.alloc();rt.data.extend(c.armour(check,f['slots'],boss,warden,guard,wc,table))
    if w.u32(rt.arm,c.IMPULSE_SITE-0x02000000)!=0xe5961044:raise ValueError('Native impulse hook prologue differs')
    hit=rt.alloc();rt.data.extend(c.impulse(hit,check,state+56));rt.hook(c.IMPULSE_SITE,hit)
    hit_log=rt.alloc(bytes(4+64*32));observer=rt.alloc();rt.data.extend(c.hit_observer(observer,boss,hit_log))
    if w.u32(rt.arm,c.CONTACT_RESULT_SITE-0x02000000)!=0xe59d0054:raise ValueError('Contact post-result prologue differs')
    rt.hook(c.CONTACT_RESULT_SITE,observer)
    hp=rt.alloc();rt.data.extend(voltage.damage(hp,crane.target(0x02049304,w.u32(rt.arm,0x49304)),state,boss,hit_threshold=4,window=100));rt.hook(0x02049304,hp)
    capture=forge.parent.combat.capture_hero(f['capture'],f['hero']);play=f['capture']+len(capture)
    think=rt.alloc();rt.data.extend(forge.combat.think(think,f['records'],f['slots'],f['attack_counters'],f['hero'],f['hero']-4,f['move_counters'],play,653,
        rewrite=lambda s:c.decisions(s,meta['chapter_spectacle']['runtime']['navigation'],meta['midnight_encore']['runtime']['poise'],state,table,f['hero'],check)))
    struct.pack_into('<I',rt.new,forge.combat.THINK_SLOT-0x02000000,think)
    second=rt.alloc();rt.data.extend(c.secondary(second,meta['chapter_spectacle']['runtime']['secondary'],f['slots'],boss,check));struct.pack_into('<I',rt.new,forge.combat.SECOND_SLOT-0x02000000,second)
    update=rt.alloc();rt.data.extend(c.update(update,f['update'],f['slots'],boss,f['hero'],state,contact,table));struct.pack_into('<I',rt.new,forge.combat.UPDATE_SLOT-0x02000000,update)
    e=next(e for e in w.nitrofs_entries(rom) if e['name']=='Glob.bin');g=rom[e['start']:e['end']];o,names,_=w.parse_glob(g);blobs=[g[a:b] for a,b in zip(o,o[1:])]
    import mod
    from tools.qol_suits_menu import StringSlots,decode_grown
    _,ng,_=mod.load_clean();no,nn,_=w.parse_glob(ng)
    changed=[]
    rooms=None;ramp={}
    if not pilot:
        from tools import midnight_reliability_rooms as room_changes
        rooms=room_changes.apply(names,blobs,rt,lambda n:ng[no[nn.index(n)]:no[nn.index(n)+1]],meta);changed.extend(rooms['modified_resources'])
        scripted=meta['chapter_spectacle']['scripted_runtime'];roster=scripted['roster_table'];goals=scripted['goal_table']
        for room,(pattern,budget,hp_values) in RAMP.items():
            pat=rt.alloc(bytes(pattern));found=False
            for row in range(40):
                off=offset(roster)+row*12;rid=w.u32(rt.arm,off)
                if not rid:break
                if rid==room:struct.pack_into('<2I',rt.new,off+4,pat,len(pattern));found=True;break
            if not found:raise ValueError('Missing roster room')
            for row in range(40):
                off=offset(goals)+row*20;rid=w.u32(rt.arm,off)
                if not rid:raise ValueError('Missing goal room')
                if rid==room:
                    for col in (4,8):
                        ptr=w.u32(rt.arm,off+col);data=bytearray(rt.arm[offset(ptr):offset(ptr)+24]);struct.pack_into('<2I',data,0,budget[0]*4096,budget[1]*4096)
                        dest=rt.alloc(data);struct.pack_into('<I',rt.new,off+col,dest)
                    break
            ramp[str(room)]=dict(pattern=pattern,total_cost=budget[0],live_cost=budget[1],base_HP=hp_values,max_live_actors=4)
        cfg_array=rt.alloc(struct.pack('<3I',*(cfgs[s]['config'] for s in ('skitter','warden','eye'))))
        stats=rt.alloc(b''.join(struct.pack('<4I',room,*(v*4096 for v in hp)) for room,hp in [(76,(12,18,10)),*((r,data[2]) for r,data in RAMP.items()),(88,(12,18,10)),(89,(12,18,10))])+bytes(16))
        site=0x0204c5a4;spawn=rt.alloc();rt.data.extend(c.staged_spawn(spawn,crane.target(site,w.u32(rt.arm,site-0x02000000)),stats,cfg_array,f['slots'],f['hero']-4));rt.hook(site,spawn,link=True)
    for name in forge.chapter.STRING_FILES:
        i=names.index(name);ni=nn.index(name)
        if 'Pump Refuge' not in decode_grown(blobs[i],1131) or 'Signal House' not in decode_grown(blobs[i],1133):raise ValueError('Expected prior chapter guide slots')
        edits={50:f'TASM v{VERSION}\nPress a button to start',74:f'Options v{VERSION}',
            1131:'Terminal > Floodworks > Turbine Rise.\nObservatory > Sanctuary > Conductor.\nX opens the marked doors.\nSave: Relay Sanctuary before the boss.\nCrown Return leads to Storm Gate.',
            1133:'Conductor defeated.\nCrown Return leads to Storm Gate.\nStorm Gate left: back to Sewer.\nSave at Relay Sanctuary first.\nSave in-game before closing.'}
        raw=StringSlots(ng[no[ni]:no[ni+1]]).grown(blobs[i],edits)
        blobs[i]=raw+bytes((len(blobs[i])-len(raw))%4);changed.append(name)
    result=rt.finish({'Glob.bin':w.pack_glob(names,blobs)});h=w.parse_header(result)
    report=dict(version=VERSION,parent_sha256=PARENT,pilot=pilot,runtime=dict(state=state,table=table,armour=check,impulse=hit,think=think,secondary=second,update=update,contact=contact,hit_log=hit_log,lifecycle=life),modified_resources=changed,rooms=rooms,ramp=ramp,
        boss_armour=guarded,warden_armour=ward,player_kit_preserved=True,rom_sha256=w.sha256(result),arm9_sha256=w.sha256(result[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]))
    if not pilot:
        from tools import release_info
        pin=release_info.PROFILE_INFO.get('tasm-v'+VERSION,{})
        for key in ('rom_sha256','arm9_sha256'):
            if pin.get(key) and pin[key]!=report[key]:raise ValueError('Reliability differs from immutable release pin')
    return result,report


def generate(output,source=None,**options):
    output=Path(output);source=Path(source) if source else ROOT/'build/version-0.27.0-final/Versioned.nds'
    if not output.resolve().is_relative_to((ROOT/'build').resolve()):raise ValueError('Candidate must stay in build/')
    raw,report=apply_rom(source.read_bytes(),**options);path=output/'Versioned.nds';meta=json.loads(source.with_suffix('.build.json').read_text())
    meta['midnight_reliability']=report;meta.update(release_version=VERSION,release_date=DATE,output_rom_sha256=w.sha256(raw),output=str(path.resolve()))
    v=w.validate_rom(raw,target=True);e=next(e for e in v['nitrofs'] if e['name']=='Glob.bin');meta.update(rom_size=len(raw),used_rom_size=v['header']['used_rom_size'],nitrofs=v['nitrofs'],header_crc16=v['header']['header_crc16'],output_glob_sha256=w.sha256(raw[e['start']:e['end']]))
    w.atomic_write(path,raw,sources=(source,));w.write_json(path.with_suffix('.build.json'),meta)
    recipe=json.loads((ROOT/'reference/gameplay_profile.json').read_text());recipe.update(profile='tasm-v'+VERSION,release_version=VERSION);w.write_json(output/'gameplay_profile.json',recipe)
    print(json.dumps(dict(path=str(path),sha256=report['rom_sha256'],runtime=report['runtime'])));return path


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--source',type=Path);p.add_argument('--diagnostic',action='store_true');p.add_argument('--pilot',action='store_true');a=p.parse_args()
    if a.diagnostic:diagnostic(a.out,a.source)
    else:generate(a.out,a.source,pilot=a.pilot)
