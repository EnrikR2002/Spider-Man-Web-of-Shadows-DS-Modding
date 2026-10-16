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
# Broken docks have a solid maintenance deck below them: a missed swing loses
# height, never progress or a life. Door heights/IDs and earned flags stay stable.
LOWER={0:-20,1:-24,3:-24,7:-32,11:-20}
UPPER_PATROLS={0:48,6:112,7:48}
MATERIALS={
    'Pier_Map04':('Fconcrete01','Pbeam01','Pcrate01','corugated02','rcorugated01','wbrick01','skyline01','skyline02','skyline03'),
    'Pier_Map06':('Fconcrete02',), 'Pier_Map01':('gdoor01',),
    'Downtown_Map02':('Metal','Grate','WarningStrip'),
    'Downtown_Map01':('officeCLights','screens01'),
}
TITLE='Crane Row'
LINES={
    'AR_CraneQuay':'Cargo power is out. Engine House lies beyond the docks. X opens high hatches.',
    'AR_FreightExchange':'Save office: upper left. Main route: ground right.',
    'AR_HarbourOffice':'X at the sphere to save.',
    'AR_DryDock':'Cross the ship. Engine House: high right hatch.',
    'AR_EngineHouse':'X at the floor lever restores cargo power.',
    'power':'Power restored. Next: the Crown crew.',
    'locked':'Restore Engine House power first.',
    'upper_locked':'Defeat the Crown crew to open this shortcut.',
    'boss_locked':'Defeat the crew to open the final arm.',
    'AR_Counterweight':'Climb to the high right hatch, then cross Gantry to Crown.',
    'AR_GantrySpine':'Crown lies through the right door.',
    'AR_WinchCache':'Optional cache: smash the barrels above.',
    'AR_CraneCrown':'Clear the crew to open the high right hatch.',
    'crown_clear':'Crown clear. The high right hatch leads to the hoist.',
    'AR_LongArm':'Dodge the grabber. Strike the winch during recovery. Green pads are refuges.',
    'boss_clear':'Hoist down. Breakwater leads back to Quay and the Pier.',
    'victory_locked':'Defeat the hoist to open this exit.',
    'AR_Breakwater':'Quay: right door. Pier: Quay ground left.',
    'cache_done':'Cache recovered.',
    'AR_ContainerWarren':'Cross the Yard to Dry Dock.',
    'guide_crown':'Next: the Crown crew.',
    'guide_hoist':'Next: the hoist. Crown high right hatch.',
    'guide_done':'Return to the Pier through Breakwater and Quay.',
    'quay_power':'The Freight high right shortcut now leads to Engine House.',
    'freight_power':'Engine House shortcut: high right hatch.',
    'return_locked':'Return route. Approach the hoist through Crown.',
    'power_route_locked':'X at the floor lever opens this door.',
    'objective_power':'Cross Freight, Yard and Dry Dock to Engine House. Use X at its floor lever. The bolt on the map marks Engine House.',
    'objective_crown':'Take Engine House low right to Shaft. Climb to the high right hatch, cross Gantry and defeat the Crown crew.',
    'objective_hoist':'Crown high right leads to Long Arm. Dodge the grabber, then hit the exposed winch. Green pads are refuges.',
    'objective_done':'Breakwater leads to Quay. Its ground left door returns to the Pier. Office save and Winch Cache are optional.',
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
       (NAMES[5],2):('power','power_route_locked'),
       (NAMES[5],5):('upper','upper_locked'),(NAMES[9],2):('upper','upper_locked'),
       (NAMES[9],3):('crown','boss_locked'),(NAMES[10],2):('boss','victory_locked'),
       (NAMES[11],1):('boss','return_locked')}
DESTINATIONS=dict(zip(NAMES,('QUAY','FREIGHT','OFFICE','YARD','DOCK','ENGINE',
                          'SHAFT','GANTRY','CACHE','CROWN','ARM','BREAKWATER')))
DESTINATIONS['Pier_Save02']='PIER'

def sign_height(name,floor):
    # Ground labels clear the24-unit cargo beside Quay's right exit; high
    # hatches also clear the underside of the next stacked landing (Engine
    # House80 ->112). Keep X on a separate column, tops below the roof.
    return min(floor+(18 if floor else 27),BOUNDS[NAMES.index(name)][1]-8)

def door_action(name,group):
    if not PORTS[name][group-1][2]:return 'WALK IN'
    if (name,group)==(NAMES[1],3):return 'X SAVE RM'
    if (name,group)==(NAMES[5],4):return 'X OPTIONAL'
    if (name,group)==(NAMES[9],3):return 'X HOIST'
    if (name,group) in LOCKS and LOCKS[name,group][0] in ('power','upper'):return 'X SHORT'
    return 'X RETURN' if (name,group)==(NAMES[0],3) else 'X ENTER'

def looks():
    return dict(floor=rc.Look('HarborStone',(64,64)),
        wall=rc.Look('HarborHull',(64,32),(26,29,31)),
        metal=art.STEEL,
        beam=art.AMBER,
        crate=rc.Look('HarborWood',(32,32)),
        cargo=rc.Look('HarborRed',(48,48)),
        cargo2=rc.Look('HarborBlue',(48,48)),
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
    bottom=LOWER.get(i,0)
    if outdoor:
        panels=[rc.Panel(0,bottom,w,h,None)]
        scenery.append(rc.Quad(art.WATER,
            ((-12,-4,-120),(-12,-4,-26),(w+12,-4,-26),(w+12,-4,-120)),
            ((0,0),(0,3),((w+24)/64,3),((w+24)/64,0)),.85))
        # The three native pictures form one panorama. Repeating all three
        # every 240 units turned the bridge into a wallpaper strip.
        for n in range(3):
            scenery+=rc.backdrop(rc.Look('HarborSky'+str(n),(224,224)),
                                  -128+n*224,96+n*224,-28,196,tile=224,mirror=False,sky=max(100,h))
        # The native skyline's black bottom row is not a harbor horizon.
        # A far water face joins the skyline to the nearer horizontal water.
        scenery.append(rc.Quad(art.WATER,
            ((-128,-28,-169),(-128,-180,-169),(544,-180,-169),(544,-28,-169)),
            ((0,0),(0,5),(10.5,5),(10.5,0)),.80))
        # Dock-edge facing and warm marker bars keep landings legible.
        scenery+=rc.box(0,bottom-4,20,w,bottom,24,l['floor'],1,'front top')
        for x in range(24,w-10,64):
            scenery+=rc.box(x,0,-20,x+1,11,-18,l['metal'],.8,'front top')
            scenery.append(art.face(art.LAMP,x-2,10,x+4,13,-17.8))
    if i==0:
        # First thirty seconds: broken quay -> hanging freight -> rooftop.
        solids += [_box(0,bottom,64,0,art.DECK),_box(124,bottom,180,0,art.DECK),
                   _box(244,bottom,360,0,art.DECK),
                   _box(142,0,174,18,l['cargo2']),_box(260,0,294,18,l['cargo']),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((68,-10,100),(188,-10,220),(60,64,118),(78,16,118),(182,36,226),
                      (244,54,300),(20,20,56),(12,42,50),(0,64,42))]]
    elif i==1:
        # Broad fight deck below a complete container-roof express route.
        solids += [_box(0,bottom,58,0,art.DECK),_box(90,bottom,304,0,art.DECK),
                   _box(344,bottom,400,0,art.DECK),
                   _box(108,0,148,20,l['cargo']),_box(184,0,232,40,l['cargo2']),
                   _box(154,0,180,20,l['crate']),
                   _box(264,0,302,20,l['cargo']),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((60,-12,84),(310,-12,338),(0,64,44),(40,20,88),
                      (80,42,124),(128,64,188),(208,84,268),(288,104,348),
                      (346,112,400),(304,60,350))]]
    elif i==2:
        panels=[rc.Panel(8,12,38,32,art.HULL,.95)]
        scenery+=rc.box(8,0,-22,32,4,-13,l['metal'],.9,'front top')
    elif i==3:
        # Cargo canyon: tall real stacks, an underpass and a fast roof chain.
        solids += [_box(0,bottom,48,0,art.DECK),_box(80,bottom,300,0,art.DECK),
                   _box(338,bottom,380,0,art.DECK),
                   _box(94,0,140,38,l['cargo2']),_box(166,0,214,64,l['cargo']),
                   _box(240,0,286,42,l['cargo2']),
                   _box(64,0,90,18,l['crate']),_box(142,0,162,44,l['cargo2']),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((50,-12,74),(306,-12,334),
                      (218,84,250),(242,104,286),(298,82,338),
                      (310,22,346))]]
    elif i==4:
        # The ship is now playable architecture. A raised bow/stern and two
        # deck openings let a launch become a rooftop fight or a cargo-hold dive.
        solids += [_walkway(0,64,48,l['plate']),_walkway(352,64,400,l['plate']),
                   _box(76,30,136,68,art.SHIP),_box(168,54,252,68,art.SHIP),
                   _box(284,30,324,68,art.SHIP),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((38,18,72),(44,40,82),(94,18,134),(142,38,180),
                      (220,30,262),(264,48,300),(320,20,356),(324,42,366),
                      (144,90,194),(214,108,282),(294,88,342))]]
        for x in (90,300):scenery+=rc.box(x,0,-21,x+6,30,-15,l['beam'],.8,'front left right')
    elif i==5:
        solids += [_box(92,0,120,14,l['metal']),_box(174,0,204,18,l['metal'])]
        solids += [_walkway(a,y,b,l['plate']) for a,y,b in ((0,80,42),(0,112,40),(58,32,110),(112,56,162),(172,80,280),(208,112,252))]
        for x in (64,204):scenery+=rc.box(x,0,-23,x+30,44,-13,l['metal'],.85,'front top left right')
        panels=[rc.Panel(32,40,252,132,art.HULL,.8)]
    elif i==6:
        # Switchbacks around the live counterweight, rather than eleven
        # identical shelves. Central rungs are alternate swing recoveries.
        for a,y,b in ((32,18,88),(94,40,154),(26,62,88),(94,84,154),
                      (20,106,78),(92,128,154),(28,150,88),(94,172,154),
                      (134,192,176)):
            solids.append(_walkway(a,y,b,l['plate']))
        for x in (50,120):scenery+=rc.box(x-2,0,-22,x+2,220,-18,l['beam'],1,'front left right')
        for x,y in ((22,44),(130,108),(24,172)):
            scenery+=rc.box(x,y,-22,x+24,y+20,-12,l['cargo'],.9,'front top left right under')
    elif i==7:
        # A fractured crane bridge. Below each leap, a visible service deck
        # catches the player and short recovery steps lead back into the run.
        solids += [_box(0,bottom,54,0,art.DECK),_box(366,bottom,420,0,art.DECK),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((74,0,124),(154,16,208),(238,0,290),(318,20,360),
                      (44,-16,74),(126,-16,154),(208,-16,238),(290,-16,318),
                      (54,40,106),(142,58,194),(228,76,280),(316,58,370))]]
    elif i==8:
        solids += [_box(36,0,66,18,l['crate']),_walkway(62,38,96,l['plate']),
                   _walkway(94,40,150,l['plate']),_walkway(28,62,62,l['plate'])]
        panels=[rc.Panel(20,24,140,78,art.HULL,.9)]
    elif i==9:
        # The crown fight has a wide stage and a complete ring of launch
        # platforms above it. All required exits retain their original levels.
        solids += [_box(84,0,244,16,art.DECK),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((34,38,82),(104,58,160),(182,78,238),(264,96,336),
                      (48,100,102),(126,122,186),(216,140,270))]]
    elif i==10:
        # Flat readable fighting pocket at the motor; long approach retains
        # broad takeoffs and enough height for launches and evade cancels.
        solids += [_box(70,0,112,18,l['metal']),_box(124,0,164,18,l['metal']),_box(164,0,206,36,l['metal']),
                   _walkway(112,56,160,l['plate']),_walkway(214,56,264,l['plate'])]
        scenery+=rc.box(8,30,-23,410,34,-18,l['beam'],.9,'front top under')
        scenery+=rc.box(318,0,-22,386,24,-12,l['metal'],1,'front left right top')
        safe=rc.Look('Grate',(8,8),(9,30,16))
        for x in (328,392):scenery+=rc.box(x-3,.12,-10,x+3,.25,12,safe,1,'top')
    elif i==11:
        solids += [_box(0,bottom,60,0,art.DECK),_box(124,bottom,186,0,art.DECK),
                   _box(250,bottom,320,0,art.DECK),
                   *[_walkway(a,y,b,l['plate']) for a,y,b in
                     ((66,-10,104),(190,-10,232),(72,20,116),(144,40,192),(220,44,262))]]
    # All upper exits have a full landing. Side walls remain climbable.
    for group,(side,wall,floor,_) in enumerate(PORTS[name],1):
        if floor:
            a,b=(0,30) if side=='left' else (w-30,w)
            solids.append(_walkway(a,floor,b,l['plate']))
        scenery+=art.portal(l['door'],wall,floor,side=='left')
        if floor:
            # One small button glyph at the hatch replaces two floating
            # destination/instruction boards. The map owns route guidance.
            a=3 if side=='left' else w-7
            scenery.append(art.face(rc.Look('AccessMark',(4,4)),a,floor+17,a+4,floor+21,-7))
    # A narrow side channel keeps catwalk undersides from sealing the native
    # wall-crawl route to high doors. Arrivals land six units onto the ledge.
    solids=[replace(q,x0=12 if q.x0==0 and q.y0>0 else q.x0,
                      x1=w-12 if q.x1==w and q.y0>0 else q.x1) for q in solids]
    scenery+=art.setwork(i,w,h,solids)
    scenery+=art.ceiling(w,h,draw_shell=outdoor)
    return rc.Room(name,(0,bottom,w,h),theme,tuple(solids),tuple(panels),tuple(scenery),textures,palettes,
                   hidden_shell=('above',) if outdoor else (),margin=18,shades=mr.LIT)

SPECS={}
for i,name in enumerate(NAMES):
    w,h=BOUNDS[i]
    doors=tuple(mr.Door(side,x,y,spawn,str(spawn),inset=18) for side,x,y,spawn in PORTS[name])
    gangs=() if i in (1,2,4,8,9,10) else (mr.Gang(
        'Residential_Map09' if i==7 else 'Pier_Map04',0x0C if i==7 else 8,
        (w/2,(h+LOWER.get(i,0))/2),(w+24,h-LOWER.get(i,0)+48),
        'Gantry Hunters' if i==7 else 'Dock Patrol'),)
    if i in UPPER_PATROLS:
        split=UPPER_PATROLS[i];cy=min(32,(LOWER.get(i,0)+split)/2)
        lower=replace(gangs[0],xy=(w/2,cy),box=(w+24,round(2*(split+8-cy))))
        upper=mr.Gang('Sewer_Map03',0x0E,(w/2,(split+h)/2),(w+24,h-split+16),'Upper Patrol')
        gangs=(lower,upper)
    bottom=LOWER.get(i,0)
    SPECS[name]=mr.Authored(name,lambda blob,n=name:geometry(n,blob),tuple(MATERIALS),doors,
        (((20,bottom),(w-20,bottom),(w-20,h-8),(20,h-8)),),area=(10,bottom,w-10,h-8),
        # Encounters follow the vertical routes. The old12-unit Shaft limit
        # excluded every switchback shelf, leaving its upper192 units empty.
        spawn_top=12 if i==10 else h-24,
        gangs=gangs,save=(48,7) if i==2 else (),
        props=tuple(mr.Prop('proto01','Object (Smashable_MetalBarrel)',xy,'Cargo Barrel '+str(j))
                    for j,xy in enumerate({0:((272,56),),1:((156,2),(244,2),(226,86)),
                                          3:((150,2),(224,2),(262,106)),4:((110,70),(222,70)),
                                          7:((250,78),),9:((120,18),(208,18))}.get(i,()))),
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
    gang=mr.Gang('Sewer_Map03' if i==4 else 'Pier_Map04',0x0E if i==4 else 8,
                 (w*.52,h/2),(w+24,h+48),'Hold Crew' if i==4 else 'Dock Crew')
    raw,ag=s.append_batch(raw,1,[(mr._spawner(blob,gang,done),'EnemySpawner (Dock Crew)')],'Dock Crew')
    if i==9:
        # Bounded reinforcement, earned only from a real clear callback.
        # No timer can award victory or open the boss door.
        second=mr.Gang('Residential_Map09',0x0C,(w*.52,h/2),(w+24,h+48),'Crown Hunters')
        raw,second_ag=s.append_batch(raw,1,[(mr._spawner(blob,second,done),'EnemySpawner (Crown Hunters)')],'Crown Hunters')
        raw,go=s.append_groups(raw,1,[(EventGroup((s.set_var(0x12A,1),s.activate(ag=second_ag,frames=45))),
                                     'Crown_Reinforcements')])
        raw,guard=s.append_groups(raw,1,[(EventGroup((s.if_var(0x12A,'==',0,then=s.action(eg=go)),)),
                                        'Crown_First_Crew_Cleared')])
        parsed=RoomObjects.parse(raw);entities=mr.Entities.parse(parsed.records[1].sections[0])
        index=next(j for j,e in enumerate(entities.records) if len(e)==28 and e[12:16]==struct.pack('<I',4) and e[22]==8)
        first=bytearray(entities.records[index]);first[25]=guard
        raw=parsed.replace_section(1,0,entities.replace_record(index,first))
        raw=s.extend_group(raw,1,0,[s.set_var(0x12A,0)])
    # A saved crew clear remains earned, while revisits still have a patrol.
    # It has no clear callback and cannot change the objective/door flags.
    patrol=mr.Gang('Pier_Map04',8,(w/2,h/2),(w+24,h+48),'Returning Patrol')
    raw,patrol_ag=s.append_batch(raw,1,[(mr._spawner(blob,patrol),'EnemySpawner (Returning Patrol)')],'Returning Patrol')
    return s.extend_group(raw,1,0,[s.if_var(FLAGS[key],'==',0,then=s.action(ag=ag),otherwise=s.action(ag=patrol_ag))])

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
        spawn_template=spawn_template,exit_template=exit_template,say=lambda k:None if k==name else say(k),links=LINKS,flags=FLAGS,
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
    if NAMES.index(name) in UPPER_PATROLS:
        # Native ambush mode2 requests the central spawn sector (0x10 at
        # 0x02081D74), rather than ordinary offscreen-sector weighting. An
        # empty real completion callback makes this a bounded optional wave.
        raw,finished=s.append_groups(raw,1,[(EventGroup(()),'Upper_Patrol_Cleared')])
        parsed=RoomObjects.parse(raw);entities=mr.Entities.parse(parsed.records[1].sections[0])
        matches=[i for i,e in enumerate(entities.records) if len(e)==28 and struct.unpack_from('<I',e,12)[0]==4 and e[22]==0x0E]
        if len(matches)!=1:raise ValueError('Upper patrol spawner must be unique')
        index=matches[0];entity=bytearray(entities.records[index]);entity[23:26]=bytes((2,1,finished))
        raw=parsed.replace_section(1,0,entities.replace_record(index,entity))
    if name==NAMES[5]:raw=power_switch(raw,blob,say)
    if name==NAMES[6]:
        from tools import crane_boss
        raw=crane_boss.weight(raw,blob)
    if name==NAMES[8]:raw=cache(raw,blob,say)
    if name==NAMES[10]:
        from tools import crane_boss
        raw=crane_boss.stage(raw,blob,FLAGS,say)
    return raw
