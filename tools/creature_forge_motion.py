"""Independent combat clips and full lifecycle choreography on exact bind rigs.

Selected moves have authored duration, multiple contact windows, continuous IK
arcs, follow-through, overlapping spine/head/claw motion and matching volumes.
"""
import math,struct
from tools import creature_forge_design as d,chapter_renewal_motion as prior
from tools.crane_creature_art import Pose as BindPose
from tools.kit_choreography import catmull,safe_ik
from tools.rush_choreography import ROOT,IDENTITY,axis,mm,mv,transpose,sub,add,stored
from tools.sca import Sca,Pool,align4
from tools.sca_author import sample
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd,Gab
from tools.actor_actions import ActorActions

REST={
 'maw':(2.8,38,((2.1,1.05,3.6),(-2.1,1.05,3.6)),((1.5,.65,-1.7),(-1.5,.65,-1.7))),
 'ballast':(4.7,10,((3.1,3.7,1.5),(-3.,4.0,.5)),((1.6,.65,1.),(-1.6,.65,-1.))),
 'spore':(4.4,8,((2.6,4.0,1.3),(-2.6,4.0,1.3)),((1.15,.65,-.5),(-1.15,.65,-.5))),
 'skitter':(3.0,50,((2.4,1.5,3.7),(-2.4,1.5,3.7)),((1.5,.65,-1.9),(-1.5,.65,-1.9))),
 'warden':(4.9,-4,((2.65,3.9,1.0),(-2.65,3.9,1.0)),((1.55,.65,.8),(-1.55,.65,-.8))),
 'eye':(4.8,-5,((3.1,4.6,1.0),(-3.1,4.6,1.0)),((1.1,.65,-.5),(-1.1,.65,-.5))),
 'conductor':(5.2,0,((3.1,4.5,1.3),(-3.1,4.5,.7)),((1.7,.65,1.),(-1.7,.65,-1.))),
}

def fast_mm(a,b):
    x,y,z=b
    return tuple((r[0]*x[0]+r[1]*y[0]+r[2]*z[0],r[0]*x[1]+r[1]*y[1]+r[2]*z[1],r[0]*x[2]+r[1]*y[2]+r[2]*z[2]) for r in a)

class DirtyList(list):
    def __init__(self,values,owner):super().__init__(values);self.owner=owner
    def __setitem__(self,index,value):
        super().__setitem__(index,value)
        self.owner.dirty=min(index,self.owner.dirty if self.owner.dirty is not None else 28)

class Pose(BindPose):
    """Same FK mathematics, reusing the unchanged ancestry during IK authoring."""
    def __init__(self,idle,parents):
        super().__init__(idle,parents);self.dirty=0;self.cache_r=[None]*28;self.cache_p=[None]*28
        self.r=DirtyList(self.r,self);self.t=DirtyList(self.t,self)
    def fk(self):
        if self.dirty is None:return self.cache_r,self.cache_p
        rs,ps=self.cache_r,self.cache_p
        for j in range(self.dirty,28):
            parent=self.parents[j]
            if parent is None:rs[j]=self.r[j];ps[j]=self.t[j]
            else:
                rs[j]=fast_mm(rs[parent],self.r[j]);x,y,z=self.t[j];pr=rs[parent];pp=ps[parent]
                ps[j]=(pp[0]+pr[0][0]*x+pr[0][1]*y+pr[0][2]*z,pp[1]+pr[1][0]*x+pr[1][1]*y+pr[1][2]*z,pp[2]+pr[2][0]*x+pr[2][1]*y+pr[2][2]*z)
        self.dirty=None;return rs,ps

def curve(keys,f):return catmull(sorted(dict(keys).items()),f)
def pulse(f,a,b):return math.sin(math.pi*max(0,min(1,(f-a)/max(1,b-a))))**2 if a<=f<=b else 0.

def locate(p,j,point,rotation=IDENTITY):
    rs,ps=p.fk();parent=p.parents[j]
    p.t[j]=mv(transpose(rs[parent]),sub(point,ps[parent]));p.world_rotation(j,rotation)

def pose(idle,parents,style,stem,source='Idle',f=0,n=1,move=None):
    p=Pose(idle,parents);p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.)
    # Creature proportions are authored in translation as well as rotation.
    # Longer forelimbs let the low predator actually plant its wrists; clamping
    # a human-length chain to a distant target produced stiff straight limbs.
    limb_length=1.55 if style in ('maw','skitter') else 1.4 if stem=='brt' else 1.22
    for u,l,e in d.arms(stem):
        for j in (l,e):p.t[j]=tuple(v*limb_length for v in p.t[j])
    root,lean,hh,ff=REST[style];hands=list(hh);feet=list(ff);twist=roll=head=0.;m=prior.mode(source)
    t=f/max(1,n-1);ph=math.tau*t;front=style in ('maw','skitter');heavy=stem=='brt'
    scale={};curl=0.;jaw=0.
    if move is not None:
        k=move.kind;first=move.contacts[0][0];last=move.contacts[-1][1];end=n-1
        wind=curve(((0,0),(max(1,first-5),1),(first,0),(min(end,first+4),-.25),(end,0)),f)
        snap=sum(pulse(f,a-2,b+3) for a,b in move.contacts)
        curl=-25*wind+18*snap;jaw=13*wind+22*snap
        root-=.5*wind+(.38 if heavy else .18)*snap
        lean+=(-12 if heavy else 13)*wind+(15 if heavy else -8)*snap
        head=-8*wind+9*curve(((0,0),(first+2,1),(last+6,.2),(end,0)),f)
        if k in ('scissor','sweep','pendulum','cadenza'):
            twist=curve(((0,0),(first-4,-30),(first+1,30),(last-4,-24),(last+2,25),(end,0)),f)
            roll=curve(((0,0),(first-3,-7),(first+3,5),(last+2,-4),(end,0)),f)
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for ci,(a,b) in enumerate(move.contacts):
                    if ci%2==i or len(move.contacts)==1:
                        high=k in ('sweep','pendulum','cadenza') and ci%2==0
                        keys.extend(((a-5,(side*3.2,7.5 if high else 2.3,-1.8)),(a,(side*.6,6.3 if high else 2.0,5.4)),
                                     (b+2,(-side*.5,3.0 if high else 1.3,4.0))))
                keys.append((end,hh[i]));hands[i]=curve(keys,f)
        elif k in ('feint','charge'):
            root-=.35*wind;lean+=15*wind+8*snap;twist=-8*wind
            for i,side in enumerate((1,-1)):
                hands[i]=curve(((0,hh[i]),(first-7,(side*2.6,1.3 if front else 3.5,1.4)),
                    (first,(side*1.1,2.8 if front else 4.8,5.2)),(last+2,(side*3.1,1.4,3.6)),(end,hh[i])),f)
            for i in range(2):
                v=pulse(f,first-7+i*3,last+3);feet[i]=add(ff[i],(0,.7*v,(-1 if i else 1)*.9*v))
        elif k in ('vault','shear','crownfall'):
            coil=pulse(f,2,first-3);air=pulse(f,first-6,last+1);lean+=20*coil-18*air;root-=.5*coil
            for i,side in enumerate((1,-1)):
                hands[i]=curve(((0,hh[i]),(first-7,(side*2.2,.9,2.0)),(first,(side*1.3,5.6,4.7)),
                    (last,(side*2.8,1.2,4.3)),(end,hh[i])),f)
                feet[i]=add(ff[i],(0,1.2*air,-1.1*air))
        elif k in ('quake','peal','fugue','march'):
            # Both hammers rise on a curved arc; subsequent strokes alternate.
            for i,side in enumerate((1,-1)):
                keys=[(0,hh[i])]
                for ci,(a,b) in enumerate(move.contacts):
                    keys.extend(((a-7,(side*1.4,9.0,-.5)),(a,(side*1.5,1.0,3.4)),(b+2,(side*2.6,1.4,2.7))))
                keys.append((end,hh[i]));hands[i]=curve(keys,f)
            lean+=15*snap;root-=.4*snap;roll=2*math.sin(f*.55)*snap
        elif k in ('beam','lance','verdict','seeds','twins','burst'):
            # Fold the aperture/petals before opening explosively, then leave
            # a readable silhouette throughout the sustained discharge.
            openq=curve(((0,0),(first-6,-.7),(first,1),(last,1),(last+5,.15),(end,0)),f)
            root+=.3*wind;lean-=10*wind;roll=3*math.sin(f*.45)*max(0,openq)
            for i,side in enumerate((1,-1)):
                hands[i]=add(hh[i],(side*(1.0*openq),.9*openq,-.5*wind+1.2*openq))
            head+=8*max(0,openq)
    elif m in ('idle','walk','run'):
        root+=(.055 if heavy else .11)*math.sin(ph*2);head=2.0*math.sin(ph-.8)
        if not heavy:twist=2*math.sin(ph);roll=1.5*math.sin(ph+.8)
        if m!='idle':
            stride=.65 if m=='walk' else 1.2
            # Stance travels linearly; swing clears the floor with a curved arc.
            for i,offset in enumerate((0,.5)):
                q=(t+offset)%1;stance=q<.6
                z=stride*(1-2*q/.6) if stance else stride*(-1+2*(q-.6)/.4)
                lift=0 if stance else .85*math.sin(math.pi*(q-.6)/.4)
                feet[i]=add(ff[i],(0,lift,z));s=math.sin(ph+i*math.pi)
                hands[i]=add(hh[i],(0,.7*max(0,-s)**2 if front else .1,-z if front else -.7*z))
            lean+=3;twist=5*math.sin(ph-.3);head=-3*math.sin(ph)
    elif m in ('knockdown','prone','rise','rise_attack','death','tumble','launch'):
        if m=='knockdown':q=curve(((0,0),(n*.25,.1),(n*.65,.95),(n-1,1)),f)
        elif m in ('rise','rise_attack'):q=curve(((0,1),(n*.3,.9),(n*.65,.5),(n-1,0)),f)
        elif m=='death':q=1-(1-t)**3
        elif m in ('tumble','launch'):q=.75;roll=15*math.sin(ph)
        else:q=1.
        root+=(.85-root)*q;lean+=(84-lean)*q;twist=-10*q;head=-18*q
        for i,side in enumerate((1,-1)):
            hands[i]=tuple(a+(b-a)*q for a,b in zip(hh[i],(side*2.5,.65,3.9)))
            feet[i]=tuple(a+(b-a)*q for a,b in zip(ff[i],(side*1.9,.5,-2.5)))
        if m in ('rise','rise_attack'):
            root-=.24*pulse(f,n*.35,n*.7);hands[0]=add(hands[0],(0,-.4*pulse(f,n*.2,n*.55),0))
        if m=='rise_attack':
            # Push off one planted hand, then whip the other claw through the
            # front instead of dealing a native get-up hit from a neutral pose.
            hands[1]=curve(((0,hands[1]),(n*.50,(-2.2,.6,2.9)),(n*.65,(-2.7,5.5,-.9)),
                            (n*.74,(-.7,3.5,5.0)),(n*.84,(-1.8,2.4,4.0)),(n-1,hh[1])),f)
            twist+=24*pulse(f,n*.6,n*.9)
    elif m=='recoil':
        q=curve(((0,0),(n*.2,1),(n*.6,-.16),(n-1,0)),f);lean-=20*q;twist=8*q;head=-15*curve(((0,0),(n*.3,1),(n-1,0)),f)
        root-=.25*q;hands=[add(v,(0,.45*q,-.65*q)) for v in hands]
    elif m=='bound':
        lean+=10;root-=.3;hands=[(x*.55,y+.6,z-.6) for x,y,z in hands];head=4*math.sin(ph*2)
    elif m=='land':
        q=pulse(f,0,n-1);root-=.65*q;lean+=12*q;hands=[add(v,(0,-.5*q,.5*q)) for v in hands]
    elif m in ('air','coil'):
        q=t if m=='coil' else 1;root-=.3*q;hands=[add(v,(0,.7*q,.3*q)) for v in hands];feet=[add(v,(0,.6*q,-.5*q)) for v in feet]
    p.t[1]=(0.,root,0.);p.r[1]=mm(axis('z',roll),mm(axis('y',twist*.28),mm(axis('x',lean),ROOT)))
    # Overlap: pelvis initiates, chest counterrotates, head settles later.
    p.r[2]=axis('x',twist*.28);p.r[3]=axis('z',-lean*.08);p.r[4]=axis('z',-lean*.24+head)
    for i,(u,l,e) in enumerate(((20,21,22),(24,25,26))):
        side=1 if i==0 else -1;safe_ik(p,u,l,e,feet[i],(side*3,2,-2 if front else 3),(side,0,1));p.world_rotation(e,IDENTITY)
    for i,(u,l,e) in enumerate(d.arms(stem)):
        side=1 if i==0 else -1;safe_ik(p,u,l,e,hands[i],(side*4.8,3 if front else 6.5,-.8),(side,0,-1));p.world_rotation(e,axis('y',side*7*math.sin(ph)))
        # Secondary digits follow through rather than retaining native fingers.
        for j in (e+1,e+2):
            if j<19:p.r[j]=mm(axis('z',curl+8*math.sin(ph-.6*i)),p.r[j])
    # A repurposed thumb/gut matrix drives an independent lower jaw/aperture.
    # It has no skinned body geometry or gameplay pointer attached to it.
    _,ps=p.fk();headjoint=4 if heavy else 5
    locate(p,19,add(ps[headjoint],(0,-.4,1.1)),axis('x',-jaw))
    for i,(j,effect) in enumerate(zip((23,27),d.fx(move,f))):
        kind,y,z,ss=effect;point=(0.,y,z);rot=IDENTITY
        if kind=='claw':
            e=d.arms(stem)[i][2];rs,ps=p.fk();point=add(ps[e],(0,0,1.2));rot=axis('x',55)
            ss=(.6,.6,1.1)
        elif kind=='beam':rot=axis('z',90)
        elif kind=='orb':rot=axis('z',90)
        elif kind=='ring' and move and move.kind=='burst':rot=axis('x',90)
        locate(p,j,point,rot);scale[j]=tuple(round(v*4096) for v in (*ss,*(1/max(.01,v) for v in ss)))
    p.forge_scale=scale
    return p

def encode(template,poses):
    """Build private SCA pools, retaining header flags and exact bind scales."""
    a=Sca.parse(template);static=[[],[],[]];dynamic=[[],[],[]];desc=[[0,0,0] for _ in range(28)]
    for comp,(group,name) in enumerate(((0,'translation'),(2,'rotation'),(1,'scale'))):
        for j in range(28):
            if name=='translation':values=tuple(tuple(round(q*4096) for q in p.t[j]) for p in poses)
            elif name=='rotation':values=tuple(stored(p.r[j]) for p in poses)
            else:values=tuple(p.forge_scale.get(j,sample(a,j,0,'scale')) for p in poses)
            const=len(set(values))==1;pool=static[group] if const else dynamic[group];key=values[0] if const else values
            if key not in pool:pool.append(key)
            idx=pool.index(key)
            if idx>=128:raise ValueError('Forge track index overflow')
            desc[j][comp]=idx*2+int(const)
    counts=tuple(map(len,static))+tuple(map(len,dynamic));sz=12*counts[0]+24*counts[1]+18*counts[2];stride=align4(12*counts[3]+24*counts[4]+18*counts[5]);pad=stride-(12*counts[3]+24*counts[4]+18*counts[5])
    head=bytearray(a.header);struct.pack_into('<4I',head,4,len(poses),28,sz,stride);head[20:26]=bytes(counts)
    out=bytes(head)+b''.join(bytes(v) for v in desc)+a.descriptor_padding+Pool(*map(tuple,static),bytes(align4(sz)-sz)).to_bytes()
    out+=b''.join(Pool(*(tuple(track[f] for track in g) for g in dynamic),bytes(pad)).to_bytes() for f in range(len(poses)))
    b=Sca.parse(out)
    if b.to_bytes()!=out:raise ValueError('Private SCA round trip failed')
    return out

def geometry(raw,poses,move,style):
    wrap=CompressedBlob.parse(raw);a=Gmb.parse(wrap.decoded);n=len(poses);data=bytearray(struct.pack('<4H',a.unknown_u16_00,n,len(a.channels),a.unknown_u16_06))
    for c in a.channels:
        data.extend(struct.pack('<hH',c.kind,c.unknown_u16_02))
        for f,p in enumerate(poses):
            rec=bytearray(c.records[min(a.record_count-1,round(f*(a.record_count-1)/max(1,n-1)))]);words=struct.unpack('<'+'i'*(len(rec)//4),rec)
            if c.kind==3 and words[7] in (0,4096):
                root,lean,hh,ff=REST[style];height=7. if style in ('maw','skitter') else 11. if style=='conductor' else 9.
                # Flatten both body shapes during actual prone clips.
                prone=p.t[1][1]<1.6;height=2.4 if prone else height
                shape=(height/2,0.,height,3.4 if style in ('ballast','conductor') else 2.6)
                struct.pack_into('<4i',rec,4,*(round(v*4096) for v in shape))
            elif c.kind==3 and words[7]==8192 and move:
                struct.pack_into('<4i',rec,4,*(round(v*4096) for v in d.hit_shape(move,f)))
            elif c.kind==0 and words[6]==36864:
                _,ps=p.fk();v=add(ps[5 if style not in ('ballast','warden','conductor') else 15],(0,0,1.0))
                struct.pack_into('<3i',rec,0,0,round(v[1]*4096),round(v[2]*4096))
            data.extend(rec)
    Gmb.parse(data)
    return wrap.replace_decoded(bytes(data),compact=True)

def prepare(blob,names,style,stem,prefix):
    x=Xbd.parse(blob(stem+'.xbd'),names);idle=Sca.parse(blob(stem+'_Idle.sca'));parents=AnimationRig.parse(blob(stem+'.nsbmd')).parents
    actions=ActorActions.parse(x.raw,names);by_source={}
    for move in d.MOVES[style]:
        action=actions.lookup(move.action)
        if action is None or not {0,3,4}.issubset({b['tag'] for b in action.bindings}):raise ValueError('Move needs existing SCA/GMB/GAB binding slots')
        by_source[next(b['name'] for b in action.bindings if b['tag']==0)]=move
    extras={prefix+'.xbd':x.raw};links={};clips=[]
    for i,b in enumerate(x.bindings):
        if b['tag']!=0:continue
        source=b['name'];raw=blob(source);a=Sca.parse(raw);move=by_source.get(source);mode=prior.mode(source)
        # Native navigation/reactive controllers can request other attack slots
        # (air pounce, strong hit, get-up retaliation). Those routes also receive
        # the new choreography/contact data instead of standing on a blank pose.
        if move is None and mode in ('strike','slam','pounce','ranged'):
            index=2 if mode=='ranged' else 1 if mode in ('pounce','slam') else 0
            move=d.MOVES[style][index]
        n=move.samples if move else a.frame_count
        rise=mode=='rise_attack'
        if rise:
            move=d.Move('Rising retaliation',0,n,((round(n*.72),round(n*.84)),),'sweep',10)
        poses=[pose(idle,parents,style,stem,source,f,n,None if rise else move) for f in range(n)]
        end=next((j for j in range(i+1,len(x.bindings)) if x.bindings[j]['tag']==0),len(x.bindings));parts=x.bindings[i+1:end]
        target=prefix+'_'+source;extras[target]=encode(raw,poses);links[b['offset']]=target
        for part in parts:
            target=prefix+'_'+source[:-4]+('.gmb' if part['tag']==3 else '.gab')
            if part['tag']==3:extras[target]=geometry(blob(part['name']),poses,move,style);links[part['offset']]=target
            elif part['tag']==4 and move:
                events=tuple(v for a,b in move.contacts for v in ((a,1,1),(b,1,5)))
                payload=b''.join(struct.pack('<3H',*e) for e in events)+b'\xff'*6
                payload+=bytes(-len(payload)%4)
                extras[target]=payload;Gab.parse(payload);links[part['offset']]=target
        clips.append(dict(source=source,resource=prefix+'_'+source,samples=n,move=move.name if move else None,mode=prior.mode(source),contacts=move.contacts if move else []))
    return extras,{prefix+'.xbd':links},clips
