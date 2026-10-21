"""Read live spawn constructor choices while using copied-save native inputs."""
import argparse,json,os,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import midnight_rebuild_lab as driver,midnight_rework_lab as lab,wos_tool as w


def main():
    p=argparse.ArgumentParser();p.add_argument('case',choices=('terminal-wave','floodworks-wave','turbine-wave','observatory','boss','press','conductor-study','map','legacy','removed-door'))
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--owned',type=Path)
    p.add_argument('--tag',default='');p.add_argument('--name',choices=('signal','refuge','terminal','floodworks'));p.add_argument('--no-heal',action='store_true');p.add_argument('--black',action='store_true');p.add_argument('--reactive',action='store_true');p.add_argument('--persist',action='store_true');p.add_argument('--capture-every',type=int,default=12);a=p.parse_args()
    if not a.out.resolve().is_relative_to((ROOT/'work').resolve()):raise ValueError('Private evidence must stay in work/')
    a.out.mkdir(parents=True,exist_ok=True);os.environ['WOS_CHAPTER_LAB_OUT']=str(a.out.resolve())
    if a.owned:
        os.environ['WOS_CHAPTER_PLAYER_PROFILE']=str(a.owned.resolve())
        from tools import owned_player_lab
        measured=owned_player_lab.install(a.owned);w.write_json(a.out/'owned-player-fixture.json',measured)
    meta=json.loads(a.rom.with_suffix('.build.json').read_text());address=meta.get('midnight_reliability_probe',{}).get('goal_log');native=lab.Walker.tick;actual_hits=[]
    def tick(self,frame,lib):
        result=native(self,frame,lib)
        if address and frame>=0 and frame%120==0 and self.last_ram:
            ram=self.last_ram;off=address-0x02000000;n=min(w.u32(ram,off),64)
            rows=[dict(zip(('room','goal_type','total_q12','live_q12'),struct.unpack_from('<4I',ram,off+4+i*16))) for i in range(n)]
            w.write_json(a.out/'goals-live.json',dict(rom_sha256=meta['output_rom_sha256'],frame=frame,rows=rows))
        contact=meta.get('midnight_reliability',{}).get('runtime',{}).get('hit_log')
        if contact and frame>=0 and frame%120==0 and self.last_ram and a.case not in ('boss','press'):
            import ctypes as ct
            from tools import kit_lab as k
            ptr,ram=k.ram_of(lib);off=contact-0x02000000;n=min(w.u32(ram,off),64)
            actual_hits.extend(dict(frame_observed=frame,values=struct.unpack_from('<8I',ram,off+4+i*32)) for i in range(n))
            ct.memmove(ptr+off,bytes(4),4)
            w.write_json(a.out/'native-hits-drained.json',dict(rows=actual_hits,limits='Only the private diagnostic log counter is drained in disposable RAM; no gameplay state changes.'))
        return result
    lab.Walker.tick=tick
    if a.owned:
        from tools import kit_lab as k
        native_run=k._run
        def owned_run(*args,**kw):
            hook=kw['extra_hook']
            def verify(frame,lib):
                result=hook(frame,lib)
                if frame==0:
                    _,ram=k.ram_of(lib);s=w.u32(ram,k.STATS_POINTER-0x02000000)-0x02000000
                    actual=list(struct.unpack_from('<3I',ram,s+12));w.write_json(a.out/'owned-at-combat.json',dict(words=actual,expected=measured['ability_words'],xp=w.u32(ram,s+0x44),hp=w.u32(ram,s+0x84),passed=actual==measured['ability_words']))
                    if actual!=measured['ability_words']:raise ValueError('Lab changed current player purchases')
                return result
            kw['extra_hook']=verify;return native_run(*args,**kw)
        k._run=owned_run
    if a.case in ('boss','press'):
        from tools import midnight_voltage_lab
        return midnight_voltage_lab.boss_case(a)
    if a.case in ('map','legacy','removed-door'):
        from tools import chapter_renewal_lab as q,creature_forge_lab as forge,midnight_walk as mw,kit_lab as k,playtest
        from tools.midnight_reliability_rooms import BY_ID
        actual=playtest.current_save();before=actual.read_bytes();copy=a.out/'current-player-copy.dsv';copy.write_bytes(before);k.TRAINING_SAVE=copy
        q.configure_rooms(a.rom);forge.OUT=a.out;q.OUT=a.out;q.RUN_TAG=a.tag;forge.install(a.rom,a.capture_every)
        if a.case=='map':
            index=87;spawn=2;steps=[mw.wait(90),mw.hold('Select',6),mw.wait(90),mw.hold('Select',6),mw.wait(90),mw.hold('Select',6),mw.wait(90)]
        elif a.case=='legacy':
            if a.name not in ('signal','refuge'):p.error('legacy requires --name signal|refuge')
            index=77 if a.name=='signal' else 82;spawn=0;target=78 if index==77 else 81
            steps=[mw.wait(90),mw.hold('Right',180),mw.until('legacy_native_return',lambda s:s.room==target,1600,'Right+X'),mw.wait(90),mw.check('legacy_recovery_reaches_active_room',lambda s:s.room==target)]
        else:
            if a.name not in ('terminal','floodworks'):p.error('removed-door requires --name terminal|floodworks')
            index=78 if a.name=='terminal' else 81;spawn=3
            steps=[mw.wait(45),mw.hold('Left+B',24),*[step for _ in range(18) for step in (mw.hold('Left+Up+X',4),mw.hold('Left+Up',4))],mw.wait(45),mw.check('retired_entry_cannot_be_used',lambda s:s.room==index)]
        result=q.run(a.rom,a.case+'-'+str(index),BY_ID[index],spawn,steps,combat=False,heal=True)
        result['source_battery_unchanged']=actual.read_bytes()==before;w.write_json(a.out/'result.json',result)
        return 0 if result['passed'] and result['source_battery_unchanged'] else 1
    if a.no_heal:
        from tools import chapter_renewal_lab as q
        native_qrun=q.run
        def no_refills(*args,**kw):kw['heal']=False;return native_qrun(*args,**kw)
        q.run=no_refills
    sys.argv=[sys.argv[0],a.case,'--rom',str(a.rom),'--tag='+a.tag];return driver.main()


if __name__=='__main__':raise SystemExit(main())
