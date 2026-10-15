"""Crane hoist encounter, moving scenery and room-scoped native adapters.

The animated native smashable retains its hit binding. Separate authored
meshes provide the motor, guard and moving grabber. Motion uses the native
world-object get/set-position API, never a player-coordinate write.
"""
from collections import OrderedDict
import struct
from tools import midnight_boss as mb,midnight_rooms as mr,room_script as s,nitro_build as nb,room_compiler as rc
from tools.room_events import Command,EventGroup

BASE=0x02000000
ROOM=106
WEIGHT_ROOM=102
CORE=0x21
# Use native electric variants, fire and box. Empty kind slots do not
# instantiate an actor. Warning electric data are harmless and non-solid.
WARN,MOTOR,HOOK,SHIELD=0x11,0x13,0x12,0x1F
HEALTH=36*4096
HP_SITE=0x0206AFA8
TICK_SITE=0x02069980
RUN,EXPOSED,ZONE,TARGET,MODE,STEP=range(0x127,0x12D)
LANES=(312,344,376)
MOTOR_X=352
ARC_OFFSETS=(0,)  # A single native live strip fits each 24-unit warning pad.

def _branch(at,to,cond=14,link=False):
    displacement=to-at-8
    if displacement%4 or not -(1<<25)<=displacement<(1<<25):raise ValueError('ARM branch range')
    return cond<<28|(0x0B000000 if link else 0x0A000000)|((displacement>>2)&0xFFFFFF)

class Arm:
    def __init__(self,at):self.at=at;self.words=[];self.labels={};self.branches=[];self.loads=[];self.pool=OrderedDict();self.blobs=OrderedDict()
    def emit(self,*words):self.words.extend(words)
    def label(self,key):
        if key in self.labels:raise ValueError('Duplicate ARM label')
        self.labels[key]=self.at+len(self.words)*4
    def b(self,key,cond=14,link=False):self.branches.append((len(self.words),key,cond,link));self.emit(0)
    def lit(self,reg,key,value=None):
        if key in self.pool and value is not None and self.pool[key] not in (None,value):raise ValueError('Literal changed')
        if key not in self.pool:self.pool[key]=value
        self.loads.append((len(self.words),reg,key));self.emit(0)
    def blob(self,key,data):self.blobs[key]=bytes(data)
    def finish(self):
        words=list(self.words);pool_at=self.at+len(words)*4
        addresses={k:pool_at+4*i for i,k in enumerate(self.pool)}
        tail=bytearray();blob_at=pool_at+len(self.pool)*4
        for key,data in self.blobs.items():
            tail.extend(bytes(-len(tail)%4));self.pool[key]=blob_at+len(tail);tail.extend(data)
        for index,key,cond,link in self.branches:words[index]=_branch(self.at+index*4,self.labels[key] if isinstance(key,str) else key,cond,link)
        for index,reg,key in self.loads:
            displacement=addresses[key]-(self.at+index*4+8)
            if not 0<=displacement<4096:raise ValueError('ARM literal range')
            words[index]=0xE59F0000|reg<<12|displacement
        if any(v is None for v in self.pool.values()):raise ValueError('Unresolved literal')
        return struct.pack(f'<{len(words)+len(self.pool)}I',*words,*self.pool.values())+tail

def _mesh(name,boxes):
    faces=[]
    for x0,y0,z0,x1,y1,z1,colour in boxes:
        look=rc.Look('none')
        for q in rc.box(x0,y0,z0,x1,y1,z1,look,1,'front top under left right'):
            faces.append((sum(round(c*q.shade)<<(5*i) for i,c in enumerate(colour)),tuple((*p,0,0) for p in q.corners)))
    points=[p for _,vs in faces for p in vs]
    lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    scale=8
    model=nb.RoomModel(name,'root',bytes((7,248,0,16)),(nb.Material('steel',None,None,nb.material_record(8,8,texture_param=0)),),
        (rc._stream(faces,scale*4096),),((0,0),),scale*4096,(len(faces)*4,len(faces),0,len(faces)),
        tuple(round(v*4096/scale) for v in (*lo,*(b-a for a,b in zip(lo,hi)))),scale*4096)
    return nb.room_model(model)

def models():
    steel=(18,22,25);gold=(31,23,6);hot=(31,28,13);dark=(5,8,11)
    return {
      'motor':_mesh('HoistMotor',[(-12,0,0,12,16,3,steel),(-10,2,3,10,14,4,dark),(-4,3,4,4,12,5,hot),(-2,4,5,2,11,5.3,(31,31,27))]),
      'shield':_mesh('HoistGuard',[(-10,0,4,10,15,7,steel),(-9,6,7,9,8,8,gold)]),
      'hook':_mesh('CargoGrabber',[(-9,9,0,9,16,5,gold),(-11,0,0,-7,11,5,steel),(7,0,0,11,11,5,steel),
                                    (-11,0,0,-3,3,5,gold),(3,0,0,11,3,5,gold),(-1.2,16,-1,1.2,60,1,steel)]),
      'weight':_mesh('Counterweight',[(-13,0,-20,13,20,-12,steel),(-12,8,-12,12,11,-11,gold),(-1,20,-18,1,58,-16,steel)]),
      'warning':_mesh('CargoWarning',[(-12,-.5,-20,12,.6,20,gold),(-10,.6,0,-8,1,15,dark),(8,.6,0,10,1,15,dark)])}

def data_adapter(clean_arm,at,old_target,resources):
    native=clean_arm[mb.DATA_BASE-BASE+CORE*64:mb.DATA_BASE-BASE+(CORE+1)*64]
    core=bytearray(native);struct.pack_into('<I',core,20,HEALTH)
    harmless=bytearray(clean_arm[mb.DATA_BASE-BASE+mb.WARNING_KIND*64:mb.DATA_BASE-BASE+(mb.WARNING_KIND+1)*64]);struct.pack_into('<I',harmless,0,0)
    records={'core':bytes(core)}
    for key in ('warning','motor','hook','shield','weight'):
        entry=bytearray(harmless);struct.pack_into('<2I',entry,4,0xB6,resources[key]);records[key]=bytes(entry)
    a=Arm(at);a.emit(0xE92D500F);a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('fallback',0)
    a.emit(0xE5922000,0xE3520000|ROOM);a.b('boss',0)
    a.emit(0xE3520000|WEIGHT_ROOM);a.b('fallback',1);a.emit(0xE3510000|HOOK);a.b('fallback',1)
    a.lit(2,'weight');a.b('store')
    a.label('boss')
    # Warning and live strips use the native electric actor family. A
    # smashable warning panel carries unwanted solid-body collision.
    a.emit(0xE3510000|WARN);a.b('other_kind',1)
    a.lit(2,'manager',0x02145C34);a.emit(0xE5922000,0xE3520000);a.b('fallback',0)
    a.emit(0xE5D221C4,0xE3520001);a.b('fallback',1)
    a.lit(2,'warning');a.b('store')
    a.label('other_kind')
    for kind,key in ((CORE,'core'),(MOTOR,'motor'),(HOOK,'hook'),(SHIELD,'shield')):
        a.emit(0xE3510000|kind);a.b('next_'+key,1);a.lit(2,key);a.b('store');a.label('next_'+key)
    a.label('fallback');a.emit(0xE8BD500F);a.b(old_target)
    a.label('store');a.emit(0xE5802000,0xE8BD900F)
    for key,value in records.items():a.blob(key,value)
    return a.finish()

def hp_adapter(at):
    a=Arm(at);a.emit(0xE92D500F,0xE590210C,0xE3520021);a.b('native',1)
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('native',0)
    a.emit(0xE5922000,0xE352006A);a.b('native',1)
    a.lit(2,'manager',0x02145C34);a.emit(0xE5922000,0xE3520000);a.b('native',0)
    a.emit(0xE5D221C1,0xE3520001);a.b('native',0)
    a.emit(0xE8BD500F,0xE12FFF1E)
    a.label('native');a.emit(0xE8BD500F,0xE92D000F);a.b(HP_SITE+4)
    return a.finish()

def motion_adapter(at,state):
    a=Arm(at);a.emit(0xE92D51FF,0xE24DD014,0xE1A04000,0xE590210C,0xE3520000|HOOK);a.b('native',1)
    a.emit(0xE5D42168,0xE3520000);a.b('native',1)
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('native',0)
    a.emit(0xE5922000,0xE3520066);a.b('weight',0)
    a.emit(0xE352006A);a.b('native',1)
    a.lit(5,'manager',0x02145C34);a.emit(0xE5955000,0xE3550000);a.b('native',0)
    a.emit(0xE5D531C3) # scratch TARGET (0x12A), manager +0x1C3
    a.emit(0xE3530002,0x83A03001)
    a.lit(6,'lane0',LANES[0]*4096);a.emit(0xE0866883) # add r6,r6,r3,lsl#17 (32 units Q12)
    a.lit(7,'high',20*4096);a.lit(8,'speed',2*4096)
    a.emit(0xE5D531C4,0xE3530002);a.b('slam',0)
    a.emit(0xE3530004);a.b('sweep',0);a.b('move')
    a.label('slam');a.lit(7,'low',2*4096);a.lit(8,'fast',4*4096);a.b('move')
    a.label('sweep');a.lit(6,'right',LANES[2]*4096);a.lit(7,'low');a.lit(8,'sweep_speed',4096);a.b('move')
    a.label('weight');a.lit(2,'stats');a.emit(0xE5922000,0xE5D2302D,0xE3130010);a.b('native',0)
    a.lit(5,'state',state);a.emit(0xE5952000,0xE2822001,0xE35200F0,0x23A02000,0xE5852000,0xE3520078)
    a.lit(7,'weight_high',154*4096);a.b('weight_done',3);a.lit(7,'weight_low',34*4096)
    a.label('weight_done');a.lit(6,'weight_x',88*4096);a.lit(8,'weight_speed',4096)
    a.label('move');a.emit(0xE1A0000D,0xE1A01004);a.b(0x02069D54,link=True)
    for offset,reg in ((0,6),(4,7)):
        a.emit(0xE59D0000|offset,0xE0401000|reg<<16,0xE1510008,0xC1A01008,
               0xE2682000,0xE1510002,0xB1A01002,0xE0800001,0xE58D0000|offset)
    a.emit(0xE1A00004,0xE1A0100D);a.b(0x02069CE4,link=True)
    a.label('native');a.emit(0xE28DD014,0xE8BD51FF,0xE92D4FF0);a.b(TICK_SITE+4)
    return a.finish()

def wave_adapter(at,old_target):
    a=Arm(at);a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b(old_target,0)
    a.emit(0xE5923000,0xE3530060);a.b(old_target,3);a.emit(0xE353006C);a.b(old_target,2)
    a.emit(0xE5913000);a.lit(2,'normal',0x021301D0);a.emit(0xE1530002);a.b(old_target,1)
    a.emit(0xE5913044,0xE3530000);a.b(0x0204C2CC,13);a.b(0x0204C340)
    return a.finish()

def stage(raw,blob,flags,say):
    groups=OrderedDict();old=s.counts(raw,1)[1]
    def gid(n):
        if n not in groups:groups[n]=None
        return old+list(groups).index(n)+1
    def group(n,commands):gid(n);groups[n]=EventGroup(tuple(c for c in commands if c is not None))
    def call(n,frames=0):return s.activate(eg=gid(n),frames=frames)
    def test(v,op,x,yes,no=None):return s.if_var(v,op,x,then=s.action(eg=gid(yes)),otherwise=s.action(eg=gid(no)) if no else bytes(4))
    def running(n,commands):
        group(n,[test(RUN,'==',1,n+'_Alive')]);group(n+'_Alive',[test(flags['boss'],'==',0,n+'_Go')]);group(n+'_Go',commands)
    def batch(n,items):
        nonlocal raw
        raw,ag=s.append_batch(raw,1,items,n);return ag
    def object(kind,xy,callback=0):
        e=mr._placed(mr._native_entity(blob('proto01_app.obj'),'Object (Hazard_Electric)'),xy)
        e[22]=kind;e[23]=callback;return bytes(e)
    core=mr._placed(mr._native_entity(blob('Hive_Map03_app.obj'),'Object (Smashable_IchorBlob) 1'),(MOTOR_X,8));core[23]=gid('Victory')
    core_ag=batch('Hoist Motor',[(bytes(core),'Object (Hoist Motor)')])
    motor=batch('Exposed Motor',[(object(MOTOR,(MOTOR_X,1)),'Object (Exposed Motor)')])
    shield=batch('Motor Guard',[(object(SHIELD,(MOTOR_X,1)),'Object (Motor Guard)')])
    hook=batch('Cargo Grabber',[(object(HOOK,(344,20)),'Object (Cargo Grabber)')])
    warnings=[batch('Warning '+str(i),[(object(WARN,(x,1)),'Object (Cargo Warning)')]) for i,x in enumerate(LANES)]
    arcs=[batch('Impact '+str(i),[(object(0x11,(x+d,1)),'Object (Cargo Impact)') for d in ARC_OFFSETS]) for i,x in enumerate(LANES)]
    start=batch('Hoist Entry',[(s.trigger(296*4096,8*4096,(8,32),gid('Begin')),'Trigger (Hoist Entry)')])
    gang=mr.Gang('Pier_Map04',8,(344,12),(80,38),'Hoist Crew')
    adds=batch('Hoist Crew',[(mr._spawner(blob,gang),'EnemySpawner (Hoist Crew)')])
    # Native zone triggers select the lane at warning start, then the target
    # stays committed. Leaving a zone does not erase the last valid lane.
    zones=[]
    for i,x in enumerate(LANES):
        group('Zone'+str(i),[s.set_var(ZONE,i)])
        e=s.trigger(x*4096,12*4096,(30,44),gid('Zone'+str(i)))
        zones.append((e,'Trigger (Hoist Lane '+str(i)+')'))
    zone_ag=batch('Hoist Lanes',zones)
    dark=[s.deactivate(ag=a) for a in (*warnings,*arcs)]
    group('Idle',[s.activate(ag=start)])
    group('Clear',[*dark,s.deactivate(ag=hook),s.deactivate(ag=shield),s.deactivate(ag=motor)])
    group('Begin',[test(RUN,'==',0,'Begin_Check')]);group('Begin_Check',[test(flags['boss'],'==',0,'Start')])
    group('Start',[s.set_var(RUN,1),s.set_var(EXPOSED,0),s.set_var(STEP,0),s.set_var(MODE,1),
                   Command(0x15,bytes(8)),
                   s.activate(ag=core_ag),s.activate(ag=shield),s.activate(ag=hook),s.activate(ag=zone_ag),
                   s.deactivate(ag=start),s.activate(ag=adds),call('Stop_Crew',45),call('Next',45)])
    running('Stop_Crew',[s.deactivate(ag=adds)])
    running('Next',[*dark,s.set_var(EXPOSED,0),s.activate(ag=shield),s.deactivate(ag=motor),
                    test(STEP,'==',0,'Select','Sweep_Warn')])
    group('Select',[test(ZONE,'==',0,'Warn0','Select1')]);group('Select1',[test(ZONE,'==',1,'Warn1','Warn2')])
    for i in range(3):
        running('Warn'+str(i),[s.set_var(TARGET,i),s.set_var(MODE,1),s.activate(ag=warnings[i]),call('Drop'+str(i),70)])
        running('Drop'+str(i),[s.set_var(MODE,2),call('Hit'+str(i),6)])
        running('Hit'+str(i),[s.deactivate(ag=warnings[i]),s.activate(ag=arcs[i]),call('Recover',30)])
    running('Sweep_Warn',[s.set_var(TARGET,0),s.set_var(MODE,1),*(s.activate(ag=a) for a in warnings),call('Sweep_Drop',70)])
    running('Sweep_Drop',[s.set_var(MODE,2),call('Sweep_0',6)])
    running('Sweep_0',[*dark,s.set_var(MODE,4),s.activate(ag=arcs[0]),call('Sweep_1',32)])
    running('Sweep_1',[s.deactivate(ag=arcs[0]),s.activate(ag=arcs[1]),call('Sweep_2',32)])
    running('Sweep_2',[s.deactivate(ag=arcs[1]),s.activate(ag=arcs[2]),call('Recover',32)])
    running('Recover',[*dark,s.set_var(MODE,3),s.set_var(EXPOSED,1),s.deactivate(ag=shield),s.activate(ag=motor),call('Recover_End',100)])
    running('Recover_End',[test(STEP,'==',0,'Set_Sweep','Set_Slam')])
    group('Set_Sweep',[s.set_var(STEP,1),call('Next')]);group('Set_Slam',[s.set_var(STEP,0),call('Next')])
    group('Victory',[test(flags['boss'],'==',0,'Win')])
    group('Win',[s.set_var(RUN,0),s.set_var(EXPOSED,0),s.set_var(flags['boss'],1),*dark,
                 *(s.deactivate(ag=a) for a in (hook,motor,shield,adds,start,zone_ag)),say('boss_clear'),call('Clear_Line',240)])
    group('Clear_Line',[Command(0x15,bytes(8))])
    if any(g is None for g in groups.values()):raise ValueError('Unresolved hoist group')
    raw,_=s.append_groups(raw,1,list((g,n) for n,g in groups.items()))
    return s.extend_group(raw,1,0,[*(s.set_var(v,0) for v in range(RUN,STEP+1)),test(flags['boss'],'==',0,'Idle','Clear')],prepend=True)

def weight(raw,blob):
    e=mr._placed(mr._native_entity(blob('proto01_app.obj'),'Object (Hazard_Electric)'),(88,34));e[22]=HOOK;e[23]=0
    raw,ag=s.append_batch(raw,1,[(bytes(e),'Object (Moving Counterweight)')],'Moving Counterweight')
    return s.extend_group(raw,1,0,[s.activate(ag=ag)])
