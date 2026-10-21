"""Distinct playable Midnight envelopes, dimensions and a real stair descent."""
from dataclasses import replace
from unittest.mock import patch
import struct
from tools import chapter_renewal_rooms as old,chapter_spectacle_rooms as painted
from tools import room_compiler as rc,room_envelope as envelope,room_author,room_minimap
from tools import room_doors,midnight_chapter as ch,midnight_rooms as mr,wos_tool as w
from tools.room_objects import RoomObjects
from tools.room_entities import Entities

SIZES={**old.SIZES,77:(80,56),82:(112,48),87:(128,80),88:(256,112)}
PORTS={**old.PORTS,88:(('left',64,2),('right',0,1))}
POLYGONS={
 77:((0,0),(80,0),(80,28),(52,56),(20,56),(0,36)),
 82:((0,0),(112,0),(112,48),(44,48),(0,28)),
 83:((0,0),(128,0),(192,36),(192,144),(112,144),(0,96)),
 86:((0,0),(72,-16),(216,-16),(288,0),(288,32),(244,96),(192,128),(96,128),(44,96),(0,32)),
 87:((0,0),(128,0),(128,32),(80,80),(40,80),(0,32)),
 89:((0,0),(224,0),(224,40),(176,96),(148,112),(76,112),(48,96),(0,40)),
}
SHAPES={76:'L-shaped street and return tower',77:'compact clipped signal cabin',78:'T-shaped vaulted train concourse',
 81:'bent low service channel and tall pump access',82:'low asymmetric maintenance shelter',83:'tapered diagonal turbine shaft',
 86:'sunken observatory bowl with sloping approaches',87:'tall vaulted checkpoint chapel',88:'descending staircase with stepped ceiling',89:'crowned storm amphitheatre'}
STEPS={**old.STEPS,88:((216,16),(168,32),(120,48),(72,64))}
ACTIVE=old.ACTIVE;BY_ID=old.BY_ID;LINKS=old.LINKS


def doors(index):
    width,height=SIZES[index]
    return tuple(mr.Door(side,0 if side=='left' else width,floor,spawn,'Port'+str(i),inset=16)
        for i,(side,floor,spawn) in enumerate(PORTS[index],1))


SPECS=dict(old.SPECS)
for _index in ACTIVE:
    _width,_height=SIZES[_index]
    SPECS[BY_ID[_index]]=replace(SPECS[BY_ID[_index]],doors=doors(_index),
        camera=(((16,0),(_width-16,0),(_width-16,_height),(16,_height)),))


def plan(index,native):
    with patch.dict(old.SIZES,SIZES),patch.dict(old.PORTS,PORTS),patch.object(painted.art,'architecture',lambda room,index:room):
        result=painted.geometry(index,native)
    solids=list(result.solids);metal=rc.Look('MLSteel',(32,32));stone=rc.Look('MLStone',(32,32))
    def solid(x,y,xx,yy,look=stone):solids.append(rc.Solid(x,y,xx,yy,top=look,front=look,side=metal,under=metal))
    if index==76:
        solid(84,52,224,88);solid(64,72,84,88)
    elif index==78:
        solid(0,80,72,112);solid(264,56,336,112)
    elif index==81:
        solid(96,54,288,112);solid(72,88,96,112)
    elif index==86:
        # Root the combat terraces in the lowered bowl. Keeping the old thin
        # bridge31 units high would create an unreachable perch47 units above
        # the new floor; a grounded dais lets native pursuers climb its sides.
        shaped=[]
        for q in solids:
            if q.x0 in (66,194) and q.y0==0:q=replace(q,y0=-16)
            if q.x0==122 and q.y0==28:q=replace(q,y0=-16,y1=11)
            shaped.append(q)
        solids=shaped
    elif index==88:
        solids=[]
        for x,xx,top in ((0,80,64),(80,128,48),(128,176,32),(176,224,16)):solid(x,0,xx,top)
        for x,xx,y in ((96,144,88),(144,192,72),(192,224,56),(224,256,40)):solid(x,y,xx,112)
    result=replace(result,solids=tuple(solids),bounds=(0,-16,288,128) if index==86 else result.bounds)
    return painted.art.architecture(result,index)


def relocate_ports(raw,index):
    old_spec=old.SPECS[old.BY_ID[index]];newdoors=doors(index)
    source=RoomObjects.parse(raw);header=bytearray(source.header)
    for i,spawn in enumerate(room_doors.spawns(raw)):
        door=next((d for d in newdoors if d.spawn_id==spawn.spawn_id),None)
        if door:struct.pack_into('<3iH',header,16+i*20,*door.spawn['xyz'],room_doors.FACING[door.spawn['facing']])
        elif index==88 and spawn.spawn_id==0:struct.pack_into('<3i',header,16+i*20,240*4096,2*4096,0)
    result=bytes(header)+raw[len(source.header):]
    source=RoomObjects.parse(result);section=source.records[0].sections[0];entities=Entities.parse(section)
    for i,entity in enumerate(entities.records):
        if index==88 and source.names[0].labels[i]=='Character (Spiderman)':
            payload=bytearray(entity);struct.pack_into('<3i',payload,0,240*4096,2*4096,0)
            section=Entities.parse(section).replace_record(i,bytes(payload));continue
        if len(entity)!=28 or w.u32(entity,12)!=7:continue
        group=entity[27]-1
        if not 1<=group<=len(newdoors):continue
        d=newdoors[group-1];payload=bytearray(entity)
        struct.pack_into('<3i',payload,0,*d.exit['center'])
        section=Entities.parse(section).replace_record(i,bytes(payload))
    result=source.replace_section(0,0,section)
    return result


def overview(native):
    """Recognizable room silhouettes in the native overview, with the same graph."""
    centres={76:(20,80),78:(62,80),81:(104,80),83:(146,80),86:(184,80),87:(184,40),89:(146,40),88:(68,40),77:(62,112),82:(104,112)}
    sizes={76:(28,14),78:(34,18),81:(30,14),83:(20,26),86:(32,20),87:(18,20),89:(26,18),88:(34,18),77:(16,12),82:(22,10)}
    rects={};body={}
    for i,(cx,cy) in centres.items():
        width,height=sizes[i];a,b=cx-width//2,cy-height//2;rects[BY_ID[i]]=[(a,b,a+width,b+height)]
        x0,y0=0,-16 if i==86 else 0;ww,hh=SIZES[i];inside=set()
        for y in range(b,b+height):
            for x in range(a,a+width):
                u=(x-a+.5)/width;v=1-(y-b+.5)/height
                if i in POLYGONS:
                    point=(u*ww,y0+v*(hh-y0));poly=POLYGONS[i]
                    valid=all(envelope.cross(p,q,point)>=-.001 for p,q in zip(poly,(*poly[1:],poly[0])))
                elif i==76:valid=u<.38 or v<.58
                elif i==78:valid=(.22<u<.79) or v<(.72 if u<.22 else .5)
                elif i==81:valid=u<.32 or v<.48
                elif i==88:valid=abs(v-(.86-.7*u))<.22
                else:valid=True
                if valid:inside.add((x,y))
        for x,y in inside:body[x,y]=(BY_ID[i],ch.EDGE if any((x+dx,y+dy) not in inside for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))) else ch.FILL)
        if i in (77,82,87):
            for d in range(-2,3):body[cx+d,cy]=(BY_ID[i],ch.EDGE);body[cx,cy+d]=(BY_ID[i],ch.EDGE)
    def pixels():return body
    with patch.object(ch,'MAP_ROOMS',rects),patch.object(ch,'_map_pixels',pixels):raw,listing=ch.map_layout(native(ch.MAP_SOURCE))
    # Native palette slots continue to own room discovery/current-room tint.
    from tools.minimap_cbmp import Cbmp
    screen=Cbmp.parse(raw);wires={}
    for (a,g),(b,spawn) in LINKS.items():
        if a not in ch.BY_NAME or b not in ch.BY_NAME:continue
        i=ch.BY_NAME[a].index;j=ch.BY_NAME[b].index
        if i not in centres or j not in centres or i>j:continue
        ax,ay=centres[i];bx,by=centres[j]
        if {i,j}=={76,88}:via=((ax,ay),(20,40),(bx,by))
        else:via=((ax,ay),(bx,ay),(bx,by))
        for (x,y),(xx,yy) in zip(via,via[1:]):
            for tx in range(min(x,xx),max(x,xx)+1):
                if (tx,y) not in body:wires[tx,y]=a
            for ty in range(min(y,yy),max(y,yy)+1):
                if (xx,ty) not in body:wires[xx,ty]=a
    cells={}
    for (x,y),owner in wires.items():cells.setdefault((3+x//8,3+y//8),[]).append((x%8,y%8))
    tiles=[];updates={}
    for (cx,cy),points in sorted(cells.items()):
        entry=screen.screen[cy*screen.width+cx];palette=entry>>12;tile=list(screen.tile(entry&1023))
        pens=[slot%16+ch.EDGE for n,slot,x,y in listing if slot//16==palette and slot%16+ch.EDGE in tile]
        if pens:pen=pens[0]
        else:palette=11;pen=6;tile=[0]*64
        for x,y in points:tile[y*8+x]=pen
        updates[cx,cy]=palette<<12|screen.count+len(tiles);tiles.append(tile)
    screen,_=screen.with_tiles(tiles)
    return screen.with_screen(updates).to_bytes(),listing


def apply(names,blobs,new,native,offset,alloc,*,pilot=False):
    reports={};changed=[];lookup=w.u32(new,ch.LOOKUP_LITERAL-0x02000000)
    for index in ((86,) if pilot else old.ACTIVE):
        name=old.BY_ID[index];room=plan(index,native);polygon=POLYGONS.get(index,());bsp_index=names.index('zz_R21_'+name+'.bsp')
        built=envelope.compile_room(room,polygon,len(blobs[bsp_index])%4)
        tree=rc.rc.RoomCollision.parse(built.collision);ports=doors(index);spec=old.SPECS[name]
        obj_index=names.index('zz_'+name+'_app.obj');raw=relocate_ports(blobs[obj_index],index)
        camera=tuple((max(16,min(room.bounds[2]-16,x)),y) for x,y in polygon) if polygon else ((16,0),(room.bounds[2]-16,0),(room.bounds[2]-16,room.bounds[3]),(16,room.bounds[3]))
        raw=room_author.set_camera(raw,(camera,))
        anchors=room_author.plan_anchors(rc.surfaces(room),room.bounds,floor_top=room.bounds[3]-22,solid=lambda x,y:tree.solid_at(x,y) is not None)
        # The original axis-wall points outside sloping corners are invalid.
        # Supply real slanted ceiling/wall grip anchors instead.
        import math
        for nx,ny,d,a,b in envelope.planes(polygon) if polygon else ():
            steps=max(1,round(math.dist(a,b)/20))
            for step in range(steps+1):
                t=(step+.5)/(steps+1);x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
                if ny<-1800:point=(x,y+2,room_author.FLOOR)
                else:point=(x-nx/4096*4.5,y-ny/4096*4.5,room_author.CEILING if ny>1800 else room_author.LEFT_WALL if nx<0 else room_author.RIGHT_WALL)
                anchors.append(point)
        anchors=[(x,y,kind) for x,y,kind in anchors if not any(tree.solid_at(xx,yy) is not None for xx,yy in ((x,y),(x-2.5,y+3),(x+2.5,y+3)))]
        raw=room_author.set_anchors(raw,anchors)
        prefix='zz_R21_'+name
        assets={prefix+'.nsbmd':built.model,prefix+'.nsbtx':built.textures,prefix+'.bsp':built.collision,
            prefix+'.cbmp':envelope.detailed_map(native(ch.MAP_SOURCE),room,built.collision,ports,spec.save),'zz_'+name+'_app.obj':raw}
        for asset,payload in assets.items():
            i=names.index(asset)
            if asset.endswith('.bsp'):
                if len(payload)%4!=len(blobs[i])%4:raise ValueError('BSP alignment contract')
                blobs[i]=payload
            else:blobs[i]=payload+bytes((len(blobs[i])-len(payload))%4)
            changed.append(asset)
        desc=w.u32(new,offset(lookup)+index*4)
        struct.pack_into('<9i',new,offset(desc)+0x28,*room_minimap.projection(room,5).fields)
        for d in ports:
            x,y,z=d.spawn['xyz']
            if tree.solid_at(x/4096,y/4096+5) is not None:raise ValueError('Arrival buried in new envelope: '+name)
        reports[name]=dict(index=index,bounds=room.bounds,shape=SHAPES[index],polygon=polygon,quads=built.quads,
            native_bsp_nodes=len(tree.nodes),anchors=len(anchors),doors=[dict(side=d.side,wall=d.wall,floor=d.floor,spawn=d.spawn_id) for d in ports],
            collision_sha256=w.sha256(built.collision))
    if not pilot:
        from tools import crane_row,creature_forge
        raw,listing=overview(native);i=names.index(ch.MAP_SCREEN);blobs[i]=raw;changed.append(ch.MAP_SCREEN)
        areas=set()
        for at in range(0,__import__('tools.tasm_kit',fromlist=['SOURCE']).SOURCE,4):
            value=w.u32(new,at)
            if crane_row.CR_BASE<=value<creature_forge.START and w.u32(new,offset(value))==names.index('MMPier.cbmp') and w.u32(new,offset(value)+6*16)==names.index(crane_row.MAP_SCREEN):areas.add(value)
        if len(areas)!=1:raise ValueError('Exact owned native area table not found')
        area=areas.pop();table=alloc(ch.map_entries(listing));struct.pack_into('<2I',new,offset(area)+5*16+8,table,len(listing))
    return reports,changed
