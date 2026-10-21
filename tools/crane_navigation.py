"""Crane Row's door graph, labelled maps and progress-aware map selection.

Only the private area6 screen is selected differently. Native map colours
still distinguish current/visited rooms; dim rooms show the district plan.
"""
from dataclasses import dataclass
from unittest.mock import patch
from tools import crane_rooms as cr, crane_art as art, midnight_chapter as ch
from tools import crane_boss as cb
from tools import room_script as script
from tools.room_events import EventGroup
from tools.minimap_cbmp import Cbmp

GOAL,LOCK=1,3                         # unused room-slot roles
SCREEN_SITE=0x020E136C
SCREEN_ORIGINAL=0xE7911202             # ldr r1,[r1,r2,lsl#4]
OBJECTIVE_SITE=0x020E0F28
OBJECTIVE_NATIVE=0x020D13CC
GOAL_TITLES=('Restore cargo power','Clear the Crown crew','Defeat the hoist','Return to the Pier')
GOAL_BODIES=('objective_power','objective_crown','objective_hoist','objective_done')
RECTS=dict(zip(cr.NAMES,((10,92,38,114),(48,84,76,114),(46,62,86,80),
    (86,96,114,114),(124,96,152,114),(162,84,190,114),(10,22,42,52),
    (50,32,82,50),(148,62,190,80),(90,22,122,52),(130,20,154,38),(162,20,190,38))))
LABELS=dict(zip(cr.NAMES,('QUAY','FRGT','OFFC','YARD','DOCK','ENG','SHAFT','GNTR','CACHE','CROWN','ARM','BWTR')))
HEADERS=(('POWER: ENGINE', ''),('CROWN CREW', ''),('HOIST', ''),('RETURN: PIER', ''))
TARGETS=(cr.NAMES[5],cr.NAMES[9],cr.NAMES[10],cr.NAMES[0])
SCREENS=('zz_CraneOverview.cbmp',*(f'zz_CraneGuide{i}.cbmp' for i in range(1,4)))

@dataclass(frozen=True)
class Link:
    source:tuple
    destination:tuple|None
    code:str|None=None
    bends:tuple=()

LINKS=(
    Link((cr.NAMES[0],2),(cr.NAMES[1],1)),
    Link((cr.NAMES[1],2),(cr.NAMES[3],1)),
    Link((cr.NAMES[3],2),(cr.NAMES[4],1)),
    Link((cr.NAMES[4],2),(cr.NAMES[5],1)),
    Link((cr.NAMES[5],2),(cr.NAMES[6],1),'A'),
    Link((cr.NAMES[6],2),(cr.NAMES[7],1),bends=((46,None),)),
    Link((cr.NAMES[7],2),(cr.NAMES[9],1),bends=((86,None),)),
    Link((cr.NAMES[9],3),(cr.NAMES[10],1),bends=((126,None),)),
    Link((cr.NAMES[10],2),(cr.NAMES[11],1)),
    Link((cr.NAMES[11],2),(cr.NAMES[0],3),'B'),
    Link((cr.NAMES[1],4),(cr.NAMES[5],3),'C'),
    Link((cr.NAMES[5],5),(cr.NAMES[9],2),'D'),
    Link((cr.NAMES[1],3),(cr.NAMES[2],1),bends=((42,None),(42,82),(90,82),(90,None))),
    Link((cr.NAMES[5],4),(cr.NAMES[8],1),bends=((196,None),(196,82),(142,82),(142,None))),
    Link((cr.NAMES[0],1),None,'P'),
)

def phase(flags):
    if flags>>cr.FLAGS['boss']&1:return 3
    if flags>>cr.FLAGS['crown']&1:return 2
    return 1 if flags>>cr.FLAGS['power']&1 else 0

def phase_flags(stage):
    return sum(1<<cr.FLAGS[k] for k in ('power','upper','crown','boss')
               if stage>={'power':1,'upper':2,'crown':2,'boss':3}[k])

def port(key):
    name,group=key;side,_,floor,_=cr.PORTS[name][group-1]
    x0,y0,x1,y1=RECTS[name]
    levels=sorted({p[2] for p in cr.PORTS[name]})
    y=y1-3 if len(levels)==1 else round(y1-3-levels.index(floor)*(y1-y0-6)/(len(levels)-1))
    return (x0 if side=='left' else x1-1,y)

def path(link):
    start,end=port(link.source),port(link.destination)
    if not link.bends:return (start,end)
    if len(link.bends)==1:
        x=link.bends[0][0];return (start,(x,start[1]),(x,end[1]),end)
    return (start,*((x,start[1] if i==0 else end[1] if i==len(link.bends)-1 else y)
                     for i,(x,y) in enumerate(link.bends)),end)

def stroke(points):
    out=set()
    for (x0,y0),(x1,y1) in zip(points,points[1:]):
        if x0!=x1 and y0!=y1:raise ValueError('Map connector must be orthogonal')
        n=max(abs(x1-x0),abs(y1-y0),1)
        out.update((round(x0+(x1-x0)*i/n),round(y0+(y1-y0)*i/n)) for i in range(n+1))
    return out

def text(text,x,y):
    out=set()
    for n,char in enumerate(text):
        for yy,row in enumerate(art.FONT[char]):
            out.update((x+6*n+xx,y+yy) for xx,value in enumerate(row) if value=='1')
    return out

def code_marker(key):
    name,group=key;side=cr.PORTS[name][group-1][0];x,y=port(key)
    if side=='left':return ((x,y),(x-2,y)),(x-8,y-3)
    return ((x,y),(x+2,y)),(x+4,y-3)

def map_pixels(stage,*,extra_saves=()):
    out={};flags=phase_flags(stage)
    for name,(x0,y0,x1,y1) in RECTS.items():
        for x in range(x0,x1):
            for y in range(y0,y1):
                edge=x in (x0,x1-1) or y in (y0,y1-1)
                out[x,y]=(name,GOAL if edge and name==TARGETS[stage] else ch.EDGE if edge else ch.FILL)
        # Keep the room shapes and real ports; only meaningful landmarks
        # get an icon. Repeated labels made a tiny DS map a wall of text.
        icons={cr.NAMES[2]:('11111','10001','10101','10001','11111'),
               cr.NAMES[5]:('00110','01100','11111','00110','01100'),
               cr.NAMES[9]:('10001','10101','11111','01110','01110'),
               cr.NAMES[10]:('11111','00100','00100','00100','01100'),
               cr.NAMES[8]:('01110','11111','11011','11111','11111')}
        icon=icons.get(name,());tx=(x0+x1-5)//2;ty=(y0+y1-5)//2
        for yy,row in enumerate(icon):
            for xx,value in enumerate(row):
                if value=='1':out[tx+xx,ty+yy]=(name,ch.EDGE)
        if name in extra_saves:
            for yy,row in enumerate(('11111','10000','11111','00001','11111')):
                for xx,value in enumerate(row):
                    if value=='1':out[x0+3+xx,y1-7+yy]=(name,ch.EDGE)
    for link in LINKS:
        if link.code:
            for key in (link.source,link.destination):
                if key is None:continue
                name,group=key;line,xy=code_marker(key)
                locked=key in cr.LOCKS and not flags>>cr.FLAGS[cr.LOCKS[key][0]]&1
                for p in stroke(line)|text(link.code,*xy):out[p]=(name,LOCK if locked else ch.EDGE)
        else:
            pixels=stroke(path(link));keys=(link.source,link.destination)
            for p in pixels:
                nearest=min(keys,key=lambda k:abs(port(k)[0]-p[0])+abs(port(k)[1]-p[1]))
                out[p]=(nearest[0],ch.EDGE)
            for key in keys:
                locked=key in cr.LOCKS and not flags>>cr.FLAGS[cr.LOCKS[key][0]]&1
                x,y=port(key)
                # A fixed footprint keeps the palette/list allocation equal
                # in all four progress screens. Red bars mean locked exits.
                for dy in (-1,0,1):out[x,y+dy]=(key[0],LOCK if locked else ch.EDGE)
    return out

def overview(raw,stage=0,*,extra_saves=()):
    palettes=tuple(p for p in ch.MAP_PALETTES if p!=11)
    colours=(0x1042,0x03FF,0x3548,0x001F,0x5E30)
    with patch.multiple(ch,MAP_ROOMS={n:[r] for n,r in RECTS.items()},MAP_PALETTES=palettes,
                        SLOT_DEFAULT=colours,_map_pixels=lambda:map_pixels(stage,extra_saves=extra_saves)):
        result,listing=ch.map_layout(raw)
    listing=[(n,slot,24+RECTS[n][0]+5,24+RECTS[n][1]+9) if n==cr.NAMES[2] else (n,slot,x,y)
             for n,slot,x,y in listing]
    screen=Cbmp.parse(result)
    # Palette11 is reserved from room allocation. B6..BA = current room,
    # BB..BF = unvisited; both keep objective/lock accents unchanged.
    colours={0xB1:0x1042,0xB2:0x7FFF,0xB3:0x03FF,0xB4:0x001F,0xB5:0x5E30,
             0xB6:0x1042,0xB7:0x03FF,0xB8:0x4E0E,0xB9:0x001F,0xBA:0x7FFF,
             0xBB:0x1042,0xBC:0x03FF,0xBD:0x2084,0xBE:0x001F,0xBF:0x3D89}
    static={}
    label=HEADERS[stage][0]
    for xy in text(label,(200-(6*len(label)-1))//2,4):static[xy]=3
    cells={};tiles=[]
    for cy in (0,1,15):
        for cx in range(25):
            tile=[static.get((cx*8+x,cy*8+y),1) for y in range(8) for x in range(8)]
            cells[cx+3,cy+3]=11<<12|screen.count+len(tiles);tiles.append(tile)
    screen,_=screen.with_tiles(tiles)
    return screen.with_screen(cells).with_colors(colours).to_bytes(),listing

def screen_adapter(at,resources):
    """Replace one native LDR; preserve all registers except its r1 result/flags."""
    if len(resources)!=4:raise ValueError('Four progress screens required')
    a=cb.Arm(at);a.emit(0xE92D500D,0xE10FC000,0xE3520006);a.b('fallback',1)
    a.lit(0,'stats',0x02145C5C);a.emit(0xE5900000,0xE3500000);a.b('fallback',0)
    a.emit(0xE5903000,0xE3530060);a.b('fallback',3);a.emit(0xE353006C);a.b('fallback',2)
    a.emit(0xE5D0302D,0xE3130040);a.b('phase3',1)
    a.emit(0xE5D0302E,0xE3130004);a.b('phase2',1)
    a.emit(0xE5D0302D,0xE3130010);a.b('phase1',1)
    a.lit(1,'map0',resources[0]);a.b('done')
    for i in (1,2,3):a.label('phase'+str(i));a.lit(1,'map'+str(i),resources[i]);a.b('done')
    a.label('fallback');a.emit(SCREEN_ORIGINAL)
    a.label('done');a.emit(0xE128F00C,0xE8BD500D);a.b(SCREEN_SITE+4)
    return a.finish()

def detail_labels(name):
    return ()

def objective_adapter(at,records):
    """Private title/body pair only at the native Objectives-page getter call.

    Other rooms tail-call the original getter with its original arguments.
    No mission counter or persistent progress is written.
    """
    a=cb.Arm(at);a.emit(0xE92D500B,0xE10FC000)
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('fallback',0)
    a.emit(0xE5923000,0xE3530060);a.b('fallback',3);a.emit(0xE353006C);a.b('fallback',2)
    a.emit(0xE5D2302D,0xE3130040);a.b('phase3',1)
    a.emit(0xE5D2302E,0xE3130004);a.b('phase2',1)
    a.emit(0xE5D2302D,0xE3130010);a.b('phase1',1)
    a.lit(2,'goal0',records);a.b('store')
    for i in (1,2,3):a.label('phase'+str(i));a.lit(2,'goal'+str(i),records+i*8);a.b('store')
    a.label('store');a.emit(0xE5802000,0xE128F00C,0xE8BD500B,0xE12FFF1E)
    a.label('fallback');a.emit(0xE128F00C,0xE8BD500B);a.b(OBJECTIVE_NATIVE)
    return a.finish()

def entry_keys(name):
    if name in (cr.NAMES[2],cr.NAMES[8]):return (name,)*4
    early=name
    powered={cr.NAMES[0]:'quay_power',cr.NAMES[1]:'freight_power',cr.NAMES[5]:'power',
             cr.NAMES[6]:cr.NAMES[6],cr.NAMES[7]:cr.NAMES[7],cr.NAMES[9]:cr.NAMES[9],
             cr.NAMES[10]:cr.NAMES[10]}.get(name,'guide_crown')
    cleared=cr.NAMES[10] if name==cr.NAMES[10] else 'crown_clear' if name==cr.NAMES[9] else 'guide_hoist'
    complete='guide_done'
    if name==cr.NAMES[11]:return ('return_locked','return_locked','return_locked',name)
    return early,powered,cleared,complete

def entry_guidance(raw,name,say):
    """First-visit local instructions selected from earned progress; no new flags."""
    groups={}
    for key in dict.fromkeys(entry_keys(name)):
        raw,groups[key]=script.append_groups(raw,1,[(EventGroup((say(key),)),'Guide_'+key)])
    early,powered,cleared,complete=(groups[k] for k in entry_keys(name))
    raw,power=script.append_groups(raw,1,[(EventGroup((script.if_var(cr.FLAGS['power'],'!=',0,
        then=script.action(eg=powered),otherwise=script.action(eg=early)),)),'Guide_Power')])
    raw,crown=script.append_groups(raw,1,[(EventGroup((script.if_var(cr.FLAGS['crown'],'!=',0,
        then=script.action(eg=cleared),otherwise=script.action(eg=power)),)),'Guide_Crown')])
    raw,boss=script.append_groups(raw,1,[(EventGroup((script.if_var(cr.FLAGS['boss'],'!=',0,
        then=script.action(eg=complete),otherwise=script.action(eg=crown)),)),'Guide_Hoist')])
    return script.extend_group(raw,1,0,[script.if_var(cr.VISITS[cr.IDS[name]],'==',0,
                                then=script.action(eg=boss))],prepend=True)
