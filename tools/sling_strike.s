// Entry at 02150F20: replace the paid zip follow-up's first punch with a kick.
ldr r1,[r1]
push {r0,r2,r3,r12}
mrs r12,cpsr
push {r3,r12}
ldr r2,[r0]
ldr r3,player_vtable
cmp r2,r3
bne action_done
// Keep the marker until the first normal air recovery physics step stops travel.
cmp r1,#38
beq action_done
ldr r2,marker
mov r3,#0
str r3,[r2]
str r3,[r2,#4]
str r3,[r2,#8]
cmp r1,#1
bne action_done
ldr r2,[r0,#0xe8]
ldr r2,[r2]
tst r2,#0x8000
beq action_done
ldr r2,[r0,#0x30]
ldr r2,[r2,#0x1f8]
cmp r2,#0
beq action_done
ldr r3,[r2,#0x44]
cmp r3,r0
bne action_done
ldr r3,[r2,#0x14]
cmp r3,#31
beq paid_zip
cmp r3,#51
bne action_done
ldr r3,[r2,#0x18]
cmp r3,#31
bne action_done
paid_zip:
ldr r3,[r2,#0x54]
cmp r3,#0
beq action_done
ldr r2,marker
str r0,[r2]
mov r1,#3
action_done:
pop {r3,r12}
msr cpsr_f,r12
pop {r0,r2,r3,r12}
b 0x020728f4
player_vtable: .word 0x0212e3f0
marker: .word 0x02152aa0
// SPLIT DAMAGE
// Entry at 02151120: retain the zip's 0.1, consolidate three 1-unit hits into one.
push {r2,r3,r12,lr}
ldr r2,[r5]
ldr r3,marker
ldr r3,[r3]
cmp r2,#0
beq damage_done
cmp r2,r3
bne damage_done
ldr r2,[r2,#0x30]
ldr r3,[r2,#0x254]
cmp r3,#3
bne damage_done
ldr r2,[r2,#0x1f8]
ldr r2,[r2,#0x14]
cmp r2,#51
bne damage_done
cmp r1,#0x1000
bne damage_done
mov r1,#0x3000
ldr r2,marker
ldr r3,[r2,#8]
cmp r3,#0
bne damage_done
mov r3,#4
str r3,[r2,#4]
mov r3,#1
str r3,[r2,#8]
damage_done:
bl 0x020492a8
pop {r2,r3,r12,pc}
marker: .word 0x02152aa0
// SPLIT PHYSICS
// After native controller update, three collision steps carry the kick; fourth stops.
push {r0,r1,r2,r3,r12,lr}
mrs r12,cpsr
ldr r0,marker
ldr r1,[r0]
cmp r1,r4
bne physics_done
ldr r1,[r0,#4]
ldr r3,[r0,#8]
cmp r3,#0
beq physics_done
ldr r2,[r4,#0x30]
ldr r3,[r2,#0x254]
cmp r3,#3
bne recovery_stop
ldr r3,[r2,#0x1f8]
cmp r3,#0
beq recovery_clear
ldr r3,[r3,#0x14]
cmp r3,#51
bne recovery_stop
cmp r1,#0
moveq r1,#0
streq r1,[r4,#0x18]
beq physics_done
sub r1,r1,#1
str r1,[r0,#4]
cmp r1,#0
streq r1,[r4,#0x18]
beq physics_done
ldr r2,[r2,#0x180]
cmp r2,#0
mov r1,#0x4000
rsbeq r1,r1,#0
str r1,[r4,#0x18]
b physics_done
recovery_stop:
ldr r2,[r4,#0x30]
ldr r2,[r2,#0x1f8]
cmp r2,#0
beq recovery_clear
ldr r2,[r2,#0x14]
cmp r2,#19
moveq r1,#0
streq r1,[r4,#0x18]
recovery_clear:
mov r1,#0
str r1,[r0]
str r1,[r0,#4]
str r1,[r0,#8]
physics_done:
msr cpsr_f,r12
pop {r0,r1,r2,r3,r12,lr}
mov r2,#0
b 0x02073b60
marker: .word 0x02152aa0
