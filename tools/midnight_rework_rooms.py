"""Midnight Line: original storm terminal geometry, preserving saved room IDs.

The old internal names are a save/lookup contract, not visual source assets.
Every plan below compiles its own model, collision, textures, camera and anchors.
"""
from functools import lru_cache
import math
import struct
from pathlib import Path
from tools import midnight_rooms as mr, midnight_chapter as ch, room_compiler as rc, crane_art as ca

NAMES=tuple(r.name for r in ch.ROOMS[:15])
TITLES=('Storm Gate','Signal House','Midnight Terminal','Switch Tower','Skyrail Viaduct',
        'Floodworks','Pump Refuge','Turbine Rise','Lightning Bridge','Capacitor Hall',
        'Storm Observatory','Relay Sanctuary','Crown Approach','The Conductor','Train Sheds')
SIZES=((232,96),(96,64),(352,112),(176,128),(384,128),(280,112),(96,64),
       (192,160),(376,112),(288,144),(256,144),(112,72),(208,128),(224,112),(320,112))
# Group order and incoming spawn IDs retain the original chapter graph.
PORTS={
 NAMES[0]:(('right',0,2),('left',0,3)),
 NAMES[1]:(('right',0,1),('left',0,2)),
 NAMES[2]:(('left',0,1),('right',0,2)),
 NAMES[3]:(('right',0,1),('left',0,2),('right',64,3)),
 NAMES[4]:(('left',0,1),('right',0,2),('left',64,3)),
 NAMES[5]:(('left',0,2),('right',0,1)),
 NAMES[6]:(('left',0,1),('right',0,2)),
 NAMES[7]:(('left',0,2),('right',112,1)),
 NAMES[8]:(('right',0,1),('left',0,2)),
 NAMES[9]:(('left',0,2),('right',0,1)),
 NAMES[10]:(('left',0,2),('right',64,1)),
 NAMES[11]:(('right',0,1),('left',0,2)),
 NAMES[12]:(('left',0,2),('left',64,1)),
 NAMES[13]:(('left',0,2),('right',0,1)),
 NAMES[14]:(('right',0,1),('left',0,2)),
}
SAVE={NAMES[1]:(48,1),NAMES[6]:(48,1),NAMES[11]:(56,1)}
TURBINE_STEPS=((50,16),(90,32),(130,48),(90,64),(50,80),(90,96),(130,112))
CROWN_STEPS=((146,16),(110,32),(74,48),(30,64))
MATERIAL_NAMES=('MLStone','MLSteel','MLGlass','MLDeck','MLAmber','MLCyan','MLWater','MLRail','MLDark','MLAccess')

def manual(name,group):
    side,floor,_=PORTS[name][group-1]
    return bool(floor) or sum(s==side for s,f,spawn in PORTS[name])>1

@lru_cache(maxsize=1)
def materials():
    out=[]
    def paint(name,w,h,fn):out.append(rc.paint(name,w,h,[fn(x,y) for y in range(h) for x in range(w)]))
    def grain(x,y):return ((x*91+y*53)^(x*y*17))%3
    paint('MLStone',64,64,lambda x,y:(11,15,19) if y%32==0 or (x+(32 if y//32%2 else 0))%64==0 else (17+grain(x,y),20+grain(x,y),23+grain(x,y)))
    paint('MLSteel',64,64,lambda x,y:(21,25,27) if x in (1,62) or y in (1,62) else (7,12,17) if x in (0,63) or y in (0,63) else (12+grain(x,y),17+grain(x,y),22+grain(x,y)))
    paint('MLGlass',32,64,lambda x,y:(17,25,30) if x%16 in (0,1) or y%32 in (0,1) else (7+x//12,15+x//10,22+x//8))
    paint('MLDeck',64,32,lambda x,y:(18,24,27) if y in (0,1) else (9,14,20) if y%8==0 else (13,18,24))
    paint('MLAmber',16,16,lambda x,y:(31,23,9) if x+y in range(8,16) else (19,12,6))
    paint('MLCyan',16,16,lambda x,y:(13,31,31) if 4<x<11 else (4,17,23))
    paint('MLWater',64,32,lambda x,y:(8,21,26) if (x+3*y)%37<2 else (3,9+y//12,17+y//10))
    paint('MLRail',32,32,lambda x,y:(23,27,29) if x in (8,9,23,24) else (8,12,17) if y%8<2 else (12,16,21))
    paint('MLDark',8,8,lambda x,y:(4,8,14))
    paint('MLAccess',8,8,lambda x,y:(30,29,21) if x==y or x+y==7 else (3,8,14))
    raw=(Path(__file__).resolve().parents[1]/'reference/art/midnight-storm-v1.rgb555').read_bytes()
    if len(raw)!=768*256*2:raise ValueError('Midnight panorama dimensions changed')
    values=struct.unpack('<196608H',raw)
    for i in range(3):
        # One room texture allocation must fit the native128KiB bank.
        # Three256x256 planes exceeded it and rendered the whole room white.
        pixels=[tuple(((values[2*y*768+i*256+x]>>(5*n)&31)+(values[(2*y+1)*768+i*256+x]>>(5*n)&31))//2
                      for n in range(3)) for y in range(128) for x in range(256)]
        out.append(rc.paint('MLStorm'+str(i),256,128,pixels,colours=256))
    return tuple(out)

def looks():return {key:rc.Look(name,size) for key,name,size in (
    ('stone','MLStone',(64,64)),('steel','MLSteel',(48,48)),('glass','MLGlass',(24,48)),
    ('deck','MLDeck',(48,24)),('amber','MLAmber',(8,8)),('cyan','MLCyan',(4,4)),
    ('water','MLWater',(120,40)),('rail','MLRail',(28,28)),('dark','MLDark',(32,32)))}

def block(x0,y0,x1,y1,look,depth=10):
    return rc.Solid(x0,y0,x1,y1,top=look,side=look,under=look,front=look,depth=depth)

def geometry(name,blob=None):
    i=NAMES.index(name);w,h=SIZES[i];l=looks();solids=[];scenery=[]
    def box(x0,y0,z0,x1,y1,z1,look,faces='front top left right under'):
        scenery.extend(rc.box(x0,y0,z0,x1,y1,z1,look,.9,faces))
    def face(look,x0,y0,x1,y1,z,shade=1):scenery.append(ca.face(look,x0,y0,x1,y1,z,shade))
    def bar(x0,y0,x1,y1,z,width=1,look=None):scenery.append(ca.bar(x0,y0,x1,y1,z,width,look or l['steel']))
    # Real depth: a single contiguous triptych, never a mirrored repeating skyline.
    for panel in range(3):
        xx=w/2-240+160*panel
        face(rc.Look('MLStorm'+str(panel)),xx,-32,xx+160,160,-170,.9)
    face(l['dark'],w/2-240,160,w/2+240,250,-170,.8)
    face(l['water'],w/2-240,-90,w/2+240,-32,-169,.5)
    # Side-door alcoves, supports, and high-door landings belong to collision.
    for side in ('left','right'):
        floors=sorted({f for s,f,_ in PORTS[name] if s==side})
        x0,x1=(0,12) if side=='left' else (w-12,w)
        y=0
        for floor in floors:
            if floor>y:solids.append(block(x0,y,x1,floor,l['stone'],25))
            y=floor+18
            if floor:
                solids.append(block(0 if side=='left' else w-34,floor-3,34 if side=='left' else w,floor,l['deck']))
        if y<h:solids.append(block(x0,y,x1,h,l['stone'],25))
        if not floors:solids.append(block(x0,0,x1,h,l['stone'],25))
        for floor in floors:
            face(l['cyan'],x0+.5,floor+15,x1-.5,floor+16,-10)
        for g,(s,f,spawn) in enumerate(PORTS[name],1):
            if s==side and manual(name,g):
                x=16 if side=='left' else w-20
                face(rc.Look('MLAccess'),x,f+13,x+4,f+17,-5)
    # Climbable, continuous structural walls. Ascending side platforms also
    # make the high doors reachable by jump/swing without purchase gates.
    high=max((f for _,f,_ in PORTS[name]),default=0)
    if high and i not in (7,12):
        side=next(s for s,f,_ in PORTS[name] if f==high)
        for n,y in enumerate(range(16,high,16)):
            x=18+(n%2)*24 if side=='left' else w-42-(n%2)*24
            solids.append(block(x,y-3,x+24,y,l['deck']))
    # Architectural silhouettes differ by place, with broad uncluttered ground.
    if i==0: # monumental terminal approach, double-depth arches
        for x in (44,116,188):
            box(x-3,0,-34,x+3,70,-26,l['stone'])
            bar(x-22,52,x,72,-27,3);bar(x,72,x+22,52,-27,3)
            face(l['glass'],x-20,20,x+20,50,-35,.7)
        solids.extend((block(54,0,90,8,l['stone']),block(142,0,172,12,l['steel'])))
    elif i in (1,6,11): # distinct small inhabited refuges
        face(l['glass'],20,18,w-20,48,-27)
        box(w-25,0,-18,w-17,12,-12,l['steel'])
        face(l['amber'],24,42,w-24,44,-24)
        if i==6:
            for x in (24,w-24):box(x-2,0,-20,x+2,38,-16,l['cyan'])
        if i==11:
            for x in range(20,w-10,18):bar(x,52,w/2,68,-26,1.2)
    elif i in (2,14): # glass train hall / maintenance sheds: authored rolling stock
        for x in range(32,w-15,48):
            box(x-1,0,-32,x+1,80,-26,l['steel'])
            bar(x,70,x+24,88,-28,1.4);bar(x+24,88,x+48,70,-28,1.4)
        for x in (60,184) if i==2 else (48,192):
            box(x,4,-22,x+86,23,-12,l['steel'])
            face(l['amber'],x+3,6,x+83,7,-11)
            for xx in range(x+8,x+79,16):face(l['glass'],xx,12,xx+11,21,-11)
            solids.append(block(x+8,0,x+78,10,l['deck']))
        face(l['rail'],12,-.1,w-12,.3,22)
    elif i in (3,7): # mechanical tower: exposed turbine in a structural frame
        cx=w/2;cy=72 if i==3 else 88;radius=35 if i==3 else 54
        for n in range(16):
            a=2*math.pi*n/16;b=2*math.pi*(n+1)/16
            x,y=cx+radius*math.cos(a),cy+radius*math.sin(a)
            xx,yy=cx+radius*math.cos(b),cy+radius*math.sin(b)
            bar(x,y,xx,yy,-38,3,l['steel']);bar(cx,cy,x,y,-39,1.6,l['cyan'])
        if i==7:
            for x,y in TURBINE_STEPS:solids.append(block(x-16,y-3,x+16,y,l['deck']))
        else:
            for y in range(20,h-15,20):
                x=54 if y//20%2 else w-100
                solids.append(block(x,y-3,x+44,y,l['deck']))
        for x in (24,w-24):box(x-2,0,-31,x+2,h,-25,l['steel'])
    elif i in (4,8): # broken elevated span over storm water, solid rescue deck
        for x,y,length in ((44,18,54),(126,34,48),(208,18,54),(290,42,44)):
            solids.append(block(x,y-4,x+length,y,l['deck']))
            bar(x,y-3,x+length/2,y-23,-18,1.5);bar(x+length/2,y-23,x+length,y-3,-18,1.5)
        for x in (52,w-52):
            box(x-2,0,-32,x+2,h,-26,l['stone'])
            bar(x,104,w/2,52,-30,1,l['cyan'])
        face(l['water'],12,0,w-12,6,-28)
    elif i==5: # flooded waterworks; huge pipes and safe pump housings
        for x in (56,140,224):
            box(x-12,0,-40,x+12,62,-26,l['steel'])
            face(l['cyan'],x-8,44,x+8,48,-25)
            bar(x-20,70,x+20,70,-26,5)
            solids.append(block(x-16,0,x+16,12,l['deck']))
        face(l['water'],12,0,w-12,14,-28)
    elif i==9: # capacitor vault; diagonal switchback through amber insulators
        for n,x in enumerate((56,112,176,232)):
            box(x-10,0,-42,x+10,94,-28,l['steel'])
            for y in range(20,90,14):box(x-13,y,-30,x+13,y+3,-24,l['amber'])
            solids.append(block(x-16,16+n%2*16,x+16,19+n%2*16,l['deck']))
        bar(28,110,w-28,110,-26,2,l['cyan'])
    elif i==10: # open observatory, storm lens and concentric orbital ribs
        for radius in (24,38,52):
            for n in range(12):
                a=math.pi*n/12;b=math.pi*(n+1)/12
                bar(w/2+radius*math.cos(a),36+radius*math.sin(a),w/2+radius*math.cos(b),36+radius*math.sin(b),-35,1.5,l['cyan'])
        solids.extend((block(62,0,96,16,l['stone']),block(108,32,148,35,l['deck']),block(164,48,198,51,l['deck'])))
    elif i==12: # victory return: stepped signal crown, not a Hive ascent
        for x,y in CROWN_STEPS:solids.append(block(x-16,y-3,x+16,y,l['deck']))
        for x in (50,104,158):box(x-2,0,-32,x+2,110,-25,l['steel'])
    elif i==13: # grounded boss arena: long clear floor, huge radial storm engine
        cx=w/2;cy=55
        for radius,look in ((42,l['steel']),(34,l['amber']),(26,l['cyan'])):
            for n in range(16):
                a=2*math.pi*n/16;b=2*math.pi*(n+1)/16
                bar(cx+radius*math.cos(a),cy+radius*math.sin(a),cx+radius*math.cos(b),cy+radius*math.sin(b),-38,2,look)
        for x in (36,w-36):box(x-4,0,-32,x+4,90,-24,l['stone'])
        # Visible green refuges separate three electrical attack lanes.
        for x in (70,154):face(l['cyan'],x-8,.3,x+8,1,23)
    theme=dict(top=l['stone'],side=l['steel'],under=l['steel'],front=l['stone'],back=l['dark'])
    return rc.Room(name,(0,0,w,h),theme,tuple(solids),(rc.Panel(0,0,w,h+60,None),),tuple(scenery),
        tuple(t for t,p in materials()),tuple(p for t,p in materials()),hidden_shell=('above',),shades=mr.LIT,back_shade=.8)

def spec(name):
    i=NAMES.index(name);w,h=SIZES[i]
    doors=tuple(mr.Door(s,0 if s=='left' else w,f,spawn,'Port'+str(g)) for g,(s,f,spawn) in enumerate(PORTS[name],1))
    gangs=() if name in SAVE or i==13 else (mr.Gang('Pier_Map04',8,(w/2,18),(w-32,48),'Midnight Patrol'),)
    # Elevated stages carry a second local encounter rather than empty scenery.
    if i in (3,7,10):gangs+= (mr.Gang('Sewer_Map03',14,(w/2,high:=64),(w-32,52),'Upper Patrol'),)
    return mr.Authored(name,lambda blob:geometry(name,blob),(),doors,(((20,0),(w-20,0),(w-20,h),(20,h)),),
                       spawn_top=116 if i in (3,7,10) else 12,gangs=gangs,save=SAVE.get(name,()))

SPECS={n:spec(n) for n in NAMES}
