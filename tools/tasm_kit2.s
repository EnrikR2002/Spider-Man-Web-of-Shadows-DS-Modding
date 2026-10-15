// TASM kit, second code block at 02155420 (KIT2), v0.10.0. tools/tasm_kit.s
// calls entries +00..+0C, +14 and +18; tools/tasm_kit.py branches native sites
// to the rest. New shop rows live in ability word 2 (stats+0x14): Web Rush
// 0x400 (ability bit 74), Ricochet 0x800 (75), Momentum 0x1000 (76), Vitality
// I..III 0x2000/0x4000/0x8000 (77..79, Both Suits list, v0.11.0), Overclock
// 0x10000, Dragnet 0x20000, Vortex 0x40000 (80..82, v0.13.0: the web block at
// the end of this file, with its own state offsets +0x70..+0x27F and literals).
// State K2 = 02157020 (zero image): +0 rush phase (1 armed, 2 playing),
// +4 target, +8 node to resume, +0xC stop x, +0x10 side (1 = target right),
// +0x14 armed age, +0x18 rush clip loaded, +0x1C dash step (1 dashing, 2 last
// step done); +0x20..+0x4F Ricochet cooldown tick per registry slot, +0x50
// Ricochet count + 256 * native results, +0x54 last victim; +0x58 Momentum
// rate of this call (0 = native), +0x5C its accumulator, +0x60 doubled steps,
// +0x64 rush glide updates, +0x68 health bar tinted by Vitality.
// Strength dial (v0.15.1): 02156FC0 (block +0x1BA0, zero in the kit image; the
// chapter build fills it) holds two bytes per room 76..115: enemy health scale
// and damage-to-Spidey scale in 1/64ths (0 or 64 = native).
// Kit exports: 02152C58 kit_owned, 5C kit_keys, 60 kit_face,
// 64 kit_alive, 68 kit_fresh, 6C kit_replay_hit.
  b k2_update             // +00 r0=Spidey actor, once per update
  b k2_rush_try           // +04 r0=controller in state 46 -> r0=1: re-enter 46
  b k2_node               // +08 r0=controller at a string node start -> r0=action or 0
  b k2_route              // +0C -> r0=1 while the rush clip is routed
  b h_momentum            // +10 from 020B21B8  Red attack animation rate
  b k2_observe            // +14 r0=common-health enemy, every update (keeps all registers)
  b k2_damage             // +18 r1=Spidey HP, r3=HP after a hit -> r3 (keeps r0, r2)
  b h_yank                // +1C from 020B6030  Y queued in the web hold
  b h_vortex_stand        // +20 from 020B69B8  queued Y, before Drill Kick / Down

k2_update:
  push {r4,lr}
  mov r4,r0
  bl rush_update
  mov r0,r4
  bl rico_update
  mov r0,r4
  bl vit_update
  mov r0,r4
  bl web_tick
  mov r0,r4
  bl drag_update
  mov r0,r4
  bl web_update
  mov r0,r4
  bl oc_update
  ldr r0,lit2_021341f4      // Red attack speed of the Reflex/Sense slots (native
  ldr r1,lit2_0000119a      // 1.15 and 1.3): 1.10 and 1.20 since v0.11.0. With
  ldr r2,lit2_00001333      // Momentum owned, combo tier 3 and up restores the
  ldr r3,[r4,#0xe8]         // native values: speed is earned through the meter.
  ldr r3,[r3,#8]
  tst r3,#0x1000
  beq speed_write
  ldr r3,lit2_02145c44
  ldr r3,[r3]
  cmp r3,#0x02000000
  blo speed_write
  cmp r3,#0x02400000
  bhs speed_write
  ldr r3,[r3]
  cmp r3,#3
  ldrge r1,lit2_00001266
  ldrge r2,lit2_000014cc
speed_write:
  str r1,[r0,#0x230]
  str r2,[r0,#0x22c]
  pop {r4,pc}

k2_owned:                   // r0=actor, r1=mask in ability word 2 -> r0=1 if Red and owned
  ldr r2,[r0,#0x34]
  cmp r2,#1
  moveq r0,#0
  bxeq lr
  ldr r2,[r0,#0xe8]
  ldr r2,[r2,#8]
  tst r2,r1
  movne r0,#1
  moveq r0,#0
  bx lr

// ---------------------------------------------------------------- Web Rush
// A (queue command 5) during a Red ground string: the nearest standing enemy
// beyond hit reach (7..56 units, same level; a held Left/Right picks the
// side) becomes the target. State 46 is re-entered and the node hook plays
// action 58 (three kicks at clocks 7, 9, 10) with the rush clip while the
// node stays the cancelled one, so the next Y continues the string after it.
// Spidey dashes by velocity to 4.5 units short of the target before the kicks.
// The engine moves him at most 5 units per update, so for a far target the
// clock is held on sample 2 (the laid-out dive) until 15 units are left
// (rush_glide, at most 16 updates).
k2_rush_try:
  push {r0,lr}
  bl web_try
  cmp r0,#0
  popne {r1,pc}
  pop {r0,lr}
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  sub sp,sp,#32
  mov r4,r0
  ldr r5,[r4,#0x44]
  mov r0,r5
  mov r1,#0x400
  bl k2_owned
  cmp r0,#0
  beq rush_no
  mov r2,#5
  str r2,[sp]
  mov r1,sp
  add r0,r4,#0x28
  bl 0x020cff0c
  cmp r0,#0
  beq rush_no
  ldr r10,lit2_02157020
  ldr r6,[r5,#0x30]
  ldr r0,[r10]              // a rush in flight chains only after its kicks
  cmp r0,#0
  beq rush_scan
  ldr r0,[r6,#0x178]
  cmp r0,#10
  blt rush_no
rush_scan:
  ldr r7,[r6,#0x7c]
  ldr r0,[r6,#0x160]
  add r7,r7,r0              // px
  ldr r8,[r6,#0x80]
  ldr r0,[r6,#0x164]
  add r8,r8,r0              // py
  bl 0x02152c5c             // kit_keys
  str r0,[sp,#4]
  ldr r9,lit2_02154c20
  ldr r11,[r9]              // tick
  add r9,r9,#0x20
  mov r0,#0
  str r0,[sp,#8]            // best actor
  ldr r0,lit2_7fffffff
  str r0,[sp,#12]           // best distance
  mov r0,#12
  str r0,[sp,#20]
rush_loop:
  ldr r0,[r9]
  cmp r0,#0
  beq rush_next
  ldr r1,[r9,#12]
  add r1,r1,#2
  cmp r1,r11
  bls rush_next
  ldr r1,[r9,#8]
  subs r1,r1,r8
  rsbmi r1,r1,#0
  cmp r1,#0x6000
  bgt rush_next
  ldr r2,[r9,#4]
  subs r2,r2,r7             // dx
  mov r3,r2
  rsbmi r3,r3,#0
  cmp r3,#0x7000            // already inside hit reach
  ble rush_next
  cmp r3,#0x38000           // 56 units
  bgt rush_next
  ldr r1,[sp,#4]
  tst r1,#0x10              // Right held: only enemies to the right
  beq rush_left
  cmp r2,#0
  blt rush_next
rush_left:
  tst r1,#0x20
  beq rush_near
  cmp r2,#0
  bgt rush_next
rush_near:
  ldr r1,[sp,#12]
  cmp r3,r1
  bge rush_next
  push {r2,r3}
  bl 0x02152c64             // kit_alive
  pop {r2,r3}
  cmp r0,#0
  beq rush_next
  ldr r0,[r9]
  push {r2,r3}
  bl k2_down
  pop {r2,r3}
  cmp r0,#0
  bne rush_next
  ldr r0,[r9]
  str r0,[sp,#8]
  str r3,[sp,#12]
  cmp r2,#0
  movgt r1,#1
  movle r1,#0
  str r1,[sp,#16]
  ldr r1,[r9,#4]
  subgt r1,r1,#0x4800
  addle r1,r1,#0x4800
  str r1,[sp,#24]           // stop x
rush_next:
  add r9,r9,#16
  ldr r0,[sp,#20]
  subs r0,r0,#1
  str r0,[sp,#20]
  bne rush_loop
  ldr r0,[sp,#8]
  cmp r0,#0
  beq rush_no
  str r0,[r10,#4]
  ldr r1,[sp,#16]
  str r1,[r10,#0x10]
  ldr r1,[sp,#24]
  str r1,[r10,#0xc]
  ldr r2,[r4,#0x80]         // a spin (node 16) resumes at its entry kick
  cmp r2,#16
  moveq r2,#15
  str r2,[r10,#8]
  mov r2,#1
  str r2,[r10]
  mov r2,#0
  str r2,[r10,#0x14]
  str r2,[r10,#0x1c]
  str r2,[r10,#0x64]
  mov r2,#5                 // consume the queued A
  str r2,[sp]
  mov r1,sp
  add r0,r4,#0x28
  bl 0x020cfc34
  mov r0,r5
  ldr r1,[r10,#0x10]
  bl 0x02152c60             // kit_face
  mov r0,#1
  add sp,sp,#32
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}
rush_no:
  mov r0,#0
  add sp,sp,#32
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

k2_node:                    // r0=controller, r1=the state he came from -> r0=action or 0
  push {r4,lr}
  ldr r4,lit2_02157020
  ldr r2,[r4]
  cmp r2,#1
  beq node_rush
  mov r2,#0                 // any other node start ends a rush
  str r2,[r4]
  ldr r2,[r4,#0x18]         // a routed clip was loaded (rush on 58, Vortex): make
  ldr r3,[r4,#0x84]         // the next commit look the resource up again
  orrs r2,r2,r3
  beq node_web
  mov r2,#0
  str r2,[r4,#0x18]
  str r2,[r4,#0x84]
  ldr r2,[r0,#0x44]
  ldr r2,[r2,#0x30]
  ldr r3,[r2,#0x2fc]
  orr r3,r3,#2
  str r3,[r2,#0x2fc]
node_web:
  bl web_node
  pop {r4,pc}
node_rush:
  mov r1,#2
  str r1,[r4]
  mov r1,#1
  str r1,[r4,#0x18]
  ldr r1,[r4,#8]
  str r1,[r0,#0x80]
  ldr r1,[r0,#0x44]
  ldr r1,[r1,#0x30]
  ldr r2,[r1,#0x2fc]
  orr r2,r2,#2
  str r2,[r1,#0x2fc]
  mov r0,#58
  pop {r4,pc}

k2_route:                   // r0=route kind (9 Web Rush, 10..13 Vortex) -> r0=1 while routed; keeps r1-r3
  ldr r12,lit2_02157020
  cmp r0,#9
  ldreq r12,[r12]
  moveq r0,#2
  ldrne r12,[r12,#0x80]
  cmp r12,r0
  moveq r0,#1
  movne r0,#0
  bx lr

rush_update:                // r0=actor
  push {r4,r5,r6,r7,lr}
  mov r4,r0
  ldr r5,lit2_02157020
  ldr r0,[r5]
  cmp r0,#0
  beq rushu_out
  ldr r6,[r4,#0x30]
  ldr r1,[r6,#0x1f8]
  cmp r1,#0
  beq rushu_clear
  ldr r2,[r1,#0x14]
  cmp r2,#46
  bne rushu_clear
  cmp r0,#1                 // armed: the node hook takes it on the re-entry
  bne rushu_fly
  ldr r0,[r5,#0x14]
  add r0,r0,#1
  str r0,[r5,#0x14]
  cmp r0,#2
  bgt rushu_clear
  b rushu_out
rushu_fly:
  ldr r0,[r6,#0x258]        // requested action; it is committed (+0x254, clock
  cmp r0,#58                // reset) after this hook on the first update
  bne rushu_clear
  ldr r7,[r6,#0x178]        // dash while the clock is below 6, then one last
  ldr r0,[r6,#0x254]        // step covers what is left; the kicks start at 7
  cmp r0,#58
  movne r7,#0
  cmp r7,#6
  blt rushu_dash
  ldr r0,[r5,#0x1c]
  cmp r0,#1
  beq rushu_last
  cmp r0,#2
  moveq r0,#0
  streq r0,[r5,#0x1c]
  streq r0,[r4,#0x18]
  b rushu_out
rushu_last:
  mov r0,#2
  str r0,[r5,#0x1c]
  mov r7,#5                 // one update left
  b rushu_aim
rushu_dash:
  mov r0,#1
  str r0,[r5,#0x1c]
rushu_aim:
  ldr r0,[r5,#4]
  bl 0x02152c68             // kit_fresh
  cmp r0,#0
  beq rushu_go
  ldr r0,[r5,#4]
  ldr r0,[r0,#0x30]
  ldr r1,[r0,#0x7c]
  ldr r0,[r0,#0x160]
  add r0,r0,r1
  ldr r1,[r5,#0x10]
  cmp r1,#1
  subeq r0,r0,#0x4800
  addne r0,r0,#0x4800
  str r0,[r5,#0xc]
rushu_go:
  ldr r0,[r5,#0xc]
  ldr r1,[r6,#0x7c]
  ldr r2,[r6,#0x160]
  add r1,r1,r2
  sub r0,r0,r1              // remaining
  rsb r1,r7,#6              // clocks left, 6..1
  adr r2,rush_recip
  ldr r2,[r2,r1,lsl #2]
  mul r3,r0,r2
  mov r0,r3,asr #8
  cmp r0,#0xc000            // at most 12 units per update
  movgt r0,#0xc000
  cmn r0,#0xc000
  ldrlt r0,lit2_ffff4000
  str r0,[r4,#0x18]
  b rushu_out
rushu_clear:
  ldr r0,[r5,#0x1c]
  cmp r0,#0
  movne r0,#0
  strne r0,[r4,#0x18]       // cut short mid-dash: drop the dash velocity
  mov r0,#0
  str r0,[r5]
  str r0,[r5,#0x1c]
rushu_out:
  pop {r4,r5,r6,r7,pc}
rush_recip: .word 0, 256, 128, 85, 64, 51, 43

// ---------------------------------------------------------------- literals
lit2_02154c20: .word 0x02154C20
lit2_02157020: .word 0x02157020
lit2_021341f4: .word 0x021341F4
lit2_02145c44: .word 0x02145C44
lit2_7fffffff: .word 0x7FFFFFFF
lit2_ffff4000: .word 0xFFFF4000
lit2_02145c5c: .word 0x02145C5C
lit2_02156fc0: .word 0x02156FC0
lit2_05000032: .word 0x05000032
lit2_0000119a: .word 0x0000119A
lit2_00001333: .word 0x00001333
lit2_00001266: .word 0x00001266
lit2_000014cc: .word 0x000014CC

// ---------------------------------------------------------------- strength dial
// Chapter rooms scale enemy health and the damage Spidey takes (table at
// 02156F20, see the top). A scaled enemy's max health is odd (native values
// are whole multiples of 16), which marks it as done.
k2_observe:                 // r0=enemy actor (common-health ABI checked by the caller)
  push {r1,r2,r3,r12,lr}
  ldr r1,lit2_02145c5c
  ldr r1,[r1]
  cmp r1,#0x02000000
  blo observe_out
  ldr r1,[r1]               // current room
  sub r1,r1,#76
  cmp r1,#40
  bhs observe_out
  ldr r2,lit2_02156fc0
  ldrb r2,[r2,r1,lsl #1]
  cmp r2,#0
  cmpne r2,#64
  beq observe_out
  ldr r1,[r0,#0x48]         // max health
  tst r1,#1
  bne observe_out
  cmp r1,#0x4000            // fighters only (the floating room object has about 1 unit)
  blt observe_out
  ldr r3,[r0,#0x44]
  cmp r3,#0
  ble observe_out
  cmp r3,r1                 // full health stays exactly full (flags survive to the beq)
  mul r12,r1,r2
  mov r1,r12,lsr #6
  orr r1,r1,#1
  str r1,[r0,#0x48]
  streq r1,[r0,#0x44]
  beq observe_out
  mul r12,r3,r2
  movs r3,r12,lsr #6
  moveq r3,#1
  str r3,[r0,#0x44]
observe_out:
  pop {r1,r2,r3,r12,pc}

// Damage to Spidey = native * room scale * Vitality (1/1.25, 1/1.5, 1/1.75 for
// levels I..III: each bar segment absorbs more), never less than 1 Q12.
k2_damage:                  // r1=HP before, r3=HP after (>= 0) -> r3
  push {r0,r2,r4,r5,lr}
  subs r4,r1,r3
  ble damage_out
  ldr r0,lit2_02145c5c
  ldr r0,[r0]
  cmp r0,#0x02000000
  blo damage_out
  mov r5,#256
  ldr r2,[r0]               // current room
  sub r2,r2,#76
  cmp r2,#40
  bhs damage_vitality
  ldr r12,lit2_02156fc0
  add r12,r12,r2,lsl #1
  ldrb r2,[r12,#1]
  cmp r2,#0
  movne r5,r2,lsl #2        // 1/64ths -> 1/256ths
damage_vitality:
  ldr r0,[r0,#0x14]         // ability word 2
  mov r2,#256
  tst r0,#0x2000
  movne r2,#205
  tst r0,#0x4000
  movne r2,#171
  tst r0,#0x8000
  movne r2,#146
  mul r12,r5,r2
  mov r5,r12,lsr #8
  cmp r5,#256
  beq damage_out
  mul r12,r4,r5
  movs r4,r12,lsr #8
  moveq r4,#1
  subs r3,r1,r4
  movmi r3,#0
damage_out:
  pop {r0,r2,r4,r5,pc}

// Vitality tints the Red health bar (top-screen BG palette colours 25..28 of
// HUDTop_8: bar shade, bar and emblem, emblem light, bar light): orange, gold,
// green. Written every update; the native reds return once after a refund.
vit_update:                 // r0=Spidey actor
  ldr r1,[r0,#0xe8]
  ldr r1,[r1,#8]
  mov r2,#0
  tst r1,#0x2000
  movne r2,#1
  tst r1,#0x4000
  movne r2,#2
  tst r1,#0x8000
  movne r2,#3
  ldr r3,lit2_02157020
  cmp r2,#0
  bne vit_write
  ldr r1,[r3,#0x68]
  cmp r1,#0
  bxeq lr
vit_write:
  str r2,[r3,#0x68]
  adr r1,vit_colors
  add r1,r1,r2,lsl #3
  ldr r3,lit2_05000032
  ldrh r2,[r1]
  strh r2,[r3]
  ldrh r2,[r1,#2]
  strh r2,[r3,#2]
  ldrh r2,[r1,#4]
  strh r2,[r3,#4]
  ldrh r2,[r1,#6]
  strh r2,[r3,#6]
  bx lr
vit_colors:                 // BGR555 x4 per level 0..3 (no word may look like a branch: bits 27..25 != 101)
  .word 0x0C77800D, 0x253D18DA
  .word 0x09BB00CF, 0x2EBF1A3D
  .word 0x0EBA014D, 0x339F1B1C
  .word 0x26C30D60, 0x47AC3326

// ---------------------------------------------------------------- Ricochet
// Passive. A registry enemy knocked down and still travelling at 1 unit per
// update or more (states 41/48/49) is a flying body: every other standing
// enemy within 3.5 units (5 vertically) of it takes Spidey's latest captured
// hit as a knockdown (kind 0x1F) through its own ReceiveHit, and so becomes a
// flying body itself. One hit per bystander per 24 ticks; the template must
// be at most 150 ticks old.
rico_update:                // r0=Spidey actor
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  mov r4,r0
  mov r1,#0x800
  bl k2_owned
  cmp r0,#0
  beq rico_out
  ldr r9,lit2_02154c20
  ldr r10,lit2_02157020
  ldr r11,[r9]
  ldr r0,[r9,#0x370]
  cmp r0,#0
  beq rico_out
  ldr r0,[r9,#0x36c]
  sub r0,r11,r0
  cmp r0,#150
  bhi rico_out
  mov r5,#0
rico_flyer:
  add r6,r9,#0x20
  add r6,r6,r5,lsl #4
  ldr r0,[r6]
  cmp r0,#0
  beq rico_next_flyer
  ldr r1,[r6,#12]
  add r1,r1,#2
  cmp r1,r11
  bls rico_next_flyer
  bl 0x02152c64             // kit_alive
  cmp r0,#0
  beq rico_next_flyer
  ldr r0,[r6]
  bl k2_flying
  cmp r0,#0
  beq rico_next_flyer
  mov r7,#0
rico_by:
  cmp r7,r5
  beq rico_next_by
  add r8,r9,#0x20
  add r8,r8,r7,lsl #4
  ldr r0,[r8]
  cmp r0,#0
  beq rico_next_by
  ldr r1,[r8,#12]
  add r1,r1,#2
  cmp r1,r11
  bls rico_next_by
  add r2,r10,#0x20
  ldr r1,[r2,r7,lsl #2]
  add r1,r1,#24
  cmp r1,r11
  bhi rico_next_by
  ldr r1,[r8,#4]
  ldr r2,[r6,#4]
  subs r1,r1,r2
  rsbmi r1,r1,#0
  cmp r1,#0x3800
  bgt rico_next_by
  ldr r1,[r8,#8]
  ldr r2,[r6,#8]
  subs r1,r1,r2
  rsbmi r1,r1,#0
  cmp r1,#0x5000
  bgt rico_next_by
  bl 0x02152c64             // kit_alive
  cmp r0,#0
  beq rico_next_by
  ldr r0,[r8]
  bl k2_down
  cmp r0,#0
  bne rico_next_by
  mov r0,#0x1f
  str r0,[r9,#0x380]
  str r0,[r9,#0x3f4]
  ldr r0,[r8]
  str r0,[r10,#0x54]
  bl 0x02152c6c             // kit_replay_hit
  ldr r1,[r10,#0x50]
  add r1,r1,r0,lsl #8
  add r1,r1,#1
  str r1,[r10,#0x50]
  add r2,r10,#0x20
  str r11,[r2,r7,lsl #2]
rico_next_by:
  add r7,r7,#1
  cmp r7,#12
  blo rico_by
rico_next_flyer:
  add r5,r5,#1
  cmp r5,#12
  blo rico_flyer
rico_out:
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

k2_flying:                  // r0=live enemy -> r0=1: knocked down and moving 1+ unit per update
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  moveq r0,#0
  bxeq lr
  ldr r1,[r1,#0x14]
  cmp r1,#41
  cmpne r1,#48
  cmpne r1,#49
  movne r0,#0
  bxne lr
  ldr r1,[r0,#0x18]
  cmp r1,#0
  rsblt r1,r1,#0
  cmp r1,#0x1000
  movge r0,#1
  movlt r0,#0
  bx lr

k2_down:                    // r0=live enemy -> r0=1 in a knockdown or get-up state
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  moveq r0,#0
  bxeq lr
  ldr r1,[r1,#0x14]
  cmp r1,#41
  cmpne r1,#48
  cmpne r1,#49
  cmpne r1,#51
  moveq r0,#1
  movne r0,#0
  bx lr

// ---------------------------------------------------------------- Momentum
// Passive. The native getter gives Red attack actions rate 1.0, 1.15 (bit 18)
// or 1.3 (bit 19) from the tuning block 021341F4, and the engine tests the
// attack box of the GMB sample the clock lands on. A plain higher rate lands
// on other samples and drops hits (action 58: 3 hits at 1.3, 1 at 1.65), so
// Momentum only ever doubles a step: the clock stays on the native grid and
// skips one grid point, and only where the two samples that point can fall in
// (clock+1, clock+2) have no active attack box. momentum_blocked holds those
// clocks per ground string action 56..62 (bit = clock; from the GMB windows,
// tests/test_tasm_kit.py); momentum_last also keeps the clock from jumping over
// an action's last sample (v0.11.0). Per call the accumulator +0x5C gains the combo
// tier + 1 ([02145C44] -> +0 tier 1..5; nothing at tier 0) and a step doubles
// at 5, so tier t doubles t+1 of 5 free steps and tier 4 doubles them all
// (v0.10.0: t of 5). Left native: other actions, the Spider-Sense counter and
// a Web Rush dash (both timed to the native clock), and without bit 18 the
// native string freeze (state 46, controller+0x64 bit 0x4000).
h_momentum:                 // r6=controller, r7=&rate; native: ldr r0,[r6,#0x44]
  push {r1,r2,r3,r12,lr}
  ldr r0,[r6,#0x44]
  bl rush_glide
  cmp r0,#0
  bne momentum_ret
  ldr r0,[r6,#0x44]
  mov r1,r6
  bl momentum_rate
momentum_ret:
  pop {r1,r2,r3,r12,lr}
  cmp r0,#0
  bne momentum_take
  ldr r0,[r6,#0x44]
  b 0x020b21bc
momentum_take:
  str r0,[r7]
  add sp,sp,#0x10
  pop {r3,r4,r5,r6,r7,pc}

rush_glide:                 // r0=actor -> r0 = 1 (rate: hold the dive sample) or 0
  ldr r1,lit2_02157020
  ldr r2,[r1]
  cmp r2,#2
  bne glide_no
  ldr r2,[r1,#0x1c]
  cmp r2,#1
  bne glide_no
  ldr r0,[r0,#0x30]
  ldr r2,[r0,#0x254]
  cmp r2,#58
  bne glide_no
  ldr r2,[r0,#0x178]
  cmp r2,#2
  bne glide_no
  ldr r2,[r0,#0x7c]
  ldr r3,[r0,#0x160]
  add r2,r2,r3
  ldr r3,[r1,#0xc]
  subs r2,r3,r2
  rsbmi r2,r2,#0
  cmp r2,#0xf000
  ble glide_no
  ldr r2,[r1,#0x64]
  add r2,r2,#1
  str r2,[r1,#0x64]
  cmp r2,#16
  bgt glide_no
  mov r0,#1
  bx lr
glide_no:
  mov r0,#0
  bx lr

momentum_rate:              // r0=actor, r1=controller -> r0 = doubled rate (Q12) or 0 for native
  push {r4,r5,lr}
  mov r4,r1
  ldr r5,lit2_02157020
  ldr r1,[r0,#0x34]
  cmp r1,#0
  bne momentum_none
  ldr r1,[r0,#0xe8]
  ldr r2,[r1,#8]
  tst r2,#0x1000
  beq momentum_none
  ldr r3,lit2_02154c20
  ldr r3,[r3,#0x340]
  cmp r3,#0
  bne momentum_none
  ldr r0,[r0,#0x30]
  ldr r2,[r0,#0x254]        // action 56..62
  sub r2,r2,#56
  cmp r2,#6
  bhi momentum_none
  ldr r3,[r0,#0x178]        // clock
  cmp r2,#2                 // action 58 during a Web Rush: native until the kicks
  bne momentum_window
  ldr r0,[r5]
  cmp r0,#2
  bne momentum_window
  cmp r3,#7
  blt momentum_none
momentum_window:
  adr r0,momentum_last      // never skip an action's last sample: the string blocker
  ldrb r0,[r0,r2]           // (020B53F8) only decides "repeat or end" on it, and a spin
  sub r0,r0,#2              // whose loop jumps over it never stops (lab, rate 1.2 doubled)
  cmp r3,r0
  bge momentum_none
  cmp r3,#31
  bhi momentum_free
  adr r0,momentum_blocked
  ldr r0,[r0,r2,lsl #2]
  mov r2,#1
  tst r0,r2,lsl r3
  bne momentum_none
momentum_free:
  ldr r2,lit2_02145c44
  ldr r2,[r2]
  cmp r2,#0x02000000
  blo momentum_none
  cmp r2,#0x02400000
  bhs momentum_none
  ldr r2,[r2]
  cmp r2,#0
  ble momentum_none
  add r2,r2,#1              // v0.11.0: tier t doubles t+1 of 5 free steps
  cmp r2,#5
  movgt r2,#5
  ldr r0,[r5,#0x5c]
  add r0,r0,r2
  cmp r0,#5
  strlt r0,[r5,#0x5c]
  blt momentum_none
  sub r0,r0,#5
  str r0,[r5,#0x5c]
  ldr r2,[r1]
  ldr r3,lit2_021341f4
  tst r2,#0x40000
  bne momentum_boost
  ldr r0,[r4,#0x14]
  cmp r0,#46
  bne momentum_plain
  ldr r0,[r4,#0x64]
  tst r0,#0x4000
  bne momentum_none
momentum_plain:
  mov r0,#0x1000
  b momentum_double
momentum_boost:
  ldr r0,[r3,#0x230]
  tst r2,#0x80000
  ldrne r0,[r3,#0x22c]
momentum_double:
  mov r0,r0,lsl #1
  str r0,[r5,#0x58]
  ldr r1,[r5,#0x60]
  add r1,r1,#1
  str r1,[r5,#0x60]
  pop {r4,r5,pc}
momentum_none:
  mov r0,#0
  str r0,[r5,#0x58]
  pop {r4,r5,pc}
momentum_blocked: .word 0x39C, 0x7, 0x3E0, 0x1C, 0x39C, 0x71C38, 0x70
momentum_last: .word 0x1219100B, 0x0013260B             // bytes 11, 16, 25, 18, 11, 38, 19: last sample of actions 56..62
// (GMB record count - 1). Words, not .byte: Keystone shifts every later absolute branch by the size of a .byte run.

// ---------------------------------------------------------------- web lines
// The game's own WebLine actor (vtable 0212EFBC): Spidey spawns one with
// 0205F844(&out, &spidey, &from, &to, &colour), moves its start with 0206632C,
// ties it to an actor with 020672D0(line, &actor, 1) (the end then follows
// him) and lets go with 02066FDC (the line retracts and deletes itself). The
// kit keeps up to eight of its own in 16-byte slots at K2+0x100: {weak link to
// line+4, link next, enemy actor, age}. The link is the game's own intrusive
// weak reference, so a line that dies clears it. Age 0 = held by Dragnet,
// otherwise the updates left before the line lets go (a "flash" line).
web_hand:                   // r0=Spidey actor, r1=out {x, y}
  ldr r2,[r0,#0x30]
  ldr r3,[r2,#0x7c]
  ldr r12,[r2,#0x160]
  add r3,r3,r12
  ldr r12,[r2,#0x180]
  cmp r12,#1
  addeq r3,r3,#0xe00
  subne r3,r3,#0xe00
  str r3,[r1]
  ldr r3,[r2,#0x80]
  ldr r12,[r2,#0x164]
  add r3,r3,r12
  add r3,r3,#0x800
  str r3,[r1,#4]
  bx lr

web_spawn:                  // r0=slot, r1=Spidey actor, r2=to x, r3=to y -> r0=line or 0
  push {r4,r5,lr}
  sub sp,sp,#0x2c
  mov r4,r0
  mov r5,r1
  str r2,[sp,#0x10]
  str r3,[sp,#0x14]
  mov r0,r5
  add r1,sp,#8
  bl web_hand
  ldr r0,lit3_00007fff
  str r0,[sp,#0x18]
  str r5,[sp,#0x1c]
  mov r0,#0
  str r0,[sp,#0x20]
  add r0,sp,#0x18
  str r0,[sp]
  add r0,sp,#0x20
  add r1,sp,#0x1c
  add r2,sp,#8
  add r3,sp,#0x10
  bl 0x0205f844
  ldr r0,[sp,#0x20]
  cmp r0,#0
  beq web_spawn_out
  add r1,r0,#4
  str r1,[r4]
  ldr r2,[r1]
  str r2,[r4,#4]
  str r4,[r1]
web_spawn_out:
  add sp,sp,#0x2c
  pop {r4,r5,pc}

web_release:                // r0=slot: let go of its target, retract, drop the link
  push {r4,lr}
  mov r4,r0
  ldr r0,[r4]
  cmp r0,#0
  beq web_release_out
  sub r0,r0,#4
  bl 0x02066fdc
  ldr r1,[r4]               // unlink (the line lives on until it has retracted)
  cmp r1,#0
  beq web_release_out
  ldr r3,[r1]
web_unlink_loop:
  cmp r3,#0
  beq web_release_out
  cmp r3,r4
  beq web_unlink_found
  add r1,r3,#4
  ldr r3,[r3,#4]
  b web_unlink_loop
web_unlink_found:
  ldr r2,[r4,#4]
  str r2,[r1]
web_release_out:
  mov r0,#0
  str r0,[r4]
  str r0,[r4,#4]
  str r0,[r4,#8]
  str r0,[r4,#12]
  pop {r4,pc}

web_line:                   // r0=live enemy, r1=Spidey actor, r2=age -> r0=slot or 0
  push {r4,r5,r6,r7,lr}
  sub sp,sp,#4
  mov r4,r0
  mov r5,r1
  mov r6,r2
  ldr r7,lit3_02157020
  add r7,r7,#0x100
  mov r3,#8
web_line_find:
  ldr r0,[r7]
  cmp r0,#0
  beq web_line_take
  add r7,r7,#16
  subs r3,r3,#1
  bne web_line_find
  mov r0,#0
  b web_line_out
web_line_take:
  ldr r1,[r4,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3
  ldr r3,[r1,#0x80]
  ldr r12,[r1,#0x164]
  add r3,r3,r12
  mov r0,r7
  mov r1,r5
  bl web_spawn
  cmp r0,#0
  beq web_line_out
  str r4,[r7,#8]
  str r6,[r7,#12]
  str r4,[sp]
  mov r1,sp
  mov r2,#1
  bl 0x020672d0
  mov r0,r7
web_line_out:
  add sp,sp,#4
  pop {r4,r5,r6,r7,pc}

web_tick:                   // r0=Spidey actor: every line starts at his hand; flash lines age
  push {r4,r5,r6,lr}
  sub sp,sp,#8
  mov r4,r0
  ldr r5,lit3_02157020
  add r5,r5,#0x100
  mov r6,#8
web_tick_loop:
  ldr r0,[r5]
  cmp r0,#0
  bne web_tick_live
  str r0,[r5,#8]            // the line is gone: the slot is free
  str r0,[r5,#12]
  b web_tick_next
web_tick_live:
  mov r0,r4
  mov r1,sp
  bl web_hand
  ldr r0,[r5]
  sub r0,r0,#4
  mov r1,sp
  bl 0x0206632c
  ldr r0,[r5,#12]
  cmp r0,#0
  beq web_tick_held
  subs r0,r0,#1
  str r0,[r5,#12]
  bne web_tick_next
web_tick_drop:
  mov r0,r5
  bl web_release
  b web_tick_next
web_tick_held:              // a held line never outlives Dragnet
  ldr r0,lit3_02157020
  ldr r0,[r0,#0xc0]
  cmp r0,#0
  beq web_tick_drop
web_tick_next:
  add r5,r5,#16
  subs r6,r6,#1
  bne web_tick_loop
  add sp,sp,#8
  pop {r4,r5,r6,pc}

// Literals of the web block (a literal load reaches 4 KiB).
lit3_00007fff: .word 0x00007FFF
lit3_00040000: .word 0x00040000
lit3_02120000: .word 0x02120000
lit3_0213df00: .word 0x0213DF00
lit3_02145c44: .word 0x02145C44
lit3_02154c20: .word 0x02154C20
lit3_02157020: .word 0x02157020
lit3_7fffffff: .word 0x7FFFFFFF

// web_hit(r0=enemy actor, r1=attack kind, r2=damage Q12, r3=Spidey actor) ->
// r0 = native result (4 taken, 1 ignored, 0 none). The hit is built from
// nothing in K2+0x1C0 (info 0x40 bytes, extent record +0x200, contact record
// +0x220, attacker cell +0x1BC), so it needs no earlier captured hit: the
// victim's own ReceiveHit ([[actor+8]+0x40]) picks the reaction by kind and
// takes its fifth argument off his health (lab: 0 for the web hold costs
// nothing, 0x800 costs 2048); the response strength is a fixed 0xC00.
// Kinds used: 0x22 web hold (state 46), 0x21 web yank (he flies to Spidey and
// lands at his feet), 0x04 stagger, 0x16 stagger, 0x1F knockdown.
web_hit:
  push {r4,r5,r6,r7,lr}
  sub sp,sp,#0x14
  mov r4,r0
  mov r5,r1
  mov r6,r2
  mov r7,r3
  bl 0x02152c64             // kit_alive
  cmp r0,#0
  beq web_hit_none
  ldr r12,[r4,#8]
  ldr r2,lit3_02120000      // only real actors: interface vtable in the class range
  cmp r12,r2
  blo web_hit_none
  ldr r2,lit3_0213df00
  cmp r12,r2
  bhi web_hit_none
  ldr r0,lit3_02157020
  add r0,r0,#0x1c0
  mov r1,#0
  mov r2,#0
web_hit_clear:
  str r1,[r0,r2]
  add r2,r2,#4
  cmp r2,#0x80
  blo web_hit_clear
  str r7,[r0,#-4]           // attacker cell
  str r5,[r0]               // info: kind, strength, 3, &extent, &contact
  mov r1,#0xc00
  str r1,[r0,#4]
  mov r1,#3
  str r1,[r0,#8]
  add r1,r0,#0x40
  str r1,[r0,#0xc]
  add r1,r0,#0x60
  str r1,[r0,#0x10]
  mov r1,#0x4000
  str r1,[r0,#0x18]
  mov r1,#7
  str r1,[r0,#0x1c]
  mov r1,#0x1000
  str r1,[r0,#0x2c]
  ldr r2,[r7,#0x30]         // contact record: {attacker part, 3, victim part 0, 5, 0, kind, part, strength}
  add r1,r2,#0x2b4
  str r1,[r0,#0x60]
  mov r1,#3
  str r1,[r0,#0x64]
  mov r1,#5
  str r1,[r0,#0x6c]
  str r5,[r0,#0x74]
  add r1,r2,#0x310
  str r1,[r0,#0x78]
  mov r1,#0xc00
  str r1,[r0,#0x7c]
  mov r3,r0
  sub r2,r0,#4
  mov r0,#0
  str r0,[sp,#8]
  str r6,[sp]               // fifth argument: the health the hit takes (Q12)
  add r0,sp,#8
  add r1,r4,#8
  ldr r12,[r12,#0x40]
  blx r12
  ldr r0,[sp,#8]
  add sp,sp,#0x14
  pop {r4,r5,r6,r7,pc}
web_hit_none:
  mov r0,#0
  add sp,sp,#0x14
  pop {r4,r5,r6,r7,pc}

k2_fighter:                 // r0=live actor -> r0=actor, flags HS for a fighter (max health 4 units and up;
  ldr r1,[r0,#0x48]         // the floating room object has about one)
  cmp r1,#0x4000
  bx lr

k2_state:                   // r0=live actor -> r0=controller state or -1
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  mvneq r0,#0
  ldrne r0,[r1,#0x14]
  bx lr

// ---------------------------------------------------------------- Dragnet
// Ability word 2 bit 0x20000. Keep A held through the web grapple: after 12
// updates of the hold up to four more standing enemies in front (48 units,
// same level) get a line of their own and the web hold (kind 0x22). Y in
// that hold yanks all of them and the first target (kind 0x21): they fly to
// Spidey and land at his feet, and he plays the heave (Vortex step 4) in
// state 46, so the next Y continues into Vortex. The flight needs a line on
// the enemy, and the game lets go of its own line as the hold ends: the
// first target gets a kit line and his yank one update later (+0xD0). Any
// other exit of the hold only lets the lines go (the enemies stay webbed
// until they break out).
// +0xC0 phase (1 lines out, 2 yanked), +0xC4 enemies webbed by the last
// burst, +0xC8 updates A was held in the grapple, +0xCC phase timer.
drag_update:                // r0=Spidey actor
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  sub sp,sp,#0x14
  mov r4,r0
  ldr r10,lit3_02157020
  ldr r5,[r4,#0x30]
  ldr r6,[r5,#0x1f8]
  cmp r6,#0
  beq drag_out
  ldr r7,[r6,#0x14]         // state
  ldr r0,lit3_02154c20
  ldr r0,[r0,#0x360]
  ldr r1,[r10,#0xc8]
  tst r0,#1
  addne r1,r1,#1
  moveq r1,#0
  cmp r7,#37
  cmpne r7,#38
  movne r1,#0
  str r1,[r10,#0xc8]
  ldr r0,[r10,#0xcc]
  add r0,r0,#1
  str r0,[r10,#0xcc]
  ldr r0,[r10,#0xc0]
  cmp r0,#0
  bne drag_live
  cmp r7,#38
  bne drag_out
  cmp r1,#12
  blt drag_out
  mov r0,r4
  mov r1,#0x20000
  bl k2_owned
  cmp r0,#0
  beq drag_out
  ldr r11,[r6,#0x54]        // the natively grappled target
  cmp r11,#0
  beq drag_out
  sub r11,r11,#4
  ldr r0,[r5,#0x7c]
  ldr r1,[r5,#0x160]
  add r0,r0,r1
  str r0,[sp]               // px
  ldr r0,[r5,#0x80]
  ldr r1,[r5,#0x164]
  add r0,r0,r1
  str r0,[sp,#4]            // py
  ldr r0,[r5,#0x180]
  str r0,[sp,#8]            // facing (1 right)
  ldr r9,lit3_02154c20
  ldr r8,[r9]               // tick
  add r9,r9,#0x20
  mov r7,#0                 // lines out
  mov r6,#12
drag_scan:
  ldr r0,[r9]
  cmp r0,#0
  cmpne r0,r11
  beq drag_next
  ldr r1,[r9,#12]
  add r1,r1,#2
  cmp r1,r8
  bls drag_next
  ldr r1,[r9,#8]
  ldr r2,[sp,#4]
  subs r1,r1,r2
  rsbmi r1,r1,#0
  cmp r1,#0xa000
  bgt drag_next
  ldr r1,[r9,#4]
  ldr r2,[sp]
  subs r1,r1,r2             // dx
  ldr r2,[sp,#8]
  rsbmi r1,r1,#0
  eormi r2,r2,#1            // left of him: counts when he faces left
  cmp r2,#1
  bne drag_next
  cmp r1,#0x30000
  bgt drag_next
  bl 0x02152c64             // kit_alive
  cmp r0,#0
  beq drag_next
  ldr r0,[r9]
  bl k2_fighter
  blo drag_next
  bl k2_down
  cmp r0,#0
  bne drag_next
  ldr r0,[r9]
  mov r1,r4
  mov r2,#0
  bl web_line
  cmp r0,#0
  beq drag_armed            // no slot left
  ldr r0,[r9]
  mov r1,#0x22
  mov r2,#0
  mov r3,r4
  bl web_hit
  add r7,r7,#1
  cmp r7,#4
  bhs drag_armed
drag_next:
  add r9,r9,#16
  subs r6,r6,#1
  bne drag_scan
drag_armed:
  str r7,[r10,#0xc4]
  cmp r7,#0
  movne r0,#1
  strne r0,[r10,#0xc0]
  mov r0,#0
  str r0,[r10,#0xcc]
  sub r0,r0,#0x4000         // one burst per press of A
  str r0,[r10,#0xc8]
  b drag_out
drag_live:
  cmp r0,#2
  beq drag_fly
  cmp r7,#37                // lines out: they hold while he holds
  cmpne r7,#38
  bne drag_drop
  ldr r0,[r10,#0xcc]
  cmp r0,#8                 // the hold reaction is committed a few updates later
  blt drag_out
  mov r8,#46
  b drag_sweep
drag_fly:                   // yanked: a line lets go when its enemy has landed
  ldr r9,[r10,#0xd0]        // the first target: his own line, then the yank
  cmp r9,#0
  beq drag_fly_time
  mov r0,#0
  str r0,[r10,#0xd0]
  mov r0,r9
  bl 0x02152c68             // kit_fresh
  cmp r0,#0
  beq drag_fly_time
  mov r0,r9
  mov r1,r4
  mov r2,#0
  bl web_line
  cmp r0,#0
  beq drag_fly_time
  mov r0,r9
  mov r1,#0x21
  mov r2,#0x800
  mov r3,r4
  bl web_hit
drag_fly_time:
  ldr r0,[r10,#0xcc]
  cmp r0,#30
  bge drag_drop
  cmp r0,#6
  blt drag_out
  mov r8,#44
drag_sweep:                 // release the Dragnet lines whose enemy left state r8
  add r9,r10,#0x100
  mov r6,#8
  mov r7,#0                 // lines still out
drag_sweep_loop:
  ldr r0,[r9]
  cmp r0,#0
  beq drag_sweep_next
  ldr r0,[r9,#12]
  cmp r0,#0
  bne drag_sweep_next
  ldr r0,[r9,#8]
  bl 0x02152c68             // kit_fresh
  cmp r0,#0
  beq drag_sweep_free
  ldr r0,[r9,#8]
  bl k2_state
  cmp r0,r8
  addeq r7,r7,#1
  beq drag_sweep_next
drag_sweep_free:
  mov r0,r9
  bl web_release
drag_sweep_next:
  add r9,r9,#16
  subs r6,r6,#1
  bne drag_sweep_loop
  cmp r7,#0
  streq r7,[r10,#0xc0]
  b drag_out
drag_drop:
  add r9,r10,#0x100
  mov r6,#8
drag_drop_loop:
  ldr r0,[r9,#12]
  cmp r0,#0
  bne drag_drop_next        // (never 'bleq label': Keystone encodes it as a branch to itself)
  mov r0,r9
  bl web_release
drag_drop_next:
  add r9,r9,#16
  subs r6,r6,#1
  bne drag_drop_loop
  mov r0,#0
  str r0,[r10,#0xc0]
drag_out:
  add sp,sp,#0x14
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

h_yank:                     // r6=controller, a Y is queued in the web hold; native: ldr r0,[r6,#0x44]
  push {r1,r2,r3,r12,lr}
  ldr r1,lit3_02157020
  ldr r0,[r1,#0xc0]
  cmp r0,#1
  bne yank_native
  mov r0,r6
  bl yank_fire
  pop {r1,r2,r3,r12,lr}
  add sp,sp,#0x10c
  mov r0,#46
  pop {r4,r5,r6,r7,pc}
yank_native:
  pop {r1,r2,r3,r12,lr}
  ldr r0,[r6,#0x44]
  b 0x020b6034

yank_fire:                  // r0=controller
  push {r4,r5,r6,r7,lr}
  sub sp,sp,#4
  mov r4,r0
  ldr r5,[r4,#0x44]
  ldr r6,lit3_02157020
  mov r2,#1                 // consume the queued Y
  str r2,[sp]
  mov r1,sp
  add r0,r4,#0x28
  bl 0x020cfc34
  ldr r0,[r4,#0x54]         // the first target follows from drag_update
  cmp r0,#0
  subne r0,r0,#4
  str r0,[r6,#0xd0]
  add r7,r6,#0x100
  mov r4,#8
yank_loop:
  ldr r0,[r7]
  cmp r0,#0
  beq yank_next
  ldr r0,[r7,#12]
  cmp r0,#0
  bne yank_next
  ldr r0,[r7,#8]
  mov r1,#0x21
  mov r2,#0x800
  mov r3,r5
  bl web_hit
yank_next:
  add r7,r7,#16
  subs r4,r4,#1
  bne yank_loop
  mov r0,#2
  str r0,[r6,#0xc0]
  mov r0,#0
  str r0,[r6,#0xcc]
  mov r0,#1
  str r0,[r6,#0x94]
  add sp,sp,#4
  pop {r4,r5,r6,r7,pc}

// ---------------------------------------------------------------- Vortex
// Ability word 2 bit 0x40000. Down+Y after native hit 2, its old pause entry,
// or a Dragnet yank. Four queued Y steps: whip, lash, lash, slam. R cancels
// retain the parked node; native dodge-Y Drill Kick is bypassed only here.
// No string node is spent: the node hook swaps the action and parks the node
// on 12 (14 for the last step), as Web Rush does. Steps (+0x7C): 1 whip
// (action 57), 2 double lash (56), 3 slam (59), 4 the Dragnet heave (49).
// Each contact of a step also lands on every enemy within 14 units on either
// side (8 vertically) who was not hit natively in the last two ticks: a
// built hit (web_hit) of the step's kind and damage, one update after the
// clock reaches the contact's first active sample (or when the action ends).
// +0x80 route kind of the step's clip (10 heave, 11..13), +0x84 clip loaded,
// +0x88 contacts seen (bits 0-1) and delivered (bits 4-5), +0x8C clean (hit 2
// played, no dodge since), +0x90 hits (count + 256 * results), +0x94 heave
// armed, +0x98 pause window extended, +0x9C updates to skip after a step
// starts (its action is committed one update later), +0xA0 direct entry armed,
// +0xA4 extra lash played. Up/A/B/R keep their native exits.
h_vortex_stand:
  push {r1,lr}              // native r1 is the queued command pointer
  mov r0,r8
  bl web_try
  cmp r0,#0
  pop {r1,lr}
  moveq r5,#0
  beq 0x020b69bc
  cmp r0,#2
  mvneq r0,#0x80000000       // let the native dodge finish, retaining queued Y
  movne r0,#46
  add sp,sp,#0x30
  pop {r4,r5,r6,r7,r8,pc}

web_node:                   // r0=controller, r1=previous state -> r0=action or 0
  push {r4,r5,r6,r7,lr}
  mov r5,r0
  mov r6,r1
  ldr r4,lit3_02157020
  mov r0,#0
  str r0,[r4,#0x80]
  ldr r7,[r5,#0x80]         // the node the native entry chose
  ldr r0,[r4,#0x94]
  cmp r0,#0
  bne web_heave
  ldr r0,[r4,#0x7c]
  cmp r0,#0
  beq web_pause
  cmp r7,#13                // a step continues only from the parked node 12
  bne web_end
  cmp r0,#3
  beq web_end               // the slam was the last step
  cmp r0,#2
  bne web_advance
  ldr r1,[r4,#0xa4]         // one extra double lash, with the next Y
  cmp r1,#1
  movlo r1,#1
  strlo r1,[r4,#0xa4]
  blo web_owned
web_advance:
  movhi r0,#0               // after the heave: the whip
  add r0,r0,#1
  b web_owned
web_pause:
  cmp r7,#13
  bne web_end
  ldr r0,[r4,#0xa0]         // Down+Y was consumed in hit 2 by web_try
  cmp r0,#0
  bne web_start
  cmp r6,#46                // no pause: the Y came during hit 2
  beq web_end
  ldr r0,[r4,#0x8c]
  cmp r0,#0
  beq web_end
web_start:
  mov r0,#1
web_owned:
  mov r7,r0
  ldr r0,[r5,#0x44]
  ldr r1,lit3_00040000
  bl k2_owned
  cmp r0,#0
  beq web_end
  mov r0,r7
  cmp r0,#3
  movlo r1,#12
  movhs r1,#14
  b web_play
web_heave:
  mov r0,#0
  str r0,[r4,#0x94]
  mov r0,#4
  mov r1,#12
web_play:                   // r0=step, r1=node to park on
  mov r2,#0
  str r2,[r4,#0xa0]
  cmp r0,#1
  streq r2,[r4,#0xa4]
  str r0,[r4,#0x7c]
  str r1,[r5,#0x80]
  and r1,r0,#3              // route kinds: heave 10, steps 11..13
  add r1,r1,#10
  str r1,[r4,#0x80]
  mov r1,#1
  str r1,[r4,#0x84]
  str r1,[r4,#0x9c]
  mov r1,#0
  str r1,[r4,#0x88]
  ldr r1,[r5,#0x44]         // same action as the one before: look the resource up again
  ldr r1,[r1,#0x30]
  ldr r2,[r1,#0x2fc]
  orr r2,r2,#2
  str r2,[r1,#0x2fc]
  adr r1,web_actions
  ldr r0,[r1,r0,lsl #2]
  pop {r4,r5,r6,r7,pc}
web_end:
  mov r0,#0
  str r0,[r4,#0x7c]
  pop {r4,r5,r6,r7,pc}

// A buffered Down+Y during native hit 2 enters without waiting for idle.
// Keep plain Y strings, the native standing Down attack and R cancels intact.
web_try:                    // r0=controller -> 1 to re-enter state 46
  push {r4,r5,lr}
  sub sp,sp,#4
  mov r4,r0
  ldr r1,[r4,#0x80]
  cmp r1,#12
  bne web_try_no
  ldr r5,lit3_02157020
  ldr r1,[r5,#0x7c]
  cmp r1,#3                 // the slam ends this string
  beq web_try_no
  ldr r0,[r4,#0x44]
  ldr r1,lit3_00040000
  bl k2_owned
  cmp r0,#0
  beq web_try_no
  bl 0x02152c5c             // held keys, Down (0x80), R takes precedence
  tst r0,#0x100
  bne web_try_no
  tst r0,#0x43              // Up/A/B keep their native exits (and A's Web Rush)
  bne web_try_no
  ldr r1,[r5,#0x7c]
  cmp r1,#0
  bne web_try_active
  tst r0,#0x80
  beq web_try_no
  ldr r0,[r4,#0x44]
  ldr r0,[r0,#0x30]
  ldr r0,[r0,#0x178]
  ldr r1,[r4,#0x14]
  cmp r1,#46
  movne r0,#4               // between hits, idle/duck clock is unrelated
  cmp r0,#4                 // native hit 2 contact (2..3) must finish first
  blt web_try_no
  b web_try_consume
web_try_active:
  ldr r0,[r4,#0x14]
  cmp r0,#46
  beq web_try_window
  cmp r0,#6                 // ground idle/movement after an attack or dodge
  bls web_try_consume
  cmp r0,#24                // the roll lands here before becoming idle
  beq web_try_consume
  cmp r0,#53
  cmpne r0,#54
  cmpne r0,#57
  bne web_try_no            // never ground-enter from a jump/hurt/web hold
  mov r0,#2                 // entry from state 57 itself would still Drill Kick
  b web_try_out             // leave Y queued until the native idle transition
web_try_window:
  mov r2,#11                // lash's last sample; finish both contacts
  cmp r1,#1
  moveq r2,#16              // whip
  cmp r1,#4
  moveq r2,#9               // Dragnet heave
  ldr r0,[r4,#0x44]
  ldr r0,[r0,#0x30]
  ldr r0,[r0,#0x178]
  cmp r0,r2
  blt web_try_no
web_try_consume:
  mov r2,#1
  str r2,[sp]
  mov r1,sp
  add r0,r4,#0x28
  bl 0x020cff0c
  cmp r0,#0
  beq web_try_no
  mov r1,sp
  add r0,r4,#0x28
  bl 0x020cfc34
  mov r0,#1
  str r0,[r5,#0xa0]
  b web_try_out
web_try_no:
  mov r0,#0
web_try_out:
  add sp,sp,#4
  pop {r4,r5,pc}
web_actions: .word 0, 57, 56, 59, 49       // words: a byte table could read as a branch to the build's checks
// Per step two contacts: first active sample (255 = none), kind, damage / 256.
web_contacts:               // bytes: sample, kind, strength / 256, 0
  .word 0x000000FF, 0x000000FF
  .word 0x000C0402, 0x00080408
  .word 0x00080404, 0x00080409
  .word 0x00101F04, 0x000000FF
  .word 0x000000FF, 0x000000FF

web_update:                 // r0=Spidey actor
  push {r4,r5,r6,r7,r8,r9,lr}
  mov r4,r0
  ldr r5,lit3_02157020
  ldr r6,[r4,#0x30]
  ldr r7,[r6,#0x1f8]
  cmp r7,#0
  beq web_update_out
  ldr r8,[r7,#0x14]         // state
  ldr r9,[r7,#0x80]         // node
  cmp r8,#46
  bne web_away
  mov r0,#0
  str r0,[r5,#0x98]
  cmp r9,#12
  moveq r0,#1
  str r0,[r5,#0x8c]
  b web_step
web_away:
  cmp r8,#38                // the heave is armed in the web hold
  moveq r0,#0
  movne r0,#1
  cmp r8,#0
  cmpne r8,#1
  cmpne r8,#4
  cmpne r8,#6
  beq web_stand
  mov r1,#0                 // a dodge, a jump or a hit: no pause entry
  str r1,[r5,#0x8c]
  cmp r0,#0
  strne r1,[r5,#0x94]
  b web_step
web_stand:                  // back on his feet after hit 2: a longer window for the pause
  mov r1,#0
  str r1,[r5,#0x94]
  ldr r0,[r5,#0x8c]
  cmp r0,#0
  beq web_step
  cmp r9,#12
  bne web_step
  ldr r0,[r5,#0x98]
  cmp r0,#0
  bne web_step
  mov r0,#1
  str r0,[r5,#0x98]
  mov r0,r4
  ldr r1,lit3_00040000
  bl k2_owned
  cmp r0,#0
  movne r0,#16
  strbne r0,[r7,#0x90]
web_step:
  ldr r0,[r5,#0x7c]
  cmp r0,#0
  beq web_update_out
  ldr r1,[r5,#0x9c]         // the step's action is committed after this update
  cmp r1,#0
  movne r1,#0
  strne r1,[r5,#0x9c]
  bne web_update_out
  adr r1,web_actions
  ldr r1,[r1,r0,lsl #2]
  ldr r2,[r6,#0x254]
  cmp r8,#46
  cmpeq r2,r1
  bne web_flush
  ldr r3,[r6,#0x178]        // clock
  adr r2,web_contacts
  add r2,r2,r0,lsl #3
  mov r0,#0
web_contact:
  ldrb r1,[r2,r0,lsl #2]
  cmp r3,r1
  blt web_contact_next
  ldr r12,[r5,#0x88]
  mov r1,#1
  mov r1,r1,lsl r0
  tst r12,r1
  orreq r12,r12,r1          // first sight: the native hit lands this tick
  streq r12,[r5,#0x88]
  beq web_contact_next
  tst r12,r1,lsl #4
  bne web_contact_next
  orr r12,r12,r1,lsl #4
  str r12,[r5,#0x88]
  push {r0,r2,r3}
  add r2,r2,r0,lsl #2
  ldrb r1,[r2,#1]
  ldrb r2,[r2,#2]
  mov r2,r2,lsl #8
  mov r0,r4
  bl web_area
  pop {r0,r2,r3}
web_contact_next:
  add r0,r0,#1
  cmp r0,#2
  blo web_contact
  b web_over
web_flush:                  // the action ended: deliver a contact that was seen and not yet answered
  ldr r12,[r5,#0x88]
  adr r2,web_contacts
  add r2,r2,r0,lsl #3
  mov r0,#0
web_flush_loop:
  mov r1,#1
  mov r1,r1,lsl r0
  tst r12,r1
  beq web_flush_next
  tst r12,r1,lsl #4
  bne web_flush_next
  orr r12,r12,r1,lsl #4
  str r12,[r5,#0x88]
  push {r0,r2,r12}
  add r2,r2,r0,lsl #2
  ldrb r1,[r2,#1]
  ldrb r2,[r2,#2]
  mov r2,r2,lsl #8
  mov r0,r4
  bl web_area
  pop {r0,r2,r12}
web_flush_next:
  add r0,r0,#1
  cmp r0,#2
  blo web_flush_loop
web_over:
  cmp r9,#0                 // the string node died: Vortex is over
  streq r9,[r5,#0x7c]
web_update_out:
  pop {r4,r5,r6,r7,r8,r9,pc}

// web_area(r0=Spidey actor, r1=kind, r2=damage): the hit lands on every
// enemy within 14 units (8 vertically) that the native contact did not just
// hit; each one gets a flash line (4 updates).
web_area:
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  sub sp,sp,#4
  mov r4,r0
  mov r5,r1
  mov r6,r2
  ldr r0,[r4,#0x30]
  ldr r7,[r0,#0x7c]
  ldr r1,[r0,#0x160]
  add r7,r7,r1              // px
  ldr r8,[r0,#0x80]
  ldr r1,[r0,#0x164]
  add r8,r8,r1              // py
  ldr r9,lit3_02154c20
  ldr r10,[r9]              // tick
  add r9,r9,#0x20
  mov r11,#12
web_area_loop:
  ldr r0,[r9]
  cmp r0,#0
  beq web_area_next
  ldr r1,[r9,#12]
  add r1,r1,#2
  cmp r1,r10
  bls web_area_next
  ldr r1,[r9,#4]
  subs r1,r1,r7
  rsbmi r1,r1,#0
  cmp r1,#0xe000
  bgt web_area_next
  ldr r1,[r9,#8]
  subs r1,r1,r8
  rsbmi r1,r1,#0
  cmp r1,#0x8000
  bgt web_area_next
  bl 0x02152c64             // kit_alive
  cmp r0,#0
  beq web_area_next
  ldr r0,[r9]
  bl k2_fighter
  blo web_area_next
  bl web_native
  cmp r0,#0
  bne web_area_line
  ldr r0,[r9]
  mov r1,r5
  mov r2,r6
  mov r3,r4
  bl web_hit
  ldr r2,lit3_02157020
  ldr r1,[r2,#0x90]
  add r1,r1,r0,lsl #8
  add r1,r1,#1
  str r1,[r2,#0x90]
web_area_line:
  ldr r0,[r9]
  mov r1,r4
  mov r2,#4
  bl web_line
web_area_next:
  add r9,r9,#16
  subs r11,r11,#1
  bne web_area_loop
  add sp,sp,#4
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

web_native:                 // r0=enemy -> r0=1 if a native Spidey hit landed on him in the last two ticks
  ldr r1,lit3_02154c20
  ldr r12,[r1]
  add r1,r1,#0x2b0
  mov r3,#4
web_native_loop:
  ldr r2,[r1,#4]!
  cmp r2,r0
  ldr r2,[r1,#4]!
  bne web_native_next
  add r2,r2,#2
  cmp r2,r12
  movhs r0,#1
  bxhs lr
web_native_next:
  subs r3,r3,#1
  bne web_native_loop
  mov r0,#0
  bx lr

// ---------------------------------------------------------------- Overclock
// Ability word 2 bit 0x10000. Passive at combo meter tier 5: every hit Spidey
// lands (not a web hit) also fires a web shot at the nearest other standing
// enemy within 60 units (10 vertically): a built stagger (kind 0x16, half a
// health unit) and a flash line. One shot per captured hit, one per enemy per
// 16 ticks. +0x70 capture tick already answered, +0x74 shots (count + 256 *
// results), +0x240.. last shot tick per registry slot.
oc_update:                  // r0=Spidey actor
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  sub sp,sp,#16
  mov r4,r0
  ldr r10,lit3_02157020
  ldr r9,lit3_02154c20
  ldr r0,[r9,#0x36c]
  ldr r1,[r10,#0x70]
  cmp r0,r1
  beq oc_out
  str r0,[r10,#0x70]
  ldr r11,[r9]              // tick
  add r0,r0,#2
  cmp r0,r11
  blo oc_out                // an old capture
  ldr r0,[r9,#0x370]
  cmp r0,r4
  bne oc_out
  ldr r0,[r9,#0x380]
  sub r0,r0,#0x20
  cmp r0,#6                 // web hits 0x20..0x26 do not answer
  bls oc_out
  mov r0,r4
  mov r1,#0x10000
  bl k2_owned
  cmp r0,#0
  beq oc_out
  ldr r0,lit3_02145c44
  ldr r0,[r0]
  cmp r0,#0x02000000
  blo oc_out
  cmp r0,#0x02400000
  bhs oc_out
  ldr r0,[r0]
  cmp r0,#5
  blt oc_out
  ldr r0,[r4,#0x30]
  ldr r5,[r0,#0x7c]
  ldr r1,[r0,#0x160]
  add r5,r5,r1              // px
  ldr r6,[r0,#0x80]
  ldr r1,[r0,#0x164]
  add r6,r6,r1              // py
  mov r0,#0
  str r0,[sp]               // best slot address
  ldr r0,lit3_7fffffff
  str r0,[sp,#4]            // best distance
  add r7,r9,#0x20
  mov r8,#0
oc_scan:
  ldr r0,[r7]
  cmp r0,#0
  beq oc_next
  ldr r1,[r9,#0x37c]        // not the enemy he just hit
  cmp r0,r1
  beq oc_next
  ldr r1,[r7,#12]
  add r1,r1,#2
  cmp r1,r11
  bls oc_next
  add r1,r10,#0x240
  ldr r1,[r1,r8,lsl #2]
  add r1,r1,#16
  cmp r1,r11
  bhi oc_next
  ldr r1,[r7,#8]
  subs r1,r1,r6
  rsbmi r1,r1,#0
  cmp r1,#0xa000
  bgt oc_next
  ldr r1,[r7,#4]
  subs r1,r1,r5
  rsbmi r1,r1,#0
  cmp r1,#0x3c000
  bgt oc_next
  ldr r2,[sp,#4]
  cmp r1,r2
  bge oc_next
  str r1,[sp,#8]
  bl 0x02152c64             // kit_alive
  cmp r0,#0
  beq oc_next
  ldr r0,[r7]
  bl k2_fighter
  blo oc_next
  bl k2_down
  cmp r0,#0
  bne oc_next
  str r7,[sp]
  ldr r1,[sp,#8]
  str r1,[sp,#4]
  add r1,r10,#0x240
  add r1,r1,r8,lsl #2
  str r1,[sp,#12]           // its cooldown cell
oc_next:
  add r7,r7,#16
  add r8,r8,#1
  cmp r8,#12
  blo oc_scan
  ldr r7,[sp]
  cmp r7,#0
  beq oc_out
  ldr r1,[sp,#12]
  str r11,[r1]
  ldr r0,[r7]
  mov r1,#0x16
  mov r2,#0x800
  mov r3,r4
  bl web_hit
  ldr r1,[r10,#0x74]
  add r1,r1,r0,lsl #8
  add r1,r1,#1
  str r1,[r10,#0x74]
  ldr r0,[r7]
  mov r1,r4
  mov r2,#5
  bl web_line
oc_out:
  add sp,sp,#16
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}
.ltorg
