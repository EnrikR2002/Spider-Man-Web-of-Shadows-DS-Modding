"""Species choreography, including prone knockdown and get-up transitions.

Continuous trajectories are authored on the original bind rig. All SCA bindings
are replaced privately; contact clocks and body volumes are rebuilt together.
"""
import math,struct
from tools import crane_creature_motion as old, crane_creatures as cc
from tools.crane_creature_art import Pose
from tools.kit_choreography import catmull,safe_ik
from tools.rush_choreography import ROOT,IDENTITY,mm,mv,axis,stored,add,sub,transpose
from tools.sca import Sca,Pool,align4
from tools.sca_author import repack_samples,sample
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd,Gab

STYLES=('maw','ballast','spore','skitter','warden','eye','conductor')
KINDS=dict(zip(STYLES,('maw','ballast','spore','maw','ballast','spore','ballast')))

def compact_private(raw):
    """Rebuild only private animations, with every sampled TRS value exact.

    Native authoring appends tracks to preserve the source. Shipping seven
    sets must remove those now-unreferenced pools and share constant tracks.
    No nonzero opaque/alignment bytes may be discarded.
    """
    a=Sca.parse(raw)
    if any(a.static_pool.padding) or any(any(p.padding) for p in a.frames):raise ValueError('Nonzero SCA pool alignment')
    static=[[],[],[]];dynamic=[[],[],[]];descriptors=[[0,0,0] for _ in range(a.joint_count)]
    for component,(channel,group) in enumerate((('translation',0),('rotation',2),('scale',1))):
        for j in range(a.joint_count):
            values=tuple(sample(a,j,f,channel) for f in range(a.frame_count));constant=len(set(values))==1
            pool=static[group] if constant else dynamic[group];key=values[0] if constant else values
            if key not in pool:pool.append(key)
            index=pool.index(key)
            if index>=128:raise ValueError('Private SCA track index overflow')
            descriptors[j][component]=index*2+int(constant)
    counts=tuple(map(len,static))+tuple(map(len,dynamic));poolsize=12*counts[0]+24*counts[1]+18*counts[2]
    stride=align4(12*counts[3]+24*counts[4]+18*counts[5]);padding=stride-(12*counts[3]+24*counts[4]+18*counts[5])
    header=bytearray(a.header);struct.pack_into('<2I',header,12,poolsize,stride);header[20:26]=bytes(counts)
    rawpool=Pool(*map(tuple,static),bytes(align4(poolsize)-poolsize)).to_bytes()
    frames=b''.join(Pool(*(tuple(track[f] for track in group) for group in dynamic),bytes(padding)).to_bytes() for f in range(a.frame_count))
    result=bytes(header)+b''.join(bytes(d) for d in descriptors)+a.descriptor_padding+rawpool+frames;b=Sca.parse(result)
    if b.to_bytes()!=result:raise ValueError('Private animation framing changed')
    for j in range(a.joint_count):
        for f in range(a.frame_count):
            for channel in ('translation','rotation','scale'):
                if sample(a,j,f,channel)!=sample(b,j,f,channel):raise ValueError('Compaction changed a pose')
    return result

def mode(source):
    if 'HurtLandGetUpAttack' in source:return 'rise_attack'
    if 'HurtLandGetUp' in source:return 'rise'
    if any(x in source for x in ('HurtLandFace','HurtLandHit','HurtLandTumble','HurtLand.')):return 'prone'
    if 'HurtKnockDown' in source:return 'knockdown'
    if 'HurtKnockUp' in source:return 'launch'
    if 'HurtFall' in source or 'HurtAir' in source:return 'tumble'
    if 'Die' in source or 'Explode' in source:return 'death'
    if 'Hurt' in source or 'BlockImpact' in source:return 'recoil'
    if 'Grappl' in source:return 'bound'
    if 'LeapAttackPrep' in source:return 'coil'
    if 'Attack' in source or 'Throw' in source or 'Kick' in source:
        return 'ranged' if 'Ranged' in source or 'ThrowIchor' in source else 'slam' if 'Attack2' in source or 'DropDown' in source else 'pounce' if 'Leap' in source else 'strike'
    if 'Run' in source or 'Crawl' in source:return 'run'
    if 'Walk' in source:return 'walk'
    if 'Land' in source:return 'land'
    if any(x in source for x in ('Jump','Fall','Fly','Wings')):return 'air'
    if any(x in source for x in ('Prep','Duck','Burrow')):return 'coil'
    return 'idle'

def curve(keys,t):return catmull(sorted(dict(keys).items()),t)

def pose(idle,parents,style,source,frame,frames,impact,recovery):
    kind=KINDS[style];cfg=old.BASE[kind];p=Pose(idle,parents)
    p.r[0]=IDENTITY;p.t[0]=(0.,0.,0.)
    root=cfg['root'];lean=cfg['lean'];roll=0;twist=0;head=0
    hands=list(cfg['hands']);feet=list(cfg['feet']);m=mode(source)
    t=frame/max(1,frames-1);phase=t*2*math.pi
    # Species share a rig, but their cadence and silhouette do not share a clip.
    if m in ('idle','walk','run'):
        amp=.09 if style in ('ballast','warden','conductor') else .18
        root+=amp*math.sin(phase*2)
        if style in ('spore','eye'):root+=.23*math.sin(phase);roll=3*math.sin(phase)
        if style=='skitter':lean+=3*math.sin(phase*2);twist=4*math.sin(phase)
        if m!='idle':
            stride=.7 if m=='walk' else 1.3
            for i,off in enumerate((0,math.pi)):
                s=phase+off;x,y,z=feet[i];feet[i]=(x,y+.7*max(0,math.sin(s))**2,z+stride*math.cos(s))
                x,y,z=hands[i]
                hands[i]=(x,y+(.6 if kind=='maw' else .1)*max(0,-math.sin(s))**2,z-stride*.65*math.cos(s))
    elif m in ('knockdown','prone','rise','rise_attack','death','launch','tumble'):
        # A genuine flattened silhouette; the old generic hurt clip returned
        # upright while the engine still considered the creature grounded.
        if m=='knockdown':q=math.sin(t*math.pi/2)
        elif m in ('rise','rise_attack'):q=1-(3*t*t-2*t*t*t)
        elif m=='death':q=1-(1-t)**3
        elif m=='launch':q=.3+.55*math.sin(t*math.pi/2)
        elif m=='tumble':q=.85;roll=18*math.sin(phase)
        else:q=1
        root+=(1.0-root)*q;lean+=(82-lean)*q
        twist=(12 if style in ('maw','skitter') else -12)*q;head=-14*q
        for i,side in enumerate((1,-1)):
            hands[i]=tuple(a+(b-a)*q for a,b in zip(hands[i],(side*2.5,.6,3.8)))
            feet[i]=tuple(a+(b-a)*q for a,b in zip(feet[i],(side*1.9,.6,-2.0)))
        if m=='launch':root+=.4*math.sin(math.pi*t)
    elif m=='recoil':
        q=math.sin(math.pi*t)*(1-.35*t);lean-=23*q;head=-18*q;root-=.25*q
        hands=[add(v,(0,.45*q,-.65*q)) for v in hands]
    elif m=='bound':
        root-=.3;lean+=8;hands=[(x*.45,y+.7,z-.6) for x,y,z in hands];head=5*math.sin(phase)
    elif m=='coil':
        q=3*t*t-2*t*t*t;root-=.5*q;lean+=12*q;hands=[add(v,(0,.4*q,-.9*q)) for v in hands]
    elif m=='air':
        root-=.1;hands=[add(v,(0,.65,.3)) for v in hands];feet=[add(v,(0,.5,-.4)) for v in feet]
    elif m=='land':
        q=math.sin(math.pi*t);root-=.6*q;lean+=10*q;hands=[add(v,(0,-.3*q,.4*q)) for v in hands]
    else:
        end=max(1,frames-1);hit=max(1,min(impact,end-1));ready=max(0,hit-3);stop=min(end,max(hit+2,recovery))
        q=curve(((0,0),(ready,1),(hit,-.25),(stop,-.1),(end,0)),frame)
        burst=curve(((0,0),(ready,0),(hit,1),(stop,.2),(end,0)),frame)
        if kind=='maw':
            # Dock: rear-loaded hook and bite. Rail: paired scythe projection.
            rail=style=='skitter';lean+=14*q-12*burst;root-=.4*q;head=9*burst
            twist=(24 if not rail else -12)*burst
            for i,side in enumerate((1,-1)):
                start=hands[i];reach=(side*(.8 if rail else 1.6),1.4 if m=='slam' else 3.2,5.4 if rail else 4.8)
                hands[i]=curve(((0,start),(ready,(side*2.7,.9,1.4)),(hit,reach),(stop,(side*2.8,.7,3.4)),(end,start)),frame)
            if m=='pounce':root+=.5*burst;feet=[add(v,(0,.8*burst,-.6*burst)) for v in feet]
        elif kind=='ballast':
            bell=style in ('warden','conductor');root-=.45*q+.5*burst;lean+=-12*q+25*burst
            twist=(18 if bell else 42)*curve(((0,0),(ready,-.8),(hit,.4),(stop,1),(end,0)),frame)
            for i,side in enumerate((1,-1)):
                start=hands[i]
                up=(side*(1.3 if bell else 2.1),9.0,-.3)
                down=(side*.9,1.1,3.8) if m=='slam' else (side*1.4,5.0,5.0)
                if not bell and m!='slam' and i==0:up=(3.3,5.0,-3.0);down=(1.2,4.3,5.5)
                hands[i]=curve(((0,start),(ready,up),(hit,down),(stop,(side*2.2,2.2,3.0)),(end,start)),frame)
            if style=='conductor':roll=8*q;head=-12*q
        else:
            # Lantern coils down before releasing; Arc Eye opens vertically.
            eye=style=='eye';root+=(-.5 if not eye else .4)*q;lean+=-18*q+16*burst;head=-20*q+24*burst
            for i,side in enumerate((1,-1)):
                start=hands[i]
                hands[i]=curve(((0,start),(ready,(side*.7,6.7 if eye else 4.4,1.8)),
                    (hit,(side*(3.8 if eye else 2.8),6 if eye else 3.4,4.1)),(stop,(side*3.0,4.6,2.0)),(end,start)),frame)
            roll=(6 if eye else -6)*burst
    p.t[1]=(0.,root,0.)
    p.r[1]=mm(axis('z',roll),mm(axis('y',twist*.4),mm(axis('x',lean),ROOT)))
    p.r[2]=axis('x',twist*.35);p.r[3]=axis('z',-lean*.1);p.r[4]=axis('z',-lean*.4+head)
    rotations,_=p.fk()
    for i,(u,l,e,side) in enumerate(((20,21,22,1),(24,25,26,-1))):
        safe_ik(p,u,l,e,feet[i],(side*3,2,-2 if kind=='maw' else 2),(side,0,1));p.world_rotation(e,rotations[e])
    for i,(u,l,e,side) in enumerate(((6,7,8,1),(13,14,15,-1))):
        safe_ik(p,u,l,e,hands[i],(side*4.5,2.5 if kind=='maw' else 6,1 if kind=='maw' else -1.4),(side,0,-1));p.world_rotation(e,rotations[e])
    return p

def prepare(blob,names,style,stem,prefix):
    xbd=Xbd.parse(blob(stem+'.xbd'),names);idle=Sca.parse(blob(stem+'_Idle.sca'))
    parents=AnimationRig.parse(blob(stem+'.nsbmd')).parents;extras={prefix+'.xbd':xbd.raw};mapping={};clips=[]
    neutral=old.neutral(idle,parents,KINDS[style]);r0,p0=neutral.fk();joint=4 if KINDS[style]=='maw' else 5 if KINDS[style]=='spore' else 15
    local=mv(transpose(r0[joint]),sub(add(p0[joint],(0,.3,1.6)),p0[joint]))
    for i,b in enumerate(xbd.bindings):
        if b['tag']!=0:continue
        source=b['name'];raw=blob(source);sca=Sca.parse(raw)
        end=next((j for j in range(i+1,len(xbd.bindings)) if xbd.bindings[j]['tag']==0),len(xbd.bindings))
        parts=xbd.bindings[i+1:end];gab=next((blob(v['name']) for v in parts if v['tag']==4),None)
        old_gab=gab
        if gab is not None and source in ('brt_GroundAttack2.sca','hLpr_LeapAttack.sca'):
            changed=bytearray(gab)
            for j,(f,event,value) in enumerate(Gab.parse(gab).records):
                if event==1 and value==1 and f==2:struct.pack_into('<H',changed,j*6,6)
                elif source=='brt_GroundAttack2.sca' and event==1 and value==5 and f==6:struct.pack_into('<H',changed,j*6,11)
            gab=bytes(changed);Gab.parse(gab)
        impact,recovery=cc.contact_window(gab,sca.frame_count)
        # Every attack's anticipation reaches its first actual contact; short
        # native clocks are retained so no animation extends a damage window.
        rotations={j:[] for j in range(28)};translations={j:[] for j in range(28)};positions=[];refs=[]
        for f in range(sca.frame_count):
            p=pose(idle,parents,style,source,f,sca.frame_count,impact,recovery);rs,ps=p.fk();positions.append(ps);refs.append(add(ps[joint],mv(rs[joint],local)))
            for j in range(28):rotations[j].append(stored(p.r[j]));translations[j].append(tuple(round(v*4096) for v in p.t[j]))
        name=prefix+'_'+source;extras[name]=compact_private(repack_samples(raw,rotations=rotations,translations=translations));mapping[b['offset']]=name
        if gab!=old_gab:
            target=prefix+'_'+source[:-4]+'.gab';extras[target]=gab
            event=next(part for part in parts if part['tag']==4);mapping[event['offset']]=target
        for part in parts:
            if part['tag']!=3:continue
            target=prefix+'_'+source[:-4]+'.gmb'
            motion_mode={'strike':'attack','pounce':'leap','ranged':'spit','slam':'slam','rise_attack':'attack'}.get(mode(source),mode(source))
            extras[target]=cc.geometry_motion(blob(part['name']),KINDS[style],positions,refs,motion_mode,source);mapping[part['offset']]=target
        clips.append(dict(source=source,resource=name,mode=mode(source),frames=sca.frame_count,contact=impact))
    return extras,{prefix+'.xbd':mapping},clips
