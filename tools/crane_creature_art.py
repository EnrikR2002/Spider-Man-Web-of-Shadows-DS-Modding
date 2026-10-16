"""Original creature geometry on preserved native28-bone animation rigs."""
import math,struct,sys
from pathlib import Path
sys.path.insert(0,'.')
from tools import wos_tool as w,nitro_build as nb
from tools.model_geometry import ModelGeometry
from tools.animation_rig import AnimationRig
from tools.nitro_texture import dictionary,TextureArchive
from tools.sca import Sca
from tools.sca_author import sample
from tools.rush_choreography import Pose as NativePose,decoded,transpose,mv,sub,add,mul,cross,unit

class Pose(NativePose):
    def __init__(self,idle,parents):
        assert idle.joint_count==len(parents)
        self.parents=parents
        self.r=[decoded(idle.rotation(j,0)) for j in range(idle.joint_count)]
        self.t=[tuple(v/4096 for v in sample(idle,j,0,'translation')) for j in range(idle.joint_count)]

def rgb(r,g,b):return r|g<<5|b<<10
DARK=rgb(5,9,12);SHELL=rgb(15,20,22);RUST=rgb(24,12,5);BONE=rgb(27,26,18);GLOW=rgb(5,31,26)

def ellipsoid(c,r,colour,sides=8,rings=4):
    faces=[]
    def point(i,j):
        theta=2*math.pi*i/sides;phi=.05+(math.pi-.1)*j/rings
        return add(c,(r[0]*math.sin(phi)*math.cos(theta),r[1]*math.cos(phi),r[2]*math.sin(phi)*math.sin(theta)))
    for j in range(rings):
        for i in range(sides):
            # Outward normals; mild per-face shade gives facets, not flat boxes.
            shade=.68+.32*max(0,math.cos(2*math.pi*(i+.5)/sides-1))
            cs=tuple(round(((colour>>(5*n))&31)*shade) for n in range(3))
            faces.append((rgb(*cs),(point(i,j),point(i,j+1),point(i+1,j+1),point(i+1,j))))
    return faces

def tube(a,b,r0,r1,colour,sides=6):
    direction=unit(sub(b,a));v=unit(cross(direction,(0,1,0) if abs(direction[1])<.9 else (0,0,1)));u=cross(v,direction)
    def pt(c,r,i):return add(c,add(mul(u,r*math.cos(2*math.pi*i/sides)),mul(v,r*math.sin(2*math.pi*i/sides))))
    return [(colour,(pt(a,r0,i),pt(a,r0,i+1),pt(b,r1,i+1),pt(b,r1,i))) for i in range(sides)]

def packets(commands):
    commands=list(commands)+[(0,())]*(-len(commands)%4);data=bytearray()
    for p in range(0,len(commands),4):
        block=commands[p:p+4];data.extend(bytes(op for op,_ in block))
        for _,args in block:
            if args:data.extend(struct.pack('<'+'I'*len(args),*args))
    return bytes(data)

def mesh_stream(groups,colour_slots=None,width=64):
    cmds=[];count=0
    for slot,faces in groups.items():
        cmds.extend(((0x14,(slot,)),(0x40,(1,))))
        for colour,vertices in faces:
            # The engine sets COLOR from the material, including its damage /
            # death override. A COLOR in the display list masks that feedback.
            # Put the authored face colour in the texture instead.
            slot=colour_slots[colour] if colour_slots is not None else 0
            cmds.append((0x22,((slot%width*16+8)|((slot//width*16+8)<<16),)))
            for p in vertices:
                x,y,z=(round(v*4096) for v in p)
                if any(not -32768<=v<32768 for v in (x,y,z)):raise ValueError('Bone-local vertex outside Q12 range')
                cmds.append((0x23,((x&65535)|(y&65535)<<16,z&65535)))
            count+=1
        cmds.append((0x41,()))
    return packets(cmds),count

def colour_atlas(groups,textures):
    colours=sorted({colour for faces in groups.values() for colour,_ in faces})
    if any(len(colours)>t['width']*t['height'] for t in textures):raise ValueError('Creature colour atlas overflow')
    slots={c:i for i,c in enumerate(colours)}
    out=tuple(nb.Texture(t['name'],t['width'],t['height'],7,
        b''.join(struct.pack('<H',c|0x8000) for c in colours)+b'\xff\xff'*(t['width']*t['height']-len(colours))) for t in textures)
    return slots,out

def ballast(template,idle_raw,pose=None):
    model=ModelGeometry.parse(template);rig=AnimationRig.parse(template);pose=pose or Pose(Sca.parse(idle_raw),rig.parents)
    if len(rig.names)!=28 or len(model.shapes)!=1:raise ValueError('Expected28-bone Brute chassis')
    rotations,positions=pose.fk();slots={}
    for _,op,args in rig.node_records:
        if op in (0x26,0x66):slots[args[0]]=args[3]
    groups={}
    def bind(j,faces):
        inverse=transpose(rotations[j])
        groups.setdefault(slots[j],[]).extend((col,tuple(mv(inverse,sub(v,positions[j])) for v in vertices)) for col,vertices in faces)
    torso=add(positions[3],(0,-.3,-.3))
    bind(3,ellipsoid(torso,(2.7,1.7,2.5),SHELL))
    bind(2,ellipsoid(add(positions[2],(0,.2,-.4)),(1.9,1.4,1.5),DARK))
    # Split hammerhead, luminous eyes and a jagged tooth-lined maw.
    head=add(positions[4],(0,-.1,.6))
    bind(4,ellipsoid(head,(1.6,.9,1.25),DARK,rings=3))
    for side in (-1,1):
        bind(4,ellipsoid(add(head,(side*.9,.15,.96)),(.36,.22,.18),GLOW,sides=6,rings=3))
        bind(4,tube(add(head,(side*.7,-.4,.8)),add(head,(side*1.1,-.7,2.0)),.24,.025,BONE))
    # Asymmetric forelimbs, hooked claws, rear legs and pointed feet.
    for upper,lower,end,side in ((6,7,8,1),(13,14,15,-1),(20,21,22,1),(24,25,26,-1)):
        arm=upper in (6,13);radius=.75 if arm and side==-1 else .5 if arm else .58
        bind(upper,tube(positions[upper],positions[lower],radius,radius*.75,DARK))
        bind(lower,tube(positions[lower],positions[end],radius*1.15,radius*.85,SHELL))
        bind(end,ellipsoid(positions[end],(radius*1.5,radius*1.2,radius*1.4),RUST,sides=6,rings=3))
        for n in (-1,1):
            root=add(positions[end],(n*.35,-.12,.2))
            bind(end,tube(root,add(root,(n*.1,-.3,1.35 if arm else 1.0)),.19,.025,BONE,sides=5))
    # Barnacle-like ballast plates and a distinct backward-fanning silhouette.
    for side in (-1,1):
        for y,z in ((.3,-1.2),(1.2,-.9),(1.8,-.2)):
            a=add(torso,(side*1.65,y,z));b=add(a,(side*1.25,.8,-1.1))
            bind(3,tube(a,b,.45,.03,RUST,sides=5))
    # A forked, anchored tail breaks the native humanoid silhouette.
    tail=add(positions[1],(0,.3,-.6))
    for end in ((0,3.5,-2.7),(0,3.0,-4.5)):
        bind(1,tube(tail,end,.5,.25,DARK));tail=end
    for side in (-1,1):bind(1,tube(tail,add(tail,(side*1.0,.3,-.6)),.25,.025,BONE,sides=5))
    slots,textures=colour_atlas(groups,({'name':'Brute64','width':64,'height':64},))
    stream,count=mesh_stream(groups,slots,64)
    result=bytearray(model.replace_streams([stream],vertices=count*4,quads=count))
    mat=model.model+w.u32(template,model.model+8)
    for _,entry in dictionary(template,mat+4,4):
        at=mat+w.u32(entry,0)
        struct.pack_into('<I',result,at+4,0x0000FFFF)
        struct.pack_into('<I',result,at+8,0)
        struct.pack_into('<I',result,at+12,0x001F00C0)
    tex=nb.texture_archive(textures,
                          (nb.Palette('Brute64_pl',b'\xff\x7f'*16),))
    ModelGeometry.parse(result)
    return bytes(result),tex,{'quads':count,'joints':len(rig.names),'slots':sorted(groups)}

def _writer(template,pose):
    model=ModelGeometry.parse(template);rig=AnimationRig.parse(template)
    if len(rig.names)!=28 or len(model.shapes)!=1:raise ValueError('Expected one-shape28-bone creature chassis')
    rotations,positions=pose.fk();slots={args[0]:args[3] for _,op,args in rig.node_records if op in (0x26,0x66)}
    groups={}
    def bind(j,faces):
        # Some native rigs omit an unused intermediate matrix (Maw spine2,
        # Spore neck4). Use the stored head child or nearest stored ancestor;
        # vertices are converted through that exact matrix, not a guessed slot.
        if j not in slots:
            if j==4 and 5 in slots and rig.parents[5]==4:j=5
            else:
                while j not in slots:
                    j=rig.parents[j]
                    if j is None:raise ValueError('No stored matrix for authored geometry')
        inv=transpose(rotations[j])
        groups.setdefault(slots[j],[]).extend((col,tuple(mv(inv,sub(v,positions[j])) for v in vertices)) for col,vertices in faces)
    return model,positions,groups,bind

def _finish(template,texture,model,groups):
    old=TextureArchive.parse(texture)
    slots,textures=colour_atlas(groups,old.textures)
    widths={t['width'] for t in old.textures}
    if len(widths)!=1:raise ValueError('Creature atlas needs matching texture widths')
    stream,count=mesh_stream(groups,slots,next(iter(widths)))
    result=bytearray(model.replace_streams([stream],vertices=count*4,quads=count))
    mat=model.model+w.u32(template,model.model+8)
    for _,entry in dictionary(template,mat+4,4):
        at=mat+w.u32(entry,0)
        struct.pack_into('<III',result,at+4,0xFFFF,0,0x001F00C0)
    palettes=(nb.Palette('CreatureWhite',b'\xff\x7f'*16),)
    tex=nb.texture_archive(textures,palettes)
    newrig=AnimationRig.parse(result);oldrig=AnimationRig.parse(template)
    if newrig.names!=oldrig.names or newrig.parents!=oldrig.parents:raise ValueError('Authored geometry changed the rig')
    return bytes(result),tex,{'quads':count,'joints':len(newrig.names),'slots':sorted(groups)}

def maw(template,texture,pose):
    model,p,groups,bind=_writer(template,pose)
    skin=rgb(4,7,9);plate=rgb(15,4,6);eyes=rgb(31,22,4)
    body=add(p[3],(0,-.4,-.25));head=add(p[4],(0,-.4,.7))
    bind(3,ellipsoid(body,(1.65,1.15,2.0),plate,rings=3))
    bind(2,ellipsoid(add(p[2],(0,-.2,-.4)),(1.4,.95,1.5),skin,rings=2))
    bind(4,ellipsoid(head,(1.25,.8,1.15),skin,rings=2))
    for side in (-1,1):
        for yy,xx in ((.25,.75),(.55,.45)):
            bind(4,ellipsoid(add(head,(side*xx,yy,.9)),(.22,.18,.17),eyes,sides=4,rings=2))
        for yy in (-.3,.3):
            a=add(head,(side*.8,yy,.8));b=add(a,(-side*.15,-yy*.9,1.2))
            bind(4,tube(a,b,.22,.025,BONE,sides=4))
    for upper,lower,end in ((6,7,8),(13,14,15),(20,21,22),(24,25,26)):
        front=upper in (6,13)
        bind(upper,tube(p[upper],p[lower],.3,.25,skin,sides=5))
        bind(lower,tube(p[lower],p[end],.32,.16,plate,sides=5))
        for side in (-1,1):
            a=add(p[end],(side*.25,0,.1));b=add(a,(side*.13,-.12,1.1 if front else .7))
            bind(end,tube(a,b,.18,.02,BONE,sides=5))
    for side in (-1,1):
        for yy,zz in ((.3,-1.0),(.7,-.2),(1.0,.5)):
            a=add(body,(side*1.1,yy,zz));bind(3,tube(a,add(a,(side*.8,.6,-.5)),.3,.02,plate,sides=4))
    tail=add(p[1],(0,.25,-.4))
    for end in ((0,3,-2.6),(0,2.7,-4.0)):
        bind(1,tube(tail,end,.35,.15,skin,sides=4));tail=end
    bind(1,tube(tail,add(tail,(0,.8,-.8)),.2,.02,BONE,sides=4))
    return _finish(template,texture,model,groups)

def spore(template,texture,pose):
    model,p,groups,bind=_writer(template,pose)
    skin=rgb(4,13,13);frill=rgb(8,18,16);core=rgb(21,31,10)
    centre=add(p[1],(0,1.5,.3));mouth=add(centre,(0,-.2,1.8))
    bind(3,ellipsoid(centre,(2.25,2.25,1.8),skin,sides=10,rings=3))
    bind(4,ellipsoid(add(centre,(0,1.0,-.1)),(3.1,1.4,2.1),frill,sides=8,rings=3))
    bind(4,ellipsoid(mouth,(1.05,.85,.3),DARK,sides=8,rings=3))
    bind(4,ellipsoid(add(mouth,(0,0,.2)),(.7,.6,.2),core,sides=8,rings=3))
    for upper,lower,end in ((6,7,8),(13,14,15),(20,21,22),(24,25,26)):
        bind(upper,tube(p[upper],p[lower],.24,.2,frill))
        bind(lower,tube(p[lower],p[end],.2,.07,skin))
        bind(end,tube(p[end],add(p[end],(0,-.7,.2)),.12,.02,BONE,sides=5))
    for side in (-1,1):
        for z in (-.8,.8):
            a=add(centre,(side*1.8,-.8,z));b=add(a,(side*.4,-1.4,-.3));c=add(b,(-side*.2,-1.0,.8))
            bind(3,tube(a,b,.19,.12,frill));bind(3,tube(b,c,.12,.02,skin))
    return _finish(template,texture,model,groups)
