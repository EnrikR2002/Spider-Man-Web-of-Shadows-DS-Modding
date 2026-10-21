"""Compile the approved chapter spaces and stage per-room purpose and machinery."""
from dataclasses import replace
import struct
from tools import chapter_renewal_rooms as renewal,crane_rooms as crane,midnight_rooms as mr,midnight_chapter as ch
from tools import chapter_spectacle_art as art,chapter_spectacle_events as events,chapter_spectacle_combat as combat,chapter_spectacle_audio as audio
from tools import room_compiler as rc,room_author,room_minimap,oscorp_resources,crane_boss,midnight_boss,crane_creatures as cc,crane_row
from tools import room_script as s,wos_tool as w
from tools.room_objects import RoomObjects
from tools.room_entities import Entities
from tools.room_events import EventGroup
from tools.qol_suits_menu import StringSlots,decode_grown

ROSTERS={76:(21,21),78:(21,36,21,20),81:(36,20,36),83:(21,20,21),86:(20,36,21,20),88:(21,),89:(36,),
         96:(21,21,20),97:(36,21,20,21),99:(21,20,21),100:(36,21,36),101:(20,36),102:(21,20),103:(20,21,21),105:(36,20,21),106:(21,),107:(21,)}
BUDGETS={76:(3,2),78:(7,3),81:(6,3),83:(4,2),86:(8,3),88:(2,1),89:(2,2),
         96:(5,3),97:(8,3),99:(6,3),100:(8,3),101:(5,2),102:(4,2),103:(5,3),105:(4,4),106:(1,1),107:(2,1)}
PROGRESS={97:144,100:145,105:146}
# (saved/scalar flag, world positions). Native harmless marker objects carry
# only light panels; architecture and every player landing are compiled solids.
LIGHTS={76:(147,((50,68),(114,68),(178,68))),78:(events.PUMP,((68,58),(164,58),(260,58))),
        81:(events.PUMP,((66,48),(144,48),(222,48))),83:(events.PUMP,((30,26),(162,74),(30,122))),
        86:(147,((106,48),(144,68),(182,48))),89:(147,((88,50),(112,64),(136,50))),
        96:(140,((70,80),(158,70),(272,68))),98:(140,((20,48),(82,48))),101:(140,((130,18),(142,22),(154,18))),
        102:(140,((50,56),(120,120),(50,184))),103:(140,((70,50),(210,70),(350,50))),
        105:(140,((54,72),(168,102),(282,72))),107:(142,((60,28),(160,34),(260,28)))}

def geometry(index,native):
    name=renewal.BY_ID[index] if index<96 else crane.NAMES[index-96]
    plan=renewal.geometry(index,native) if index<96 else renewal.crane_geometry(name,native)
    if index==78:
        # Carriage roofs are solid slabs above an open foreground platform.
        # Their old full-height12-unit boxes trapped pursuing enemies beneath
        # the perch and disagreed with the visible25-unit roof.
        solids=[]
        for q in plan.solids:
            if q.y0==0 and q.y1==12 and q.x0 in (84,156,228):
                q=replace(q,y0=22,y1=25,top=rc.Look('MLRail',(32,32)),front=rc.Look('MLSteel',(32,32)))
            solids.append(q)
        plan=replace(plan,solids=tuple(solids))
    return art.architecture(plan,index)

def install_runtime(arm,clean_arm,names,alloc,data,fx):
    base=0x02000000
    def hook(site,make,link=False):
        old=crane_row.target(site,w.u32(arm,site-base));at=alloc();data.extend(make(at,old))
        struct.pack_into('<I',arm,site-base,crane_row.branch(site,at,link=link));return at
    patterns={i:alloc(bytes(seq)) for i,seq in ROSTERS.items()}
    table=alloc(b''.join(struct.pack('<3I',i,patterns[i],len(seq)) for i,seq in ROSTERS.items())+bytes(12));state=alloc(struct.pack('<2I',0xffffffff,0))
    variant=hook(cc.VARIANT_CALL,lambda at,old:combat.variant(at,table,state,old),link=True)
    native_goals=cc.goal_configs(clean_arm)['patrol'];goal_cache={}
    def goal(total,live):
        key=(total,live)
        if key not in goal_cache:
            raw=bytearray(native_goals);struct.pack_into('<2I',raw,0,total*4096,live*4096);goal_cache[key]=alloc(raw)
        return goal_cache[key]
    goals=alloc(b''.join(struct.pack('<5I',i,goal(*budget),goal(3,2),goal(3,2),PROGRESS.get(i,0)) for i,budget in BUDGETS.items())+bytes(20))
    goal_hook=hook(cc.GOAL_CALL,lambda at,old:combat.goals(at,goals,old),link=True)
    # Exact native harmless world-object record; only the model fields differ.
    harmless=bytearray(clean_arm[midnight_boss.DATA_BASE-base+midnight_boss.WARNING_KIND*64:midnight_boss.DATA_BASE-base+(midnight_boss.WARNING_KIND+1)*64])
    struct.pack_into('<I',harmless,0,0);world_rows=[];models={}
    for room,kind,flag,off,on in fx:
        ptrs=[]
        for name in (off,on):
            if name not in models:
                raw=bytearray(harmless);struct.pack_into('<2I',raw,4,0xB6,names.index(name));models[name]=alloc(raw)
            ptrs.append(models[name])
        world_rows.append(struct.pack('<5I',room,kind,flag,*ptrs))
    world_table=alloc(b''.join(world_rows)+bytes(20))
    world_hook=hook(0x020D1610,lambda at,old:combat.world_data(at,world_table,old))
    hp=hook(crane_boss.HP_SITE,combat.core_phase)
    return dict(variant=variant,roster_table=table,roster_state=state,patterns=patterns,goals=goal_hook,goal_table=goals,
                world_data=world_hook,world_table=world_table,core_hp=hp)

def apply(names,blobs,arm,native,alloc,data,runtime,*,pilot=False):
    names=list(names);blobs=list(blobs);originals=tuple(blobs);modified=set();plans={};built={};objects={};reports={};fx=[];extras={}
    lookup=w.u32(arm,ch.LOOKUP_LITERAL-0x02000000)
    offset=lambda a:__import__('tools.chapter_spectacle',fromlist=['offset']).offset(a)
    active=[78,101,106] if pilot else [*renewal.ACTIVE,*range(96,108)]
    for index in active:
        name=renewal.BY_ID[index] if index<96 else crane.NAMES[index-96]
        print('STAGE '+name,flush=True);plan=geometry(index,native);plans[index]=plan;built[index]=rc.compile_room(plan)
        raw=blobs[names.index('zz_'+name+'_app.obj')]
        if index==78:
            tree=rc.rc.RoomCollision.parse(built[index].collision)
            points=room_author.plan_anchors(rc.surfaces(plan),plan.bounds,floor_top=90,solid=lambda x,y:tree.solid_at(x,y) is not None)
            raw=room_author.set_anchors(raw,points)
        raw=events.triggered_patrol(raw,index,plan.bounds[2],plan.bounds[3])
        marker=None
        if index in LIGHTS:
            flag,positions=LIGHTS[index];cx=plan.bounds[2]/2
            pair=[]
            for on in (False,True):
                n=f'zz_CS23_L{index}_{int(on)}.nsbmd';extras[n]=art.lights(index,tuple((x-cx,y) for x,y in positions),on=on);pair.append(n)
            fx.append((index,0x13,flag,*pair))
            entity=mr._placed(mr._native_entity(native('proto01_app.obj'),'Object (Hazard_Electric)'),(cx,0));entity[22]=0x13;entity[23]=0
            raw,marker=s.append_batch(raw,1,[(bytes(entity),'Object (Machinery Lamps)')],'Machinery Lamps')
            raw=s.extend_group(raw,1,0,[s.activate(ag=marker)])
        if index==81:raw=events.pump(raw,native,marker,audio.IDS)
        if index==89:raw=events.conductor(raw,marker,audio.IDS)
        if index==101:raw=events.rewrite(raw,1,'Cargo_Power',lambda commands:(*commands,*events.refresh(raw,marker),events.sound(audio.IDS['pump-start'])))
        if index==106:
            raw=events.hoist(raw,audio.IDS);raw=events.checkpoint(raw,native)
            for key in ('motor','shield','hook'):extras['zz_CS23_'+key+'.nsbmd']=art.machinery(key)
            extras['zz_CS23_motor_dead.nsbmd']=art.machinery('motor',broken=True,dead=True)
            extras['zz_CS23_shield_broken.nsbmd']=art.machinery('shield',broken=True)
            fx.append((106,crane_boss.MOTOR,142,'zz_CS23_motor.nsbmd','zz_CS23_motor_dead.nsbmd'))
            fx.append((106,crane_boss.SHIELD,events.HOIST_PHASE,'zz_CS23_shield.nsbmd','zz_CS23_shield_broken.nsbmd'))
            wreck=mr._placed(mr._native_entity(native('proto01_app.obj'),'Object (Hazard_Electric)'),(352,1));wreck[22]=crane_boss.MOTOR;wreck[23]=0
            raw,wreck_ag=s.append_batch(raw,1,[(bytes(wreck),'Object (Disabled Hoist Motor)')],'Disabled Hoist Motor')
            raw=events.rewrite(raw,1,'Win',lambda commands:(*commands,s.activate(ag=wreck_ag)))
            raw=s.extend_group(raw,1,0,[s.if_var(142,'==',1,then=s.action(ag=wreck_ag))])
        if index==104:
            prop=mr._native_entity(native('proto01_app.obj'),'Object (Smashable_MetalBarrel)')
            raw,stash=s.append_batch(raw,1,[(bytes(mr._placed(prop,xy)),'Object (Reserve Supply '+str(j)+')') for j,xy in enumerate(((40,20),(100,42),(144,42)))],'Reserve Supplies')
            raw=s.extend_group(raw,1,0,[s.if_var(143,'==',0,then=s.action(ag=stash))])
        raw=events.ambience(raw,index,audio.IDS);objects[index]=raw
        prefix='zz_R21_'+name
        for ext,payload in (('.nsbmd',built[index].model),('.nsbtx',built[index].textures)):
            i=names.index(prefix+ext);blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);modified.add(i)
        if index==78:
            i=names.index(prefix+'.bsp');payload=built[index].collision;blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);modified.add(i)
        if index in (78,106):
            spec=renewal.SPECS[name] if index<96 else crane.SPECS[name]
            payload,_=room_minimap.build(native(ch.MAP_SOURCE),plan,spec.doors,save=(36,1) if index==106 else (),glyphs=__import__('tools.crane_art',fromlist=['FONT']).FONT)
            i=names.index(prefix+'.cbmp');blobs[i]=payload;modified.add(i)
        i=names.index('zz_'+name+'_app.obj');blobs[i]=raw;modified.add(i)
        if len(raw)%4!=len(originals[i])%4:raise ValueError('OBJ changed global model alignment: '+name)
        reports[name]=dict(index=index,bounds=plan.bounds,quads=built[index].quads,roof_platforms=index==78,save=(36,1) if index==106 else (),
                           roster=ROSTERS.get(index,()),budget=BUDGETS.get(index),objects_sha256=w.sha256(raw))
    # Improved grabber silhouette retains its existing model id/native mover.
    i=names.index('zz_CR_hook.nsbmd');newhook=extras.pop('zz_CS23_hook.nsbmd');blobs[i]=newhook+bytes((len(blobs[i])-len(newhook))%4);modified.add(i)
    # Descriptors retain every id, resource binding, camera and doorway.
    for index,plan in plans.items():
        desc=w.u32(arm,offset(lookup)+index*4);struct.pack_into('<9i',arm,offset(desc)+0x28,*room_minimap.projection(plan,5 if index<96 else 6).fields)
    if not pilot:
        from tools import crane_navigation as nav
        for stage,n in enumerate(nav.SCREENS):
            _,old_listing=nav.overview(native(ch.MAP_SOURCE),stage)
            payload,listing=nav.overview(native(ch.MAP_SOURCE),stage,extra_saves=(crane.NAMES[10],))
            if listing!=old_listing:raise ValueError('Checkpoint marker changed owned map allocation')
            i=names.index(n);blobs[i]=payload;modified.add(i)
    # Existing owned messages carry the new purpose/checkpoint help; no shop or
    # dialogue capacity expansion, and no intrusive new instruction boards.
    replacements={
        'Terminal > Floodworks > Turbine.\nObservatory > Sanctuary > Conductor.\nX opens the lit shutters.\nSave: Signal House / Pump Refuge.\nCrown Return loops to Storm Gate.':
        'Cross Terminal by roof or platform.\nX at Floodworks lever: steady the pumps.\nTurbine > Observatory > Sanctuary.\nSave before facing the Conductor.\nX opens the lit shutters.',
        crane.LINES['objective_hoist']:'Save in the Long Arm approach. Dodge the grabber, then combo the exposed winch. A damaged motor stays open longer. Green pads are refuges.'}
    for n in ch.STRING_FILES:
        i=names.index(n);edits={}
        for slot in range(crane_row.slot_count(blobs[i])):
            text=decode_grown(blobs[i],slot)
            if text in replacements:edits[slot]=replacements[text]
        payload=StringSlots(native(n)).grown(blobs[i],edits);blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);modified.add(i)
    aligned={};size=sum(map(len,blobs))
    for n,payload in extras.items():
        if size%4:pad=bytes(-size%4);aligned[f'zz_CS23_pad{len(aligned)}.bin']=pad;size+=len(pad)
        aligned[n]=payload;size+=len(payload)
    outnames,outblobs=oscorp_resources.append_resources(names,blobs,aligned);modified.add(names.index('GlobFiles.txt'))
    from tools import creature_forge_art as enemy_art,creature_forge_motion as motion,creature_texture_fix as texture_fix,chapter_renewal
    from tools.sca import Sca
    from tools.animation_rig import AnimationRig
    creature_models={}
    for style,stem,_,_ in chapter_renewal.PRIVATE_STYLES:
        if pilot and style!='warden':continue
        rig=AnimationRig.parse(native(stem+'.nsbmd'));pose=motion.pose(Sca.parse(native(stem+'_Idle.sca')),rig.parents,style,stem)
        model,meta=enemy_art.model(style,stem,native(stem+'.nsbmd'),pose,sculpt_type=art.ReadableSculpt)
        model,_=texture_fix.fix_model(model);i=outnames.index('zz_F22_'+style+'.nsbmd');outblobs[i]=model+bytes((len(outblobs[i])-len(model))%4);modified.add(i)
        creature_models[style]=meta
    clean,_,_=__import__('mod').load_clean();h=w.parse_header(clean);ca=clean[h['arm9_offset']:h['arm9_offset']+h['arm9_size']]
    hooks=install_runtime(arm,ca,outnames,alloc,data,fx)
    struct.pack_into('<I',arm,ch.GLOB_COUNT,len(outnames))
    return outnames,outblobs,arm,dict(rooms=reports,world_models={n:dict(size=len(p),sha256=w.sha256(p)) for n,p in aligned.items()},
        scripted_runtime=hooks,modified_indices=list(modified),material_atlas=str(art.ATLAS.name),pump_flag=events.PUMP,
        checkpoint=dict(room=106,xy=(36,1),disabled_during_combat=True),map_areas=dict(midnight=5,crane=6),sound=dict(first=audio.FIRST,count=len(audio.NAMES)),readable_creature_models=creature_models)
