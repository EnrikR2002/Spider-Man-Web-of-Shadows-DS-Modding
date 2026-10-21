"""Guarded chapter staging, native checkpoints and saved machinery consequences."""
import struct
from tools import room_script as s,midnight_rooms as mr,room_doors
from tools.room_objects import RoomObjects
from tools.room_entities import Entities
from tools.room_events import Events,EventGroup,Command

PUMP=245
PRESSURE,ARENA_BUSY,HOIST_PHASE,WAKE=0x12D,0x12E,0x12F,0x130

def group_index(raw,record,name):
    names=s.names(raw,record)[1]
    if names.count(name)!=1:raise ValueError('Expected one event '+name)
    return names.index(name)

def rewrite(raw,record,name,change):
    obj=RoomObjects.parse(raw);rec=obj.records[record];events=Events.parse(rec.sections[1],rec.raw[3]);groups=list(events.groups)
    i=group_index(raw,record,name);groups[i]=EventGroup(tuple(change(groups[i].commands)))
    return obj.replace_section(record,1,s._events_bytes(groups))

def sound(index):return Command(0x22,struct.pack('<HH',index,0))

def triggered_patrol(raw,index,width,height):
    special={77,82,87,89,97,98,100,104,105,106}
    if index in special:return raw
    obj=RoomObjects.parse(raw);section=obj.records[1].sections[0];entities=Entities.parse(section)
    sizes=s.counts(raw,1)[0];spawners=[];offset=0
    for ag,size in enumerate(sizes):
        for ei,e in enumerate(entities.records[offset:offset+size]):
            if len(e)==28 and struct.unpack_from('<I',e,12)[0]==4:spawners.append((ag,offset+ei,e))
        offset+=size
    if not spawners:return raw
    # Keep authored vertical routes; the central arenas have deliberate sectors.
    sectors={76:(112,10,128,34),78:(168,18,232,46),81:(144,14,196,42),
             83:(96,56,144,104),86:(144,16,200,48),88:(112,12,128,38)}
    if index in sectors:
        x,y,bw,bh=sectors[index]
        for _,ei,e in spawners:
            changed=bytearray(e);struct.pack_into('<2i',changed,0,x*4096,y*4096);struct.pack_into('<2H',changed,16,bw,bh)
            section=Entities.parse(section).replace_record(ei,changed)
        raw=obj.replace_section(1,0,section)
    owned={ag+1 for ag,_,_ in spawners}
    raw,_=s.drop_commands(raw,1,lambda g,c:g==0 and c.opcode==0x1C and c.operand[4] in owned and c.operand[5]==0)
    old=s.counts(raw,1)[1];gate=old+1;live=old+2
    trigger=s.trigger(round(width/2*4096),round(height/2*4096),(max(20,int(width-96)),int(height+20)),gate)
    raw,ag=s.append_batch(raw,1,[(trigger,'Trigger (Encounter Approach)')],'Encounter Approach')
    raw,_=s.append_groups(raw,1,[
        (EventGroup((s.if_var(WAKE,'==',0,then=s.action(eg=live)),)),'Encounter_Wake'),
        (EventGroup((s.set_var(WAKE,1),s.deactivate(ag=ag),*(s.activate(ag=a,frames=18) for a,_,_ in spawners))),'Encounter_Live')])
    return s.extend_group(raw,1,0,[s.set_var(WAKE,0),s.activate(ag=ag)])

def pump(raw,native,refresh,sounds):
    switch=mr._placed(mr._native_entity(native('Sewer_Map04_app.obj'),'Object (Switch)'),(110,1));switch[23]=0
    raw,ag=s.append_batch(raw,1,[(bytes(switch),'Object (Pump Isolation Lever)')],'Pump Isolation Lever')
    old=s.counts(raw,1)[1];use=old+1
    trigger=mr._placed(mr._native_entity(native('Sewer_Map04_app.obj'),'Trigger (Button Press)'),(114,5));trigger[27]=use
    raw,button=s.append_batch(raw,1,[(bytes(trigger),'Trigger (Pump Isolation Lever)')],'Pump Lever Input')
    raw,_=s.append_groups(raw,1,[(EventGroup((s.set_var(PUMP,1),s.animate(ag,1,0x19),s.deactivate(ag=button),
        s.deactivate(ag=refresh),s.activate(ag=refresh),sound(sounds['pump-start']))),'Pump_Stabilized')])
    raw,restored=s.append_groups(raw,1,[(EventGroup((s.animate(ag,1,0x64),)),'Pump_Already_Stable')])
    return s.extend_group(raw,1,0,[s.activate(ag=ag),s.if_var(PUMP,'==',0,then=s.action(ag=button),otherwise=s.action(eg=restored))])

def refresh(raw,ag):return (s.deactivate(ag=ag),s.activate(ag=ag))

def conductor(raw,fx,sounds):
    # Arena and creature take turns committing pressure; all old RUN/death
    # guards remain in place around these bodies, including delayed actions.
    i=group_index(raw,1,'Next_Go');obj=RoomObjects.parse(raw);r=obj.records[1]
    original=Events.parse(r.sections[1],r.raw[3]).groups[i].commands
    raw,perform=s.append_groups(raw,1,[(EventGroup(original),'Floor_Perform')])
    next_id=group_index(raw,1,'Next')+1
    raw,wait=s.append_groups(raw,1,[(EventGroup((s.activate(eg=next_id,frames=12),)),'Floor_Wait_For_Creature')])
    raw=rewrite(raw,1,'Next_Go',lambda _: (s.if_var(PRESSURE,'==',0,then=s.action(eg=perform),otherwise=s.action(eg=wait)),))
    for key in ('Opening','Charged','Critical'):
        raw=rewrite(raw,1,key+'_Go',lambda commands:(s.set_var(ARENA_BUSY,1),sound(sounds['storm-tell']),*commands))
        raw=rewrite(raw,1,key+'_Rest_Go',lambda commands:(s.set_var(ARENA_BUSY,0),*commands))
    raw=rewrite(raw,1,'Win',lambda commands:(*commands,s.set_var(PRESSURE,0),s.set_var(ARENA_BUSY,0),
        *refresh(raw,fx),sound(sounds['storm-release'])))
    return s.extend_group(raw,1,0,[s.set_var(PRESSURE,0),s.set_var(ARENA_BUSY,0)])

def hoist(raw,sounds):
    # Shorter setup, larger combo openings. Real HP makes the damaged guard
    # phase more urgent while extending its exposed motor opening.
    for name in ('Warn0_Go','Warn1_Go','Warn2_Go','Sweep_Warn_Go'):
        commands=Events.parse(RoomObjects.parse(raw).records[1].sections[1],RoomObjects.parse(raw).records[1].raw[3]).groups[group_index(raw,1,name)].commands
        def timing(delay):
            return tuple(Command(c.opcode,struct.pack('<H',delay)+c.operand[2:]) if c.opcode==0x1C and struct.unpack_from('<H',c.operand)[0]==70 else c for c in commands)
        raw,base=s.append_groups(raw,1,[(EventGroup((sound(sounds['hoist-tell']),*timing(48))),name+'_Steady')])
        raw,damaged=s.append_groups(raw,1,[(EventGroup((sound(sounds['hoist-tell']),*timing(36))),name+'_Damaged')])
        raw=rewrite(raw,1,name,lambda _,b=base,d=damaged:(s.if_var(HOIST_PHASE,'==',0,then=s.action(eg=b),otherwise=s.action(eg=d)),))
    for name in ('Hit0_Go','Hit1_Go','Hit2_Go'):
        raw=rewrite(raw,1,name,lambda commands:(sound(sounds['hoist-impact']),*(Command(c.opcode,struct.pack('<H',18)+c.operand[2:]) if c.opcode==0x1C and struct.unpack_from('<H',c.operand)[0]==30 else c for c in commands)))
    commands=Events.parse(RoomObjects.parse(raw).records[1].sections[1],RoomObjects.parse(raw).records[1].raw[3]).groups[group_index(raw,1,'Recover_Go')].commands
    for key,delay in (('Steady',132),('Damaged',156)):
        changed=[Command(c.opcode,struct.pack('<H',delay)+c.operand[2:]) if c.opcode==0x1C and struct.unpack_from('<H',c.operand)[0]==100 else c for c in commands]
        raw,eg=s.append_groups(raw,1,[(EventGroup((sound(sounds['motor-open']),*changed)),'Motor_Open_'+key)])
        if key=='Steady':base=eg
        else:damaged=eg
    raw=rewrite(raw,1,'Recover_Go',lambda _:(s.if_var(HOIST_PHASE,'==',0,then=s.action(eg=base),otherwise=s.action(eg=damaged)),))
    raw=rewrite(raw,1,'Win',lambda commands:(*commands,sound(sounds['harbor-release'])))
    return s.extend_group(raw,1,0,[s.set_var(HOIST_PHASE,0)],prepend=True)

def checkpoint(raw,native):
    # Spawn0 and the actual player placement both point at a quiet approach.
    template=RoomObjects.parse(native('Sewer_Save04_app.obj'))
    sphere=next(e for e in Entities.parse(template.records[0].sections[0]).records if len(e)==16 and struct.unpack_from('<I',e,12)[0]==10)
    raw,ag=s.append_batch(raw,0,[(bytes(mr._placed(sphere,(36,1))),'SavePoint')],'Arm Approach Save')
    raw=s.extend_group(raw,0,0,[s.activate(ag=ag)])
    obj=RoomObjects.parse(raw);es=Entities.parse(obj.records[0].sections[0]);ei=next(i for i,e in enumerate(es.records) if len(e)==24 and struct.unpack_from('<I',e,12)[0]==2 and e[22]==1)
    raw=obj.replace_section(0,0,es.replace_record(ei,mr._placed(es.records[ei],(36,2))))
    header=bytearray(raw);sp=next(i for i,p in enumerate(room_doors.spawns(raw)) if p.spawn_id==0)
    struct.pack_into('<3iH',header,16+20*sp,36*4096,2*4096,0,room_doors.FACING['right']);raw=bytes(header)
    old=s.counts(raw,0)[1];cut=old+1
    raw,trip=s.append_batch(raw,0,[(s.trigger(282*4096,50*4096,(8,110),cut),'Trigger (Leave Safe Approach)')],'Leave Safe Approach')
    raw,_=s.append_groups(raw,0,[(EventGroup((s.deactivate(ag=ag),s.deactivate(ag=trip))),'Close_Checkpoint_In_Combat')])
    # Once the real win flag is set, restore the sphere exactly once. Record0
    # owns it; actions never accidentally address another record's AG bank.
    old=s.counts(raw,0)[1];poll=old+1;again=old+2
    raw,_=s.append_groups(raw,0,[
        (EventGroup((s.if_var(142,'==',1,then=s.action(ag=ag),otherwise=s.action(eg=again)),)),'Checkpoint_Await_Victory'),
        (EventGroup((s.activate(eg=poll,frames=120),)),'Checkpoint_Poll')])
    return s.extend_group(raw,0,0,[s.if_var(142,'==',0,then=s.action(ag=trip)),s.if_var(142,'==',0,then=s.action(eg=again))])

def ambience(raw,index,sounds):
    if index in (77,82,87,98,104,106):return raw
    cue=sounds['station-air'] if index<96 else sounds['harbor-air']
    old=s.counts(raw,1)[1];a=old+1;b=old+2
    raw,_=s.append_groups(raw,1,[
        (EventGroup((sound(cue),s.activate(eg=b,frames=260))),'Room_Air_A'),
        (EventGroup((s.activate(eg=a,frames=85),)),'Room_Air_B')])
    return s.extend_group(raw,1,0,[s.activate(eg=a,frames=85)])
