"""2099 revision: anatomical volume, surface-mounted blades and a torn web cape.

The 0.30 author remains reproducible. This revision starts with the exact native
Black mesh, preserves all bone/SBC/animation data, and reshapes skin vertices in
bind space. The cape uses an isolated transparent-index atlas region and native
shoulder/chest/pelvis matrices. It is bone-deformed cloth, not a physics solver.
"""
from collections import defaultdict
from dataclasses import replace
import math
import struct

from tools import spider2099_art as old, wos_tool as w
from tools.animation_rig import AnimationRig
from tools.model_geometry import ModelGeometry
from tools.nitro_texture import TextureArchive, dictionary
from tools.rush_choreography import add, sub, mul, dot, cross, unit, length, mv, transpose

WIDTH, HEIGHT = 256, 128
CAPE_COLUMNS, CAPE_ROWS = 8, 5


def inverse(matrix):
    cofactors = (cross(matrix[1],matrix[2]),cross(matrix[2],matrix[0]),cross(matrix[0],matrix[1]))
    det = dot(matrix[0],cofactors[0])
    if abs(det) < .5:
        raise ValueError('Invalid native bind rotation')
    return tuple(tuple(v/det for v in row) for row in transpose(cofactors))


def native_vertices(raw):
    """One vertex per GPU emission, retaining the source's primitive/UV order."""
    _,rotations,positions,slots=old.bind_matrices(raw)
    slot,uv,xyz=3,(0.,0.),[0.,0.,0.]
    signed=lambda v,b:(v&((1<<b)-1))-((1<<b) if v&(1<<(b-1)) else 0)
    for op,args in old.gpu_commands(raw):
        if op==0x14:slot=args[0]
        elif op==0x22:uv=(signed(args[0],16)/16,signed(args[0]>>16,16)/16)
        elif 0x23<=op<=0x28:
            if op==0x23:xyz=[signed(args[0],16)/4096,signed(args[0]>>16,16)/4096,signed(args[1],16)/4096]
            elif op==0x24:xyz=[signed(args[0]>>(i*10),10)/64 for i in range(3)]
            elif op in (0x25,0x26,0x27):
                for i,k in enumerate({0x25:(0,1),0x26:(0,2),0x27:(1,2)}[op]):xyz[k]=signed(args[0]>>(i*16),16)/4096
            else:xyz=[xyz[i]+signed(args[0]>>(i*10),10)/4096 for i in range(3)]
            j=slots[slot]
            yield old.Vertex(add(positions[j],mv(rotations[j],xyz)),uv,slot,tuple(xyz))


class Anatomy:
    def __init__(self,raw):
        if w.sha256(raw)!=old.MODEL_SHA:
            raise ValueError('Sculpt requires exact native Black model')
        self.raw=raw
        self.rig,self.rotations,self.positions,self.slots=old.bind_matrices(raw)
        self.inverses=[inverse(m) for m in self.rotations]
        self.segments=[(a,b,kind) for a,b,kind in ((7,8,'upper'),(8,9,'fore'),(17,18,'upper'),(18,19,'fore'))]
        self.original=old.mesh(raw)
        self.faces=[tuple(replace(v,position=self.morph(v.position)) for v in face) for face in self.original]

    def arm(self,p):
        candidates=[]
        for a,b,kind in self.segments:
            origin=self.positions[a];axis=sub(self.positions[b],origin)
            f=max(0.,min(1.,dot(sub(p,origin),axis)/dot(axis,axis)))
            center=add(origin,mul(axis,f))
            candidates.append((length(sub(p,center)),f,center,kind,a))
        return min(candidates)

    def morph(self,p):
        x,y,z=p;ax=abs(x)
        # Broad lats/pecs taper into the original waist and unchanged neck.
        upper=math.exp(-((y-7.45)/.93)**4)
        body_weight=max(0.,min(1.,(1.85-ax)/.7))
        torso=(x*(1+.24*upper*body_weight),y,z*(1+.32*upper*body_weight))
        if 6.9<y<8.35 and z>-.15:
            pec=.18*math.exp(-((ax-.55)/.52)**2-((y-7.66)/.48)**2)*body_weight
            torso=add(torso,(0,0,pec))
        # Higher traps give the shoulders a deliberate slope.
        trap=.13*math.exp(-((y-8.13)/.28)**2-((ax-.58)/.5)**2)
        torso=add(torso,(0,trap,0))
        if ax>1.25 and y>5.8:
            distance,f,center,kind,_=self.arm(p)
            if distance<.9:
                envelope=math.sin(math.pi*f)**.8
                scale=1.06+(.58 if kind=='upper' else .09)*envelope
                arm=add(center,mul(sub(p,center),scale))
                blend=max(0.,min(1.,(ax-1.25)/.48))
                torso=add(mul(torso,1-blend),mul(arm,blend))
        # Small thigh volume increase; original hip/knee/ankle pivots stay put.
        if 1.1<y<5.3:
            best=None
            for a,b in ((26,27),(30,31)):
                origin=self.positions[a];axis=sub(self.positions[b],origin)
                f=max(0.,min(1.,dot(sub(p,origin),axis)/dot(axis,axis)))
                center=add(origin,mul(axis,f));d=length(sub(p,center))
                if best is None or d<best[0]:best=(d,f,center)
            distance,f,center=best
            if distance<.8 and y>3.25:
                torso=add(center,mul(sub(p,center),1+.12*math.sin(math.pi*f)))
        return torso

    def local(self,slot,p):
        j=self.slots[slot]
        return mv(self.inverses[j],sub(p,self.positions[j]))

    def ray_skin(self,origin,direction,slot=None,limit=8.):
        """First forward ray/skin intersection; no guessed offsets beneath skin."""
        hits=[]
        for face in self.faces:
            if slot is not None and not any(v.slot==slot for v in face):continue
            a,b,c=(v.position for v in face);e1,e2=sub(b,a),sub(c,a)
            h=cross(direction,e2);det=dot(e1,h)
            if abs(det)<1e-9:continue
            s=sub(origin,a);u=dot(s,h)/det
            q=cross(s,e1);v=dot(direction,q)/det;t=dot(e2,q)/det
            if -.0001<=u<=1.0001 and v>=-.0001 and u+v<=1.0001 and .025<t<limit:hits.append((t,face))
        if not hits:raise ValueError('Accessory ray missed its native skin surface')
        return min(hits,key=lambda hit:hit[0])

    def surface(self,slot,origin,direction):
        return self.ray_skin(origin,direction,slot,1.5)[0]


def _key(p):return tuple(round(v,5) for v in p)


def body_color(p,normal,anatomy):
    base=old.paint(p)
    red=base[0]>20
    if abs(p[0])>2.3 and p[1]>6.1:
        d,f,_,kind,_=anatomy.arm(p)
        if kind=='fore' and f>.13 and d<.8:red=True
    light=unit((-.4,.8,1.))
    shade=.28+.72*max(0.,dot(normal,light))
    # Broad under-pec and centre grooves remain readable without fine noise.
    if abs(p[0])<1.2 and 6.85<p[1]<8.1 and p[2]>.05:
        groove=.10*math.exp(-((p[1]-7.32)/.095)**2)
        groove+=.11*math.exp(-(p[0]/.095)**2)
        shade=max(.22,shade-groove)
    if red:return (round(18+13*shade),round(1+3*shade),round(3+4*shade))
    return (round(2+5*shade),round(4+10*shade),round(10+17*shade))


def cape_color(u,v):
    """Opaque crimson strands and true transparent holes in the cape-only half."""
    # Ripped lower edge, unequal tips, and a few missing outer web links.
    hem=.91+.075*math.cos(u*math.pi*8)+.025*math.cos(u*math.pi*17)
    if v>hem:return None
    x,y=u-.5,v+.13;r=math.hypot(x,y);theta=math.atan2(x,y)
    angles=[math.radians(-76+i*19) for i in range(9)]
    spoke=min(abs(math.sin(theta-a))*r for a in angles)
    nearest=min(range(9),key=lambda i:abs(theta-angles[i]))
    spoke_on=spoke<(.0135 if nearest%2==0 else .011)
    # Bowed transverse threads connect the radial ribs.
    phase=(theta-angles[0])/math.radians(19)
    scallop=.016*math.sin(math.pi*(phase%1))
    rings=(.19,.32,.47,.64,.82,1.02,1.23)
    ring=min(abs(r-radius-scallop) for radius in rings)
    cross_on=ring<.0095
    border=(u<.019 or u>.981) and v<.78
    collar=v<.027
    if v>.67 and nearest in (1,7) and .73<v<.84:spoke_on=False
    if not (spoke_on or cross_on or border or collar):return None
    glint=(.55+.45*math.cos(u*math.pi*3-v*2))
    if spoke_on or border or collar:return (31,round(2+3*glint),round(5+5*glint))
    return (round(23+6*glint),2,round(4+4*glint))


def artwork(raw):
    from tools.suit_uv_inspect import barycentric
    a=Anatomy(raw);normals=defaultdict(lambda:(0.,0.,0.))
    for face in a.faces:
        p,q,r=(v.position for v in face);n=cross(sub(q,p),sub(r,p))
        for v in face:normals[_key(v.position)]=add(normals[_key(v.position)],n)
    normals={k:unit(n) if length(n)>1e-8 else (0,0,1) for k,n in normals.items()}
    colors=[None]*(WIDTH*HEIGHT);covered=[False]*(128*128)
    for original,face in zip(a.original,a.faces):
        pts=[(v.uv[0]*2,v.uv[1]*2) for v in original]
        for y in range(max(0,math.floor(min(v[1] for v in pts))),min(128,math.ceil(max(v[1] for v in pts)))):
            for x in range(max(0,math.floor(min(v[0] for v in pts))),min(128,math.ceil(max(v[0] for v in pts)))):
                weights=barycentric((x+.5,y+.5),*pts)
                if not weights:continue
                p=tuple(sum(weights[j]*original[j].position[k] for j in range(3)) for k in range(3))
                n=tuple(sum(weights[j]*normals[_key(face[j].position)][k] for j in range(3)) for k in range(3))
                colors[y*WIDTH+x]=body_color(p,unit(n),a);covered[y*128+x]=True
    # Three texels of island bleed, with an opaque body-only background.
    for _ in range(3):
        previous=list(colors)
        for y in range(128):
            for x in range(128):
                i=y*WIDTH+x
                if previous[i] is None:
                    neighbors=[previous[ny*WIDTH+nx] for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                               if 0<=nx<128 and 0<=ny<128 and previous[ny*WIDTH+nx] is not None]
                    if neighbors:colors[i]=neighbors[0]
    for y in range(128):
        for x in range(128):
            if colors[y*WIDTH+x] is None:colors[y*WIDTH+x]=(3,7,16)
            colors[y*WIDTH+x+128]=cape_color((x+.5)/128,(y+.5)/128)
    for j,c in enumerate(((31,3,6),(17,1,3),(4,7,13),(8,13,23))):
        for y in range(124,128):
            for x in range(j*4,j*4+4):
                if covered[y*128+x]:raise ValueError('Accessory swatch overlaps native body UV')
                colors[y*WIDTH+x]=c
    # I4 keeps this 256x128 atlas in the preceding release's 16 KiB pixel pool.
    # A 32 KiB I8 atlas prevents actor textures binding in the crowded Terminal.
    palette=((2,4,10),(3,6,13),(4,8,16),(5,10,20),(6,12,24),(7,14,27),
             (17,1,3),(22,2,4),(26,3,6),(29,2,5),(30,3,7),(31,3,6),
             (31,5,10),(4,7,13),(8,13,23))
    lookup={c:1+min(range(len(palette)),key=lambda i:sum((c[k]-palette[i][k])**2 for k in range(3)))
            for c in set(colors) if c is not None}
    indices=bytes(lookup[c] if c is not None else 0 for c in colors)
    pal=bytes(2)+b''.join(struct.pack('<H',r|g<<5|b<<10) for r,g,b in palette)
    pal+=bytes(512-len(pal))
    if any(indices[y*WIDTH+x]==0 for y in range(128) for x in range(128)):
        raise ValueError('Transparent index leaked into the player body')
    return indices,pal,{'opaque_colors':len(palette),'storage_format':'I4','pixel_pool_bytes':16384,
        'cape_transparent_texels':sum(c is None for row in range(128) for c in colors[row*WIDTH+128:(row+1)*WIDTH]),'body_transparent_texels':0}


def texture(raw,indices,palette):
    if w.sha256(raw)!=old.TEXTURE_SHA:raise ValueError('Expected exact native Black I8 archive')
    if len(indices)!=WIDTH*HEIGHT or len(palette)!=512:raise ValueError('Invalid 2099 body/cape atlas')
    if any(v>15 for v in indices):raise ValueError('I4 palette index exceeds 15')
    packed=bytes(indices[i]|indices[i+1]<<4 for i in range(0,len(indices),2))
    out=bytearray(raw[:164]+packed+palette);delta=len(packed)-4096
    struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,24,len(out)-20)
    struct.pack_into('<H',out,32,len(packed)//8)
    for at in (0x24,0x28,0x38):struct.pack_into('<I',out,20+at,w.u32(raw,20+at)+delta)
    params=w.u32(raw,0x64)
    struct.pack_into('<I',out,0x64,(params&~((7<<20)|(7<<23)|(7<<26)))|5<<20|4<<23|3<<26|1<<29)
    extra=w.u32(raw,0x68)
    struct.pack_into('<I',out,0x68,(extra&~0x3fffff)|WIDTH|(HEIGHT<<11))
    parsed=TextureArchive.parse(out)
    if not parsed.textures[0]['params']&0x2000:raise ValueError('Cape transparency flag was lost')
    return bytes(out)


def model(raw):
    a=Anatomy(raw);g=ModelGeometry.parse(raw);commands=[];vertices=iter(native_vertices(raw));body_points=[]
    def vertex(slot,p):
        local=a.local(slot,p);values=tuple(round(v*4096) for v in local)
        if any(not -32768<=v<=32767 for v in values):raise ValueError('Sculpt vertex exceeds native Q12 bounds')
        x,y,z=values
        return (0x23,((x&65535)|(y&65535)<<16,z&65535))
    for op,args in old.gpu_commands(raw):
        if op==0x22:
            u,v=struct.unpack('<hh',struct.pack('<I',args[0]));args=(struct.unpack('<I',struct.pack('<hh',u*2,v*2))[0],)
        if 0x23<=op<=0x28:
            original=next(vertices);p=a.morph(original.position);body_points.append(p)
            commands.append(vertex(original.slot,p))
        else:commands.append((op,args))
    additions=[];fin_anchors=[]
    def triangle(points,uv):additions.append((tuple(points),tuple(uv)))
    def solid(slot,points,swatch):
        uv=(swatch*4+1.5,125.5)
        triangle([(slot,p) for p in points],(uv,uv,uv))
    # Surface-mounted, elbow-swept dorsal blades; each side has its own native axis.
    for slot,elbow,wrist in ((6,8,9),(15,18,19)):
        origin=a.positions[elbow];axis=sub(a.positions[wrist],origin);direction=unit(axis)
        dorsal=unit(sub((0,0,-1),mul(direction,dot((0,0,-1),direction))))
        across=unit(cross(direction,dorsal))
        for f,height in ((.21,.46),(.48,.58),(.75,.44)):
            center=add(origin,mul(axis,f));radius=a.surface(slot,center,dorsal)
            roots=[]
            for sign in (-1,1):
                origin_=add(center,mul(direction,sign*.13))
                t=a.surface(slot,origin_,dorsal)
                roots.append(add(add(origin_,mul(dorsal,t-.012)),mul(across,sign*.048)))
            left,right=roots;tip=add(add(center,mul(dorsal,radius+height)),mul(direction,-.20))
            ridge=add(add(center,mul(dorsal,radius+.10)),mul(across,.09))
            for ps,swatch in (((left,right,tip),0),((right,left,ridge),1),((left,tip,ridge),0),((tip,right,ridge),1)):
                solid(slot,ps,swatch)
            fin_anchors.append({'slot':slot,'fraction':f,'surface_radius':radius,'visible_height':height,
                'base_world':add(center,mul(dorsal,radius)),'tip_world':tip,'sweep_toward_elbow':dot(sub(tip,center),direction)<0})
    # Small native-finger hooks retain the hand's animation and contact geometry.
    for slot in (9,11,12,18,20,21):
        vs=[v for face in a.original for v in face if v.slot==slot]
        sign=-1 if slot<13 else 1
        end=(min if sign<0 else max)(v.local[0] for v in vs)
        cy=sum(v.local[1] for v in vs)/len(vs);cz=sum(v.local[2] for v in vs)/len(vs)
        points=((end,cy-.05,cz-.05),(end,cy+.05,cz+.05),(end+sign*.15,cy-.08,cz+.03))
        j=a.slots[slot];ps=[a.morph(add(a.positions[j],mv(a.rotations[j],p))) for p in points]
        solid(slot,ps,2);solid(slot,tuple(reversed(ps)),3)
    # Broad torn cape: collar anchors are behind the back surface, not inside it.
    rows=((8.18,-1.10,1.23),(7.42,-1.05,1.59),(6.64,-.96,1.79),
          (5.85,-.88,1.72),(5.06,-.80,1.56),(4.25,-.75,1.42))
    billow=(.16,.90,1.50,2.05,2.45,2.75)
    grid=[];collar_anchors=[]
    for row,(y,z,half_width) in enumerate(rows):
        line=[]
        for column in range(CAPE_COLUMNS+1):
            u=column/CAPE_COLUMNS;s=2*u-1
            point=(s*half_width,y+.10*abs(s),
                z-billow[row]*(1-s*s)**.7+.12*math.sin(s*math.pi*3)*row/CAPE_ROWS)
            slot=2 if row<=2 else 1
            if row==0:
                x=s*half_width;anchor_y=8.23-.25*abs(s)
                for adjust in range(7):
                    try:
                        origin=(x,anchor_y-adjust*.04,-4.)
                        distance,face=a.ray_skin(origin,(0,0,1))
                        break
                    except ValueError:
                        if adjust==6:raise
                skin=add(origin,(0,0,distance));point=add(skin,(0,0,-.07))
                counts={v.slot:sum(q.slot==v.slot for q in face) for v in face}
                slot=max(counts,key=counts.get)
                if slot==3:slot=2
                collar_anchors.append({'column':column,'slot':slot,'skin':skin,'point':point,'back_clearance':.07})
            line.append((slot,point,(129+u*125,1+row/CAPE_ROWS*125)))
        grid.append(line)
    for row in range(CAPE_ROWS):
        for col in range(CAPE_COLUMNS):
            q=(grid[row][col],grid[row+1][col],grid[row+1][col+1],grid[row][col+1])
            for indices_ in ((0,1,2),(0,2,3),(2,1,0),(3,2,0)):
                triangle([(q[i][0],q[i][1]) for i in indices_],[q[i][2] for i in indices_])
    for points,uvs in additions:
        commands.append((0x40,(0,)))
        for (slot,p),(u,v) in zip(points,uvs):
            commands.extend(((0x14,(slot,)),(0x22,(round(u*16)|(round(v*16)<<16),)),vertex(slot,p)))
        commands.append((0x41,()))
    out=bytearray(g.replace_streams([old.packets(commands)],
        vertices=w.u16(raw,g.model+36)+len(additions)*3,quads=w.u16(raw,g.model+38)+len(additions)))
    struct.pack_into('<2H',out,g.model+40,w.u16(raw,g.model+40)+len(additions),w.u16(raw,g.model+42))
    mats=g.model+w.u32(raw,g.model+8);mat=mats+w.u32(dictionary(raw,mats+4,4)[0][1],0)
    struct.pack_into('<2H',out,mat+32,WIDTH,HEIGHT)
    # Expand the native, documented model box for the trailing cape and blades.
    all_points=body_points+[p for points,_ in additions for _,p in points]
    box_scale=w.u32(raw,g.model+56)/4096
    low=[math.floor(min(p[k] for p in all_points)/box_scale*4096)-2 for k in range(3)]
    high=[math.ceil(max(p[k] for p in all_points)/box_scale*4096)+2 for k in range(3)]
    struct.pack_into('<6h',out,g.model+44,*low,*(high[k]-low[k] for k in range(3)))
    rig=AnimationRig.parse(out)
    if (rig.parents,rig.node_records)!=(a.rig.parents,a.rig.node_records):raise ValueError('Sculpt changed native rig/SBC')
    return bytes(out),{'native_body_triangles':480,'added_triangles':len(additions),'total_triangles':480+len(additions),
        'forearm_blades':fin_anchors,'cape':{'width':3.58,'drop':3.93,'rows':CAPE_ROWS,'columns':CAPE_COLUMNS,
        'triangles_double_sided':CAPE_ROWS*CAPE_COLUMNS*4,'anchors':'ray-qualified upper-back skin/chest/pelvis',
        'collar_anchors':collar_anchors,'color':'crimson transparent-index web'},
        'physique':'broader lats/pecs and traps, radial upper-arm/forearm volume, modest thighs; native pivots unchanged',
        'texture_size':[WIDTH,HEIGHT],'native_rig_unchanged':True,'model_box_expanded':True}


def posed_mesh(model,clip,frame):
    """Private pose QA on native animation samples; never writes an SCA."""
    from tools.sca_author import sample
    from tools.rush_choreography import decoded,mm
    rig=AnimationRig.parse(model);_,_,_,slots=old.bind_matrices(model)
    rotations=[];positions=[]
    for j,parent in enumerate(rig.parents):
        r=decoded(clip.rotation(j,frame));t=tuple(v/4096 for v in sample(clip,j,frame,'translation'))
        rotations.append(r if parent is None else mm(rotations[parent],r))
        positions.append(t if parent is None else add(positions[parent],mv(rotations[parent],t)))
    # Keep animation-root motion out of this inspection turntable only.
    origin=positions[1];offset=(origin[0],origin[1]-5.724,origin[2])
    return [tuple(replace(v,position=sub(add(positions[slots[v.slot]],mv(rotations[slots[v.slot]],v.local)),offset)) for v in face)
            for face in old.mesh(model)]
