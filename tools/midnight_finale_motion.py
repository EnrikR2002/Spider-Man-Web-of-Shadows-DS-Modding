"""Continuous, rig-authored Midnight poses with a shared action-boundary stance."""
import math,struct
from tools import creature_forge_motion as f,creature_forge_design as d
from tools import midnight_encore_motion as encore,midnight_enemy_motion as contacts,chapter_renewal_motion as modes
from tools.creature_forge_design import Move
from tools.rush_choreography import ROOT,IDENTITY,axis,mm,mv,add,sub
from tools.kit_choreography import safe_ik
from tools.sca import Sca
from tools.custom_formats import Xbd
from tools.actor_actions import ActorActions
from tools.animation_rig import AnimationRig

BOSS=(
 Move('Livewire rake',55,36,((8,11),(18,21),(27,30)),'cadenza',24,((3,11,1.8),(14,21,2.2),(24,30,2.0)),((3,.7),(17,.65)),12),
 Move('Coil reversal',63,38,((10,14),(26,30)),'fugue',34,((3,12,2.4),(15,22,-1.5),(24,30,2.8)),((3,1.05),),16),
 Move('Storm lance',30,38,((11,16),(25,30)),'verdict',58,((3,9,-1.9),(19,28,2.6)),((3,1.15),),16),
 Move('Railbreaker',136,40,((12,16),(29,33)),'crownfall',38,((3,14,2.8),(18,24,-1.1),(26,33,2.7)),((4,1.65),),18),
 Move('Surge escape',74,40,((14,19),(29,34)),'crownfall',30,((2,8,-1.8),(10,22,3.0),(25,34,2.1)),((2,1.2),),22),
 Move('Livewire counter',74,40,((14,19),(29,34)),'crownfall',30,((2,8,-2.0),(10,22,3.35),(25,34,2.3)),((2,1.25),),22),
)
MOVES={**encore.MOVES,'conductor':BOSS}
STYLES=('skitter','warden','eye','conductor')


def stance(style):
    if style=='conductor':return 4.65,18.,((3.4,2.8,2.5),(-3.4,3.,2.1)),((1.8,.65,1.1),(-1.8,.65,-1.1))
    return f.REST[style]


def pose(idle,parents,style,stem,source='Idle',fno=0,n=1,move=None):
    mode=modes.mode(source)
    # Complete native prone/rise/death routes remain present. Their endpoints
    # are adjusted to the same upright proportions, without touching contacts.
    if move is None and mode not in ('idle','walk','run','recoil'):
        p=encore.pose(idle,parents,style,stem,source,fno,n)
        if style=='conductor':
            upright=max(0,min(1,(p.t[1][1]-1.4)/3.8))
            p.t[1]=add(p.t[1],(0,-.55*upright,0))
            p.r[1]=mm(axis('x',18*upright),p.r[1])
        return p
    p=f.Pose(idle,parents);p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.)
    front=style=='skitter';boss=style=='conductor';heavy=stem=='brt'
    for u,l,e in d.arms(stem):
        for j in (l,e):p.t[j]=tuple(v*(1.55 if front else 1.4 if heavy else 1.22) for v in p.t[j])
    root,lean,hh,ff=stance(style);hands=list(hh);feet=list(ff)
    end=max(1,n-1);u=fno/end;phase=math.tau*u
    yaw=roll=chest=head=jaw=0.;shift=0.;env=math.sin(math.pi*u)**2
    if move is None:
        if mode=='idle':
            root+=.06*math.sin(phase);chest=1.8*math.sin(phase)
            head=-1.5*math.sin(phase)*math.cos(phase-.5)
            hands=[add(h,(0,.10*math.sin(phase+i*.4)*math.sin(phase/2),.07*math.sin(phase))) for i,h in enumerate(hands)]
        elif mode=='recoil':
            recoil=f.curve(((0,0),(2.5,1),(5.5,.55),(end,0)),fno)
            root-=.42*recoil;lean-=17*recoil;yaw=12*recoil;chest=-12*recoil;head=9*recoil
            hands=[add(h,(side*.5*recoil,.4*recoil,-.9*recoil)) for h,side in zip(hands,(1,-1))]
            jaw=12*recoil
        else:
            stride=4.6 if front else 4.1 if boss else 2.8
            for i in range(2):
                q=(u+i*.5)%1
                z=stride*math.cos(math.tau*q)/2
                lift=(1.25 if front else 1.0)*max(0,math.sin(math.tau*q))**2
                feet[i]=add(ff[i],(0,lift,z))
                if front:hands[i]=add(hh[i],(0,.95*max(0,-math.sin(math.tau*q))**2,-z))
                else:hands[i]=add(hh[i],(0,.25*math.sin(math.tau*q),-.7*z))
            root+=.15*(1-math.cos(phase*2));roll=2.8*math.sin(phase)
            yaw=4.*math.sin(phase);chest=-yaw*.55;head=-yaw*.35
    else:
        first=move.contacts[0][0];last=move.contacts[-1][1];kind=move.kind
        curve=lambda keys,t=fno:f.curve(keys,t)
        # Long curves cross each contact with momentum. The opposite hand
        # follows through while the next shoulder winds; feet carry the load.
        load=curve(((0,0),(max(2,first-4),1),(first+2,-.4),(last+1,.2),(end,0)))
        root-=.48*load;lean+=(-11 if heavy else 12)*load
        chest=-7*load;head=5*load;jaw=14*max(0,load)
        if kind in ('cadenza','scissor','pendulum','fugue'):
            twist=[(0,0)]
            for ci,(a,b) in enumerate(move.contacts):
                sign=1 if ci%2==0 else -1
                twist.extend(((max(2,a-4),-sign*27),(a+2,sign*43),(b+2,sign*25)))
            twist.append((end,0));yaw=curve(twist);chest=.32*curve(twist,max(0,fno-1.7))
            roll=yaw*.16
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for ci,(a,b) in enumerate(move.contacts):
                    if ci%2!=i and kind!='fugue':continue
                    h=4.2 if front else 6.2
                    keys.extend(((max(2,a-5),(side*3.6,h,-.5)),(a-1,(side*3.7,h+.3,2.7)),
                        (a+2,(-side*.8,2.3 if front else 3.8,5.9)),(b+2,(-side*2.7,1.1 if front else 2.2,3.6))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
            if kind=='fugue':roll+=21*math.sin(math.tau*u)*env;lean+=18*env
        elif kind in ('crownfall','vault','shear'):
            jump=move.jumps[0][0] if move.jumps else first-5
            roll=curve(((0,0),(jump,0),(first-2,22),(first+3,-18),(last,8),(end,0)))
            yaw=curve(((0,0),(jump,-24),(first+2,65),(last-3,-32),(last+1,18),(end,0)))
            lean+=curve(((0,0),(jump-1,20),(first-2,-23),(first+3,18),(last,22),(end,0)))
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i]),(max(2,jump),(side*2.5,2.,1.3)),(first-3,(side*3.9,6.8,-.5)),
                    (first+1,(-side*.9,1.1,5.6)),(first+5,(-side*2.6,1.,3.4))]
                if len(move.contacts)>1:
                    a,b=move.contacts[1];keys.extend(((a-4,(side*3.2,6.5,.8)),(a+1,(side*.7,1.2,4.8)),(b+1,(side*2.8,1.8,2.8))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
                feet[i]=add(ff[i],(side*.35*env,1.35*f.pulse(fno,jump,first+5),(-1. if i==0 else 1.)*env))
            root-=.8*f.pulse(fno,last-3,last+4)
        elif kind in ('peal','march'):
            yaw=17*math.sin(phase)*env
            for ci,(a,b) in enumerate(move.contacts):
                slam=f.pulse(fno,a-4,b+3);root-=.75*slam;lean+=20*slam
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for a,b in move.contacts:keys.extend(((max(2,a-5),(side*2.8,8.6,-.6)),(a+1,(side*.7,1.1,4.6)),(b+2,(side*2.,2.,2.9))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
        else:
            release=curve(((0,0),(max(2,first-4),-.4),(first+2,1),(last,.7),(end,0)))
            yaw=26*math.sin(phase)*env;roll=8*env
            for i,side in enumerate((1,-1)):hands[i]=add(hh[i],(side*1.2*release,1.3*release,2.9*release))
            jaw+=24*max(0,release)
        # Carry the arms with the body turn; world-fixed tips fighting a
        # rotating spine were causing the old rubber-band/paddling impression.
        carry=mm(axis('z',roll*.55),axis('y',yaw*.72));center=(0,root,0)
        hands=[add(center,mv(carry,sub(h,center))) for h in hands]
        head+=3*math.sin(fno*.45-.8)*env
    p.t[1]=(shift,root,0.)
    p.r[1]=mm(axis('z',roll),mm(axis('y',yaw*.55),mm(axis('x',lean),ROOT)))
    p.r[2]=axis('x',chest*.4);p.r[3]=axis('y',chest*.5);p.r[4]=axis('z',head)
    for i,(a,b,e) in enumerate(((20,21,22),(24,25,26))):
        side=1 if i==0 else -1
        safe_ik(p,a,b,e,feet[i],(side*3.2,2,-2 if front else 3),(side,0,1));p.world_rotation(e,IDENTITY)
    for i,(a,b,e) in enumerate(d.arms(stem)):
        side=1 if i==0 else -1
        safe_ik(p,a,b,e,hands[i],(side*5,3.5 if front or boss else 6,-1.4),(side,0,-1))
        p.world_rotation(e,mm(axis('y',side*15*env if move else 0),axis('x',-18*env if move else 8)))
        for j in (e+1,e+2):
            if j<19:p.r[j]=mm(axis('z',-12*math.sin(phase-i*.5)*env),p.r[j])
    _,ps=p.fk();f.locate(p,19,add(ps[4 if heavy else 5],(0,-.4,1.1)),axis('x',-jaw))
    p.forge_scale={}
    for i,(j,effect) in enumerate(zip((23,27),d.fx(move,fno))):
        kind,y,z,scale=effect;point=(0.,y,z);rot=IDENTITY
        if kind=='claw':
            _,ps=p.fk();point=add(ps[d.arms(stem)[i][2]],(0,0,1.));rot=axis('x',55);scale=(.65,.5,1.0)
        elif kind in ('beam','orb'):rot=axis('z',90)
        elif kind=='ring' and move and move.kind=='burst':rot=axis('x',90)
        f.locate(p,j,point,rot);p.forge_scale[j]=tuple(round(v*4096) for v in (*scale,*(1/max(.01,v) for v in scale)))
    return p


def prepare(blob,names,style,stem,published):
    x=Xbd.parse(blob(stem+'.xbd'),names);idle=Sca.parse(blob(stem+'_Idle.sca'))
    parents=AnimationRig.parse(blob(stem+'.nsbmd')).parents;actions=ActorActions.parse(x.raw,names);selected={}
    for move in MOVES[style]:
        a=actions.lookup(move.action);selected[next(b['name'] for b in a.bindings if b['tag']==0)]=move
    extras={};clips=[]
    for i,b in enumerate(x.bindings):
        if b['tag']!=0:continue
        source=b['name'];target='zz_F22_'+style+'_'+source;old=Sca.parse(published(target));mode=modes.mode(source);move=selected.get(source)
        if move is None and mode in ('strike','slam','pounce','ranged'):move=MOVES[style][2 if mode=='ranged' else 1 if mode=='slam' else 0]
        # Preserve get-up attack sample count and its exact GAB/GMB. Its authored
        # lifecycle already covers full native damage/death/reward semantics.
        if mode=='rise_attack':continue
        n=move.samples if move else 23 if mode in ('walk','run') else old.frame_count
        poses=[pose(idle,parents,style,stem,source,j,n,move) for j in range(n)]
        extras[target]=f.encode(blob(source),poses)
        end=next((j for j in range(i+1,len(x.bindings)) if x.bindings[j]['tag']==0),len(x.bindings))
        for part in x.bindings[i+1:end]:
            name='zz_F22_'+style+'_'+source[:-4]+('.gmb' if part['tag']==3 else '.gab')
            if part['tag']==3:extras[name]=contacts.geometry(blob(part['name']),poses,move,style)
            elif part['tag']==4 and move:
                raw=b''.join(struct.pack('<3H',*e) for a,b in move.contacts for e in ((a,1,1),(b,1,5)))+b'\xff'*6
                extras[name]=raw+bytes(-len(raw)%4)
        clips.append(dict(resource=target,mode=mode,samples=n,move=move.name if move else None))
    return extras,clips
