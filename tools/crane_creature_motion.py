"""Authored full-body enemy motion, using native rigs and action sample counts.

Attack poses are generated from an idle bind pose and continuous control curves;
native attack samples are not used as choreography. Native scales/timing and
opaque animation bytes remain preserved by sca_author.
"""
import math
from tools.sca import Sca
from tools.sca_author import repack_samples
from tools.crane_creature_art import Pose
from tools.kit_choreography import catmull,safe_ik
from tools.rush_choreography import ROOT,IDENTITY,mm,mv,axis,stored,add,sub,mul,transpose

BASE={
 'ballast':{'root':4.5,'lean':7,'hands':((3.0,5.0,1.5),(-3.0,4.6,.3)),
            'feet':((1.5,.55,1.0),(-1.5,.55,-1.0))},
 'maw':{'root':2.7,'lean':40,'hands':((2.0,.65,3.3),(-2.0,.65,3.3)),
        'feet':((1.6,.5,-1.6),(-1.6,.5,-1.6))},
 'spore':{'root':4.5,'lean':0,'hands':((2.6,3.6,1.2),(-2.6,3.6,1.2)),
          'feet':((1.0,.65,-.4),(-1.0,.65,-.4))},
}

def _curve(keys,t):
    # Native very short clips can merge anticipation/recovery samples.
    unique={float(k):v for k,v in keys}
    return catmull(sorted(unique.items()),t)

def pose(idle,parents,kind,frame=0,frames=1,mode='idle',impact=6,recovery=12):
    if kind not in BASE:raise ValueError('Unknown creature motion')
    p=Pose(idle,parents);cfg=BASE[kind]
    p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.)
    root=cfg['root'];lean=cfg['lean'];twist=0.;head_pitch=0.;drive=0.
    hands=list(cfg['hands']);feet=list(cfg['feet'])
    phase=2*math.pi*frame/max(1,frames-1)
    stride=0.0
    if mode in ('walk','run'):
        stride=(.7 if kind=='maw' else .5) if mode=='walk' else (1.0 if kind=='maw' else .8)
    root+=.07*math.sin(2*phase)
    if kind=='spore':root+=.18*math.sin(phase);head_pitch=3*math.sin(phase+.7)
    if stride:
        for i,(side,off) in enumerate(((1,0),(-1,math.pi))):
            swing=math.sin(phase+off);lift=max(0,swing)**2
            x,y,z=cfg['feet'][i];feet[i]=(x,y+.5*lift,z+stride*math.cos(phase+off))
            x,y,z=cfg['hands'][i]
            if kind=='maw':hands[i]=(x,y+.55*max(0,-swing)**2,z-stride*math.cos(phase+off))
            else:hands[i]=(x,y+.15*math.cos(phase+off),z-.6*stride*math.cos(phase+off))
    elif kind=='maw':
        hands=[add(v,(0,.04*math.sin(phase+i*math.pi),0)) for i,v in enumerate(hands)]
    if mode in ('die','hurt','bound'):
        t=frame/max(1,frames-1)
        if mode=='die':
            collapse=1-(1-t)**3
            root-=min(root-.6,2.4)*collapse;lean+=38*collapse;head_pitch=-24*collapse
            hands=[add(v,(0,-.5*collapse,-1.0*collapse)) for v in hands]
            feet=[add(v,(0,.1*collapse,.55*collapse)) for v in feet]
        elif mode=='hurt':
            recoil=math.sin(math.pi*t)*(1-.5*t)
            lean-=24*recoil;root-=.25*recoil;head_pitch=-18*recoil
            hands=[add(v,(0,.6*recoil,-.6*recoil)) for v in hands]
        else:
            curl=.65+.1*math.sin(phase*2);root-=.3;lean+=8
            hands=[(x*.55,y+curl,z-.4) for x,y,z in hands]
    elif mode=='prep':
        t=frame/max(1,frames-1)
        root-=(.25 if kind=='maw' else .65)*t;lean+=(12 if kind=='maw' else 10)*t;head_pitch=-8*t
        hands=[add(v,(0,.35*t,-1.1*t)) for v in hands]
    elif mode=='air':
        root-=.12;lean+=5
        hands=[add(v,(0,.9,.5)) for v in hands];feet=[add(v,(0,.5,-.2)) for v in feet]
    elif mode=='land':
        squash=math.sin(math.pi*min(1,frame/max(1,frames-1)))**2
        root-=.45*squash;lean+=8*squash;hands=[add(v,(0,.1,-.3*squash)) for v in hands]
    elif mode in ('attack','leap','slam','charge','spit','backhand'):
        end=max(1,frames-1);hit=min(max(2,impact),max(2,end-2));stop=min(end,max(hit+2,recovery))
        ready=max(1,hit-2);settle=min(end,stop+max(2,(end-stop)*.45))
        if mode=='leap':stop=max(stop,round(end*.55));settle=max(settle,round(end*.85))
        charge=_curve(((0,1 if mode=='leap' else 0),(ready,1),(hit,.15),(min(end,hit+2),-.35),(settle,0),(end,0)),frame)
        burst=_curve(((0,0),(ready,0),(hit,1),(stop,.25),(settle,0),(end,0)),frame)
        sweep=_curve(((0,0),(ready,-.8),(hit,.25),(stop,1),(settle,.2),(end,0)),frame)
        if kind=='ballast':
            root-=.35*charge+.18*burst;lean+=-14*charge+19*burst;twist=35*sweep;head_pitch=-lean*.3
            drive=.18*burst
            hands[0]=_curve(((0,cfg['hands'][0]),(ready,(2.6,6.8,-1.0)),
                (hit,(2.1,5.8,-2.7)),(stop,(1.0,4.5,4.7)),(settle,cfg['hands'][0]),(end,cfg['hands'][0])),frame)
            hands[1]=_curve(((0,cfg['hands'][1]),(ready,(-2.2,8.2,-1.6)),
                (hit,(-1.0,4.7,4.8)),(stop,(-1.5,4.4,-3.5)),(settle,cfg['hands'][1]),(end,cfg['hands'][1])),frame)
            if mode=='slam':
                root-=.7*burst;lean+=22*burst;twist*=.2
                for i,side in enumerate((1,-1)):
                    hands[i]=_curve(((0,cfg['hands'][i]),(ready,(side*1.4,9.3,.6)),
                        (hit,(side*.9,1.0,3.3)),(stop,(side*1.7,1.5,3.0)),
                        (settle,cfg['hands'][i]),(end,cfg['hands'][i])),frame)
            elif mode=='charge':
                lean+=25*burst;twist*=.15
                hands=[add(v,(0,-.5*burst,2.5*burst)) for v in cfg['hands']]
                feet[1]=add(feet[1],(0,.6*burst,-.5*burst))
        elif kind=='maw':
            root-=.25*charge;lean+=12*charge-13*burst;head_pitch=-8*charge+8*burst
            for i,(x,y,z) in enumerate(cfg['hands']):
                hands[i]=_curve(((0,(x,1.0,2.2) if mode=='leap' else (x,y,z)),(ready,(x,1.0,2.2)),
                    (hit,(x*.65,3.0,5.6)),(stop,(x,1.2,4.3)),(settle,(x,y,z)),(end,(x,y,z))),frame)
            for i,(x,y,z) in enumerate(cfg['feet']):feet[i]=(x,y+.55*burst,z-.5*burst)
            drive=.12*burst
            if mode=='backhand':
                twist=-28*sweep;hands[0],hands[1]=((-hands[1][0],hands[1][1]+.5,hands[1][2]),(-hands[0][0],hands[0][1],hands[0][2]))
        else:
            lean+=-14*charge+13*burst;head_pitch=-18*charge+22*burst;root+=.18*charge
            for i,side in enumerate((1,-1)):
                hands[i]=_curve(((0,cfg['hands'][i]),(ready,(side*1.3,6.1,2.5)),
                    (hit,(side*1.7,5.6,3.9)),(stop,(side*2.8,4.8,2.8)),
                    (settle,cfg['hands'][i]),(end,cfg['hands'][i])),frame)
    p.t[1]=(0.,root,drive)
    p.r[1]=mm(axis('y',twist*.35),mm(axis('x',lean),ROOT))
    p.r[2]=axis('x',twist*.45);p.r[3]=axis('z',-lean*.12);p.r[4]=axis('z',-lean*.45+head_pitch)
    # Solve every major limb anew. End rotations keep claws/tendrils coherent.
    rotations,_=p.fk()
    for i,(upper,lower,end,side) in enumerate(((20,21,22,1),(24,25,26,-1))):
        pole=(side*3.0,2.1,-2.3 if kind=='maw' else 2.0)
        safe_ik(p,upper,lower,end,feet[i],pole,(side,0,1))
        p.world_rotation(end,rotations[end])
    for i,(upper,lower,end,side) in enumerate(((6,7,8,1),(13,14,15,-1))):
        pole=(side*4.5,2.4,2.2) if kind=='maw' else (side*4.5,6.0,-1.4)
        safe_ik(p,upper,lower,end,hands[i],pole,(side,0,-1))
        p.world_rotation(end,rotations[end])
    return p

def neutral(idle,parents,kind):return pose(idle,parents,kind)

def author(raw,idle_raw,parents,kind,mode,impact=6,recovery=12,*,reference=None):
    a=Sca.parse(raw);idle=Sca.parse(idle_raw)
    if a.joint_count!=28 or len(parents)!=28:raise ValueError('Expected28-bone creature motion')
    rotations={j:[] for j in range(28)};translations={j:[] for j in range(28)};frames=[]
    for f in range(a.frame_count):
        p=pose(idle,parents,kind,f,a.frame_count,mode,impact,recovery)
        rs,points=p.fk();frames.append(points)
        if reference is not None:
            joint,local,refs=reference
            refs.append(add(points[joint],mv(rs[joint],local)))
        for j in range(28):
            rotations[j].append(stored(p.r[j]));translations[j].append(tuple(round(v*4096) for v in p.t[j]))
    result=repack_samples(raw,rotations=rotations,translations=translations)
    return result,frames
