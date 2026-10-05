#!/usr/bin/env python3
"""Optional Keystone reassembly of our HUD. Normal ROM builds use pinned hex."""
from pathlib import Path
import hashlib
import struct
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

TARGET = 0x0214F420
ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
source = Path(__file__).with_name('combat_hud.s').read_text(encoding='utf-8')
code = bytearray(0x3600)

def put(offset, assembly, limit):
    raw = bytes(ks.asm(assembly, TARGET + offset)[0])
    if len(raw) > limit: raise ValueError('Extension entry overlaps the next entry')
    code[offset:offset+len(raw)] = raw
    print(hex(offset), len(raw))

put(0, source, 0x1000)
put(0x1000, '''push {r1,r2,r3,r12}
mrs r12,cpsr
ldr r1,state
str r5,[r1]
mov r3,#0
str r3,[r1,#8]
str r3,[r1,#12]
add r1,r1,#0x20
mov r2,#376
clear_state:
str r3,[r1],#4
subs r2,r2,#1
bne clear_state
msr cpsr_f,r12
pop {r1,r2,r3,r12}
pop {r3,r4,r5,pc}
state: .word 0x02152420''', 0x100)

cleanup = '''push {r0-r12,lr}
mrs r12,cpsr
push {r11,r12}
ldr r4,state
ldr r1,[r4]
cmp r1,r0
bne clean_done
mov r1,#0
str r1,[r4]
ldr r0,[r4,#4]
str r1,[r4,#4]
cmp r0,#0
beq clean_done
ldr r0,font
bl 0x0200b200
clean_done:
pop {r11,r12}
msr cpsr_f,r12
pop {r0-r12,lr}
push {r4,lr}
b CONTINUE
state: .word 0x02152420
font: .word 0x02151c20'''
put(0x1100, cleanup.replace('CONTINUE', '0x020e8f3c'), 0x100)
put(0x1200, cleanup.replace('CONTINUE', '0x020e8f94'), 0x100)

# Retain read-only, capped native HP telemetry for paired balance experiments.
capture = '''push {r0-r12,lr}
mrs r12,cpsr
push {r11,r12}
ldr r5,state
ldr r2,[r5]
cmp r2,#0
beq capture_done
LOAD_HP
mov r8,r2
cmp r2,#0
ble capture_done
cmp r1,#0
ble capture_done
cmp r1,r2
movgt r1,r2
add r4,r5,#BUCKET
ldr r3,[r5,#12]
str r3,[r4]
mov r2,#1
str r2,[r4,#8]
add r4,r5,#0x100
ldr r6,[r4]
add r7,r6,#1
str r7,[r4]
and r6,r6,#15
add r4,r4,#0x20
add r4,r4,r6,lsl #5
str r0,[r4]
str r1,[r4,#4]
str r8,[r4,#8]
str r3,[r4,#12]
str lr,[r4,#16]
mov r2,#CATEGORY
str r2,[r4,#20]
ldr r2,[sp,#12]
str r2,[r4,#24]
sub r8,r8,r1
str r8,[r4,#28]
capture_done:
pop {r11,r12}
msr cpsr_f,r12
pop {r0-r12,lr}
push {r0,r1,r2,r3}
b CONTINUE
state: .word 0x02152420'''
put(0x1300, capture.replace('LOAD_HP', 'ldr r2,[r0,#0xe4]\nldr r2,[r2,#0x84]')
    .replace('BUCKET', '0x60').replace('CATEGORY', '1')
    .replace('CONTINUE', '0x0205f3f4'), 0x200)
put(0x1500, capture.replace('LOAD_HP', 'ldr r2,[r0,#0x44]')
    .replace('BUCKET', '0x20').replace('CATEGORY', '0')
    .replace('CONTINUE', '0x020492ac'), 0x200)

# Snapshot only currently updating actors with the known enemy HP setter ABI.
put(0x1700, '''push {r0-r12,lr}
mrs r12,cpsr
push {r11,r12}
ldr r5,state
ldr r2,[r5]
cmp r2,#0
beq observer_done
ldr r2,[r0]
ldr r3,code_low
cmp r2,r3
blo observer_done
ldr r3,code_high
cmp r2,r3
bhi observer_done
ldr r2,[r2,#0x150]
ldr r3,enemy_setter
cmp r2,r3
bne observer_done
ldr r8,[r0,#0x44]
ldr r9,[r0,#0x48]
cmp r8,#0
ble observer_done
cmp r8,r9
bge observer_done
cmp r9,#0x1000000
bhi observer_done
ldr r6,[r0,#0x30]
ldr r2,ram_low
cmp r6,r2
blo observer_done
ldr r2,ram_high
cmp r6,r2
bhi observer_done
tst r6,#3
bne observer_done
ldr r3,[r5,#12]
add r4,r5,#0x400
mov r7,#0
mov r10,#0
find_slot:
ldr r1,[r4]
cmp r1,r0
beq store_snapshot
cmp r7,#0
bne scan_next
cmp r1,#0
moveq r7,r4
beq scan_next
ldr r2,[r4,#4]
sub r2,r3,r2
cmp r2,#2
movhi r7,r4
scan_next:
add r4,r4,#32
add r10,r10,#1
cmp r10,#8
blo find_slot
cmp r7,#0
beq observer_done
mov r4,r7
store_snapshot:
str r0,[r4]
str r3,[r4,#4]
str r8,[r4,#8]
str r9,[r4,#12]
ldr r1,[r6,#0x7c]
ldr r2,[r6,#0x160]
add r1,r1,r2
str r1,[r4,#16]
ldr r1,[r6,#0x80]
ldr r2,[r6,#0x164]
add r1,r1,r2
str r1,[r4,#20]
ldr r1,[r6,#0x84]
str r1,[r4,#24]
ldr r1,[r6,#0x8c]
str r1,[r4,#28]
observer_done:
pop {r11,r12}
msr cpsr_f,r12
pop {r0-r12,lr}
push {r4-r10,lr}
b 0x02073a6c
state: .word 0x02152420
enemy_setter: .word 0x02049304
code_low: .word 0x02120000
code_high: .word 0x0213df00
ram_low: .word 0x02153420
ram_high: .word 0x023ffd00''', 0x400)

struct.pack_into('<9I', code, 0x2680, 10000000,1000000,100000,10000,1000,100,10,1,0)
Path(__file__).with_name('combat_hud.hex').write_text(
    '\n'.join(code[i:i+32].hex() for i in range(0,len(code),32))+'\n', encoding='utf-8')
print('SHA256', hashlib.sha256(code).hexdigest())
