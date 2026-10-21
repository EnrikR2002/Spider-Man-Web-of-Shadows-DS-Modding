"""The Conductor: a damageable original creature and HP-driven storm phases."""
import struct
from tools import room_script as s, midnight_rooms as mr, midnight_boss as mb, wos_tool as w
from tools.room_events import Command,EventGroup,Events
from tools.room_objects import RoomObjects
from tools.crane_boss import Arm

DEFEATED=147
LEGACY_DEFEATED=246
RUN,STEP,PHASE=0x127,0x128,0x129
LANES=(44,112,180)
HP_SITE=0x02049304

def hp_adapter(at):
    """Observe the native HP setter, retaining its prologue and all arguments.

    NormalEnemy+0x44/48 are current/max HP. Only room89's single creature
    advances the arena phase; this does not alter damage or player position.
    """
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000)
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('native',0)
    a.emit(0xE5922000,0xE3520059);a.b('native',1)
    a.emit(0xE5902000);a.lit(3,'enemy',0x021301D0);a.emit(0xE1520003);a.b('native',1)
    a.lit(2,'manager',0x02145C34);a.emit(0xE5922000,0xE3520000);a.b('native',0)
    a.emit(0xE5D231C0,0xE3530001);a.b('native',1)
    a.emit(0xE5903048,0xE15100A3);a.b('native',8) # hp > max/2
    a.emit(0xE3A00001,0xE1510123,0x93A00002)     # <= max/4 -> phase2
    a.emit(0xE5D231C2,0xE1500003);a.b('native',9)
    a.emit(0xE5C201C2)
    a.label('native');a.emit(0xE128F00C,0xE8BD500F,0xE92D000F);a.b(HP_SITE+4)
    return a.finish()

def lock_exits(raw):
    """Closed until actual creature defeat; callbacks never credit a timeout."""
    parsed=RoomObjects.parse(raw);events=Events.parse(parsed.records[0].sections[1],parsed.records[0].raw[3]);out=raw
    for group in (1,2):
        commands=events.groups[group].commands
        out,opened=s.append_groups(out,0,[(EventGroup(commands),'Conductor Exit '+str(group))])
        out,_=s.drop_commands(out,0,lambda g,c:g==group)
        out=s.extend_group(out,0,group,[s.if_var(DEFEATED,'==',1,then=s.action(eg=opened))])
    return out

def stage(raw,blob):
    groups={};old=s.counts(raw,1)[1]
    def gid(name):
        if name not in groups:groups[name]=None
        return old+list(groups).index(name)+1
    def group(name,commands):gid(name);groups[name]=EventGroup(tuple(commands))
    def call(name,frames=0):return s.activate(eg=gid(name),frames=frames)
    def test(v,op,x,yes,no=None):return s.if_var(v,op,x,then=s.action(eg=gid(yes)),otherwise=s.action(eg=gid(no)) if no else bytes(4))
    def running(name,commands):
        group(name,[test(RUN,'==',1,name+'_Check')]);group(name+'_Check',[test(DEFEATED,'==',0,name+'_Go')]);group(name+'_Go',commands)
    def batch(name,entries):
        nonlocal raw
        raw,ag=s.append_batch(raw,1,entries,name);return ag
    start=batch('Conductor Entry',[(s.trigger(46*4096,8*4096,(6,22),gid('Start')),'Trigger (Conductor Entry)')])
    gang=mr.Gang('Pier_Map04',8,(112,16),(168,40),'The Conductor')
    crew=batch('The Conductor',[(mr._spawner(blob,gang,gid('Victory')),'EnemySpawner (The Conductor)')])
    warnings=[];arcs=[]
    arc=mr._native_entity(blob('proto01_app.obj'),'Object (Hazard_Electric)')
    for n,x in enumerate(LANES):
        warning=mr._placed(arc,(x,1));warning[22]=mb.WARNING_KIND;warning[23]=0
        live=mr._placed(arc,(x,1));live[23]=0
        warnings.append(batch('Storm Warning '+str(n),[(bytes(warning),'Object (Storm Warning)')]))
        arcs.append(batch('Storm Strike '+str(n),[(bytes(live),'Object (Storm Strike)')]))
    dark=[s.deactivate(ag=a) for a in (*warnings,*arcs)]
    group('Idle',[s.activate(ag=start)])
    group('Start',[test(RUN,'==',0,'Start_Check')]);group('Start_Check',[test(DEFEATED,'==',0,'Begin')])
    group('Begin',[s.set_var(RUN,1),s.deactivate(ag=start),s.activate(ag=crew),Command(0x15,bytes(8)),call('Next',150)])
    running('Next',[*dark,test(PHASE,'==',0,'Opening','Phase_Check')])
    group('Phase_Check',[test(PHASE,'==',1,'Charged','Critical')])
    for key,lanes,warn,live,rest in (('Opening',(1,),105,35,100),('Charged',(0,2),90,40,75),('Critical',(0,1),80,40,60)):
        running(key,[*(s.activate(ag=warnings[i]) for i in lanes),call(key+'_Live',warn)])
        running(key+'_Live',[*dark,*(s.activate(ag=arcs[i]) for i in lanes),call(key+'_Rest',live)])
        running(key+'_Rest',[*dark,call('Next',rest)])
    # Native finite spawner callback, not a timer or lab health cap.
    group('Victory',[test(DEFEATED,'==',0,'Win')])
    group('Win',[s.set_var(RUN,0),s.set_var(DEFEATED,1),s.set_var(LEGACY_DEFEATED,1),*dark,
                 s.deactivate(ag=crew),s.deactivate(ag=start),Command(0x22,struct.pack('<HH',188,0))])
    if any(g is None for g in groups.values()):raise ValueError('Unresolved Conductor event')
    raw,_=s.append_groups(raw,1,[(g,n) for n,g in groups.items()])
    raw=s.extend_group(raw,1,0,[s.set_var(RUN,0),s.set_var(STEP,0),s.set_var(PHASE,0),test(DEFEATED,'==',0,'Idle')])
    return lock_exits(raw)
