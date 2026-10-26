// Light targets settle near three units in front; retain the native vertical launch.
front:
 push {r0-r3,r12,lr}
 cmp r8,#0x25
 bne front_done
 ldr r0,[r4]
 cmp r0,#1
 beq front_done
 ldr r0,[r6,#0x30]
 ldr r1,[r0,#0x7c]
 ldr r2,[r0,#0x160]
 add r1,r1,r2
 sub r0,r5,#8
 ldr r0,[r0,#0x30]
 ldr r2,[r0,#0x7c]
 ldr r3,[r0,#0x160]
 add r2,r2,r3
 subs r2,r2,r1
 mov r3,#0x3000
 cmp r2,#0
 rsblt r3,r3,#0
 sub r2,r3,r2
 mov r2,r2,asr #5
 mov r3,#0x600
 cmp r2,r3
 movgt r2,r3
 rsb r3,r3,#0
 cmp r2,r3
 movlt r2,r3
 sub r0,r5,#8
 str r2,[r0,#0x18]
front_done:
 pop {r0-r3,r12,lr}
 ldr r0,[r4]
 ldr r12,=CONTINUATION
 bx r12
 .ltorg
