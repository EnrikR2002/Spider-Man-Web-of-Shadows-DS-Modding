"""Crane Row's deterministic, original pixel materials and non-colliding setwork.

All decoration stays behind the actor plane or on an existing solid face.
Collision, anchors, cameras, entrances and encounter scripts remain owned by
crane_rooms. Native skyline pictures are borrowed only from the visited Pier.
"""
from functools import lru_cache
import math
import struct
from pathlib import Path
from tools import room_compiler as rc

STEEL=rc.Look('HarborSteel',(48,48))
DECK=rc.Look('HarborDeck',(48,48))
HULL=rc.Look('HarborHull',(64,32))
SHIP=rc.Look('HarborShip',(48,32))
EDGE=rc.Look('HarborEdge',(8,2))
LAMP=rc.Look('HarborLamp',(4,4))
WATER=rc.Look('HarborWater',(128,48))
AMBER=rc.Look('HarborGirder',(24,12))
DARK=rc.Look('HarborSteel',(48,48),(12,17,24))

# Five-pixel lettering is drawn once into tiny sign textures. No font/runtime
# dependency, random seeds, image files or extracted asset in the repository.
FONT={
 'A':('01110','10001','10001','11111','10001','10001','10001'),
 'B':('11110','10001','10001','11110','10001','10001','11110'),
 'C':('01111','10000','10000','10000','10000','10000','01111'),
 'D':('11110','10001','10001','10001','10001','10001','11110'),
 'E':('11111','10000','10000','11110','10000','10000','11111'),
 'F':('11111','10000','10000','11110','10000','10000','10000'),
 'G':('01111','10000','10000','10111','10001','10001','01111'),
 'H':('10001','10001','10001','11111','10001','10001','10001'),
 'I':('11111','00100','00100','00100','00100','00100','11111'),
 'J':('00111','00010','00010','00010','10010','10010','01100'),
 'K':('10001','10010','10100','11000','10100','10010','10001'),
 'L':('10000','10000','10000','10000','10000','10000','11111'),
 'M':('10001','11011','10101','10101','10001','10001','10001'),
 'N':('10001','11001','11001','10101','10011','10011','10001'),
 'O':('01110','10001','10001','10001','10001','10001','01110'),
 'P':('11110','10001','10001','11110','10000','10000','10000'),
 'R':('11110','10001','10001','11110','10100','10010','10001'),
 'Q':('01110','10001','10001','10001','10101','10010','01101'),
 'S':('01111','10000','10000','01110','00001','00001','11110'),
 'T':('11111','00100','00100','00100','00100','00100','00100'),
 'U':('10001','10001','10001','10001','10001','10001','01110'),
 'V':('10001','10001','10001','10001','10001','01010','00100'),
 'W':('10001','10001','10001','10101','10101','11011','10001'),
 'X':('10001','10001','01010','00100','01010','10001','10001'),
 'Y':('10001','10001','01010','00100','00100','00100','00100'),
 'Z':('11111','00001','00010','00100','01000','10000','11111'),
 '>':('10000','01000','00100','00010','00100','01000','10000'),
 ':':('00000','00100','00100','00000','00100','00100','00000'),
 '/':('00001','00010','00010','00100','01000','01000','10000'),
 '-':('00000','00000','00000','11111','00000','00000','00000'),
 '=':('00000','00000','11111','00000','11111','00000','00000'),
 '0':('01110','10001','10011','10101','11001','10001','01110'),
 '1':('00100','01100','00100','00100','00100','00100','01110'),
 '2':('01110','10001','00001','00110','01000','10000','11111'),
 '3':('11110','00001','00001','01110','00001','00001','11110'),
 '4':('00010','00110','01010','10010','11111','00010','00010'),
 '5':('11111','10000','10000','11110','00001','00001','11110'),
 '6':('01110','10000','10000','11110','10001','10001','01110'),
 '7':('11111','00001','00010','00100','01000','01000','01000'),
 '8':('01110','10001','10001','01110','10001','10001','01110'),
 '9':('01110','10001','10001','01111','00001','00001','01110'),
 ' ':('00000',)*7,
}
SIGNS=('CRANE ROW','OFFICE','POWER','CROWN','DOCK 04','GANTRY','CACHE','HOIST',
       'PIER','QUAY','FREIGHT','DOCK','ENGINE','SHAFT','ARM','BREAKWATER','YARD',
       'X ENTER','X SHORT','X RETURN','WALK IN','X SAVE RM','X OPTIONAL','X HOIST')

def _sign(text):
    w,h=64,16;bg=(3,8,12);pixels=[bg]*(w*h)
    for y in (0,15):
        for x in range(w):pixels[y*w+x]=(18,24,24)
    for y in range(1,15):pixels[y*w]=pixels[y*w+63]=(18,24,24)
    x0=(w-(len(text)*6-1))//2
    for n,char in enumerate(text):
        for y,row in enumerate(FONT[char]):
            for x,p in enumerate(row):
                if p=='1':pixels[(y+4)*w+x0+n*6+x]=(29,26,15)
    return rc.paint('HarborSign'+str(SIGNS.index(text)),w,h,pixels)

@lru_cache(maxsize=1)
def materials():
    """Immutable original art, cached only to avoid repeating quantization."""
    out=[]
    def add(name,w,h,pixel):out.append(rc.paint(name,w,h,[pixel(x,y) for y in range(h) for x in range(w)]))
    def grain(x,y):return ((x*374761393+y*668265263)^((x*1274126177+y*97)>>7))%19
    def steel(x,y):
        v=1 if grain(x,y)==0 else 0
        if x==0 or y==0:return (9,13,16)
        if x==1 or y==1:return (15,19,21)
        if (x in (5,58) and y in (5,58)):return (19,22,22)
        return (12+v,16+v,18+v)
    def deck(x,y):
        if x==0 or y==0:return (8,12,14)
        if x==1 or y==1:return (15,19,21)
        if y%16==8 and x%12 in (4,5):return (14,18,20)
        v=1 if grain(x,y)<2 else 0
        return (11+v,15+v,17+v)
    def hull(x,y):
        if y==0 or x==0:return (6,10,13)
        if y==1:return (12,18,20)
        v=1 if grain(x,y)==1 else 0
        return (9+v,14+v,17+v)
    def water(x,y):
        # Broken horizontal glints; no bright grid/checkerboard across the bay.
        wave=math.sin(y*.73+math.sin(x*.035)*2)
        if wave>.94 and (x+7*y)%71<18:return (3,6,8)
        return (1,3,5) if wave>0 else (1,3,4)
    add('HarborSteel',64,64,steel);add('HarborDeck',64,64,deck)
    add('HarborHull',64,32,hull);add('HarborWater',128,64,water)
    for name,base in (('HarborStone',(16,17,17)),('HarborRed',(19,9,7)),('HarborBlue',(7,13,17))):
        def pixel(x,y,b=base):
            if name=='HarborStone':
                v=-1 if grain(x,y)==0 else 0
                return tuple(c+v for c in b) if x%63 and y%63 else tuple(c-2 for c in b)
            ridge=1 if x%12==1 else -2 if x%12==0 else 0
            wear=-1 if grain(x,y)==0 and y>45 else 0
            return tuple(max(0,c+ridge+wear) for c in b)
        add(name,64,64,pixel)
    add('HarborWood',64,64,lambda x,y:(14,11,7) if x%16==0 else
        (20,16,11) if x%16==1 else (17+(grain(x//2,y//8)==0),13,8))
    def ship(x,y):
        if y in (0,31) or x%32==0:return (4,7,9)
        if y>20:return (14+y%3,6+x%2,5)
        if y in (18,19,20):return (25,18,9)
        if x%32 in (3,28) and y%8==3:return (20,24,24)
        return (6+(x*3+y)%3,12+y%2,16+x%2)
    add('HarborShip',64,32,ship)
    add('HarborOffice',32,32,lambda x,y:(9,15,16) if y>22 else
        (21,21,18) if (x*13+y*7)%17 else (19,19,16))
    add('HarborGirder',64,32,lambda x,y:(9,10,10) if y in (0,31) else
        (24,19,10) if y in (1,30) or x in (5,58) and y in (5,26) else (18,13,6))
    add('HarborEdge',32,8,lambda x,y:(20,16,8) if y in (3,4) else (7,11,13))
    add('HarborLamp',16,16,lambda x,y:(31,29,18) if 3<x<12 and 4<y<11 else
        (20,16,7) if 2<x<13 and 3<y<12 else (4,8,12))
    bolt=('00001100','00011000','00110000','01111110','00011000','00110000','01100000','00000000')
    add('HarborBolt',8,8,lambda x,y:(29,24,10) if bolt[y][x]=='1' else (5,10,13))
    path=Path(__file__).resolve().parents[1]/'reference/art/crane-harbor-v1.rgb555'
    raw=path.read_bytes()
    if len(raw)!=768*128*2:raise ValueError('Harbor panorama dimensions changed')
    values=struct.unpack('<98304H',raw)
    for panel in range(3):
        pixels=[tuple((values[y*768+panel*256+x]>>(n*5))&31 for n in range(3)) for y in range(128) for x in range(256)]
        out.append(rc.paint('HarborSky'+str(panel),256,128,pixels,colours=256))
    out.extend(_sign(text) for text in SIGNS)
    return tuple(out)

def face(look,x0,y0,x1,y1,z,shade=1):
    return rc.Quad(look,((x0,y1,z),(x0,y0,z),(x1,y0,z),(x1,y1,z)),shade=shade)

def bar(x0,y0,x1,y1,z,width=1,look=AMBER):
    """Thin planar beam. Perpendicular offset retains front winding for all slopes."""
    dx,dy=x1-x0,y1-y0;length=math.hypot(dx,dy)
    if not length:raise ValueError('Zero length crane brace')
    ox,oy=-dy/length*width/2,dx/length*width/2
    return rc.Quad(look,((x0+ox,y0+oy,z),(x0-ox,y0-oy,z),
                        (x1-ox,y1-oy,z),(x1+ox,y1+oy,z)))

def sign(text,x,y,z=-20,width=24):
    return face(rc.Look('HarborSign'+str(SIGNS.index(text))),x,y,x+width,y+width/4,z)

def portal(look,wall,floor,facing_right):
    """Shutter and recessed jambs face into the room, including side views.

    Native materials cull their back faces. A left-wall shutter needs a +x
    normal; the older shared shutter helper winds it in the other direction.
    Jambs project less than the player's collision radius from the wall.
    """
    direction=1 if facing_right else -1
    x=wall+direction*.16
    def panel(y0,y1,z0,z1,material):
        corners=((x,y1,z1),(x,y0,z1),(x,y0,z0),(x,y1,z0))
        if not facing_right:corners=corners[::-1]
        return rc.Quad(material,corners,shade=.95)
    out=[panel(floor,floor+14,-9,9,look)]
    x0,x1=sorted((wall+direction*.2,wall+direction*1.3))
    for y0,y1,z0,z1 in ((floor,floor+17,-12,-9.3),
                         (floor,floor+17,9.3,12),
                         (floor+14.3,floor+17,-9.3,9.3)):
        out+=rc.box(x0,y0,z0,x1,y1,z1,STEEL,1,'front left right under')
    # A practical light above the shutter remains visible when looking
    # obliquely along either boundary wall.
    x=wall+direction*1.35
    out.append(panel(floor+14.8,floor+16.4,-5,5,LAMP))
    return out

def ceiling(w,h,draw_shell=False):
    """Trim on the real ceiling, never an extra non-colliding hanging beam."""
    out=[]
    # Outdoor shells originally omit render faces and ceiling enemy anchors.
    # Draw those faces as scenery to preserve the existing anchor contract.
    if draw_shell:out+=rc.box(0,h,-25,w,h+18,25,STEEL,1,'under')
    # The fascia sits wholly inside the solid; its amber edge makes the
    # crawl limit readable without changing any collision or anchor points.
    out+=rc.box(0,h,-25,w,h+18,25.08,STEEL,1,'front')
    out+=rc.box(0,h+.15,-25,w,h+.95,25.16,EDGE,1,'front')
    for x in range(12,int(w),64):
        out+=rc.box(x,h,-24,min(x+2,w),h+1,24,AMBER,1,'under')
    return out

def crane(x,y,scale,z=-100):
    """One recognisable lattice harbor crane, not intersecting solid gold bars."""
    out=[]
    def beam(a,b,c,d,width=1.5):out.append(bar(x+a*scale,y+b*scale,x+c*scale,y+d*scale,z,width*scale))
    for a in (-13,13):beam(a,0,a,82,3)
    for n in range(4):
        yy=n*20;beam(-13,yy,13,yy+20);beam(13,yy,-13,yy+20)
    beam(-115,80,87,80,3);beam(-115,87,87,87,2)
    for n in range(10):
        a=-113+n*20;beam(a,80,a+10,87,.85);beam(a+10,87,a+20,80,.85)
    beam(-13,80,0,103,2);beam(13,80,0,103,2)
    beam(-112,87,0,103,.7);beam(0,103,84,87,.7)
    beam(54,80,54,40,.7);beam(62,80,62,40,.7)
    # Cab, rear counterbalance, hanging spreader, and a warm cab window.
    for a,b,c,d,look in ((-23,65,8,78,STEEL),(-21,69,-2,76,LAMP),
                        (-94,76,-70,82,DARK),(46,37,70,41,AMBER)):
        out.append(face(look,x+a*scale,y+b*scale,x+c*scale,y+d*scale,z+.2))
    return out

def platform_details(solids,w):
    out=[]
    for q in solids:
        if abs(q.y1-q.y0-3)>.01 or q.y0<=0:continue
        a,b,y=q.x0,q.x1,q.y1
        if b-a<8:continue
        # Rail and bracing sit behind the player's movement plane. Amber lip
        # lies on the solid fascia; it never suggests an extra landing.
        out.append(face(EDGE,a,q.y0+.4,b,q.y0+1.1,q.depth+.08))
        out.append(bar(a,y+6,b,y+6,-23,.65,STEEL))
        if b-a>=64:
            for x in (a+2,b-2):out.append(bar(x,y,x,y+6,-23,.65,STEEL))
        out.append(bar(a,y-3,min(b,a+12),max(0,y-13),-24,1.2,AMBER))
    return out

def cargo_details(solids):
    out=[]
    for n,q in enumerate(solids):
        if q.y0!=0 or q.y1<10 or q.x1-q.x0<25:continue
        x0,x1,y0,y1,z=q.x0,q.x1,q.y0,q.y1,q.depth+.12
        # Fittings are confined to existing collision silhouettes.
        for x in (x0+.8,x1-1.6):out.append(face(STEEL,x,y0+.3,x+.8,y1-.3,z))
        out.append(face(EDGE,x0+.9,y1-1.6,x1-.9,y1-.7,z+.04))
        for x in ((x0+x1)/2-3,(x0+x1)/2+3):out.append(face(STEEL,x,y0+1,x+.45,y1-2,z+.06))
    return out

def setwork(i,w,h,solids):
    """Room-specific landmarks. This function contributes no collision."""
    out=platform_details(solids,w)+cargo_details(solids)
    def box(a,b,c,d,z=-22,depth=3,look=STEEL):out.extend(rc.box(a,b,z,c,d,z+depth,look,.95,'front top left right'))
    if i==0:
        # The gateway is the first reveal: a tall harbor crane, freight signs,
        # mooring bollards and a nearby boat beyond the dock.
        out+=crane(158,-10,.95,-115)
        for x in (34,132,278):
            box(x,0,x+3,4,-17);box(x-1,3,x+4,5,-17,look=AMBER)
        box(214,-1,278,6,-68,8,HULL);box(238,6,258,17,-68,8,STEEL)
        out.append(face(LAMP,241,10,255,15,-59))
        # Hanging cargo aligns with the actual upper take-off ledges.
        for a,b,y in ((78,118,16),(182,226,36),(244,300,54)):
            for x in (a+3,b-3):out.append(bar(x,y,x,94,-24,.5,STEEL))
        for x in (64,114):out.append(bar(x,64,x,94,-24,.5,STEEL))
        for a,b in ((0,64),(124,180),(244,360)):
            box(a,-18,a+3,0,-22,4,AMBER);box(b-3,-18,b,0,-22,4,AMBER)
    elif i==1:
        # Roof express has visible suspension; the broad lower arena remains
        # open enough to launch, cross up and throw the native cargo barrels.
        for a,b,y in ((114,170,64),(198,254,84),(282,340,104)):
            out.append(bar(a,y,b,y,-24,1.5,AMBER))
            for x in (a+4,b-4):out.append(bar(x,y,x,154,-24,.6,STEEL))
        out.append(bar(48,154,352,154,-24,3,AMBER))
    elif i==2:
        # Warm desk, chart board, high harbor window, ceiling conduit.
        box(4,0,8,64,look=AMBER);box(100,0,104,64,look=AMBER)
        box(7,47,101,50,look=AMBER)
        out.append(face(HULL,8,11,38,32,-24))
        out.append(sign('CRANE ROW',9,23,-23,28))
        out.append(face(rc.Look('screens01'),11,14,35,22,-22))
        box(63,0,93,3,-22,7);box(66,3,69,11,-21);box(87,3,90,11,-21)
        box(62,10,94,12,-23,9,AMBER)
        out.append(face(rc.Look('screens01'),75,13,86,23,-18))
        out.append(face(AMBER,7,32,101,33,-23))
        out.append(face(STEEL,7,0,101,2,-23))
        for x in (22,76):out.append(face(LAMP,x,46,x+10,50,-19))
    elif i==3:
        # Distant stacks show how deep the cargo canyon runs. They sit well
        # behind the playable stacks so Spidey and their top edges stay clear.
        for n,x in enumerate((34,110,218,302)):
            box(x,-8,x+52,72+n%2*24,-72,6,HULL)
        for x,y in ((116,62),(182,86),(246,104)):
            out.append(bar(x,y,x,144,-24,.5,STEEL))
    elif i==4:
        # Ship reads as a vessel: keel, waterline, portholes, hull seams,
        # superstructure and deck rail, all behind the traversable supports.
        for a,b in ((77,135),(169,251),(285,323)):
            out.append(face(EDGE,a,64,b,65,-7.8))
        for x in (86,114,182,210,238,294):
            out.append(face(STEEL,x,40,x+8,47,-7.7))
            out.append(face(LAMP,x+1,41,x+7,46,-7.6))
        box(178,68,246,86,-22,8,HULL);box(192,86,230,100,-22,8,STEEL)
        for x in (198,215):out.append(face(LAMP,x,90,x+10,96,-13.8))
        for a,b in ((78,134),(170,250),(286,322)):
            out.append(bar(a,74,b,74,-9,.65,STEEL))
            for x in range(a,b,18):out.append(bar(x,68,x,74,-9,.65,STEEL))
        box(246,68,255,116,-22,6,AMBER)
        out.append(bar(250,114,142,90,-24,.7,STEEL))
        out.append(bar(250,114,338,88,-24,.7,STEEL))
    elif i==5:
        out.append(face(rc.Look('HarborBolt'),138,16,146,24,-20))
        # Pipe trunk and console bays replace the giant repeated monitor wall.
        for x in (36,236):
            box(x,4,x+4,132,-23,4);box(x-2,129,x+24,133,-23,4)
        for x in (60,200):
            out.append(face(EDGE,x,13,x+30,15,-12.8))
            out.append(face(rc.Look('screens01'),x+5,24,x+25,39,-12.7))
        for x in (86,186):out.append(face(LAMP,x,115,x+14,119,-18))
    elif i==6:
        # Guide rails, cross braces and floor numbers sell a working shaft.
        for y in range(24,216,32):
            out.append(bar(53,y,119,y+22,-24,1.1,DARK))
            out.append(bar(119,y,53,y+22,-24,1.1,DARK))
            out.append(face(LAMP,82,y+12,90,y+15,-23))
        for y in (18,62,106,150,192):
            out.append(face(EDGE,54,y+5,68,y+6,-23))
    elif i==7:
        out+=crane(288,-45,1.15,-135)
        # Broken truss follows the real stepped bridge; there is no fake solid
        # floor across its gaps. The lower service deck is clearly supported.
        for a,b,y in ((0,54,0),(74,124,0),(154,208,16),(238,290,0),(318,360,20),(366,420,0)):
            out.append(bar(a,y-3,b,y-3,-22,2,AMBER))
            out.append(bar(a,y-3,b,y+22,-23,1,AMBER))
        out.append(bar(16,102,404,102,-24,2,AMBER))
        for x in (64,152,236,324):out.append(bar(x,56,x,102,-24,.6,STEEL))
    elif i==8:
        for x in (20,124):
            box(x,2,x+3,70,look=AMBER);box(x-1,68,x+16,71,look=AMBER)
        out.append(face(LAMP,71,76,89,80,-19))
    elif i==9:
        out+=crane(168,-6,1.15,-65)
        out.append(bar(78,16,78,158,-24,3,AMBER))
        out.append(bar(256,16,256,158,-24,3,AMBER))
        out.append(bar(78,158,256,158,-24,4,AMBER))
        out.append(bar(78,158,166,172,-24,2,AMBER))
        out.append(bar(166,172,256,158,-24,2,AMBER))
        # Far container stacks below this crane establish height.
        for n,x in enumerate(range(30,330,56)):
            box(x,-18,x+42,-2+n%3*5,-76,8,HULL)
    elif i==10:
        # Deliberately quiet combat backdrop: lane markers and motor remain
        # the strongest contrast; a massive truss frames their machinery.
        for x in range(18,402,32):out.append(bar(x,30,x+16,49,-24,1.2,AMBER))
        out.append(bar(8,50,410,50,-24,2,AMBER))
        for x in (328,392):
            out.append(face(rc.Look('HarborSteel',(4,4),(12,31,23)),x-2,0,x+2,1,-12))
        out+=crane(330,-25,.8,-130)
    elif i==11:
        # A quieter victory promenade with boat lights and a single far crane.
        out+=crane(80,-30,.62,-155)
        box(128,-2,220,6,-66,7,HULL);box(160,6,187,20,-66,7,STEEL)
        for x in (165,176):out.append(face(LAMP,x,11,x+7,16,-58.8))
    return out
