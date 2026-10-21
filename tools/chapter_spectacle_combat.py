"""Opt-in authored enemy decisions and native-physics obstacle pursuit for0.23.

The immutable Forge template remains the default. This transform runs only for
the new post-pass and retains its pointer/config, ABI and interruption guards.
"""
from tools import creature_forge_combat as forge
from tools.chapter_renewal_combat import asm
HEAVY_APPROACH=16
SOUND_EVENT_SITE=0x0203A894


def sound_event(at,first,count,play):
    """Play only our appended OBJ-event cues inside the private chapters.

    Opcode22 has two582-ID guards before the existing sound adapters. Use
    Forge's complete native sound-handle player only for the nine new cues;
    every other event executes the original handler/prologue byte for byte.
    """
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        ldr r3,stats
        ldr r3,[r3]
        cmp r3,#0
        beq native
        ldr r3,[r3]
        cmp r3,#76
        blo native
        cmp r3,#108
        bhs native
        ldr r4,[r0,#12]
        ldrh r4,[r4]
        ldr r3,first
        cmp r4,r3
        blo native
        ldr r3,total
        cmp r4,r3
        bhs native
        mov r0,r4
        bl #0x{play:x}
        msr cpsr_f,r5
        pop {{r0-r5,r12,pc}}
    native:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        push {{r3,r4,lr}}
        b #0x{SOUND_EVENT_SITE+4:x}
    first: .word {first}
    total: .word {first+count}
    stats: .word 0x02145c5c
    ''',at)


def replace_once(source, old, new):
    if source.count(old)!=1:raise ValueError('Forge template contract changed: '+old[:60])
    return source.replace(old,new,1)


def enhance(source, navigation):
    # Keep all old guards and resources; this is a decision/pursuit revision.
    source=replace_once(source,'    distance:\n        ldr r0,hero','''    distance:
        ldr r0,stats
        ldr r0,[r0]
        ldr r1,[r0]
        cmp r1,#106
        bne still_fighting
        ldrb r0,[r0,#0x2d]
        tst r0,#0x40
        beq still_fighting
        mov r9,#0
        b walking
    still_fighting:
        ldr r0,hero''')
    source=replace_once(source,'''        cmp r9,#15
        beq active
        cmp r9,#6''','''        ldr r0,[r7,#12]
        cmp r0,#0
        cmpne r0,#3
        bne prep_checked
        cmp r5,#28
        moveq r5,#0
        cmp r9,#28
        bne prep_checked
        ldr r0,[r11,#0x254]
        cmp r0,#122
        moveq r9,#0
        moveq r5,#0
    prep_checked:
        cmp r9,#15
        beq active
        cmp r9,#6''')
    source=replace_once(source,'''        mov r1,#0xc000
        ldr r0,[r7,#12]
        cmp r0,#2
        cmpne r0,#5
        moveq r1,#0x14000''','''        ldr r0,[r8,#16]
        cmn r0,#4
        beq pursuit_rise
        cmn r0,#5
        beq pursuit_escape
        mov r1,#0x9000
        ldr r0,[r7,#12]
        cmp r0,#2
        cmpne r0,#5
        moveq r1,#0x6000
        cmp r0,#6
        moveq r1,#0xc000''')
    source=replace_once(source,'    count_ready:\n        cmp r0,r1', f'''    count_ready:
        ldr r3,[r7,#12]
        cmp r3,#6
        bne select_species
        ldr r3,manager
        ldr r3,[r3]
        cmp r3,#0
        beq select_ready
        ldrb r3,[r3,#0x1c7]
        cmp r3,#0
        beq select_ready
        mov r5,#0
        mov r3,#0
        str r3,[r8,#28]
        b done
    select_species:
        cmp r3,#2
        cmpne r3,#5
        beq select_ranged
        cmp r3,#1
        cmpne r3,#4
        beq select_heavy
        cmp r2,#0x12000
        bls select_ready
        cmp r3,#3
        moveq r0,#2
        movne r0,#1
        b select_ready
    select_heavy:
        cmp r2,#{HEAVY_APPROACH*4096:#x}
        movhi r0,#2
        bhi select_ready
        cmp r0,#2
        moveq r0,#0
        b select_ready
    select_ranged:
        cmp r2,#0xb000
        movlo r0,#1
        blo select_ready
        cmp r0,#1
        moveq r0,#2
    select_ready:
        cmp r0,r1''')
    # Coordinate Conductor's movement program and room-lane choreography.
    source=replace_once(source,'    slot:\n        ldr r0,[r8,#8]', '''    slot:
        ldr r0,[r7,#12]
        cmp r0,#6
        bne pressure_done
        ldr r0,manager
        ldr r0,[r0]
        cmp r0,#0
        beq pressure_done
        ldr r1,[r8,#20]
        cmp r1,#0
        movne r1,#1
        strb r1,[r0,#0x1c6]
    pressure_done:
        ldr r0,[r8,#8]''')
    source=replace_once(source,'    vertical:\n        cmp r12,#0\n        bge suppress', '''    vertical:
        cmp r12,#0
        bge pursuit_above''')
    # Above-target pursuit is physical hopping, never changing coordinates.
    source=replace_once(source,'    walking:\n        ldr r0,[r7,#12]', f'''    pursuit_above:
        cmp r12,#0x50000
        bgt suppress
        cmp r2,#0x24000
        bhi walking
        ldr r0,stats
        ldr r0,[r0]
        ldr r0,[r0]
        cmp r0,#78
        bne pursuit_jump
        ldr r0,[r11,#0x80]
        ldr r1,[r11,#0x164]
        add r0,r0,r1
        cmp r0,#0x14000
        bge pursuit_jump
        ldr r0,[r11,#0x7c]
        ldr r1,[r11,#0x160]
        add r0,r0,r1
        cmp r0,#0x71000
        ldrlo r3,roof_left
        blo roof_position
        cmp r0,#0x95000
        ldrlo r3,roof_gap1
        blo roof_position
        cmp r0,#0xb9000
        ldrlo r3,roof_gap1
        blo roof_position
        cmp r0,#0xdd000
        ldrlo r3,roof_gap2
        blo roof_position
        cmp r0,#0x100000
        ldrlo r3,roof_gap2
        ldrhs r3,roof_right
    roof_position:
        subs r1,r3,r0
        rsbmi r2,r1,#0
        movpl r2,r1
        cmp r2,#0x1800
        bls pursuit_jump
        cmp r1,#0
        movgt r9,#1
        movle r9,#0
        mvn r0,#4
        str r0,[r8,#16]
        b walking
    pursuit_escape:
        cmp r12,#0x9000
        bgt escape_continue
        mov r0,#12
        str r0,[r8,#16]
        b spacing
    escape_continue:
        ldr r0,[r11,#0x7c]
        ldr r1,[r11,#0x160]
        add r0,r0,r1
        ldr r1,roof_left
        subs r2,r0,r1
        rsbmi r2,r2,#0
        cmp r2,#0x1800
        bls pursuit_jump
        ldr r1,roof_gap1
        subs r2,r0,r1
        rsbmi r2,r2,#0
        cmp r2,#0x1800
        bls pursuit_jump
        ldr r1,roof_gap2
        subs r2,r0,r1
        rsbmi r2,r2,#0
        cmp r2,#0x1800
        bls pursuit_jump
        ldr r1,roof_right
        subs r2,r0,r1
        rsbmi r2,r2,#0
        cmp r2,#0x1800
        bls pursuit_jump
        ldr r9,[r8,#24]
        b walking
    pursuit_jump:
        ldr r0,[r4,#0x14]
        cmp r0,#4
        bhs walking
        ldr r0,[r6,#0x1c]
        cmp r0,#0
        bne walking
        mov r0,r6
        bl #0x020739b4
        ldr r0,pursuit_vy
        str r0,[r6,#0x1c]
        mov r5,#5
        ldr r0,stats
        ldr r0,[r0]
        ldr r0,[r0]
        cmp r0,#78
        bne walking
        mvn r0,#3
        str r0,[r8,#16]
        mov r0,#0
        str r0,[r8,#28]
        mov r5,#5
        b done
    pursuit_rise:
        ldr r0,[r11,#0x80]
        ldr r1,[r11,#0x164]
        add r0,r0,r1
        cmp r0,#0x1e000
        bge rise_done
        ldr r0,[r6,#0x1c]
        cmp r0,#0
        ble rise_done
        mov r0,#0
        str r0,[r8,#28]
        mov r5,#5
        b done
    rise_done:
        mov r0,#12
        str r0,[r8,#16]
        b walking
    walking:
        ldr r10,navigation
        ldr r0,slots
        sub r0,r8,r0
        add r10,r10,r0,lsr #2
        ldr r0,[r11,#0x7c]
        ldr r1,[r11,#0x160]
        add r0,r0,r1
        ldr r1,[r10]
        str r0,[r10]
        subs r0,r0,r1
        rsbmi r0,r0,#0
        cmp r0,#96
        ldr r1,[r10,#4]
        movhi r1,#0
        addls r1,r1,#1
        str r1,[r10,#4]
        cmp r1,#18
        blo pursuit_walk
        ldr r0,[r4,#0x14]
        cmp r0,#4
        bhs pursuit_walk
        ldr r0,[r6,#0x1c]
        cmp r0,#0
        bne pursuit_walk
        mov r0,#0
        str r0,[r10,#4]
        mov r0,r6
        bl #0x020739b4
        ldr r0,obstacle_vy
        str r0,[r6,#0x1c]
        mov r5,#5
    pursuit_walk:
        ldr r0,[r7,#12]''')
    source=replace_once(source,'''        str r9,[r8,#24]
        mov r5,#1
        b done
    suppress:''', '''        str r9,[r8,#24]
        cmp r5,#5
        cmpne r5,#7
        movne r5,#1
        b done
    suppress:''')
    source=replace_once(source,'    enemy: .word 0x021301d0',f'''    navigation: .word 0x{navigation:x}
    pursuit_vy: .word 16384
    obstacle_vy: .word 18842
    roof_left: .word 311296
    roof_gap1: .word 610304
    roof_gap2: .word 905216
    roof_right: .word 1204224
    manager: .word 0x02145c34
    enemy: .word 0x021301d0''')
    return source


def think(at,runtime,navigation,room,play):
    return forge.think(at,runtime['records'],runtime['slots'],runtime['attack_counters'],
                       runtime['hero'],room,runtime['move_counters'],play,653,
                       rewrite=lambda source:enhance(source,navigation))


def secondary(at,slots,leapers):
    """Keep navigation; native Leaper28 is LeapAttackPrep, not hurt."""
    return asm(f'''
        push {{r4-r8,lr}}
        mov r4,r0
        bl #0x02095a78
        mov r5,r0
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
        ldr r8,[r7,#0x40]
        ldr r0,[r6,#8]
        cmp r8,r0
        bne done
        ldr r0,[r7,#0x44]
        cmp r0,#0
        ble done
        cmp r5,#28
        bne program
        ldr r0,maw
        cmp r8,r0
        ldrne r0,skitter
        cmpne r8,r0
        ldreq r5,keep
        beq done
    program:
        cmp r5,#25
        bhi done
        ldr r0,[r6,#20]
        cmp r0,#0
        ldrne r5,keep
        bne done
        ldr r0,[r6,#16]
        cmn r0,#4
        cmnne r0,#5
        ldreq r5,keep
    done:
        mov r0,r5
        pop {{r4-r8,pc}}
    keep: .word 0x7fffffff
    slots: .word 0x{slots:x}
    maw: .word 0x{leapers[0]:x}
    skitter: .word 0x{leapers[1]:x}
    ''',at)


def variant(at,table,state,old):
    return asm(f'''
        push {{r2-r5,r12,lr}}
        mrs r12,cpsr
        ldr r2,stats
        ldr r2,[r2]
        cmp r2,#0
        beq fallback
        ldr r3,[r2]
        ldr r2,table
    find:
        ldr r4,[r2]
        cmp r4,#0
        beq fallback
        cmp r4,r3
        beq found
        add r2,r2,#12
        b find
    found:
        ldr r4,state
        ldr r5,[r4]
        cmp r5,r3
        strne r3,[r4]
        movne r5,#0
        ldreq r5,[r4,#4]
        ldr r3,[r2,#8]
        cmp r5,r3
        movhs r5,#0
        ldr r2,[r2,#4]
        ldrb r2,[r2,r5]
        add r5,r5,#1
        str r5,[r4,#4]
        str r2,[r0]
        msr cpsr_f,r12
        pop {{r2-r5,r12,pc}}
    fallback:
        msr cpsr_f,r12
        pop {{r2-r5,r12,lr}}
        b #0x{old:x}
    stats: .word 0x02145c5c
    table: .word 0x{table:x}
    state: .word 0x{state:x}
    ''',at)


def goals(at,table,old):
    return asm(f'''
        push {{r4-r6,lr}}
        mov r4,r0
        mov r5,r1
        bl #0x{old:x}
        push {{r0-r3,r12,lr}}
        mrs r12,cpsr
        ldr r2,stats
        ldr r2,[r2]
        cmp r2,#0
        beq done
        ldr r3,[r2]
        ldr r6,table
    find:
        ldr r0,[r6]
        cmp r0,#0
        beq done
        cmp r0,r3
        beq found
        add r6,r6,#20
        b find
    found:
        cmp r5,#14
        ldreq r2,[r6,#8]
        beq store
        ldr r1,[r6,#16]
        cmp r1,#0
        beq ordinary
        mov r0,r1,lsr #3
        add r0,r0,r2
        ldrb r0,[r0,#0x1c]
        and r1,r1,#7
        mov r3,#1
        tst r0,r3,lsl r1
        ldrne r2,[r6,#12]
        bne store
    ordinary:
        ldr r2,[r6,#4]
    store:
        str r2,[r4]
    done:
        msr cpsr_f,r12
        pop {{r0-r3,r12,lr}}
        pop {{r4-r6,pc}}
    stats: .word 0x02145c5c
    table: .word 0x{table:x}
    ''',at)


def world_data(at,table,old):
    return asm(f'''
        push {{r1-r5,r12,lr}}
        mrs r12,cpsr
        ldr r2,stats
        ldr r2,[r2]
        cmp r2,#0
        beq fallback
        ldr r3,[r2]
        ldr r4,table
    find:
        ldr r5,[r4]
        cmp r5,#0
        beq fallback
        cmp r5,r3
        bne next
        ldr r5,[r4,#4]
        cmp r5,r1
        beq found
    next:
        add r4,r4,#20
        b find
    found:
        ldr r1,[r4,#8]
        ldr r5,flag_limit
        cmp r1,r5
        bhs scalar
        mov r3,r1,lsr #3
        add r3,r3,r2
        ldrb r3,[r3,#0x1c]
        and r1,r1,#7
        mov r2,#1
        tst r3,r2,lsl r1
        b selected
    scalar:
        ldr r2,manager
        ldr r2,[r2]
        cmp r2,#0
        beq fallback
        add r1,r1,#0x99
        ldrb r3,[r2,r1]
        cmp r3,#0
    selected:
        ldreq r2,[r4,#12]
        ldrne r2,[r4,#16]
        str r2,[r0]
        msr cpsr_f,r12
        pop {{r1-r5,r12,pc}}
    fallback:
        msr cpsr_f,r12
        pop {{r1-r5,r12,lr}}
        b #0x{old:x}
    stats: .word 0x02145c5c
    manager: .word 0x02145c34
    flag_limit: .word 0x123
    table: .word 0x{table:x}
    ''',at)


def core_phase(at,old):
    """Observe real native core HP after its existing guarded damage path."""
    return asm(f'''
        push {{r4-r7,r12,lr}}
        mov r4,r0
        ldr r5,[r4]
        bl #0x{old:x}
        push {{r0-r3}}
        mrs r7,cpsr
        ldr r0,stats
        ldr r0,[r0]
        cmp r0,#0
        beq done
        ldr r0,[r0]
        cmp r0,#106
        bne done
        ldr r0,[r4]
        cmp r0,r5
        bne done
        ldr r0,[r4,#0x10c]
        cmp r0,#0x21
        bne done
        ldr r0,[r4,#0x110]
        cmp r0,#0
        ble done
        cmp r0,#0x12000
        bgt done
        ldr r1,manager
        ldr r1,[r1]
        cmp r1,#0
        movne r0,#1
        strbne r0,[r1,#0x1c8]
    done:
        msr cpsr_f,r7
        pop {{r0-r3}}
        pop {{r4-r7,r12,pc}}
    stats: .word 0x02145c5c
    manager: .word 0x02145c34
    ''',at)
