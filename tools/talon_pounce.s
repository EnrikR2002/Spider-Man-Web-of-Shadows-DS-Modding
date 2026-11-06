// Use the native Y charge gate and air collision, with a private player action record.
 b begin
 b think
 b animation
 b update
 b contact

// State words: motion, controller, room, phase (coil/quick/low/high),
// elapsed updates, original Y action, facing, first accepted hit, heavy hit.
begin:                      // Native state46 update, r8 controller.
 push {r0-r7,r12,lr}
 ldr r6,[r8,#0x44]
 ldr r7,[r6,#0x30]
 mov r0,r7
 bl owned
 cmp r0,#0
 beq begin_native
 cmp r2,r8
 bne begin_native
 ldr r5,=STATE
 str r7,[r5]
 str r8,[r5,#4]
 ldr r3,[r6,#0xe8]
 ldr r3,[r3,#-12]
 str r3,[r5,#8]
 tst r0,#0x4000000
 moveq r0,#1
 movne r0,#2
 str r0,[r5,#12]
 mov r0,#1
 str r0,[r5,#16]
 mov r0,#0
 strb r0,[r6,#0x28]
 str r0,[r5,#28]
 str r0,[r5,#32]
 ldr r0,[r7,#0x258]
 str r0,[r5,#20]
 bl request
 pop {r0-r7,r12,lr}
 b 0x020c361c
begin_native:
 pop {r0-r7,r12,lr}
 ldrsb r0,[r8,#0x8f]
 b 0x020c3378

think:
 push {r4-r8,lr}
 sub sp,sp,#8
 mov r4,r0
 ldr r5,=STATE
 ldr r0,[r5,#12]
 cmp r0,#0
 beq think_native
 ldr r6,[r4,#0x44]
 ldr r7,[r6,#0x30]
 mov r0,r7
 bl active
 cmp r0,#0
 beq think_clear
 cmp r2,r4
 bne think_clear
 mov r8,r0
 mov r0,#3
 bl peek
 cmp r0,#0
 bne think_evade
 mov r0,#4
 bl peek
 cmp r0,#0
 bne think_release
 cmp r8,#2
 bhi think_flight
 mov r0,#5
 bl peek
 cmp r0,#0
 bne think_release
 mov r0,#2
 bl peek
 cmp r0,#0
 bne think_release
 ldr r0,=0x02145a48
 ldrh r2,[r0,#2]
 ldr r1,[r5,#16]
 tst r2,#0x800
 bne think_hold
 cmp r8,#2
 moveq r0,#8
 movne r0,#16
 cmp r1,r0
 bhs think_launch
 bl resume_coil
 mov r0,#46
 b think_out
think_hold:
 cmp r1,#16
 addlo r1,r1,#1
 strlo r1,[r5,#16]
 mov r0,#46
 b think_out
think_launch:
 tst r2,#0x40
 moveq r0,#3
 movne r0,#4
 str r0,[r5,#12]
 ldr r0,[r7,#0x180]
 and r2,r2,#0x30
 cmp r2,#0x20
 moveq r0,#0
 cmp r2,#0x10
 moveq r0,#1
 str r0,[r5,#24]
 mov r0,#0
 str r0,[r5,#16]
 str r0,[r4,#0x80]
 strb r0,[r4,#0x90]
 mov r0,#1
 bl request
 mov r0,#15                 // Native takeoff clears ground contact before the air strike.
 b think_out

think_flight:
 ldr r0,[r5,#16]
 cmp r0,#2
 bls flight_stay
 ldr r1,[r7,#0x2ac]
 cmp r1,#0
 bgt flight_land
 cmp r0,#14
 bhs flight_fall
 cmp r8,#4
 bne flight_stay
 ldr r1,[r6,#0xe8]
 ldr r1,[r1,#8]
 tst r1,#0x1000000
 beq flight_combo
 ldr r0,=BOARD_STATE
 ldr r1,[r0,#24]
 cmp r1,#0
 ldreq r1,[r0,#56]
 cmpeq r1,#0
 bne flight_combo
 ldr r1,=0x02145a48
 ldrh r1,[r1,#2]
 ldr r2,[r5,#24]
 cmp r2,#0
 moveq r2,#0x20
 movne r2,#0x10
 tst r1,r2
 beq flight_combo
 mov r0,r6
 mov r1,#0
 bl BOARD_TARGET
 cmp r0,#0
 beq flight_combo
 ldr r1,[r0,#0x30]
 mov r0,r7
 bl clear_path
 cmp r0,#0
 bne think_clear            // The native Boarding entry owns the actual latch.
flight_combo:
 ldr r0,[r5,#28]
 cmp r0,#0
 beq flight_stay
 ldr r1,[r5,#16]
 sub r1,r1,r0
 cmp r1,#2
 blo flight_stay
 mov r0,#1
 bl peek
 cmp r0,#0
 bne flight_rake
flight_stay:
 ldr r0,[r4,#0x14]
 cmp r0,#15
 ldreq r1,[r7,#0x2ac]
 cmpeq r1,#0
 bgt think_out
 mov r0,#51
 b think_out
flight_rake:
 mov r0,#1
 bl consume
 mov r0,#0
 str r0,[r5,#12]
 str r0,[r4,#0x80]
 mov r0,#1
 strb r0,[r4,#4]
 bl request                 // Re-enter the native air string with a fresh clip lookup.
 mov r0,#51
 b think_out
flight_land:
 mov r8,#24
 b flight_end
flight_fall:
 mov r8,#19
flight_end:
 mov r0,#0
 str r0,[r5,#12]
 str r0,[r6,#0x18]
 mov r0,r8
 b think_out

think_evade:
 ldr r0,[r7,#0x2ac]
 cmp r0,#0
 bgt evade_ground
 ldr r0,[r6,#0xe8]
 ldr r0,[r0]
 tst r0,#0x400
 moveq r8,#19
 movne r8,#52
 b evade_consume
evade_ground:
 mov r8,#53
 ldr r0,[r6,#0xe8]
 ldr r0,[r0]
 tst r0,#0x200
 beq evade_consume
 mov r0,r4
 bl 0x020c9fe8
 cmp r0,#0
 movne r8,#54
evade_consume:
 mov r0,#3
 bl consume
 b flight_end

think_release:
 cmp r8,#2
 bls release_coil
 b think_clear
release_coil:
 bl resume_coil
 mov r0,#1
 strb r0,[r6,#0x28]
 b think_native
think_clear:
 mov r0,#0
 str r0,[r5,#12]
think_native:
 mov r0,r4
 add sp,sp,#8
 pop {r4-r8,lr}
 b OLD_THINK
think_out:
 add sp,sp,#8
 pop {r4-r8,pc}

resume_coil:
 mov r0,#0
 str r0,[r5,#12]
 ldr r0,[r5,#20]
request:
 str r0,[r7,#0x258]
 ldr r0,[r7,#0x2fc]
 orr r0,r0,#2
 str r0,[r7,#0x2fc]
 bx lr

peek:
 push {r0,lr}
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 pop {r1,pc}
consume:
 push {r0,lr}
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34
 pop {r1,pc}

animation:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 cmp r0,#0
 beq animation_native
 mov r0,r4
 bl active
 cmp r0,#0
 beq animation_native
 ldr r1,[r4,#0x258]
 cmp r0,#2
 ldrle r2,=STATE
 ldrle r2,[r2,#20]
 movgt r2,#1
 cmp r1,r2
 bne animation_native
 sub r0,r0,#1
 add r0,r0,r0,lsl #1
 adr r1,clips
 add r0,r1,r0,lsl #2
 ldmia r0,{r1-r3}
 str r1,[sp,#0x4c]
 str r2,[sp,#0x58]
 str r3,[sp,#0x5c]
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 cmp r0,#0
 b 0x02070488
animation_native:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_ANIMATION
clips:
 .word COIL_SCA,COIL_GMB,COIL_GAB
 .word QUICK_SCA,QUICK_GMB,QUICK_GAB
 .word LOW_SCA,LOW_GMB,LOW_GAB
 .word HIGH_SCA,HIGH_GMB,HIGH_GAB

update:                     // Native controller has run, native motion still lies ahead.
 push {r0-r7,r12,lr}
 mrs r5,cpsr
 ldr r6,=STATE
 ldr r7,[r6]
 ldr r0,[r6,#12]
 cmp r0,#3
 blo update_out
 ldr r1,[r4,#0x30]
 cmp r7,r1
 bne update_out
 mov r0,r7
 bl active
 cmp r0,#3
 blo update_out
 ldr r2,[r6,#16]
 ldr r3,[r6,#24]
 str r3,[r7,#0x180]
 cmp r2,#0
 bne update_speed
 cmp r0,#4
 moveq r12,#0x2900
 movne r12,#0x1380
 str r12,[r4,#0x1c]
 mov r0,#1
 bl request
 ldr r0,[r6,#12]
update_speed:
 cmp r2,#14
 bhs update_out
 add r12,r2,#1
 str r12,[r6,#16]
 adr r12,speeds
 ldr r12,[r12,r2,lsl #2]
 cmp r0,#4
 bne update_brake
 sub r12,r12,r12,lsr #2
 ldr r1,[r6,#32]
 cmp r1,#0
 beq update_direction       // Follow the rising juggle until the player's next Y.
update_brake:
 ldr r0,[r6,#28]
 cmp r0,#0
 beq update_direction
 sub r0,r2,r0
 cmp r0,#2
 movlo r12,r12,lsr #2
 movhs r12,#0
update_direction:
 cmp r3,#0
 rsbeq r12,r12,#0
 str r12,[r4,#0x18]
update_out:
 msr cpsr_f,r5
 pop {r0-r7,r12,lr}
 b OLD_UPDATE
speeds:
 .word 0x0d00,0x1c00,0x2480,0x2480,0x2480,0x2480,0x2480
 .word 0x2480,0x2480,0x2480,0x2480,0x1800,0x0c00,0x0400

contact:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,[r2]
 bl ram_ok
 cmp r0,#0
 beq contact_native
 ldr r0,[r2]
 ldr r1,[r0]
 ldr r3,=0x0212e3f0
 cmp r1,r3
 bne contact_native
 ldr r0,[r0,#0x30]
 bl ram_ok
 cmp r0,#0
 beq contact_native
 ldr r0,[r2]
 ldr r0,[r0,#0x30]
 ldr r1,[r0,#0x230]
 ldr r3,=LOW_GMB
 cmp r1,r3
 ldrne r3,=HIGH_GMB
 cmpne r1,r3
 bne contact_native
 bl active
 cmp r0,#3
 blo contact_ignore
 ldr r0,=STATE
 ldr r0,[r0,#28]
 cmp r0,#0
 bne contact_ignore
 ldr r0,[r1,#0x30]
 ldr r1,[sp,#12]
 ldr r1,[r1,#0x28]
 bl clear_path
 cmp r0,#0
 beq contact_ignore
 adr r4,receive
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b POUNCE_CONTACT           // Skip Sky Rake's receiver for this private action only.
contact_ignore:             // The old GMB can still dispatch once after a cancel.
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 mov r2,#1
 str r2,[r0]
 b 0x0207862c
contact_native:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_CONTACT

clear_path:                 // Native BSP sweep of a point from torso to torso.
 push {r4-r6,lr}
 sub sp,sp,#0x40
 mov r4,r0
 mov r5,r1
 mov r0,r5
 bl ram_ok
 cmp r0,#0
 beq path_out
 ldr r6,=0x02145c3c
 ldr r6,[r6]
 mov r0,r6
 bl ram_ok
 cmp r0,#0
 beq path_out
 ldr r0,[r6]
 bl ram_ok
 cmp r0,#0
 beq path_out
 ldr r0,[r4,#0x7c]
 ldr r1,[r4,#0x160]
 add r0,r0,r1
 str r0,[sp,#0x18]
 str r0,[sp,#0x1c]
 ldr r1,[r5,#0x7c]
 ldr r2,[r5,#0x160]
 add r1,r1,r2
 sub r1,r1,r0
 str r1,[sp,#0x30]
 ldr r0,[r4,#0x80]
 ldr r1,[r4,#0x164]
 add r0,r0,r1
 add r0,r0,#0x2000
 str r0,[sp,#0x20]
 str r0,[sp,#0x24]
 ldr r1,[r5,#0x80]
 ldr r2,[r5,#0x164]
 add r1,r1,r2
 add r1,r1,#0x2000
 sub r1,r1,r0
 str r1,[sp,#0x34]
 mov r0,#0
 str r0,[sp,#0x28]
 str r0,[sp,#0x2c]
 str r0,[sp,#0x38]
 mov r0,sp
 mov r1,r6
 add r2,sp,#0x18
 add r3,sp,#0x30
 bl 0x02029240
 ldrh r0,[sp,#0x10]
 cmp r0,#0x2000
 moveq r0,#1
 movne r0,#0
path_out:
 add sp,sp,#0x40
 pop {r4-r6,pc}

receive:
 push {r4-r10,lr}
 sub sp,sp,#0x70
 mov r4,r0
 mov r5,r1
 mov r6,r2
 mov r7,r3
 mov r8,#0x14
 mov r9,#0
 ldr r0,[sp,#0x90]
 str r0,[sp]                // The native fifth argument is HP damage.
 ldr r0,[r5,#-8]
 ldr r1,=0x0212ce38
 cmp r0,r1
 beq receive_heavy
 ldr r1,=0x021301d0
 cmp r0,r1
 bne receive_copy
 ldr r0,[r5,#0x38]
 ldr r1,=BOSS_CONFIG
 cmp r0,r1
 beq receive_heavy
 ldr r0,[r5,#0x28]
 bl ram_ok
 cmp r0,#0
 beq receive_copy
 ldr r0,[r5,#0x28]
 ldr r0,[r0,#0x2ac]
 cmp r0,#0
 movgt r8,#0x1f
 b receive_copy
receive_heavy:
 mov r8,#4
 mov r9,#1
receive_copy:
 mov r0,#0
 ldr r10,[r7,#16]
copy_info:
 ldr r1,[r7,r0]
 add r2,sp,#0x10
 add r2,r2,r0
 str r1,[r2]
 add r0,r0,#4
 cmp r0,#0x40
 blo copy_info
 mov r0,#0
copy_contact:
 ldr r1,[r10,r0]
 add r2,sp,#0x50
 add r3,r2,r0
 str r1,[r3]
 add r0,r0,#4
 cmp r0,#0x20
 blo copy_contact
 str r2,[sp,#0x20]
receive_native:
 str r8,[sp,#0x10]
 str r8,[sp,#0x64]
 mov r0,r4
 mov r1,r5
 mov r2,r6
 add r3,sp,#0x10
 ldr r12,[r5]
 ldr r12,[r12,#0x40]
 blx r12
 ldr r1,[r4]
 cmp r1,#1
 bne receive_record
 cmp r8,#4
 beq receive_record
 mov r8,#4
 b receive_native
receive_record:
 cmp r1,#4
 bne receive_done
 ldr r1,=STATE
 ldr r2,[r1,#16]
 str r2,[r1,#28]
 str r9,[r1,#32]
receive_done:
 add sp,sp,#0x70
 pop {r4-r10,pc}

active:                     // Motion -> private phase, with current actor and controller.
 push {r4-r5,lr}
 sub sp,sp,#4
 ldr r4,=STATE
 ldr r5,[r4,#12]
 cmp r5,#0
 beq active_no
 ldr r12,[r4]
 cmp r0,r12
 bne active_no
 bl owned
 cmp r0,#0
 beq active_no
 ldr r12,[r4,#4]
 cmp r2,r12
 bne active_no
 ldr r0,[r1,#0xe8]
 ldr r0,[r0,#-12]
 ldr r12,[r4,#8]
 cmp r0,r12
 bne active_no
 ldr r0,[r2,#0x14]
 cmp r5,#2
 bhi active_air
 cmp r0,#46
 b active_match
active_air:
 cmp r0,#15
 cmpne r0,#51
active_match:
 moveq r0,r5
 beq active_out
active_no:
 mov r0,#0
active_out:
 add sp,sp,#4
 pop {r4-r5,pc}

owned:                      // Motion -> ability word, reciprocal actor and controller.
 push {r4,r5,r12,lr}
 mov r4,r0
 bl ram_ok
 cmp r0,#0
 beq owned_no
 ldr r5,[r4]
 mov r0,r5
 bl ram_ok
 cmp r0,#0
 beq owned_no
 ldr r0,[r5]
 ldr r3,=0x0212e3f0
 cmp r0,r3
 ldreq r0,[r5,#0x30]
 cmpeq r0,r4
 ldreq r0,[r5,#0x34]
 cmpeq r0,#1
 bne owned_no
 ldr r2,[r4,#0x1f8]
 mov r0,r2
 bl ram_ok
 cmp r0,#0
 beq owned_no
 ldr r0,[r2]
 ldr r3,=0x021352a4
 cmp r0,r3
 ldreq r0,[r2,#0x44]
 cmpeq r0,r5
 bne owned_no
 ldr r0,[r5,#0xe8]
 bl ram_ok
 cmp r0,#0
 beq owned_no
 ldr r0,[r5,#0xe8]
 ldr r0,[r0]
 tst r0,#0x2000000
 movne r1,r5
 popne {r4,r5,r12,pc}
owned_no:
 mov r0,#0
 pop {r4,r5,r12,pc}
ram_ok:
 tst r0,#3
 bne ram_no
 ldr r3,=0x0200000c
 cmp r0,r3
 ldrhs r3,=0x023ffc00
 cmphs r3,r0
 movhs r0,#1
 bxhs lr
ram_no:
 mov r0,#0
 bx lr
.ltorg
