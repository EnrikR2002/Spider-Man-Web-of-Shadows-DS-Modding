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
# One ring, as the doors run: Quay, Freight, Yard, Dock and Engine along the
# ground, the Shaft up the right edge, then Gantry, Crown, Arm and Breakwater
# back along the roofs to Quay. Every pair of doors is a short neck between
# touching rooms, as on the native maps; only the Pier exit is a dotted arrow.
# Both rows sit on their floors, so a room's height reads as its height.
RECTS=dict(zip(cr.NAMES,((12,80,33,118),(36,76,61,118),(36,58,61,69),
    (64,90,86,118),(89,98,112,118),(115,70,147,118),(171,18,189,118),
    (126,38,167,54),(151,86,167,100),(90,32,123,54),(46,30,87,54),(12,36,43,54))))
# Extra rectangles joined to a room's main one: roofs, towers and stacks.
EXTRA={cr.NAMES[3]:((64,84,76,90),),cr.NAMES[4]:((95,88,106,98),),cr.NAMES[9]:((98,18,114,32),),
       cr.NAMES[10]:((60,24,74,30),),cr.NAMES[1]:((53,70,61,76),)}
LABELS=dict(zip(cr.NAMES,('QUAY','FRGT','OFFC','YARD','DOCK','ENG','SHAFT','GNTR','CACHE','CROWN','ARM','BWTR')))
HEADERS=(('POWER: ENGINE', ''),('CROWN CREW', ''),('HOIST', ''),('RETURN: PIER', ''))
TARGETS=(cr.NAMES[5],cr.NAMES[9],cr.NAMES[10],cr.NAMES[0])
SCREENS=('zz_CraneOverview.cbmp',*(f'zz_CraneGuide{i}.cbmp' for i in range(1,4)))

@dataclass(frozen=True)
class Link:
    source:tuple
    destination:tuple|None
    neck:tuple|None=None                  # filled strip between the two touching rooms
    arrow:tuple|None=None                 # (x,y,dx): dotted exit stub leaving a room

LINKS=(
    Link((cr.NAMES[0],2),(cr.NAMES[1],1),(33,108,36,111)),
    Link((cr.NAMES[1],2),(cr.NAMES[3],1),(61,108,64,111)),
    Link((cr.NAMES[3],2),(cr.NAMES[4],1),(86,108,89,111)),
    Link((cr.NAMES[4],2),(cr.NAMES[5],1),(112,108,115,111)),
    Link((cr.NAMES[5],2),(cr.NAMES[6],1),(147,112,171,115)),
    Link((cr.NAMES[6],2),(cr.NAMES[7],1),(167,41,171,44)),
    Link((cr.NAMES[7],2),(cr.NAMES[9],1),(123,46,126,49)),
    Link((cr.NAMES[9],3),(cr.NAMES[10],1),(87,46,90,49)),
    Link((cr.NAMES[10],2),(cr.NAMES[11],1),(43,46,46,49)),
    Link((cr.NAMES[11],2),(cr.NAMES[0],3),(15,54,18,80)),
    Link((cr.NAMES[1],4),(cr.NAMES[5],3),(61,80,115,83)),
    Link((cr.NAMES[5],5),(cr.NAMES[9],2),(117,54,120,70)),
    Link((cr.NAMES[1],3),(cr.NAMES[2],1),(47,69,50,76)),
    Link((cr.NAMES[5],4),(cr.NAMES[8],1),(147,92,151,95)),
    Link((cr.NAMES[0],1),None,arrow=(12,114,-1)),
)

def phase(flags):
    if flags>>cr.FLAGS['boss']&1:return 3
    if flags>>cr.FLAGS['crown']&1:return 2
    return 1 if flags>>cr.FLAGS['power']&1 else 0

def phase_flags(stage):
    return sum(1<<cr.FLAGS[k] for k in ('power','upper','crown','boss')
               if stage>={'power':1,'upper':2,'crown':2,'boss':3}[k])

def locked(key,flags):
    return key in cr.LOCKS and not flags>>cr.FLAGS[cr.LOCKS[key][0]]&1

def rects(name):return (RECTS[name],*EXTRA.get(name,()))

def rect_gap(x,y,rect):
    x0,y0,x1,y1=rect
    return max(x0-x,0,x-x1+1)+max(y0-y,0,y-y1+1)

def shape(name):
    return {(x,y) for x0,y0,x1,y1 in rects(name) for x in range(x0,x1) for y in range(y0,y1)}

def neck_pixels(link,flags):
    """Pixels of one connecting neck: each half belongs to the room it touches
    and turns red while that room's door is still locked."""
    out={}
    x0,y0,x1,y1=link.neck
    for x in range(x0,x1):
        for y in range(y0,y1):
            key=min((link.source,link.destination),key=lambda k:min(rect_gap(x,y,r) for r in rects(k[0])))
            out[x,y]=(key[0],LOCK if locked(key,flags) else ch.EDGE)
    return out

def arrow_pixels(link):
    """A dotted stub and arrow head leaving the room's side, as the native maps mark their exits."""
    x,y,dx=link.arrow
    dots=[(x+dx*(2+2*i),y) for i in range(3)]
    tip=x+dx*8
    head=[(tip,y),(tip-dx,y-1),(tip-dx,y+1),(tip-2*dx,y-2),(tip-2*dx,y+2)]
    return dots+head

def text(text,x,y):
    out=set()
    for n,char in enumerate(text):
        for yy,row in enumerate(art.FONT[char]):
            out.update((x+6*n+xx,y+yy) for xx,value in enumerate(row) if value=='1')
    return out

def map_pixels(stage,*,extra_saves=()):
    out={};flags=phase_flags(stage)
    icons={cr.NAMES[5]:('00110','01100','11111','00110','01100'),
           cr.NAMES[9]:('10001','10101','11111','01110','01110'),
           cr.NAMES[10]:('11111','00100','00100','00100','01100'),
           cr.NAMES[8]:('01110','11111','11011','11111','11111')}
    for name,(x0,y0,x1,y1) in RECTS.items():
        inside=shape(name)
        for x,y in inside:
            edge=any((x+dx,y+dy) not in inside for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))
            out[x,y]=(name,GOAL if edge and name==TARGETS[stage] else ch.EDGE if edge else ch.FILL)
        # Only landmarks get an icon, in the upper left so the native
        # you-are-here marker keeps the room centre.
        for yy,row in enumerate(icons.get(name,())):
            for xx,value in enumerate(row):
                if value=='1':out[x0+3+xx,y0+3+yy]=(name,ch.EDGE)
        if name in extra_saves or name==cr.NAMES[2]:
            for yy,row in enumerate(('11111','10000','11111','00001','11111')):
                for xx,value in enumerate(row):
                    if value=='1':out[x0+3+xx,y1-8+yy]=(name,ch.EDGE)
    for link in LINKS:
        if link.neck:out.update(neck_pixels(link,flags))
        else:
            for p in arrow_pixels(link):out[p]=(link.source[0],ch.EDGE)
    return out

def overview(raw,stage=0,*,extra_saves=()):
    palettes=tuple(p for p in ch.MAP_PALETTES if p!=11)
    colours=(0x1042,0x03FF,0x3548,0x001F,0x5E30)
    with patch.multiple(ch,MAP_ROOMS={n:list(rects(n)) for n in RECTS},MAP_PALETTES=palettes,
                        SLOT_DEFAULT=colours,_map_pixels=lambda:map_pixels(stage,extra_saves=extra_saves)):
        result,listing=ch.map_layout(raw)
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
