// Stateless Black air routing. Native movement, chain eligibility and victim credit.
 b animation
 b contact
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
 beq animation_out
 sub r0,r0,#1
 add r0,r0,r0,lsl #1
 ldr r1,=ROUTES
 add r1,r1,r0,lsl #2
 ldr r0,[r1]
 str r0,[sp,#0x4c]
 ldr r0,[r1,#4]
 str r0,[sp,#0x58]
 ldr r0,[r1,#8]
 str r0,[sp,#0x5c]
animation_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_ANIMATION

contact:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,[r3]
 cmp r0,#0x14
 beq contact_check
 cmp r0,#0x16
 bne contact_out
contact_check:
 mov r0,r2
 bl ram_ok
 cmp r0,#0
 bne contact_cell
 tst r2,#3
 bne contact_out
 ldr r0,=0x027e0000       // Native attacker cells can live on the DTCM stack.
 cmp r2,r0
 blo contact_out
 ldr r0,=0x027ffffc
 cmp r2,r0
 bhi contact_out
contact_cell:
 ldr r0,[r2]
 bl ram_ok
 cmp r0,#0
 beq contact_out
 ldr r0,[r2]
 ldr r0,[r0,#0x30]
 bl active
 cmp r0,#0
 beq contact_out
 ldr r12,[r3]
 cmp r12,#0x16
 bne contact_receiver
 cmp r0,#4
 bne contact_out
contact_receiver:
 adr r4,pop_hit          // Native dispatch still owns the contact and its credit.
contact_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_CONTACT

// ReceiveHit wrapper: a local info/contact copy cannot leak to the next victim.
pop_hit:
 push {r4-r8,lr}
 sub sp,sp,#0x80
 mov r4,r0
 mov r5,r1
 mov r6,r2
 mov r7,r3
 ldr r0,[sp,#0x98]
 str r0,[sp]
 mov r0,#0
copy_info:
 ldr r1,[r7,r0]
 add r2,sp,#0x10
 add r2,r2,r0
 str r1,[r2]
 add r0,r0,#4
 cmp r0,#0x40
 blo copy_info
 ldr r2,[r7,#16]
 mov r0,#0
copy_contact:
 ldr r1,[r2,r0]
 add r3,sp,#0x50
 add r12,r3,r0
 str r1,[r12]
 add r0,r0,#4
 cmp r0,#0x20
 blo copy_contact
 str r3,[sp,#0x20]
 ldr r8,[r7]
 cmp r8,#0x16
 moveq r8,#0x25
 ldr r0,[r5,#-8]
 ldr r1,=0x021301d0
 cmp r0,r1
 bne pop_native
 ldr r0,[r5,#0x38]
 ldr r1,=BOSS_CONFIG
 cmp r0,r1
 moveq r8,#4
pop_native:
 str r8,[sp,#0x10]
 str r8,[sp,#0x64]
 mov r0,r4
 mov r1,r5
 mov r2,r6
 add r3,sp,#0x10
 ldr r12,[r5]
 ldr r12,[r12,#0x40]
 blx r12
 ldr r0,[r4]
 cmp r0,#1
 bne pop_done
 cmp r8,#4
 beq pop_done
 mov r8,#4                 // A refused launch gets one native stagger attempt.
 b pop_native
pop_done:
 add sp,sp,#0x80
 pop {r4-r8,pc}

evade:                      // r4 controller, r0 actor at the native air blocker.
 push {r0-r3,r12,lr}
 sub sp,sp,#8
 mov r0,#0
 str r0,[sp,#4]
 ldr r0,[r4,#0x44]
 ldr r0,[r0,#0x30]
 bl active
 cmp r0,#0
 beq evade_out
 ldr r0,[r4,#0x44]
 ldr r0,[r0,#0x30]
 ldr r1,[r0,#0x1f8]
 cmp r1,r4
 bne evade_out
 mov r0,#3
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 beq evade_out
 ldr r0,[r4,#0x44]
 ldr r0,[r0,#0xe8]
 ldr r0,[r0]
 tst r0,#0x400
 bne evade_native
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34             // Without paid Air Dodge, R releases into native fall.
 mov r0,#19
 str r0,[sp,#4]
 b evade_out
evade_native:
 mvn r0,#0x80000000
 str r0,[sp,#4]
evade_out:
 ldr r0,[sp,#4]
 cmp r0,#0
 strne r0,[sp,#8]
 add sp,sp,#8
 pop {r0-r3,r12,lr}
 beq OLD_AIR
 pop {r4,pc}

active:                     // Current owned Black motion -> air action 1..4, else 0.
 push {r4-r6,lr}
 mov r4,r0
 bl ram_ok
 cmp r0,#0
 beq inactive
 ldr r5,[r4]
 mov r0,r5
 bl ram_ok
 cmp r0,#0
 beq inactive
 ldr r0,[r5]
 ldr r1,=0x0212e3f0
 cmp r0,r1
 bne inactive
 ldr r0,[r5,#0x30]
 cmp r0,r4
 bne inactive
 ldr r0,[r5,#0x34]
 cmp r0,#1
 bne inactive
 ldr r6,[r5,#0xe8]
 mov r0,r6
 bl ram_ok
 cmp r0,#0
 beq inactive
 ldr r0,[r6,#8]
 tst r0,#0x200000
 beq inactive
 ldr r6,[r4,#0x1f8]
 mov r0,r6
 bl ram_ok
 cmp r0,#0
 beq inactive
 ldr r0,[r6,#0x44]
 cmp r0,r5
 bne inactive
 ldr r0,[r6,#0x14]
 cmp r0,#51
 bne inactive
 ldr r0,[r4,#0x258]
 cmp r0,#1
 blo inactive
 cmp r0,#4
 popls {r4-r6,pc}
inactive:
 mov r0,#0
 pop {r4-r6,pc}

ram_ok:
 tst r0,#3
 bne ram_no
 cmp r0,#0x02000000
 blo ram_no
 ldr r1,=0x023ffc00
 cmp r0,r1
 movls r0,#1
 bxls lr
ram_no:
 mov r0,#0
 bx lr
