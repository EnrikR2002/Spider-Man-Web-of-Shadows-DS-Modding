#!/usr/bin/env python3
"""Optional developer assembler for our extension; builds no ROM or assets.
Install Keystone into an isolated environment. Regular builds use guarded hex
and need only Python's standard library. Comments in combat_feedback.s describe
the native ABI, output layout and entry points.
"""
from pathlib import Path
import struct
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
TARGET = 0x0214F420
ks=Ks(KS_ARCH_ARM,KS_MODE_ARM)
source=Path(__file__).with_name('combat_feedback.s').read_text(encoding='utf-8')
code=bytearray(bytes(ks.asm(source,TARGET)[0]))
def put(offset,asm):
    raw=bytes(ks.asm(asm,TARGET+offset)[0])
    if len(code)<offset+len(raw):code.extend(bytes(offset+len(raw)-len(code)))
    code[offset:offset+len(raw)]=raw
    print(hex(offset),len(raw))
put(0x1000,'''push {r1,r2,r3,r12}
mrs r12,cpsr
mov r3,#0
ldr r1,state
str r5,[r1]
mov r2,#0
str r2,[r1,#8]
str r2,[r1,#12]
str r2,[r1,#0x100]
add r1,r1,#0x20
mov r2,#32
clear_buckets:
str r3,[r1],#4
subs r2,r2,#1
bne clear_buckets
msr cpsr_f,r12
pop {r1,r2,r3,r12}
pop {r3,r4,r5,pc}
state: .word 0x02152420''')
cleanup='''push {r0-r12,lr}
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
put(0x1100,cleanup.replace('CONTINUE','0x020e8f3c'))
put(0x1200,cleanup.replace('CONTINUE','0x020e8f94'))
capture='''push {r0-r12,lr}
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
ldr r2,[r4]
sub r2,r3,r2
cmp r2,#120
bls keep_chain
mov r2,#0
str r2,[r4,#4]
str r2,[r4,#0x10]
str r2,[r4,#0x18]
str r2,[r4,#0x20]
keep_chain:
str r3,[r4]
ldr r2,[r4,#4]
add r2,r2,r1
cmp r2,#0x1000000
movhi r2,#0x1000000
str r2,[r4,#4]
mov r2,#1
str r2,[r4,#8]
ldr r6,[r4,#0x18]
ldr r7,[r4,#0x1c]
str r6,[r4,#0x20]
str r7,[r4,#0x24]
ldr r6,[r4,#0x10]
ldr r7,[r4,#0x14]
str r6,[r4,#0x18]
str r7,[r4,#0x1c]
str r1,[r4,#0x10]
str r3,[r4,#0x14]
// Bounded telemetry, no engine data mutation.
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
put(0x1300,capture.replace('LOAD_HP','ldr r2,[r0,#0xe4]\nldr r2,[r2,#0x84]').replace('BUCKET','0x60').replace('CATEGORY','1').replace('CONTINUE','0x0205f3f4'))
put(0x1500,capture.replace('LOAD_HP','ldr r2,[r0,#0x44]').replace('BUCKET','0x20').replace('CATEGORY','0').replace('CONTINUE','0x020492ac'))
code.extend(bytes(0x3400-len(code)))
for offset,label in [(0x2600,'COMBO '),(0x2620,'DEALT'),(0x2640,'TAKEN'),(0x2660,'SUM ')]:
    raw=label.encode('utf-16le')+b'\0\0';code[offset:offset+len(raw)]=raw
struct.pack_into('<9I',code,0x2680,10000000,1000000,100000,10000,1000,100,10,1,0)

Path(__file__).with_name('combat_feedback.hex').write_text('\n'.join(code[i:i+32].hex() for i in range(0,len(code),32))+'\n', encoding='utf-8')
