"""Convex sloping room boundaries on top of the existing box compiler.

Visible cut faces, native BSP half-planes and the detailed map use one polygon.
Axis-aligned inner solids and nonconvex stepped corridors remain ordinary boxes.
"""
from dataclasses import replace
import math,struct
from tools import room_compiler as rc,room_collision as collision,room_minimap as minimap
from tools.minimap_cbmp import Cbmp


def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def planes(polygon):
    if len(polygon)<3 or any(cross(polygon[i-1],polygon[i],polygon[(i+1)%len(polygon)])<-.001 for i in range(len(polygon))):raise ValueError('Envelope must be convex and counterclockwise')
    out=[];bounds=(min(x for x,y in polygon),min(y for x,y in polygon),max(x for x,y in polygon),max(y for x,y in polygon))
    for a,b in zip(polygon,(*polygon[1:],polygon[0])):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.01:raise ValueError('Degenerate envelope edge')
        nx,ny=round(dy/length*4096),round(-dx/length*4096)
        distance=round((nx*a[0]+ny*a[1])/4)*4
        if nx==0 and a[1] in (bounds[1],bounds[3]):continue
        if ny==0 and a[0] in (bounds[0],bounds[2]):continue
        out.append((nx,ny,distance,a,b))
    return out


def clip(poly,nx,ny,d,inside=True):
    out=[];sign=1 if inside else -1
    for a,b in zip(poly,(*poly[1:],poly[0])):
        da=(nx*a[0]+ny*a[1]-d)*sign;db=(nx*b[0]+ny*b[1]-d)*sign
        if da<=.0001:out.append(a)
        if (da<0<db) or (db<0<da):
            t=da/(da-db);out.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
    return tuple(out)


def visual(plan,polygon):
    scene=list(plan.scenery);x,y,xx,yy=plan.bounds;rect=((x,y),(xx,y),(xx,yy),(x,yy))
    wall=plan.theme['front'];edge=plan.theme['under'];cuts=planes(polygon);previous=[]
    for nx,ny,d,a,b in cuts:
        region=clip(rect,nx,ny,d,False)
        for px,py,pd in previous:
            if region:region=clip(region,px,py,pd)
        if len(region)>=3:
            for i in range(1,len(region)-1):
                points=(region[0],region[i],region[i+1],region[i+1])
                scene.append(rc.Quad(wall,tuple((x,y,rc.DEPTH+.03) for x,y in points),tuple((x/wall.size[0],-y/wall.size[1]) for x,y in points),.9))
        corners=((*a,-rc.DEPTH),(*a,rc.DEPTH),(*b,rc.DEPTH),(*b,-rc.DEPTH))
        length=math.dist(a,b)
        scene.append(rc.Quad(edge,corners,((0,0),(0,50/edge.size[1]),(length/edge.size[0],50/edge.size[1]),(length/edge.size[0],0)),.85))
        previous.append((nx,ny,d))
    return replace(plan,scenery=tuple(scene))


def collision_bytes(raw,polygon,modulo=None):
    source=collision.RoomCollision.parse(raw);source.check_tree();cuts=planes(polygon) if polygon else []
    if modulo is not None and (len(raw)+2*len(cuts))%4!=modulo:
        # BSP lists are2 mod4. Add a redundant, unreachable split inside the
        # already-solid far exterior rather than appending invalid list bytes.
        if (len(raw)+2*len(cuts)+2)%4!=modulo:raise ValueError('Impossible BSP alignment residue')
        cuts.append((4096,0,32760*4096,(32760,0),(32760,1)))
    count=len(cuts)
    if not count:return raw
    if source.nodes[0][1]!=0x40000002 or source.nodes[1][1]!=0x40000006:raise ValueError('Expected compiler depth slab first')
    nodes=list(source.nodes[:2]);lists=list(source.lists)
    for i,(nx,ny,d,a,b) in enumerate(cuts):
        normal=(0x40000000|(4 if nx<0 else 0)) if ny==0 else (0x40000001|(4 if ny<0 else 0)) if nx==0 else ((-nx)&65535)|(((-ny)&65535)<<16)
        nodes.append((d|1,normal,0,len(lists)))
        lists.append(tuple([(2+i,collision.PLAIN),*((2+j,collision.PLAIN) for j in reversed(range(i))),(1,collision.PLAIN),(0,collision.PLAIN)]))
    for i,(d,normal,unknown,link) in enumerate(source.nodes[2:],2):
        if not d&1 and not d&2:link+=count
        nodes.append((d,normal,unknown,link))
    for i in range(2,len(source.lists)):
        lists[i]=tuple((n+count if n>=2 else n,v) for n,v in lists[i])+tuple((2+j,collision.PLAIN) for j in reversed(range(count)))
    table_end=24+4*len(lists);body=b''.join(struct.pack('<iIHH',*n) for n in nodes);offsets=[]
    for entries in lists:
        offsets.append(table_end+len(body));body+=struct.pack('<H',len(entries))+b''.join(struct.pack('<HH',*e) for e in entries)
    result=b'BSP\0'+struct.pack('<4I',7,2,table_end+len(body),table_end)+struct.pack('<'+'I'*len(offsets),*offsets)+struct.pack('<I',0x01000000)+body
    parsed=collision.RoomCollision.parse(result);parsed.check_tree()
    if parsed.to_bytes()!=result:raise ValueError('Envelope BSP round trip')
    return result


def compile_room(plan,polygon=(),modulo=None):
    shaped=visual(plan,polygon) if polygon else plan;built=rc.compile_room(shaped)
    return replace(built,collision=collision_bytes(built.collision,polygon,modulo)) if polygon or modulo is not None else built


def detailed_map(template,plan,raw_collision,doors,save=()):
    """Rasterize actual walkable space, including slants and stepped envelopes."""
    tree=collision.RoomCollision.parse(raw_collision);p=minimap.projection(plan);l,t,r,b=p.rect
    pixels=[[1]*256 for _ in range(192)];x0,y0,x1,y1=plan.bounds
    for yy in range(t,b+1):
        for xx in range(l,r+1):
            wx=x0+(xx-l)/(r-l)*(x1-x0);wy=y1-(yy-t)/(b-t)*(y1-y0)
            pixels[yy][xx]=2 if tree.solid_at(wx,wy) is not None else 1
    for yy in range(t,b+1):
        for xx in range(l,r+1):
            if pixels[yy][xx]!=1:continue
            if any(px<l or px>r or py<t or py>b or pixels[py][px]==2 for px,py in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1))):pixels[yy][xx]=3
    def mark(x,y,pen):
        xx,yy=p.point(x,y)
        for dy in range(-2,3):
            for dx in range(-2,3):
                if 24<=xx+dx<224 and 24<=yy+dy<152:pixels[yy+dy][xx+dx]=pen
    for d in doors:mark(d.wall,d.floor+6,5)
    if save:mark(*save,8)
    screen=Cbmp.parse(template);tiles=[];cells={}
    for cy in range(3,19):
        for cx in range(3,28):
            cells[cx,cy]=minimap.PALETTE<<12|screen.count+len(tiles)
            tiles.append([pixels[cy*8+dy][cx*8+dx] for dy in range(8) for dx in range(8)])
    screen,_=screen.with_tiles(tiles);screen=screen.with_screen(cells).with_colors({minimap.PALETTE*16+i:c for i,c in enumerate(minimap.COLOURS)})
    return screen.to_bytes()
