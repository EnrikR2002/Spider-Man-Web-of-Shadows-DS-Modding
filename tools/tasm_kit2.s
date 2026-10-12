// TASM kit, second code block at 02155420 (KIT2), v0.10.0. tools/tasm_kit.s
// calls entries +00..+0C, +14 and +18; tools/tasm_kit.py branches native sites
// to the rest. New shop rows live in ability word 2 (stats+0x14): Web Rush
// 0x400 (ability bit 74), Ricochet 0x800 (75), Momentum 0x1000 (76), Vitality
// I..III 0x2000/0x4000/0x8000 (77..79, Both Suits list, v0.11.0).
// State K2 = 02157020 (zero image): +0 rush phase (1 armed, 2 playing),
// +4 target, +8 node to resume, +0xC stop x, +0x10 side (1 = target right),
// +0x14 armed age, +0x18 rush clip loaded, +0x1C dash step (1 dashing, 2 last
// step done); +0x20..+0x4F Ricochet cooldown tick per registry slot, +0x50
// Ricochet count + 256 * native results, +0x54 last victim; +0x58 Momentum
// rate of this call (0 = native), +0x5C its accumulator, +0x60 doubled steps,
// +0x64 rush glide updates, +0x68 health bar tinted by Vitality.
// Strength dial (v0.11.0): 02156F20 (block +0x1B00, zero in the kit image; the
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

k2_update:
  push {r4,lr}
  mov r4,r0
  bl rush_update
  mov r0,r4
  bl rico_update
  mov r0,r4
  bl vit_update
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

k2_node:                    // r0=controller
  push {r4,lr}
  ldr r4,lit2_02157020
  ldr r1,[r4]
  cmp r1,#1
  beq node_rush
  mov r1,#0                 // any other node start ends a rush
  str r1,[r4]
  ldr r1,[r4,#0x18]         // rush clip loaded for action 58: make the next
  cmp r1,#0                 // commit look the resource up again
  beq node_none
  mov r1,#0
  str r1,[r4,#0x18]
  ldr r1,[r0,#0x44]
  ldr r1,[r1,#0x30]
  ldr r2,[r1,#0x2fc]
  orr r2,r2,#2
  str r2,[r1,#0x2fc]
node_none:
  mov r0,#0
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

k2_route:                   // keeps r1-r3
  ldr r0,lit2_02157020
  ldr r0,[r0]
  cmp r0,#2
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
lit2_02156f20: .word 0x02156F20
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
  ldr r2,lit2_02156f20
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
  ldr r12,lit2_02156f20
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
momentum_last: .byte 11, 16, 25, 18, 11, 38, 19, 0      // last sample of actions 56..62 (GMB record count - 1)
.ltorg
