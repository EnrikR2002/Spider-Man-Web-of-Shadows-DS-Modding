"""UV-painted, articulated creature meshes; one shared128px material atlas.

Lofted shells, beveled armor, split blades and actual joint chains replace the
previous colour-sampled ellipsoids. Native hurt/death material tint survives.
"""
import math,struct
from pathlib import Path
from tools import nitro_build as nb,wos_tool as w
from tools.model_geometry import ModelGeometry
from tools.animation_rig import AnimationRig
from tools.crane_creature_art import packets
from tools.rush_choreography import add,sub,mul,unit,cross,mv,transpose
from tools.creature_forge_design import arms

ROOT=Path(__file__).resolve().parents[1]
ATLAS=ROOT/'reference/art/creature-forge-materials-v1.png'
TEXNAME='Forge128';PALNAME='ForgePal'

def texture():
    from PIL import Image
    im=Image.open(ATLAS).convert('RGB').resize((128,128),Image.Resampling.LANCZOS)
    data=b''.join(struct.pack('<H',0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)) for r,g,b in im.getdata())
    return nb.texture_archive((nb.Texture(TEXNAME,128,128,7,data),),(nb.Palette(PALNAME,b'\xff\x7f'*16),))

class Sculpt:
    def __init__(self,template,pose):
        self.template=template;self.model=ModelGeometry.parse(template);self.rig=AnimationRig.parse(template)
        self.r,self.p=pose.fk();self.slots={a[0]:a[3] for _,op,a in self.rig.node_records if op in (0x26,0x66)};self.groups={}
    def face(self,j,tile,verts,uv=((0,0),(0,1),(1,1),(1,0))):
        if j not in self.slots:
            if j==4 and 5 in self.slots:j=5
            else:
                while j not in self.slots:j=self.rig.parents[j]
        inv=transpose(self.r[j]);verts=tuple(mv(inv,sub(v,self.p[j])) for v in verts)
        self.groups.setdefault(self.slots[j],[]).append((tile,verts,uv))
    def loft(self,j,a,b,radii,tile,sides=6):
        """Continuous section profiles with shared edges and continuous UVs."""
        d=unit(sub(b,a));u=unit(cross(d,(0,1,0) if abs(d[1])<.9 else (0,0,1)));v=cross(u,d)
        def pt(k,i):
            f,rx,ry=radii[k];c=add(a,mul(sub(b,a),f));theta=2*math.pi*i/sides
            return add(c,add(mul(u,rx*math.cos(theta)),mul(v,ry*math.sin(theta))))
        for k in range(len(radii)-1):
            for i in range(sides):
                self.face(j,tile,(pt(k,i),pt(k+1,i),pt(k+1,i+1),pt(k,i+1)),
                    ((i/sides,radii[k][0]),(i/sides,radii[k+1][0]),((i+1)/sides,radii[k+1][0]),((i+1)/sides,radii[k][0])))
        # Collapsed quad caps are legal in the native DS quad primitive.
        for k in (0,len(radii)-1):
            c=add(a,mul(sub(b,a),radii[k][0]))
            for i in range(0,sides,2):self.face(j,tile,(pt(k,i),pt(k,i+1),pt(k,i+2),c))
    def limb(self,j,a,b,r,tile):
        self.loft(j,a,b,((0,r*.65,r*.65),(.35,r,r*.86),(1,r*.45,r*.45)),tile,4)
    def blade(self,j,a,b,width,tile=2,curve=(0,0,0)):
        mid=add(add(a,mul(sub(b,a),.62)),curve)
        d=unit(sub(b,a));u=unit(cross(d,(0,1,0) if abs(d[1])<.85 else (0,0,1)))
        v=cross(u,d)
        ring=[add(a,mul(u,-width)),add(mid,mul(u,-width*.65)),b,add(mid,mul(u,width*.65)),add(a,mul(u,width))]
        ridge=add(mid,mul(v,width*.3))
        for i in range(len(ring)):
            self.face(j,tile,(ring[i],ring[(i+1)%len(ring)],ridge,ridge))
    def panel(self,j,c,size,tile,bevel=.18):
        x,y,z=size
        back=[add(c,v) for v in ((-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z))]
        front=[add(c,v) for v in ((-x+bevel,-y+bevel,z),(x-bevel,-y+bevel,z),(x-bevel,y-bevel,z),(-x+bevel,y-bevel,z))]
        self.face(j,tile,front)
        for i in range(4):self.face(j,tile,(back[i],back[(i+1)%4],front[(i+1)%4],front[i]))
    def side_panel(self,j,c,half_y,half_z,tile):
        # The game camera sees Y/Z. Eyes and weak-point lights must read in
        # that plane, not only on a creature's forward-facing chest surface.
        self.face(j,tile,tuple(add(c,v) for v in ((0,-half_y,-half_z),(0,-half_y,half_z),(0,half_y,half_z),(0,half_y,-half_z))))
    def ring(self,j,tile):
        # Three-dimensional jagged energy annulus, scales on a spare toe bone.
        for i in range(8):
            a,b=i*math.tau/8,(i+1)*math.tau/8
            p=lambda r,t: (r*math.cos(t),.12 if r>1.8 else 0.,r*math.sin(t))
            # Bind at the effect joint's canonical world pose.
            vs=tuple(add(self.p[j],q) for q in (p(1.62,a),p(2.,a),p(2.,b),p(1.62,b)))
            self.face(j,tile,vs)
    def finish(self):
        cmds=[];count=0
        for slot,faces in self.groups.items():
            cmds.extend(((0x14,(slot,)),(0x40,(1,))))
            for tile,verts,uvs in faces:
                for p,(u,v) in zip(verts,uvs):
                    # Half-texel inset prevents atlas bleeding on hardware.
                    s=(tile%4*32+1+u*30)*16;t=(tile//4*32+1+v*30)*16
                    cmds.append((0x22,(round(s)|(round(t)<<16),)))
                    x,y,z=(round(q*4096) for q in p)
                    if any(not -32768<=q<32768 for q in (x,y,z)):raise ValueError('Bone-local forge vertex exceeds Q12: '+str(p))
                    cmds.append((0x23,((x&65535)|(y&65535)<<16,z&65535)))
                count+=1
            cmds.append((0x41,()))
        out=bytearray(self.model.replace_streams([packets(cmds)],vertices=count*4,quads=count))
        mat=self.model.model+w.u32(self.template,self.model.model+8)
        from tools.nitro_texture import dictionary
        for _,e in dictionary(out,mat+4,4):
            at=mat+w.u32(e,0);struct.pack_into('<III',out,at+4,0xffff,0,0x001f00c0)
        for field,name in ((0,TEXNAME),(2,PALNAME)):
            at=mat+w.u16(out,mat+field)
            if out[at+1]:
                if out[at+1]!=1:raise ValueError('Expected a single creature material')
                size=w.u16(out,at+2);rows=dictionary(out,at,4)
                replacement=nb.dictionary_bytes(((name,rows[0][1]),))
                if len(replacement)!=size:raise ValueError('Material dictionary framing changed')
                out[at:at+size]=replacement
        ModelGeometry.parse(out)
        if AnimationRig.parse(out).parents!=self.rig.parents:raise ValueError('Forge changed the bind rig')
        return bytes(out),dict(quads=count,vertices=count*4,stored_matrices=len(self.groups),shared_texture=TEXNAME)

def model(style,stem,template,pose,*,sculpt_type=Sculpt):
    s=sculpt_type(template,pose);p=s.p;arm=arms(stem);front=style in ('maw','skitter');heavy=stem=='brt'
    skin=3 if style in ('maw','ballast','spore') else 15
    shell={'maw':1,'ballast':4,'spore':0,'skitter':6,'warden':12,'eye':6,'conductor':5}[style]
    glow=8 if style in ('maw','ballast') else 10 if style=='spore' else 9
    # Four real articulated chains. Armor is split at joints, without rigid
    # decorative legs following the torso as in the earlier Skitter.
    for i,(u,l,e) in enumerate((*arm,(20,21,22),(24,25,26))):
        hand=i<2;r=(.63 if heavy else .25) if hand else .4 if heavy else .23
        s.limb(u,p[u],p[l],r,skin);s.limb(l,p[l],p[e],r*1.1,shell)
        if hand and heavy:
            size=(.82,1.0,.85) if style=='ballast' else (.55,1.15,.55)
            s.panel(e,add(p[e],(0,-.1,.25)),size,shell)
        for q in (-1,1):
            a=add(p[e],(q*(.4 if heavy else .2),-.12,.2))
            b=add(a,(q*.15,-.3,(2.0 if front else 1.0) if hand else .75))
            digit=e+1 if hand else e
            s.blade(digit,a,b,.24 if heavy else .15,13 if style in ('skitter','eye') else 2)
    if front:
        # Low predatory carapace with a long taper and a split jaw.
        c=add(p[3],(0,-.1,-.3))
        rail=style=='skitter'
        s.loft(3,add(c,(0,.1,-2.5 if rail else -1.9)),add(c,(0,.1,1.0 if rail else 1.3)),
               ((0,.25,.35),(.25,1.15 if rail else 1.35,.6 if rail else .8),(.66,1.25 if rail else 1.6,.85 if rail else 1.0),(1,.9 if rail else 1.,.65)),shell,7)
        s.loft(1,add(p[1],(0,.1,-2.6)),add(p[1],(0,.1,.5)),((0,.12,.18),(.6,1.0,.65),(1,.9,.6)),skin,6)
        head=add(p[5],(0,-.15,.55))
        s.loft(5,add(head,(0,0,-.7)),add(head,(0,0,1.5)),((0,.8,.6),(.65,1.05,.5),(1,.35,.25)),shell,6)
        s.panel(5,add(head,(0,.18,1.35)),(.7,.16,.06),glow,.04)
        for side in (-1,1):s.side_panel(5,add(head,(side*.92,.2,.7)),.18,.45,glow)
        for side in (-1,1):
            for z,y in (((-1.2,.8),(.7,1.0)) if rail else ((-1.1,.8),(.2,1.),(1.,.7))):
                a=add(c,(side*1.0,y,z));s.blade(3,a,add(a,(side*.7,1.9 if rail else .9,-1.2 if rail else -1.0)),.32 if rail else .36,shell)
            e=arm[0 if side==1 else 1][2]
            # Scythes belong to wrists, so the attacks actually sweep the blades.
            a=add(p[e],(side*.25,.2,0));s.blade(e,a,add(a,(side*.1,.6 if rail else 1.4,3.8 if rail else 3.0)),.48 if rail else .65,13 if rail else 2,(0,-.8 if rail else -.5,1.0 if rail else .7))
            s.blade(19,add(head,(side*.7,-.35,.9)),add(head,(side*.9,-.8,2.2)),.22,2)
        s.loft(19,add(head,(0,-.4,.7)),add(head,(0,-.5,1.8)),((0,.7,.23),(.5,.85,.3),(1,.3,.1)),0,4)
        if rail:
            for side in (-1,1):
                a=add(p[1],(side*.55,.2,-1.1));s.blade(1,a,add(a,(side*.7,1.5,-3.1)),.45,6)
            s.blade(1,add(p[1],(0,.3,-1.4)),add(p[1],(0,1.4,-4.4)),.5,13)
    elif heavy:
        c=add(p[3],(0,0,-.2));boss=style=='conductor'
        # Broad shoulders, a narrow articulated waist, layered breast plates.
        s.loft(3,add(c,(0,-1.4,0)),add(c,(0,1.5,0)),((0,1.1,1.0),(.36,2.05,1.35),(.83,2.6 if not boss else 2.9,1.5),(1,1.9,1.0)),shell,8)
        s.loft(2,add(p[2],(0,-.7,0)),add(p[2],(0,.7,0)),((0,1.,.8),(.5,1.25,1.0),(1,1.1,.8)),skin,6)
        s.panel(3,add(c,(0,.1,1.42)),(.6,.85,.12),glow,.15)
        for side in (-1,1):s.side_panel(3,add(c,(side*2.1,.1,.25)),.7,.55,glow)
        head=add(p[4],(0,.3,.55))
        s.panel(4,head,(.85,1.05,.7),6 if style!='ballast' else 0)
        s.panel(4,add(head,(0,.18,.76)),(.65,.16,.04),glow,.025)
        for side in (-1,1):s.side_panel(4,add(head,(side*.86,.2,.18)),.15,.55,glow)
        s.panel(19,add(p[19],(0,-.05,.2)),(.65,.23,.5),0 if style=='ballast' else 5,.08)
        for side in (-1,1):
            shoulder=arm[0 if side==1 else 1][0]
            s.panel(shoulder,add(p[shoulder],(side*.2,.35,0)),(.8,.6,.85),shell)
            if style=='ballast':
                e=arm[0 if side==1 else 1][2]
                s.blade(e,add(p[e],(side*.6,.4,0)),add(p[e],(side*1.2,.1,2.2)),.8,4)
            else:
                # Split bell mantle on independent scapulae, visibly swings.
                j=5 if side==1 else 12
                a=add(c,(side*1.6,.9,-.2));b=add(c,(side*2.4,-2.,.1))
                s.loft(j,a,b,((0,.5,.65),(.6,.65,.85),(1,.95,1.0)),12,5)
        if boss:
            # A broken, asymmetric crown with a central negative space.
            for i in range(7):
                a=math.pi*.12+i*math.pi*.125;b=a+math.pi*.10
                q=lambda t: add(head,(3.3*math.cos(t),3.3*math.sin(t),-.9))
                s.limb(4,q(a),q(b),.22,5)
                if i%2==0:s.blade(4,q(a),add(q(a),(math.cos(a)*1.,math.sin(a)*1.,0)),.3,9)
            for side,j in ((1,5),(-1,12)):
                for z in (-.8,.4):
                    a=add(c,(side*2,1,z));s.blade(j,a,add(a,(side*1.9,-4.3,-.6)),.75,6)
    else:
        # Spore is an armored seed lantern; Eye is an open ceramic aperture.
        c=add(p[3],(0,.35,.1));eye=style=='eye'
        s.loft(3,add(c,(0,-1.4,0)),add(c,(0,1.6,0)),((0,.65,.65),(.35,1.25 if eye else 1.9,.9 if eye else 1.35),(.7,1.1 if eye else 1.7,.8 if eye else 1.1),(1,.5,.5)),shell,8)
        s.loft(5,add(p[5],(0,-.6,.5)),add(p[5],(0,.8,.5)),((0,.45 if eye else .6,.4 if eye else .5),(.5,.72 if eye else 1.05,.55 if eye else .8),(1,.45 if eye else .6,.4 if eye else .5)),glow,8)
        for side in (-1,1):s.side_panel(5,add(p[5],(side*1.06,.1,.5)),.6,.55,glow)
        for side,(u,l,e) in zip((1,-1),arm):
            # Long articulated petals are carried by upper arms and forearms.
            s.blade(u,add(p[u],(side*.3,0,-.2)),add(p[l],(side*.8,1.8,-.7)),.65,shell)
            s.blade(l,add(p[l],(side*.2,0,0)),add(p[e],(side*.7,-.7,1.4)),.55,13 if eye else 2)
        for side in (-1,1):
            s.blade(5,add(p[5],(side*.7,.4,.1)),add(p[5],(side*1.8,2.4,-.7)),.4,6 if eye else 0)
        if eye:
            # Aperture with an empty dark center, bright narrow iris.
            h=add(p[5],(0,.15,.5))
            for i in range(12):
                a,b=i*math.tau/12,(i+1)*math.tau/12
                q=lambda r,t:add(h,(0,r*math.cos(t),r*math.sin(t)))
                s.face(5,6,(q(1.05,a),q(2.2,a),q(2.2,b),q(1.05,b)))
    # All species carry the same two small effect meshes, fully hidden in idle.
    # Their independent translation/scale tracks animate pulses, bolts or arcs.
    for j in (23,27):s.ring(j,glow)
    return s.finish()
