// TASM "never stand still" Red kit: own ARM code at 02152C20 (KIT_BASE).
// Every behavior is gated on Spidey's Red form (actor+0x34 != 1) and the
// replaced Red purchase bit; unowned/Black play keeps native behavior.
// Entry offsets below are fixed: tools/tasm_kit.py branches native sites here.
// State lives at KIT_STATE = 02154C20 (copied zero image, see tasm_kit.py).
  b h_reflex_generic      // +00 from 020B5738  attack states 43..49 "stay"
  b h_reflex_string       // +04 from 020B5334  ground string non-cancel node
  b h_reflex_direction    // +08 from 020B5C58  evade choice after R queued
  b h_spin_repeat         // +0C from 020B5508  Scissor repeat: queued Y direction
  b h_string_node         // +10 from 020C31E4  string node before action queue
  b h_update              // +14 from 02073B5C  after an actor controller update
  b h_observer            // +18 from 02073A68  per-actor observer (enemy registry)
  b h_anim_route          // +1C from 02070480  action resource record lookup
  b h_string_back         // +20 from 020B6B54  Y+back inside the owned branch/spin
  b h_spin_limit          // +24 from 020B5464  Red bit17 repeat limit (Black path never reaches)
  b h_reflex_air          // +28 from 020B7B18  air attack stay (air dodge itself needs bit 10)
  b h_action              // +2C from 020728F0  action request (Perch substitution)
  b h_hit_capture         // +30 from 02078628  hit dispatch (blx to victim ReceiveHit)
  b h_train_floor         // +34 from 0205F420  player HP store (training: no lethal hits)
// Exports for the second code block (tools/tasm_kit2.s, KIT2 = 02155420): fixed offsets.
  b kit_owned             // +38
  b kit_keys              // +3C
  b kit_face              // +40
  b kit_alive             // +44
  b kit_fresh             // +48
  b kit_replay_hit        // +4C

// ---------------------------------------------------------------- Reflex
// Bit 18 (Amazing Speed slot): R cancels Red attack states immediately.
h_reflex_generic:
  mov r0,r8
  bl reflex_ok
  cmp r0,#0
  bne reflex_pass
  ldr r0,[r8,#0x44]
  b 0x020b573c
h_reflex_string:
  mov r0,r8
  bl 0x02155424             // KIT2 Web Rush: A in a ground string set up a rush?
  cmp r0,#0
  bne rush_enter
  mov r0,r8
  bl reflex_ok
  cmp r0,#0
  bne reflex_pass
  ldr r1,[r8,#0x80]
  b 0x020b5338
rush_enter:                 // re-enter state 46: the node hook plays the rush
  mov r0,#1
  strb r0,[r8,#4]
  add sp,sp,#0x58
  mov r0,#46
  pop {r4,r5,r6,r7,r8,pc}
reflex_pass:
  // Let the later evade transition consume R this update.
  add sp,sp,#0x58
  mvn r0,#0x80000000
  pop {r4,r5,r6,r7,r8,pc}

h_reflex_direction:
  mov r0,r5
  bl sense_try
  cmp r0,#0
  bne sense_return
  ldr r0,[r5,#0x14]
  sub r0,r0,#43
  cmp r0,#6
  bhi reflex_native
  mov r0,r5
  bl reflex_ok
  cmp r0,#0
  beq reflex_native
  // Remember the cancelled node so the string exit keeps it alive longer.
  ldr r0,lit_02154c20
  mov r1,#1
  str r1,[r0,#4]
  bl kit_keys
  mov r1,#0
  tst r0,#0x20
  bne reflex_turn
  mov r1,#1
  tst r0,#0x10
  bne reflex_turn
  // Neutral: the in-place dodge (state 53) plays the back tuck (route kind 8).
  // 020B5DA4 consumes the queued command type in r2: it must be 3 (R); 1
  // would eat a queued Y and leave the R queued (v0.4.0 bug).
  ldr r0,lit_02154c20
  mov r2,#1
  str r2,[r0,#0x368]
  mov r2,#3
  b 0x020b5da4
reflex_turn:
  // Directional: face the held side, then the native forward roll (state 57).
  ldr r0,lit_02154c20
  mov r2,#1
  str r2,[r0,#0x10]
  ldr r0,[r5,#0x44]
  bl kit_face
  b 0x020b5c78
reflex_native:
  ldr r0,[r5,#0x24]
  b 0x020b5c5c
sense_return:               // consume R, (re)enter the ground string at node 14
  mov r2,#3
  str r2,[sp,#0x20]
  add r1,sp,#0x20
  add r0,r5,#0x28
  bl 0x020cfc34
  mov r0,#1
  strb r0,[r5,#4]
  add sp,sp,#0x94
  mov r0,#0x2e
  pop {r3,r4,r5,r6,r7,r8,pc}

h_reflex_air:               // r4=controller, r0=actor
  push {r0,lr}
  mov r0,r4
  bl reflex_ok
  cmp r0,#0
  pop {r0,lr}
  bne reflex_air_pass
  ldrb r1,[r0,#0x28]
  b 0x020b7b1c
reflex_air_pass:
  mvn r0,#0x80000000
  pop {r4,pc}

reflex_ok:                  // r0=controller -> r0=1 if Red, bit18 owned, R queued
  push {r4,lr}
  sub sp,sp,#8
  mov r4,r0
  ldr r0,[r4,#0x44]
  mov r1,#0x40000
  bl kit_owned
  cmp r0,#0
  beq reflex_ok_out
  mov r2,#3
  str r2,[sp]
  mov r1,sp
  add r0,r4,#0x28
  bl 0x020cff0c
reflex_ok_out:
  add sp,sp,#8
  pop {r4,pc}

// ---------------------------------------------------------------- Split Decision / Spin Cycle
// Bit 16 (Spider Dance slot): branch nodes 15..17 pick their side every hit.
h_string_node:
  push {r0,r1,r2,r3,lr}
  mov r0,r7
  ldr r1,[r6]               // the state he came from (46 = no pause)
  bl 0x02155428             // KIT2: r0 = Web Rush or Vortex action (node set) or 0
  cmp r0,#0
  bne string_rush
  mov r0,r7
  bl split_face
  pop {r0,r1,r2,r3,lr}
  ldr r2,[r7,#0x80]
  b 0x020c31e8
string_rush:                // request the rush action instead of the node's
  str r0,[sp,#0x2c]         // native action slot sp+0x18 (20 bytes pushed)
  pop {r0,r1,r2,r3,lr}
  add r1,sp,#0x18
  ldr r0,[r7,#0x44]
  b 0x020c31fc

split_face:                 // r0=controller
  push {r4,r5,r6,lr}
  mov r4,r0
  ldr r5,[r4,#0x80]
  cmp r5,#15
  blo split_out
  cmp r5,#17
  bhi split_out
  ldr r6,[r4,#0x44]
  mov r0,r6
  mov r1,#0x10000
  bl kit_owned
  cmp r0,#0
  beq split_out
  bl kit_keys               // held direction wins
  tst r0,#0x20
  movne r1,#0
  bne split_turn
  tst r0,#0x10
  movne r1,#1
  bne split_turn
  // Hits 1-2 prefer an enemy behind within 12 units; otherwise (and for the
  // sweep) the nearest, so a far enemy behind never turns him off a close one.
  cmp r5,#17
  beq split_nearest
  mov r0,r6
  mov r1,#1
  mov r2,#0xc000
  bl kit_target_in
  cmp r0,#0
  bne split_found
split_nearest:
  mov r0,r6
  mov r1,#0
  bl kit_target
  cmp r0,#0
  beq split_out
split_found:
  mov r1,r2
split_turn:
  mov r0,r6
  bl kit_face
split_out:
  pop {r4,r5,r6,pc}

// Y with a held back direction normally becomes the native turn attack (47).
// Inside the owned branch (nodes 15..16) or a spin, it continues the string;
// split_face/spin flips already choose the side. r8=controller, r4=&state.
h_string_back:
  push {r0,r1,r2,r3,lr}
  ldr r0,[r8,#0x44]
  bl kit_spin_active
  cmp r0,#0
  bne string_back_continue
  ldr r1,[r8,#0x14]
  cmp r1,#46
  bne string_back_native
  ldr r1,[r8,#0x80]
  cmp r1,#15
  blo string_back_native
  cmp r1,#16
  bhi string_back_native
  ldr r0,[r8,#0x44]
  mov r1,#0x10000
  bl kit_owned
  cmp r0,#0
  beq string_back_native
string_back_continue:
  pop {r0,r1,r2,r3,lr}
  b 0x020b6bd0
string_back_native:
  pop {r0,r1,r2,r3,lr}
  ldr r0,[r4]
  b 0x020b6b58

// Native repeats only take neutral/forward Y; Y+back or up/down leaves the
// spin for the sweep. While spinning, any direction counts as a repeat (the
// native accept path, which reads the direction twice), so steering away from
// the aimed enemy keeps him spinning. r1=command, r8=controller.
h_spin_repeat:
  push {r1,r2,r3,lr}
  ldr r0,[r8,#0x44]
  bl kit_spin_active
  cmp r0,#0
  pop {r1,r2,r3,lr}
  bne 0x020b5560
  ldr r0,[r1,#4]
  b 0x020b550c

// Native allows 6 + 2*tier repeats; Spin Cycle keeps going while Y is mashed.
h_spin_limit:
  add r4,r4,#10
  ldrsb r0,[r8,#0x93]
  b 0x020b5468

// ---------------------------------------------------------------- per update
h_update:
  push {r0,r1,r2,r3,r12,lr}
  mrs r12,cpsr
  push {r12}
  ldr r0,[r4]
  ldr r1,lit_0212e3f0
  cmp r0,r1
  bne update_done
  ldr r0,lit_02154c20
  ldr r1,[r0]
  add r1,r1,#1
  str r1,[r0]
  bl kit_keys               // held keys and this update's new presses
  ldr r1,lit_02154c20
  ldr r2,[r1,#0x360]
  str r0,[r1,#0x360]
  bic r2,r0,r2
  str r2,[r1,#0x364]
  ldr r2,[r1,#0x350]        // flip animation timer (Perch hop/spring)
  subs r2,r2,#1
  strge r2,[r1,#0x350]
  mov r0,r4
  bl train_update
  mov r0,r4
  bl spin_update
  mov r0,r4
  bl roll_update
  mov r0,r4
  bl resume_update
  mov r0,r4
  bl perch_update
  mov r0,r4
  bl leap_update
  mov r0,r4
  bl sky_update
  mov r0,r4
  bl sense_update
  mov r0,r4
  bl 0x02155420             // KIT2 per-update (Web Rush dash, Ricochet)
update_done:
  pop {r12}
  msr cpsr_f,r12
  pop {r0,r1,r2,r3,r12,lr}
  mov r2,#0
  b 0x02073b60

// Bit 17 (Scissor slot): handstand spin while repeating node 16. Before each
// of the loop's two contacts (clocks 4 and 9) aim: an enemy on the other side
// within hit reach wins (crowds get both sides), else the nearest within spin
// reach (16 units). Left/Right steers; with neither held he glides toward the enemy he
// faces until it is inside hit reach, so both contacts land.
spin_update:                // r0=actor
  push {r4,r5,r6,lr}
  mov r4,r0
  bl kit_spin_active
  ldr r2,lit_02154c20
  cmp r0,#0
  bne spin_active
  ldr r1,[r2,#0x14]         // spin entry latch
  cmp r1,#0
  strne r0,[r4,#0x18]       // leaving the spin: drop steer/glide velocity
  str r0,[r2,#0x14]
  str r0,[r2,#8]            // aimed contact half
  b spin_out
spin_active:
  ldr r5,[r4,#0x30]
  // First spin update: ask the motion to re-commit action 60 so the
  // resource lookup (h_anim_route) swaps in the spin clip.
  ldr r1,[r2,#0x14]
  cmp r1,#0
  bne spin_aim
  mov r1,#1
  str r1,[r2,#0x14]
  ldr r1,[r5,#0x2fc]
  orr r1,r1,#2
  str r1,[r5,#0x2fc]
spin_aim:
  ldr r0,[r5,#0x178]        // action clock, 0..11 per loop
  cmp r0,#6
  movlo r6,#1
  movhs r6,#2
  ldr r1,[r2,#8]
  cmp r1,r6
  beq spin_move
  str r6,[r2,#8]
  mov r0,r4
  mov r1,#1                 // prefer the other side...
  mov r2,#0x7000            // ...within hit reach (7 units)
  bl kit_target_in
  cmp r0,#0
  bne spin_turn
  mov r0,r4
  mov r1,#0                 // else the nearest within spin reach
  mov r2,#0x10000
  bl kit_target_in
  cmp r0,#0
  beq spin_move
spin_turn:
  mov r1,r2
  mov r0,r4
  bl kit_face
spin_move:
  bl kit_keys
  mov r1,#0
  tst r0,#0x10
  movne r1,#0x2800
  tst r0,#0x20
  ldrne r1,lit_ffffd800
  tst r0,#0x30
  bne spin_velocity
  mov r0,r4
  mov r1,#2                 // nearest enemy on the facing side
  mov r2,#0x10000
  bl kit_target_in
  mov r1,#0
  cmp r0,#0
  beq spin_velocity
  cmp r3,#0x4800            // already inside hit reach
  ble spin_velocity
  cmp r2,#1
  moveq r1,#0x2000
  ldrne r1,lit_ffffe000
spin_velocity:
  str r1,[r4,#0x18]
spin_out:
  pop {r4,r5,r6,pc}

kit_spin_active:            // r0=actor -> r0=1 during an owned Red spin repeat
  push {r4,lr}
  mov r4,r0
  mov r1,#0x20000
  bl kit_owned
  cmp r0,#0
  beq spin_no
  ldr r1,[r4,#0x30]
  ldr r2,[r1,#0x254]
  cmp r2,#60
  bne spin_no
  ldr r2,[r1,#0x1f8]
  cmp r2,#0
  beq spin_no
  ldr r3,[r2,#0x14]
  cmp r3,#46
  bne spin_no
  ldr r3,[r2,#0x80]
  cmp r3,#16
  bne spin_no
  ldr r3,[r2,#0x64]
  tst r3,#0x8000
  beq spin_no
  mov r0,#1
  pop {r4,pc}
spin_no:
  mov r0,#0
  pop {r4,pc}

// Native keeps the left string node alive for 10 updates. A Reflex cancel this
// update extends that to 28 so Y after the dodge resumes at the next hit.
resume_update:              // r0=actor
  ldr r3,lit_02154c20
  ldr r1,[r3,#4]
  cmp r1,#0
  bxeq lr
  mov r1,#0
  str r1,[r3,#4]
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  bxeq lr
  ldr r2,[r1,#0x80]
  cmp r2,#5
  bxlo lr
  cmp r2,#18
  bxhs lr
  ldr r3,lit_0211bb74
  ldr r3,[r3,r2,lsl #4]
  cmp r3,#0
  bxeq lr
  mov r2,#28
  strb r2,[r1,#0x90]
  bx lr

// The Reflex roll marker ends with the roll; animation routing reads it.
roll_update:                // Reflex clip flags live only through their dodge state
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  ldrne r1,[r1,#0x14]
  ldr r3,lit_02154c20
  mov r2,#0
  cmp r1,#57
  strne r2,[r3,#0x10]       // directional roll
  cmp r1,#53
  strne r2,[r3,#0x368]      // neutral back tuck
  bx lr

// ---------------------------------------------------------------- Spider Perch
// Bit 15 (Mid-Air Snare slot): the Snare zip's air follow-ups become stomps
// while Spidey is held on the target's head; the chain ends in a spring-off.
h_action:                   // r0=actor, r1=&action (native: ldr r1,[r1])
  ldr r1,[r1]
  push {r0,r2,r3,lr}
  bl perch_action
  pop {r0,r2,r3,lr}
  b 0x020728f4

perch_action:               // r0=actor, r1=action -> r1=action (maybe 130/133)
  push {r4,r5,r6,lr}
  mov r4,r0
  mov r5,r1
  // During a Perch hop/spring flip, air/fall/stomp requests keep the flip.
  ldr r2,lit_02154c20
  ldr r2,[r2,#0x350]
  cmp r2,#0
  beq perch_action_native
  ldr r2,[r4]
  ldr r3,lit_0212e3f0
  cmp r2,r3
  bne perch_action_native
  cmp r5,#38
  cmpne r5,#130
  beq perch_flip_take
  sub r2,r5,#1
  cmp r2,#3
  bhi perch_action_native
perch_flip_take:
  mov r5,#133
  b perch_action_out
perch_action_native:
  sub r2,r5,#1
  cmp r2,#3
  bhi perch_action_out
  cmp r5,#130
  beq perch_action_out
  ldr r2,[r4]
  ldr r3,lit_0212e3f0
  cmp r2,r3
  bne perch_action_out
  mov r0,r4
  mov r1,#0x8000
  bl kit_owned
  cmp r0,#0
  beq perch_action_out
  ldr r2,[r4,#0x30]
  cmp r2,#0
  beq perch_action_out
  ldr r2,[r2,#0x1f8]
  cmp r2,#0
  beq perch_action_out
  ldr r3,[r2,#0x14]
  cmp r3,#31
  beq perch_take
  cmp r3,#51
  bne perch_action_out
  ldr r3,lit_02154c20
  ldr r6,[r3,#0x300]
  cmp r6,#0
  bne perch_take
  ldr r3,[r2,#0x18]
  cmp r3,#31
  bne perch_action_out
perch_take:
  ldr r3,[r2,#0x54]
  cmp r3,#0
  beq perch_action_out
  sub r3,r3,#4
  mov r0,r3
  push {r3}
  bl kit_fresh
  pop {r3}
  cmp r0,#0
  beq perch_action_out
  ldr r6,lit_02154c20
  mov r0,#1
  str r0,[r6,#0x300]
  str r3,[r6,#0x304]
  mov r5,#130
perch_action_out:
  mov r1,r5
  pop {r4,r5,r6,pc}

perch_update:               // r0=actor
  push {r4,r5,r6,r7,r8,lr}
  mov r4,r0
  ldr r8,lit_02154c20
  ldr r0,[r8,#0x300]
  cmp r0,#0
  beq perch_out
  ldr r5,[r4,#0x30]
  ldr r1,[r5,#0x1f8]
  cmp r1,#0
  beq perch_end
  ldr r2,[r1,#0x14]
  cmp r2,#19                // brief fall between pounds: native A/B win
  beq perch_fall
  cmp r2,#51
  bne perch_release         // hit, Snare, swing...: let go without a spring
  ldr r0,[r8,#0x354]
  cmp r0,#0
  bne perch_hop
  ldr r0,[r8,#0x364]        // new presses
  tst r0,#2
  bne perch_spring          // B: spring off high
  tst r0,#1
  beq perch_keep
  mov r0,r4                 // A: hop onto the next head
  bl hop_pick
  cmp r0,#0
  beq perch_keep
  str r0,[r8,#0x304]
  mov r1,r2
  mov r0,r4
  bl kit_face
  ldr r0,[r5,#0x7c]
  ldr r1,[r5,#0x160]
  add r0,r0,r1
  str r0,[r8,#0x358]        // hop start x/y
  ldr r0,[r5,#0x80]
  ldr r1,[r5,#0x164]
  add r0,r0,r1
  str r0,[r8,#0x35c]
  mov r0,#1
  str r0,[r8,#0x354]
  mov r0,r5
  bl perch_flip
  b perch_out
perch_fall:
  ldr r0,[r8,#0x354]        // a hop in flight keeps flying
  cmp r0,#0
  bne perch_hop
perch_keep:
  // A buffered Y re-enters the air attack a few updates after the stomp ends;
  // keep the hold through that gap so it becomes another pound.
  mov r3,#4
  ldr r1,[r5,#0x1f8]
  ldr r2,[r1,#0x14]
  cmp r2,#51
  bne perch_grace
  ldr r2,[r5,#0x258]
  cmp r2,#130
  beq perch_hold
perch_grace:
  ldr r3,[r8,#0x308]
  subs r3,r3,#1
  blt perch_end
perch_hold:
  str r3,[r8,#0x308]
  ldr r6,[r8,#0x304]
  mov r0,r6
  bl kit_fresh
  cmp r0,#0
  beq perch_end
  ldr r7,[r6,#0x30]
  cmp r7,#0
  beq perch_end
  ldr r0,[r7,#0x7c]
  ldr r1,[r7,#0x160]
  add r0,r0,r1              // target x
  ldr r1,[r7,#0x80]
  ldr r2,[r7,#0x164]
  add r1,r1,r2              // target y (feet)
  ldr r2,[r5,#0x180]
  cmp r2,#1
  subeq r0,r0,#0x1800       // just behind the head on the near side
  addne r0,r0,#0x1800
  add r1,r1,#0x7000         // standing on the head
  bl perch_steer
  b perch_out
perch_spring:               // B: high flip off the head, steer with Left/Right
  mov r0,#0
  str r0,[r8,#0x300]
  str r0,[r8,#0x354]
  ldr r0,[r8,#0x360]
  mov r1,#0
  tst r0,#0x10
  movne r1,#0x1400
  tst r0,#0x20
  ldrne r1,lit_ffffec00
  str r1,[r4,#0x18]
  mov r1,#0x4c00
  str r1,[r4,#0x1c]
  mov r0,r5
  bl perch_flip
  // Use up this B: otherwise the native air B swings as the flip ends.
  ldr r0,[r5,#0x1f8]
  sub sp,sp,#8
  mov r1,#2
  str r1,[sp]
  mov r1,sp
  add r0,r0,#0x28
  bl 0x020cfc34
  add sp,sp,#8
  b perch_out
perch_hop:                  // r0 = step 1..8: arc from the start to the new head
  str r0,[r8,#0x308]        // r0 >= 1: keep the hold alive (grace)
  ldr r6,[r8,#0x304]
  mov r0,r6
  bl kit_fresh
  cmp r0,#0
  beq perch_end
  ldr r7,[r6,#0x30]
  cmp r7,#0
  beq perch_end
  ldr r6,[r8,#0x354]        // step
  ldr r0,[r7,#0x7c]
  ldr r1,[r7,#0x160]
  add r0,r0,r1              // target x
  ldr r2,[r5,#0x180]
  cmp r2,#1
  subeq r0,r0,#0x1800
  addne r0,r0,#0x1800
  ldr r1,[r8,#0x358]
  sub r0,r0,r1
  mul r2,r0,r6
  add r0,r1,r2,asr #3       // x = start + (end - start) * step / 8
  ldr r1,[r7,#0x80]
  ldr r2,[r7,#0x164]
  add r1,r1,r2
  add r1,r1,#0x7000         // head height
  ldr r2,[r8,#0x35c]
  sub r1,r1,r2
  mul r3,r1,r6
  add r1,r2,r3,asr #3
  rsb r2,r6,#8
  mul r3,r2,r6
  mov r2,#0x600             // arc: 6 units at mid-hop
  mla r1,r3,r2,r1
  bl perch_steer
  add r6,r6,#1
  cmp r6,#8
  movgt r6,#0
  str r6,[r8,#0x354]
  bne perch_out
  // Landed: pound straight away; a long grace leaves time for Y/A/B.
  mov r0,#12
  str r0,[r8,#0x308]
  mov r0,#130
  str r0,[r5,#0x258]
  ldr r0,[r5,#0x2fc]
  orr r0,r0,#2
  str r0,[r5,#0x2fc]
  b perch_out
perch_release:
  mov r0,#0
  str r0,[r8,#0x354]
  str r0,[r8,#0x300]
  b perch_out
perch_end:
  mov r0,#0
  str r0,[r8,#0x354]
  str r0,[r8,#0x300]
  ldr r2,[r5,#0x180]
  cmp r2,#1
  ldreq r1,lit_ffffec00
  movne r1,#0x1400
  str r1,[r4,#0x18]
  mov r1,#0x2c00
  str r1,[r4,#0x1c]
perch_out:
  pop {r4,r5,r6,r7,r8,pc}

// perch_steer: r0/r1 = wanted x/y, r4 = actor, r5 = motion. v0.4.1: velocity
// toward the point (at most 6 units per update) instead of a position write,
// so native collision keeps the ride and the head-hop out of walls/ceilings.
perch_steer:
  push {r0,lr}
  ldr r2,[r5,#0x7c]
  ldr r3,[r5,#0x160]
  add r2,r2,r3
  sub r0,r0,r2
  bl leap_clamp
  str r0,[r4,#0x18]
  ldr r2,[r5,#0x80]
  ldr r3,[r5,#0x164]
  add r2,r2,r3
  sub r0,r1,r2
  bl leap_clamp
  str r0,[r4,#0x1c]
  pop {r0,pc}

// perch_flip(motion): play the Reflex front flip (route kind 7) for 8 updates.
perch_flip:
  ldr r1,lit_02154c20
  mov r2,#8
  str r2,[r1,#0x350]
  mov r2,#133
  str r2,[r0,#0x258]
  ldr r2,[r0,#0x2fc]
  orr r2,r2,#2
  str r2,[r0,#0x2fc]
  bx lr

// hop_pick(actor) -> r0=nearest other fresh enemy within 24 units (held
// Left/Right picks that side), r2=facing toward it; skips the current perch.
hop_pick:
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  ldr r4,[r0,#0x30]
  ldr r5,[r4,#0x7c]
  ldr r6,[r4,#0x160]
  add r5,r5,r6              // px
  ldr r6,[r4,#0x80]
  ldr r7,[r4,#0x164]
  add r6,r6,r7              // py
  ldr r4,lit_02154c20
  ldr r9,[r4]               // tick
  ldr r10,[r4,#0x304]       // current perch (excluded)
  ldr r11,[r4,#0x360]       // held keys
  add r4,r4,#0x20
  mov r0,#0
  mov lr,#0
  ldr r8,lit_7fffffff
  mov r7,#12
hop_loop:
  ldr r1,[r4]
  cmp r1,#0
  cmpne r1,r10
  beq hop_next
  ldr r2,[r4,#12]
  add r2,r2,#2
  cmp r2,r9
  bls hop_next
  ldr r2,[r4,#8]
  subs r2,r2,r6
  rsbmi r2,r2,#0
  cmp r2,#0xc000            // heads up to 12 units above/below
  bgt hop_next
  ldr r2,[r4,#4]
  subs r3,r2,r5             // dx
  tst r11,#0x10
  beq hop_left
  cmp r3,#0
  ble hop_next
hop_left:
  tst r11,#0x20
  beq hop_dist
  cmp r3,#0
  bge hop_next
hop_dist:
  mov r12,r3
  cmp r12,#0
  rsblt r12,r12,#0
  cmp r12,#0x18000
  bgt hop_next
  cmp r12,r8
  bge hop_next
  mov r8,r12
  mov r0,r1
  cmp r3,#0
  movgt lr,#1
  movle lr,#0
hop_next:
  add r4,r4,#16
  subs r7,r7,#1
  bne hop_loop
  mov r2,lr
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

kit_fresh:                  // r0=actor -> r0=1 if the registry saw it this/last tick
  push {r4,lr}
  ldr r1,lit_02154c20
  ldr r2,[r1]
  add r1,r1,#0x20
  mov r3,#12
fresh_loop:
  ldr r4,[r1]
  cmp r4,r0
  bne fresh_next
  ldr r4,[r1,#12]
  add r4,r4,#2
  cmp r4,r2
  bhi fresh_alive
fresh_next:
  add r1,r1,#16
  subs r3,r3,#1
  bne fresh_loop
  mov r0,#0
  pop {r4,pc}
fresh_alive:
  bl kit_alive
  pop {r4,pc}

// kit_alive(r0=actor) -> r0=1 if its vtable is in the class range and its
// motion (+0x30) and controller (motion+0x1F8, may be 0) pointers are RAM.
// A registry entry is trusted for two ticks; an actor freed and reused in
// that window must not be dereferenced (v0.4.0 abort in the Sense scan).
kit_alive:
  push {r1,r2,lr}
  mov r1,r0
  bl kit_ram_ok
  cmp r0,#0
  beq alive_no
  ldr r2,[r1]
  ldr r0,lit_02120000
  cmp r2,r0
  blo alive_no
  ldr r0,lit_0213df00
  cmp r2,r0
  bhi alive_no
  ldr r0,[r1,#0x30]
  bl kit_ram_ok
  cmp r0,#0
  beq alive_no
  ldr r2,[r1,#0x30]
  ldr r0,[r2,#0x1f8]
  cmp r0,#0
  beq alive_yes
  bl kit_ram_ok
  cmp r0,#0
  beq alive_no
alive_yes:
  mov r0,#1
  pop {r1,r2,pc}
alive_no:
  mov r0,#0
  pop {r1,r2,pc}

// ---------------------------------------------------------------- Leapfrog
// Bit 13 (Web Kick slot): the native pull and kick connect (damage, low pop);
// after the hit-stop Spidey front-flips over the target in six updates (kick
// clocks 3-8), lands 3 units past it and turns back toward it.
// v0.4.1: horizontal velocity (desired point - current position, at most 6
// units per update, plus the cancelled Rebound recoil), so native collision
// stops it at walls; no position writes. The kick state ignores vertical
// velocity: the height over his head is the clip's (visual) root.
// Latch at +0x310: 0 idle, 1 kick started, 2 vaulting (step count at +0x320),
// 3 landed.
leap_update:                // r0=actor
  push {r4,r5,r6,r7,r8,lr}
  mov r4,r0
  ldr r8,lit_02154c20
  ldr r5,[r4,#0x30]
  ldr r6,[r5,#0x1f8]
  cmp r6,#0
  beq leap_reset
  ldr r7,[r6,#0x14]
  ldr r0,[r8,#0x310]
  cmp r0,#2
  beq leap_vault
  cmp r0,#3
  beq leap_landed
  cmp r7,#43
  bne leap_reset
  mov r0,r4
  mov r1,#0x2000
  bl kit_owned
  cmp r0,#0
  beq leap_reset
  ldr r0,[r8,#0x310]
  cmp r0,#0
  bne leap_wait
  ldr r0,[r6,#0x54]
  cmp r0,#0
  beq leap_out
  sub r0,r0,#4
  str r0,[r8,#0x31c]
  mov r1,#1
  str r1,[r8,#0x310]
leap_wait:                  // contact + hit-stop occupy the kick's clocks 0..1
  ldr r0,[r5,#0x254]        // the first kick update still shows the pull's clock
  cmp r0,#50
  bne leap_out
  ldr r0,[r5,#0x178]
  cmp r0,#2
  blt leap_out
  ldr r1,[r5,#0x7c]
  ldr r2,[r5,#0x160]
  add r1,r1,r2
  str r1,[r8,#0x314]
  ldr r1,[r5,#0x80]
  ldr r2,[r5,#0x164]
  add r1,r1,r2
  str r1,[r8,#0x318]
  mov r1,#0
  str r1,[r8,#0x320]
  mov r1,#2
  str r1,[r8,#0x310]
leap_vault:
  cmp r7,#43
  cmpne r7,#19
  cmpne r7,#20
  cmpne r7,#24
  bne leap_cut
  ldr r0,[r8,#0x31c]
  bl kit_fresh
  cmp r0,#0
  beq leap_reset
  ldr r0,[r8,#0x320]
  add r0,r0,#1
  str r0,[r8,#0x320]
  sub r0,r0,#1              // step index 0..5 (kick clocks 3..8)
  ldr r1,[r8,#0x31c]
  ldr r1,[r1,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3              // target x (moving)
  ldr r3,[r8,#0x314]        // start x
  cmp r2,r3
  addgt r2,r2,#0x3000       // land 3 units past the target
  suble r2,r2,#0x3000
  sub r2,r2,r3
  adr r1,leap_progress
  ldr r1,[r1,r0,lsl #2]
  mul r12,r2,r1
  add r3,r3,r12,asr #8      // desired x
  push {r0}
  ldr r1,[r5,#0x7c]
  ldr r12,[r5,#0x160]
  add r1,r1,r12
  sub r0,r3,r1
  bl leap_recoil
  add r0,r0,r1
  bl leap_clamp
  str r0,[r4,#0x18]
  pop {r0}
  cmp r0,#5
  blt leap_out
  mov r1,#3
  str r1,[r8,#0x310]
  b leap_out
leap_landed:                // cancel the kick's recoil step through its end
  bl leap_recoil
  str r1,[r4,#0x18]
  cmp r7,#43
  beq leap_out
leap_cut:                   // the vault was cut short: stop, still face him
  mov r1,#0
  str r1,[r4,#0x18]
leap_turn:
  mov r1,#0
  str r1,[r8,#0x310]
  ldr r0,[r8,#0x31c]
  bl kit_fresh
  cmp r0,#0
  beq leap_out
  ldr r1,[r8,#0x31c]
  ldr r1,[r1,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3
  ldr r3,[r5,#0x7c]
  ldr r0,[r5,#0x160]
  add r3,r3,r0
  cmp r2,r3
  movgt r1,#1
  movle r1,#0
  mov r0,r4
  bl kit_face
  b leap_out
leap_reset:
  ldr r0,[r8,#0x310]
  cmp r0,#2                 // cut short mid-vault: drop the vault velocity
  moveq r0,#0
  streq r0,[r4,#0x18]
  mov r0,#0
  str r0,[r8,#0x310]
leap_out:
  pop {r4,r5,r6,r7,r8,pc}
leap_progress: .word 45, 105, 165, 215, 245, 256
// The Web Kick GMB (Rebound, v0.1.1) steps back 4096, 6144, 6144, 4096 on
// clocks 5-8. leap_recoil -> r1 = the velocity that cancels this update's step.
leap_recoil:                // r5=motion; keeps r0
  ldr r1,[r5,#0x254]
  cmp r1,#50
  movne r1,#0
  bxne lr
  ldr r1,[r5,#0x178]
  cmp r1,#8
  movhi r1,#0
  bxhi lr
  adr r12,leap_rebound
  ldr r1,[r12,r1,lsl #2]
  ldr r12,[r5,#0x180]       // facing 1 = right: the step goes left
  cmp r12,#1
  rsbne r1,r1,#0
  bx lr
leap_rebound:  .word 0, 0, 0, 0, 0, 4096, 6144, 6144, 4096
leap_clamp:                 // r0 = clamp(r0, +-6 units)
  cmp r0,#0x6000
  movgt r0,#0x6000
  cmn r0,#0x6000
  ldrlt r0,lit_ffffa000
  bx lr

// ---------------------------------------------------------------- literals
// One labelled table mid-code (ARM literal loads reach 4 KiB either way). It sits
// after Leapfrog since v0.13.0: the staged crowd-hit candidates add code and the
// last loads were 49 bytes out of reach of a table before it.
// Do not use 'ldr rX,=value' or a mid-file .ltorg: Keystone wraps far
// literals and shifts later absolute branches (TECHNICAL, research pitfalls).
lit_02049304: .word 0x02049304
lit_0207862c: .word 0x0207862C
lit_0211bb74: .word 0x0211BB74
lit_027e0000: .word 0x027E0000
lit_02120000: .word 0x02120000
lit_0212e3f0: .word 0x0212E3F0
lit_0213df00: .word 0x0213DF00
lit_02154b20: .word 0x02154B20
lit_02154c20: .word 0x02154C20
lit_7fffffff: .word 0x7FFFFFFF
lit_ffff7000: .word 0xFFFF7000
lit_ffffa000: .word 0xFFFFA000
lit_ffffd800: .word 0xFFFFD800
lit_ffffe000: .word 0xFFFFE000
lit_ffffec00: .word 0xFFFFEC00
lit_fffff000: .word 0xFFFFF000

// ---------------------------------------------------------------- hit capture
// The native contact dispatcher calls the victim's ReceiveHit interface
// ([[actor+8]+0x40]: r0=&result, r1=actor+8, r2=&attacker, r3=&info,
// [sp]=0x1000). Keep a replayable copy of the latest hit Spidey deals: info
// (0x40 bytes) at +0x380, its two pointed-to records at +0x3C0/+0x3E0 (victim
// part pointer cleared), the attacker at +0x370 and the tick at +0x36C. The
// victim goes to +0x37C and into a ring of the last four {victim, tick} at
// +0x2B4 (index +0x2B0): KIT2 uses it to leave natively hit enemies alone.
h_hit_capture:
  push {r0,r1,r2,r3,r4,r5,r12}
  mov r0,r2
  bl kit_ram_ok
  cmp r0,#0
  beq capture_done
  ldr r12,[r2]
  mov r0,r12
  bl kit_ram_ok
  cmp r0,#0
  beq capture_done
  mov r0,r3
  bl kit_ram_ok
  cmp r0,#0
  beq capture_done
  ldr r0,[r12]
  ldr r1,lit_0212e3f0
  cmp r0,r1
  bne capture_done
  ldr r5,lit_02154c20
  str r12,[r5,#0x370]
  ldr r0,[r5]
  str r0,[r5,#0x36c]
  ldr r0,[sp,#4]            // the victim's interface (actor+8)
  sub r0,r0,#8
  str r0,[r5,#0x37c]
  ldr r1,[r5,#0x2b0]
  add r1,r1,#1
  and r1,r1,#3
  str r1,[r5,#0x2b0]
  add r1,r5,r1,lsl #3
  str r0,[r1,#0x2b4]
  ldr r0,[r5]
  str r0,[r1,#0x2b8]
  add r1,r5,#0x380
  mov r4,#0
capture_info:
  ldr r0,[r3,r4]
  str r0,[r1,r4]
  add r4,r4,#4
  cmp r4,#0x40
  blo capture_info
  ldr r2,[r3,#12]
  add r1,r5,#0x3c0
  bl capture_record
  str r1,[r5,#0x38c]
  ldr r2,[r3,#16]
  add r1,r5,#0x3e0
  bl capture_record
  str r1,[r5,#0x390]
  mov r0,#0
  str r0,[r5,#0x3e8]        // victim part: the replay hits someone else
capture_done:
  pop {r0,r1,r2,r3,r4,r5,r12}
  // Spider-Sense dash guard: a hit on Spidey is answered "ignored" (1, as
  // for native get-up states) without calling his ReceiveHit.
  push {r0,r2}
  ldr r2,lit_02154c20
  ldr r2,[r2,#0x344]
  cmp r2,#0
  beq capture_native
  ldr r2,[r1,#-8]
  ldr r0,lit_0212e3f0
  cmp r2,r0
  bne capture_native
  pop {r0,r2}
  mov r2,#1
  str r2,[r0]
  b 0x0207862c
capture_native:
  pop {r0,r2}
  ldr lr,lit_0207862c
  bx r4

capture_record:             // copy 0x20 bytes from r2 to r1 (zeros if r2 is not RAM)
  push {lr}
  mov r0,r2
  bl kit_ram_ok
  cmp r0,#0
  moveq r2,#0
  pop {lr}
  mov r4,#0
capture_loop:
  cmp r2,#0
  moveq r0,#0
  ldrne r0,[r2,r4]
  str r0,[r1,r4]
  add r4,r4,#4
  cmp r4,#0x20
  blo capture_loop
  bx lr

// kit_ram_ok(r0) -> r0=1 for a word address in main RAM or DTCM (no data abort).
kit_ram_ok:
  tst r0,#3
  bne ram_bad
  cmp r0,#0x02000000
  blo ram_bad
  cmp r0,#0x02400000
  blo ram_good
  push {r1}
  ldr r1,lit_027e0000
  cmp r0,r1
  pop {r1}
  blo ram_bad
  cmp r0,#0x02800000
  bhs ram_bad
ram_good:
  mov r0,#1
  bx lr
ram_bad:
  mov r0,#0
  bx lr

// kit_replay_hit(actor): the captured Spidey hit lands on actor through its
// own ReceiveHit; r0 = native result (4 = taken, 1 = ignored, 0 = none).
kit_replay_hit:
  push {r4,lr}
  sub sp,sp,#0x10
  mov r4,r0
  bl kit_alive
  cmp r0,#0
  beq replay_none
  mov r0,r4
  ldr r4,lit_02154c20
  add r1,r0,#8
  ldr r12,[r1]
  ldr r2,lit_02120000       // only real actors: interface vtable in the class range
  cmp r12,r2
  blo replay_none
  ldr r2,lit_0213df00
  cmp r12,r2
  bhi replay_none
  ldr r12,[r12,#0x40]
  mov r0,#0
  str r0,[sp,#8]
  mov r0,#0x1000
  str r0,[sp]
  add r0,sp,#8
  add r2,r4,#0x370
  add r3,r4,#0x380
  blx r12
  ldr r0,[sp,#8]
  add sp,sp,#0x10
  pop {r4,pc}
replay_none:
  mov r0,#0
  add sp,sp,#0x10
  pop {r4,pc}

// ---------------------------------------------------------------- Skyjack
// Bit 14 (Web Launch slot): after the Web Vault launch (state 40) the juggle
// floats (both fall at quarter speed) and the air finisher (action 4) spikes
// the target straight down. Latch +0x330, target +0x334, spike timer +0x338.
sky_update:                 // r0=actor
  push {r4,r5,r6,r7,r8,lr}
  mov r4,r0
  ldr r8,lit_02154c20
  ldr r5,[r4,#0x30]
  ldr r6,[r5,#0x1f8]
  cmp r6,#0
  beq sky_reset
  ldr r7,[r6,#0x14]
  ldr r0,[r8,#0x330]
  cmp r0,#0
  beq sky_idle
  ldr r0,[r8,#0x338]
  cmn r0,#1                 // spike delivered: wait for the target to land
  beq sky_impact
  b sky_active
sky_idle:
  cmp r7,#40
  bne sky_out
  mov r0,r4
  mov r1,#0x4000
  bl kit_owned
  cmp r0,#0
  beq sky_out
  ldr r0,[r6,#0x54]
  cmp r0,#0
  beq sky_out
  sub r0,r0,#4
  str r0,[r8,#0x334]
  mov r0,#0
  str r0,[r8,#0x338]
  mov r0,#1
  str r0,[r8,#0x330]
  b sky_out
sky_active:
  cmp r7,#40
  cmpne r7,#20
  cmpne r7,#19
  cmpne r7,#51
  cmpne r7,#52
  cmpne r7,#15
  bne sky_reset
  ldr r0,[r8,#0x334]
  bl kit_fresh
  cmp r0,#0
  beq sky_reset
  ldr r6,[r8,#0x334]
  // Spike: the finisher's strike drives the target down for six updates.
  ldr r0,[r5,#0x254]
  cmp r0,#4
  bne sky_float
  ldr r0,[r5,#0x178]
  cmp r0,#4
  blt sky_float
  ldr r0,[r8,#0x338]
  cmp r0,#0
  bne sky_float
  // Only a target within reach of the finisher is spiked.
  ldr r1,[r6,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3
  ldr r3,[r5,#0x7c]
  ldr r0,[r5,#0x160]
  add r3,r3,r0
  subs r2,r2,r3
  rsbmi r2,r2,#0
  cmp r2,#0xe000
  bgt sky_float
  ldr r2,[r1,#0x80]
  ldr r3,[r1,#0x164]
  add r2,r2,r3
  ldr r3,[r5,#0x80]
  ldr r0,[r5,#0x164]
  add r3,r3,r0
  subs r2,r2,r3
  rsbmi r2,r2,#0
  cmp r2,#0x8000
  bgt sky_float
  mov r0,#6
  str r0,[r8,#0x338]
sky_float:
  ldr r0,[r8,#0x338]
  cmp r0,#0
  ble sky_soft
  sub r0,r0,#1
  cmp r0,#0
  moveq r0,#-1
  str r0,[r8,#0x338]
  ldr r1,lit_ffff7000
  str r1,[r6,#0x1c]
  mov r1,#0
  str r1,[r6,#0x18]
  b sky_out
sky_soft:
  cmp r7,#51
  cmpne r7,#19
  bne sky_out
  ldr r0,[r8,#0x338]
  cmp r0,#0
  bne sky_player            // after the spike only the player floats
  ldr r1,[r6,#0x1c]
  cmp r1,#0
  movlt r1,r1,asr #2
  strlt r1,[r6,#0x1c]
sky_player:
  ldr r0,[r8,#0x338]
  cmp r0,#0
  bne sky_out               // juggle over once the spike fires
  cmp r7,#51
  cmpne r7,#19
  bne sky_out
  ldr r1,[r4,#0x1c]
  cmp r1,#0
  movlt r1,r1,asr #2
  strlt r1,[r4,#0x1c]
  // Stay within reach: drift toward a point 7 units short of the target.
  ldr r1,[r6,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3              // target x
  ldr r3,[r5,#0x7c]
  ldr r0,[r5,#0x160]
  add r3,r3,r0              // player x
  cmp r2,r3
  subgt r2,r2,#0x7000
  addle r2,r2,#0x7000
  subs r2,r2,r3             // correction
  cmp r2,#0x1000
  movgt r2,#0x1000
  cmn r2,#0x1000
  ldrlt r2,lit_fffff000
  ldr r1,[r5,#0x7c]
  add r1,r1,r2
  str r1,[r5,#0x7c]
  b sky_out
// Bowling: when the spiked target stops falling (vertical velocity >= 0, or
// 40 updates pass), the finisher's captured hit lands on every other enemy
// within 8 units of it. One impact per spike.
sky_impact:
  ldr r0,[r8,#0x334]
  bl kit_fresh
  cmp r0,#0
  beq sky_reset
  ldr r6,[r8,#0x334]
  ldr r0,[r8,#0x33c]
  add r0,r0,#1
  str r0,[r8,#0x33c]
  cmp r0,#40
  bgt sky_reset
  ldr r1,[r6,#0x1c]
  cmp r1,#0
  blt sky_out
  ldr r0,[r8]               // the template must be this spike's hit
  ldr r1,[r8,#0x36c]
  sub r0,r0,r1
  cmp r0,#60
  bhi sky_reset
  mov r0,#0x1f              // bowl with the heavy kick's knockdown reaction
  str r0,[r8,#0x380]
  str r0,[r8,#0x3f4]
  ldr r7,[r6,#0x30]
  ldr r4,[r7,#0x7c]
  ldr r0,[r7,#0x160]
  add r4,r4,r0              // impact x
  ldr r5,[r7,#0x80]
  ldr r0,[r7,#0x164]
  add r5,r5,r0              // impact y
  add r7,r8,#0x20
  mov r3,#12
sky_bowl:
  ldr r0,[r7]
  cmp r0,#0
  cmpne r0,r6
  beq sky_bowl_next
  ldr r1,[r7,#12]
  add r1,r1,#2
  ldr r2,[r8]
  cmp r1,r2
  bls sky_bowl_next
  ldr r1,[r7,#4]
  subs r1,r1,r4
  rsbmi r1,r1,#0
  cmp r1,#0x8000
  bgt sky_bowl_next
  ldr r1,[r7,#8]
  subs r1,r1,r5
  rsbmi r1,r1,#0
  cmp r1,#0x6000
  bgt sky_bowl_next
  push {r3}
  ldr r1,[r7]
  str r1,[r8,#0x378]        // telemetry: last bowled actor, count
  bl kit_replay_hit
  ldr r1,[r8,#0x374]
  add r1,r1,r0,lsl #8       // + result * 256 per replay
  add r1,r1,#1
  str r1,[r8,#0x374]
  pop {r3}
sky_bowl_next:
  add r7,r7,#16
  subs r3,r3,#1
  bne sky_bowl
sky_reset:
  mov r0,#0
  str r0,[r8,#0x330]
  str r0,[r8,#0x33c]
sky_out:
  pop {r4,r5,r6,r7,r8,pc}

// ---------------------------------------------------------------- Spider-Sense
// Bit 19 (Ultimate Speed slot, needs bit 18): R while an enemy is mid-attack
// (melee state 15 within 12 units, ranged state 16 within 16) flips Spidey
// over that attacker into the heavy string kick (node 14) with the reversal
// animation. v0.4.1: no teleport. He dashes 3 units past the attacker in four
// updates with velocity, which the native collision resolves (a position
// write could put him inside walls or floors), then turns to face him.
// Counter +0x344 (7 at the press): dash while 6..3, turn at 2, and while it
// is above 0 hits on Spidey are ignored (h_hit_capture). +0x340 = 1 dash
// left / 2 dash right (also routes the clip), +0x348 attacker, +0x34C target x.
sense_try:                  // r0=controller -> r0=1 if the counter was set up
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  mov r4,r0
  ldr r5,[r4,#0x44]
  mov r0,r5
  mov r1,#0x80000
  bl kit_owned
  cmp r0,#0
  beq sense_no
  ldr r6,[r5,#0x30]
  ldr r7,[r6,#0x7c]
  ldr r0,[r6,#0x160]
  add r7,r7,r0              // px
  ldr r8,[r6,#0x80]
  ldr r0,[r6,#0x164]
  add r8,r8,r0              // py
  ldr r9,lit_02154c20
  ldr r10,[r9]              // tick
  add r9,r9,#0x20
  mov r11,#12
  mov r0,#0                 // best attacker
  ldr lr,lit_7fffffff        // best distance
sense_loop:
  ldr r1,[r9]
  cmp r1,#0
  beq sense_next
  ldr r2,[r9,#12]
  add r2,r2,#2
  cmp r2,r10
  bls sense_next
  ldr r2,[r9,#8]
  subs r2,r2,r8
  rsbmi r2,r2,#0
  cmp r2,#0x8000
  bgt sense_next
  ldr r2,[r9,#4]
  subs r2,r2,r7
  rsbmi r2,r2,#0
  cmp r2,#0x10000
  bgt sense_next
  cmp r2,lr
  bge sense_next
  push {r0,r1,r2,lr}
  mov r0,r1
  bl kit_alive
  mov r3,r0
  pop {r0,r1,r2,lr}
  cmp r3,#0
  beq sense_next
  ldr r3,[r1,#0x30]
  ldr r3,[r3,#0x1f8]
  cmp r3,#0
  beq sense_next
  ldr r3,[r3,#0x14]
  cmp r3,#16                // ranged attack (spit), within 16 units
  beq sense_take
  cmp r3,#15                // melee attack state, within 12 units
  bne sense_next
  cmp r2,#0xc000
  bgt sense_next
sense_take:
  mov lr,r2
  mov r0,r1
sense_next:
  add r9,r9,#16
  subs r11,r11,#1
  bne sense_loop
  cmp r0,#0
  beq sense_no
  // Lock the attacker; aim 3 units past him and face him (the dash direction).
  ldr r9,lit_02154c20
  str r0,[r9,#0x348]
  ldr r1,[r0,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3              // ex
  cmp r2,r7
  addgt r3,r2,#0x3000
  movgt r10,#1              // he is right of Spidey: dash right
  suble r3,r2,#0x3000
  movle r10,#0
  str r3,[r9,#0x34c]
  add r1,r10,#1
  str r1,[r9,#0x340]
  mov r1,#7
  str r1,[r9,#0x344]
  mov r0,r5
  mov r1,r10
  bl kit_face
  mov r0,#13                // entering 46 advances to node 14: heavy kick
  str r0,[r4,#0x80]
  mov r0,#1
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}
sense_no:
  mov r0,#0
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

sense_update:               // r0=actor: dash, turn; the flag lasts while node 13/14 plays
  push {r4,r5,r6,lr}
  mov r4,r0
  ldr r5,lit_02154c20
  ldr r1,[r4,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  beq sense_clear
  ldr r2,[r1,#0x14]
  cmp r2,#46
  bne sense_clear
  ldr r2,[r1,#0x80]
  cmp r2,#14
  cmpne r2,#13
  bne sense_clear
  ldr r6,[r5,#0x344]
  subs r6,r6,#1
  blt sense_out
  str r6,[r5,#0x344]
  cmp r6,#2
  blt sense_out             // 1, 0: guard only
  beq sense_turn
  // Dash step (r6 = 6..3): velocity = remaining / updates left (4..1).
  bl sense_target_x         // r0 = target x
  ldr r1,[r4,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3              // px
  sub r0,r0,r2
  sub r1,r6,#2
  adr r2,sense_recip
  ldr r2,[r2,r1,lsl #2]
  mul r3,r0,r2
  mov r0,r3,asr #8
  cmp r0,#0x6000            // at most 6 units per update
  movgt r0,#0x6000
  cmn r0,#0x6000
  ldrlt r0,lit_ffffa000
  str r0,[r4,#0x18]
  b sense_out
sense_turn:                 // dash over: stop and face the attacker
  mov r0,#0
  str r0,[r4,#0x18]
  ldr r1,[r5,#0x340]
  cmp r1,#2
  moveq r1,#0               // dashed right: by default face back left
  movne r1,#1
  ldr r0,[r5,#0x348]
  push {r1}
  bl kit_fresh
  pop {r1}
  cmp r0,#0
  beq sense_face
  ldr r0,[r5,#0x348]
  ldr r0,[r0,#0x30]
  cmp r0,#0
  beq sense_face
  ldr r2,[r0,#0x7c]
  ldr r3,[r0,#0x160]
  add r2,r2,r3              // ex
  ldr r0,[r4,#0x30]
  ldr r3,[r0,#0x7c]
  ldr r0,[r0,#0x160]
  add r3,r3,r0              // px
  cmp r2,r3
  movgt r1,#1
  movle r1,#0
sense_face:
  mov r0,r4
  bl kit_face
  b sense_out
sense_clear:
  ldr r1,[r5,#0x344]
  cmp r1,#2                 // cut short mid-dash: drop the dash velocity
  movgt r1,#0
  strgt r1,[r4,#0x18]
  mov r1,#0
  str r1,[r5,#0x340]
  str r1,[r5,#0x344]
sense_out:
  pop {r4,r5,r6,pc}

sense_target_x:             // r5=KIT_STATE -> r0 = 3 units past the attacker (last known)
  push {lr}
  ldr r0,[r5,#0x348]
  bl kit_fresh
  cmp r0,#0
  beq sense_target_old
  ldr r0,[r5,#0x348]
  ldr r0,[r0,#0x30]
  cmp r0,#0
  beq sense_target_old
  ldr r1,[r0,#0x7c]
  ldr r0,[r0,#0x160]
  add r0,r0,r1
  ldr r1,[r5,#0x340]
  cmp r1,#2
  addeq r0,r0,#0x3000
  subne r0,r0,#0x3000
  str r0,[r5,#0x34c]
  pop {pc}
sense_target_old:
  ldr r0,[r5,#0x34c]
  pop {pc}
sense_recip: .word 0, 256, 128, 85, 64

// ---------------------------------------------------------------- enemy registry
// Every live common-health enemy refreshes a slot each update. Entries are
// only trusted for two ticks, so a despawned actor is never dereferenced.
h_observer:
  push {r0,r1,r2,r3,r4,r5,r6,r7,r12,lr}
  mrs r7,cpsr
  ldr r4,[r0]
  ldr r5,lit_02120000
  cmp r4,r5
  blo obs_done
  ldr r5,lit_0213df00
  cmp r4,r5
  bhi obs_done
  ldr r5,lit_0212e3f0
  cmp r4,r5
  beq obs_done
  ldr r5,[r4,#0x150]
  ldr r6,lit_02049304
  cmp r5,r6
  bne obs_done
  bl train_observe
  bl 0x02155434             // KIT2 strength dial (chapter rooms; keeps every register)
  ldr r5,[r0,#0x44]
  cmp r5,#0
  ble obs_done
  ldr r1,[r0,#0x30]
  cmp r1,#0
  beq obs_done
  ldr r2,lit_02154c20
  ldr r3,[r2]               // tick
  add r4,r2,#0x20
  mov r5,#0
  mov r6,#0                 // first free/stale slot
obs_scan:
  ldr r12,[r4,r5,lsl #4]
  cmp r12,r0
  beq obs_slot
  cmp r6,#0
  bne obs_next
  add r12,r4,r5,lsl #4
  ldr r12,[r12,#12]
  add r12,r12,#2
  cmp r12,r3
  addls r6,r4,r5,lsl #4
  ldr r12,[r4,r5,lsl #4]
  cmp r12,#0
  addeq r6,r4,r5,lsl #4
obs_next:
  add r5,r5,#1
  cmp r5,#12
  blo obs_scan
  cmp r6,#0
  beq obs_done
  mov r5,r6
  b obs_write
obs_slot:
  add r5,r4,r5,lsl #4
obs_write:
  str r0,[r5]
  ldr r12,[r1,#0x7c]
  ldr r2,[r1,#0x160]
  add r12,r12,r2
  str r12,[r5,#4]
  ldr r12,[r1,#0x80]
  ldr r2,[r1,#0x164]
  add r12,r12,r2
  str r12,[r5,#8]
  str r3,[r5,#12]
obs_done:
  msr cpsr_f,r7
  pop {r0,r1,r2,r3,r4,r5,r6,r7,r12,lr}
  b 0x02151920

// ---------------------------------------------------------------- Training room
// Test Upgrades: the room's native training target carries actor+0x88 bit 4
// (no story enemy seen with it). Observer calls count bit-4 sightings
// (+0x2F0); each Spidey update turns them into the active flag (+0x2F4).
// While active, every common-health enemy gets bit 4 (the native setter then
// clamps a lethal hit to 40 instead of killing), 8 HP units instead of the
// native 1, and refills to max once "defeated" (HP 1..40). Spidey heals to
// full every 900 updates (30 s, timer +0x2F8) or while SELECT+Down is held;
// h_train_floor leaves him 1 Q12 on a lethal hit.
train_observe:              // r0=enemy actor (common-health ABI checked); keeps r0
  push {r1,r2,r3,lr}
  ldr r3,lit_02154c20
  ldr r2,[r0,#0x88]
  tst r2,#4
  ldrne r1,[r3,#0x2f0]
  addne r1,r1,#1
  strne r1,[r3,#0x2f0]
  ldr r1,[r3,#0x2f4]
  cmp r1,#0
  beq train_obs_out
  orr r2,r2,#4
  str r2,[r0,#0x88]
  ldr r1,[r0,#0x48]
  cmp r1,#0x1000            // native training HP (1 unit) -> 8 units
  moveq r1,#0x8000
  streq r1,[r0,#0x48]
  streq r1,[r0,#0x44]
  ldr r2,[r0,#0x44]
  cmp r2,#0
  ble train_obs_out
  cmp r2,#40
  strle r1,[r0,#0x44]
train_obs_out:
  pop {r1,r2,r3,pc}

train_update:               // r0=Spidey actor
  push {r4,r5,lr}
  mov r4,r0
  ldr r5,lit_02154c20
  ldr r1,[r5,#0x2f0]
  mov r2,#0
  str r2,[r5,#0x2f0]
  cmp r1,#0
  movne r1,#1
  str r1,[r5,#0x2f4]
  beq train_out
  ldr r0,[r4,#0xe4]         // stats: +0x84 HP, +0x88 max (Q12)
  bl kit_ram_ok
  cmp r0,#0
  beq train_out
  ldr r4,[r4,#0xe4]
  ldr r1,[r5,#0x2f8]
  add r1,r1,#1
  ldr r2,[r5,#0x360]        // held keys: SELECT 0x4 + Down 0x80 heals now
  and r2,r2,#0x84
  cmp r2,#0x84
  moveq r1,#900
  cmp r1,#900
  blo train_store
  ldr r2,[r4,#0x88]
  cmp r2,#0
  strgt r2,[r4,#0x84]
  mov r1,#0
train_store:
  str r1,[r5,#0x2f8]
train_out:
  pop {r4,r5,pc}

h_train_floor:              // r1=HP, r2=stats, r3=new HP (0 if lethal); native str r3,[r2,#0x84]
  push {lr}
  bl 0x02155438             // KIT2 damage scale (chapter room dial, Vitality) -> r3
  pop {lr}
  push {r0}
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x2f4]
  cmp r0,#0
  beq floor_store
  cmp r3,#1
  movlt r3,#1
floor_store:
  pop {r0}
  str r3,[r2,#0x84]
  b 0x0205f424

// kit_target(actor, mode) -> r0=enemy actor or 0, r2=facing toward it, r3=|dx|
// (modes 0/2). Fresh registry entries within 40 units horizontally and 10
// vertically. Mode 0 nearest, 1 prefer behind, 2 facing side only.
// kit_target_in takes the horizontal reach in r2.
kit_target:
  mov r2,#0x28000
kit_target_in:
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  sub sp,sp,#4
  str r2,[sp]
  mov r10,r1
  ldr r4,[r0,#0x30]
  ldr r5,[r4,#0x7c]
  ldr r6,[r4,#0x160]
  add r5,r5,r6              // px
  ldr r6,[r4,#0x80]
  ldr r7,[r4,#0x164]
  add r6,r6,r7              // py
  ldr r11,[r4,#0x180]       // facing (1 = right)
  ldr r4,lit_02154c20
  ldr r9,[r4]               // tick
  add r4,r4,#0x20
  mov r0,#0                 // best actor
  mov lr,#0                 // facing toward best
  ldr r8,lit_7fffffff        // best score
  mov r7,#12
target_loop:
  ldr r1,[r4]
  cmp r1,#0
  beq target_next
  ldr r2,[r4,#12]
  add r2,r2,#2
  cmp r2,r9
  bls target_next
  ldr r2,[r4,#8]
  subs r2,r2,r6
  rsbmi r2,r2,#0
  cmp r2,#0xa000
  bgt target_next
  ldr r2,[r4,#4]
  subs r3,r2,r5             // dx
  mov r12,r3
  cmp r12,#0
  rsblt r12,r12,#0
  ldr r2,[sp]
  cmp r12,r2
  bgt target_next
  cmp r10,#0
  beq target_score
  cmp r10,#2
  bne target_behind
  cmp r11,#1                // facing side only
  bne target_front_left
  cmp r3,#0
  ble target_next
  b target_score
target_front_left:
  cmp r3,#0
  bge target_next
  b target_score
target_behind:
  // prefer behind: an enemy opposite the facing side scores far better
  cmp r11,#1
  bne target_left
  cmp r3,#0
  sublt r12,r12,#0x40000
  b target_score
target_left:
  cmp r3,#0
  subgt r12,r12,#0x40000
target_score:
  cmp r12,r8
  bge target_next
  mov r8,r12
  mov r0,r1
  cmp r3,#0
  movgt lr,#1
  movle lr,#0
target_next:
  add r4,r4,#16
  subs r7,r7,#1
  bne target_loop
  mov r2,lr
  mov r3,r8
  add sp,sp,#4
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

// ---------------------------------------------------------------- animation routing
// r4 = motion. The action record copy lives at sp+0x2C (SCA id at +0).
h_anim_route:
  push {r0,r1,r2,r3,lr}
  mov r0,r4
  add r1,sp,#0x40           // 0x2C + 20 bytes pushed
  bl kit_route
  pop {r0,r1,r2,r3,lr}
  ldrb r0,[sp,#0x40]
  b 0x02070484

kit_route:                  // r0=motion, r1=record (SCA id at +0)
  push {r4,r5,r6,lr}
  mov r4,r0
  mov r5,r1
  ldrb r2,[r5,#0x14]
  cmp r2,#0
  beq route_out
  ldr r6,[r4]               // owning actor
  ldr r2,[r6]
  ldr r3,lit_0212e3f0
  cmp r2,r3
  bne route_out
  ldr r2,[r4,#0x258]        // requested action
  ldr r3,lit_02154b20        // route table (KIT_BASE+0x1F00): {action, kind, sca}
route_loop:
  ldr r0,[r3]
  cmp r0,#0
  beq route_out
  cmp r0,r2
  bne route_next
  ldr r0,[r3,#4]
  cmp r0,#1                 // kind 1: spin repeat
  bne route_kind2
  push {r2,r3}
  mov r0,r6
  bl kit_spin_active
  pop {r2,r3}
  cmp r0,#0
  bne route_take
  b route_next
route_kind2:
  cmp r0,#3                 // kind 3: Spider Perch stomp
  bne route_kind2b
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x300]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2b:
  cmp r0,#4                 // kind 4: owned Red grapple pull/kick (Leapfrog)
  bne route_kind2c
  ldr r0,[r6,#0x30]
  ldr r0,[r0,#0x1f8]
  cmp r0,#0
  beq route_next
  ldr r0,[r0,#0x14]
  cmp r0,#43
  bne route_next
  push {r2,r3}
  mov r0,r6
  mov r1,#0x2000
  bl kit_owned
  pop {r2,r3}
  cmp r0,#0
  bne route_take
  b route_next
route_kind2c:
  cmp r0,#5                 // kind 5: Skyjack juggle in progress
  bne route_kind2d
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x330]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2d:
  cmp r0,#6                 // kind 6: Spider-Sense counter kick
  bne route_kind2e
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x340]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2e:
  cmp r0,#7                 // kind 7: Perch hop/spring flip
  bne route_kind2f
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x350]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2f:
  cmp r0,#8                 // kind 8: Reflex neutral back tuck
  bne route_kind2g
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x368]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2g:
  cmp r0,#9                 // kinds 9+: KIT2 keeps the flags (9 Web Rush, 10..13 Vortex)
  blo route_kind2h
  push {r1,r2,r3}
  bl 0x0215542c
  pop {r1,r2,r3}
  cmp r0,#0
  bne route_take
  b route_next
route_kind2h:
  cmp r0,#2                 // kind 2: Reflex roll
  bne route_next
  ldr r0,lit_02154c20
  ldr r0,[r0,#0x10]
  cmp r0,#0
  bne route_take
route_next:
  add r3,r3,#12
  b route_loop
route_take:
  ldr r0,[r3,#8]
  str r0,[r5]
route_out:
  pop {r4,r5,r6,pc}

// ---------------------------------------------------------------- helpers
kit_owned:                  // r0=actor, r1=mask -> r0=1 if Red and owned
  ldr r2,[r0,#0x34]
  cmp r2,#1
  moveq r0,#0
  bxeq lr
  ldr r2,[r0,#0xe8]
  ldr r2,[r2]
  tst r2,r1
  movne r0,#1
  moveq r0,#0
  bx lr

kit_keys:                   // r0 = held keys (1 = held): 0x10 Right, 0x20 Left
  mov r0,#0x04000000
  add r0,r0,#0x130
  ldrh r0,[r0]
  mvn r0,r0
  bx lr

kit_face:                   // r0=actor, r1=facing (1 right) via native turn
  push {r4,lr}
  sub sp,sp,#8
  ldr r2,[r0,#0x30]
  ldr r2,[r2,#0x180]
  cmp r2,r1
  beq face_out
  str r1,[sp]
  mov r1,sp
  bl 0x02072860
face_out:
  add sp,sp,#8
  pop {r4,pc}
.ltorg
