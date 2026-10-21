"""Brisk whole-body creature choreography and synchronized native contacts.

This is a new authoring pass; the pinned Forge generators remain unchanged.
Durations are actual sampled animation time, never a global game-speed patch.
"""
import math,struct
from tools import creature_forge_motion as f,creature_forge_design as old
from tools import chapter_renewal_motion as modes
from tools.creature_forge_design import Move
from tools.rush_choreography import ROOT,IDENTITY,axis,mm,add
from tools.kit_choreography import safe_ik
from tools.sca import Sca
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd
from tools.actor_actions import ActorActions
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob

MOVES={
 'skitter':(
  Move('Railcut cross',55,27,((8,11),(16,19)),'scissor',10,((7,11,.7),(15,19,.4)),(),12),
  Move('Switchback execution',63,32,((14,18),),'feint',23,((3,7,-.65),(10,18,1.35)),(),16),
  Move('Trackside bound',68,35,((10,14),(24,27)),'shear',23,((5,17,1.05),),((5,1.35),),16)),
 'warden':(
  Move('Pendulum sentence',55,36,((11,14),(23,26)),'pendulum',12,((10,14,.3),),(),19),
  Move('Deadbell peal',63,40,((14,19),(28,33)),'peal',20,(),(),21),
  Move('Toll march',136,38,((11,15),(25,29)),'march',19,((6,13,.7),(20,27,.65)),(),19)),
 'eye':(
  Move('Arc guillotine',55,36,((14,24),),'beam',37,(),(),18),
  Move('Capacitor bloom',63,30,((10,15),),'burst',13,((7,14,-.55),),((7,1.05),),16),
  Move('Twin discharge',68,38,((10,17),(23,30)),'twins',37,(),(),18)),
 'maw':(
  Move('Riptide scissor',55,29,((9,12),(17,20)),'scissor',10,((8,12,.6),(16,20,.4)),(),14),
  Move('Anchor vault',63,34,((12,17),),'vault',22,((6,19,1.05),),((6,1.4),),18),
  Move('Keelbreaker feint',68,33,((15,20),),'feint',22,((4,8,-.5),(11,20,1.3)),(),18)),
 'ballast':(
  Move('Dredger sweep',55,38,((13,17),(25,29)),'sweep',12,((12,17,.35),(24,29,.2)),(),20),
  Move('Breakwater rupture',63,42,((15,21),(29,35)),'quake',20,(),(),23),
  Move('Hull charge',136,39,((14,22),(28,32)),'charge',28,((10,22,1.2),(23,26,.4)),(),23)),
 'spore':(
  Move('Seed procession',55,39,((10,15),(20,25),(29,34)),'seeds',35,((31,36,-.3),),(),18),
  Move('Bloom recoil',63,30,((10,15),),'burst',12,((7,15,-.6),),((7,1.1),),16),
  Move('Lantern lance',68,34,((13,24),),'lance',38,(),(),18)),
 'conductor':(
  Move('Cadenza',55,44,((12,16),(23,27),(33,37)),'cadenza',16,((10,16,.5),(21,27,.5),(31,37,.6)),(),16),
  Move('Blackout fugue',63,50,((17,23),(29,35),(40,46)),'fugue',26,(),(),20),
  Move('Storm verdict',30,48,((17,25),(32,40)),'verdict',44,(),(),21),
  Move('Crownfall',136,46,((15,21),(33,39)),'crownfall',30,((9,22,1.15),),((9,1.7),),23)),
}


def contact(move,sample):return any(a<=sample<b for a,b in move.contacts)


def pose(idle,parents,style,stem,source='Idle',fno=0,n=1,move=None):
    # Lifecycle clips retain their rig-safe complete poses, with actual shorter
    # durations below. Locomotion and attack are authored here as whole actions.
    mode=modes.mode(source)
    if move is None and mode not in ('idle','walk','run'):
        return f.pose(idle,parents,style,stem,source,fno,n)
    p=f.Pose(idle,parents);p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.)
    front=style in ('maw','skitter');heavy=stem=='brt'
    for u,l,e in old.arms(stem):
        for j in (l,e):p.t[j]=tuple(v*(1.55 if front else 1.4 if heavy else 1.22) for v in p.t[j])
    root,lean,hh,ff=f.REST[style];hands=list(hh);feet=list(ff)
    twist=roll=head=jaw=0.;phase=math.tau*fno/max(1,n);time=fno/max(1,n-1)
    if front:root-=.15;lean-=7
    if move is None:
        if mode=='idle':
            root+=.035*math.sin(phase);head=.8*math.sin(phase-.8)
            hands=[add(v,(0,.04*math.sin(phase+i*.8),0)) for i,v in enumerate(hands)]
        else:
            # A diagonal trot for the predators, a planted weighted stride for
            # heavies. Stance moves continuously; the swing has a single arc.
            stride=3.6 if front else 2.7 if heavy else 2.8
            for i in range(2):
                q=(fno/max(1,n)+i*.5)%1
                stance=q<.6
                z=stride*(.5-q/.6) if stance else stride*(-.5+(q-.6)/.4)
                lift=0 if stance else (1.05 if front else .8)*math.sin(math.pi*(q-.6)/.4)
                feet[i]=add(ff[i],(0,lift,z))
                if front:
                    q=(q+.5)%1;stance=q<.6
                    z=stride*(.5-q/.6) if stance else stride*(-.5+(q-.6)/.4)
                    lift=0 if stance else .85*math.sin(math.pi*(q-.6)/.4)
                    hands[i]=add(hh[i],(0,lift,z))
                else:hands[i]=add(hh[i],(0,.15*math.sin(phase+i*math.pi),-z*.65))
            root+=.12*math.cos(phase*2);roll=1.3*math.sin(phase);twist=3*math.sin(phase);head=-2*math.sin(phase-.4)
    else:
        k=move.kind;first=move.contacts[0][0];last=move.contacts[-1][1];end=n-1
        curve=lambda keys:f.curve(keys,fno)
        coil=curve(((0,0),(first-3,1),(first+1,-.2),(min(end,last+3),.15),(end,0)))
        root-=.35*coil;lean+=(10 if front else -8)*coil;head=-6*coil;jaw=12*max(0,coil)
        if k in ('scissor','sweep','pendulum','cadenza'):
            # Lead arm recoils while the other plants/guards; opposite shoulder
            # takes over the second stroke before the first has fully settled.
            keys=[(0,0)]
            for ci,(a,b) in enumerate(move.contacts):keys.extend(((a-3,(-1 if ci%2==0 else 1)*18),(a+1,(1 if ci%2==0 else -1)*22)))
            keys.append((end,0));twist=curve(keys);roll=twist*.14
            if heavy:
                load=0.
                for a,b in move.contacts:load+=curve(((0,0),(a-3,0),(a,.85),(b+2,.4),(min(end,b+5),0),(end,0)))
                root-=.65*max(0,min(1.2,load));lean+=5*max(0,min(1.,load))
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for ci,(a,b) in enumerate(move.contacts):
                    if ci%2!=i:continue
                    y=3.3 if front else 5.5 if ci%2==0 else 2.7
                    keys.extend(((max(1,a-4),(side*2.8,y+1,-.6)),(a,(side*.65,y,5.6)),
                                 (b+2,(-side*.6,y-.8,4.6))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
                feet[i]=add(ff[i],(0,.45*f.pulse(fno,first-4+i*3,first+5+i*3),.9*f.pulse(fno,first-4+i*3,last+2)))
        elif k in ('feint','charge'):
            lean+=curve(((0,0),(first-5,13),(first+2,-5),(last+3,6),(end,0)))
            twist=curve(((0,0),(first-4,-12),(first+1,16),(last+3,5),(end,0)))
            for i,side in enumerate((1,-1)):
                hands[i]=curve(((0,hh[i]),(first-5,(side*2.3,1.1 if front else 3.5,1.7)),
                    (first,(side*.9,3.0 if front else 5.,5.4)),(last+3,(side*2.5,1.4,3.9)),(end,hh[i])))
                feet[i]=add(ff[i],(0,.7*f.pulse(fno,first-6+i*2,first+3+i*2),1.2*f.pulse(fno,first-6+i*2,last+3)))
        elif k in ('vault','shear','crownfall'):
            jump=move.jumps[0][0] if move.jumps else first-5
            lean+=curve(((0,0),(jump-1,17),(jump+3,-13),(first+3,-4),(last+3,9),(end,0)))
            root-=.35*f.pulse(fno,0,jump+2)
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i]),(jump-1,(side*2.,.7,2.7)),(first-2,(side*2.6,5.8,1.5)),
                      (first+1,(side*.9,1.2,5.1)),(first+4,(side*2.2,.7,3.9))]
                if len(move.contacts)>1:
                    a,b=move.contacts[1]
                    if k=='crownfall':keys.extend(((a-3,(side*2.5,5.5,1.7)),(a,(side*1.5,1.9,3.2)),(b+2,(side*2.4,2.,2.8))))
                    else:keys.extend(((a-3,(side*2.5,2.6,1.7)),(a+1,(side*.6,1.2,5.3)),(b+2,(side*2.4,1.,3.8))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
                feet[i]=add(ff[i],(0,1.1*f.pulse(fno,jump,first+5),-.8*f.pulse(fno,jump,first+5)))
            if k=='crownfall':
                a,b=move.contacts[1];load=curve(((0,0),(a-5,0),(a,1),(b+2,.45),(end,0)))
                root-=2.1*max(0,load);lean+=24*max(0,load)
        elif k=='fugue':
            # Conduct the floor pulses with alternating open arms. A conjured
            # wave is a gesture, distinct from the Warden's physical bell slam.
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for ci,(a,b) in enumerate(move.contacts):
                    lead=ci%2==i
                    keys.extend(((max(1,a-5),(side*2.1,7.8,-.4)),(a,(side*(3.6 if lead else 2.5),4.8 if lead else 6.,3.4)),(b+3,(side*2.8,4.5,2.5))))
                keys.append((end,hh[i]));hands[i]=curve(keys)
            twist=curve(((0,0),*((a,(-1 if i%2==0 else 1)*17) for i,(a,b) in enumerate(move.contacts)),(end,0)))
            root-=.55*sum(f.pulse(fno,a-4,b+4) for a,b in move.contacts);lean+=5*math.sin(math.pi*time)**2
        elif k in ('quake','peal','march'):
            # One heavy downstroke, recoil into the next; hips, chest and head
            # trail the hammer rather than bouncing in separate eased poses.
            keys=[(0,hh[0])];tw=[]
            for ci,(a,b) in enumerate(move.contacts):
                keys.extend(((max(1,a-6),(2.,9.4,-.5)),(a-2,(1.3,5.5,2.4)),(a,(1.5,1.9 if style=='warden' else 1.8,3.2)),(b+2,(2.5,2.0,2.8))))
                tw.extend(((a-3,-12),(a+2,18),(b+3,4)))
            keys.append((end,hh[0]));hands[0]=curve(keys)
            hands[1]=tuple(hh[1][j]+(hands[0][j]-hh[0][j])*(.86 if k!='march' else .55) for j in range(3))
            twist=curve(((0,0),*tw,(end,0)));lean+=twist*.35
            load=0.
            for a,b in move.contacts:load+=curve(((0,0),(max(1,a-5),0),(a,1),(b+2,.55),(min(end,b+5),0),(end,0)))
            load=max(0,min(1.1,load));root-=2.1*load;lean+=24*load
        else:
            # Aim -> aperture opens -> recoil. A single continuous held aim
            # makes the moving high/low lane readable throughout release.
            release=curve(((0,0),(first-3,-.45),(first+1,1),(last,1),(min(end,last+4),.2),(end,0)))
            lean-=7*coil;root+=.16*coil;roll=1.5*math.sin(fno*.65)*max(0,release)
            for i,side in enumerate((1,-1)):
                hands[i]=add(hh[i],(side*release,.6*release,1.8*release-.35*coil))
            jaw+=18*max(0,release)
    p.t[1]=(0.,root,0.);p.r[1]=mm(axis('z',roll),mm(axis('y',twist*.28),mm(axis('x',lean),ROOT)))
    p.r[2]=axis('x',twist*.24);p.r[3]=axis('z',-lean*.08+twist*.08);p.r[4]=axis('z',-lean*.22+head)
    for i,(u,l,e) in enumerate(((20,21,22),(24,25,26))):
        side=1 if i==0 else -1;safe_ik(p,u,l,e,feet[i],(side*3,2,-2 if front else 3),(side,0,1));p.world_rotation(e,IDENTITY)
    for i,(u,l,e) in enumerate(old.arms(stem)):
        side=1 if i==0 else -1;safe_ik(p,u,l,e,hands[i],(side*4.5,3.4 if front else 6.2,-.8),(side,0,-1));p.world_rotation(e,axis('x',-8 if move and contact(move,fno) else 0))
        for j in (e+1,e+2):
            if j<19:p.r[j]=mm(axis('z',-12*max(0,math.sin(phase-.3*i))),p.r[j])
    _,ps=p.fk();headjoint=4 if heavy else 5
    f.locate(p,19,add(ps[headjoint],(0,-.4,1.1)),axis('x',-jaw))
    p.forge_scale={}
    for i,(j,effect) in enumerate(zip((23,27),old.fx(move,fno))):
        kind,y,z,ss=effect;point=(0.,y,z);rot=IDENTITY
        if kind=='claw':
            _,ps=p.fk();point=add(ps[old.arms(stem)[i][2]],(0,0,1.2));rot=axis('x',55);ss=(.55,.55,1.0)
        elif kind in ('beam','orb'):rot=axis('z',90)
        elif kind=='ring' and move and move.kind=='burst':rot=axis('x',90)
        f.locate(p,j,point,rot);p.forge_scale[j]=tuple(round(v*4096) for v in (*ss,*(1/max(.01,v) for v in ss)))
    return p


def geometry(raw,poses,move,style):
    # Resampling preserves unknown native records. Set the actual contact-enable
    # field too; GAB on/off alone never establishes a damaging strike.
    value=f.geometry(raw,poses,move,style)
    if move is None:return value
    wrap=CompressedBlob.parse(value);g=Gmb.parse(wrap.decoded);out=bytearray(wrap.decoded)
    for ch in g.channels:
        if ch.kind==3 and ch.words(0)[7]==8192:
            for i in range(g.record_count):struct.pack_into('<i',out,ch.offset+4+i*ch.stride+20,int(contact(move,i)))
    if Gmb.parse(out).to_bytes()!=out:raise ValueError('Contact geometry round trip')
    return wrap.replace_decoded(bytes(out),compact=True)


def duration(mode,n,style):
    if mode=='idle':return 40
    if mode=='walk':return 22 if style in ('warden','ballast','conductor') else 20
    if mode=='run':return 18 if style in ('warden','ballast','conductor') else 14
    return min(n,dict(recoil=11,knockdown=15,prone=20,rise=20,rise_attack=26,death=25,tumble=16,launch=12,land=12,coil=12,air=16,bound=18).get(mode,n))


def prepare(blob,names,style,stem,prefix):
    x=Xbd.parse(blob(stem+'.xbd'),names);idle=Sca.parse(blob(stem+'_Idle.sca'));parents=AnimationRig.parse(blob(stem+'.nsbmd')).parents
    actions=ActorActions.parse(x.raw,names);by_source={}
    for move in MOVES[style]:
        action=actions.lookup(move.action)
        if action is None:raise ValueError('Missing native action slot')
        by_source[next(b['name'] for b in action.bindings if b['tag']==0)]=move
    extras={prefix+'.xbd':x.raw};links={};clips=[]
    for i,b in enumerate(x.bindings):
        if b['tag']!=0:continue
        source=b['name'];a=Sca.parse(blob(source));move=by_source.get(source);mode=modes.mode(source)
        if move is None and mode in ('strike','slam','pounce','ranged'):
            move=MOVES[style][2 if mode=='ranged' else 1 if mode in ('pounce','slam') else 0]
        n=move.samples if move else duration(mode,a.frame_count,style);rise=mode=='rise_attack'
        if rise:move=Move('Rising retaliation',0,n,((round(n*.72),round(n*.84)),),'sweep',10)
        poses=[pose(idle,parents,style,stem,source,j,n,None if rise else move) for j in range(n)]
        end=next((j for j in range(i+1,len(x.bindings)) if x.bindings[j]['tag']==0),len(x.bindings))
        target=prefix+'_'+source;extras[target]=f.encode(blob(source),poses);links[b['offset']]=target
        for part in x.bindings[i+1:end]:
            target=prefix+'_'+source[:-4]+('.gmb' if part['tag']==3 else '.gab')
            if part['tag']==3:extras[target]=geometry(blob(part['name']),poses,move,style);links[part['offset']]=target
            elif part['tag']==4 and move:
                payload=b''.join(struct.pack('<3H',*e) for a,b in move.contacts for e in ((a,1,1),(b,1,5)))+b'\xff'*6
                extras[target]=payload+bytes(-len(payload)%4);links[part['offset']]=target
        clips.append(dict(source=source,resource=prefix+'_'+source,samples=n,move=move.name if move else None,mode=mode,contacts=move.contacts if move else []))
    return extras,{prefix+'.xbd':links},clips
