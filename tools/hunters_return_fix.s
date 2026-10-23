 b contact
 b next_victim
 b update_owner

// Native dispatch copies r0-r2 to SP+80..88, then never reads those copies.
// Keep restoration data there until this victim's native hit credit is finished.
contact:
 push {r0-r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 mov r0,#0
 str r0,[sp,#0xc0]
 ldr r4,[r3]
 cmp r4,#0x20
 bne contact_out
 mov r6,r3
 ldr r5,[r3,#16]
 tst r5,#3
 bne contact_out
 cmp r5,#0x02000000
 blo contact_out
 ldr r0,=0x023fffe0
 cmp r5,r0
 bls contact_valid
 ldr r0,=0x027e0000
 cmp r5,r0
 blo contact_out
 ldr r0,=0x027fffe0
 cmp r5,r0
 bhi contact_out
contact_valid:
 ldr r7,[r5,#20]
 ldr r0,[r2]
 sub r1,r1,#8
 mov r2,r6
 bl OLD_RAKE
 ldr r0,[r6]
 cmp r0,r4
 beq contact_out
 str r4,[sp,#0xc0]
 str r5,[sp,#0xc4]
 str r7,[sp,#0xc8]
contact_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r12,lr}
 b OLD_CONTACT

// Also reached for victims skipped before ReceiveHit: their saved r0 is a
// pointer, never the 0x20 conversion marker. Nested dispatches have own frames.
next_victim:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,[sp,#0xa0]
 cmp r0,#0x20
 bne next_out
 str r0,[sp,#0xac]
 ldr r1,[sp,#0xa4]
 ldr r2,[sp,#0xa8]
 str r2,[r1,#20]
 mov r0,#0
 str r0,[sp,#0xa0]
next_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 ldr r0,[sp,#4]
 b 0x02078670

update_owner:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,[r4]
 ldr r1,=0x0212e3f0
 cmp r0,r1
 bne update_out
 ldr r0,=STATE
 ldr r1,[r0]
 cmp r1,r4
 beq update_out
 mov r1,#0
 str r1,[r0]
 str r1,[r0,#20]
update_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_UPDATE
