// Private air utility. Native controllers, gravity, collision and chosen attacks continue.
 b think
 b animation
 b update_entry
 b effect

think:
 push {r4-r8,lr}
 sub sp,sp,#8
 mov r4,r0
 ldr r6,[r4,#0x44]
 ldr r5,=STATE
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
 ldr r0,[r7,#0x2ac]
 cmp r0,#0
 ble think_airborne
 ldr r0,[r6,#0x1c]
 cmp r0,#0
 bgt think_airborne
 bl cleanup
 mov r0,#24             // Native upward floor normal + descending velocity: land immediately.
 b think_out
think_airborne:
 mov r0,#3
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 beq think_switch
 bl cleanup
 ldr r0,[r6,#0xe8]
 ldr r0,[r0]
 tst r0,#0x400
 bne think_native
 mov r0,#3
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34
 b think_fall
think_switch:
 mov r0,#4
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 bne think_release_native
 ldr r0,[r5,#48]
 cmp r0,#0
 beq think_clock
 mov r0,#1
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 beq think_clock
 mov r0,#1
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34
 bl cleanup
 mov r0,#0
 str r0,[r4,#0x80]
 mov r0,#1
 strb r0,[r4,#4]
 ldr r0,[r7,#0x2fc]
 orr r0,r0,#2
 str r0,[r7,#0x2fc]
 mov r0,#51             // A chosen Y enters the native fresh air string, with its own motion/hits.
 b think_out
think_clock:
 ldr r0,[r7,#0x178]
 cmp r0,#13
 bhs think_finish
 mov r0,#51
 b think_out
think_finish:
 bl cleanup
think_fall:
 mov r0,#19
 b think_out
think_release_native:
 bl cleanup
 b think_native
think_start:
 ldr r0,[r4,#0x14]
 cmp r0,#15
 cmpne r0,#19
 cmpne r0,#51
 bne think_native
 ldr r0,[r4,#0x24]
 cmp r0,#1
 blo think_native
 cmp r0,#3
 bhi think_native
 mov r0,#3
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 bne think_native
 mov r0,#4
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 bne think_native
 mov r0,#5
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 beq think_native
 mov r0,r6
 bl select_target
 cmp r0,#0
 beq think_native
 mov r8,r0
 ldr r0,[r8,#0x30]
 bl SHARED_XY
 mov r2,r0
 mov r0,r7
 bl SHARED_XY
 subs r2,r2,r0
 beq think_facing
 movgt r1,#1
 movlt r1,#0
 str r1,[sp,#4]
 mov r0,r6
 add r1,sp,#4
 bl 0x02072860           // A nearby foe below may lie behind; turn through the native method.
think_facing:
 ldr r0,[r4,#0x14]
 str r0,[r5,#124]
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
 ldr r0,[r8,#0x40]
 str r0,[r5,#20]
 ldr r1,=BOSS_CONFIG
 cmp r0,r1
 moveq r0,#1
 movne r0,#0
 str r0,[r5,#52]
 ldr r0,[r6,#0xe8]
 ldr r0,[r0,#-12]
 str r0,[r5,#32]
 ldr r0,[r7,#0x180]
 str r0,[r5,#88]
 mov r0,#0
 str r0,[r5,#28]
 str r0,[r5,#36]
 str r0,[r5,#44]
 str r0,[r5,#48]
 str r0,[r5,#56]
 str r0,[r5,#80]
 str r0,[r5,#92]
 str r0,[r4,#0x80]
 strb r0,[r4,#0x90]
 mov r0,#1
 str r0,[r5,#24]
 strb r0,[r4,#4]
 ldr r0,[r7,#0x2fc]
 orr r0,r0,#2
 str r0,[r7,#0x2fc]
 ldr r0,[r5,#60]
 add r0,r0,#1
 str r0,[r5,#60]
 mov r0,#5
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34
 mov r0,#51
 b think_out
think_native:
 mov r0,r4
 add sp,sp,#8
 pop {r4-r8,lr}
 b NATIVE_THINK
think_out:
 add sp,sp,#8
 pop {r4-r8,pc}

owned:
 push {r4,lr}
 mov r4,r0
 bl SHARED_OWNED
 cmp r0,#0
 beq owned_out
 ldr r0,[r4,#0xe8]
 ldr r0,[r0,#8]
 tst r0,#0x100000       // Reel In bit84; SHARED_OWNED checks its Web Yank parent83.
 movne r0,#1
 moveq r0,#0
owned_out:
 pop {r4,pc}

active:
 push {r4-r6,lr}
 mov r4,r0
 bl owned
 cmp r0,#0
 beq active_out
 ldr r5,=STATE
 ldr r0,[r5,#24]
 cmp r0,#0
 beq active_out
 ldr r0,[r5,#112]
 add r1,r4,#4
 cmp r0,r1
 bne inactive
 ldr r0,[r5]
 cmp r0,r4
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

link:                   // token, actor's intrusive head; destructor clears the token.
 ldr r2,[r1]
 str r1,[r0]
 str r2,[r0,#4]
 str r0,[r1]
 bx lr

select_target:
 push {r4-r11,lr}
 sub sp,sp,#12
 mov r4,r0
 ldr r0,[r4,#0x30]
 ldr r11,[r0,#0x180]
 bl SHARED_XY
 mov r9,r0
 mov r10,r1
 mov r5,#0
 ldr r6,=0x4c001
 ldr r7,=0x02154c40
 mov r8,#12
select_loop:
 ldr r0,[r7]
 bl 0x02152c68
 cmp r0,#0
 beq select_next
 ldr r0,[r7]
 ldr r1,[r0,#0x44]
 cmp r1,#0
 ble select_next
 ldr r1,[r0,#0x48]
 cmp r1,#0x4000
 blo select_next
 ldr r1,[r0,#0x30]
 ldr r2,[r1]
 cmp r2,r0
 bne select_next
 mov r0,r1
 bl SHARED_XY
 sub r1,r1,r10
 cmn r1,#0x28000
 blt select_next
 cmp r1,#0xc000
 bgt select_next
 sub r0,r0,r9
 mov r2,r11
 cmp r0,#0
 eorlt r2,r2,#1
 rsblt r0,r0,#0
 cmp r0,#0xc000
 cmple r1,#-0x9000
 ble select_distance
 cmp r2,#1
 bne select_next
select_distance:
 cmp r0,#0x24000
 bgt select_next
 cmp r1,#0
 rsblt r1,r1,#0
 cmp r0,#0x9000
 cmplt r1,#0x9000
 blt select_next          // Already in claw range: preserve native air A.
 add r0,r0,r1
 cmp r0,r6
 bhs select_next
 mov r6,r0
 ldr r5,[r7]
select_next:
 add r7,r7,#16
 subs r8,r8,#1
 bne select_loop
 mov r0,r5
 add sp,sp,#12
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
 ldr r0,=REEL_SCA
 str r0,[sp,#0x4c]
 ldr r0,=REEL_GMB
 str r0,[sp,#0x58]
 ldr r0,=REEL_GAB
 str r0,[sp,#0x5c]
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 cmp r0,#0
 b 0x02070488           // This route owns the utility; older Sky Rake routing must not replace it.
animation_out:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_ANIMATION

update_entry:
 push {r0-r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 mov r0,r4
 bl update
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r12,lr}
 b OLD_UPDATE

target_live:
 push {r4,lr}
 ldr r4,[r5,#8]
 cmp r4,#0
 beq target_no
 sub r4,r4,#4
 mov r0,r4
 bl SHARED_RAM_OK
 cmp r0,#0
 beq target_no
 mov r0,r4
 bl 0x02152c68
 cmp r0,#0
 beq target_no
 ldr r0,[r4,#0x44]
 cmp r0,#0
 ble target_no
 ldr r0,[r4,#0x30]
 ldr r1,[r5,#16]
 cmp r0,r1
 bne target_no
 ldr r1,[r0]
 cmp r1,r4
 bne target_no
 ldr r0,[r4,#0x40]
 ldr r1,[r5,#20]
 cmp r0,r1
 bne target_no
 mov r0,r4
 pop {r4,pc}
target_no:
 mov r0,#0
 pop {r4,pc}

update:
 push {r4-r11,lr}
 sub sp,sp,#12
 mov r4,r0
 ldr r5,=STATE
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
 bl target_live
 cmp r0,#0
 beq update_clear
 mov r8,r0
 cmp r4,r6
 beq update_hero
 cmp r4,r8
 bne update_out
 ldr r0,[r5,#44]
 cmp r0,#4
 bne update_out
 ldr r0,[r5,#52]
 cmp r0,#0
 bne update_out
 ldr r9,[r8,#0x30]
 ldr r0,[r9,#0x1f8]
 bl SHARED_RAM_OK
 cmp r0,#0
 beq update_clear
 ldr r0,[r9,#0x1f8]
 ldr r0,[r0,#0x14]
 cmp r0,#39
 bne update_out          // Native ReceiveHit commits the launch before we steer it.
 ldr r0,[r6,#0x30]
 bl SHARED_XY
 ldr r2,[r5,#88]
 cmp r2,#1
 addeq r10,r0,#0x6000
 subne r10,r0,#0x6000
 mov r11,r1
 mov r0,r9
 bl SHARED_XY
 sub r0,r10,r0
 mov r0,r0,asr #1
 mov r2,#0x4000
 bl clamp
 str r0,[r8,#0x18]
 sub r0,r11,r1
 mov r0,r0,asr #1
 mov r2,#0x4000
 bl clamp
 str r0,[r8,#0x1c]
 mov r0,#1
 str r0,[r5,#92]
 b update_out
update_hero:
 ldr r7,[r6,#0x30]
 ldr r0,[r5,#28]
 add r0,r0,#1
 str r0,[r5,#28]
 cmp r0,#2
 bls update_out          // A reused air action can still expose the previous clip's clock.
 cmp r0,#48
 bhi update_clear
 ldr r10,[r7,#0x178]
 str r10,[r5,#40]
 cmp r10,#2
 blo update_out
 ldr r0,[r5,#80]
 cmp r0,#0
 bne update_line
 mov r0,#1
 str r0,[r5,#80]
 ldr r0,[r5,#124]
 cmp r0,#51
 bne recoil_done
 ldr r0,[r5,#52]
 cmp r0,#0
 bne recoil_done
 ldr r0,[r6,#0x1c]
 cmp r0,#0
 movle r0,#0x1800
 strle r0,[r6,#0x1c]     // One physical recoil extends a descending combo; gravity immediately resumes.
recoil_done:
 mov r0,r6
 mov r1,r8
 bl line_make
 cmp r0,#0
 beq update_clear
 ldr r0,[r5,#52]
 cmp r0,#0
 bne update_line
 mov r0,#1
 str r0,[r5,#36]
 mov r0,r8
 mov r1,#0x25
 mov r2,#0
 mov r3,r6
 bl WEB_HIT
 str r0,[r5,#44]
 mov r1,#0
 str r1,[r5,#36]
 cmp r0,#1
 moveq r1,#1
 streq r1,[r5,#52]
 beq update_line
 cmp r0,#4
 bne update_clear
 ldr r0,[r5,#64]
 add r0,r0,#1
 str r0,[r5,#64]
update_line:
 ldr r0,[r5,#96]
 cmp r0,#0
 beq update_clear
 ldr r0,[r5,#52]
 cmp r0,#0
 beq update_hand
 mov r0,r8
 mov r1,sp
 bl body_anchor
 cmp r0,#0
 beq update_clear
 ldr r10,[sp]
 ldr r11,[sp,#4]
 ldr r0,[r8,#0x30]
 bl SHARED_XY
 sub r10,r10,r0
 sub r11,r11,r1
 ldr r0,[r5,#96]
 sub r0,r0,#4
 str r10,[r0,#0x80]
 str r11,[r0,#0x84]      // The native weak tie follows the posed body instead of the logical floor point.
update_hand:
 mov r0,r6
 mov r1,sp
 bl WEB_HAND
 ldr r0,[r5,#96]
 sub r0,r0,#4
 mov r1,sp
 bl 0x0206632c
 ldr r0,[r7,#0x1f8]
 ldr r0,[r0,#0x14]
 cmp r0,#51
 bne update_clear
 ldr r0,[r8,#0x30]
 bl SHARED_XY
 mov r10,r0
 mov r11,r1
 mov r0,r7
 bl SHARED_XY
 sub r10,r10,r0
 sub r11,r11,r1
 ldr r0,[r5,#52]
 cmp r0,#0
 beq update_arrival
 mov r0,r10
 cmp r0,#0
 rsblt r0,r0,#0
 sub r0,r0,#0x7000
 cmp r0,#0
 movlt r0,#0
 mov r2,#0x2800
 bl clamp
 cmp r10,#0
 rsblt r0,r0,#0
 str r0,[r6,#0x18]
 add r0,r11,#0x6000
 mov r0,r0,asr #2
 mov r2,#0x2800
 bl clamp
 str r0,[r6,#0x1c]
 mov r0,#1
 str r0,[r5,#56]
update_arrival:
 cmp r10,#0
 rsblt r10,r10,#0
 cmp r11,#0
 rsblt r11,r11,#0
 cmp r10,#0x9000
 cmple r11,#0x8000
 movle r0,#1
 strle r0,[r5,#48]
 b update_out
update_clear:
 bl cleanup
update_out:
 add sp,sp,#12
 pop {r4-r11,pc}

body_anchor:             // Live heavy actor, outputXY -> native model center transformed by its draw pose.
 push {r4-r11,lr}
 sub sp,sp,#12
 mov r4,r0
 mov r7,r1
 ldr r8,[r4,#0x30]
 mov r0,r8
 bl SHARED_RAM_OK
 cmp r0,#0
 beq body_no
 ldr r0,[r8]
 cmp r0,r4
 bne body_no
 ldr r5,[r8,#0x58]
 mov r0,r5
 bl SHARED_RAM_OK
 cmp r0,#0
 beq body_no
 add r5,r5,#0x190
 mov r6,#0
body_scale:
 ldr r0,[r5,r6]
 cmp r0,#0x10000
 bgt body_no
 cmn r0,#0x10000
 blt body_no
 add r1,r8,#12
 ldr r1,[r1,r6]
 cmp r1,#0
 ble body_no
 cmp r1,#0x2000
 bgt body_no
 mul r0,r1,r0
 add r0,r0,#0x800
 mov r0,r0,asr #12
 add r1,sp,r6
 str r0,[r1]
 add r6,r6,#4
 cmp r6,#12
 blo body_scale
 mov r10,#0
body_axis:
 add r9,r8,#0x20
 add r9,r9,r10
 mov r11,#0
 mov r3,#0
body_product:
 ldr r0,[sp,r3]
 add r1,r3,r3,lsl #1
 add r1,r9,r1
 ldr r1,[r1]
 cmp r1,#0x1000
 bgt body_no
 cmn r1,#0x1000
 blt body_no
 mul r0,r1,r0
 add r11,r11,r0
 add r3,r3,#4
 cmp r3,#12
 blo body_product
 add r11,r11,#0x800
 mov r11,r11,asr #12
 add r0,r8,#0x44
 ldr r0,[r0,r10]
 add r11,r11,r0
 add r0,r7,r10
 str r11,[r0]
 add r10,r10,#4
 cmp r10,#8
 blo body_axis
 mov r0,#1
 b body_done
body_no:
 mov r0,#0
body_done:
 add sp,sp,#12
 pop {r4-r11,pc}

clamp:                  // signed r0, positive bound r2; preserve vertical delta in r1.
 cmp r0,r2
 movgt r0,r2
 rsb r3,r2,#0
 cmp r0,r3
 movlt r0,r3
 bx lr

cleanup:
 push {r4-r6,lr}
 ldr r5,=STATE
 bl target_live
 cmp r0,#0
 beq cleanup_hero
 mov r4,r0
 ldr r1,[r5,#92]
 cmp r1,#0
 beq cleanup_hero
 ldr r0,[r4,#0x30]
 ldr r0,[r0,#0x1f8]
 bl SHARED_RAM_OK
 cmp r0,#0
 beq cleanup_hero
 ldr r0,[r4,#0x30]
 ldr r0,[r0,#0x1f8]
 ldr r0,[r0,#0x14]
 cmp r0,#39
 moveq r0,#0
 streq r0,[r4,#0x18]     // A later native juggle/knockback owns its velocity.
cleanup_hero:
 ldr r4,[r5,#112]
 cmp r4,#0
 beq cleanup_links
 sub r4,r4,#4
 mov r0,r4
 bl active
 cmp r0,#0
 beq cleanup_links
 ldr r0,[r5,#56]
 cmp r0,#0
 movne r0,#0
 strne r0,[r4,#0x18]
cleanup_links:
 add r0,r5,#96
 bl WEB_RELEASE
 add r0,r5,#8
 bl SHARED_UNLINK_TARGET
 add r0,r5,#112
 bl SHARED_UNLINK_TARGET
 mov r0,#0
 str r0,[r5]
 str r0,[r5,#4]
 str r0,[r5,#24]
 str r0,[r5,#36]
 str r0,[r5,#48]
 str r0,[r5,#56]
 str r0,[r5,#92]
 ldr r0,[r5,#76]
 add r0,r0,#1
 str r0,[r5,#76]
 pop {r4-r6,pc}

line_make:
 push {r4-r6,lr}
 sub sp,sp,#40
 mov r4,r0
 mov r6,r1
 add r1,sp,#8
 bl WEB_HAND
 ldr r0,[r6,#0x30]
 bl SHARED_XY
 str r0,[sp,#16]
 str r1,[sp,#20]
 ldr r0,=0x147f
 str r0,[sp,#24]
 str r4,[sp,#28]
 mov r0,#0
 str r0,[sp,#32]
 add r0,sp,#24
 str r0,[sp]
 add r0,sp,#32
 add r1,sp,#28
 add r2,sp,#8
 add r3,sp,#16
 bl 0x0205f844
 ldr r4,[sp,#32]
 cmp r4,#0
 beq line_out
 add r0,r5,#96
 add r1,r4,#4
 bl link
 str r6,[sp,#28]
 mov r0,r4
 add r1,sp,#28
 mov r2,#1
 bl 0x020672d0
line_out:
 mov r0,r4
 add sp,sp,#40
 pop {r4-r6,pc}

effect:                 // Only our synchronous zero-HP catch skips native attack flashes.
 push {r0-r3,r12,lr}
 mrs r12,cpsr
 push {r3,r12}
 ldr r0,=STATE
 ldr r1,[r0,#36]
 cmp r1,#1
 bne effect_native
 ldr r1,[sp,#0x1f0]
 ldr r1,[r1]
 cmp r1,#0
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
 ldr r1,[r0,#68]
 add r1,r1,#1
 str r1,[r0,#68]
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b 0x02095670
effect_native:
 pop {r3,r12}
 msr cpsr_f,r12
 pop {r0-r3,r12,lr}
 b OLD_EFFECT
 .ltorg
