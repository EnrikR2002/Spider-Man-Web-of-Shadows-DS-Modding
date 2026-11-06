// Native Hammer Slam states 35/36 own movement, floor contact and credit.
 b animation
 b landing
 b radius
 b contact
 b think

animation:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 cmp r0,#0
 beq animation_out
 ldr r1,[sp,#0x4c]
 ldr r2,=NATIVE_DIVE
 cmp r1,r2
 ldrne r2,=NATIVE_LAND
 cmpne r1,r2
 bne animation_out
 mov r0,r4
 bl owned
 cmp r0,#0
 beq animation_out
 ldr r0,[r2,#0x14]
 ldr r3,=STATE
 ldr r1,[r3]
 cmp r0,#35
 bne animation_land
 ldr r0,[r4,#0x258]
 cmp r0,#73
 bne animation_out
 cmp r1,r4
 ldreq r0,[r4,#0x254]
 cmpeq r0,#73
 beq animation_dive
 ldr r0,[r4,#0x80]
 ldr r1,[r4,#0x164]
 add r0,r0,r1
 str r4,[r3]
 str r0,[r3,#4]
 mvn r0,#0
 str r0,[r3,#8]
animation_dive:
 ldr r0,=DIVE_SCA
 b animation_set
animation_land:
 cmp r0,#36
 cmpeq r1,r4
 bne animation_out
 ldr r0,[r4,#0x258]
 cmp r0,#74
 bne animation_out
 ldr r0,[r3,#8]
 cmp r0,#0
 blt animation_out
 ldr r0,=LAND_SCA
animation_set:
 str r0,[sp,#0x4c]       // Caller action record SCA at original SP+0x2c.
animation_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_ANIMATION

landing:
 push {r0-r3,r12,lr}
 ldr r0,[r4,#0x44]
 ldr r0,[r0,#0x30]
 bl owned
 cmp r0,#0
 beq landing_out
 cmp r2,r4
 bne landing_out
 ldr r3,[r4,#0x18]
 cmp r3,#35
 bne landing_out
 ldr r3,=STATE
 ldr r0,[r3]
 ldr r1,[r1,#0x30]
 cmp r0,r1
 bne landing_out
 ldr r2,[r1,#0x2ac]
 cmp r2,#0
 ble landing_out
 ldr r0,[r3,#4]
 ldr r2,[r1,#0x80]
 ldr r1,[r1,#0x164]
 sub r0,r0,r2
 sub r0,r0,r1
 subs r0,r0,#0x1b000
 movlt r0,#0
 cmp r0,#0x36000
 movgt r0,#0x36000
 mov r2,#76
 mul r1,r0,r2
 mov r2,r1,lsr #12
 cmp r2,#0x1000
 movgt r2,#0x1000
 str r2,[r3,#8]
 ldr r1,[sp,#8]
 add r1,r1,r2,lsr #1    // Native vertical shake, with at most half a unit added.
 str r1,[sp,#8]
landing_out:
 pop {r0-r3,r12,lr}
 b 0x0207e5cc

radius:
 push {r0-r3,r12,lr}
 mov r0,r4
 bl impact_power
 cmp r0,#0
 ble radius_out
 ldr r2,[sp,#16]
 mul r1,r2,r0
 add r2,r2,r1,lsr #11
 str r2,[sp,#16]
 mul r1,r5,r0
 add r5,r5,r1,lsr #11   // Expand horizontal extents, retaining the center and vertical reach.
radius_out:
 pop {r0-r3,r12,lr}
 str r12,[sp,#0xa8]
 b 0x02071130

contact:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,[r3]
 cmp r0,#0x10
 cmpne r0,#0x12
 bne contact_out
 ldr r0,[r2]
 cmp r0,#0
 beq contact_out
 ldr r12,[r0,#0x30]
 ldr r1,=STATE
 ldr r3,[r1,#12]
 cmp r3,#0
 beq contact_apply
 cmp r3,r12
 bne contact_apply
 ldr r1,[r0]
 ldr r2,=0x0212e3f0
 cmp r1,r2
 beq contact_released
contact_apply:
 mov r0,r12
 bl impact_power
 cmp r0,#0
 adrge r4,receive
contact_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_CONTACT
contact_released:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 mov r2,#1
 str r2,[r0]             // R was consumed before this native slam sample reached dispatch.
 b 0x0207862c

receive:
 push {r4-r8,lr}
 ldr r12,[r1,#-8]
 ldr r8,=0x021301d0
 cmp r12,r8
 beq receive_enemy
 ldr r8,=0x0212ce38
 cmp r12,r8
 bne receive_original
 b receive_heavy
receive_enemy:
 ldr r12,[r1,#0x38]
 ldr r8,=BOSS_CONFIG
 cmp r12,r8
 beq receive_heavy
 ldr r12,=STATE
 ldr r12,[r12,#8]
 cmp r12,#0
 beq receive_original
 ldr r8,[r3]
 b receive_copy
receive_heavy:
 mov r8,#4
receive_copy:
 sub sp,sp,#0x50
 mov r4,r0
 mov r5,r1
 mov r6,r2
 mov r7,r3
 ldr r0,[sp,#0x68]
 str r0,[sp]             // Keep the native fifth argument, the HP value.
 mov r0,#16
 mov r2,r7
 add r3,sp,#0x10
copy_info:
 ldr r1,[r2],#4
 str r1,[r3],#4
 subs r0,r0,#1
 bne copy_info
 str r8,[sp,#0x10]
 ldr r1,=STATE
 ldr r0,[sp,#0x14]
 ldr r1,[r1,#8]
 mul r2,r0,r1
 add r0,r0,r2,lsr #13   // Up to 50 percent more reaction strength.
 str r0,[sp,#0x14]
 mov r0,r4
 mov r1,r5
 mov r2,r6
 add r3,sp,#0x10
 ldr r12,[r5]
 ldr r12,[r12,#0x40]
 blx r12
 add sp,sp,#0x50
 pop {r4-r8,pc}
receive_original:
 ldr r12,[r1]
 ldr r12,[r12,#0x40]
 pop {r4-r8,lr}
 bx r12

think:
 push {r0-r3,r12,lr}
 ldr r3,=STATE
 ldr r2,[r3,#12]
 cmp r2,#0
 beq think_active
 ldr r1,[r0]
 ldr r12,=0x021352a4
 cmp r1,r12
 moveq r1,#0
 streq r1,[r3,#12]
think_active:
 ldr r2,[r3]
 cmp r2,#0
 beq think_native
 ldr r1,[r0,#0x44]
 ldr r0,[r1,#0x30]
 cmp r0,r2
 bne think_clear
 bl owned
 cmp r0,#0
 beq think_clear
 ldr r3,[sp]
 cmp r2,r3
 bne think_clear
 ldr r1,[r2,#0x14]
 cmp r1,#35
 cmpne r1,#36
 bne think_clear
 sub sp,sp,#8
 tst r0,#0x400
 moveq r0,#19
 movne r0,#52
 cmp r1,#36
 moveq r0,#53
 str r0,[sp,#4]
 mov r0,#3
 str r0,[sp]
 mov r1,sp
 add r0,r2,#0x28
 bl 0x020cff0c
 cmp r0,#0
 beq think_no_r
 ldr r0,[sp,#4]
 cmp r0,#53
 bne think_consume
 ldr r0,[sp,#8]
 ldr r1,[r0,#0x44]
 ldr r1,[r1,#0xe8]
 ldr r1,[r1]
 tst r1,#0x200
 beq think_consume
 bl 0x020c9fe8
 cmp r0,#0
 movne r0,#54
 strne r0,[sp,#4]
think_consume:
 ldr r0,[sp,#8]
 add r0,r0,#0x28
 mov r1,sp
 bl 0x020cfc34
 ldr r1,=STATE
 ldr r3,[sp,#4]
 cmp r3,#53
 cmpne r3,#54
 ldreq r2,[r1]
 streq r2,[r1,#12]
 mov r0,#0
 str r0,[r1]
 mov r0,r3
 add sp,sp,#12
 pop {r1-r3,r12,pc}
think_no_r:
 add sp,sp,#8
 b think_native
think_clear:
 ldr r3,=STATE
 mov r0,#0
 str r0,[r3]
think_native:
 pop {r0-r3,r12,lr}
 b OLD_THINK

impact_power:             // -1 outside the owned landing, otherwise Q12 bonus.
 ldr r1,=STATE
 ldr r2,[r1]
 cmp r2,r0
 bne impact_inactive
 cmp r2,#0
 beq impact_inactive
 ldr r2,[r0,#0x254]
 cmp r2,#74
 bne impact_inactive
 push {r4,lr}
 mov r4,r1
 bl owned
 cmp r0,#0
 beq impact_not_owned
 ldr r2,[r2,#0x14]
 cmp r2,#36
 ldreq r0,[r4,#8]
 popeq {r4,pc}
impact_not_owned:
 mvn r0,#0
 pop {r4,pc}
impact_inactive:
 mvn r0,#0
 bx lr

owned:                    // Motion -> ability word, actor in r1, controller in r2.
 mov r12,r0
 ldr r3,=0x023ffc00
 tst r12,#3
 bne not_owned
 cmp r12,#0x02000000
 cmpcs r3,r12
 bcc not_owned
 ldr r1,[r12]
 tst r1,#3
 bne not_owned
 cmp r1,#0x02000000
 cmpcs r3,r1
 bcc not_owned
 ldr r2,[r1]
 ldr r3,=0x0212e3f0
 cmp r2,r3
 bne not_owned
 ldr r2,[r1,#0x30]
 cmp r2,r12
 ldreq r2,[r1,#0x34]
 cmpeq r2,#1
 bne not_owned
 ldr r2,[r12,#0x1f8]
 tst r2,#3
 bne not_owned
 ldr r3,=0x023ffc00
 cmp r2,#0x02000000
 cmpcs r3,r2
 bcc not_owned
 ldr r0,[r2]
 ldr r12,=0x021352a4
 cmp r0,r12
 ldreq r0,[r2,#0x44]
 cmpeq r0,r1
 bne not_owned
 ldr r12,[r1,#0xe8]
 tst r12,#3
 bne not_owned
 cmp r12,#0x02000000
 cmpcs r3,r12
 bcc not_owned
 ldr r0,[r12]
 tst r0,#0x400000
 bxne lr
not_owned:
 mov r0,#0
 bx lr
.ltorg
