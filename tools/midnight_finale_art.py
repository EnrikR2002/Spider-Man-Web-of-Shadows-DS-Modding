"""Closed, broad creature anatomy designed for the DS side camera.

Uses the established painted atlas and rig; no new bitmap or texture allocation.
Large connected volumes replace the crown/shard clutter of the older mesh.
"""
import math
from tools import creature_forge_art as art
from tools.chapter_spectacle_art import ReadableSculpt
from tools.creature_forge_design import arms
from tools.rush_choreography import add,sub,mul


class Sculpt(ReadableSculpt):
    def face(self,j,tile,verts,uv=((0,0),(0,1),(1,1),(1,0))):
        # Broad painted regions, without repeatedly tiling the swatch's border
        # onto each tiny polygon. All ordinary hurt/death tint stays native.
        uv=tuple((.16+.68*u,.18+.64*v) for u,v in uv)
        return super().face(j,tile,verts,uv)

    def tissue(self,j,a,b,r,tile):
        return art.Sculpt.loft(self,j,a,b,((0,r*.62,r*.58),(.44,r,r*.86),(1,r*.52,r*.46)),tile,4)

    def claw(self,j,a,b,width,tile):
        return art.Sculpt.loft(self,j,a,b,((0,width*.7,width*.55),(.45,width,width*.65),(1,.015,.015)),tile,3)


def model(style,stem,template,pose):
    s=Sculpt(template,pose);p=s.p;arm=arms(stem);boss=style=='conductor';front=style=='skitter';heavy=stem=='brt'
    shell={'conductor':0,'skitter':0,'warden':6,'eye':6}[style];skin=3;glow=9;edge=13
    # The joints remain exposed between tapered muscle/shell groups. Hands and
    # feet have a short palm and readable hooked digits instead of square pads.
    for i,(a,b,e) in enumerate((*arm,(20,21,22),(24,25,26))):
        hand=i<2;r=(.66 if boss else .62 if heavy else .38) if hand else .50 if heavy else .31
        s.tissue(a,p[a],p[b],r,skin)
        s.tissue(b,p[b],p[e],r*(1.2 if hand else .85),shell)
        palm=add(p[e],(0,-.15,.65 if hand else .25))
        art.Sculpt.loft(s,e,p[e],palm,((0,r*.8,r*.7),(1,r*.5,r*.4)),skin,4)
        for q in ((-1,1) if hand else (0,)):
            a0=add(palm,(q*(.3 if heavy else .23),0,0))
            s.claw(e,a0,add(a0,(q*.18,-.25,1.7 if hand and boss else 1.15 if hand else .7)),.18 if heavy else .14,edge)
    c=add(p[3],(0,0,-.15))
    if front:
        # Smooth narrow thorax and a backward taper; two working scythes are
        # enough to identify Skitter without a forest of decorative spikes.
        art.Sculpt.loft(s,3,add(c,(0,.1,-2.2)),add(c,(0,.1,1.1)),
            ((0,.35,.4),(.2,1.0,.66),(.58,1.35,.92),(.86,1.15,.78),(1,.65,.4)),shell,6)
        s.tissue(1,add(p[1],(0,.1,-2.0)),p[2],.85,skin)
        for side,(a,b,e) in zip((1,-1),arm):
            start=add(p[e],(side*.22,.1,.6))
            s.claw(e,start,add(start,(side*.15,.75,3.0)),.45,edge)
        head=add(p[5],(0,-.1,.65));hj=5
        art.Sculpt.loft(s,hj,add(head,(0,0,-.65)),add(head,(0,0,1.3)),((0,.7,.5),(.35,1.,.7),(.72,.85,.5),(1,.35,.27)),shell,6)
    elif heavy:
        # Articulated waist, ribcage and deltoids. Boss shoulder mass is swept
        # backward; Warden retains a broad upright plated bell silhouette.
        art.Sculpt.loft(s,3,add(c,(0,-1.5,0)),add(c,(0,1.65,0)),
            ((0,1.05,.85),(.2,1.5,1.05),(.58,2.3 if boss else 2.45,1.45),(.86,2.55 if boss else 2.6,1.4),(1,1.65,.85)),shell,6)
        s.tissue(2,add(p[2],(0,-.65,0)),add(p[2],(0,.7,0)),1.05,skin)
        s.tissue(1,add(p[1],(0,-.45,0)),add(p[1],(0,.55,0)),1.05,shell)
        for side,(a,b,e) in zip((1,-1),arm):
            s.tissue(a,add(p[a],(side*.1,.2,-.25)),add(p[a],(side*.6,.2,-.8)),.95,shell)
            # Organic shoulder fin and a curved wrist edge carry the boss's
            # identity through turns; no floating crown or rigid hanging shards.
            if boss:
                s.claw(a,add(p[a],(side*.3,.5,-.4)),add(p[a],(side*1.15,1.2,-2.3)),.48,shell)
                s.claw(b,add(p[b],(side*.25,0,0)),add(p[e],(side*.4,.25,2.2)),.46,shell)
            else:
                s.tissue(a,add(p[a],(side*.25,.6,-.3)),add(p[a],(side*.35,-1.3,-.2)),.9,6)
        head=add(p[4],(0,.25,.55));hj=4
        art.Sculpt.loft(s,hj,add(head,(0,-.85,-.4)),add(head,(0,.75,.45)),
            ((0,.5,.55),(.25,.83,.72),(.65,.9,.78),(.9,.7,.5),(1,.32,.25)),shell,6)
        # Two cyan gill/rib cuts on each visible side, rather than a large
        # rectangular glowing badge. Their surrounding dark volume stays clear.
        for side in (-1,1):
            for y,z in ((.35,.35),(-.25,.5)):
                s.side_panel(3,add(c,(side*1.85,y,z)),.095,.60 if boss else .42,glow)
    else:
        # Eye: an open, rounded aperture inside four articulated petals.
        s.tissue(2,add(p[2],(0,-.6,0)),add(p[3],(0,.6,0)),.75,skin)
        art.Sculpt.loft(s,3,add(c,(0,-1.15,0)),add(c,(0,1.4,0)),((0,.55,.5),(.35,1.1,.85),(.7,1.1,.85),(1,.5,.5)),shell,6)
        head=add(p[5],(0,.2,.45));hj=5
        for side,(a,b,e) in zip((1,-1),arm):
            s.claw(a,add(p[a],(side*.15,.2,0)),add(p[b],(side*.55,1.6,-.3)),.48,shell)
            s.claw(b,add(p[b],(side*.15,0,0)),add(p[e],(side*.45,-.4,.9)),.43,shell)
        for side in (-1,1):
            cx=head[0]+side*1.1
            for i in range(10):
                a,b=i*math.tau/10,(i+1)*math.tau/10
                q=lambda r,t:(cx,head[1]+r*math.cos(t),head[2]+r*math.sin(t))
                vs=(q(.66,a),q(1.65,a),q(1.65,b),q(.66,b))
                s.face(hj,shell,tuple(reversed(vs)) if side>0 else vs)
                vs=(q(.40,a),q(.66,a),q(.66,b),q(.40,b))
                s.face(hj,glow,tuple(reversed(vs)) if side>0 else vs)
    if style!='eye':
        # Large slanted eye cuts and a dark open jaw remain readable in the
        # actual Y/Z camera plane in both facing directions.
        for side in (-1,1):
            cx=head[0]+side*(1.0 if heavy else 1.08)
            vs=tuple(add((cx,head[1],head[2]),v) for v in ((0,.15,.15),(0,.05,.95),(0,.36,.78),(0,.42,.05)))
            s.face(hj,glow,tuple(reversed(vs)) if side>0 else vs)
            s.side_panel(19,add(p[19],(side*.76,-.05,.45)),.22,.75,3)
            for z in (.20,.75):
                vs=tuple(add(p[19],v) for v in ((side*.78,.1,z-.10),(side*.78,.1,z+.12),(side*.78,-.22,z+.13)))
                s.face(19,2,(*vs,vs[-1]) if side<0 else (vs[2],vs[1],vs[0],vs[0]))
    for j in (23,27):s.ring(j,glow)
    raw,report=s.finish()
    if report['quads']>460:raise ValueError('Creature exceeds native crowd mesh budget')
    report.update(direction='coherent closed anatomy, large side eyes, restrained fins, working claws',style=style)
    return raw,report
