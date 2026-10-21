"""Comboable normal attacks, standing recoil, and a bounded pressure escape.

Both decision passes use the same rule. Only action74 (the earned counter)
has armour; ordinary attacks accept native hurt. No HP/position writes.
"""
from tools import midnight_voltage_combat as voltage
from tools.chapter_spectacle_combat import replace_once
from tools.chapter_renewal_combat import asm


def decisions(source,navigation,poise,state,table,hero):
    source=voltage.decisions(source,navigation,poise,state,table,hero)
    source=replace_once(source,'        mov r1,#64','        mov r1,#72')
    source=replace_once(source,'''        ldr r1,[r8,#20]
        cmp r1,#0
        beq voltage_done
        ldr r2,[r11,#0x178]''','''        ldr r1,[r8,#20]
        cmp r1,#0
        beq voltage_done
        ldr r2,[r1]
        cmp r2,#74
        bne voltage_done
        ldr r2,[r11,#0x178]''')
    source=replace_once(source,'        sub r3,r3,#3','        sub r3,r3,#7')
    source=replace_once(source,'    voltage_done:\n', '''    voltage_done:
        @ Native38..45 are airborne hurt/knockback and48..50 are floor
        @ knockdown. Keep their damage, but enter standing hurt37 instead.
        @ Web/grapple46/47 and death53 retain their native decisions.
        ldr r0,[r7,#12]
        cmp r0,#6
        bne finale_mapped
        cmp r5,#38
        blo finale_mapped
        cmp r5,#45
        movls r5,#37
        bls finale_mapped
        cmp r5,#48
        blo finale_mapped
        cmp r5,#50
        movls r5,#37
    finale_mapped:
''')
    # Preserve the fast pursuit while adding honest post-interruption space.
    source=replace_once(source,'        moveq r0,#4','        moveq r0,#10')
    return source


def secondary(at,old,slots,config):
    """Chain the spectacle navigation pass, bypassing old blanket armour."""
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
        ldr r7,slots
        mov r8,#32
    scan:
        ldr r0,[r7]
        cmp r0,r4
        beq owner
        add r7,r7,#32
        subs r8,r8,#1
        bne scan
        b done
    owner:
        ldr r0,[r7,#4]
        cmp r0,r6
        bne done
        ldr r0,[r7,#8]
        ldr r1,config
        cmp r0,r1
        bne done
        ldr r0,[r4,#0x14]
        cmp r0,#15
        bne standing
        ldr r0,[r7,#20]
        cmp r0,#0
        beq standing
        ldr r1,[r0]
        cmp r1,#74
        bne standing
        ldr r1,[r6,#0x30]
        ldr r2,[r1]
        cmp r2,r6
        bne done
        ldr r2,[r1,#0x178]
        ldr r3,[r0,#4]
        sub r3,r3,#7
        cmp r2,r3
        bhs standing
        ldr r2,[r1,#0x254]
        cmp r2,#74
        mov r0,#0
        strbeq r0,[r4,#4]
        ldr r5,keep
        b done
    standing:
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
    config: .word 0x{config:x}
    ''',at)
