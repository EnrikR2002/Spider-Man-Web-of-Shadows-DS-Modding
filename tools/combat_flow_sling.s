// Entry at 02150F20: replace the paid zip follow-up's first punch with a kick.
ldr r1,[r1]
push {r0,r2,r3,r12}
mrs r12,cpsr
push {r3,r12}
ldr r2,[r0]
ldr r3,player_vtable
cmp r2,r3
bne action_done
// Keep the marker through fall/landing so bounded passage can stop and turn.
cmp r1,#38
beq action_done
cmp r1,#119
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
cmp r2,#0
beq damage_done
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
mov r3,#8
str r3,[r2,#4]
mov r3,#1
str r3,[r2,#8]
// Snapshot target X at the confirmed contact; movement uses no retained target pointer.
ldr r3,[r0,#0x30]
ldr r12,[r3,#0x7c]
ldr r3,[r3,#0x160]
add r12,r12,r3
str r12,[r2,#12]
ldr r3,[r2]
ldr r3,[r3,#0x30]
ldr r3,[r3,#0x180]
str r3,[r2,#16]
cmp r3,#0
addeq r12,r12,#-81920
addne r12,r12,#81920
str r12,[r2,#20]
damage_done:
bl 0x020492a8
pop {r2,r3,r12,pc}
marker: .word 0x02152aa0
// SPLIT PHYSICS
// A confirmed paid kick crosses to the far side, then faces the target again.
// At most seven advancing native collision steps; normal input/interruption wins.
push {r0,r1,r2,r3,r12,lr}
mrs r12,cpsr
push {r3,r12}
ldr r0,marker
ldr r1,[r0]
cmp r1,r4
bne physics_done
ldr r3,[r0,#8]
cmp r3,#0
beq physics_done
ldr r2,[r4,#0x30]
ldr r3,[r2,#0x1f8]
cmp r3,#0
beq recovery_clear
ldr r3,[r3,#0x14]
cmp r3,#51
beq allow_kick
cmp r3,#19
bne recovery_stop
ldr r3,[r2,#0x254]
cmp r3,#38
beq pass_step
cmp r3,#3
bne recovery_stop
b pass_step
allow_kick:
ldr r3,[r2,#0x254]
cmp r3,#3
bne recovery_stop
pass_step:
ldr r1,[r0,#4]
subs r1,r1,#1
str r1,[r0,#4]
ble pass_stop
ldr r1,[r2,#0x7c]
ldr r3,[r2,#0x160]
add r1,r1,r3
ldr r3,[r0,#20]
ldr r2,[r0,#16]
cmp r2,#0
beq check_left
cmp r1,r3
bge pass_stop
mov r1,#0x5000
b pass_move
check_left:
cmp r1,r3
ble pass_stop
mov r1,#0x5000
rsb r1,r1,#0
pass_move:
str r1,[r4,#0x18]
b physics_done
recovery_stop:
// The controller queues landing before the motion changes on this update.
ldr r2,[r4,#0x30]
ldr r3,[r2,#0x1f8]
ldr r3,[r3,#0x14]
cmp r3,#24
beq pass_stop
// Stop residual passing velocity on landing; turn only if actually across target.
ldr r2,[r4,#0x30]
ldr r3,[r2,#0x254]
cmp r3,#119
beq pass_stop
cmp r3,#38
beq pass_stop
b recovery_clear
pass_stop:
mov r1,#0
str r1,[r4,#0x18]
ldr r2,[r4,#0x30]
ldr r1,[r2,#0x7c]
ldr r3,[r2,#0x160]
add r1,r1,r3
ldr r3,[r0,#12]
ldr r2,[r0,#16]
cmp r2,#0
beq crossed_left
cmp r1,r3
ble recovery_clear
b turn_back
crossed_left:
cmp r1,r3
bge recovery_clear
turn_back:
eor r2,r2,#1
sub sp,sp,#8
str r2,[sp]
mov r0,r4
mov r1,sp
bl 0x02072860
add sp,sp,#8
ldr r0,marker
recovery_clear:
mov r1,#0
str r1,[r0]
str r1,[r0,#4]
str r1,[r0,#8]
physics_done:
pop {r3,r12}
msr cpsr_f,r12
pop {r0,r1,r2,r3,r12,lr}
mov r2,#0
b 0x02073b60
marker: .word 0x02152aa0
