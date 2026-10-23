// Exact-parent post-pass. Four entry points; original kit ABI stays fixed.
 b start_try
 b node
 b update
 b hud_filter
 b yank_entry

start_try:                  // r0 controller -> bool, consume queued Y only on success
 push {r4-r11,lr}
 sub sp,sp,#4
 mov r4,r0
 ldr r5,=STATE
 ldr r0,[r5,#16]
 cmp r0,#0
 bne try_no
 ldr r0,[r4,#0x14]
 cmp r0,#6
 bls try_ground
 cmp r0,#46
 beq try_ground
 cmp r0,#37
 cmpne r0,#38
 bne try_no
try_ground:
 ldr r6,[r4,#0x44]
 mov r0,r6
 mov r1,#0x40000
 bl K2_OWNED
 cmp r0,#0
 beq try_no
 bl 0x02152c5c
 tst r0,#0x80
 beq try_no
 tst r0,#0x100
 bne try_no
 tst r0,#0x43
 bne try_no
 mov r0,#1
 str r0,[sp]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cff0c
 cmp r0,#0
 beq try_no
 str r6,[r5]
 str r4,[r5,#4]
 mov r7,#0
 mov r0,#0
 str r0,[r5,#8]
 str r0,[r5,#12]
 str r0,[r5,#24]
 str r0,[r5,#28]
 ldr r8,=0x02154c40
 mov r9,#12
try_scan:
 ldr r0,[r8]
 cmp r0,#0
 beq try_next
 bl 0x02152c68
 cmp r0,#0
 beq try_next
 ldr r0,[r8]
 ldr r1,[r0,#0x48]
 cmp r1,#0x4000
 blo try_next
 ldr r1,[r0,#0x30]
 ldr r2,[r1,#0x1f8]
 cmp r2,#0
 beq try_next
 ldr r2,[r2,#0x14]
 cmp r2,#46               // actual native cocoon, either source of webbing
 bne try_next
 ldr r2,[r6,#0x30]
 ldr r3,[r2,#0x7c]
 ldr r10,[r2,#0x160]
 add r3,r3,r10
 ldr r10,[r8,#4]
 subs r3,r10,r3
 rsbmi r3,r3,#0
 cmp r3,#0x1e000
 bgt try_next
 ldr r3,[r2,#0x80]
 ldr r10,[r2,#0x164]
 add r3,r3,r10
 ldr r10,[r8,#8]
 subs r3,r10,r3
 rsbmi r3,r3,#0
 cmp r3,#0xc000
 bgt try_next
 add r10,r5,#64
 add r10,r10,r7,lsl #4
 str r0,[r10]
 str r1,[r10,#4]
 ldr r3,[r0,#0x40]
 str r3,[r10,#8]
 mov r3,#0
 str r3,[r10,#12]
 add r7,r7,#1
 cmp r7,#4
 bhs try_found
try_next:
 add r8,r8,#16
 subs r9,r9,#1
 bne try_scan
try_found:
 cmp r7,#0
 beq try_no
 str r7,[r5,#8]
 mov r1,sp
 add r0,r4,#0x28
 bl 0x020cfc34
 mov r0,#1
 str r0,[r5,#12]
 ldr r1,=0x02154c20
 ldr r1,[r1]
 str r1,[r5,#36]
 ldr r1,[r6,#0x30]
 ldr r1,[r1,#0x180]
 str r1,[r5,#32]
 b try_return
try_no:
 mov r0,#0
try_return:
 add sp,sp,#4
 pop {r4-r11,pc}

node:                       // r0 controller, r1 prior state -> action or zero
 push {r4-r6,lr}
 mov r4,r0
 ldr r5,=0x02157020
 mov r1,#0
 str r1,[r5,#0x80]
 str r1,[r5,#0x7c]
 ldr r2,[r5,#0x94]
 str r1,[r5,#0x94]
 cmp r2,#0
 beq node_vortex
 mov r0,#49                // unchanged Dragnet heave and clip
 mov r2,#10
 mov r3,#12
 b node_play
node_vortex:
 ldr r6,=STATE
 ldr r0,[r6,#12]
 str r1,[r6,#12]
 cmp r0,#0
 beq node_none
 ldr r0,[r6,#4]
 cmp r0,r4
 bne node_none
 ldr r0,=0x02154c20
 ldr r0,[r0]
 ldr r2,[r6,#36]
 sub r0,r0,r2
 cmp r0,#2
 bhi node_none
 mov r0,#1
 str r0,[r6,#16]
 str r0,[r6,#48]
 mvn r0,#0
 str r0,[r6,#20]
 ldr r0,[r6,#40]
 add r0,r0,#1
 str r0,[r6,#40]
 mov r0,#59
 mov r2,#13
 mov r3,#14
node_play:
 str r2,[r5,#0x80]
 mov r2,#1
 str r2,[r5,#0x84]
 str r3,[r4,#0x80]
 ldr r1,[r4,#0x44]
 ldr r1,[r1,#0x30]
 ldr r2,[r1,#0x2fc]
 orr r2,r2,#2
 str r2,[r1,#0x2fc]
 pop {r4-r6,pc}
node_none:
 mov r0,#0
 pop {r4-r6,pc}

update:                     // r0 hero, once per native update
 push {r4-r11,lr}
 sub sp,sp,#12
 mov r4,r0
 ldr r5,=STATE
 ldr r0,[r5,#16]
 cmp r0,#0
 beq update_out
 ldr r0,[r5]
 cmp r0,r4
 bne release
 ldr r6,[r4,#0x30]
 ldr r0,[r6,#0x1f8]
 ldr r1,[r5,#4]
 cmp r0,r1
 bne release
 ldr r1,[r0,#0x14]
 cmp r1,#46
 bne release              // native R, jump, hurt/death always interrupt
 ldr r1,[r6,#0x254]
 cmp r1,#59
 beq update_action
 ldr r1,[r5,#48]
 cmp r1,#0
 beq release
 mov r1,#0
 str r1,[r5,#48]
 b update_out             // node commit happens one native update later
update_action:
 ldr r7,[r6,#0x178]
 cmp r7,#18
 bhi release
 ldr r0,[r6,#0x7c]
 ldr r1,[r6,#0x160]
 add r0,r0,r1
 str r0,[sp]
 ldr r0,[r6,#0x80]
 ldr r1,[r6,#0x164]
 add r0,r0,r1
 str r0,[sp,#4]
 ldr r0,[r5,#20]
 str r7,[r5,#20]
 cmp r7,#2
 blo update_out
 add r8,r5,#64
 ldr r9,[r5,#8]
target_loop:
 ldr r0,[r8]
 bl 0x02152c68
 cmp r0,#0
 beq target_next
 ldr r10,[r8]
 ldr r11,[r10,#0x30]
 ldr r1,[r8,#4]
 cmp r11,r1
 bne target_next
 ldr r1,[r10,#0x40]
 ldr r2,[r8,#8]
 cmp r1,r2
 bne target_next
 ldr r1,[r10,#0x44]
 cmp r1,#0
 ble target_next
 mov r0,r10
 mov r1,r4
 mov r2,#6
 bl WEB_LINE
 ldr r1,[r8,#12]
 cmp r1,#0
 bne target_launched
 mov r0,r10
 mov r1,#0x25
 mov r2,#0x800
 mov r3,r4
 bl WEB_HIT
 cmp r0,#4
 bne target_next
 mov r1,#1
 str r1,[r8,#12]
target_launched:
 cmp r7,#13
 bhs target_slam
 // Catapult arc uses native velocity/collision, never coordinates/clocks.
 adr r0,trajectory
 sub r1,r7,#2
 add r0,r0,r1,lsl #3
 ldr r1,[r0]
 ldr r2,[r5,#32]
 cmp r2,#1
 rsbne r1,r1,#0
 ldr r2,[sp]
 add r1,r1,r2
 ldr r2,[r11,#0x7c]
 ldr r3,[r11,#0x160]
 add r2,r2,r3
 sub r1,r1,r2
 mov r1,r1,asr #1
 cmp r1,#0x3000
 movgt r1,#0x3000
 cmn r1,#0x3000
 movlt r1,#0x3000
 rsblt r1,r1,#0
 str r1,[r10,#0x18]
 ldr r1,[r0,#4]
 ldr r2,[sp,#4]
 add r1,r1,r2
 ldr r2,[r11,#0x80]
 ldr r3,[r11,#0x164]
 add r2,r2,r3
 sub r1,r1,r2
 mov r1,r1,asr #1
 cmp r1,#0x3000
 movgt r1,#0x3000
 cmn r1,#0x3000
 movlt r1,#0x3000
 rsblt r1,r1,#0
 str r1,[r10,#0x1c]
 b target_collide
target_slam:
 cmp r1,#2
 bhs slam_velocity
 mov r0,r10
 mov r1,#0x1f
 mov r2,#0x2800
 mov r3,r4
 bl WEB_HIT
 mov r1,#2
 str r1,[r8,#12]
 ldr r1,[r5,#44]
 add r1,r1,#1
 str r1,[r5,#44]
slam_velocity:
 mov r1,#0
 str r1,[r10,#0x18]
 mov r1,#0x4000
 rsb r1,r1,#0
 str r1,[r10,#0x1c]
target_collide:
 cmp r7,#2
 blo target_next
 bl body_sweep
target_next:
 add r8,r8,#16
 subs r9,r9,#1
 bne target_loop
 b update_out
release:
 mov r0,#0
 str r0,[r5,#16]
 str r0,[r5,#12]
 str r0,[r5,#8]
 // Clear all per-target launch ownership for the next native webbed capture.
 add r1,r5,#64
 mov r2,#4
release_loop:
 str r0,[r1,#12]
 add r1,r1,#16
 subs r2,r2,#1
 bne release_loop
update_out:
 add sp,sp,#12
 pop {r4-r11,pc}

body_sweep:                 // carried enemy physically intersects a bystander
 push {r6-r11,lr}
 sub sp,sp,#4
 ldr r6,=0x02154c40
 mov r7,#0
 ldr r8,[r11,#0x7c]
 ldr r0,[r11,#0x160]
 add r8,r8,r0
 ldr r9,[r11,#0x80]
 ldr r0,[r11,#0x164]
 add r9,r9,r0
 ldr r11,[r5,#20]
 cmp r11,#13
 movlo r11,#24
 movhs r11,#28
 blo body_loop
 // The final impact spreads along the floor only after the body descends.
 ldr r0,[r4,#0x30]
 ldr r1,[r0,#0x80]
 ldr r2,[r0,#0x164]
 add r1,r1,r2
 sub r1,r9,r1
 cmp r1,#0x5000
 bgt body_out
body_loop:
 ldr r0,[r5,r11]
 mov r1,#1
 tst r0,r1,lsl r7
 bne body_next
 ldr r0,[r6]
 cmp r0,#0
 cmpne r0,r10
 beq body_next
 // Captured bodies never damage one another or receive a second free slam.
 add r1,r5,#64
 ldr r2,[r5,#8]
body_owned:
 ldr r3,[r1]
 cmp r0,r3
 beq body_next
 add r1,r1,#16
 subs r2,r2,#1
 bne body_owned
 bl 0x02152c68
 cmp r0,#0
 beq body_next
 ldr r0,[r6]
 ldr r1,[r0,#0x48]
 cmp r1,#0x4000
 blo body_next
 ldr r1,[r6,#4]
 subs r1,r1,r8
 rsbmi r1,r1,#0
 cmp r11,#28
 mov r2,#0x5000
 moveq r2,#0xe000
 cmp r1,r2
 bgt body_next
 ldr r1,[r6,#8]
 subs r1,r1,r9
 rsbmi r1,r1,#0
 cmp r1,#0x5000
 bgt body_next
 mov r1,#0x1f
 mov r2,#0x1000
 mov r3,r4
 bl WEB_HIT
 cmp r0,#4
 bne body_next
 ldr r0,[r5,r11]
 mov r1,#1
 orr r0,r0,r1,lsl r7
 str r0,[r5,r11]
 ldr r0,[r5,#52]
 add r0,r0,#1
 str r0,[r5,#52]
body_next:
 add r6,r6,#16
 add r7,r7,#1
 cmp r7,#12
 blo body_loop
body_out:
 add sp,sp,#4
 pop {r6-r11,pc}

yank_entry:                 // queued Y in native web hold, exact native frame
 push {r1,r2,r3,r12,lr}
 mov r0,r6
 bl start_try
 cmp r0,#0
 beq yank_fallback
 pop {r1,r2,r3,r12,lr}
 add sp,sp,#0x10c
 mov r0,#46
 pop {r4,r5,r6,r7,pc}
yank_fallback:
 pop {r1,r2,r3,r12,lr}
 b OLD_YANK

trajectory:                 // sample2..12: physical arc relative to the hero
 .word 40960,12288, 45056,28672, 40960,45056
 .word 24576,61440, 0,69632, -24576,69632
 .word -40960,61440, -45056,45056, -32768,28672
 .word -8192,12288, 24576,0

hud_filter:
 push {r1,r2,r12,lr}
 mrs r12,cpsr
 ldr r1,[r0]
 ldr r2,=0x021301d0
 cmp r1,r2
 bne hud_native
 ldr r1,[r0,#0x40]
 ldr r2,=BOSS_CONFIG
 cmp r1,r2
 bne hud_native
 msr cpsr_f,r12
 pop {r1,r2,r12,lr}
 push {r4-r10,lr}
 b 0x02073a6c
hud_native:
 msr cpsr_f,r12
 pop {r1,r2,r12,lr}
 push {r2,r3,r12,lr}       // original cheap HUD filter's displaced instruction
 b 0x02151924
 .ltorg
