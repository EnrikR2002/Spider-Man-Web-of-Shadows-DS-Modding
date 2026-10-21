"""Continuous weight shifts, raking arcs and recoil for the0.25 creatures.

The0.24 author remains immutable. All times are real SCA samples; root travel
is supplied separately through native velocity/gravity by the program tables.
"""
import math,struct
from tools import midnight_enemy_motion as prior,creature_forge_motion as f
from tools import creature_forge_design as d,chapter_renewal_motion as modes
from tools.creature_forge_design import Move
from tools.rush_choreography import ROOT,IDENTITY,axis,mm,add
from tools.kit_choreography import safe_ik
from tools.sca import Sca
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd
from tools.actor_actions import ActorActions

MOVES={
 'skitter':(
  Move('Razor figure eight',55,25,((7,10),(14,18)),'scissor',12,((5,10,.9),(12,18,.8)),(),9),
  Move('Switchblade reversal',63,29,((13,19),),'feint',25,((2,7,-.85),(10,20,1.75)),(),11),
  Move('Flying rail shear',68,31,((10,14),(21,25)),'shear',25,((4,17,1.3),(20,25,.55)),((4,1.25),),12)),
 'warden':(
  Move('Execution pendulum',55,30,((9,13),(19,23)),'pendulum',14,((6,13,.6),(17,23,.4)),(),13),
  Move('Cathedral crash',63,34,((12,17),(24,29)),'peal',22,((7,11,.45),),(),15),
  Move('Iron processional',136,32,((10,14),(21,26)),'march',22,((4,14,1.0),(17,26,.9)),(),13)),
 'eye':(
  Move('Prismatic guillotine',55,31,((11,22),),'beam',40,((5,10,-.3),),(),14),
  Move('Capacitor rupture',63,27,((9,15),),'burst',14,((5,14,-.9),),((5,1.05),),12),
  Move('Staggered lightning',68,32,((8,14),(20,27)),'twins',40,(),(),14)),
 'maw':(
  Move('Undertow talons',55,26,((7,11),(15,19)),'scissor',12,((5,11,.8),(13,19,.6)),(),10),
  Move('Anchor cartwheel',63,30,((11,17),),'vault',25,((4,18,1.4),),((4,1.35),),13),
  Move('Keel ripper',68,29,((13,20),),'feint',25,((2,7,-.7),(10,20,1.65)),(),13)),
 'ballast':(
  Move('Dredger backhand',55,33,((10,15),(22,27)),'sweep',15,((7,15,.55),(19,27,.4)),(),15),
  Move('Breakwater collapse',63,37,((13,19),(26,32)),'quake',24,((7,12,.35),),(),17),
  Move('Hull breach',136,34,((12,20),(25,29)),'charge',30,((7,20,1.55),(21,26,.6)),(),16)),
 'spore':(
  Move('Scattering lanterns',55,34,((8,13),(17,22),(26,30)),'seeds',38,((27,32,-.45),),(),14),
  Move('Bloom kickback',63,26,((8,14),),'burst',14,((5,14,-.9),),((5,1.05),),12),
  Move('Thorn lance',68,30,((10,23),),'lance',42,((4,9,-.4),),(),14)),
 'conductor':(
  Move('Royal mutilation',55,34,((8,12),(17,21),(26,30)),'cadenza',20,((5,12,1.3),(14,21,1.2),(23,30,1.5)),(),7),
  Move('Blackout cyclone',63,38,((11,17),(24,31)),'fugue',32,((5,13,1.25),(16,22,-.85),(24,31,1.45)),(),9),
  Move('Storm execution',30,35,((10,18),(24,30)),'verdict',52,((3,8,-.8),(20,24,.7)),(),8),
  Move('Crown breaker',136,34,((11,16),(24,29)),'crownfall',34,((5,18,1.6),(20,25,.55)),((5,1.35),),10)),
}


def pose(idle,parents,style,stem,source='Idle',fno=0,n=1,move=None):
    mode=modes.mode(source)
    if move is None and mode not in ('idle','walk','run'):
        return prior.pose(idle,parents,style,stem,source,fno,n)
    p=f.Pose(idle,parents);p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.)
    front=style in ('maw','skitter');heavy=stem=='brt';boss=style=='conductor'
    for u,l,e in d.arms(stem):
        for j in (l,e):p.t[j]=tuple(v*(1.55 if front else 1.4 if heavy else 1.22) for v in p.t[j])
    root,lean,hh,ff=f.REST[style];hands=list(hh);feet=list(ff)
    phase=math.tau*fno/max(1,n);u=fno/max(1,n-1)
    yaw=roll=chest=head=jaw=shift=0.
    if front:root-=.15;lean-=7
    if move is None:
        if mode=='idle':
            # A continuous asymmetric breath with delayed head/scapula motion.
            root+=.07*math.sin(phase);lean+=1.5*math.sin(phase-.3)
            chest=2.2*math.sin(phase-.65);head=2.5*math.sin(phase-1.1)
            hands=[add(v,(0,.12*math.sin(phase-i*.8),.13*math.sin(phase-i*.5))) for i,v in enumerate(hands)]
        else:
            stride=4.8 if front else 3.7 if boss else 3.25
            for i in range(2):
                q=(fno/max(1,n)+i*.5)%1;stance=q<.58
                z=stride*(.5-q/.58) if stance else stride*(-.5+(q-.58)/.42)
                lift=0 if stance else (1.45 if front else 1.1)*math.sin(math.pi*(q-.58)/.42)
                feet[i]=add(ff[i],(0,lift,z))
                if front:
                    q=(q+.5)%1;stance=q<.58
                    z=stride*(.5-q/.58) if stance else stride*(-.5+(q-.58)/.42)
                    hands[i]=add(hh[i],(0,0 if stance else 1.25*math.sin(math.pi*(q-.58)/.42),z))
                else:hands[i]=add(hh[i],(0,.3*math.sin(phase+i*math.pi),-z*.9))
            root+=.24*math.cos(phase*2);roll=4*math.sin(phase);yaw=7*math.sin(phase)
            chest=-5*math.sin(phase-.2);head=-4*math.sin(phase-.55)
    else:
        end=n-1;first=move.contacts[0][0];last=move.contacts[-1][1];k=move.kind
        curve=lambda keys,t=fno:f.curve(keys,t)
        env=math.sin(math.pi*u)**.8
        # Hips lead the load; sternum and head follow on delayed curves. Curves
        # cross their keys with momentum rather than easing to a stop at each.
        coil=curve(((0,0),(max(2,first-4),1),(first+1,-.7),(last,.3),(end,0)))
        root-=.6*coil;lean+=(17 if front else -15)*coil
        shift=.25*coil;head=-8*coil;jaw=17*max(0,coil)
        if k in ('scissor','sweep','pendulum','cadenza','fugue'):
            strokes=[]
            for ci,(a,b) in enumerate(move.contacts):
                sign=1 if ci%2==0 else -1
                strokes.extend(((max(1,a-4),-sign*35),(a+1,sign*52),(b+2,sign*24)))
            yaw=curve(((0,0),*strokes,(end,0)))
            chest=.34*curve(((0,0),*strokes,(end,0)),max(0,fno-1.5))
            roll=yaw*(.28 if front else .2);lean+=13*env
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for ci,(a,b) in enumerate(move.contacts):
                    if ci%2!=i and k!='fugue':continue
                    # The hand cuts across the entire silhouette, continues
                    # past contact, then loops under the next winding arm.
                    high=6.8 if not front else 4.1
                    keys.extend(((max(1,a-5),(side*3.6,high,-1.8)),
                        (a-1,(side*3.1,high+.6,2.5)),
                        (a+2,(-side*.8,3.6 if not front else 1.8,6.8)),
                        (b+2,(-side*3.2,2.4 if not front else .65,3.5))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
                feet[i]=add(ff[i],(side*.35*env,.7*f.pulse(fno,first-5+i*3,first+3+i*3),1.4*env*(1 if i==0 else -.5)))
            if k=='fugue':
                # A travelling, low corkscrew between the two floor shocks.
                roll+=curve(((0,0),(8,-12),(17,24),(23,-26),(30,12),(end,0)))
                lean+=curve(((0,0),(12,28),(20,46),(28,18),(end,0)))
                root-=.85*env
        elif k in ('feint','charge'):
            lean+=curve(((0,0),(first-5,25),(first+2,-17),(last,12),(end,0)))
            yaw=curve(((0,0),(first-5,-40),(first+2,45),(last+2,18),(end,0)))
            roll=-yaw*.2;chest=yaw*.3
            for i,side in enumerate((1,-1)):
                hands[i]=curve(((0,hh[i]),(first-5,(side*3.3,.5 if front else 2.8,-.8)),
                    (first,(side*1.6,4 if front else 6.5,5.8)),(last,(-side*1.3,.8 if front else 2.3,5.2)),(end,hh[i])))
                feet[i]=add(ff[i],(0,1.1*f.pulse(fno,first-6+i*2,first+4+i*2),1.6*env*(1 if i==0 else -.7)))
        elif k in ('vault','shear','crownfall'):
            jump=move.jumps[0][0] if move.jumps else first-5
            lean+=curve(((0,0),(jump-1,28),(jump+3,-30),(first+2,18),(last,32),(end,0)))
            yaw=curve(((0,0),(jump-1,-30),(first,80 if boss else 62),(first+6,-25),(last,15),(end,0)))
            roll=curve(((0,0),(jump,0),(first,28 if boss else 38),(first+6,-16),(last,8),(end,0)))
            chest=yaw*.25
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i]),(max(1,jump-1),(side*2.6,.6,2.2)),(first-2,(side*4.1,7.,-.8)),
                    (first+1,(-side*.9,1.2,6.1)),(first+5,(-side*2.7,.8,3.8))]
                if len(move.contacts)>1:
                    a,b=move.contacts[1];keys.extend(((a-3,(side*3.2,7.,.1)),(a+1,(side*.8,1.,4.5)),(b+1,(side*3.3,1.3,2.4))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
                feet[i]=add(ff[i],(side*.6*env,1.8*f.pulse(fno,jump,first+6),(-1.7 if i==0 else 1.4)*f.pulse(fno,jump,first+6)))
            if boss:
                a,b=move.contacts[1];land=curve(((0,0),(a-3,0),(a+1,1),(b+1,.35),(end,0)))
                root-=2.25*max(0,land);lean+=25*max(0,land)
        elif k in ('quake','peal','march'):
            keys=[(0,hh[0])];tw=[]
            for ci,(a,b) in enumerate(move.contacts):
                keys.extend(((max(1,a-5),(3.,10.4,-1.8)),(a-2,(1.4,7.,2.6)),(a+1,(-1.,.9,4.8)),(b+2,(-2.6,1.5,2.7))))
                tw.extend(((max(1,a-5),-32),(a+2,36),(b+2,14)))
            keys.append((end,hh[0]));hands[0]=curve(keys)
            hands[1]=tuple(hh[1][j]+(hands[0][j]-hh[0][j])*.85 for j in range(3))
            yaw=curve(((0,0),*tw,(end,0)));chest=yaw*.4;roll=-yaw*.2
            for a,b in move.contacts:
                load=f.pulse(fno,a-3,b+3);root-=1.8*load;lean+=30*load
            feet[0]=add(ff[0],(0,.65*f.pulse(fno,first-6,first+1),.9*env))
        else:
            release=curve(((0,0),(max(1,first-4),-.6),(first+1,1),(last,.8),(end,0)))
            yaw=curve(((0,0),(max(1,first-4),-32),(first+2,38),(last,12),(end,0)))
            roll=12*env;chest=yaw*.35;lean-=12*coil
            for i,side in enumerate((1,-1)):
                hands[i]=add(hh[i],(side*(1.9*release),1.6*release,3.6*release-1.2*coil))
            jaw+=24*max(0,release)
        # Residual mantle/neck motion follows the impact and changes sign with
        # the next stroke; it is not another synchronous whole-body bob.
        head+=5*math.sin(fno*.55-.9)*env
    p.t[1]=(shift,root,0.);p.r[1]=mm(axis('z',roll),mm(axis('y',yaw*.7),mm(axis('x',lean),ROOT)))
    p.r[2]=axis('x',chest*.45);p.r[3]=axis('z',chest*.5);p.r[4]=axis('z',head-lean*.15)
    for i,(u0,l,e) in enumerate(d.arms(stem)):
        scapula=u0-1
        if scapula in (5,12):p.r[scapula]=mm(axis('z',3*math.sin(phase-.7-i)),p.r[scapula])
    for i,(u0,l,e) in enumerate(((20,21,22),(24,25,26))):
        side=1 if i==0 else -1
        safe_ik(p,u0,l,e,feet[i],(side*3.4,2,-2 if front else 3),(side,0,1));p.world_rotation(e,IDENTITY)
    for i,(u0,l,e) in enumerate(d.arms(stem)):
        side=1 if i==0 else -1
        safe_ik(p,u0,l,e,hands[i],(side*5.4,3.1 if front else 6.2,-1.4),(side,0,-1))
        p.world_rotation(e,mm(axis('y',(-side*25 if move else 0)),axis('x',-22 if move and prior.contact(move,fno) else 8)))
        for j in (e+1,e+2):
            if j<19:p.r[j]=mm(axis('z',-24*math.sin(phase-.65*i)*math.sin(math.pi*fno/max(1,n-1))),p.r[j])
    _,ps=p.fk();headjoint=4 if heavy else 5
    f.locate(p,19,add(ps[headjoint],(0,-.4,1.1)),axis('x',-jaw))
    p.forge_scale={}
    for i,(j,effect) in enumerate(zip((23,27),d.fx(move,fno))):
        kind,y,z,ss=effect;point=(0.,y,z);rot=IDENTITY
        if kind=='claw':
            _,ps=p.fk();point=add(ps[d.arms(stem)[i][2]],(0,0,1.2));rot=axis('x',55);ss=(.75,.65,1.25)
        elif kind in ('beam','orb'):rot=axis('z',90)
        elif kind=='ring' and move and move.kind=='burst':rot=axis('x',90)
        f.locate(p,j,point,rot);p.forge_scale[j]=tuple(round(v*4096) for v in (*ss,*(1/max(.01,v) for v in ss)))
    return p


def prepare(blob,names,style,stem,prefix):
    x=Xbd.parse(blob(stem+'.xbd'),names);idle=Sca.parse(blob(stem+'_Idle.sca'))
    parents=AnimationRig.parse(blob(stem+'.nsbmd')).parents;actions=ActorActions.parse(x.raw,names);by_source={}
    for move in MOVES[style]:
        action=actions.lookup(move.action)
        if action is None:raise ValueError('Missing native action slot')
        by_source[next(b['name'] for b in action.bindings if b['tag']==0)]=move
    extras={};clips=[]
    for i,b in enumerate(x.bindings):
        if b['tag']!=0:continue
        source=b['name'];a=Sca.parse(blob(source));move=by_source.get(source);mode=modes.mode(source)
        if move is None and mode in ('strike','slam','pounce','ranged'):
            move=MOVES[style][2 if mode=='ranged' else 1 if mode in ('pounce','slam') else 0]
        n=move.samples if move else prior.duration(mode,a.frame_count,style)
        if mode=='rise_attack':move=Move('Rising retaliation',0,n,((round(n*.72),round(n*.84)),),'sweep',10)
        poses=[pose(idle,parents,style,stem,source,j,n,None if mode=='rise_attack' else move) for j in range(n)]
        end=next((j for j in range(i+1,len(x.bindings)) if x.bindings[j]['tag']==0),len(x.bindings))
        target=prefix+'_'+source;extras[target]=f.encode(blob(source),poses)
        for part in x.bindings[i+1:end]:
            target=prefix+'_'+source[:-4]+('.gmb' if part['tag']==3 else '.gab')
            if part['tag']==3:extras[target]=prior.geometry(blob(part['name']),poses,move,style)
            elif part['tag']==4 and move:
                raw=b''.join(struct.pack('<3H',*e) for a,b in move.contacts for e in ((a,1,1),(b,1,5)))+b'\xff'*6
                extras[target]=raw+bytes(-len(raw)%4)
        clips.append(dict(source=source,resource=prefix+'_'+source,samples=n,move=move.name if move else None,mode=mode,contacts=move.contacts if move else []))
    return extras,clips
