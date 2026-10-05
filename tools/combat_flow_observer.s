// Cheap observer filter for ordinary actors/full-health enemies. Preserve native flags.
push {r2,r3,r12,lr}
mrs r12,cpsr
ldr r2,state
ldr r3,[r2]
cmp r3,#0
beq skip_snapshot
ldr r2,[r0]
ldr r3,low
cmp r2,r3
blo skip_snapshot
ldr r3,high
cmp r2,r3
bhi skip_snapshot
ldr r2,[r2,#0x150]
ldr r3,setter
cmp r2,r3
bne skip_snapshot
ldr r2,[r0,#0x44]
cmp r2,#0
ble skip_snapshot
ldr r3,[r0,#0x48]
cmp r2,r3
bge skip_snapshot
msr cpsr_f,r12
pop {r2,r3,r12,lr}
b 0x02150b20
skip_snapshot:
msr cpsr_f,r12
pop {r2,r3,r12,lr}
push {r4-r10,lr}
b 0x02073a6c
state: .word 0x02152420
low: .word 0x02120000
high: .word 0x0213df00
setter: .word 0x02049304
