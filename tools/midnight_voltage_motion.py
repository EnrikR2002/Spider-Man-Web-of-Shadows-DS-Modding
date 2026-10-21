"""Low, twisting electrical predator motion on the owned28-joint boss rig."""
import math,struct
from tools import midnight_encore_motion as prior,creature_forge_motion as f,creature_forge_design as d
from tools import chapter_renewal_motion as modes
from tools.creature_forge_design import Move
from tools.rush_choreography import axis,mm,add,IDENTITY
from tools.kit_choreography import safe_ik
from tools.sca import Sca
from tools.custom_formats import Xbd
from tools.animation_rig import AnimationRig
from tools.actor_actions import ActorActions

MOVES=(
 Move('Voltage rake',55,26,((5,8),(12,15),(19,22)),'cadenza',24,((0,8,2.15),(9,15,2.7),(17,23,2.5)),((0,.75),(12,.7)),3),
 Move('Arc wheel',63,28,((7,12),(19,24)),'fugue',34,((0,10,2.6),(12,18,-1.8),(19,25,3.)),((0,.95),),4),
 Move('Pulse lance',30,26,((6,12),(17,22)),'verdict',58,((0,5,-2.25),(12,20,2.8)),((0,1.15),),3),
 Move('Rail rupture',136,28,((8,12),(20,24)),'crownfall',38,((0,12,3.),(13,19,-1.3),(20,25,2.9)),((0,1.65),),4),
 Move('Surge release',74,28,((8,12),(19,24)),'crownfall',30,((0,8,-2.6),(11,25,3.)),((0,1.8),),3),
 Move('Livewire return',74,28,((8,12),(19,24)),'crownfall',30,((0,7,-3.),(10,25,3.5)),((0,1.65),),3),
)


def pose(idle,parents,style='conductor',stem='brt',source='Idle',fno=0,n=1,move=None):
    p=prior.pose(idle,parents,style,stem,source,fno,n,move)
    mode=modes.mode(source)
    if move is None and mode not in ('idle','walk','run'):return p
    _,world=p.fk();hands=[world[e] for u,l,e in d.arms(stem)];feet=[world[22],world[26]]
    phase=math.tau*fno/max(1,n);u=fno/max(1,n-1);env=math.sin(math.pi*u)**.8 if move else 0
    # A forward-loaded waist and long front limbs replace the upright guard.
    p.t[1]=(p.t[1][0],p.t[1][1]-1.65,p.t[1][2]);p.r[1]=mm(axis('x',31),p.r[1])
    if move:
        if move.action in (74,136):
            spin=f.curve(((0,0),(3,-22),(9,190),(16,330),(22,360),(n-1,360)),fno)
            p.r[1]=mm(axis('y',spin),mm(axis('z',30*math.sin(math.pi*u*2)*env),p.r[1]))
        elif move.kind=='fugue':p.r[1]=mm(axis('z',38*math.sin(math.tau*u)*env),p.r[1])
        p.r[3]=mm(axis('z',12*math.sin(fno*.7-1.2)*env),p.r[3])
    else:
        p.r[3]=mm(axis('z',2.5*math.sin(phase-.65)),p.r[3])
    for i,(a,b,e) in enumerate(d.arms(stem)):
        side=1 if i==0 else -1;target=add(hands[i],(side*.25,-1.6,1.6))
        if move and move.action in (74,136):target=add(target,(side*1.2*env,2.*env,-1.6*env))
        safe_ik(p,a,b,e,target,(side*5,3.8,-1.6),(side,0,-1))
        p.world_rotation(e,mm(axis('y',side*22*env),axis('x',-15)))
    for i,(a,b,e) in enumerate(((20,21,22),(24,25,26))):
        side=1 if i==0 else -1;target=add(feet[i],(side*.2,0,-.8))
        if move and move.action in (74,136):target=add(target,(side*.8*env,1.1*env,-1.1*env))
        safe_ik(p,a,b,e,target,(side*3.5,2,-2),(side,0,1));p.world_rotation(e,IDENTITY)
    # Keep claw effects attached to the current animated wrists after the load.
    _,world=p.fk()
    for i,(j,effect) in enumerate(zip((23,27),d.fx(move,fno))):
        if effect[0]=='claw':f.locate(p,j,add(world[d.arms(stem)[i][2]],(0,0,1.2)),axis('x',55))
    return p


def prepare(blob,names):
    x=Xbd.parse(blob('brt.xbd'),names);idle=Sca.parse(blob('brt_Idle.sca'));parents=AnimationRig.parse(blob('brt.nsbmd')).parents
    actions=ActorActions.parse(x.raw,names);by_source={}
    for move in MOVES:
        action=actions.lookup(move.action);by_source[next(b['name'] for b in action.bindings if b['tag']==0)]=move
    extras={};clips=[]
    for i,b in enumerate(x.bindings):
        if b['tag']!=0:continue
        source=b['name'];original=Sca.parse(blob(source));move=by_source.get(source);mode=modes.mode(source)
        if move is None and mode in ('strike','slam','pounce','ranged'):move=MOVES[2 if mode=='ranged' else 1 if mode=='slam' else 0]
        n=move.samples if move else 14 if mode in ('walk','run') else prior.prior.duration(mode,original.frame_count,'conductor')
        if mode=='rise_attack':move=None
        poses=[pose(idle,parents,source=source,fno=j,n=n,move=move) for j in range(n)]
        end=next((j for j in range(i+1,len(x.bindings)) if x.bindings[j]['tag']==0),len(x.bindings))
        target='zz_F22_conductor_'+source;extras[target]=f.encode(blob(source),poses)
        for part in x.bindings[i+1:end]:
            target='zz_F22_conductor_'+source[:-4]+('.gmb' if part['tag']==3 else '.gab')
            if part['tag']==3:extras[target]=prior.prior.geometry(blob(part['name']),poses,move,'conductor')
            elif part['tag']==4 and move:
                raw=b''.join(struct.pack('<3H',*e) for a,b in move.contacts for e in ((a,1,1),(b,1,5)))+b'\xff'*6
                extras[target]=raw+bytes(-len(raw)%4)
        clips.append(dict(source=source,resource='zz_F22_conductor_'+source,samples=n,move=move.name if move else None,contacts=move.contacts if move else [],mode=mode))
    return extras,clips
