// Private purchased-Black boss ride; only Miguel receives movement writes.
 b think
 b animation
 b update_entry
 b effect

think:
 push {r4-r8,lr}
 sub sp,sp,#8
 mov r4,r0
 ldr r6,[r4,#0x44]
 ldr r5,lit1_state
 mov r0,r6
 bl owned
 cmp r0,#0
 beq think_native
 ldr r7,[r6,#0x30]
 ldr r0,[r7,#0x1f8]
 cmp r0,r4
 bne think_native
 ldr r0,[r5,#24]
 cmp r0,#0
 beq think_start
 mov r0,r6
 bl active
 cmp r0,#0
 beq think_native
 mov r0,#3
 bl peek
 cmp r0,#0
 bne think_cancel
 mov r0,#4
 bl peek
 cmp r0,#0
 bne think_release
 ldr r0,[r5,#24]
 cmp r0,#2
 bne think_stay
 mov r0,#5
 bl peek
 cmp r0,#0
 beq think_y
 mov r0,#5
 bl consume
 mov r0,#4
 bl phase
 b think_stay
think_y:
 mov r0,#1
 bl peek
 cmp r0,#0
 beq think_stay
 mov r0,#1
 bl consume
 mov r0,#3
 bl phase
think_stay:
 mov r0,#51
 b think_out
think_cancel:
 bl cleanup
 ldr r0,[r6,#0xe8]
 ldr r0,[r0]
 tst r0,#0x400
 bne think_native
 mov r0,#3
 bl consume
 mov r0,#19
 b think_out
think_release:
 bl cleanup
 b think_native
think_start:
 ldr r0,lit1_pad
 ldrh r8,[r0,#2]
 tst r8,#0x30
 moveq r0,#0
 streq r0,[r5,#56]
 beq think_native
 ldr r0,[r5,#56]
 cmp r0,#0
 bne think_native
 mov r0,#3
 bl peek
 cmp r0,#0
 bne think_native
 mov r0,#4
 bl peek
 cmp r0,#0
 bne think_native
 ldr r0,[r4,#0x14]
 cmp r0,#15
 cmpne r0,#19
 cmpne r0,#51
 beq think_jump
 ldr r0,lit1_yank
 ldr r1,[r0]
 cmp r1,r6
 bne think_mini_zip
 ldr r1,[r0,#24]
 cmp r1,#0
 beq think_mini_zip
 ldr r1,[r0,#56]
 cmp r1,#0
 beq think_native
 mov r0,r6
 mov r1,#0
 bl select_target
 cmp r0,#0
 beq think_native
 mov r8,r0
 bl release_yank
 b think_latch
think_mini_zip:
 ldr r0,[r4,#0x14]
 cmp r0,#6
 bhi think_native
 ldr r0,[r4,#0x24]
 cmp r0,#5
 blo think_native
 cmp r0,#7
 bhi think_native
 ldr r0,[r6,#0xe8]
 ldr r0,[r0,#8]
 tst r0,#0x80000
 beq think_native
 mov r0,#5
 bl peek
 cmp r0,#0
 beq think_native
 mov r0,r6
 mov r1,#1
 bl select_target
 cmp r0,#0
 beq think_native
 mov r8,r0
 mov r0,#5
 bl consume
 bl begin
 mov r0,r6
 mov r1,r8
 bl line_make
 mov r0,#6
 bl phase
 b think_enter
think_jump:
 ldr r0,[r7,#0x2ac]
 cmp r0,#0
 bgt think_native
 ldr r0,lit1_meteor
 ldr r0,[r0,#24]
 cmp r0,#0
 bne think_native
 ldr r0,lit1_reel
 ldr r0,[r0,#24]
 cmp r0,#0
 bne think_native
 mov r0,r6
 mov r1,#0
 bl select_target
 cmp r0,#0
 beq think_native
 mov r8,r0
think_latch:
 bl begin
 mov r0,#1
 bl phase
think_enter:
 mov r0,#1
 strb r0,[r4,#4]
 mov r0,#0
 str r0,[r4,#0x80]
 strb r0,[r4,#0x90]
 mov r0,#51
 b think_out
think_native:
 mov r0,r4
 add sp,sp,#8
 pop {r4-r8,lr}
 b OLD_THINK
think_out:
 add sp,sp,#8
 pop {r4-r8,pc}

peek:
 push {r2,lr}
 sub sp,sp,#8
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 add sp,sp,#8
 pop {r2,pc}
consume:
 push {r2,lr}
 sub sp,sp,#8
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34
 add sp,sp,#8
 pop {r2,pc}

begin:
 push {r4-r8,lr}
 str r6,[r5]
 str r4,[r5,#4]
 add r0,r5,#8
 add r1,r8,#4
 bl link
 add r0,r5,#112
 add r1,r6,#4
 bl link
 ldr r0,[r8,#0x30]
 str r0,[r5,#16]
 ldr r1,[r0,#0x1f8]
 str r1,[r5,#136]
 ldr r0,[r8]
 str r0,[r5,#140]
 ldr r1,lit1_mini
 cmp r0,r1
 ldreq r0,[r8,#0xf8]
 ldrne r0,[r8,#0x40]
 str r0,[r5,#20]
 mov r0,r7
 bl SHARED_XY
 mov r4,r0
 ldr r0,[r8,#0x30]
 bl SHARED_XY
 cmp r4,r0
 movlt r0,#1
 movge r0,#0
 str r0,[r5,#88]
 ldr r0,[r6,#0xe8]
 ldr r0,[r0,#-12]
 str r0,[r5,#32]
 mov r0,#1
 str r0,[r5,#56]
 ldr r0,[r5,#60]
 add r0,r0,#1
 str r0,[r5,#60]
 mov r0,#0
 str r0,[r5,#36]
 str r0,[r5,#84]
 pop {r4-r8,pc}

phase:                      // r0 phase; r5 state, r7 player motion.
 str r0,[r5,#24]
 mov r0,#0
 str r0,[r5,#44]
 str r0,[r5,#52]
 str r0,[r5,#84]
 mov r0,#1
 str r0,[r7,#0x258]
 ldr r0,[r7,#0x2fc]
 orr r0,r0,#2
 str r0,[r7,#0x2fc]
 bx lr

active:
 push {r4-r6,lr}
 mov r4,r0
 bl owned
 cmp r0,#0
 beq active_out
 ldr r5,lit1_state
 ldr r0,[r5,#24]
 cmp r0,#0
 beq active_out
 ldr r0,[r5]
 cmp r0,r4
 bne inactive
 ldr r0,[r5,#112]
 add r1,r4,#4
 cmp r0,r1
 bne inactive
 ldr r6,[r4,#0x30]
 ldr r0,[r6,#0x1f8]
 ldr r1,[r5,#4]
 cmp r0,r1
 bne inactive
 ldr r0,[r0,#0x14]
 cmp r0,#51
 bne inactive
 ldr r0,[r4,#0xe8]
 ldr r0,[r0,#-12]
 ldr r1,[r5,#32]
 cmp r0,r1
 bne inactive
 mov r0,#1
 b active_out
inactive:
 mov r0,#0
active_out:
 pop {r4-r6,pc}
lit1_state: .word STATE
lit1_mini: .word 0x0212ce38
lit1_pad: .word 0x02145a48
lit1_yank: .word YANK_STATE
lit1_reel: .word REEL_STATE
lit1_meteor: .word METEOR_STATE

mini_ok:                    // Class-specific layout, never NormalEnemy HP offsets.
 push {r4-r6,lr}
 mov r4,r0
 bl SHARED_RAM_OK
 cmp r0,#0
 beq mini_no
 ldr r0,[r4]
 ldr r1,lit1_mini
 cmp r0,r1
 bne mini_no
 ldr r0,[r4,#8]
 ldr r1,=0x0212ce54
 cmp r0,r1
 bne mini_no
 ldr r0,[r4,#0xfc]
 cmp r0,#0
 ble mini_no
 ldr r1,[r4,#0x100]
 cmp r0,r1
 bhi mini_no
 ldr r0,[r4,#0xf4]
 cmp r0,#3
 bhi mini_no
 adr r1,mini_params
 ldr r1,[r1,r0,lsl #2]
 ldr r0,[r4,#0xf8]
 cmp r0,r1
 bne mini_no
 ldr r5,[r4,#0x30]
 mov r0,r5
 bl SHARED_RAM_OK
 cmp r0,#0
 beq mini_no
 ldr r0,[r5]
 cmp r0,r4
 bne mini_no
 ldr r6,[r5,#0x1f8]
 mov r0,r6
 bl SHARED_RAM_OK
 cmp r0,#0
 beq mini_no
 ldr r0,[r6]
 ldr r1,=0x02133c18
 cmp r0,r1
 bne mini_no
 ldr r0,[r6,#0x44]
 cmp r0,r4
 bne mini_no
 mov r0,r4
 pop {r4-r6,pc}
mini_no:
 mov r0,#0
 pop {r4-r6,pc}
mini_params:
 .word 0x0213754c,0x021375a0,0x02137648,0x0213769c

target_ok:
 push {r4-r7,lr}
 sub sp,sp,#4
 mov r4,r0
 bl mini_ok
 cmp r0,#0
 bne target_ok_out
 mov r0,r4
 bl 0x02152c68
 cmp r0,#0
 beq target_ok_out
 ldr r0,[r4,#0x44]
 cmp r0,#0
 ble target_no
 ldr r0,[r4,#0x30]
 ldr r1,[r0]
 cmp r1,r4
 bne target_no
 ldr r0,[r4,#0x40]
 ldr r1,=BOSS_CONFIG
 cmp r0,r1
 beq target_yes
 ldr r1,lit1_state
 ldr r2,[r1,#8]
 add r3,r4,#4
 cmp r2,r3
 bne target_scan_heavy
 ldr r2,[r1,#24]
 cmp r2,#0
 beq target_scan_heavy
 ldr r1,[r1,#20]
 cmp r0,r1
 beq target_yes
target_scan_heavy:
 ldr r6,lit1_yank
 mov r7,#5
target_heavy_loop:
 ldr r0,[r6,#8]
 add r1,r4,#4
 cmp r0,r1
 ldreq r0,[r6,#52]
 cmpeq r0,#1
 beq target_yes
 cmp r7,#5
 ldreq r6,=YANK_RECORDS
 addne r6,r6,#128
 subs r7,r7,#1
 bne target_heavy_loop
 b target_no
target_yes:
 mov r0,r4
 b target_ok_out
target_no:
 mov r0,#0
target_ok_out:
 add sp,sp,#4
 pop {r4-r7,pc}

target_live:
 push {r4,r6,lr}
 sub sp,sp,#4
 ldr r4,[r5,#8]
 cmp r4,#0
 beq live_no
 sub r4,r4,#4
 mov r0,r4
 bl target_ok
 cmp r0,#0
 beq live_no
 ldr r0,[r4,#0x30]
 ldr r1,[r5,#16]
 cmp r0,r1
 bne live_no
 ldr r0,[r0,#0x1f8]
 ldr r1,[r5,#136]
 cmp r0,r1
 bne live_no
 ldr r0,[r4]
 ldr r1,[r5,#140]
 cmp r0,r1
 bne live_no
 ldr r1,lit1_mini
 cmp r0,r1
 ldreq r0,[r4,#0xf8]
 ldrne r0,[r4,#0x40]
 ldr r1,[r5,#20]
 cmp r0,r1
 bne live_no
 mov r0,r4
 b live_out
live_no:
 mov r0,#0
live_out:
 add sp,sp,#4
 pop {r4,r6,pc}

attacking:                  // Native locomotion/hurt allowed; attack states release.
 ldr r1,[r0,#0x30]
 ldr r1,[r1,#0x1f8]
 ldr r1,[r1,#0x14]
 ldr r2,[r0]
 ldr r3,lit1_mini
 cmp r2,r3
 bne attacking_normal
 cmp r1,#9
 movls r0,#0
 bxls lr
 cmp r1,#15
 cmpne r1,#19
 cmpne r1,#24
 cmpne r1,#63
 cmpne r1,#65
 cmpne r1,#67
 cmpne r1,#68
 cmpne r1,#74
 cmpne r1,#75
 cmpne r1,#77
 cmpne r1,#79
 moveq r0,#0
 movne r0,#1
 bx lr
attacking_normal:
 cmp r1,#15
 cmpne r1,#16
 moveq r0,#1
 movne r0,#0
 bx lr

select_target:              // r1=1 permits distant mini-boss zip, 0 means nearby ride.
 push {r4-r11,lr}
 sub sp,sp,#20
 str r1,[sp,#4]
 mov r4,r0
 ldr r0,[r4,#0x30]
 bl SHARED_XY
 str r0,[sp,#8]
 str r1,[sp,#12]
 mov r5,#0
 ldr r6,=0x7fffffff
 ldr r7,=0x02154c40
 mov r8,#13
select_loop:
 cmp r8,#1
 ldrne r9,[r7]
 bne select_check
 ldr r0,lit1_state
 ldr r9,[r0,#192]
 cmp r9,#0
 beq select_next
 sub r9,r9,#4
 ldr r1,[r4,#0xe8]
 ldr r1,[r1,#-12]
 ldr r2,[r0,#216]
 cmp r1,r2
 bne select_next
 ldr r1,=0x02154c20
 ldr r1,[r1]
 ldr r2,[r0,#212]
 sub r1,r1,r2
 cmp r1,#2
 bhi select_next
select_check:
 mov r0,r9
 bl target_ok
 cmp r0,#0
 beq select_next
 mov r0,r9
 bl attacking
 cmp r0,#0
 bne select_next
 ldr r0,[r9,#0x30]
 bl SHARED_XY
 ldr r2,[sp,#8]
 subs r0,r0,r2
 ldr r2,lit1_pad
 ldrh r2,[r2,#2]
 mov r10,#1
 movlt r10,#0
 tst r2,#0x10
 beq select_left
 cmp r0,#0
 blt select_next
 b select_side
select_left:
 tst r2,#0x20
 beq select_next
 cmp r0,#0
 bgt select_next
select_side:
 cmp r0,#0
 rsblt r0,r0,#0
 ldr r2,[sp,#4]
 cmp r2,#0
 moveq r3,#0x9000
 movne r3,#0x2d000
 cmp r0,r3
 bgt select_next
 ldr r3,[sp,#12]
 sub r1,r1,r3
 cmp r1,#0
 rsblt r1,r1,#0
 cmp r1,#0x12000
 bgt select_next
 cmp r2,#0
 beq select_distance
 ldr r2,[r9]
 ldr r3,lit1_mini
 cmp r2,r3
 bne select_next
select_distance:
 add r0,r0,r1
 cmp r0,r6
 bhs select_next
 mov r6,r0
 mov r5,r9
select_next:
 add r7,r7,#16
 subs r8,r8,#1
 bne select_loop
 mov r0,r5
 add sp,sp,#20
 pop {r4-r11,pc}

animation:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 cmp r0,#0
 beq animation_out
 ldr r0,[r4]
 bl active
 cmp r0,#0
 beq animation_out
 ldr r0,lit1_state
 ldr r0,[r0,#24]
 cmp r0,#6
 moveq r0,#1
 sub r0,r0,#1
 add r0,r0,r0,lsl #1
 adr r1,clips
 ldr r2,[r4,#0x180]
 cmp r2,#0
 adreq r1,clips_left
 add r0,r1,r0,lsl #2
 ldr r1,[r0]
 ldr r2,[r0,#4]
 ldr r3,[r0,#8]
 str r1,[sp,#0x4c]
 str r2,[sp,#0x58]
 str r3,[sp,#0x5c]
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 cmp r0,#0
 b 0x02070488
animation_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_ANIMATION
clips:
 .word LATCH_SCA,LATCH_GMB,LATCH_GAB
 .word HOLD_SCA,HOLD_GMB,HOLD_GAB
 .word RAKE_SCA,RAKE_GMB,RAKE_GAB
 .word RIP_SCA,RIP_GMB,RIP_GAB
 .word KICK_SCA,KICK_GMB,KICK_GAB
clips_left:
 .word LATCH_LEFT_SCA,LATCH_GMB,LATCH_GAB
 .word HOLD_LEFT_SCA,HOLD_GMB,HOLD_GAB
 .word RAKE_LEFT_SCA,RAKE_GMB,RAKE_GAB
 .word RIP_LEFT_SCA,RIP_GMB,RIP_GAB
 .word KICK_LEFT_SCA,KICK_GMB,KICK_GAB

update_entry:
 push {r0-r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 mov r0,r4
 bl observe_mini
 mov r0,r4
 bl update
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r12,lr}
 b OLD_UPDATE

observe_mini:
 push {r4-r6,lr}
 mov r4,r0
 bl mini_ok
 cmp r0,#0
 beq observe_out
 ldr r5,lit1_state
 ldr r0,[r5,#192]
 add r1,r4,#4
 cmp r0,r1
 beq observe_stamp
 add r0,r5,#192
 bl SHARED_UNLINK_TARGET
 add r0,r5,#192
 add r1,r4,#4
 bl link
observe_stamp:
 ldr r0,=0x02145c5c
 ldr r6,[r0]
 mov r0,r6
 bl SHARED_RAM_OK
 cmp r0,#0
 beq observe_out
 ldr r0,[r6]
 str r0,[r5,#216]
 ldr r0,=0x02154c20
 ldr r0,[r0]
 str r0,[r5,#212]
 ldr r0,[r4,#0x30]
 str r0,[r5,#200]
 ldr r0,[r0,#0x1f8]
 str r0,[r5,#204]
 ldr r0,[r4,#0xf8]
 str r0,[r5,#208]
observe_out:
 pop {r4-r6,pc}

update:
 push {r4-r11,lr}
 sub sp,sp,#12
 mov r4,r0
 ldr r5,lit1_state
 ldr r0,[r5,#24]
 cmp r0,#0
 beq update_out
 ldr r0,[r5,#112]
 cmp r0,#0
 beq update_clear
 sub r6,r0,#4
 mov r0,r6
 bl active
 cmp r0,#0
 beq update_clear
 cmp r4,r6
 bne update_out
 ldr r7,[r6,#0x30]
 ldr r0,[r5,#84]
 add r0,r0,#1
 str r0,[r5,#84]
 ldr r0,[r5,#24]
 cmp r0,#5
 beq update_kick
 bl target_live
 cmp r0,#0
 beq update_clear
 mov r8,r0
 bl attacking
 cmp r0,#0
 bne update_shake
 ldr r9,[r8,#0x30]
 ldr r0,[r5,#24]
 cmp r0,#2
 blo update_face
 cmp r0,#4
 bhi update_face
 bl within_reach
 cmp r0,#0
 beq update_clear
update_face:
 ldr r0,[r5,#88]
 str r0,[r7,#0x180]
 ldr r0,[r7,#0x16c]
 ldr r1,[r5,#24]
 cmp r1,#1
 ldreq r2,=LATCH_GAB
 cmpeq r0,r2
 bne update_hold
 ldr r0,[r7,#0x178]
 cmp r0,#5
 blo update_follow
 mov r0,#2
 bl phase
 b update_follow
update_hold:
 cmp r1,#2
 bne update_rake
 ldr r1,=HOLD_GAB
 cmp r0,r1
 bne update_follow
 ldr r0,[r7,#0x178]
 cmp r0,#22
 blo update_follow
 mov r0,#2
 bl phase
 ldr r0,[r5,#80]
 add r0,r0,#1
 str r0,[r5,#80]
 b update_follow
update_rake:
 cmp r1,#3
 bne update_rip
 ldr r1,=RAKE_GAB
 cmp r0,r1
 bne update_follow
 ldr r0,[r7,#0x178]
 cmp r0,#6
 blo rake_wait
 mov r10,#0x1000
 bl strike
rake_wait:
 ldr r0,[r5,#24]
 cmp r0,#0
 beq update_out
 ldr r0,[r7,#0x178]
 cmp r0,#13
 blo update_follow
 mov r0,#2
 bl phase
 b update_follow
update_rip:
 cmp r1,#4
 bne update_zip
 ldr r1,=RIP_GAB
 cmp r0,r1
 bne update_follow
 ldr r0,[r7,#0x178]
 cmp r0,#9
 blo rip_wait
 mov r10,#0x2000
 bl strike
rip_wait:
 ldr r0,[r5,#24]
 cmp r0,#0
 beq update_out
 cmp r0,#5
 beq update_out
 ldr r0,[r5,#52]
 cmp r0,#0
 beq update_follow
 ldr r0,[r5,#44]
 cmp r0,#4
 beq rip_kick
 ldr r0,[r7,#0x178]
 cmp r0,#14
 blo update_follow
rip_kick:
 bl kick_off
 cmp r0,#0
 beq update_clear
 b update_out
update_zip:
 cmp r1,#6
 bne update_follow
 ldr r0,[r5,#96]
 cmp r0,#0
 beq update_clear
 mov r0,r9
 bl SHARED_XY
 mov r10,r0
 mov r11,r1
 mov r0,r7
 bl SHARED_XY
 sub r2,r10,r0
 cmp r2,#0
 movge r3,#1
 movlt r3,#0
 str r3,[r7,#0x180]
 cmp r2,#0
 rsblt r2,r2,#0
 cmp r2,#0x7000
 blo update_arrive
 sub r0,r10,r0
 mov r2,#0x4000
 bl clamp
 str r0,[r6,#0x18]
 sub r0,r11,r1
 mov r2,#0x2800
 bl clamp
 str r0,[r6,#0x1c]
 b update_line
update_arrive:
 bl release_line
 ldr r2,lit1_pad
 ldrh r2,[r2,#2]
 mov r0,r7
 bl SHARED_XY
 subs r0,r10,r0
 beq arrive_center
 bge arrive_right
arrive_left:
 tst r2,#0x20
 beq update_clear
 mov r1,#0
 str r1,[r5,#88]
 b arrive_latch
arrive_center:
 tst r2,#0x10
 bne arrive_right
 b arrive_left
arrive_right:
 tst r2,#0x10
 beq update_clear
 mov r1,#1
 str r1,[r5,#88]
arrive_latch:
 mov r0,#1
 bl phase
 b update_follow
update_shake:
 ldr r0,[r5,#72]
 add r0,r0,#1
 str r0,[r5,#72]
 ldr r0,[r5,#88]
 cmp r0,#1
 ldreq r0,=0xffffe000
 movne r0,#0x2000
 str r0,[r6,#0x18]
 mov r0,#0x2000
 str r0,[r6,#0x1c]
 bl cleanup
 b update_out
update_follow:
 mov r0,r8
 bl shoulder_height
 mov r11,r0
 mov r0,r9
 bl SHARED_XY
 ldr r2,[r5,#88]
 cmp r2,#1
 subeq r10,r0,#0x3000
 addne r10,r0,#0x3000
 add r11,r1,r11
 mov r0,r7
 bl SHARED_XY
 sub r0,r10,r0
 mov r0,r0,asr #1
 mov r2,#0x4000
 bl clamp
 str r0,[r6,#0x18]
 sub r0,r11,r1
 mov r0,r0,asr #1
 add r0,r0,#0x400
 mov r2,#0x4000
 bl clamp
 str r0,[r6,#0x1c]
 mov r0,r6
 bl 0x020739b4
 b update_out
update_line:
 mov r0,r6
 add r1,sp,#0
 bl WEB_HAND
 ldr r0,[r5,#96]
 sub r0,r0,#4
 mov r1,sp
 bl 0x0206632c
 b update_out
update_kick:
 ldr r0,[r7,#0x16c]
 ldr r1,=KICK_GAB
 cmp r0,r1
 bne update_out
 ldr r0,[r7,#0x178]
 cmp r0,#14
 blo update_out
update_clear:
 bl cleanup
update_out:
 add sp,sp,#12
 pop {r4-r11,pc}

strike:
 push {r4-r11,lr}
 sub sp,sp,#4
 ldr r0,[r5,#52]
 cmp r0,#0
 bne strike_out
 bl within_reach
 cmp r0,#0
 bne strike_contact
 bl cleanup
 b strike_out
strike_contact:
 mov r0,#1
 str r0,[r5,#52]
 str r0,[r5,#36]
 mov r0,r8
 mov r1,#4
 mov r2,r10
 mov r3,r6
 bl WEB_HIT
 str r0,[r5,#44]
 cmp r0,#4
 ldreq r0,[r5,#48]
 addeq r0,r0,#1
 streq r0,[r5,#48]
 mov r0,#0
 str r0,[r5,#36]
 ldr r0,[r5,#24]
 cmp r0,#3
 ldreq r0,[r5,#64]
 addeq r0,r0,#1
 streq r0,[r5,#64]
 ldr r0,[r5,#24]
 cmp r0,#4
 ldreq r0,[r5,#68]
 addeq r0,r0,#1
 streq r0,[r5,#68]
 bl target_live
 cmp r0,#0
 bne strike_out
 ldr r0,[r5,#24]
 cmp r0,#4
 bne strike_cleanup
 ldr r0,[r5,#44]
 cmp r0,#4
 bne strike_cleanup
 bl kick_off
 cmp r0,#0
 bne strike_out
strike_cleanup:
 bl cleanup
strike_out:
 add sp,sp,#4
 pop {r4-r11,pc}

kick_off:                   // Only the still-owned rider is needed after a lethal tear.
 push {r4-r8,lr}
 mov r0,r6
 bl active
 cmp r0,#0
 beq kick_out
 ldr r7,[r6,#0x30]
 mov r0,#5
 bl phase
 ldr r0,[r5,#88]
 cmp r0,#1
 ldreq r0,=0xffffd800
 movne r0,#0x2800
 str r0,[r6,#0x18]
 mov r0,#0x4000
 str r0,[r6,#0x1c]
 mov r0,r6
 bl 0x020739b4
 add r0,r5,#8
 bl SHARED_UNLINK_TARGET
 mov r0,#1
kick_out:
 pop {r4-r8,pc}

within_reach:               // Collision-blocked follows cannot deal remote damage.
 push {r4-r7,lr}
 sub sp,sp,#4
 mov r0,r8
 bl shoulder_height
 mov r5,r0
 ldr r0,[r8,#0x30]
 bl SHARED_XY
 mov r4,r0
 add r5,r1,r5
 ldr r0,[r6,#0x30]
 bl SHARED_XY
 sub r0,r0,r4
 cmp r0,#0
 rsblt r0,r0,#0
 cmp r0,#0x6000
 bgt reach_no
 sub r0,r1,r5
 cmp r0,#0
 rsblt r0,r0,#0
 cmp r0,#0x8000
 movle r0,#1
 movgt r0,#0
 b reach_out
reach_no:
 mov r0,#0
reach_out:
 add sp,sp,#4
 pop {r4-r7,pc}

shoulder_height:            // Smaller native player rigs need a lower grip than the Conductor.
 ldr r1,[r0]
 ldr r2,lit1_mini
 cmp r1,r2
 movne r0,#0xa000
 bxne lr
 ldr r1,[r0,#0x30]
 ldr r1,[r1,#0x10]
 cmp r1,#0x1000
 movlt r0,#0xa000
 bxlt lr
 cmp r1,#0x2000
 movgt r0,#0xa000
 bxgt lr
 mov r2,#10
 mul r0,r1,r2
 sub r0,r0,#0x4000
 cmp r0,#0x8000
 movlt r0,#0x8000
 cmp r0,#0xc000
 movgt r0,#0xc000
 bx lr

release_line:
 push {r4-r6,lr}
 ldr r0,[r5,#96]
 cmp r0,#0
 beq line_clear
 add r0,r5,#96
 bl WEB_RELEASE
line_clear:
 add r0,r5,#96
 bl SHARED_UNLINK_TARGET
 pop {r4-r6,pc}

release_yank:
 push {r4-r9,lr}
 sub sp,sp,#4
 mov r4,r6
 ldr r7,lit1_yank
 ldr r8,[r7,#120]
 cmp r8,#5
 movhi r8,#5
 ldr r5,lit1_yank
 mov r9,#0
yank_clear_loop:
 cmp r8,#0
 beq yank_clear_done
 mov r0,r5
 bl YANK_CLEAR
 cmp r9,#0
 ldreq r5,=YANK_RECORDS
 addne r5,r5,#128
 add r9,r9,#1
 subs r8,r8,#1
 b yank_clear_loop
yank_clear_done:
 add r0,r7,#112
 bl SHARED_UNLINK_TARGET
 mov r0,#0
 str r0,[r7]
 str r0,[r7,#4]
 str r0,[r7,#8]
 str r0,[r7,#24]
 str r0,[r7,#56]
 str r0,[r7,#120]
 add sp,sp,#4
 pop {r4-r9,pc}

cleanup:
 push {r4-r7,lr}
 sub sp,sp,#4
 ldr r5,lit1_state
 bl release_line
 ldr r4,[r5,#112]
 cmp r4,#0
 beq cleanup_unlink
 sub r4,r4,#4
 mov r0,r4
 bl SHARED_RAM_OK
 cmp r0,#0
 beq cleanup_unlink
 ldr r0,[r4]
 ldr r1,=0x0212e3f0
 cmp r0,r1
 bne cleanup_unlink
 ldr r0,[r4,#0x30]
 bl SHARED_RAM_OK
 cmp r0,#0
 beq cleanup_unlink
 ldr r0,[r4,#0x30]
 ldr r1,[r0]
 cmp r1,r4
 bne cleanup_unlink
 ldr r0,[r0,#0x1f8]
 ldr r1,[r5,#4]
 cmp r0,r1
 bne cleanup_unlink
 ldr r1,[r0,#0x14]
 cmp r1,#51
 movne r0,#0
 bne cleanup_unlink
 mov r1,#19
 bl 0x02077844
cleanup_unlink:
 add r0,r5,#8
 bl SHARED_UNLINK_TARGET
 add r0,r5,#112
 bl SHARED_UNLINK_TARGET
 mov r0,#0
 str r0,[r5]
 str r0,[r5,#4]
 str r0,[r5,#24]
 str r0,[r5,#36]
 ldr r0,[r5,#76]
 add r0,r0,#1
 str r0,[r5,#76]
 add sp,sp,#4
 pop {r4-r7,pc}

effect:
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,lit1_state
 ldr r1,[r0,#36]
 cmp r1,#1
 bne effect_native
 ldr r1,[r0,#8]
 ldr r3,[r6,#0x44]
 add r3,r3,#4
 cmp r1,r3
 bne effect_native
 ldr r1,[r0]
 ldr r3,[r5]
 cmp r1,r3
 bne effect_native
 ldr r0,[r6,#0x44]
 bl shoulder_height
 sub r3,r0,#0x3000
 ldr r0,[r6,#0x44]
 ldr r0,[r0,#0x30]
 ldr r2,[r0,#0x4c]
 str r2,[sp,#0x188]
 bl SHARED_XY
 add r1,r1,r3
 str r0,[sp,#0x180]
 str r1,[sp,#0x184]
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b 0x020955e0
effect_native:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_EFFECT
