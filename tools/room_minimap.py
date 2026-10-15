"""Detailed CBMP maps for authored rooms, derived from the collision plan.

Native descriptor fields +2C/+30 and +34/+38 are map rectangle endpoints,
not its size (0x02084ACC subtracts them). +3C..48 are world endpoints.
"""
from dataclasses import dataclass
from tools.minimap_cbmp import Cbmp

U=4096
VIEW=(30,30,218,146)
PALETTE=1
COLOURS=(0x1042,0x1042,0x28C4,0x73B7,0x4B10,0x2FFF,0x7C1F,0x021F,0x03FF,0x7FFF)


@dataclass(frozen=True)
class Projection:
    bounds:tuple
    rect:tuple
    area:int=5

    def point(self,x,y):
        x0,y0,x1,y1=self.bounds;l,t,r,b=self.rect
        return round(l+(x-x0)*(r-l)/(x1-x0)),round(b-(y-y0)*(b-t)/(y1-y0))

    @property
    def fields(self):
        x0,y0,x1,y1=self.bounds;l,t,r,b=self.rect
        return (self.area,*(round(v*U) for v in (l,t,r,b,x0,y1,x1,y0)))


def projection(room,area=5):
    x0,y0,x1,y1=room.bounds;l,t,r,b=VIEW
    scale=min((r-l)/(x1-x0),(b-t)/(y1-y0))
    w,h=round((x1-x0)*scale),round((y1-y0)*scale)
    left=l+(r-l-w)//2;top=t+(b-t-h)//2
    return Projection(room.bounds,(left,top,left+w,top+h),area)


def build(template,room,doors,*,hazards=(),cores=(),save=()):
    """Keep native frame/HUD palettes, replace only the empty detail-map panel."""
    screen=Cbmp.parse(template)
    pixels=[[1]*256 for _ in range(192)]
    p=projection(room);l,t,r,b=p.rect
    def fill(x0,y0,x1,y1,colour):
        for y in range(max(24,y0),min(152,y1)):
            for x in range(max(24,x0),min(224,x1)):pixels[y][x]=colour
    def worldbox(x0,y0,x1,y1,colour):
        a,z=p.point(x0,y1);c,d=p.point(x1,y0)
        fill(min(a,c),min(z,d),max(a,c)+1,max(z,d)+1,colour)
    fill(l,t,r+1,b+1,3);fill(l+2,t+2,r-1,b-1,1)
    for solid in room.solids:
        if solid.hidden:continue
        worldbox(solid.x0,solid.y0,solid.x1,solid.y1,2)
        a,z=p.point(solid.x0,solid.y1);c,d=p.point(solid.x1,solid.y1)
        fill(a,z,c+1,z+2,3)
    for door in doors:
        x,y=p.point(door.wall,door.floor+6)
        fill(x-2,y-3,x+3,y+4,5)
    for phase in hazards:
        for x,y in phase:
            a,z=p.point(x,y);fill(a-2,z-1,a+3,z+2,6)
    for x,y in cores:
        a,z=p.point(x,y);fill(a-3,z-3,a+4,z+4,7);fill(a-1,z-1,a+2,z+2,9)
    if save:
        a,z=p.point(*save);fill(a-3,z-3,a+4,z+4,8);fill(a-1,z-1,a+2,z+2,9)
    cells={};tiles=[]
    for cy in range(3,19):
        for cx in range(3,28):
            tile=[pixels[cy*8+y][cx*8+x] for y in range(8) for x in range(8)]
            cells[cx,cy]=PALETTE<<12|screen.count+len(tiles);tiles.append(tile)
    screen,_=screen.with_tiles(tiles)
    screen=screen.with_screen(cells).with_colors({PALETTE*16+i:c for i,c in enumerate(COLOURS)})
    return screen.to_bytes(),p
