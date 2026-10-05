// After native target dispatch, match a confirmed paid Red Web Vault launch.
// Original overwritten instruction adds the result buffer at native sp+228.
push {r0-r3,r5-r8,r12,lr}
mrs r12,cpsr
push {r3,r12}
// Native stack has moved by 48 bytes; no caller locals are modified.
ldr r0,[r4,#0x14]
cmp r0,#40
bne vault_done
ldr r0,[r4,#0x44]
ldr r1,[r0]
ldr r2,player_vtable
cmp r1,r2
bne vault_done
ldr r1,[r0,#0xe8]
ldr r1,[r1]
tst r1,#0x4000
beq vault_done
ldr r1,[sp,#0x258]
cmp r1,#4
bne vault_done
ldr r5,[sp,#0x250]
cmp r5,#0
beq vault_done
sub r5,r5,#4
ldr r1,[r5]
ldr r1,[r1,#0x150]
ldr r2,enemy_setter
cmp r1,r2
bne vault_done
ldr r6,[r5,#0x1c]
cmp r6,#0
ble vault_done
mov r7,r0
mov r0,r4
bl 0x020bf164
// Both now use the native confirmed enemy impulse and the same normal gravity.
str r6,[r7,#0x1c]
mov r1,#0
str r1,[r5,#0x18]
vault_done:
pop {r3,r12}
msr cpsr_f,r12
pop {r0-r3,r5-r8,r12,lr}
add r0,sp,#0x228
b 0x020c9318
player_vtable: .word 0x0212e3f0
enemy_setter: .word 0x02049304
