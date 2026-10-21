"""Damage-triggered physical escapes and pressure for the electronic symbiote."""
from tools.chapter_renewal_combat import asm
from tools import midnight_encore_combat as prior


def damage(at,old,state,config,*,hit_threshold=3,window=80):
    """Observe real native HP loss; queue a response without changing damage."""
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        ldr r2,lower
        cmp r0,r2
        blo native
        ldr r2,upper
        cmp r0,r2
        bhs native
        tst r0,#3
        bne native
        ldr r2,[r0]
        ldr r3,enemy
        cmp r2,r3
        bne native
        ldr r2,[r0,#0x40]
        ldr r3,config
        cmp r2,r3
        bne native
        ldr r2,stats
        ldr r2,[r2]
        cmp r2,#0
        beq native
        ldr r2,[r2]
        cmp r2,#89
        bne native
        ldr r4,state
        ldr r2,[r4]
        ldr r3,[r0,#0x30]
        cmp r2,r0
        bne reset
        ldr r2,[r4,#4]
        cmp r2,r3
        beq owned
    reset:
        str r0,[r4]
        str r3,[r4,#4]
        mov r2,#0
        str r2,[r4,#8]
        str r2,[r4,#12]
        str r2,[r4,#16]
        str r2,[r4,#20]
        str r2,[r4,#24]
    owned:
        ldr r2,[r0,#0x44]
        cmp r1,#0
        ble dead
        cmp r1,r2
        bhs native
        ldr r3,[r4,#36]
        add r3,r3,#1
        str r3,[r4,#36]
        ldr r3,[r4,#12]
        cmp r3,#0
        moveq r2,#0
        ldrne r2,[r4,#8]
        add r2,r2,#1
        mov r3,#{window}
        str r3,[r4,#12]
        cmp r2,#{hit_threshold}
        blo counted
        mov r2,#0
        mov r3,#1
        str r3,[r4,#16]
    counted:
        str r2,[r4,#8]
        b native
    dead:
        mov r2,#0
        str r2,[r4,#8]
        str r2,[r4,#16]
        str r2,[r4,#24]
    native:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        b #0x{old:x}
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    enemy: .word 0x021301d0
    stats: .word 0x02145c5c
    config: .word 0x{config:x}
    state: .word 0x{state:x}
    ''',at)


def decisions(source,navigation,poise,state,table,hero):
    source=prior.decisions(source,navigation,poise)
    first=source.index('        @ Committed boss strikes have poise')
    last=source.index('    encore_poise_done:\n',first)+len('    encore_poise_done:\n')
    source=source[:first]+f'''
        ldr r0,[r7,#12]
        cmp r0,#6
        bne voltage_done
        ldr r0,voltage_state
        ldr r1,[r0]
        cmp r1,r6
        bne voltage_done
        ldr r1,[r0,#4]
        cmp r1,r11
        bne voltage_done
        ldr r1,[r0,#12]
        cmp r1,#0
        subne r1,r1,#1
        strne r1,[r0,#12]
        ldr r1,[r0,#24]
        cmp r1,#0
        subne r1,r1,#1
        strne r1,[r0,#24]
        ldr r1,[r0,#20]
        cmp r1,#0
        subne r1,r1,#1
        strne r1,[r0,#20]
        bne voltage_holding
        ldr r1,[r0,#16]
        cmp r1,#0
        beq voltage_holding
        cmp r5,#53
        beq voltage_done
        @ A third real HP loss triggers an actual native attack transition,
        @ including from flinch/knockback. Its jump and drive tables move it.
        ldr r1,[r0,#32]
        and r1,r1,#1
        eor r2,r1,#1
        str r2,[r0,#32]
        add r1,r1,#4
        ldr r10,voltage_table
        add r10,r10,r1,lsl #5
        str r10,[r8,#20]
        mov r1,#0
        str r1,[r8,#12]
        str r1,[r8,#16]
        str r1,[r0,#16]
        str r1,[r0,#8]
        mov r1,#64
        str r1,[r0,#20]
        str r1,[r0,#24]
        ldr r1,[r0,#28]
        add r1,r1,#1
        str r1,[r0,#28]
        ldr r1,voltage_hero
        ldr r1,[r1]
        ldr r2,lower
        cmp r1,r2
        blo voltage_face_kept
        ldr r2,upper
        cmp r1,r2
        bhs voltage_face_kept
        tst r1,#3
        bne voltage_face_kept
        ldr r2,[r1]
        ldr r3,player
        cmp r2,r3
        bne voltage_face_kept
        mov r12,r1
        ldr r1,[r1,#0x30]
        tst r1,#3
        bne voltage_face_kept
        ldr r2,upper
        cmp r1,r2
        bhs voltage_face_kept
        ldr r2,lower
        cmp r1,r2
        blo voltage_face_kept
        ldr r2,[r1]
        cmp r2,r12
        bne voltage_face_kept
        ldr r2,[r1,#0x7c]
        ldr r3,[r1,#0x160]
        add r2,r2,r3
        ldr r3,[r11,#0x7c]
        ldr r1,[r11,#0x160]
        add r3,r3,r1
        cmp r2,r3
        movge r1,#1
        movlt r1,#0
        @ Face the target for the returning cut. Native walls contain the
        @ initial recoil; edge cases turn inward before the impulse.
        cmp r3,#0x28000
        movlo r1,#0
        cmp r3,#0xb8000
        movhi r1,#1
        str r1,[r8,#24]
    voltage_face_kept:
        mvn r1,#0
        str r1,[r8,#28]
        mov r1,#1
        strb r1,[r4,#4]
        mov r5,#15
        b done
    voltage_holding:
        cmp r9,#15
        bne voltage_done
        cmp r5,#26
        blo voltage_done
        cmp r5,#50
        bhi voltage_done
        ldr r1,[r8,#20]
        cmp r1,#0
        beq voltage_done
        ldr r2,[r11,#0x178]
        ldr r3,[r1,#4]
        sub r3,r3,#3
        cmp r2,r3
        bhs voltage_done
        mov r5,#15
        @ Consume the hurt transition without restarting the running clip.
        ldr r1,[r1]
        ldr r2,[r11,#0x254]
        cmp r1,r2
        moveq r1,#0
        strbeq r1,[r4,#4]
    voltage_done:
''' + source[last:]
    source=prior.replace_once(source,'        movgt r1,#3','        movgt r1,#3\n        movle r1,#4')
    source=prior.replace_once(source,'        moveq r1,#0x1300','        moveq r1,#0x2400')
    return source+f'\n voltage_state: .word 0x{state:x}\n voltage_table: .word 0x{table:x}\n voltage_hero: .word 0x{hero:x}\n'


def secondary(at,old,slots,config):
    return asm(f'''
        push {{r4-r8,lr}}
        mov r4,r0
        bl #0x{old:x}
        mov r5,r0
        cmp r5,#26
        blo done
        cmp r5,#50
        bhi done
        ldr r6,[r4,#0x44]
        ldr r0,[r6,#0x40]
        ldr r1,config
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x44]
        cmp r0,#0
        ble done
        ldr r0,[r4,#0x14]
        cmp r0,#15
        bne done
        ldr r7,slots
        mov r8,#32
    scan:
        ldr r0,[r7]
        cmp r0,r4
        beq owned
        add r7,r7,#32
        subs r8,r8,#1
        bne scan
        b done
    owned:
        ldr r0,[r7,#4]
        cmp r0,r6
        bne done
        ldr r0,[r7,#20]
        cmp r0,#0
        beq done
        ldr r1,[r6,#0x30]
        ldr r2,[r1,#0x178]
        ldr r3,[r0,#4]
        sub r3,r3,#3
        cmp r2,r3
        bhs done
        ldr r2,[r1,#0x254]
        ldr r0,[r0]
        cmp r2,r0
        moveq r0,#0
        strbeq r0,[r4,#4]
        ldr r5,keep
    done:
        mov r0,r5
        pop {{r4-r8,pc}}
    keep: .word 0x7fffffff
    config: .word 0x{config:x}
    slots: .word 0x{slots:x}
    ''',at)


def update(at,old,slots,config,hero,state,*,gap=14,rake_first=9,rake_second=16,wheel_gap=15):
    """Turn at authored gaps, rather than racing past a target into a wall."""
    return asm(f'''
        push {{r0-r8,lr}}
        mov r4,r0
        ldr r0,[r4,#0x14]
        cmp r0,#15
        bne done
        ldr r6,[r4,#0x44]
        ldr r0,[r6,#0x40]
        ldr r1,config
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x44]
        cmp r0,#0
        ble done
        ldr r5,slots
        mov r7,#32
    scan:
        ldr r0,[r5]
        cmp r0,r4
        beq slot
        add r5,r5,#32
        subs r7,r7,#1
        bne scan
        b done
    slot:
        ldr r0,[r5,#4]
        cmp r0,r6
        bne done
        ldr r0,[r5,#20]
        cmp r0,#0
        beq done
        ldr r7,[r6,#0x30]
        ldr r1,[r7]
        cmp r1,r6
        bne done
        ldr r1,[r0]
        ldr r2,[r7,#0x254]
        cmp r1,r2
        bne done
        ldr r2,[r7,#0x178]
        ldr r3,[r5,#28]
        mov r8,#{gap}
        cmp r1,#55
        bne turn_other
        mov r8,#{rake_first}
        cmp r2,#{rake_second}
        movhs r8,#{rake_second}
    turn_other:
        cmp r1,#63
        moveq r8,#{wheel_gap}
        cmp r1,#136
        moveq r8,#{wheel_gap}
        cmp r2,r8
        blt done
        cmp r3,r8
        bge done
        ldr r0,hero
        ldr r0,[r0]
        ldr r1,lower
        cmp r0,r1
        blo done
        ldr r1,upper
        cmp r0,r1
        bhs done
        tst r0,#3
        bne done
        ldr r1,[r0]
        ldr r2,player
        cmp r1,r2
        bne done
        mov r8,r0
        ldr r0,[r0,#0x30]
        ldr r1,lower
        cmp r0,r1
        blo done
        ldr r1,upper
        cmp r0,r1
        bhs done
        tst r0,#3
        bne done
        ldr r1,[r0]
        cmp r1,r8
        bne done
        ldr r1,[r0,#0x7c]
        ldr r2,[r0,#0x160]
        add r1,r1,r2
        ldr r2,[r7,#0x7c]
        ldr r3,[r7,#0x160]
        add r2,r2,r3
        cmp r1,r2
        movge r0,#1
        movlt r0,#0
        cmp r2,#0x18000
        movlo r0,#1
        cmp r2,#0xc8000
        movhi r0,#0
        str r0,[r5,#24]
        ldr r0,state
        ldr r1,[r0,#44]
        add r1,r1,#1
        str r1,[r0,#44]
    done:
        pop {{r0-r8,lr}}
        b #0x{old:x}
    slots: .word 0x{slots:x}
    config: .word 0x{config:x}
    hero: .word 0x{hero:x}
    state: .word 0x{state:x}
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    player: .word 0x0212e3f0
    ''',at)
