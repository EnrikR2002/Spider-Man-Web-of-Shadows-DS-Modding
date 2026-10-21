"""Private enemy attack sequencers and reliable lifecycle voice cues.

Native navigation, damage, interruption, physics and death remain authoritative.
Only exact private chapter configurations enter these attack sequencers.
"""
import math,struct,sys
from pathlib import Path
from tools import wos_tool as w,sdat,crane_audio as audio
from tools.crane_boss import Arm

FIRST=617
THINK_SLOT=0x02133410
ENTER_SLOT=0x02133418
NATIVE_THINK=0x02095834
NATIVE_ENTER=0x02097D80
# (action, native execution state, recovery updates). Ordered combos change the
# actual attack selected, not only the model or the old random AI parameters.
PATTERNS={
 'maw':((55,15,12),(121,15,32),(63,15,65)),
 'ballast':((63,15,38),(55,15,10),(55,15,85)),
 'spore':((71,16,12),(71,16,85)),
 'skitter':((121,15,8),(63,15,12),(121,15,75)),
 'warden':((55,15,12),(63,15,55),(63,15,85)),
 'eye':((71,16,8),(71,16,8),(71,16,100)),
 'conductor':((63,15,20),(71,16,18),(55,15,10),(63,15,65)),
}

def asm(source,at):
    # Same optional assembler used by the existing Red kit build tooling.
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'work/research-libs'))
    from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
    return bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm(source,at)[0])

def loader():
    """SDK-compatible descending copies, preloading a row before overlap.

    The extension is the last autoload entry and has zero BSS. Read all three
    words before copying, so its source may overlap its destination/table.
    The original ITCM/DTCM entries and their BSS/cache handling remain intact.
    """
    return asm('''
        ldmia r1!, {r4,r5,r6}
        add r0,r4,r5
    copy:
        subs r5,r5,#4
        ldrpl r7,[r3,r5]
        strpl r7,[r4,r5]
        bpl copy
        sub r5,r0,r4
        add r3,r3,r5
        mov r5,r0
        add r6,r0,r6
        mov r7,#0
    zero:
        cmp r5,r6
        strlo r7,[r5],#4
        blo zero
        bic r4,r4,#31
    cache:
        mcr p15,0,r7,c7,c10,4
        mcr p15,0,r4,c7,c5,1
        mcr p15,0,r4,c7,c14,1
        add r4,r4,#32
        cmp r4,r6
        blt cache
        b #0x02000a0c
    ''',0x02000A14)

def capture_hero(at,hero):
    a=Arm(at);a.emit(0xE92D5007,0xE10FC000,0xE5901000)
    a.lit(2,'controller',0x021352A4);a.emit(0xE1510002);a.b('done',1)
    a.emit(0xE5901044);a.lit(2,'hero',hero);a.emit(0xE5821000)
    a.label('done');a.emit(0xE128F00C,0xE8BD5007,0xE92D4010);a.b(0x020776C0)
    return a.finish()

def think(at,records,slots,counters,hero=0):
    return asm(f'''
        push {{r4-r10,lr}}
        mov r4,r0
        bl #0x{NATIVE_THINK:x}
        mov r5,r0
        ldr r6,[r4,#0x44]
        cmp r6,#0
        beq done
        ldr r0,[r6]
        ldr r1,enemy
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x44]
        cmp r0,#0
        ble done
        ldr r0,[r6,#0x40]
        ldr r7,records
    config:
        ldr r1,[r7]
        cmp r1,#0
        beq done
        cmp r0,r1
        beq owned
        add r7,r7,#16
        b config
    owned:
        ldr r8,slots
        mov r9,#32
    find:
        ldr r0,[r8]
        cmp r0,r4
        beq slot
        cmp r0,#0
        beq fresh
        add r8,r8,#32
        subs r9,r9,#1
        bne find
        ldr r8,slots
    fresh:
        str r4,[r8]
        str r6,[r8,#4]
        mov r0,#0
        str r0,[r8,#12]
        mov r0,#25
        str r0,[r8,#16]
        mov r0,#0
        str r0,[r8,#20]
    slot:
        ldr r0,[r8,#8]
        ldr r1,[r7]
        cmp r0,r1
        strne r1,[r8,#8]
        movne r0,#0
        strne r0,[r8,#12]
        strne r0,[r8,#20]
        movne r0,#25
        strne r0,[r8,#16]
        ldr r0,[r4,#0x14]
        cmp r0,#6
        bhi done
        cmp r5,#26
        blo eligible
        cmp r5,#53
        bls done
    eligible:
        ldr r0,[r8,#16]
        cmp r0,#0
        subne r0,r0,#1
        strne r0,[r8,#16]
        bne suppress
        ldr r9,[r8,#12]
        ldr r10,[r7,#4]
        add r10,r10,r9,lsl #3
        add r10,r10,r9,lsl #2
        ldr r9,[r10]
        ldr r0,hero
        ldr r0,[r0]
        ldr r1,lower
        cmp r0,r1
        blo done
        ldr r1,upper
        cmp r0,r1
        bhs done
        ldr r1,[r0]
        ldr r2,player
        cmp r1,r2
        bne done
        mov r2,r0
        ldr r0,[r0,#0x30]
        ldr r1,lower
        cmp r0,r1
        blo done
        ldr r1,upper
        cmp r0,r1
        bhs done
        ldr r1,[r0]
        cmp r1,r2
        bne done
        ldr r1,[r6,#0x30]
        ldr r2,[r0,#0x7c]
        ldr r3,[r0,#0x160]
        add r2,r2,r3
        ldr r3,[r1,#0x7c]
        sub r2,r2,r3
        ldr r3,[r1,#0x160]
        subs r2,r2,r3
        rsbmi r2,r2,#0
        mov r3,#0xa000
        cmp r9,#121
        moveq r3,#0x1e000
        cmp r9,#71
        moveq r3,#0x48000
        cmp r2,r3
        bhi suppress
        ldr r2,[r0,#0x80]
        ldr r3,[r0,#0x164]
        add r2,r2,r3
        ldr r3,[r1,#0x80]
        sub r2,r2,r3
        ldr r3,[r1,#0x164]
        subs r2,r2,r3
        rsbmi r2,r2,#0
        mov r3,#0xc000
        cmp r9,#71
        moveq r3,#0x20000
        cmp r2,r3
        bhi suppress
        mov r0,r10
        ldr r1,[r0]
        str r1,[r8,#20]
        ldr r5,[r0,#4]
        ldr r1,[r0,#8]
        str r1,[r8,#16]
        ldr r9,[r8,#12]
        add r9,r9,#1
        ldr r1,[r7,#8]
        cmp r9,r1
        movhs r9,#0
        str r9,[r8,#12]
        ldr r0,[r7,#12]
        ldr r1,counters
        ldr r2,[r1,r0,lsl #2]
        add r2,r2,#1
        str r2,[r1,r0,lsl #2]
        b done
    suppress:
        cmp r5,#15
        cmpne r5,#16
        moveq r5,#0
    done:
        mov r0,r5
        pop {{r4-r10,pc}}
    enemy: .word 0x021301d0
    records: .word 0x{records:x}
    slots: .word 0x{slots:x}
    counters: .word 0x{counters:x}
    hero: .word 0x{hero:x}
    player: .word 0x0212e3f0
    lower: .word 0x02000000
    upper: .word 0x02400000
    ''',at)

def enter(at,records,slots,voice_counters):
    return asm(f'''
        push {{r4-r10,lr}}
        mov r4,r0
        ldr r5,[r2]
        bl #0x{NATIVE_ENTER:x}
        ldr r6,[r4,#0x44]
        cmp r6,#0
        beq done
        ldr r0,[r6,#0x40]
        ldr r7,records
    config:
        ldr r1,[r7]
        cmp r1,#0
        beq done
        cmp r0,r1
        beq owned
        add r7,r7,#16
        b config
    owned:
        cmp r5,#15
        cmpne r5,#16
        bne voice
        ldr r8,slots
        mov r9,#32
    find:
        ldr r0,[r8]
        cmp r0,r4
        beq action
        add r8,r8,#32
        subs r9,r9,#1
        bne find
        b voice
    action:
        ldr r0,[r8,#20]
        cmp r0,#0
        beq voice
        ldr r1,[r6,#0x30]
        str r0,[r1,#0x258]
        ldr r0,[r1,#0x2fc]
        orr r0,r0,#2
        str r0,[r1,#0x2fc]
    voice:
        mov r8,#1
        cmp r5,#15
        cmpne r5,#16
        beq play
        mov r8,#2
        cmp r5,#53
        beq play
        mov r8,#3
        cmp r5,#28
        cmpne r5,#29
        cmpne r5,#32
        cmpne r5,#33
        bne done
    play:
        ldr r0,[r7,#12]
        add r9,r0,r0,lsl #2
        add r9,r9,r8
        ldr r0,first
        add r9,r9,r0
        ldr r0,[r7,#12]
        ldr r1,counts
        ldr r2,[r1,r0,lsl #2]
        add r2,r2,#1
        str r2,[r1,r0,lsl #2]
        sub sp,sp,#16
        add r0,sp,#4
        bl #0x0203d564
        add r0,sp,#4
        mov r1,r9
        mov r2,#20
        mov r3,#0
        str r3,[sp]
        bl #0x{audio.SITE:x}
        add r0,sp,#4
        bl #0x0203d580
        add sp,sp,#16
    done:
        pop {{r4-r10,pc}}
    records: .word 0x{records:x}
    slots: .word 0x{slots:x}
    first: .word {FIRST}
    counts: .word 0x{voice_counters:x}
    ''',at)

def sound_filter(at,old):
    # All old creature vocal requests are muted in private chapter rooms;
    # exact actor state entry plays the new voice. Weapon/impact SFX survive.
    a=Arm(at);a.emit(0xE92D500D,0xE10FC000)
    a.lit(2,'stats',0x02145C5C);a.emit(0xE5922000,0xE3520000);a.b('native',0)
    a.emit(0xE5922000,0xE352004C);a.b('native',3);a.emit(0xE352006C);a.b('native',2)
    a.lit(2,'first_old',582);a.emit(0xE1510002);a.b('ranges',3)
    a.lit(2,'last_old',616);a.emit(0xE1510002);a.b('silent',9)
    a.label('ranges')
    for i,(lo,hi) in enumerate(((306,328),(457,501))):
        a.lit(2,'lo'+str(i),lo);a.emit(0xE1510002);a.b('next'+str(i),3)
        a.lit(2,'hi'+str(i),hi);a.emit(0xE1510002);a.b('silent',9);a.label('next'+str(i))
    a.b('native');a.label('silent');a.lit(1,'silence',652)
    a.label('native');a.emit(0xE128F00C,0xE8BD500D);a.b(old)
    return a.finish()

def voice(style,category):
    rate=11025;duration=(.4,.42,.85,.2,.32)[category];count=round(rate*duration);count+=-count%4
    samples=bytearray();seed=0x9163+style*157;phase=0
    for i in range(count):
        t=i/rate;u=i/max(1,count-1);seed=(1664525*seed+1013904223)&0xffffffff;noise=(seed>>16)/32767.5-1
        env=min(1,u*40)*(1-u)**(.7 if category==2 else 1.5)
        pitch=(.55 if category==2 else 1.2 if category==3 else 1)
        freq=(180,67,420,760,140,940,88)[style]*pitch
        phase+=2*math.pi*freq*(1-.45*u if category==2 else 1+.12*math.sin(t*24))/rate
        if style==0:value=.55*noise*math.exp(-((t*28)%1)*3)+.3*math.sin(phase)
        elif style==1:value=.45*math.sin(phase)+.35*math.sin(phase*2.67)*math.exp(-t*8)+.3*noise*math.exp(-t*22)
        elif style==2:value=.6*math.sin(phase+2.5*math.sin(t*56))*(.5+.5*math.sin(t*65)**2)+.12*noise
        elif style==3:value=(.45*math.sin(phase)+.25*math.sin(phase*1.91))*(.25+.75*math.sin(t*92)**6)+.2*noise
        elif style==4:value=.45*math.sin(phase)+.3*math.sin(phase*2.76)*math.exp(-t*6)+.2*math.sin(phase*4.07)*math.exp(-t*10)
        elif style==5:value=.55*math.sin(phase+4*math.sin(t*38))*(.3+.7*math.sin(t*29)**2)+.15*noise
        else:value=.4*math.sin(phase)+.25*math.sin(phase*1.5)+.3*noise*math.exp(-t*12)
        samples.append(round(max(-1,min(1,value*env))*118)&255)
    return struct.pack('<BBHHHI',0,0,rate,round(16756991/rate),0,len(samples)//4)+samples

def sound_data(raw):
    a=sdat.Sdat.parse(raw);ids=(a.file_id(1,0),a.file_id(2,20),a.file_id(3,0));seq,bank,wave=(a.blob(i) for i in ids)
    if (w.u32(seq,0x1c),w.u32(bank,0x38),w.u32(wave,0x38))!=(FIRST,)*3:raise ValueError('Expected0.20 audio')
    waves=[voice(i,c) for i in range(7) for c in range(5)];waves.append(struct.pack('<BBHHHI',0,0,11025,1520,0,4)+bytes(16))
    notes=[struct.pack('<HH6B',FIRST+i,0,60,127,127,127,127,64) for i in range(len(waves))]
    seqs=[(306,bytes((0x81,0x80|((FIRST+i)>>7),(FIRST+i)&127,60,120,0,0xff))) for i in range(len(waves))]
    return a.replace({ids[0]:sdat.append_sequences(seq,seqs),ids[1]:sdat.append_indexed(bank,b'SBNK',notes,instrument=True),ids[2]:sdat.append_indexed(wave,b'SWAR',waves)})
