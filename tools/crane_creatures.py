"""Original Crane creature assets and scoped native-framework integration.

Original model-sheet groups, actor files and animation bindings stay intact.
New geometry/motion are private appended resources, selected only in Crane Row.
"""
from dataclasses import dataclass
import struct
from tools import wos_tool as w,crane_creature_art as art,crane_creature_motion as motion
from tools.animation_rig import AnimationRig
from tools.custom_formats import Xbd,Gab
from tools.sca import Sca
from tools.gmb import Gmb
from tools.grip_compression import CompressedBlob
from tools.rush_choreography import mv,transpose,sub,add

@dataclass(frozen=True)
class Creature:
    key:str
    name:str
    kind:int
    stem:str
    hp:int
    cost:int

CREATURES=(Creature('maw','Mooring Maw',21,'hLpr',10,1),
           Creature('ballast','Ballast Beast',36,'brt',14,2),
           Creature('spore','Lantern Spore',20,'hRng',7,1))
BY_KEY={c.key:c for c in CREATURES}

def mode_of(name,key):
    if name.endswith('_Idle.sca') or name.endswith('_NoticeSpidey.sca'):return 'idle'
    if name.endswith('_Walk.sca'):return 'walk'
    if name.endswith('_Run.sca'):return 'run'
    if key=='maw' and name.endswith('_LeapAttackPrep.sca'):return 'prep'
    if key=='maw' and name.endswith('_LeapAttack.sca'):return 'leap'
    if key=='maw' and name.endswith(('_Land.sca','_Fall.sca','_Jump.sca')):return 'land' if name.endswith('_Land.sca') else 'air'
    if key=='ballast' and ('GroundAttack2' in name or 'DropDownAttack' in name):return 'slam'
    if key=='ballast' and name.endswith('_RunAttack.sca'):return 'charge'
    if key=='spore' and 'GroundRangedAttack' in name:return 'spit'
    if key=='maw' and 'GroundAttack2' in name:return 'backhand'
    if 'Attack' in name:return 'attack'
    if '_Die.' in name or '_Explode.' in name:return 'die'
    if any(s in name for s in ('Hurt','BlockImpact','GettingPossessed')):return 'hurt'
    if 'Grapple' in name:return 'bound'
    if any(s in name for s in ('Jump','Fall','Fly','SproutWings')):return 'air'
    if 'Land' in name:return 'land'
    if any(s in name for s in ('Throw','Kick')):return 'attack'
    if any(s in name for s in ('Prep','Burrow','Duck')):return 'prep'
    if 'Crawl' in name:return 'walk'
    return 'idle'

def contact_window(gab,frames):
    events=Gab.parse(gab).records if gab else ()
    start=next((f for f,event,value in events if event==1 and value==1),max(2,round(frames*.4)))
    stop=next((f for f,event,value in events if event==1 and value==5 and f>start),min(frames-1,start+4))
    return start,stop


def attack_events(spec,source,raw):
    """Give the fast shell slam a visible windup within its native17 samples."""
    if raw is None or spec.key!='ballast' or source!='brt_GroundAttack2.sca':return raw
    parsed=Gab.parse(raw)
    if parsed.records!=((2,1,1),(6,1,5)):raise ValueError('Native fast-slam event contract changed')
    result=bytearray(raw);struct.pack_into('<H',result,0,6);struct.pack_into('<H',result,6,11)
    if Gab.parse(result).records!=((6,1,1),(11,1,5)):raise ValueError('Invalid authored slam timing')
    return bytes(result)

def geometry_motion(raw,kind,positions,reference,mode,source):
    """Author observed axis-aligned body/attack shapes, preserving other words.

    Native channel kinds/flags/part IDs and gameplay movement stay exact. These
    authored coordinates require live hit/launch controls in addition to parsing.
    """
    wrapper=CompressedBlob.parse(raw);a=Gmb.parse(wrapper.decoded);out=bytearray(a.raw)
    if len(positions)!=a.record_count:raise ValueError('Creature SCA/GMB sample counts disagree')
    for c in a.channels:
        for f,record in enumerate(c.records):
            words=c.words(f);at=c.offset+4+f*c.stride
            if c.kind==3 and words[7] in (0,4096):
                if kind=='maw':
                    y,z,height,radius=(3.4,0,6.8,3.0) if words[7]==0 else (3.4,1.0,6.8,3.2)
                    struct.pack_into('<4i',out,at+4,*(round(v*4096) for v in (y,z,height,radius)))
                elif kind=='spore' and words[7]==4096:
                    struct.pack_into('<4i',out,at+4,*(round(v*4096) for v in (6.0,.4,6.4,2.5)))
            elif c.kind==3 and words[7]==8192 and mode in ('attack','leap','slam','charge','spit','backhand'):
                if kind=='maw':shape=(3.4,2.2,5.8,4.6)
                elif kind=='ballast':shape=(3.5,0.,7.,5.5) if 'GroundAttack1' in source or 'GetUpAttack' in source else (2.5,1.5,5.,4.)
                else:shape=(5.,2.,5.,3.)
                struct.pack_into('<4i',out,at+4,*(round(v*4096) for v in shape))
            elif c.kind==0 and words[6]==36864:
                # The original effect/projectile reference point follows the
                # newly posed mouth/claw instead of the old actor silhouette.
                x,y,z=reference[f]
                struct.pack_into('<3i',out,at,0,round(y*4096),round(z*4096))
    Gmb.parse(out)
    return wrapper.replace_decoded(bytes(out))

def prepare(blob,names,*,specs=None,prefix_base='zz_CR_',model_author=None):
    """Return appendable authored assets, deferred XBD links and diagnostics."""
    extras={};links={};report={}
    for spec in (CREATURES if specs is None else specs):
        template=blob(spec.stem+'.nsbmd');texture=blob(spec.stem+'.nsbtx');idle_raw=blob(spec.stem+'_Idle.sca')
        idle=Sca.parse(idle_raw);rig=AnimationRig.parse(template);neutral=motion.neutral(idle,rig.parents,spec.key)
        if model_author is not None:model,tex,meta=model_author(spec,template,texture,neutral)
        elif spec.key=='ballast':model,tex,meta=art.ballast(template,idle_raw,neutral)
        elif spec.key=='maw':model,tex,meta=art.maw(template,texture,neutral)
        else:model,tex,meta=art.spore(template,texture,neutral)
        prefix=prefix_base+spec.key
        model_name=prefix+'.nsbmd';tex_name=prefix+'.nsbtx';xbd_name=prefix+'.xbd'
        extras[model_name]=model;extras[tex_name]=tex
        source_xbd=blob(spec.stem+'.xbd');xbd=Xbd.parse(source_xbd,names)
        extras[xbd_name]=source_xbd;mapping={};clips=[]
        r0,p0=neutral.fk()
        if spec.key=='spore':joint=5;point=add(p0[1],(0,1.3,2.3))
        elif spec.key=='maw':joint=4;point=add(p0[4],(0,-.4,2.5))
        else:joint=15;point=add(p0[15],(0,-.4,1.4))
        local=mv(transpose(r0[joint]),sub(point,p0[joint]))
        for i,binding in enumerate(xbd.bindings):
            if binding['tag']!=0:continue
            source=binding['name'];mode=mode_of(source,spec.key)
            if mode is None:continue
            end=next((j for j in range(i+1,len(xbd.bindings)) if xbd.bindings[j]['tag']==0),len(xbd.bindings))
            parts=xbd.bindings[i+1:end];original_gab=next((blob(b['name']) for b in parts if b['tag']==4),None)
            gab=attack_events(spec,source,original_gab)
            raw=blob(source);a=Sca.parse(raw);impact,recovery=contact_window(gab,a.frame_count)
            name=prefix+'_'+source
            refs=[]
            edited,positions=motion.author(raw,idle_raw,rig.parents,spec.key,mode,impact,recovery,reference=(joint,local,refs))
            if name in extras and extras[name]!=edited:raise ValueError('Aliased creature animation has conflicting timing')
            extras[name]=edited;mapping[binding['offset']]=name
            if gab!=original_gab:
                event_name=prefix+'_'+source[:-4]+'.gab';extras[event_name]=gab
                event_binding=next(b for b in parts if b['tag']==4);mapping[event_binding['offset']]=event_name
            for part in parts:
                if part['tag']!=3:continue
                target=prefix+'_'+source[:-4]+'.gmb'
                data=geometry_motion(blob(part['name']),spec.key,positions,refs,mode,source)
                if target in extras and extras[target]!=data:raise ValueError('Conflicting authored GMB')
                extras[target]=data;mapping[part['offset']]=target
            clips.append({'source':source,'authored':name,'mode':mode,'frames':a.frame_count,'contact_start':impact,'contact_end':recovery})
        links[xbd_name]=mapping
        report[spec.key]={'name':spec.name,'native_chassis_kind':spec.kind,'model':model_name,'texture':tex_name,'xbd':xbd_name,
                          'hp_before_room_dial':spec.hp,'cost':spec.cost,'clips':clips,**meta}
    return extras,links,report

def bind_xbds(names,blobs,links):
    out=list(blobs)
    for name,bindings in links.items():
        index=names.index(name);raw=out[index]
        for offset,target in bindings.items():raw=Xbd.parse(raw,names).replace_binding(offset,names.index(target),names)
        out[index]=raw
    return out

CONFIG_SITE=0x020D12A0
GOAL_CALL=0x0204C15C
GOAL_NATIVE=0x020D11B0
VARIANT_CALL=0x0204C5A4
VARIANT_NATIVE=0x020D102C
CONFIG_TABLE=0x02136880
GOAL_TABLE=0x02136634
REWARD_SITE=0x020D1590
REWARD_TABLE=0x0211E808
REWARD_SET=31

def _scope(a,fallback,test_room=None):
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b(fallback,0)
    a.emit(0xE5923000)
    if test_room is not None:a.emit(0xE3530000|test_room);a.b('in_scope',0)
    a.emit(0xE3530060);a.b(fallback,3);a.emit(0xE353006C);a.b(fallback,2)
    a.label('in_scope')

def config_adapter(at,configs,*,test_room=None):
    from tools.crane_boss import Arm
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000);_scope(a,'native',test_room)
    for spec in CREATURES:
        a.emit(0xE3510000|spec.kind);a.b(spec.key,0)
    a.b('native')
    for spec in CREATURES:
        a.label(spec.key);a.lit(2,'config_'+spec.key,configs[spec.key]);a.b('store')
    a.label('store');a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('native');a.emit(0xE128F00C,0xE8BD500F,0xE92D000F);a.b(CONFIG_SITE+4)
    return a.finish()

def variant_adapter(at,state,*,test_room=None):
    from tools.crane_boss import Arm
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000);_scope(a,'native',test_room)
    a.lit(2,'state',state);a.emit(0xE5921000,0xE1510003);a.b('same_room',0)
    a.emit(0xE5823000,0xE3A01000,0xE5821004)
    a.label('same_room');a.emit(0xE353006A);a.b('maw',0)
    a.emit(0xE5921004,0xE3510003,0x23A01000,0xE2813001,0xE5823004)
    a.emit(0xE3510000);a.b('maw',0);a.emit(0xE3510001);a.b('spore',0);a.b('ballast')
    for spec in CREATURES:
        a.label(spec.key);a.emit(0xE3A02000|spec.kind);a.b('store')
    a.label('store');a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('native');a.emit(0xE128F00C,0xE8BD500F);a.b(VARIANT_NATIVE)
    return a.finish()

def goal_adapter(at,goals,*,test_room=None):
    from tools.crane_boss import Arm
    a=Arm(at)
    # Run native lazy initialization first. Preserve its returned registers and
    # flags even when a private goal pointer replaces the out-parameter.
    a.emit(0xE92D4070,0xE1A04000,0xE1A05001);a.b(GOAL_NATIVE,link=True)
    a.emit(0xE92D100F,0xE10F6000);_scope(a,'restore',test_room)
    a.emit(0xE353006A);a.b('opening',0)
    a.emit(0xE355000E);a.b('ordinary',1)
    for room in (96,102,103):a.emit(0xE3530000|room);a.b('upper',0)
    a.label('ordinary')
    for room in (97,100,105):a.emit(0xE3530000|room);a.b('clear_'+str(room),0)
    a.b('patrol')
    for room,mask in ((97,1),(100,2),(105,4)):
        a.label('clear_'+str(room));a.emit(0xE5D2202E,0xE3120000|mask);a.b('patrol',1);a.b('crew')
    for name in ('opening','patrol','crew','upper'):
        a.label(name);a.lit(2,'goal_'+name,goals[name]);a.b('store')
    a.label('store');a.emit(0xE5842000)
    a.label('restore');a.emit(0xE128F006,0xE8BD100F,0xE8BD4070,0xE12FFF1E)
    return a.finish()

def character_config(arm,spec,group):
    start=CONFIG_TABLE-0x02000000+(spec.kind-2)*84
    raw=bytearray(arm[start:start+84])
    if len(raw)!=84:raise ValueError('Character config outside ARM9')
    struct.pack_into('<I',raw,8,group)
    struct.pack_into('<I',raw,12,spec.hp*4096)
    # ERewardSetType, passed to RewardSetSpewer by native lethal HP setter
    # 0x020493F4. Private31 supplies native physical HP/XP orbs, not stat writes.
    struct.pack_into('<I',raw,0x50,REWARD_SET)
    # Preserve native costs (1/2/1). Other uses of that field have not been
    # audited, so it must not be treated as cost only.
    if w.u32(raw,0)!=spec.cost*4096:raise ValueError('Unexpected native character cost')
    return bytes(raw)

def goal_configs(arm):
    start=GOAL_TABLE-0x02000000+8*24
    native=arm[start:start+24]
    p=w.u32(native,16)-0x02000000;weight=0
    for _ in range(21):
        if w.u32(arm,p)==20:break
        weight=(weight+arm[p+4])&255;p+=8
    else:raise ValueError('Native goal list lacks its observed terminator')
    result={}
    for name,total,live in (('patrol',8,4),('crew',12,4),('opening',1,1),('upper',4,2)):
        raw=bytearray(native);struct.pack_into('<2I',raw,0,total*4096,live*4096)
        raw[20]=weight
        result[name]=bytes(raw)
    return result

def reward_config(arm):
    raw=bytearray(arm[REWARD_TABLE-0x02000000+9*48:REWARD_TABLE-0x02000000+10*48])
    if len(raw)!=48:raise ValueError('Native reward set bounds')
    # Native set9 XP remains10..12 points; HP's negative lower roll is replaced
    # with0.25..0.5 health units.0.25 is the native smallest HP orb threshold.
    struct.pack_into('<2i',raw,0,1024,2048)
    return bytes(raw)

def reward_adapter(at,record):
    from tools.crane_boss import Arm
    a=Arm(at);a.emit(0xE92D500F,0xE10FC000,0xE3510000|REWARD_SET);a.b('native',1)
    _scope(a,'native');a.lit(2,'reward',record);a.emit(0xE5802000,0xE128F00C,0xE8BD900F)
    a.label('native');a.emit(0xE128F00C,0xE8BD500F,0xE92D000F);a.b(REWARD_SITE+4)
    return a.finish()


def install_runtime(arm,groups,alloc,data):
    """Allocate owned records/adapters and return verified native-site hooks."""
    from tools.crane_row import branch
    configs={s.key:alloc(character_config(arm,s,groups[s.key])) for s in CREATURES}
    goals={key:alloc(raw) for key,raw in goal_configs(arm).items()}
    reward=alloc(reward_config(arm))
    state=alloc(bytes(8))
    hooks=[];adapters={}
    for key,site,native,make in (
        ('config',CONFIG_SITE,None,lambda at:config_adapter(at,configs)),
        ('variant',VARIANT_CALL,VARIANT_NATIVE,lambda at:variant_adapter(at,state)),
        ('goal',GOAL_CALL,GOAL_NATIVE,lambda at:goal_adapter(at,goals)),
        ('reward',REWARD_SITE,None,lambda at:reward_adapter(at,reward))):
        expected=0xE92D000F if native is None else branch(site,native,link=True)
        if w.u32(arm,site-0x02000000)!=expected:raise ValueError('Native creature '+key+' hook changed')
        at=alloc();data.extend(make(at));adapters[key]=at
        hooks.append((site,branch(site,at,link=native is not None)))
    return hooks,{'groups':groups,'configs':configs,'goals':goals,'reward':reward,'state':state,'adapters':adapters,
                  'scope':list(range(96,108)),'native_ai_framework':True}
