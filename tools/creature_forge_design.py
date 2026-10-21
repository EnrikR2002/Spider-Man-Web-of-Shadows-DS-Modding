"""Authored encounter programs. Times are SCA samples, not native attack IDs.

Action numbers are resource slots only: all selected motion, events, shapes and
movement are replaced. Ground contact is low enough to jump; beams have lanes.
"""
from dataclasses import dataclass

STYLES=('maw','ballast','spore','skitter','warden','eye','conductor')
STEMS=('hLpr','brt','hRng','hLpr','brt','hRng','brt')
HP=(14,20,10,12,18,10,80)

@dataclass(frozen=True)
class Move:
    name:str
    action:int
    samples:int
    contacts:tuple
    kind:str
    reach:float
    drives:tuple=()       # sample start/end, local forward units/update
    jumps:tuple=()        # sample, vertical impulse; gravity remains native
    cooldown:int=18

MOVES={
 'maw':(
  Move('Riptide scissor',55,43,((13,16),(22,25)),'scissor',10,((12,17,.72),(21,25,.48))),
  Move('Anchor vault',63,49,((19,25),),'vault',23,((13,25,1.15),),((13,2.8),),24),
  Move('Keelbreaker feint',68,47,((21,26),),'feint',20,((5,11,-.45),(17,25,1.55)),(),25)),
 'ballast':(
  Move('Dredger sweep',55,55,((22,27),(33,37)),'sweep',11,((21,26,.28),(32,36,.2))),
  Move('Breakwater rupture',63,61,((22,29),(39,45)),'quake',19,(),(),26),
  Move('Hull charge',71,60,((23,32),(39,43)),'charge',29,((20,32,1.45),(33,36,.55)),(),28)),
 'spore':(
  Move('Seed procession',55,54,((16,21),(26,31),(36,41)),'seeds',37,((39,46,-.3),)),
  Move('Bloom recoil',63,47,((17,23),),'burst',12,((12,22,-.8),),((12,2.8),),22),
  Move('Lantern lance',68,52,((23,33),),'lance',40,(),(),24)),
 'skitter':(
  Move('Railcut cross',55,39,((11,14),(19,22)),'scissor',10,((10,14,.8),(18,22,.5),(26,30,-.35))),
  Move('Switchback execution',63,46,((19,25),),'feint',28,((6,12,-.65),(16,25,1.9)),(),24),
  Move('Overhead shear',68,51,((17,22),(32,36)),'shear',23,((11,24,1.15),),((11,3.2),),26)),
 'warden':(
  Move('Pendulum sentence',55,58,((20,25),(34,39)),'pendulum',12,((19,23,.2),)),
  Move('Deadbell peal',63,63,((24,31),(41,48)),'peal',20,(),(),28),
  Move('Toll march',71,66,((16,21),(30,35),(44,49)),'march',18,((11,16,.55),(25,30,.55),(39,44,.55)),(),26)),
 'eye':(
  Move('Arc guillotine',55,58,((25,39),),'beam',39,(),(),25),
  Move('Capacitor bloom',63,48,((19,26),),'burst',13,((13,24,-.65),),((13,2.8),),23),
  Move('Twin discharge',68,58,((17,26),(32,41)),'twins',39,(),(),25)),
 'conductor':(
  Move('Cadenza',55,66,((19,23),(31,35),(44,49)),'cadenza',15,((17,22,.45),(29,34,.4),(42,48,.6)),(),18),
  Move('Blackout fugue',63,76,((27,33),(43,49),(59,65)),'fugue',26,(),(),22),
  Move('Storm verdict',71,72,((27,38),(47,56)),'verdict',46,(),(),24),
  Move('Crownfall',136,70,((22,29),(42,51)),'crownfall',31,((14,29,1.3),),((14,3.4),),28)),
}

def arms(stem):
    # Leaper/ranger include a scapula before shoulder. Brute does not.
    return ((6,7,8),(13,14,15)) if stem=='brt' else ((7,8,9),(14,15,16))

def fx(move,f):
    """Two independently posed effects: (kind, centerY, forwardZ, scaleXYZ).

    Ring radius is 2 model units, orb radius .7. No damage outside contacts.
    Effects are parked below ground outside the corresponding contact/tell.
    """
    hidden=('ring',-24.,0.,(.01,.01,.01))
    if move is None:return (hidden,hidden)
    k=move.kind;out=[]
    for i,(a,b) in enumerate(move.contacts):
        if not a-4<=f<=b+3:continue
        u=max(0.,min(1.,(f-a)/max(1,b-a)))
        if k in ('quake','fugue','march','peal') or k=='crownfall' and i==1:
            rad=(5.+(move.reach-5)*u)/2
            y=6.7 if k=='peal' and i==0 else .65
            out.append(('ring',y,0.,(rad,.32,rad)))
        elif k in ('seeds','twins'):
            z=3+(move.reach-4)*u
            y=(7.5 if i%2==0 else 2.8) if k=='twins' else 4.3
            out.append(('orb',y,z,(1.4,1.4,1.4)))
        elif k in ('lance','beam','verdict'):
            y=7.8-5.4*u if k=='beam' else 7.0 if k=='verdict' and i==0 else 3.0 if k=='verdict' else 5.8
            out.append(('beam',y,move.reach/2,(.3,.65,move.reach/4)))
        elif k=='burst':
            rad=2+4*u;out.append(('ring',4.,0.,(rad,rad,rad)))
        else:
            # Short claw arc follows the actual striking hand, posed in motion.
            out.append(('claw',3.3,4.2,(1.,1.,1.)))
    return tuple((out+[hidden,hidden])[:2])

def hit_shape(move,f):
    """(center height, forward center, full height, horizontal radius)."""
    active=next(((i,a,b) for i,(a,b) in enumerate(move.contacts) if a<=f<b),None)
    if active is None:return (3.,0.,.2,.1)
    i,a,b=active;u=(f-a)/max(1,b-a);k=move.kind
    if k in ('quake','fugue','march') or k=='crownfall' and i==1:return (1.1,0.,2.2,5+(move.reach-5)*u)
    if k=='peal':return (6.7 if i==0 else 1.1,0.,2.2,5+(move.reach-5)*u)
    if k in ('seeds','twins'):
        y=(7.5 if i%2==0 else 2.8) if k=='twins' else 4.3
        return (y,3+(move.reach-4)*u,2.5,2.)
    if k in ('beam','lance','verdict'):
        y=7.8-5.4*u if k=='beam' else 7. if k=='verdict' and i==0 else 3. if k=='verdict' else 5.8
        return (y,move.reach/2,1.9,move.reach/2)
    if k=='burst':return (4.,0.,8.,4+move.reach*.5*u)
    if k in ('vault','shear','crownfall'):return (3.8 if i==0 else 1.4,2.7,5.8 if i==0 else 2.8,4.6)
    if k in ('sweep','pendulum','cadenza'):return (5.8 if i%2==0 else 2.2,3.2,4. if i%2==0 else 3.,5.)
    return (3.7,4.,5.2,3.7)
