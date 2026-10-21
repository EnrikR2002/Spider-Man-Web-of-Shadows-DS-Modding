"""Exact-config ARM attack programs, animation-clock movement and impact cues.

Native collision, gravity, interruptions, damage, death and rewards remain.
Attack handlers select private resources; movement is authored here rather than
inherited from a base enemy attack. No player state/position/HP writes exist.
"""
from tools.chapter_renewal_combat import asm
THINK_SLOT=0x02133410;ENTER_SLOT=0x02133418;UPDATE_SLOT=0x0213341c
SECOND_SLOT=0x02133414

def think(at,records,slots,counts,hero,room,moves,play=0,first=653,*,rewrite=None):
    source=f'''
        push {{r4-r11,lr}}
        sub sp,sp,#4
        mov r4,r0
        bl #0x02095834
        mov r5,r0
        ldr r6,[r4,#0x44]
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
        ldr r0,stats
        ldr r0,[r0]
        ldr r0,[r0]
        ldr r1,room
        ldr r2,[r1]
        cmp r0,r2
        beq findslot
        str r0,[r1]
        ldr r1,slots
        mov r2,#32
        mov r0,#0
    clear:
        str r0,[r1],#32
        subs r2,r2,#1
        bne clear
    findslot:
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
        ldr r0,[r7]
        str r0,[r8,#8]
        mov r0,#0
        str r0,[r8,#12]
        str r0,[r8,#20]
        str r0,[r8,#28]
        mov r0,#10
        str r0,[r8,#16]
        ldr r0,[r7,#12]
        add r0,r0,r0,lsl #2
        ldr r1,first_sound
        add r0,r0,r1
        bl #0x{play:x}
    slot:
        ldr r0,[r8,#8]
        ldr r1,[r7]
        cmp r0,r1
        bne fresh
        ldr r11,[r6,#0x30]
        ldr r0,[r11]
        cmp r0,r6
        bne done
        ldr r9,[r4,#0x14]
        @ Freight's narrow recovery ledges admit the small Spore beneath them,
        @ while the player's wider capsule cannot drop through the same slit.
        @ Walk to the clear edge, then make one real recovery vault onto deck.
        ldr r0,[r7,#12]
        cmp r0,#2
        bne recovery_done
        ldr r0,room
        ldr r0,[r0]
        cmp r0,#97
        bne recovery_done
        cmp r9,#15
        beq recovery_state
        cmp r9,#6
        bhi recovery_done
    recovery_state:
        cmp r5,#26
        blo recovery_position
        cmp r5,#53
        bls recovery_done
    recovery_position:
        ldr r12,[r11,#0x7c]
        ldr r0,[r11,#0x160]
        add r12,r12,r0
        ldr r3,[r11,#0x80]
        ldr r0,[r11,#0x164]
        add r3,r3,r0
        ldr r0,pit1_left
        cmp r12,r0
        blt recovery_done
        ldr r10,pit1_clear
        cmp r12,r10
        ldrlt r2,pit1_hop
        blt recovery_zone
        ldr r0,pit2_left
        cmp r12,r0
        blt recovery_done
        ldr r10,pit2_clear
        cmp r12,r10
        bge recovery_done
        ldr r2,pit2_hop
    recovery_zone:
        ldr r0,[r8,#16]
        mvn r1,#1
        cmp r0,r1
        beq recovery_flying
        cmn r3,#0xa000
        bge recovery_done
        mov r0,#0
        str r0,[r8,#20]
        mov r0,#1
        str r0,[r8,#24]
        mov r0,#0xc00
        str r0,[r8,#28]
        cmp r12,r2
        movlt r5,#1
        blt done
        mov r0,r6
        bl #0x020739b4
        ldr r0,recovery_vy
        str r0,[r6,#0x1c]
        mvn r0,#1
        str r0,[r8,#16]
        ldr r0,recovery_voice
        bl #0x{play:x}
        mov r5,#5
        b done
    recovery_flying:
        mov r0,#0
        str r0,[r8,#20]
        mov r0,#1
        str r0,[r8,#24]
        mov r0,#0xc00
        str r0,[r8,#28]
        @ A ceiling contact can cancel a hop. Retry after a full landing,
        @ rather than refreshing upward velocity every frame.
        ldr r0,[r6,#0x1c]
        cmp r0,#0
        bne recovery_air
        cmn r3,#0xa000
        bge recovery_air
        ldr r0,[r4,#8]
        cmp r0,#30
        movgt r0,#10
        strgt r0,[r8,#16]
    recovery_air:
        mov r5,#5
        b done
    recovery_done:
        ldr r0,[r8,#16]
        mvn r1,#1
        cmp r0,r1
        moveq r0,#18
        streq r0,[r8,#16]
        cmp r9,#15
        beq active
        cmp r9,#6
        bhi interrupted
        ldr r10,[r8,#20]
        cmp r10,#0
        beq available
        ldr r0,[r10,#8]
        str r0,[r8,#16]
        mov r0,#0
        str r0,[r8,#20]
    available:
        ldr r0,no_steer
        str r0,[r8,#28]
        cmp r5,#26
        blo distance
        cmp r5,#53
        bls done
    distance:
        ldr r0,hero
        ldr r0,[r0]
        ldr r1,lower
        cmp r0,r1
        blo suppress
        ldr r1,upper
        cmp r0,r1
        bhs suppress
        ldr r1,[r0]
        ldr r2,player
        cmp r1,r2
        bne suppress
        mov r2,r0
        ldr r0,[r0,#0x30]
        ldr r1,lower
        cmp r0,r1
        blo suppress
        ldr r1,upper
        cmp r0,r1
        bhs suppress
        ldr r1,[r0]
        cmp r1,r2
        bne suppress
        ldr r2,[r0,#0x7c]
        ldr r3,[r0,#0x160]
        add r2,r2,r3
        ldr r3,[r11,#0x7c]
        sub r2,r2,r3
        ldr r3,[r11,#0x160]
        subs r2,r2,r3
        movge r9,#1
        movlt r9,#0
        rsblt r2,r2,#0
        ldr r3,[r0,#0x80]
        ldr r1,[r0,#0x164]
        add r3,r3,r1
        ldr r1,[r11,#0x80]
        sub r3,r3,r1
        ldr r1,[r11,#0x164]
        subs r3,r3,r1
        mov r12,r3
        rsbmi r3,r3,#0
        mov r1,#0xc000
        ldr r0,[r7,#12]
        cmp r0,#2
        cmpne r0,#5
        moveq r1,#0x14000
        cmp r3,r1
        bhi vertical
        str r9,[r8,#24]
        ldr r0,[r8,#16]
        cmp r0,#0
        movlt r0,#0
        cmp r0,#0
        subne r0,r0,#1
        strne r0,[r8,#16]
        bne spacing
        ldr r0,[r8,#12]
        ldr r1,[r7,#8]
        ldr r3,[r7,#12]
        cmp r3,#6
        bne count_ready
        ldr r3,[r6,#0x44]
        ldr r12,[r6,#0x48]
        cmp r3,r12,asr #1
        movgt r1,#3
    count_ready:
        cmp r0,r1
        movhs r0,#0
        ldr r10,[r7,#4]
        add r10,r10,r0,lsl #5
        ldr r1,[r10,#28]
        cmp r2,r1
        bhi walking
        add r0,r0,#1
        str r0,[r8,#12]
        str r10,[r8,#20]
        str r9,[r8,#24]
        mvn r0,#0
        str r0,[r8,#28]
        ldr r0,[r7,#12]
        ldr r1,counts
        ldr r2,[r1,r0,lsl #2]
        add r2,r2,#1
        str r2,[r1,r0,lsl #2]
        ldr r0,[r10,#24]
        ldr r1,moves
        ldr r2,[r1,r0,lsl #2]
        add r2,r2,#1
        str r2,[r1,r0,lsl #2]
        mov r5,#15
        mov r0,#1
        strb r0,[r4,#4]
        b done
    active:
        ldr r10,[r8,#20]
        cmp r10,#0
        beq suppress
        cmp r5,#26
        blo holding
        cmp r5,#53
        bls interrupted
    holding:
        ldr r0,[r11,#0x254]
        ldr r1,[r10]
        cmp r0,r1
        bne hold
        ldr r0,[r11,#0x178]
        ldr r1,[r10,#4]
        cmp r0,r1
        blo hold
        mov r5,#0
        ldr r0,[r10,#8]
        str r0,[r8,#16]
        mov r0,#0
        str r0,[r8,#20]
        str r0,[r8,#28]
        b done
    hold:
        mov r5,#15
        b done
    interrupted:
        mov r0,#0
        str r0,[r8,#20]
        mov r0,#18
        str r0,[r8,#16]
        b done
    vertical:
        cmp r12,#0
        bge suppress
        @ A target below a catwalk needs an actual walk off the edge. The base
        @ ranger otherwise retreats into a wall forever above the player.
        ldr r0,[r8,#16]
        cmp r0,#0
        ldrlt r9,[r8,#24]
        blt walking
        mvn r0,#0
        str r0,[r8,#16]
        ldr r0,[r11,#0x7c]
        ldr r1,[r11,#0x160]
        add r0,r0,r1
        cmp r0,#0x40000
        movlt r9,#1
        movge r9,#0
        b walking
    spacing:
        mov r0,#0
        str r0,[r8,#28]
        ldr r0,[r7,#12]
        cmp r0,#2
        cmpne r0,#5
        beq ranged_space
        cmp r2,#0xa000
        bhi walking
        mov r5,#0
        b done
    ranged_space:
        cmp r2,#0x19000
        bhi walking
        cmp r2,#0xc000
        eorlo r9,r9,#1
        blo walking
        mov r5,#0
        b done
    walking:
        ldr r0,[r7,#12]
        mov r1,#0xa00
        cmp r0,#3
        moveq r1,#0xe00
        cmp r0,#1
        cmpne r0,#4
        cmpne r0,#6
        moveq r1,#0x680
        cmp r9,#0
        rsbeq r1,r1,#0
        str r1,[r8,#28]
        str r9,[r8,#24]
        mov r5,#1
        b done
    suppress:
        cmp r5,#15
        cmpne r5,#16
        moveq r5,#0
    done:
        mov r0,r5
        add sp,sp,#4
        pop {{r4-r11,pc}}
    enemy: .word 0x021301d0
    player: .word 0x0212e3f0
    stats: .word 0x02145c5c
    lower: .word 0x02000000
    upper: .word 0x02400000
    records: .word 0x{records:x}
    slots: .word 0x{slots:x}
    counts: .word 0x{counts:x}
    moves: .word 0x{moves:x}
    room: .word 0x{room:x}
    hero: .word 0x{hero:x}
    no_steer: .word 0x7fffffff
    first_sound: .word {first}
    pit1_left: .word 237568
    pit1_hop: .word 356352
    pit1_clear: .word 385024
    pit2_left: .word 1245184
    pit2_hop: .word 1396736
    pit2_clear: .word 1425408
    recovery_vy: .word 14746
    recovery_voice: .word {first+11}
    '''
    return asm(rewrite(source) if rewrite else source,at)

def enter(at,records,slots,voices,first,play):
    return asm(f'''
        push {{r4-r10,lr}}
        mov r4,r0
        ldr r5,[r2]
        bl #0x02097d80
        ldr r6,[r4,#0x44]
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
        ldr r0,[r0]
        ldr r1,[r6,#0x30]
        str r0,[r1,#0x258]
        ldr r0,[r1,#0x2fc]
        orr r0,r0,#2
        str r0,[r1,#0x2fc]
        mvn r0,#0
        str r0,[r8,#28]
    voice:
        mov r8,#1
        cmp r5,#15
        beq sound
        mov r8,#2
        cmp r5,#53
        beq sound
        mov r8,#3
        cmp r5,#26
        blo done
        cmp r5,#50
        bhi done
    sound:
        ldr r0,[r7,#12]
        ldr r1,voices
        ldr r2,[r1,r0,lsl #2]
        add r2,r2,#1
        str r2,[r1,r0,lsl #2]
        add r0,r0,r0,lsl #2
        add r0,r0,r8
        ldr r1,first
        add r0,r0,r1
        bl #0x{play:x}
    done:
        pop {{r4-r10,pc}}
    records: .word 0x{records:x}
    slots: .word 0x{slots:x}
    voices: .word 0x{voices:x}
    first: .word {first}
    ''',at)

def secondary(at,slots):
    """Keep an authored airborne strike through the native fall/land pass.

    The engine has two state-decision passes. Its secondary fall selector ran
    after the custom impulse, replacing the clip before its first contact.
    Native hurt/death decisions remain eligible and clear the program normally.
    """
    return asm(f'''
        push {{r4-r8,lr}}
        mov r4,r0
        bl #0x02095a78
        mov r5,r0
        ldr r0,[r4,#0x14]
        cmp r0,#15
        bne done
        ldr r6,slots
        mov r7,#32
    find:
        ldr r0,[r6]
        cmp r0,r4
        beq found
        add r6,r6,#32
        subs r7,r7,#1
        bne find
        b done
    found:
        ldr r7,[r4,#0x44]
        ldr r0,[r6,#4]
        cmp r0,r7
        bne done
        ldr r0,[r6,#8]
        ldr r1,[r7,#0x40]
        cmp r0,r1
        bne done
        ldr r0,[r7,#0x44]
        cmp r0,#0
        ble done
        ldr r0,[r6,#20]
        cmp r0,#0
        beq done
        cmp r5,#25
        ldrls r5,keep
    done:
        mov r0,r5
        pop {{r4-r8,pc}}
    keep: .word 0x7fffffff
    slots: .word 0x{slots:x}
    ''',at)

def play(at):
    return asm('''
        push {r4,lr}
        sub sp,sp,#16
        mov r4,r0
        add r0,sp,#4
        bl #0x0203d564
        add r0,sp,#4
        mov r1,r4
        mov r2,#20
        mov r3,#0
        str r3,[sp]
        bl #0x0203d5e4
        add r0,sp,#4
        bl #0x0203d580
        add sp,sp,#16
        pop {r4,pc}
    ''',at)

def update(at,slots,play,cues,moves=0):
    return asm(f'''
        push {{r4-r11,lr}}
        sub sp,sp,#4
        mov r4,r0
        bl #0x02097e74
        ldr r0,[r4,#0x14]
        cmp r0,#15
        beq findslot
        cmp r0,#6
        bhi done
    findslot:
        ldr r5,slots
        mov r0,#32
    find:
        ldr r1,[r5]
        cmp r1,r4
        beq found
        add r5,r5,#32
        subs r0,r0,#1
        bne find
        b done
    found:
        ldr r6,[r4,#0x44]
        ldr r0,[r5,#4]
        cmp r0,r6
        bne done
        ldr r0,[r5,#8]
        ldr r1,[r6,#0x40]
        cmp r0,r1
        bne done
        ldr r7,[r5,#20]
        cmp r7,#0
        beq ground
        ldr r8,[r6,#0x30]
        ldr r0,[r8,#0x254]
        ldr r1,[r7]
        cmp r0,r1
        bne done
        ldr r9,[r8,#0x178]
        ldr r10,[r5,#28]
        ldr r11,[r5,#24]
        str r11,[r8,#0x180]
        ldr r0,[r7,#12]
        mov r3,#0
    drives:
        ldmia r0!,{{r1,r2,r12}}
        cmp r9,r1
        blt setdrive
        cmp r9,r2
        movlt r3,r12
        blt setdrive
        b drives
    setdrive:
        cmp r11,#0
        rsbeq r3,r3,#0
        str r3,[r6,#0x18]
        ldr r0,[r7,#16]
    jumps:
        ldmia r0!,{{r1,r2}}
        cmp r9,r1
        blt sounds
        cmp r10,r1
        bge jumps
        push {{r0,r2}}
        mov r0,r6
        bl #0x020739b4
        pop {{r0,r2}}
        str r2,[r6,#0x1c]
        b jumps
    sounds:
        ldr r11,[r7,#20]
    cue:
        ldmia r11!,{{r0,r1}}
        cmp r9,r0
        blt finished
        cmp r10,r0
        bge cue
        mov r0,r1
        bl #0x{play:x}
        ldr r0,cues
        ldr r1,[r0]
        add r1,r1,#1
        str r1,[r0]
        ldr r0,moves
        ldr r1,[r7,#24]
        ldr r2,[r0,r1,lsl #2]
        add r2,r2,#0x10000
        str r2,[r0,r1,lsl #2]
        b cue
    finished:
        str r9,[r5,#28]
        b done
    ground:
        ldr r0,[r4,#0x14]
        cmp r0,#6
        bhi done
        ldr r3,[r5,#28]
        ldr r0,no_steer
        cmp r3,r0
        beq done
        ldr r8,[r6,#0x30]
        ldr r0,[r5,#24]
        str r0,[r8,#0x180]
        str r3,[r6,#0x18]
    done:
        add sp,sp,#4
        pop {{r4-r11,pc}}
    slots: .word 0x{slots:x}
    cues: .word 0x{cues:x}
    no_steer: .word 0x7fffffff
    moves: .word 0x{moves:x}
    ''',at)

def sound_filter(at,old,silence):
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
        ldr r2,first
        cmp r1,r2
        blo native
        ldr r2,last
        cmp r1,r2
        ldrls r1,silence
    native:
        msr cpsr_f,r12
        pop {{r2,r12,lr}}
        b #0x{old:x}
    stats: .word 0x02145c5c
    first: .word 617
    last: .word 651
    silence: .word {silence}
    ''',at)
