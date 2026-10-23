// Stateless purchased-Black clip routing; native movement, hits and air follow-up.
 b animation
 b evade

animation:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 cmp r0,#0
 beq animation_out
 mov r0,r4
 bl active
 cmp r0,#0
 ldrne r0,=LIFT_SCA
 strne r0,[sp,#0x4c]       // caller's native action record at original SP+0x2c
animation_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_ANIMATION

evade:
 push {r0-r3,r12,lr}
 sub sp,sp,#8
 ldr r0,[r8,#0x44]
 ldr r0,[r0,#0x30]
 bl active
 cmp r0,#0
 beq evade_out
 ldr r0,[r8,#0x44]
 ldr r0,[r0,#0x30]
 ldr r0,[r0,#0x1f8]
 cmp r0,r8
 movne r0,#0
 bne evade_out
 mov r0,#3
 str r0,[sp]
 mov r1,sp
 add r0,r8,#0x28
 bl 0x020cff0c
evade_out:
 cmp r0,#0
 add sp,sp,#8
 pop {r0-r3,r12,lr}
 beq OLD_EVADE
 add sp,sp,#0x58          // later native evade transition consumes the queued R
 mvn r0,#0x80000000
 pop {r4-r8,pc}

active:                   // current motion -> owned Black state45/action128
 tst r0,#3
 bne inactive
 cmp r0,#0x02000000
 blo inactive
 ldr r3,=0x023ffc00
 cmp r0,r3
 bhi inactive
 ldr r1,[r0]
 tst r1,#3
 bne inactive
 cmp r1,#0x02000000
 blo inactive
 ldr r3,=0x023fff00
 cmp r1,r3
 bhi inactive
 ldr r2,[r1]
 ldr r3,=0x0212e3f0
 cmp r2,r3
 bne inactive
 ldr r2,[r1,#0x30]
 cmp r2,r0
 bne inactive
 ldr r2,[r1,#0x34]
 cmp r2,#1
 bne inactive
 ldr r2,[r1,#0xe8]
 tst r2,#3
 bne inactive
 cmp r2,#0x02000000
 blo inactive
 ldr r3,=0x023ffffc
 cmp r2,r3
 bhi inactive
 ldr r2,[r2]
 tst r2,#0x200000
 beq inactive
 ldr r2,[r0,#0x258]
 cmp r2,#128
 bne inactive
 ldr r2,[r0,#0x1f8]
 tst r2,#3
 bne inactive
 cmp r2,#0x02000000
 blo inactive
 ldr r3,=0x023fff00
 cmp r2,r3
 bhi inactive
 ldr r3,[r2,#0x44]
 cmp r3,r1
 bne inactive
 ldr r2,[r2,#0x14]
 cmp r2,#45
 bne inactive
 mov r0,#1
 bx lr
inactive:
 mov r0,#0
 bx lr
