"""Original synthesized creature voices, appended without replacing native sounds."""
import math,struct
from tools import sdat,wos_tool as w

FIRST=582
SITE=0x0203D5E4
STATE_SITE=0x02077844
KINDS=('ballast','spore','maw')
CATEGORIES=('alert','attack','death','hurt','idle')
RANGES=((306,310),(311,315),(316,318),(319,323),(324,328),
        (457,461),(462,466),(467,469),(470,474),(475,479),
        (480,484),(485,489),(490,492),(493,497),(498,501))

def voice(kind,category):
    rate=11025;duration=(.42,.36,.65,.18,.32)[CATEGORIES.index(category)]
    n=round(duration*rate);n+=-n%4;out=bytearray();noise=0x5783
    phase=0.;smooth=0.
    for i in range(n):
        t=i/rate;u=i/max(1,n-1);noise=(noise*1664525+1013904223)&0xFFFFFFFF
        rand=((noise>>16)/32767.5-1);smooth=.8*smooth+.2*rand
        env=min(1,u*28)*(1-u)**(1.3 if category!='death' else .75)
        pitch=(1.35 if category=='hurt' else .75 if category=='death' else 1)
        if kind=='maw':
            phase+=2*math.pi*(145+90*(1-u))*pitch/rate
            chirr=(.45+.55*math.sin(t*2*math.pi*34)**2)
            v=(.28*math.sin(phase+1.5*math.sin(phase*.51))+.62*(rand-smooth))*chirr
        elif kind=='ballast':
            phase+=2*math.pi*(62+100*math.exp(-t*28))*pitch/rate
            v=.6*math.sin(phase)+.15*math.sin(phase*2.07)+.4*smooth
            v+=.35*rand*math.exp(-t*25)
        else:
            phase+=2*math.pi*(380+600*u+75*math.sin(t*39))*pitch/rate
            v=.34*math.sin(phase+2*math.sin(t*49))+.55*smooth
            v*=.7+.3*math.sin(t*2*math.pi*19)
        out.append(round(max(-1,min(1,v*env*.8))*110)&255)
    # SWAR wave data: non-looping PCM8; length measured in four-byte words.
    return struct.pack('<BBHHHI',0,0,rate,round(16756991/rate),0,len(out)//4)+bytes(out)

def apply(raw):
    archive=sdat.Sdat.parse(raw)
    seq_id=archive.file_id(1,0);bank_id=archive.file_id(2,20);wave_id=archive.file_id(3,0)
    seq,bank,wave=(archive.blob(i) for i in (seq_id,bank_id,wave_id))
    if (w.u32(seq,0x1C),w.u32(bank,0x38),w.u32(wave,0x38))!=(FIRST,)*3:raise ValueError('Native sound IDs changed')
    waves=[];notes=[];sequences=[]
    for index,(kind,category) in enumerate((k,c) for k in KINDS for c in CATEGORIES):
        slot=FIRST+index;waves.append(voice(kind,category))
        # PCM note definition, unity key C4, immediate envelope, centered pan.
        notes.append(struct.pack('<HH6B',slot,0,60,127,127,127,127,64))
        sequences.append((RANGES[index][0],bytes((0x81,0x80|(slot>>7),slot&127,60,110,0,0xFF))))
    result=archive.replace({seq_id:sdat.append_sequences(seq,sequences),
        bank_id:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),
        wave_id:sdat.append_indexed(wave,b'SWAR',waves)})
    return result,{'first':FIRST,'count':15,'sample_rate':11025,'native_files_preserved':True,
                   'ranges':[list(x) for x in RANGES],'voices':[k+'_'+c for k in KINDS for c in CATEGORIES]}

def adapter(at):
    from tools.crane_boss import Arm
    from tools.crane_creatures import _scope
    a=Arm(at);a.emit(0xE92D500D,0xE10FC000);_scope(a,'done')
    for i,(lo,hi) in enumerate(RANGES):
        a.lit(2,'lo'+str(i),lo);a.emit(0xE1510002);a.b('next'+str(i),3)
        a.lit(2,'hi'+str(i),hi);a.emit(0xE1510002);a.b('next'+str(i),8)
        a.lit(1,'sound'+str(i),FIRST+i);a.b('done');a.label('next'+str(i))
    a.label('done');a.emit(0xE128F00C,0xE8BD500D,0xE92D40F0);a.b(SITE+4)
    return a.finish()

def spore_adapter(at,config):
    """The native ranged chassis lacks vocal cues on its attack/death states.

    Add one original cue on entry, guarded by controller type and exact private
    config. Use the same sound handle construction/destruction as native OBJ
    sounds; native ability/other-character controllers keep their original path.
    """
    from tools.crane_boss import Arm
    from tools.crane_creatures import _scope
    a=Arm(at);a.emit(0xE92D503F,0xE10F5000,0xE1A04000);_scope(a,'native')
    a.emit(0xE5942000);a.lit(3,'controller',0x02133368);a.emit(0xE1520003);a.b('native',1)
    a.emit(0xE5942048);a.lit(3,'config',config);a.emit(0xE1520003);a.b('native',1)
    for state,label in ((15,'attack'),(16,'attack'),(28,'hurt'),(29,'hurt'),(53,'death')):
        a.emit(0xE3510000|state);a.b(label,0)
    a.b('native')
    for label,sound in (('attack',588),('hurt',590),('death',589)):
        a.label(label);a.lit(4,'sound_'+label,sound);a.b('play')
    a.label('play');a.emit(0xE24DD010,0xE28D0004);a.b(0x0203D564,link=True)
    a.emit(0xE28D0004,0xE1A01004,0xE3A02014,0xE3A03000,0xE58D3000);a.b(SITE,link=True)
    a.emit(0xE28D0004);a.b(0x0203D580,link=True);a.emit(0xE28DD010)
    a.label('native');a.emit(0xE128F005,0xE8BD503F,0xE92D000F);a.b(STATE_SITE+4)
    return a.finish()
