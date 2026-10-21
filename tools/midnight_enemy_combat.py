"""Exact-owner sound routing for the revised creature choreography."""
from tools.chapter_renewal_combat import asm
SPATIAL_SITE=0x020746ac
SOUND_SITE=0x0203d5e4


def attack_gate(at,selected,walking):
    """Begin grounded programs only after a real landing; owned jumps continue."""
    return asm(f'''
        ldr r3,[r6,#0x10]
        tst r3,#0x80
        beq #0x{walking:x}
        ldr r3,[r4,#0x14]
        cmp r3,#3
        bhi #0x{walking:x}
        ldr r3,[r6,#0x1c]
        cmp r3,#0
        bne #0x{walking:x}
        cmp r0,r1
        b #0x{selected+4:x}
    ''',at)


def voice_bank(at,old,first):
    return asm(f'''
        push {{r2,r12,lr}}
        mrs r12,cpsr
        ldr r2,stats
        ldr r2,[r2]
        cmp r2,#0
        beq native
        ldr r2,[r2]
        cmp r2,#76
        blo native
        cmp r2,#108
        bhs native
        ldr r2,first_old
        cmp r1,r2
        blo native
        sub r2,r1,r2
        cmp r2,#57
        bhs native
        cmp r2,#35
        bhs remap
        cmp r5,#48
        cmpne r5,#49
        cmpne r5,#50
        bne remap
    category:
        cmp r2,#5
        subhs r2,r2,#5
        bhs category
        cmp r2,#3
        ldreq r1,silence
        beq native
        ldr r2,first_old
        sub r2,r1,r2
    remap:
        ldr r1,first_new
        add r1,r1,r2
    native:
        msr cpsr_f,r12
        pop {{r2,r12,lr}}
        b #0x{old:x}
    stats: .word 0x02145c5c
    first_old: .word 653
    first_new: .word {first}
    silence: .word 652
    ''',at)


def spatial(at,configs,play,first):
    """R7 owns the native spatial request at this specific actor callsite.

    Revised creatures already have complete attack/hurt/death cues. Suppress
    their queued stock vocal/swish events; locomotion gets its own short foley.
    Native player and every other owner retain the exact request and pointer.
    """
    return asm(f'''
        push {{r3-r6,lr}}
        sub sp,sp,#12
        str r0,[sp,#4]
        str r2,[sp,#8]
        mrs r6,cpsr
        ldr r3,stats
        ldr r3,[r3]
        cmp r3,#0
        beq native
        ldr r3,[r3]
        cmp r3,#76
        blo native
        cmp r3,#108
        bhs native
        ldr r3,lower
        cmp r7,r3
        blo native
        ldr r3,upper
        cmp r7,r3
        bhs native
        tst r7,#3
        bne native
        ldr r3,[r7]
        ldr r4,enemy
        cmp r3,r4
        bne native
        ldr r3,[r7,#0x40]
        ldr r4,configs
        mov r5,#0
    find:
        ldr r12,[r4,r5,lsl #2]
        cmp r3,r12
        beq owned
        add r5,r5,#1
        cmp r5,#7
        blo find
        b native
    owned:
        ldr r3,[r7,#0x30]
        ldr r4,lower
        cmp r3,r4
        blo native
        ldr r4,upper
        cmp r3,r4
        bhs native
        tst r3,#3
        bne native
        ldr r4,[r3]
        cmp r4,r7
        bne native
        ldr r3,[r3,#0x254]
        cmp r3,#158
        cmpne r3,#134
        cmpne r3,#20
        bne muted
        add r0,r5,r5,lsl #2
        ldr r3,first
        add r0,r0,r3
        add r0,r0,#4
        bl #0x{play:x}
    muted:
        ldr r0,[sp,#4]
        ldr r2,[sp,#8]
        ldr r3,silence
        str r3,[sp]
        mov r1,sp
        bl #0x0205e6a8
        b done
    native:
        msr cpsr_f,r6
        bl #0x0205e6a8
    done:
        msr cpsr_f,r6
        add sp,sp,#12
        pop {{r3-r6,pc}}
    stats: .word 0x02145c5c
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    enemy: .word 0x021301d0
    configs: .word 0x{configs:x}
    first: .word {first}
    silence: .word 652
    ''',at)
