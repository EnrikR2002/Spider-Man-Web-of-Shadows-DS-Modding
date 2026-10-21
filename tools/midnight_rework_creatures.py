"""Midnight's original electrical fauna, native rig/AI chassis and private audio.

Adapter fallbacks chain the accepted Crane composition. No original actor,
animation, texture, sound or reward record is overwritten.
"""
import math,struct
from tools import crane_creatures as cc, crane_creature_art as art, crane_audio as audio, sdat, wos_tool as w
from tools.crane_boss import Arm
from tools.crane_row import branch
from tools.rush_choreography import add

CREATURES=(cc.Creature('maw','Rail Skitter',21,'hLpr',7,1),
           cc.Creature('ballast','Bell Warden',36,'brt',10,2),
           cc.Creature('spore','Arc Eye',20,'hRng',6,1))
BOSS=cc.Creature('ballast','The Conductor',36,'brt',64,2)
FIRST_SOUND=597

def model(spec,template,texture,pose,*,boss=False):
    mesh,p,groups,bind=art._writer(template,pose)
    rgb=art.rgb;steel=rgb(9,15,23);ivory=rgb(26,28,28);light=rgb(8,30,31);gold=rgb(31,20,5);dark=rgb(2,5,10)
    def ell(j,c,r,col,sides=6,rings=3):bind(j,art.ellipsoid(c,r,col,sides,rings))
    def tube(j,a,b,r0,r1,col):bind(j,art.tube(a,b,r0,r1,col,sides=5))
    if spec.key=='maw':
        # Long segmented centipede/mantis chassis, blade mandibles and six
        # angular legs; none of the original humanoid geometry survives.
        for j,rad in ((1,1.1),(2,1.25),(3,1.45)):
            ell(j,add(p[j],(0,.15,-.3)),(rad,.75,1.3),steel)
        head=add(p[4],(0,-.15,.9));ell(4,head,(1.05,.65,1.4),ivory)
        for side in (-1,1):
            ell(4,add(head,(side*.65,.25,1)),(.22,.22,.3),light,4,2)
            tube(4,add(head,(side*.7,-.1,.8)),add(head,(side*.5,-.15,2.2)),.22,.015,gold)
            for z in (-1.3,0,1.3):
                a=add(p[3],(side*.9,.1,z));b=add(a,(side*1.5,.3,-.5));c=add(b,(side*.6,-1.7,.4))
                tube(3,a,b,.2,.14,ivory);tube(3,b,c,.14,.02,steel)
    elif spec.key=='spore':
        # Floating ring-like eye on four electrical tendrils, tripod outline.
        centre=add(p[3],(0,.7,.2));ell(3,centre,(2.3,1.7,1.3),steel,8)
        ell(4,add(centre,(0,.3,1.0)),(1.6,1.5,.6),ivory,8)
        ell(4,add(centre,(0,.3,1.5)),(1.2,1.15,.2),dark,8)
        ell(4,add(centre,(0,.3,1.7)),(.65,.7,.12),light,8)
        for side in (-1,1):
            tube(4,add(centre,(side*1.5,1.1,0)),add(centre,(side*3,2.8,-.8)),.17,.02,gold)
    else:
        # Bell silhouette: narrow luminous waist, split brass carapace,
        # suspended eye and asymmetric fork arms. Boss carries a radial halo.
        centre=add(p[3],(0,.2,0));ell(3,centre,(2.25,1.6,1.6),steel,8)
        ell(2,p[2],(1.1,1.1,1.0),light)
        head=add(p[4],(0,.4,.5));ell(4,head,(1.0,1.6,1.0),dark)
        ell(4,add(head,(0,.25,.9)),(.5,.8,.2),light)
        for side in (-1,1):
            for z in (-.8,.6):
                a=add(centre,(side*1.5,.8,z));b=add(a,(side*1.3,-2.7,.3))
                tube(3,a,b,.65,.95,gold if z>0 else ivory)
        if boss:
            for n in range(10):
                a=n*2*math.pi/10;b=(n+1)*2*math.pi/10
                q=add(head,(3.3*math.cos(a),3.3*math.sin(a),-.7))
                qq=add(head,(3.3*math.cos(b),3.3*math.sin(b),-.7))
                tube(4,q,qq,.14,.14,gold)
                tube(4,q,add(q,(math.cos(a),math.sin(a),0)),.18,.01,light)
    for upper,lower,end in ((6,7,8),(13,14,15),(20,21,22),(24,25,26)):
        front=upper in (6,13)
        tube(upper,p[upper],p[lower],.28 if front else .23,.2,ivory)
        tube(lower,p[lower],p[end],.3 if spec.key=='ballast' and front else .19,.12,steel)
        for side in (-1,1):
            a=add(p[end],(side*.22,0,0));b=add(a,(side*.25,-.15,1.1 if front else .7))
            tube(end,a,b,.15,.02,gold)
    return art._finish(template,texture,mesh,groups)

def prepare(blob,names):
    extras,links,report=cc.prepare(blob,names,specs=CREATURES,prefix_base='zz_MLR_',model_author=model)
    boss,bl,br=cc.prepare(blob,names,specs=(BOSS,),prefix_base='zz_MLR_Boss_',
        model_author=lambda *a:model(*a,boss=True))
    extras.update(boss);links.update(bl);report['boss']=br['ballast']
    return extras,links,report

def scope(a,fallback):
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b(fallback,0)
    a.emit(0xE5923000,0xE353004C);a.b(fallback,3);a.emit(0xE3530060);a.b(fallback,2)

def config_adapter(at,configs,old):
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000);scope(a,'fallback')
    a.emit(0xE3530059);a.b('bossroom',0)
    for c in CREATURES:a.emit(0xE3510000|c.kind);a.b(c.key,0)
    a.b('fallback');a.label('bossroom');a.emit(0xE3510024);a.b('boss',0);a.b('fallback')
    for key in (*[c.key for c in CREATURES],'boss'):
        a.label(key);a.lit(2,key,configs[key]);a.b('store')
    a.label('store');a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500F);a.b(old)
    return a.finish()

def variant_adapter(at,state,old):
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000);scope(a,'fallback')
    a.emit(0xE3530059);a.b('boss',0)
    a.lit(2,'state',state);a.emit(0xE5921000,0xE1510003);a.b('same',0)
    a.emit(0xE5823000,0xE3A01000,0xE5821004)
    a.label('same');a.emit(0xE5921004,0xE3510003,0x23A01000,0xE2813001,0xE5823004)
    for i,c in enumerate(CREATURES):a.emit(0xE3510000|i);a.b(c.key,0)
    a.b('fallback')
    for c in CREATURES:a.label(c.key);a.emit(0xE3A02000|c.kind);a.b('store')
    a.label('boss');a.emit(0xE3A02024)
    a.label('store');a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500F);a.b(old)
    return a.finish()

def goal_adapter(at,goals,old):
    a=Arm(at);a.emit(0xE92D4070,0xE1A04000,0xE1A05001);a.b(old,link=True)
    a.emit(0xE92D100F,0xE10F6000);scope(a,'restore')
    a.emit(0xE3530059);a.b('boss',0)
    for key in ('patrol','upper'):
        if key=='patrol':a.emit(0xE355000E);a.b('upper',0)
        a.label(key);a.lit(2,key,goals[key]);a.b('store')
    a.label('boss');a.lit(2,'boss',goals['boss'])
    a.label('store');a.emit(0xE5842000)
    a.label('restore');a.emit(0xE128F006,0xE8BD100F,0xE8BD4070,0xE12FFF1E)
    return a.finish()

def reward_adapter(at,record,old):
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000,0xE351001F);a.b('fallback',1)
    scope(a,'fallback');a.lit(2,'reward',record);a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500F);a.b(old)
    return a.finish()

def voice(kind,category):
    rate=11025;duration=(.4,.36,.9,.2,.36)[audio.CATEGORIES.index(category)];n=round(rate*duration);n+=-n%4
    data=bytearray();noise=0x735B;phase=0
    for i in range(n):
        u=i/max(1,n-1);t=i/rate;noise=(noise*1664525+1013904223)&0xFFFFFFFF;v=(noise>>16)/32767.5-1
        f=(125 if kind=='boss' else 260 if kind=='spore' else 90 if kind=='ballast' else 680)*(1-.5*u if category=='death' else 1+.2*math.sin(t*25))
        phase+=2*math.pi*f/rate
        bell=math.sin(phase)+.35*math.sin(phase*2.71)+.2*math.sin(phase*4.07)
        env=min(1,u*35)*(1-u)**1.3
        value=(bell*.35+v*.18*(.5+.5*math.sin(t*180)))*env
        data.append(round(max(-1,min(1,value))*110)&255)
    return struct.pack('<BBHHHI',0,0,rate,round(16756991/rate),0,len(data)//4)+data

def sound_data(raw):
    archive=sdat.Sdat.parse(raw);ids=(archive.file_id(1,0),archive.file_id(2,20),archive.file_id(3,0))
    seq,bank,wave=(archive.blob(i) for i in ids)
    if (w.u32(seq,0x1C),w.u32(bank,0x38),w.u32(wave,0x38))!=(597,)*3:raise ValueError('Expected accepted Crane audio parent')
    waves=[];notes=[];sequences=[]
    for i,(key,cat) in enumerate((k,c) for k in ('ballast','spore','maw','boss') for c in audio.CATEGORIES):
        slot=FIRST_SOUND+i;waves.append(voice(key,cat));notes.append(struct.pack('<HH6B',slot,0,60,127,127,127,127,64))
        sequences.append((306,bytes((0x81,0x80|(slot>>7),slot&127,60,110,0,0xFF))))
    return archive.replace({ids[0]:sdat.append_sequences(seq,sequences),ids[1]:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),ids[2]:sdat.append_indexed(wave,b'SWAR',waves)})

def sound_adapter(at,old):
    a=Arm(at);a.emit(0xE92D500D,0xE10FC000);scope(a,'fallback')
    a.emit(0xE3530059);a.b('boss',0)
    a.lit(2,'normal');a.b('loop');a.label('boss');a.lit(2,'boss')
    a.label('loop');a.emit(0xE5920000,0xE3500000);a.b('fallback',0)
    a.emit(0xE1510000);a.b('next',3)
    a.emit(0xE5920004,0xE1510000);a.b('next',8)
    a.emit(0xE5921008);a.b('selected')
    a.label('next');a.emit(0xE282200C);a.b('loop')
    a.label('selected');a.emit(0xE128F00C,0xE8BD500D,0xE92D40F0);a.b(audio.SITE+4)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500D);a.b(old)
    a.blob('normal',b''.join(struct.pack('<3I',lo,hi,FIRST_SOUND+i) for i,(lo,hi) in enumerate(audio.RANGES))+bytes(12))
    a.blob('boss',b''.join(struct.pack('<3I',lo,hi,FIRST_SOUND+15+i) for i,(lo,hi) in enumerate(audio.RANGES[:5]))+bytes(12))
    return a.finish()

def spore_adapter(at,config,old):
    """Give the ranged chassis the authored attack/hurt/death one-shots too."""
    a=Arm(at);a.emit(0xE92D503F,0xE10F5000,0xE1A04000);scope(a,'native')
    a.emit(0xE5942000);a.lit(3,'controller',0x02133368);a.emit(0xE1520003);a.b('native',1)
    a.emit(0xE5942048);a.lit(3,'config',config);a.emit(0xE1520003);a.b('native',1)
    for state,label in ((15,'attack'),(16,'attack'),(28,'hurt'),(29,'hurt'),(53,'death')):a.emit(0xE3510000|state);a.b(label,0)
    a.b('native')
    for label,sound in (('attack',603),('hurt',605),('death',604)):
        a.label(label);a.lit(4,'sound_'+label,sound);a.b('play')
    a.label('play');a.emit(0xE24DD010,0xE28D0004);a.b(0x0203D564,link=True)
    a.emit(0xE28D0004,0xE1A01004,0xE3A02014,0xE3A03000,0xE58D3000);a.b(audio.SITE,link=True)
    a.emit(0xE28D0004);a.b(0x0203D580,link=True);a.emit(0xE28DD010)
    a.label('native');a.emit(0xE128F005,0xE8BD503F);a.b(old)
    return a.finish()
