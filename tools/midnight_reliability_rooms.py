"""Eight-room active route, removed cabin/refuge branches and spatial overview."""
from dataclasses import replace
from unittest.mock import patch
import math,struct
from tools import midnight_rebuild_rooms as base,chapter_renewal_rooms as renewal
from tools import midnight_chapter as ch,room_script as script,room_doors,room_author,room_minimap,room_envelope,room_compiler as rc,wos_tool as w
from tools.room_objects import RoomObjects
from tools.room_entities import Entities

RETIRED=(77,82)
ACTIVE=tuple(i for i in base.ACTIVE if i not in RETIRED)
BY_ID=base.BY_ID;SIZES=base.SIZES;STEPS=base.STEPS
PORTS={i:(p[:2] if i in (78,81) else p) for i,p in base.PORTS.items()}
LINKS={a:b for a,b in base.LINKS.items() if a[0] in {BY_ID[i] for i in ACTIVE} and b[0] not in {BY_ID[i] for i in RETIRED}}
SPECS={n:replace(s,doors=tuple(d for j,d in enumerate(s.doors,1) if not (n in (BY_ID[78],BY_ID[81]) and j==3))) for n,s in base.SPECS.items()}


def doors(index):
    return SPECS[BY_ID[index]].doors


def plan(index,native):
    with patch.dict(base.PORTS,{i:PORTS[i] for i in (78,81)}):room=base.plan(index,native)
    if index==83:
        upper=[q for q in room.solids if q.y0==93 and q.y1==96]
        if not upper:raise ValueError('Expected native upper turbine landing')
        # One continuous exit balcony keeps a real mixed encounter on the
        # player's final tier rather than scattered above/below the climb.
        solids=[q for q in room.solids if q not in upper]
        solids.append(replace(upper[0],x0=70,x1=192));room=replace(room,solids=tuple(solids))
    return room


def upper_wave(raw):
    p=RoomObjects.parse(raw);section=p.records[1].sections[0];entities=Entities.parse(section);labels=p.names[1].labels;spawners=triggers=0
    for i,(entity,label) in enumerate(zip(entities.records,labels)):
        if len(entity)!=28:continue
        payload=bytearray(entity)
        if w.u32(entity,12)==4:
            struct.pack_into('<2i',payload,0,132*4096,104*4096);struct.pack_into('<2H',payload,16,96,12);spawners+=1
        elif label=='Trigger (Encounter Approach)':
            struct.pack_into('<2i',payload,0,132*4096,104*4096);struct.pack_into('<2H',payload,20,128,18);triggers+=1
        else:continue
        section=Entities.parse(section).replace_record(i,payload)
    if (spawners,triggers)!=(1,1):raise ValueError('Expected one upper encounter spawner/approach')
    return p.replace_section(1,0,section)


def remove_branch(raw):
    """Delete the selected entity/name and clear its event without renumbering EGs."""
    p=RoomObjects.parse(raw);rec=p.records[0];entities=Entities.parse(rec.sections[0])
    if len(entities.batches)!=1:raise ValueError('Expected one main room batch')
    items=list(entities.records);hits=[i for i,e in enumerate(items) if len(e)==28 and w.u32(e,12)==7 and e[27]==4]
    if len(hits)!=1:raise ValueError('Expected exactly one branch door trigger')
    index=hits[0];items.pop(index);old=entities.batches[0].header;size=(4+len(items)+3)//4*4
    head=bytearray(old[:size]);head.extend(bytes(size-len(head)));struct.pack_into('<HBB',head,0,size+sum(map(len,items)),size,len(items))
    head[4:4+len(items)]=bytes(map(len,items))
    for j in range(4+len(items),size):head[j]=0
    section=bytes(head)+b''.join(items);Entities.parse(section)
    record=rec.replace_section(0,section);names=p.names[0];slots=list(names.slots);slots.pop(index)
    header=bytearray(names.raw[:20]);ends=tuple(x-1 for x in names.category_ends);struct.pack_into('<I',header,0,20+len(slots)*32);struct.pack_into('<7H',header,6,*ends)
    records=[r.raw for r in p.records];records[0]=record;blocks=[n.raw for n in p.names];blocks[0]=bytes(header)+b''.join(slots)
    raw=room_doors._assemble(p,records,blocks)
    raw,_=script.drop_commands(raw,0,lambda g,c:g==3)
    script.counts(raw,0)
    if any(x.group==3 for x in room_doors.exits(raw)):raise ValueError('Removed branch still has an exit')
    return raw


# X is unfolded in actual left-to-right room order. Turbine Rise raises the
# floor; Crown Return descends to the original gate's upper return landing.
CENTRES={76:(13,68),78:(40,68),81:(70,68),83:(94,60),86:(120,46),87:(143,46),89:(162,46),88:(187,58)}
MAP_SIZES={76:(20,14),78:(31,18),81:(25,14),83:(18,28),86:(27,24),87:(14,20),89:(23,22),88:(24,20)}
ORDER=(76,78,81,83,86,87,89,88)


def overview(native):
    body={};rects={}
    for i in ORDER:
        cx,cy=CENTRES[i];width,height=MAP_SIZES[i];a,b=cx-width//2,cy-height//2
        rects[BY_ID[i]]=[(a,b,a+width,b+height)];ww,hh=SIZES[i];low=-16 if i==86 else 0;inside=set()
        for y in range(b,b+height):
            for x in range(a,a+width):
                u=(x-a+.5)/width;v=1-(y-b+.5)/height
                if i in base.POLYGONS:
                    point=(u*ww,low+v*(hh-low));poly=base.POLYGONS[i]
                    valid=all(room_envelope.cross(p,q,point)>=-.001 for p,q in zip(poly,(*poly[1:],poly[0])))
                elif i==76:valid=u<.38 or v<.58
                elif i==78:valid=.22<u<.79 or v<(.72 if u<.22 else .5)
                elif i==81:valid=u<.32 or v<.48
                elif i==88:valid=abs(v-(.86-.7*u))<.22
                else:valid=True
                if valid:inside.add((x,y))
        for x,y in inside:body[x,y]=(BY_ID[i],ch.EDGE if any((x+dx,y+dy) not in inside for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else ch.FILL)
        if i==87:
            for d in range(-2,3):body[cx+d,cy]=(BY_ID[i],ch.EDGE);body[cx,cy+d]=(BY_ID[i],ch.EDGE)
    def port(i,group):
        side,floor,_=PORTS[i][group-1];a,b,xx,yy=rects[BY_ID[i]][0];low=-16 if i==86 else 0
        return (a if side=='left' else xx-1,round(yy-1-(floor-low)/(SIZES[i][1]-low)*(yy-b-1)))
    def line(owner,points):
        for (x,y),(xx,yy) in zip(points,points[1:]):
            for tx in range(min(x,xx),max(x,xx)+1):
                if (tx,y) not in body:body[tx,y]=(BY_ID[owner],ch.EDGE)
            for ty in range(min(y,yy),max(y,yy)+1):
                if (xx,ty) not in body:body[xx,ty]=(BY_ID[owner],ch.EDGE)
    for i,j in zip(ORDER,ORDER[1:]):
        g=next(g for (n,g),(dest,sp) in LINKS.items() if n==BY_ID[i] and dest==BY_ID[j]);dest=LINKS[BY_ID[i],g][1]
        h=next(k for k,p in enumerate(PORTS[j],1) if p[2]==dest);a=port(i,g);b=port(j,h)
        line(i,(a,(b[0],a[1]),b))
    a=port(88,2);b=port(76,3);line(88,(a,(199,a[1]),(199,89),(1,89),(1,b[1]),b))
    # Return direction and label are part of the owned room's normal tint slot.
    line(88,((100,87),(98,89),(100,91)))
    from tools.crane_art import FONT
    x=82
    for letter in 'RETURN':
        glyph=FONT.get(letter)
        if glyph:
            for y,row in enumerate(glyph):
                for dx,value in enumerate(row):
                    if value not in ('0',' ','.'):body[x+dx,79+y]=(BY_ID[88],ch.EDGE)
            x+=len(glyph[0])+1
    # Compose connectors before allocation: they receive a valid room palette
    # rather than the old fallback palette that drew black links over the map.
    with patch.object(ch,'MAP_ROOMS',rects),patch.object(ch,'_map_pixels',lambda:body):
        raw,listing=ch.map_layout(native(ch.MAP_SOURCE))
    return raw,listing


def apply(names,blobs,rt,native,meta):
    changed=[];reports={};lookup=w.u32(rt.new,ch.LOOKUP_LITERAL-0x02000000)
    for index in (78,81,83):
        name=BY_ID[index];room=plan(index,native);prefix='zz_R21_'+name;i=names.index(prefix+'.bsp')
        built=room_envelope.compile_room(room,base.POLYGONS.get(index,()),len(blobs[i])%4)
        oi=names.index('zz_'+name+'_app.obj');raw=upper_wave(blobs[oi]) if index==83 else remove_branch(blobs[oi])
        tree=rc.rc.RoomCollision.parse(built.collision)
        anchors=room_author.plan_anchors(rc.surfaces(room),room.bounds,floor_top=room.bounds[3]-22,solid=lambda x,y:tree.solid_at(x,y) is not None)
        polygon=base.POLYGONS.get(index,())
        for nx,ny,d,a,b in room_envelope.planes(polygon) if polygon else ():
            count=max(1,round(math.dist(a,b)/20))
            for step in range(count+1):
                t=(step+.5)/(count+1);x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
                anchors.append((x,y+2,room_author.FLOOR) if ny<-1800 else (x-nx/4096*4.5,y-ny/4096*4.5,room_author.CEILING if ny>1800 else room_author.LEFT_WALL if nx<0 else room_author.RIGHT_WALL))
        anchors=[(x,y,k) for x,y,k in anchors if not any(tree.solid_at(xx,yy) is not None for xx,yy in ((x,y),(x-2.5,y+3),(x+2.5,y+3)))]
        raw=room_author.set_anchors(raw,anchors)
        # Retain all native camera/spawn/anchor data; physical geometry changes
        # only the retired portal/landing. Main doors retain their group IDs.
        assets={prefix+'.nsbmd':built.model,prefix+'.nsbtx':built.textures,prefix+'.bsp':built.collision,
            prefix+'.cbmp':room_envelope.detailed_map(native(ch.MAP_SOURCE),room,built.collision,doors(index),SPECS[name].save),'zz_'+name+'_app.obj':raw}
        for asset,payload in assets.items():
            i=names.index(asset);blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4);changed.append(asset)
        reports[name]=dict(index=index,removed_exit_group=3 if index in (78,81) else None,upper_balcony_encounter=index==83,remaining_ports=[vars(d) for d in doors(index)],quads=built.quads)
    # Keep retired IDs loadable only for old checkpoints, with a safe one-way
    # return to a remaining floor door. No active route or map reaches them.
    for index,destination,spawn in ((77,78,1),(82,81,2)):
        i=names.index('zz_'+BY_ID[index]+'_app.obj');old=blobs[i]
        exits=room_doors.exits(old);changes={(e.record,e.group):(destination,1,spawn) for e in exits}
        raw=room_doors.retarget(old,changes);blobs[i]=raw+bytes((len(old)-len(raw))%4);changed.append(names[i])
    raw,listing=overview(native);i=names.index(ch.MAP_SCREEN);blobs[i]=raw+bytes((len(blobs[i])-len(raw))%4);changed.append(ch.MAP_SCREEN)
    area=meta['chapter_spectacle'].get('map_areas')
    # Find the current native area table through its immutable room-map id.
    from tools import crane_row,creature_forge,tasm_kit
    candidates=set()
    for at in range(0,tasm_kit.SOURCE,4):
        value=w.u32(rt.arm,at)
        if crane_row.CR_BASE<=value<creature_forge.START and w.u32(rt.arm,creature_forge.offset(value))==names.index('MMPier.cbmp') and w.u32(rt.arm,creature_forge.offset(value)+6*16)==names.index(crane_row.MAP_SCREEN):candidates.add(value)
    if len(candidates)!=1:raise ValueError('Owned area table is ambiguous')
    area=candidates.pop();table=rt.alloc(ch.map_entries(listing));struct.pack_into('<2I',rt.new,creature_forge.offset(area)+5*16+8,table,len(listing))
    return dict(active=ACTIVE,retired=RETIRED,order=ORDER,rooms=reports,map_table=table,map_entries=len(listing),modified_resources=changed)
