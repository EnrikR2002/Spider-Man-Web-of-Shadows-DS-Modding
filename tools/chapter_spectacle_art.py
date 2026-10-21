"""Painted chapter materials, architectural depth and original machinery meshes."""
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
import math
from tools import room_compiler as rc,nitro_build as nb,crane_art as ca
from tools.creature_forge_art import Sculpt

ATLAS=Path(__file__).resolve().parents[1]/'reference/art/chapter-spectacle-materials-v1.png'
CELLS={'MLStone':0,'MLSteel':1,'MLDeck':2,'MLGlass':13,'MLRail':14,
       'HarborStone':11,'HarborSteel':1,'HarborDeck':2,'HarborHull':7,
       'HarborRed':4,'HarborBlue':5,'HarborWood':8,'HarborOffice':9,
       'HarborGirder':6,'HarborShip':7}

class ReadableSculpt(Sculpt):
    """Keep the exact rig and motion; give native-scale limbs and cores mass."""
    def limb(self,j,a,b,r,tile):return super().limb(j,a,b,r*1.24,tile)
    def loft(self,j,a,b,radii,tile,sides=6):
        if j==3:radii=tuple((f,rx*1.08,ry*1.12) for f,rx,ry in radii)
        return super().loft(j,a,b,radii,tile,sides)
    def side_panel(self,j,c,half_y,half_z,tile):
        sign=1 if c[0]>=self.p[j][0] else -1
        delta=.55 if j==3 else .18
        c=(c[0]+sign*delta,c[1],c[2]);hy=half_y*1.12;hz=half_z*1.12
        vs=tuple((c[0],c[1]+y,c[2]+z) for y,z in ((-hy,-hz),(-hy,hz),(hy,hz),(hy,-hz)))
        # The two sides require opposite outward normals. Reusing one winding
        # for both hides the near core when the creature turns around.
        self.face(j,tile,tuple(reversed(vs)) if sign>0 else vs)

@lru_cache(maxsize=64)
def painted(name,width,height):
    from PIL import Image
    im=Image.open(ATLAS).convert('RGB');cell=CELLS[name];sx=im.width/4;sy=im.height/4
    # Avoid a neighboring swatch's seam; preserve the painted broad structure.
    x,y=cell%4,cell//4
    im=im.crop((round(x*sx)+3,round(y*sy)+3,round((x+1)*sx)-3,round((y+1)*sy)-3)).resize((width,height),Image.Resampling.LANCZOS)
    pixels=[]
    for r,g,b in im.getdata():
        # Restrained cool stone and warm dock metals, never electric-blue floors.
        if name=='MLStone':r,g,b=r*.82,g*.91,min(255,b*1.04)
        pixels.append(tuple(max(0,min(31,round(c/255*31))) for c in (r,g,b)))
    return rc.paint(name,width,height,pixels)

def materials(plan):
    textures=list(plan.textures);palettes=list(plan.palettes);pm={p.name:i for i,p in enumerate(palettes)}
    for i,t in enumerate(textures):
        if t.name not in CELLS:continue
        tt,pp=painted(t.name,t.width,t.height)
        textures[i]=replace(tt,flags=t.flags,extra=t.extra)
        palettes[pm[pp.name]]=replace(pp,flag=palettes[pm[pp.name]].flag)
    return replace(plan,textures=tuple(textures),palettes=tuple(palettes))

def architecture(plan,index):
    midnight=index<96;w=plan.bounds[2];h=plan.bounds[3];scene=list(plan.scenery)
    metal=rc.Look('MLSteel' if midnight else 'HarborSteel',(32,32))
    dark=rc.Look('MLDark' if midnight else 'HarborHull',(32,32),(15,18,20))
    trim=rc.Look('MLAmber' if midnight else 'HarborGirder',(16,16),(24,24,22))
    def face(look,a,y,b,top,z=-22,shade=1):scene.append(ca.face(look,a,y,b,top,z,shade))
    def box(a,y,z,b,top,zz,look=metal,shade=1):scene.extend(rc.box(a,y,z,b,top,zz,look,shade,'front top left right under'))
    def bar(a,y,b,top,z=-30,width=1.1,look=metal):scene.append(ca.bar(a,y,b,top,z,width,look))
    # Recessed joints and strong, supported platform fascias at the collision edge.
    for q in plan.solids:
        if q.hidden or q.x1-q.x0<8:continue
        z=q.depth+.15
        face(metal,q.x0,q.y1-1.7,q.x1,q.y1-.8,z,.88)
        if q.y0>0:
            face(dark,q.x0,q.y0,q.x1,min(q.y1,q.y0+.65),z,.6)
            if q.x1-q.x0>30:
                bar(q.x0+2,q.y0,q.x0+10,max(0,q.y0-10),-24,1.2)
    if midnight:
        # Structural wall piers have a shadow side and a narrow bevel, rather
        # than being equally lit rectangles. Keep these behind action and doors.
        for x in range(24,int(w)-20,64):
            box(x-3,0,-59,x+1,h-10,-53,metal,.48)
            face(metal,x+1,0,x+2,h-10,-52,.9)
        for y in range(12,int(h),32):face(dark,12,y,w-12,y+.65,-62,.75)
        if index==78:
            # Recessed carriage fronts, modeled wheels and roof seams. The
            # foreground roof slabs are also the real collision surfaces.
            for x in (80,152,224):
                for xx in (x+11,x+52):
                    for n in range(10):
                        a=n*2*math.pi/10;b=(n+1)*2*math.pi/10
                        bar(xx+4*math.cos(a),5+4*math.sin(a),xx+4*math.cos(b),5+4*math.sin(b),-9,1.8,dark)
                face(dark,x+29,5,x+39,24,-10,.7)
                face(trim,x+31,12,x+32,19,-9.8,.8)
            for x in (62,310):
                box(x,0,-25,x+15,2,-13,metal,.8);box(x+2,2,-25,x+4,9,-20,metal,.65)
            # A vaulted truss canopy holds the practical lamps and cables.
            for x in (68,164,260):
                bar(x-28,66,x,87,-38,2.2);bar(x,87,x+28,66,-38,2.2)
                bar(x,87,x,59,-37,.7,trim)
        elif index==81:
            for x in (66,144,222):
                for r in (9,13):
                    for n in range(12):
                        a=n*2*math.pi/12;b=(n+1)*2*math.pi/12
                        bar(x+r*math.cos(a),36+r*math.sin(a),x+r*math.cos(b),36+r*math.sin(b),-24.5,1.8,trim)
                bar(x,52,x,78,-30,3);bar(x,78,min(w-14,x+46),78,-30,3)
            face(dark,14,0,w-14,2,-10,.8)
        elif index==83:
            # Concentric turbine housing and maintenance spine sell the climb.
            for radius in (49,53):
                for n in range(20):
                    a=n*2*math.pi/20;b=(n+1)*2*math.pi/20
                    bar(96+radius*math.cos(a),72+radius*math.sin(a),96+radius*math.cos(b),72+radius*math.sin(b),-33,2,trim)
            for y in (16,64,112):box(13,y,-28,22,y+9,-25,metal,.8)
        elif index in (86,89):
            cx=w/2;cy=54 if index==89 else 40
            for radius in (34,47):
                for n in range(20):
                    if index==86 and n>10:continue
                    a=n*2*math.pi/20;b=(n+1)*2*math.pi/20
                    bar(cx+radius*math.cos(a),cy+radius*math.sin(a),cx+radius*math.cos(b),cy+radius*math.sin(b),-29,1.3,trim)
            box(cx-12,0,-27,cx+12,9,-24,metal,.65)
        elif index in (77,82,87):
            # Benches, skirting and a sheltered ceiling conduit distinguish
            # actual public/maintenance rooms from another empty arena.
            face(trim,10,9,w-10,10,-24,.65)
            box(12,0,-25,34,3,-15,metal,.8)
            for x in (15,30):box(x,0,-20,x+1.5,3,-16,metal,.6)
            bar(10,h-12,w-12,h-12,-30,2,trim)
    else:
        if index==100:
            ship=rc.Look('HarborShip',(64,32));edge=rc.Look('HarborGirder',(32,16))
            # A continuous hull behind the playable hold, with a sloping bow,
            # waterline, portholes and structural ribs instead of isolated boxes.
            scene.append(rc.Quad(ship,((42,30,-37),(68,8,-37),(328,8,-37),(358,30,-37)),((0,0),(0,1),(5,1),(5,0)),.78))
            face(ship,42,30,358,58,-37,.83);face(edge,66,10,330,12,-36,.9)
            for x in range(78,334,34):
                box(x,30,-36,x+2,58,-33,metal,.7);box(x+8,39,-32,x+18,45,-30,dark,.85)
        if index==101:
            for x in (66,206):
                for n in range(16):
                    a=n*2*math.pi/16;b=(n+1)*2*math.pi/16
                    bar(x+15*math.cos(a),38+15*math.sin(a),x+15*math.cos(b),38+15*math.sin(b),-11,2.3,trim)
                box(x-7,20,-11,x+7,23,-8,metal,.9)
            bar(40,64,240,64,-25,3.5);bar(140,64,140,100,-26,2)
        if index==102:
            for x in (50,120):
                for y in (56,120,184):
                    for n in range(12):
                        a=n*2*math.pi/12;b=(n+1)*2*math.pi/12
                        bar(x+7*math.cos(a),y+7*math.sin(a),x+7*math.cos(b),y+7*math.sin(b),-15,1.8,trim)
        if index==106:
            # Approach culminates at a huge suspended winch housing. Every
            # fixture behind the player plane remains scenery, never collision.
            for x in (302,402):box(x,0,-42,x+6,92,-34,metal,.78)
            box(302,84,-42,408,94,-32,metal,.82)
            for x in range(308,402,20):bar(x,84,x+18,94,-31,1.8,trim)
            for x in (340,348):bar(x,28,x,88,-30,.8,trim)
            # A quiet save alcove is architecture at the safe end of the arm.
            box(24,0,-33,48,3,-24,metal,.8);box(22,3,-34,24,23,-28,metal,.6)
            bar(22,23,48,23,-28,2,trim)
    shades=dict(plan.shades or {})
    shades.update(top=1.,side=.74,under=.66,front=.46,body=.68)
    return materials(replace(plan,scenery=tuple(scene),shades=shades))


def mesh(name,faces):
    """Untextured world machinery uses its native material and correct bounds."""
    points=[p for _,vs in faces for p in vs];lo=[min(p[i] for p in points) for i in range(3)];hi=[max(p[i] for p in points) for i in range(3)]
    scale=64
    model=nb.RoomModel(name,'root',bytes((7,248,0,16)),(nb.Material('cast',None,None,nb.material_record(8,8,texture_param=0)),),
        (rc._stream(faces,scale*4096),),((0,0),),scale*4096,(len(faces)*4,len(faces),0,len(faces)),
        tuple(round(v*4096/scale) for v in (*lo,*(b-a for a,b in zip(lo,hi)))),scale*4096)
    return nb.room_model(model)

def machinery(kind,*,broken=False,dead=False):
    faces=[]
    def quad(col,pts):faces.append((sum(c<<(i*5) for i,c in enumerate(col)),tuple((*p,0,0) for p in pts)))
    def box(a,y,z,b,top,zz,col):
        for q in rc.box(a,y,z,b,top,zz,rc.Look('none'),1,'front top left right under'):
            quad(tuple(round(c*(1 if q.corners[0][1]==q.corners[1][1] else .82)) for c in col),q.corners)
    steel=(10,14,17) if not dead else (6,7,8);rim=(22,18,10) if not dead else (12,10,7)
    light=(31,23,10) if not broken else (31,12,4)
    if dead:light=(7,3,2)
    if kind=='hook':
        box(-10,11,0,10,18,5,rim);box(-8,12,5,8,17,6,steel)
        for side in (-1,1):
            a,b=sorted((side*8,side*12));box(a,0,0,b,12,4,steel)
            a,b=sorted((side*3,side*12));box(a,0,0,b,3,5,rim)
            quad((18,21,22),((side*8,10,4),(side*12,10,4),(side*12,3,5),(side*6,3,5)))
        for x in (-2,1):box(x,18,-1,x+1,62,1,steel)
        box(-5,13,6,5,15,7,light)
    else:
        box(-13,0,0,13,17,3,steel)
        for a,b in ((-13,-10),(10,13)):box(a,1,3,b,16,6,rim)
        box(-10,1,3,10,3,5,rim);box(-10,15,3,10,17,5,rim)
        if kind=='shield':
            if broken:
                box(-9,3,5,-1,15,7,(8,10,12));box(1,3,5,9,13,7,(11,12,12))
                box(-9,7,7,9,8.5,8,(22,8,3))
            else:box(-9,3,5,9,15,7,(13,17,19));box(-9,7,7,9,9,8,rim)
            for x in (-7,6):box(x,4,7,x+1,13,8,(23,25,24))
        else:
            box(-8,3,3,8,15,4,(3,5,7))
            for n in range(16):
                a=n*2*math.pi/16;b=(n+1)*2*math.pi/16
                quad(rim,((7*math.cos(a),9+7*math.sin(a),5),(7*math.cos(b),9+7*math.sin(b),5),
                          (5*math.cos(b),9+5*math.sin(b),5),(5*math.cos(a),9+5*math.sin(a),5)))
            box(-3,5,5,3,13,6,light);box(-1,6,6,1,12,6.5,(31,29,22))
            for x in (-6,4):box(x,5,5,x+1,13,6,(18,22,24))
    # The machinery must sit behind the hero. The native object's draw scale
    # otherwise makes a foreground guard hide an entire melee exchange.
    shifted=[]
    for color,vertices in faces:
        if kind=='hook':vs=tuple((x,y,z-12,u,v) for x,y,z,u,v in vertices)
        else:vs=tuple((x*.72,y*.78+1.5,z-10,u,v) for x,y,z,u,v in vertices)
        shifted.append((color,vs))
    return mesh('CS23_'+kind,shifted)


def lights(index,positions,*,on):
    faces=[]
    for x,y in positions:
        # The complete light panel is a single native harmless world object.
        col=(31,25,12) if on else (3,8,12)
        for q in rc.box(x-2,y-1,-20,x+2,y+1,-18,rc.Look('none'),1,'front top under'):
            faces.append((sum(c<<(5*i) for i,c in enumerate(col)),tuple((*p,0,0) for p in q.corners)))
    return mesh('CS23_Light',faces)
