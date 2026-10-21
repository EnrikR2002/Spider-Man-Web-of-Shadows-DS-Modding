"""Actual poise physics, short strike commitment and owned native pursuit."""
from tools.chapter_renewal_combat import asm
from tools import midnight_finale_combat as prior
from tools.chapter_spectacle_combat import replace_once

IMPULSE_SITE=0x02094d4c
CONTACT_RESULT_SITE=0x0207862c


def lifecycle(at,old,state,slots):
    """Reset private combat owners before each native arena begin, including retry."""
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        ldr r1,stats
        ldr r1,[r1]
        cmp r1,#0
        beq native
        ldr r1,[r1]
        cmp r1,#89
        bne native
        ldr r1,manager
        ldr r1,[r1]
        cmp r1,#0
        beq native
        ldrb r1,[r1,#0x1c0]
        cmp r1,#0
        bne native
        ldr r1,state
        mov r2,#0
        str r2,[r1]
        str r2,[r1,#8]
        str r2,[r1,#12]
        str r2,[r1,#16]
        str r2,[r1,#20]
        str r2,[r1,#24]
        str r2,[r1,#48]
        str r2,[r1,#52]
        str r2,[r1,#64]
        str r2,[r1,#68]
        ldr r1,slots
        mov r3,#32
    clear:
        str r2,[r1],#32
        subs r3,r3,#1
        bne clear
    native:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        b #0x{old:x}
    stats: .word 0x02145c5c
    manager: .word 0x02145c34
    state: .word 0x{state:x}
    slots: .word 0x{slots:x}
    ''',at)


def hit_observer(at,boss,log):
    """Actual native boss-to-player collision result after ReceiveHit returns."""
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        ldr r0,[sp,#0x28]
        ldr r1,lower
        cmp r0,r1
        blo done
        ldr r1,upper
        cmp r0,r1
        bhs done
        tst r0,#3
        bne done
        ldr r1,[r0]
        ldr r2,enemy
        cmp r1,r2
        bne done
        ldr r1,[r0,#0x40]
        ldr r2,boss
        cmp r1,r2
        bne done
        ldr r1,[sp,#0x78]
        ldr r2,lower
        cmp r1,r2
        blo done
        ldr r2,upper
        cmp r1,r2
        bhs done
        tst r1,#3
        bne done
        ldr r2,[r1]
        ldr r3,player
        cmp r2,r3
        bne done
        ldr r4,log
        ldr r2,[r4]
        cmp r2,#64
        bhs done
        add r3,r2,#1
        str r3,[r4]
        add r4,r4,#4
        add r4,r4,r2,lsl #5
        ldr r0,[r0,#0x30]
        ldr r1,[r1,#0x30]
        ldr r2,[r0,#0x254]
        str r2,[r4]
        ldr r2,[r0,#0x178]
        str r2,[r4,#4]
        ldr r2,[sp,#0xac]
        str r2,[r4,#8]
        ldr r2,[sp,#0x74]
        str r2,[r4,#12]
        ldr r2,stats
        ldr r2,[r2]
        ldr r2,[r2,#0x84]
        str r2,[r4,#16]
        ldr r2,[r0,#0x80]
        ldr r3,[r0,#0x164]
        add r2,r2,r3
        str r2,[r4,#20]
        ldr r2,[r1,#0x80]
        ldr r3,[r1,#0x164]
        add r2,r2,r3
        str r2,[r4,#24]
        ldr r2,[r0,#0x7c]
        ldr r3,[r0,#0x160]
        add r2,r2,r3
        ldr r3,[r1,#0x7c]
        sub r2,r2,r3
        ldr r3,[r1,#0x160]
        sub r2,r2,r3
        str r2,[r4,#28]
    done:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        ldr r0,[sp,#0x54]
        b #0x02078630
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    enemy: .word 0x021301d0
    player: .word 0x0212e3f0
    stats: .word 0x02145c5c
    boss: .word 0x{boss:x}
    log: .word 0x{log:x}
    ''',at)


def interval(at,table):
    """r0 action / r1 whole-sample clock -> r0 bool; preserve r1..r4."""
    return asm(f'''
        push {{r1-r4,lr}}
        ldr r2,table
    loop:
        ldr r3,[r2]
        cmn r3,#1
        beq absent
        cmp r3,r0
        bne next
        ldr r3,[r2,#4]
        cmp r1,r3
        blo next
        ldr r3,[r2,#8]
        cmp r1,r3
        movlo r0,#1
        poplo {{r1-r4,pc}}
    next:
        add r2,r2,#12
        b loop
    absent:
        mov r0,#0
        pop {{r1-r4,pc}}
    table: .word 0x{table:x}
    ''',at)


def armour(at,slots,boss,warden,boss_check,warden_check,counters):
    """One eligibility rule for both state passes and native incoming impulse."""
    return asm(f'''
        push {{r1-r9,lr}}
        mov r4,r0
        ldr r1,lower
        cmp r4,r1
        blo absent
        ldr r1,upper
        cmp r4,r1
        bhs absent
        tst r4,#3
        bne absent
        ldr r1,[r4,#0x14]
        cmp r1,#15
        bne absent
        ldr r5,[r4,#0x44]
        ldr r1,lower
        cmp r5,r1
        blo absent
        ldr r1,upper
        cmp r5,r1
        bhs absent
        tst r5,#3
        bne absent
        ldr r1,[r5]
        ldr r2,enemy
        cmp r1,r2
        bne absent
        ldr r1,[r5,#0x44]
        cmp r1,#0
        ble absent
        ldr r6,[r5,#0x40]
        ldr r1,boss
        cmp r6,r1
        moveq r9,#1
        beq owned_config
        ldr r1,warden
        cmp r6,r1
        bne absent
        ldr r1,stats
        ldr r1,[r1]
        cmp r1,#0
        beq absent
        ldr r1,[r1]
        cmp r1,#81
        cmpne r1,#83
        cmpne r1,#86
        bne absent
        mov r9,#0
    owned_config:
        ldr r7,slots
        mov r8,#32
    scan:
        ldr r1,[r7]
        cmp r1,r4
        beq slot
        add r7,r7,#32
        subs r8,r8,#1
        bne scan
        b absent
    slot:
        ldr r1,[r7,#4]
        cmp r1,r5
        bne absent
        ldr r1,[r7,#8]
        cmp r1,r6
        bne absent
        ldr r7,[r7,#20]
        cmp r7,#0
        beq absent
        ldr r6,[r5,#0x30]
        ldr r1,lower
        cmp r6,r1
        blo absent
        ldr r1,upper
        cmp r6,r1
        bhs absent
        tst r6,#3
        bne absent
        ldr r1,[r6]
        cmp r1,r5
        bne absent
        ldr r0,[r7]
        ldr r1,[r6,#0x254]
        cmp r0,r1
        bne absent
        ldr r1,[r6,#0x178]
        cmp r9,#1
        bne regular_windows
        ldr r2,counters
        add r3,r2,#128
        cmp r7,r3
        addne r3,r2,#160
        cmp r7,r3
        bne regular_windows
        cmp r1,#34
        movlo r0,#1
        movhs r0,#0
        pop {{r1-r9,pc}}
    regular_windows:
        cmp r9,#1
        beq boss_windows
        bl #0x{warden_check:x}
        b windows_done
    boss_windows:
        bl #0x{boss_check:x}
    windows_done:
        pop {{r1-r9,pc}}
    absent:
        mov r0,#0
        pop {{r1-r9,pc}}
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    enemy: .word 0x021301d0
    stats: .word 0x02145c5c
    slots: .word 0x{slots:x}
    boss: .word 0x{boss:x}
    warden: .word 0x{warden:x}
    counters: .word 0x{counters:x}
    ''',at)


def impulse(at,check,debug):
    """Skip only the decoded native incoming X/Y impulse block; HP still applies."""
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mrs r5,cpsr
        mov r0,r6
        bl #0x{check:x}
        cmp r0,#0
        beq native
        ldr r0,debug
        ldr r1,[r0]
        add r1,r1,#1
        str r1,[r0]
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        b #0x02094e08
    native:
        msr cpsr_f,r5
        pop {{r0-r5,r12,lr}}
        ldr r1,[r6,#0x44]
        b #0x02094d50
    debug: .word 0x{debug:x}
    ''',at)


def decisions(source,navigation,poise,state,table,hero,check):
    source=prior.decisions(source,navigation,poise,state,table,hero)
    source=replace_once(source,'    fresh:\n',f'''    fresh:
        ldr r0,[r7,#12]
        cmp r0,#6
        bne reliable_fresh_done
        ldr r0,reliable_state
        mov r1,#0
        str r1,[r0]
        str r1,[r0,#68]
    reliable_fresh_done:
''')
    source=replace_once(source,'        ldr r9,[r4,#0x14]',f'''        ldr r9,[r4,#0x14]
        ldr r0,[r7,#12]
        cmp r0,#6
        bne reliable_boss_guard_done
        ldr r0,reliable_state
        ldr r1,[r0]
        cmp r1,r6
        bne reliable_new_owner
        ldr r1,[r0,#4]
        cmp r1,r11
        beq reliable_guard_count
    reliable_new_owner:
        str r6,[r0]
        str r11,[r0,#4]
        mov r1,#0
        str r1,[r0,#8]
        str r1,[r0,#12]
        str r1,[r0,#16]
        str r1,[r0,#20]
        str r1,[r0,#24]
        str r1,[r0,#68]
    reliable_guard_count:
        cmp r9,#26
        cmpne r9,#27
        movne r1,#0
        strne r1,[r0,#68]
        bne reliable_boss_guard_done
        ldr r1,[r0,#68]
        add r1,r1,#1
        cmp r1,#12
        movhs r1,#1
        strhs r1,[r0,#16]
        movhs r1,#0
        str r1,[r0,#68]
    reliable_boss_guard_done:
        ldr r0,[r7,#12]
        cmp r0,#4
        bne reliable_warden_done
        cmp r5,#26
        blo reliable_warden_done
        cmp r5,#50
        bhi reliable_warden_done
        push {{r0-r3,r12,lr}}
        mov r0,r4
        bl #0x{check:x}
        cmp r0,#0
        pop {{r0-r3,r12,lr}}
        beq reliable_warden_done
        mov r5,#15
        mov r0,#0
        strb r0,[r4,#4]
    reliable_warden_done:''')
    first=source.index('    voltage_holding:\n');last=source.index('    voltage_done:\n',first)
    source=source[:first]+f'''    voltage_holding:
        cmp r5,#26
        blo voltage_done
        cmp r5,#50
        bhi voltage_done
        push {{r0-r3,r12,lr}}
        mov r0,r4
        bl #0x{check:x}
        cmp r0,#0
        pop {{r0-r3,r12,lr}}
        beq voltage_done
        mov r5,#15
        ldr r1,[r8,#20]
        ldr r1,[r1]
        ldr r2,[r11,#0x254]
        cmp r1,r2
        moveq r1,#0
        strbeq r1,[r4,#4]
''' + source[last:]
    # Native chase speed increases along the route; only Midnight's Skitter.
    source=replace_once(source,'        moveq r1,#0xe00', '''        moveq r1,#0xe00
        cmp r0,#3
        bne reliable_walk_done
        ldr r2,stats
        ldr r2,[r2]
        ldr r2,[r2]
        cmp r2,#81
        cmpne r2,#83
        cmpne r2,#86
        bne reliable_walk_done
        mov r1,#0x1000
        cmp r2,#83
        movhs r1,#0x1200
    reliable_walk_done:
''')
    return source+f'\n reliable_state: .word 0x{state:x}\n'


def staged_spawn(at,old,stats_table,configs,slots,room_marker):
    """Native config HP at construction; no live HP writes, max four actors."""
    return asm(f'''
        push {{r4-r8,lr}}
        mov r4,r0
        bl #0x{old:x}
        mrs r8,cpsr
        push {{r0-r3,r12,lr}}
        ldr r0,stats
        ldr r0,[r0]
        cmp r0,#0
        beq done
        ldr r5,[r0]
        ldr r6,table
    find:
        ldr r0,[r6]
        cmp r0,#0
        beq done
        cmp r0,r5
        beq found
        add r6,r6,#16
        b find
    found:
        ldr r1,room_marker
        ldr r0,[r1]
        cmp r0,r5
        beq config_start
        str r5,[r1]
        ldr r0,slots
        mov r2,#0
        mov r3,#32
    clear_old_slots:
        str r2,[r0],#32
        subs r3,r3,#1
        bne clear_old_slots
    config_start:
        ldr r7,configs
        mov r2,#3
        add r6,r6,#4
    hp_config:
        ldr r0,[r7],#4
        ldr r1,[r6],#4
        str r1,[r0,#12]
        subs r2,r2,#1
        bne hp_config
        cmp r5,#81
        cmpne r5,#83
        cmpne r5,#86
        bne done
        ldr r6,slots
        mov r7,#32
        mov r5,#0
    scan:
        ldr r0,[r6]
        cmp r0,#0
        beq next
        ldr r0,[r6,#4]
        ldr r1,lower
        cmp r0,r1
        blo next
        ldr r1,upper
        cmp r0,r1
        bhs next
        tst r0,#3
        bne next
        ldr r1,[r0]
        ldr r2,enemy
        cmp r1,r2
        bne next
        ldr r1,[r0,#0x44]
        cmp r1,#0
        ble next
        ldr r1,[r0,#0x40]
        ldr r2,[r6,#8]
        cmp r1,r2
        bne next
        ldr r2,configs
        ldr r3,[r2]
        cmp r1,r3
        ldrne r3,[r2,#4]
        cmpne r1,r3
        ldrne r3,[r2,#8]
        cmpne r1,r3
        addeq r5,r5,#1
    next:
        add r6,r6,#32
        subs r7,r7,#1
        bne scan
        cmp r5,#4
        movhs r0,#36
        strhs r0,[r4]
    done:
        pop {{r0-r3,r12,lr}}
        msr cpsr_f,r8
        pop {{r4-r8,pc}}
    table: .word 0x{stats_table:x}
    configs: .word 0x{configs:x}
    slots: .word 0x{slots:x}
    room_marker: .word 0x{room_marker:x}
    stats: .word 0x02145c5c
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    enemy: .word 0x021301d0
    ''',at)


def secondary(at,old,slots,boss,check):
    return asm(f'''
        push {{r4-r8,lr}}
        mov r4,r0
        bl #0x{old:x}
        mov r5,r0
        cmp r5,#26
        blo done
        cmp r5,#50
        bhi done
        mov r0,r4
        bl #0x{check:x}
        cmp r0,#0
        beq standing
        mov r0,#0
        strb r0,[r4,#4]
        ldr r5,keep
        b done
    standing:
        ldr r6,[r4,#0x44]
        ldr r0,[r6,#0x40]
        ldr r1,boss
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x44]
        cmp r0,#0
        ble done
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
        cmp r5,#38
        blo done
        cmp r5,#45
        movls r5,#37
        bls done
        cmp r5,#48
        blo done
        cmp r5,#50
        movls r5,#37
    done:
        mov r0,r5
        pop {{r4-r8,pc}}
    keep: .word 0x7fffffff
    slots: .word 0x{slots:x}
    boss: .word 0x{boss:x}
    ''',at)


def update(at,old,slots,boss,hero,state,contact,counters):
    """Brake in reach, face in gaps, and keep counter trajectories near the hero."""
    return asm(f'''
        push {{r4-r11,lr}}
        sub sp,sp,#12
        mov r4,r0
        bl #0x{old:x}
        str r0,[sp,#8]
        ldr r0,[r4,#0x14]
        cmp r0,#15
        bne done
        ldr r6,[r4,#0x44]
        ldr r0,[r6,#0x40]
        ldr r1,boss
        cmp r0,r1
        bne done
        ldr r0,[r6,#0x44]
        cmp r0,#0
        ble done
        ldr r5,slots
        mov r1,#32
    scan:
        ldr r0,[r5]
        cmp r0,r4
        beq slot
        add r5,r5,#32
        subs r1,r1,#1
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
        ldr r0,[r0]
        ldr r1,[r7,#0x254]
        cmp r0,r1
        bne done
        str r0,[sp]
        ldr r9,[r7,#0x178]
        ldr r8,hero
        ldr r8,[r8]
        ldr r1,lower
        cmp r8,r1
        blo done
        ldr r1,upper
        cmp r8,r1
        bhs done
        tst r8,#3
        bne done
        ldr r1,[r8]
        ldr r2,player
        cmp r1,r2
        bne done
        mov r2,r8
        ldr r8,[r8,#0x30]
        ldr r1,lower
        cmp r8,r1
        blo done
        ldr r1,upper
        cmp r8,r1
        bhs done
        tst r8,#3
        bne done
        ldr r1,[r8]
        cmp r1,r2
        bne done
        ldr r10,[r8,#0x7c]
        ldr r1,[r8,#0x160]
        add r10,r10,r1
        ldr r1,[r7,#0x7c]
        ldr r2,[r7,#0x160]
        add r1,r1,r2
        sub r10,r10,r1
        cmp r10,#0
        movge r11,r10
        rsblt r11,r10,#0
        ldr r0,[sp]
        mov r1,r9
        bl #0x{contact:x}
        cmp r0,#0
        bne facing_kept
        cmp r10,#0
        movge r1,#1
        movlt r1,#0
        ldr r2,[r5,#24]
        cmp r1,r2
        beq facing_kept
        str r1,[r5,#24]
        str r1,[r7,#0x180]
        ldr r1,[r6,#0x18]
        rsb r1,r1,#0
        str r1,[r6,#0x18]
    facing_kept:
        ldr r0,[r5,#20]
        ldr r1,counters
        add r2,r1,#128
        cmp r0,r2
        addne r2,r1,#160
        cmp r0,r2
        bne brake
        ldr r4,state
        ldr r1,[r4,#64]
        cmp r0,r1
        bne counter_start
        ldr r0,[r4,#52]
        cmp r9,r0
        bhs counter_drive
    counter_start:
        mov r0,r6
        bl #0x020739b4
        ldr r0,[r7,#0x80]
        ldr r1,[r7,#0x164]
        add r0,r0,r1
        ldr r1,[r8,#0x80]
        ldr r2,[r8,#0x164]
        add r1,r1,r2
        sub r0,r0,r1
        cmp r0,#0x5000
        movle r0,#0xb00
        movgt r0,#0x1400
        rsbgt r0,r0,#0
        str r0,[r6,#0x1c]
    counter_drive:
        ldr r0,[sp]
        str r0,[r4,#48]
        str r9,[r4,#52]
        ldr r0,[r5,#20]
        str r0,[r4,#64]
        ldr r0,[r4,#60]
        add r0,r0,#1
        str r0,[r4,#60]
        cmp r9,#8
        movlo r0,#0x1800
        rsblo r0,r0,#0
        blo set_counter_drive
        cmp r9,#34
        movhs r0,#0
        bhs set_counter_drive
        mov r0,#0x3000
        cmp r11,#0x7000
        movlo r0,#0
    set_counter_drive:
        ldr r1,[r5,#24]
        cmp r1,#0
        rsbeq r0,r0,#0
        str r0,[r6,#0x18]
        b done
    brake:
        ldr r4,state
        ldr r0,[sp]
        str r0,[r4,#48]
        str r9,[r4,#52]
        ldr r0,[r5,#20]
        str r0,[r4,#64]
        cmp r11,#0x6000
        bhs done
        ldr r0,[r6,#0x18]
        cmp r10,#0
        rsblt r0,r0,#0
        cmp r0,#0
        movgt r0,#0
        strgt r0,[r6,#0x18]
    done:
        ldr r0,[sp,#8]
        add sp,sp,#12
        pop {{r4-r11,pc}}
    slots: .word 0x{slots:x}
    boss: .word 0x{boss:x}
    hero: .word 0x{hero:x}
    state: .word 0x{state:x}
    counters: .word 0x{counters:x}
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    player: .word 0x0212e3f0
    ''',at)
