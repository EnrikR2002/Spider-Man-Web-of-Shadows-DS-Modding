"""Owned Conductor pressure and adapters for the actual native HUDBossMeter."""
from tools.chapter_renewal_combat import asm
from tools.chapter_spectacle_combat import enhance,replace_once

HUD_TICK=0x020e0ae8
HUD_METER=0x020e77b4


def decisions(source,navigation,poise=0):
    source=enhance(source,navigation)
    source=replace_once(source,'''        cmp r0,#2
        bne recovery_done''','''        cmp r0,#2
        cmpne r0,#0
        bne recovery_done''')
    source=replace_once(source,'''        cmp r9,#15
        beq recovery_state
        cmp r9,#6''','''        cmp r9,#15
        beq recovery_state
        cmp r9,#7
        beq recovery_state
        cmp r9,#6''')
    source=replace_once(source,'        ldr r0,recovery_voice\n', '''        ldr r0,recovery_voice
        ldr r1,[r7,#12]
        cmp r1,#0
        subeq r0,r0,#10
''')
    source=replace_once(source,'        ldr r9,[r4,#0x14]\n', '''        ldr r9,[r4,#0x14]
        @ Committed boss strikes have poise, never HP invulnerability. The
        @ anticipation and final recovery remain open to native launch/hurt.
        ldr r0,[r7,#12]
        cmp r0,#6
        bne encore_poise_done
        ldr r0,encore_poise
        ldr r1,[r0]
        cmp r1,r6
        beq encore_same_owner
        str r6,[r0]
        mov r1,#0
        str r1,[r0,#4]
    encore_same_owner:
        ldr r1,[r0,#4]
        cmp r1,#0
        subne r1,r1,#1
        strne r1,[r0,#4]
        cmp r9,#51
        bne encore_counter_ready
        ldr r2,[r11,#0x178]
        cmp r2,#6
        blo encore_poise_done
        cmp r5,#26
        blo encore_rise_end
        cmp r5,#50
        movls r5,#51
        b encore_poise_done
    encore_rise_end:
        cmp r5,#3
        bhi encore_poise_done
        @ A completed native get-up earns one short counterattack window.
        @ HP damage continues, so this cannot extend a defeated actor's life.
        mov r1,#36
        str r1,[r0,#4]
        mov r1,#0
        str r1,[r8,#16]
        mov r9,#0
    encore_counter_ready:
        cmp r9,#3
        bhi encore_committed
        cmp r1,#0
        beq encore_poise_done
        cmp r5,#26
        blo encore_poise_done
        cmp r5,#50
        movls r5,r9
        b encore_poise_done
    encore_committed:
        cmp r9,#15
        bne encore_poise_done
        cmp r5,#26
        blo encore_poise_done
        cmp r5,#50
        bhi encore_poise_done
        ldr r0,[r8,#20]
        cmp r0,#0
        beq encore_poise_done
        cmp r1,#0
        movne r5,#15
        bne encore_poise_done
        ldr r1,[r11,#0x178]
        cmp r1,#5
        blo encore_poise_done
        ldr r0,[r0,#4]
        sub r0,r0,#4
        cmp r1,r0
        movlo r5,#15
    encore_poise_done:
''')
    source=replace_once(source,'''        ldrb r3,[r3,#0x1c7]
        cmp r3,#0
        beq select_ready
        mov r5,#0
        mov r3,#0
        str r3,[r8,#28]
        b done''','''        @ Floor warnings and the creature can now overlap. Native jump/R
        @ counterplay and the visible safe lanes remain available.
        b select_ready''')
    source=replace_once(source,'    select_ready:\n        cmp r0,r1','''    select_ready:
        ldr r3,[r6,#0x10]
        tst r3,#0x80
        beq walking
        ldr r3,[r4,#0x14]
        cmp r3,#51
        beq encore_ground_ready
        cmp r3,#3
        bhi walking
    encore_ground_ready:
        ldr r3,[r6,#0x1c]
        cmp r3,#0
        bne walking
        ldr r3,[r7,#12]
        cmp r3,#6
        bne encore_selected
        @ Above half health three attacks; below it the leaping slam joins.
        @ Long range gets a beam or a real advancing leap instead of a slow
        @ walk across the whole arena. Near targets get alternating rushes.
        cmp r2,#0x1c000
        bls encore_close
        cmp r1,#4
        movlo r0,#2
        eorhs r0,r0,#1
        andhs r0,r0,#1
        addhs r0,r0,#2
        b encore_selected
    encore_close:
        cmp r0,#2
        bne encore_selected
        cmp r1,#4
        movlo r0,#0
        movhs r0,#3
    encore_selected:
        cmp r0,r1''')
    # Start the next response promptly after a hit without suppressing native
    # hurt, knockdown, launch, web or death states.
    source=replace_once(source,'    interrupted:\n        mov r0,#0\n        str r0,[r8,#20]\n        mov r0,#18','''    interrupted:
        mov r0,#0
        str r0,[r8,#20]
        ldr r0,[r7,#12]
        cmp r0,#6
        moveq r0,#4
        movne r0,#18''')
    source=replace_once(source,'        moveq r1,#0x680','''        moveq r1,#0x680
        cmp r0,#6
        moveq r1,#0x1300''')
    return source+f'\n    encore_poise: .word 0x{poise:x}\n'


def secondary(at,old,slots,config,poise=0):
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
        cmp r0,#51
        bne check_counter
        ldr r0,[r6,#0x30]
        ldr r0,[r0,#0x178]
        cmp r0,#6
        ldrhs r5,keep
        b done
    check_counter:
        ldr r1,poise
        ldr r2,[r1]
        cmp r2,r6
        bne check_committed
        ldr r1,[r1,#4]
        cmp r1,#0
        beq check_committed
        cmp r0,#3
        ldrlo r5,keep
        blo done
        cmp r0,#15
        ldreq r5,keep
        beq done
    check_committed:
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
        ldr r1,[r1,#0x178]
        cmp r1,#5
        blo done
        ldr r0,[r0,#4]
        sub r0,r0,#4
        cmp r1,r0
        ldrlo r5,keep
    done:
        mov r0,r5
        pop {{r4-r8,pc}}
    keep: .word 0x7fffffff
    config: .word 0x{config:x}
    slots: .word 0x{slots:x}
    poise: .word 0x{poise:x}
    ''',at)


def find_boss(at,slots,config):
    """Return a live, exact-owned actor or zero; never cache a heap pointer."""
    return asm(f'''
        push {{r4-r7,lr}}
        sub sp,sp,#4
        ldr r0,stats
        ldr r0,[r0]
        cmp r0,#0
        beq absent
        ldr r1,[r0]
        cmp r1,#89
        bne absent
        ldr r4,slots
        mov r5,#32
    scan:
        ldr r6,[r4]
        ldr r7,[r4,#4]
        ldr r1,lower
        cmp r6,r1
        blo next
        cmp r7,r1
        blo next
        ldr r1,upper
        cmp r6,r1
        bhs next
        cmp r7,r1
        bhs next
        orr r1,r6,r7
        tst r1,#3
        bne next
        ldr r1,[r6,#0x44]
        cmp r1,r7
        bne next
        ldr r1,[r7]
        ldr r2,enemy
        cmp r1,r2
        bne next
        ldr r1,[r7,#0x40]
        ldr r2,config
        cmp r1,r2
        bne next
        ldr r1,[r4,#8]
        cmp r1,r2
        bne next
        ldr r1,[r7,#0x30]
        ldr r2,lower
        cmp r1,r2
        blo next
        ldr r2,upper
        cmp r1,r2
        bhs next
        tst r1,#3
        bne next
        ldr r1,[r1]
        cmp r1,r7
        bne next
        ldr r1,[r7,#0x44]
        cmp r1,#0
        ble next
        ldr r2,[r7,#0x48]
        cmp r1,r2
        bhi next
        mov r0,r7
        b done
    next:
        add r4,r4,#32
        subs r5,r5,#1
        bne scan
    absent:
        mov r0,#0
    done:
        add sp,sp,#4
        pop {{r4-r7,pc}}
    stats: .word 0x02145c5c
    lower: .word 0x02000000
    upper: .word 0x023ffc00
    enemy: .word 0x021301d0
    slots: .word 0x{slots:x}
    config: .word 0x{config:x}
    ''',at)


def hud_tick(at,resolver,owned,observed):
    """Opt into the existing meter lifecycle at the native HUD update."""
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mov r4,r0
        bl #0x{resolver:x}
        ldr r5,observed
        str r0,[r5]
        ldr r5,owned
        cmp r0,#0
        beq cleanup
        mov r1,#1
        str r1,[r5]
        mov r0,r4
        bl #0x020e0a54
        b done
    cleanup:
        ldr r1,[r5]
        cmp r1,#0
        beq done
        mov r1,#0
        str r1,[r5]
        mov r0,r4
        bl #0x020e0a54
    done:
        pop {{r0-r5,r12,lr}}
        push {{r3,r4,r5,lr}}
        b #0x{HUD_TICK+4:x}
    owned: .word 0x{owned:x}
    observed: .word 0x{observed:x}
    ''',at)


def meter(at,resolver,observed):
    """Feed native current/max health and use the original meter renderer.

    Avoid manufacturing a managed boss/interface object: its intrusive weak
    pointer list has a different contract from NormalEnemy. Original bosses
    run the exact original update outside this adapter's live ownership.
    """
    return asm(f'''
        push {{r0-r5,r12,lr}}
        mov r4,r0
        bl #0x{resolver:x}
        cmp r0,#0
        beq native
        ldr r1,[r0,#0x44]
        ldr r2,[r0,#0x48]
        str r1,[r4,#0xc]
        str r2,[r4,#0x10]
        str r2,[r4,#0x14]
        ldr r3,observed
        str r4,[r3,#4]
        str r1,[r3,#8]
        str r2,[r3,#12]
        mov r0,r4
        bl #0x020e7920
        pop {{r0-r5,r12,pc}}
    native:
        pop {{r0-r5,r12,lr}}
        push {{r3,r4,lr}}
        b #0x{HUD_METER+4:x}
    observed: .word 0x{observed:x}
    ''',at)
