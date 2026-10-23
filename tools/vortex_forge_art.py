"""Boss-only articulated symbiote foundry armor and a continuous Vortex clip."""
import math
import struct
from tools import creature_forge_art as art
from tools.midnight_finale_art import Sculpt
from tools.creature_forge_design import arms
from tools.rush_choreography import add, mul
from tools.kit_choreography import Clip

SCALE = 1.28


class WarSculpt(Sculpt):
    def face(self, j, tile, verts, uv=((0,0),(0,1),(1,1),(1,0))):
        # Bone positions and mesh offsets receive the same scale as the private
        # SCA translations. Native timing, rotations and gameplay stay intact.
        if j not in (23,27):
            verts=tuple(mul(v,SCALE) for v in verts)
        return super().face(j,tile,verts,uv)

    def __init__(self,template,pose):
        super().__init__(template,pose)
        self.original_p=self.p
        self.p=[mul(v,SCALE) if j not in (23,27) else v for j,v in enumerate(self.p)]


def model(template,pose):
    s=WarSculpt(template,pose);p=s.original_p;steel=6;black=0;flesh=3;edge=13;hot=8
    # Wide, squat engine block with interlocking armor and a soft black waist.
    c=add(p[3],(0,0,-.15))
    s.loft(3,add(c,(0,-1.7,0)),add(c,(0,1.7,0)),
           ((0,1.15,.9),(.3,2.45,1.7),(.8,2.85,1.8),(1,1.8,1.1)),steel,6)
    s.tissue(2,p[1],p[3],1.1,flesh)
    for side in (-1,1):
        # Three overlapping rib plates: metal held together by black tendons.
        for y in (-.9,-.05,.8):
            s.loft(3,add(c,(side*2.25,y,-1.35)),add(c,(side*2.25,y,1.15)),
                   ((0,.32,.38),(.45,.48,.45),(1,.2,.23)),steel,4)
        # Exposed circular turbine on each camera-facing flank.
        center=add(c,(side*2.91,.25,.15))
        for i in range(8):
            a,b=i*math.tau/8,(i+1)*math.tau/8
            q=lambda r,t:add(center,(0,r*math.cos(t),r*math.sin(t)))
            vs=(q(.48,a),q(1.05,a),q(1.05,b),q(.48,b))
            s.face(3,edge,tuple(reversed(vs)) if side>0 else vs)
        s.side_panel(3,add(center,(0,0,0)),.37,.37,hot)
    for side,(a,b,e) in zip((1,-1),arms('brt')):
        # Massive steel pauldrons, separate working elbow and piston forearms.
        s.loft(a,add(p[a],(side*.15,0,0)),add(p[a],(side*1.1,.15,-.7)),
               ((0,1.1,1.0),(.4,1.45,1.3),(1,1.2,1.0)),steel,6)
        s.tissue(a,p[a],p[b],.8,black)
        s.loft(b,p[b],add(p[e],(0,0,.5)),((0,.85,.8),(.35,1.25,1.15),(1,1.0,.9)),steel,6)
        s.loft(b,add(p[b],(side*.9,.15,0)),add(p[e],(side*.9,.15,.1)),((0,.18,.18),(1,.18,.18)),edge,4)
        s.loft(e,add(p[e],(0,0,-.2)),add(p[e],(0,-.25,1.25)),((0,.95,.85),(1,.75,.7)),black,4)
        for z in (.3,1.0):
            s.claw(e,add(p[e],(side*.7,-.1,z)),add(p[e],(side*.85,-.65,z+1.35)),.27,edge)
        # Back-mounted exhaust/cable spines give a distinct rear silhouette.
        start=add(c,(side*1.35,1.15,-1.3))
        s.loft(3,start,add(start,(side*.2,1.65,-1.05)),((0,.42,.4),(1,.35,.32)),steel,5)
        s.claw(3,add(start,(0,.15,0)),add(start,(side*.4,.85,-2.25)),.45,black)
    for a,b,e in ((20,21,22),(24,25,26)):
        s.tissue(a,p[a],p[b],.65,black)
        s.loft(b,p[b],p[e],((0,.7,.65),(.35,.86,.8),(1,.48,.45)),steel,5)
        s.loft(e,add(p[e],(0,0,-.3)),add(p[e],(0,-.15,1.0)),((0,.65,.4),(1,.6,.35)),steel,4)
    # Recessed head, angular metal face and symbiote split jaw/ivory fangs.
    head=add(p[4],(0,.35,.65))
    s.loft(4,add(head,(0,-.75,-.55)),add(head,(0,.9,.25)),((0,.8,.75),(.6,1.05,.95),(1,.65,.5)),black,6)
    for side in (-1,1):
        s.side_panel(4,add(head,(side*1.05,.25,.55)),.16,.65,hot)
        s.loft(19,add(p[19],(side*.65,-.1,-.1)),add(p[19],(side*.75,-.2,1.35)),((0,.32,.35),(1,.23,.2)),steel,4)
        for z in (.35,.9):
            s.claw(19,add(p[19],(side*.73,.17,z)),add(p[19],(side*.73,-.38,z+.15)),.15,2)
    for j in (23,27):s.ring(j,9)
    raw,report=s.finish()
    if report['quads']>600:raise ValueError('War machine exceeds solo boss polygon budget')
    report.update(scale=SCALE,direction='symbiote foundry war machine: turbines, piston gauntlets, rib armor, exhausts and split jaw')
    return raw,report


def direct_texture(model):
    """Boss-only 64px direct RGB555: 8KiB, no shared palette residency."""
    from PIL import Image
    from tools import nitro_build as nb,wos_tool as w
    from tools.spider2099_art import gpu_commands
    from tools.crane_creature_art import packets
    from tools.model_geometry import ModelGeometry
    from tools.nitro_texture import dictionary
    g=ModelGeometry.parse(model);cmds=[]
    for op,args in gpu_commands(model):
        if op==0x22:
            u,v=args[0]&65535,args[0]>>16
            args=(round(u/2)|(round(v/2)<<16),)
        cmds.append((op,args))
    result=bytearray(g.replace_streams([packets(cmds)],vertices=w.u16(model,g.model+36),quads=w.u16(model,g.model+38)))
    mb=g.model+w.u32(model,g.model+8)
    for _,entry in dictionary(result,mb+4,4):
        at=mb+w.u32(entry,0);struct.pack_into('<2H',result,at+32,64,64)
    image=Image.open(art.ATLAS).convert('RGB').resize((64,64),Image.Resampling.LANCZOS)
    pixels=b''.join(struct.pack('<H',0x8000|(r>>3)|((gg>>3)<<5)|((b>>3)<<10)) for r,gg,b in image.getdata())
    texture=nb.texture_archive((nb.Texture('Forge128',64,64,7,pixels),),(nb.Palette('ForgePal',b'\xff\x7f'*16),))
    return bytes(result),texture


VORTEX=Clip('vortex_catapult',19,{
    'root':[(0,(0,3.1,-.3)),(2,(0,3.0,-.7)),(5,(0,4.6,-.1)),(8,(0,5.4,.3)),(11,(0,4.0,.4)),(13,(0,2.65,.5)),(15,(0,2.9,.2)),(18,(0,3.92,-.22))],
    'yaw':[(0,0),(2,-65),(5,-210),(8,-380),(11,-560),(13,-710),(18,-720)],
    'pitch':[(0,16),(3,35),(6,-10),(9,-32),(11,10),(13,54),(16,24),(18,0)],
    'spine_twist':[(0,0),(2,-28),(5,-18),(8,22),(11,34),(13,-18),(18,0)],
    'spine_pitch':[(0,20),(4,8),(8,-24),(11,22),(13,38),(18,0)],
    'head_pitch':[(0,-12),(8,15),(13,-28),(18,0)],
    'hand_l':[(0,(1.4,-.7,2.5)),(2,(2.4,-1.1,2.7)),(5,(2.5,.5,-.8)),(8,(1.6,2.6,-.5)),(10,(1.2,3.0,.8)),(12,(.6,.6,3.2)),(13,(.8,-3.2,2.3)),(15,(1.3,-2.5,1.9)),(18,(1.5,-.2,1.7))],
    'hand_r':[(0,(-1.4,-.7,2.5)),(2,(-1.7,-.5,2.9)),(5,(-2.5,1.0,-.5)),(8,(-1.2,2.9,-.4)),(10,(-1.1,3.2,.8)),(12,(-.6,.7,3.2)),(13,(-.8,-3.2,2.3)),(15,(-1.6,-.7,.3)),(18,(-1.5,-.2,1.7))],
    'foot_l':[(0,(1.5,-2.6,1.4)),(3,(1.4,-2.6,1.1)),(6,(1.1,-2.1,1.7)),(9,(1.1,-2.2,-.9)),(12,(1.8,-2.4,1.5)),(13,(1.9,-1.9,1.4)),(18,(1.1,-3.1,1.2))],
    'foot_r':[(0,(-1.5,-2.6,-1.0)),(3,(-1.4,-2.7,-1.2)),(6,(-1.1,-2.2,-1.8)),(9,(-1.1,-1.8,1.5)),(12,(-1.7,-2.4,-1)),(13,(-1.7,-1.8,-1.1)),(18,(-1.1,-3.1,-1))],
    'point_l':[(0,0),(6,.7),(10,.8),(13,0)],'point_r':[(0,0),(6,.7),(10,.8),(13,0)],
})
