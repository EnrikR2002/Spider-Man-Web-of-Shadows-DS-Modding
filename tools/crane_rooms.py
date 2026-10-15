"""Authored Crane Row geometry and native object scripts. No ROM assets included."""
from dataclasses import replace
import struct
from tools import midnight_rooms as mr, room_compiler as rc, room_script as s, crane_art as art
from tools.room_events import Command, EventGroup, Events
from tools.room_objects import RoomObjects

U=4096
NAMES=('AR_CraneQuay','AR_FreightExchange','AR_HarbourOffice','AR_ContainerWarren',
       'AR_DryDock','AR_EngineHouse','AR_Counterweight','AR_GantrySpine',
       'AR_WinchCache','AR_CraneCrown','AR_LongArm','AR_Breakwater')
IDS={n:96+i for i,n in enumerate(NAMES)}
VISITS=dict(zip(range(96,108),(*range(161,151,-1),149,148)))
FLAGS=dict(zip(('power','upper','boss','cache','freight','drydock','crown'),range(140,147)))
BOUNDS=((360,96),(400,176),(112,64),(380,160),(400,144),(280,144),
        (176,224),(420,112),(160,96),(336,176),(420,144),(320,96))
MATERIALS={
    'Pier_Map04':('Fconcrete01','Pbeam01','Pcrate01','corugated02','rcorugated01','wbrick01','skyline01','skyline02','skyline03'),
    'Pier_Map06':('Fconcrete02',), 'Pier_Map01':('gdoor01',),
    'Downtown_Map02':('Metal','Grate','WarningStrip'),
    'Downtown_Map01':('officeCLights','screens01'),
}
TITLE='Crane Row'
LINES={
    'AR_CraneQuay':'Crane Row. Cargo power is out. Find the engine house beyond the dry dock. X opens marked high hatches.',
    'AR_FreightExchange':'Freight Exchange. Save in the office above. The route to cargo power runs through the containers.',
    'AR_HarbourOffice':'Harbor Office. Save here before climbing the cranes.',
    'AR_DryDock':'Dry Dock. Follow the supports beneath the hull to reach the engine house.',
    'AR_EngineHouse':'Engine House. Press X at the cargo lever. Upper maintenance hatches loop back to the yard.',
    'power':'Cargo power restored. Climb to the yard maintenance hatch and press X.',
    'locked':'This maintenance route needs cargo power.',
    'upper_locked':'The upper return opens from Crane Crown.',
    'boss_locked':'Clear the crane platform crew before crossing the final arm.',
    'AR_Counterweight':'Counterweight Shaft. Climb the supports to reach the high gantry.',
    'AR_GantrySpine':'Gantry Spine. Cross the steelwork to Crane Crown. The harbor is far below.',
    'AR_WinchCache':'Winch Cache. A maintenance route hidden above the engine room.',
    'AR_CraneCrown':'Crane Crown. Defeat the platform crew to open the final arm and the shortcut down.',
    'crown_clear':'Crane platform secured. The descent and final arm are open.',
    'AR_LongArm':'The Long Arm. Evade the committed grabber, then hit the exposed winch. Green marks show refuge points.',
    'boss_clear':'The hoist is down. The waterfront return is open.',
    'victory_locked':'The hoist controls this service return.',
    'AR_Breakwater':'Breakwater. The cleared waterfront leads back to Quayside.',
    'cache_done':'Maintenance stash recovered. The upper walkway overlooks the harbor.',
}
# (side, wall x, floor y, spawn). Groups follow this order, preserving IDs.
PORTS={
    NAMES[0]:(('left',0,0,1),('right',360,0,2),('left',0,64,3)),
    NAMES[1]:(('left',0,0,1),('right',400,0,2),('left',0,64,3),('right',400,112,4)),
    NAMES[2]:(('right',112,0,1),),
    NAMES[3]:(('left',0,0,1),('right',380,0,2)),
    NAMES[4]:(('left',0,64,1),('right',400,64,2)),
    NAMES[5]:(('left',0,0,1),('right',280,0,2),('left',0,80,3),('right',280,80,4),('left',0,112,5)),
    NAMES[6]:(('left',0,0,1),('right',176,192,2)),
    NAMES[7]:(('left',0,0,1),('right',420,0,2)),
    NAMES[8]:(('left',0,0,1),),
    NAMES[9]:(('left',0,0,1),('right',336,0,2),('right',336,96,3)),
    NAMES[10]:(('left',0,0,1),('right',420,0,2)),
    NAMES[11]:(('left',0,0,1),('right',320,0,2)),
}
LINKS={}
def _join(a,ga,b,gb):
    LINKS[(NAMES[a],ga)]=(NAMES[b],gb)
    LINKS[(NAMES[b],gb)]=(NAMES[a],ga)
for connection in ((0,2,1,1),(1,2,3,1),(1,3,2,1),(3,2,4,1),(4,2,5,1),
                   (5,2,6,1),(5,3,1,4),(5,4,8,1),(5,5,9,2),(6,2,7,1),
                   (7,2,9,1),(9,3,10,1),(10,2,11,1),(11,2,0,3)):
    _join(*connection)
LINKS[(NAMES[0],1)]=('Pier_Save02',2)
LOCKS={(NAMES[1],4):('power','locked'),(NAMES[5],3):('power','locked'),
       (NAMES[5],2):('power','locked'),
       (NAMES[5],5):('upper','upper_locked'),(NAMES[9],2):('upper','upper_locked'),
       (NAMES[9],3):('crown','boss_locked'),(NAMES[10],2):('boss','victory_locked'),
       (NAMES[11],1):('boss','victory_locked')}

def looks():
    return dict(floor=rc.Look('Fconcrete02',(28,24),(30,29,28)),
        wall=rc.Look('wbrick01',(24,24),(25,27,31)),
        metal=art.STEEL,
        beam=art.AMBER,
        crate=rc.Look('Pcrate01',(18,18),(31,26,21)),
        cargo=rc.Look('rcorugated01',(32,16),(31,20,14)),
        cargo2=rc.Look('corugated02',(28,16),(17,26,31)),
        plate=art.DECK,
        stripe=rc.Look('WarningStrip',(8,8)),
        door=rc.Look('gdoor01',(16,18)), light=rc.Look('officeCLights',(12,12)))

def _box(x0,y0,x1,y1,look,depth=12):
    return rc.Solid(x0,y0,x1,y1,top=look,side=look,under=look,front=look,depth=depth)

def _walkway(x0,y,x1,look):return _box(x0,y-3,x1,y,look,8)

def geometry(name,blob):
    i=NAMES.index(name);w,h=BOUNDS[i];l=looks()
    textures,palettes=mr._borrowed(blob,MATERIALS)
    painted=art.materials()
    textures=(*textures,*(t for t,p in painted));palettes=(*palettes,*(p for t,p in painted))
    mark_pixels=[(28,28,24) if abs(x-y)<2 or abs(x+y-15)<2 else (3,9,14) for y in range(16) for x in range(16)]
    mark,mark_palette=rc.paint('AccessMark',16,16,mark_pixels)
    textures=(*textures,mark);palettes=(*palettes,mark_palette)
    theme={'top':l['floor'],'side':l['wall'],'under':l['floor'],'front':l['floor'],'back':l['wall']}
    if i in (6,7,9,10):
        theme.update(top=art.DECK,side=art.STEEL,under=art.STEEL,front=art.STEEL)
    if i in (5,8):theme.update(top=art.DECK,back=art.HULL,under=art.STEEL)
    if i==2:
        theme.update(back=rc.Look('HarborOffice',(16,32)),
                     top=rc.Look('Fconcrete02',(28,24),(31,27,22)))
    solids=[];scenery=[];panels=[]
    outdoor=i not in (2,5,8)
    if outdoor:
        panels=[rc.Panel(0,0,w,h,None)]
        scenery.append(rc.Quad(art.WATER,
            ((-12,-4,-120),(-12,-4,-26),(w+12,-4,-26),(w+12,-4,-120)),
            ((0,0),(0,3),((w+24)/64,3),((w+24)/64,0)),.85))
        # The three native pictures form one panorama. Repeating all three
        # every 240 units turned the bridge into a wallpaper strip.
        for n in range(3):
            scenery+=rc.backdrop(rc.Look('skyline0'+str(n+1),(224,144),(22,24,30)),
                                  -128+n*224,96+n*224,16,160,tile=224,mirror=False,sky=max(100,h))
        # The native skyline's black bottom row is not a harbor horizon.
        # A far water face joins the skyline to the nearer horizontal water.
        scenery.append(rc.Quad(art.WATER,
            ((-128,16,-169),(-128,-180,-169),(544,-180,-169),(544,16,-169)),
            ((0,0),(0,5),(10.5,5),(10.5,0)),.80))
        # Dock-edge facing and warm marker bars keep landings legible.
        scenery+=rc.box(0,-4,20,w,0,24,l['floor'],1,'front top')
        for x in range(24,w-10,64):
            scenery+=rc.box(x,0,-20,x+1,11,-18,l['metal'],.8,'front top')
            scenery.append(art.face(art.LAMP,x-2,10,x+4,13,-17.8))
    if i==0:
        solids += [_box(74,0,108,12,l['crate']),_box(172,0,212,18,l['cargo']),
                   _box(184,18,204,30,l['cargo2']),_walkway(238,32,294,l['plate']),
                   _walkway(22,18,60,l['plate']),_walkway(0,64,42,l['plate'])]
        scenery+=rc.box(290,0,-24,348,24,-12,l['cargo'],.85,'front left top')
    elif i==1:
        solids += [_box(76,0,116,14,l['cargo']),_box(168,0,212,18,l['cargo2']),
                   _box(264,0,300,12,l['crate']),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in ((0,64,44),(48,40,108),(126,64,200),
                        (216,88,276),(286,112,400),(314,40,362),(216,40,246))]]
        scenery+=rc.box(124,0,-24,162,36,-15,l['cargo2'],.8,'front left top')
    elif i==2:
        panels=[rc.Panel(8,12,38,32,art.HULL,.95)]
        scenery+=rc.box(8,0,-22,32,4,-13,l['metal'],.9,'front top')
    elif i==3:
        solids += [_box(a,0,a+36,y,l['cargo'] if n%2 else l['cargo2']) for n,(a,y) in enumerate(((64,16),(136,24),(214,18),(292,24)))]
        solids += [_walkway(a,y,b,l['plate']) for a,y,b in ((30,48,110),(140,64,220),(246,80,342),(0,112,76),(108,128,202))]
        for n,x in enumerate((10,110,228,334)):
            scenery+=rc.box(x,4,-24,x+32,52+n%2*16,-14,l['cargo2'],.8,'front left right top')
    elif i==4:
        # A supported hull behind the play plane, with an actual route below it.
        hull=art.HULL;scenery+=rc.box(76,30,-23,318,68,-8,hull,.85,'front left right top under')
        scenery.append(rc.Quad(l['metal'],((50,58,-8),(76,30,-8),(76,68,-8),(50,68,-8))))
        scenery.append(rc.Quad(l['metal'],((318,30,-8),(346,58,-8),(346,68,-8),(318,68,-8))))
        for x in (90,150,210,270):
            scenery+=rc.box(x,0,-21,x+6,30,-15,l['beam'],.8,'front left right')
        solids += [_walkway(0,64,48,l['plate']),_walkway(352,64,400,l['plate'])]
        for x,y in ((44,16),(78,32),(112,48),(254,16),(288,32),(322,48)):
            solids.append(_walkway(x,y,x+32,l['plate']))
    elif i==5:
        solids += [_box(92,0,120,14,l['metal']),_box(174,0,204,18,l['metal'])]
        solids += [_walkway(a,y,b,l['plate']) for a,y,b in ((0,80,42),(0,112,40),(58,32,110),(112,56,162),(172,80,280),(208,112,252))]
        for x in (64,204):scenery+=rc.box(x,0,-23,x+30,44,-13,l['metal'],.85,'front top left right')
        panels=[rc.Panel(32,40,252,132,art.HULL,.8)]
    elif i==6:
        for n in range(1,12):
            y=n*16;x=0 if n%2 else 96
            solids.append(_walkway(x,y,x+80,l['plate']))
        solids.append(_walkway(96,192,176,l['plate']))
        for x in (50,120):scenery+=rc.box(x-2,0,-22,x+2,220,-18,l['beam'],1,'front left right')
        for x,y in ((22,44),(130,108),(24,172)):
            scenery+=rc.box(x,y,-22,x+24,y+20,-12,l['cargo'],.9,'front top left right under')
    elif i==7:
        solids += [_box(x,0,x+24,8,l['metal']) for x in (78,170,262,354)]
        solids += [_walkway(a,40,a+52,l['plate']) for a in (36,140,244,348)]
        for x in range(12,420,48):
            scenery+=rc.box(x,0,-20,x+3,66,-16,l['beam'],.9,'front left right')
        scenery+=rc.box(4,62,-20,416,66,-16,l['beam'],1,'front top under')
    elif i==8:
        solids += [_box(54,0,86,16,l['crate']),_walkway(94,40,150,l['plate'])]
        panels=[rc.Panel(20,24,140,78,art.HULL,.9)]
    elif i==9:
        solids += [_box(80,0,108,12,l['metal']),_box(220,0,248,12,l['metal']),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in ((34,32,90),(110,48,172),(188,72,248),(264,96,336))]]
    elif i==10:
        # Flat readable fighting pocket at the motor; long approach retains
        # broad takeoffs and enough height for launches and evade cancels.
        solids += [_box(70,0,94,8,l['metal']),_box(156,0,180,8,l['metal'])]
        scenery+=rc.box(8,30,-23,410,34,-18,l['beam'],.9,'front top under')
        scenery+=rc.box(318,0,-22,386,24,-12,l['metal'],1,'front left right top')
        safe=rc.Look('Grate',(8,8),(9,30,16))
        for x in (328,392):scenery+=rc.box(x-3,.12,-10,x+3,.25,12,safe,1,'top')
    elif i==11:
        solids += [_box(90,0,122,10,l['floor']),_box(192,0,222,12,l['crate'])]
        scenery+=rc.box(130,4,-23,186,14,-14,l['cargo2'],.9,'front top left right')
    # All upper exits have a full landing. Side walls remain climbable.
    for side,wall,floor,_ in PORTS[name]:
        if floor:
            a,b=(0,30) if side=='left' else (w-30,w)
            solids.append(_walkway(a,floor,b,l['plate']))
        scenery.append(mr._shutter(l['door'],wall+(.1 if side=='left' else -.1),floor,side=='left'))
        for yy in (floor+1,floor+15):
            a,b=(1,14) if side=='left' else (w-14,w-1)
            scenery+=rc.box(a,yy,18,b,yy+.8,20,l['stripe'],1,'front')
        if floor:
            a=2 if side=='left' else w-8
            scenery.append(rc.Quad(rc.Look('AccessMark',(6,6)),((a,floor+24,18),(a,floor+18,18),(a+6,floor+18,18),(a+6,floor+24,18))))
    # A narrow side channel keeps catwalk undersides from sealing the native
    # wall-crawl route to high doors. Arrivals land six units onto the ledge.
    solids=[replace(q,x0=12 if q.x0==0 and q.y0>0 else q.x0,
                      x1=w-12 if q.x1==w and q.y0>0 else q.x1) for q in solids]
    scenery+=art.setwork(i,w,h,solids)
    return rc.Room(name,(0,0,w,h),theme,tuple(solids),tuple(panels),tuple(scenery),textures,palettes,
                   hidden_shell=('above',) if outdoor else (),margin=18,shades=mr.LIT)

SPECS={}
for i,name in enumerate(NAMES):
    w,h=BOUNDS[i]
    doors=tuple(mr.Door(side,x,y,spawn,str(spawn),inset=18) for side,x,y,spawn in PORTS[name])
    gangs=() if i in (1,2,4,5,8,9,10,11) else (mr.Gang('Pier_Map04',8,(w/2,12),(w-32,40),'Dock Patrol'),)
    SPECS[name]=mr.Authored(name,lambda blob,n=name:geometry(n,blob),tuple(MATERIALS),doors,
        (((20,0),(w-20,0),(w-20,h-8),(20,h-8)),),area=(10,0,w-10,h-8),
        gangs=gangs,save=(48,7) if i==2 else (),
        lines=(('first',LINES[name]),) if name in LINES else ())

def lock_exits(raw,name,say):
    parsed=RoomObjects.parse(raw);rec=parsed.records[0]
    events=Events.parse(rec.sections[1],rec.raw[3]);groups=list(events.groups)
    for (room,group),(flag,hint) in LOCKS.items():
        if room!=name:continue
        original=groups[group]
        raw,go=s.append_groups(raw,0,[(original,'Open_'+str(group))])
        no=0
        if say(hint):raw,no=s.append_groups(raw,0,[(EventGroup((say(hint),)),'Locked_'+str(group))])
        parsed=RoomObjects.parse(raw);rec=parsed.records[0];events=Events.parse(rec.sections[1],rec.raw[3])
        groups=list(events.groups)
        groups[group]=EventGroup((s.if_var(FLAGS[flag],'!=',0,then=s.action(eg=go),otherwise=s.action(eg=no)),))
        raw=parsed.replace_section(0,1,s._events_bytes(groups))
    return raw

def encounter(raw,name,blob,say):
    # Persistent callbacks use one native spawner; there is no timed victory.
    i=NAMES.index(name)
    key={1:'freight',4:'drydock',9:'crown'}.get(i)
    if not key:return raw
    clear=[s.set_var(FLAGS[key],1)]
    if i==9:clear += [s.set_var(FLAGS['upper'],1),say('crown_clear')]
    raw,done=s.append_groups(raw,1,[(EventGroup(tuple(c for c in clear if c)),'Crew_Cleared')])
    w,h=BOUNDS[i]
    gang=mr.Gang('Pier_Map04',8,(w*.52,h/2),(w-48,h+32),'Dock Crew')
    raw,ag=s.append_batch(raw,1,[(mr._spawner(blob,gang,done),'EnemySpawner (Dock Crew)')],'Dock Crew')
    return s.extend_group(raw,1,0,[s.if_var(FLAGS[key],'==',0,then=s.action(ag=ag))])

def power_switch(raw,blob,say):
    parsed=RoomObjects.parse(blob('Sewer_Map04_app.obj'))
    switch=mr._placed(mr._native_entity(parsed.to_bytes(),'Object (Switch)'),(142,1));switch[23]=0
    trigger=mr._placed(mr._native_entity(parsed.to_bytes(),'Trigger (Button Press)'),(146,5))
    raw,group=s.append_groups(raw,1,[(EventGroup((s.set_var(FLAGS['power'],1),say('power'),
        Command(0x22,struct.pack('<HH',mr.SWITCH_SOUND,0)))),'Cargo_Power')])
    trigger[27]=group
    raw,ag=s.append_batch(raw,1,[(bytes(switch),'Object (Cargo Lever)'),(bytes(trigger),'Trigger (Cargo Lever)')],'Cargo Lever')
    raw=s.extend_group(raw,1,group-1,[s.animate(ag,1,0x19),s.deactivate(entity=(ag,2))])
    raw,restore=s.append_groups(raw,1,[(EventGroup((s.animate(ag,1,0x64),s.deactivate(entity=(ag,2)))),'Power_Already_On')])
    return s.extend_group(raw,1,0,[s.activate(ag=ag),s.if_var(FLAGS['power'],'!=',0,then=s.action(eg=restore))])

def cache(raw,blob,say):
    raw,done=s.append_groups(raw,1,[(EventGroup((s.set_var(FLAGS['cache'],1),say('cache_done'))),'Cache_Recovered')])
    template=mr._native_entity(blob('proto01_app.obj'),'Object (Smashable_MetalBarrel)')
    props=[]
    for i,x in enumerate((108,122,136)):
        e=mr._placed(template,(x,42));e[23]=done if i==1 else 0
        props.append((bytes(e),'Object (Maintenance Stash '+str(i)+')'))
    raw,ag=s.append_batch(raw,1,props,'Maintenance Stash')
    return s.extend_group(raw,1,0,[s.if_var(FLAGS['cache'],'==',0,then=s.action(ag=ag))])

def stage(raw,name,blob,built,spawn_template,exit_template,say):
    raw=mr.stage(raw,name,blob,room_of=lambda n:IDS[n] if n in IDS else 38,visited=VISITS[IDS[name]],
        spawn_template=spawn_template,exit_template=exit_template,say=say,links=LINKS,flags=FLAGS,
        authored=SPECS[name],compiled_room=built)
    raw=lock_exits(raw,name,say)
    parsed=RoomObjects.parse(raw);entities=mr.Entities.parse(parsed.records[0].sections[0])
    for group,port in enumerate(PORTS[name],1):
        if not port[2]:continue
        # Explicit high-hatch input avoids accidental returns when descending
        # beside several doors on the same wall. Ground exits remain walk-in.
        index=next(i for i,e in enumerate(entities.records) if len(e)==28 and struct.unpack_from('<I',e,12)[0]==7 and e[27]==group+1)
        e=bytearray(entities.records[index]);e[26]=0
        section=entities.replace_record(index,e);raw=RoomObjects.parse(raw).replace_section(0,0,section)
        entities=mr.Entities.parse(section)
    raw=encounter(raw,name,blob,say)
    if name==NAMES[5]:raw=power_switch(raw,blob,say)
    if name==NAMES[6]:
        from tools import crane_boss
        raw=crane_boss.weight(raw,blob)
    if name==NAMES[8]:raw=cache(raw,blob,say)
    if name==NAMES[10]:
        from tools import crane_boss
        raw=crane_boss.stage(raw,blob,FLAGS,say)
    return raw
