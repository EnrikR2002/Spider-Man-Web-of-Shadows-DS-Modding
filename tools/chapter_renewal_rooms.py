"""Compact Midnight circuit and unobstructed, visible ports for both chapters.

Saved room numbers remain valid. Ten rooms form the playable Midnight circuit;
superseded rooms are one-way recovery spaces for old saves, off the new map.
"""
from dataclasses import replace
import math
from tools import midnight_chapter as ch, midnight_rooms as mr, midnight_rework_rooms as old
from tools import room_compiler as rc, crane_rooms as cr, crane_art as art

ACTIVE=(76,77,78,81,82,83,86,87,88,89)
BY_ID={r.index:r.name for r in ch.ROOMS}
SIZES={76:(224,88),77:(96,64),78:(336,112),81:(288,112),82:(96,64),
       83:(192,144),86:(288,128),87:(112,72),88:(224,104),89:(224,112)}
TITLES={76:'Storm Gate',77:'Signal House',78:'Midnight Terminal',81:'Floodworks',82:'Pump Refuge',
        83:'Turbine Rise',86:'Storm Observatory',87:'Relay Sanctuary',88:'Crown Return',89:'The Conductor'}
# (side, floor, incoming spawn). Every port has a reciprocal room/spawn pair.
PORTS={76:(('right',0,2),('left',0,3),('left',48,4)),77:(('right',0,1),),
       78:(('left',0,1),('right',0,2),('left',48,3)),
       81:(('left',0,2),('right',0,1),('left',48,3)),82:(('right',0,2),),
       83:(('left',0,2),('right',96,1)),86:(('left',0,2),('right',0,1)),
       87:(('left',0,2),('right',0,1)),88:(('left',0,2),('right',0,1)),
       89:(('left',0,2),('right',0,1))}
LINKS={}
for a,ga,b,gb in ((76,1,78,1),(78,2,81,1),(78,3,77,1),(81,3,82,1),
                 (81,2,83,1),(83,2,86,1),(86,2,87,1),(87,2,89,1),
                 (89,2,88,1),(88,2,76,3)):
    LINKS[BY_ID[a],ga]=(BY_ID[b],PORTS[b][gb-1][2])
    LINKS[BY_ID[b],gb]=(BY_ID[a],PORTS[a][ga-1][2])
LINKS[BY_ID[76],2]=(ch.ENTRANCE,2)
SAVE={77:(48,1),82:(48,1),87:(56,1),95:(48,1)}
STEPS={83:((48,16),(88,32),(128,48),(88,64),(48,80),(88,96),(132,96)),
       78:((30,16),(54,32)),81:((30,16),(54,32)),76:((30,16),(54,32))}

def doors(index):
    w,h=SIZES.get(index,(112,72))
    return tuple(mr.Door(s,0 if s=='left' else w,f,spawn,'Port'+str(g),inset=16)
                 for g,(s,f,spawn) in enumerate(PORTS.get(index,(('right',0,1),)),1))

def portal(door,steel,light,shutter):
    """Side shutter plus front-facing jamb/threshold readable at DS resolution."""
    x,y=door.wall,door.floor;d=1 if door.side=='left' else -1
    out=[replace(q,look=steel if q.look.texture==art.STEEL.texture else light if q.look.texture==art.LAMP.texture else q.look)
         for q in art.portal(shutter,x,y,door.side=='left')]
    a,b=sorted((x+d*.3,x+d*8))
    out.append(art.face(shutter,a,y+1,b,y+16,-23,.95))
    out.extend(rc.box(a,y-1,-24,b,y+1,24,steel,1,'front top left right'))
    out.append(art.face(light,a,y+17,b,y+19,-6))
    mark=rc.Look('MLAccess') if shutter.texture.startswith('ML') else rc.Look('AccessMark')
    out.append(art.face(mark,min(x+d*9,x+d*13),y+13,max(x+d*9,x+d*13),y+17,-5))
    return out

def geometry(index,blob=None):
    name=BY_ID[index];w,h=SIZES.get(index,(112,72));l=old.looks();solid=[];scene=[];panels=[]
    def block(a,y,b,top,look=None):solid.append(old.block(a,y,b,top,look or l['deck']))
    def box(a,y,z,b,top,zz,look,faces='front top left right under'):
        scene.extend(rc.box(a,y,z,b,top,zz,look,.92,faces))
    def face(look,a,y,b,top,z=-26,shade=1):scene.append(art.face(look,a,y,b,top,z,shade))
    def bar(a,y,b,top,z=-28,width=2,look=None):scene.append(art.bar(a,y,b,top,z,width,look or l['steel']))
    # Window openings expose one continuous storm panorama, surrounded by solid
    # architectural back wall. No corridor is an empty sky box.
    for panel in range(3):face(rc.Look('MLStorm'+str(panel)),w/2-240+160*panel,-24,w/2-80+160*panel,168,-170,.9)
    panels.append(rc.Panel(0,0,w,h,l['stone'],.7))
    if index in (76,78,86,88,89):
        for x in range(24,w-28,64):panels.append(rc.Panel(x,24,min(w-16,x+48),h-18,None))
    if index not in ACTIVE:
        panels.append(rc.Panel(16,24,w-16,52,l['glass'],.85))
        face(l['cyan'],20,54,w-20,56)
    elif index in (77,82,87):
        panels.append(rc.Panel(16,20,w-16,48,l['glass'],.9))
        face(l['amber'],16,49,w-16,52)
        box(16,0,-23,32,8,-16,l['steel'])
        if index==82:
            for x in (18,w-18):box(x-2,0,-25,x+2,42,-19,l['cyan'])
        if index==87:
            for x in (20,w-20):bar(x,50,w/2,h-8,-24,2,l['amber'])
    elif index==76:
        # Tall entrance colonnade, vaulted canopy and a dedicated return balcony.
        for x in (46,112,178):
            box(x-3,0,-30,x+3,h-5,-25,l['stone'])
            bar(x-24,h-22,x,h-4,width=3);bar(x,h-4,x+24,h-22,width=3)
        block(78,0,106,7,l['stone']);block(142,0,174,12,l['steel'])
    elif index==78:
        # A full train, playable carriage roof and vaulted platform canopy.
        for x in (80,152,224):
            box(x,3,-23,x+66,25,-12,l['steel']);face(l['amber'],x+2,6,x+64,8,-11)
            for xx in range(x+7,x+61,17):face(l['glass'],xx,13,xx+11,23,-11)
            block(x+4,0,x+62,12)
        for x in range(36,w-16,48):
            bar(x,78,x+24,100,width=2);bar(x+24,100,x+48,78,width=2)
        face(l['rail'],12,-.1,w-12,.25,23)
    elif index==81:
        # Flood channel behind a continuous safe deck; three monumental pumps.
        face(l['water'],12,0,w-12,20,-24)
        for x in (66,144,222):
            box(x-15,0,-42,x+15,64,-27,l['steel']);face(l['cyan'],x-11,46,x+11,50)
            bar(x-22,74,x+22,74,width=5);block(x-18,0,x+18,12)
        bar(20,92,w-20,92,width=5)
    elif index==83:
        # Vertical turbine chamber. Six generous steps, one continuous wall.
        cx=w/2;cy=72
        for n in range(16):
            a=2*math.pi*n/16;b=2*math.pi*(n+1)/16
            x,y=cx+46*math.cos(a),cy+46*math.sin(a)
            xx,yy=cx+46*math.cos(b),cy+46*math.sin(b)
            bar(x,y,xx,yy,-36,3);bar(cx,cy,x,y,-37,1.6,l['cyan'])
        for x in (24,w-24):box(x-2,0,-30,x+2,h,-25,l['steel'])
    elif index==86:
        # A low, broad observatory with layered glass lens and orbiting ribs.
        for radius in (28,42,58):
            for n in range(16):
                a=math.pi*n/16;b=math.pi*(n+1)/16
                bar(w/2+radius*math.cos(a),40+radius*math.sin(a),w/2+radius*math.cos(b),40+radius*math.sin(b),-35,2,l['cyan'])
        block(66,0,94,12,l['stone']);block(122,28,162,31);block(194,0,222,12,l['stone'])
        face(l['glass'],w/2-18,42,w/2+18,78,-34,.9)
    elif index==88:
        # Reward return: a fast descending signal gantry, no extra ascent room.
        for x,y in ((58,18),(104,34),(150,18)):block(x-16,y-3,x+16,y)
        for x in (48,112,176):box(x-2,0,-30,x+2,80,-25,l['steel'])
        for x in range(20,w-20,24):face(l['cyan'],x,72,x+7,77)
    elif index==89:
        # Existing HP-driven storm machinery and three lanes retain coordinates.
        for radius,look in ((44,l['steel']),(35,l['amber']),(26,l['cyan'])):
            for n in range(16):
                a=2*math.pi*n/16;b=2*math.pi*(n+1)/16
                bar(w/2+radius*math.cos(a),54+radius*math.sin(a),w/2+radius*math.cos(b),54+radius*math.sin(b),-36,2,look)
        for x in (70,154):face(l['cyan'],x-8,.15,x+8,.4,23)
    for x,y in STEPS.get(index,()):
        radius=10 if index in (76,78,81) else 18
        block(max(12,x-radius),y-3,min(w-12,x+radius),y)
    for d in doors(index):
        if d.floor:
            block(0 if d.side=='left' else w-34,d.floor-3,34 if d.side=='left' else w,d.floor)
        scene.extend(portal(d,l['steel'],l['cyan'],rc.Look('MLRail',(16,18))))
    # Collision and visible ceiling use the same bound. Exposed underside/ribs
    # remain readable even at the top of a jump; no hidden_shell='above'.
    for x in range(16,w-12,40):box(x,h-5,-26,min(w,x+3),h,25,l['steel'])
    # The compiler's native back wall sits at z=-25. Drawing it in front of
    # the authored pumps/turbine (z=-42..-27) hides those landmarks entirely.
    # Reproduce the same wall/window rectangles at real depth behind them.
    xs=sorted({0,w,*(v for p in panels for v in (p.x0,p.x1))})
    ys=sorted({0,h,*(v for p in panels for v in (p.y0,p.y1))})
    for a,b in zip(xs,xs[1:]):
        for y,top in zip(ys,ys[1:]):
            visible=next((p for p in reversed(panels) if p.x0<=(a+b)/2<=p.x1 and p.y0<=(y+top)/2<=p.y1),None)
            if visible is None or visible.look is None:continue
            su,sv=visible.look.size
            scene.append(rc.Quad(visible.look,((a,top,-64),(a,y,-64),(b,y,-64),(b,top,-64)),
                ((a/su,-top/sv),(a/su,-y/sv),(b/su,-y/sv),(b/su,-top/sv)),visible.shade))
    theme=dict(top=l['stone'],side=l['steel'],under=l['steel'],front=l['stone'],back=l['dark'])
    mats=old.materials()
    return rc.Room(name,(0,0,w,h),theme,tuple(solid),(rc.Panel(0,0,w,h,None),),tuple(scene),
                   tuple(t for t,p in mats),tuple(p for t,p in mats),margin=80,shades=mr.LIT)

def spec(index):
    name=BY_ID[index];w,h=SIZES.get(index,(112,72))
    gangs=() if index not in ACTIVE or index in (*SAVE,89) else (
        mr.Gang('Pier_Map04',8,(w/2,h/2),(w-32,h),'Midnight crew'),)
    return mr.Authored(name,lambda blob:geometry(index,blob),(),doors(index),
        (((16,0),(w-16,0),(w-16,h),(16,h)),),spawn_top=h-22,gangs=gangs,save=SAVE.get(index,()))

SPECS={BY_ID[i]:spec(i) for i in range(76,96)}
for index in range(76,96):
    if index not in ACTIVE:LINKS[BY_ID[index],1]=(BY_ID[86],2)

def crane_geometry(name,blob):
    """Keep authored landmarks; clear every arrival/exit aisle and wall channel."""
    plan=cr.geometry(name,blob);width=plan.bounds[2];solids=list(plan.solids)
    # Earlier free-standing containers touched the ground exit approach. Upper
    # landing insets also left a12-unit gap at the actual shutter threshold.
    for door in cr.SPECS[name].doors:
        a,b=(0,24) if door.side=='left' else (width-24,width)
        new=[]
        for q in solids:
            if q.x1<=a or q.x0>=b or q.y1<=door.floor or q.y0>=door.floor+22:new.append(q);continue
            if q.x0<a:new.append(replace(q,x1=a))
            if q.x1>b:new.append(replace(q,x0=b))
            if q.y0<door.floor:new.append(replace(q,x0=max(a,q.x0),x1=min(b,q.x1),y1=door.floor))
        solids=new
        # Retain the12-unit wall-crawl channel beside upper native landings.
        # Filling it seals the climb under the platform; arrivals already
        # stand18 units inward on its actual solid deck.
    scene=list(plan.scenery)
    for d in cr.SPECS[name].doors:scene.extend(portal(d,art.STEEL,art.LAMP,cr.looks()['door']))
    return replace(plan,solids=tuple(solids),scenery=tuple(scene),hidden_shell=())
