// TASM "never stand still" Red kit: own ARM code at 02152C20 (KIT_BASE).
// Every behavior is gated on Spidey's Red form (actor+0x34 != 1) and the
// replaced Red purchase bit; unowned/Black play keeps native behavior.
// Entry offsets below are fixed: tools/tasm_kit.py branches native sites here.
// State lives at KIT_STATE = 02154C20 (copied zero image, see tasm_kit.py).
  b h_reflex_generic      // +00 from 020B5738  attack states 43..49 "stay"
  b h_reflex_string       // +04 from 020B5334  ground string non-cancel node
  b h_reflex_direction    // +08 from 020B5C58  evade choice after R queued
  nop                     // +0C reserved
  b h_string_node         // +10 from 020C31E4  string node before action queue
  b h_update              // +14 from 02073B5C  after an actor controller update
  b h_observer            // +18 from 02073A68  per-actor observer (enemy registry)
  b h_anim_route          // +1C from 02070480  action resource record lookup
  b h_string_back         // +20 from 020B6B54  Y+back inside the owned branch/spin
  b h_spin_limit          // +24 from 020B5464  Red bit17 repeat limit (Black path never reaches)
  b h_reflex_air          // +28 from 020B7B18  air attack stay (air dodge itself needs bit 10)
  b h_action              // +2C from 020728F0  action request (Perch substitution)
  nop                     // +30 reserved

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
  bl reflex_ok
  cmp r0,#0
  bne reflex_pass
  ldr r1,[r8,#0x80]
  b 0x020b5338
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
  ldr r0,=0x02154C20
  mov r1,#1
  str r1,[r0,#4]
  bl kit_keys
  mov r1,#0
  tst r0,#0x20
  bne reflex_turn
  mov r1,#1
  tst r0,#0x10
  bne reflex_turn
  b 0x020b5da4              // neutral: in-place spider-sense dodge (state 53)
reflex_turn:
  // Directional: face the held side, then the native forward roll (state 57).
  ldr r0,=0x02154C20
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
  bl split_face
  pop {r0,r1,r2,r3,lr}
  ldr r2,[r7,#0x80]
  b 0x020c31e8

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
  // Hits 1-2 prefer an enemy behind; the sweep takes the nearest.
  mov r0,r6
  cmp r5,#17
  moveq r1,#0
  movne r1,#1
  bl kit_target
  cmp r0,#0
  beq split_out
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
  ldr r1,=0x0212e3f0
  cmp r0,r1
  bne update_done
  ldr r0,=0x02154C20
  ldr r1,[r0]
  add r1,r1,#1
  str r1,[r0]
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
update_done:
  pop {r12}
  msr cpsr_f,r12
  pop {r0,r1,r2,r3,r12,lr}
  mov r2,#0
  b 0x02073b60

// Bit 17 (Scissor slot): handstand spin while repeating node 16. Steer with
// Left/Right; flip facing once per loop so the two contacts cover both sides.
spin_update:                // r0=actor
  push {r4,r5,r6,lr}
  mov r4,r0
  bl kit_spin_active
  ldr r2,=0x02154C20
  cmp r0,#0
  streq r0,[r2,#0x14]       // spin entry latch
  beq spin_out
  ldr r5,[r4,#0x30]
  // First spin update: ask the motion to re-commit action 60 so the
  // resource lookup (h_anim_route) swaps in the spin clip.
  ldr r1,[r2,#0x14]
  cmp r1,#0
  bne spin_steer
  mov r1,#1
  str r1,[r2,#0x14]
  ldr r1,[r5,#0x2fc]
  orr r1,r1,#2
  str r1,[r5,#0x2fc]
spin_steer:
  bl kit_keys
  mov r1,#0
  tst r0,#0x10
  movne r1,#0x2800
  tst r0,#0x20
  ldrne r1,=0xffffd800
  str r1,[r4,#0x18]
  ldr r0,[r5,#0x178]        // action clock, 0..11 per loop
  ldr r2,=0x02154C20
  cmp r0,#6
  movlo r1,#0
  strlo r1,[r2,#8]
  blo spin_out
  ldr r1,[r2,#8]
  cmp r1,#0
  bne spin_out
  mov r1,#1
  str r1,[r2,#8]
  ldr r1,[r5,#0x180]
  eor r1,r1,#1
  mov r0,r4
  bl kit_face
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
  ldr r3,=0x02154C20
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
  ldr r3,=0x0211bb74
  ldr r3,[r3,r2,lsl #4]
  cmp r3,#0
  bxeq lr
  mov r2,#28
  strb r2,[r1,#0x90]
  bx lr

// The Reflex roll marker ends with the roll; animation routing reads it.
roll_update:
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  cmp r1,#0
  beq roll_clear
  ldr r1,[r1,#0x14]
  cmp r1,#57
  bxeq lr
roll_clear:
  ldr r1,=0x02154C20
  mov r2,#0
  str r2,[r1,#0x10]
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

perch_action:               // r0=actor, r1=action -> r1=action (maybe 130)
  push {r4,r5,r6,lr}
  mov r4,r0
  mov r5,r1
  sub r2,r5,#1
  cmp r2,#3
  bhi perch_action_out
  cmp r5,#130
  beq perch_action_out
  ldr r2,[r4]
  ldr r3,=0x0212e3f0
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
  ldr r3,=0x02154C20
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
  ldr r6,=0x02154C20
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
  ldr r8,=0x02154C20
  ldr r0,[r8,#0x300]
  cmp r0,#0
  beq perch_out
  ldr r5,[r4,#0x30]
  ldr r1,[r5,#0x1f8]
  cmp r1,#0
  beq perch_end
  // A buffered Y re-enters the air attack a few updates after the stomp ends;
  // keep the hold through that gap so it becomes another pound.
  mov r3,#4
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
  ldr r2,[r5,#0x160]
  sub r0,r0,r2
  str r0,[r5,#0x7c]
  ldr r2,[r5,#0x164]
  sub r1,r1,r2
  str r1,[r5,#0x80]
  mov r0,#0
  str r0,[r4,#0x18]
  str r0,[r4,#0x1c]
  b perch_out
perch_end:
  mov r0,#0
  str r0,[r8,#0x300]
  ldr r2,[r5,#0x180]
  cmp r2,#1
  ldreq r1,=0xffffec00
  movne r1,#0x1400
  str r1,[r4,#0x18]
  mov r1,#0x2c00
  str r1,[r4,#0x1c]
perch_out:
  pop {r4,r5,r6,r7,r8,pc}

kit_fresh:                  // r0=actor -> r0=1 if the registry saw it this/last tick
  push {r4,lr}
  ldr r1,=0x02154C20
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
  movhi r0,#1
  pophi {r4,pc}
fresh_next:
  add r1,r1,#16
  subs r3,r3,#1
  bne fresh_loop
  mov r0,#0
  pop {r4,pc}

// ---------------------------------------------------------------- Leapfrog
// Bit 13 (Web Kick slot): the native pull and kick connect (damage, low pop);
// after the hit-stop Spidey front-flips over the target in six updates (also
// through the following fall state), lands past it and turns back toward it.
// Latch at +0x310: 0 idle, 1 kick started, 2 vaulting (step count at +0x320).
leap_update:                // r0=actor
  push {r4,r5,r6,r7,r8,lr}
  mov r4,r0
  ldr r8,=0x02154C20
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
leap_wait:                  // contact + hit-stop occupy clocks 0..1
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
  bne leap_reset
  ldr r0,[r8,#0x31c]
  bl kit_fresh
  cmp r0,#0
  beq leap_reset
  ldr r0,[r8,#0x320]
  add r0,r0,#1
  str r0,[r8,#0x320]
  sub r0,r0,#1              // step index 0..5
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
  add r3,r3,r12,asr #8
  adr r1,leap_height
  ldr r1,[r1,r0,lsl #2]
  mov r2,#0x8000
  mul r12,r2,r1
  ldr r2,[r8,#0x318]
  add r2,r2,r12,asr #8
  ldr r1,[r5,#0x160]
  sub r3,r3,r1
  str r3,[r5,#0x7c]
  ldr r1,[r5,#0x164]
  sub r2,r2,r1
  str r2,[r5,#0x80]
  mov r1,#0
  str r1,[r4,#0x18]
  str r1,[r4,#0x1c]
  cmp r0,#5
  blt leap_out
  str r3,[r8,#0x314]        // landing base x/y for the hold
  str r2,[r8,#0x318]
  mov r1,#3
  str r1,[r8,#0x310]
  b leap_out
leap_landed:                // hold the landing through the kick's end; no recoil hop
  mov r1,#0
  str r1,[r4,#0x18]
  str r1,[r4,#0x1c]
  cmp r7,#43
  bne leap_turn
  ldr r1,[r8,#0x314]
  str r1,[r5,#0x7c]
  ldr r1,[r8,#0x318]
  str r1,[r5,#0x80]
  b leap_out
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
  mov r0,#0
  str r0,[r8,#0x310]
leap_out:
  pop {r4,r5,r6,r7,r8,pc}
leap_progress: .word 50, 110, 165, 210, 240, 256
leap_height:   .word 150, 235, 256, 210, 120, 0

// ---------------------------------------------------------------- Skyjack
// Bit 14 (Web Launch slot): after the Web Vault launch (state 40) the juggle
// floats (both fall at quarter speed) and the air finisher (action 4) spikes
// the target straight down. Latch +0x330, target +0x334, spike timer +0x338.
sky_update:                 // r0=actor
  push {r4,r5,r6,r7,r8,lr}
  mov r4,r0
  ldr r8,=0x02154C20
  ldr r5,[r4,#0x30]
  ldr r6,[r5,#0x1f8]
  cmp r6,#0
  beq sky_reset
  ldr r7,[r6,#0x14]
  ldr r0,[r8,#0x330]
  cmp r0,#0
  bne sky_active
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
  ldr r1,=0xffff7000
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
  ldrlt r2,=0xfffff000
  ldr r1,[r5,#0x7c]
  add r1,r1,r2
  str r1,[r5,#0x7c]
  b sky_out
sky_reset:
  mov r0,#0
  str r0,[r8,#0x330]
sky_out:
  pop {r4,r5,r6,r7,r8,pc}

// ---------------------------------------------------------------- Spider-Sense
// Bit 19 (Ultimate Speed slot, needs bit 18): R while an enemy within reach is
// mid-attack (enemy state 15) flips Spidey behind that attacker, facing him,
// straight into the heavy string kick (node 14) with the reversal animation.
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
  ldr r9,=0x02154C20
  ldr r10,[r9]              // tick
  add r9,r9,#0x20
  mov r11,#12
  mov r0,#0                 // best attacker
  ldr lr,=0x7fffffff        // best distance
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
  cmp r2,#0xc000
  bgt sense_next
  cmp r2,lr
  bge sense_next
  ldr r3,[r1,#0x30]
  cmp r3,#0
  beq sense_next
  ldr r3,[r3,#0x1f8]
  cmp r3,#0
  beq sense_next
  ldr r3,[r3,#0x14]
  cmp r3,#15                // enemy attack state
  bne sense_next
  mov lr,r2
  mov r0,r1
sense_next:
  add r9,r9,#16
  subs r11,r11,#1
  bne sense_loop
  cmp r0,#0
  beq sense_no
  // Behind the attacker: 3 units past him on the far side, facing back.
  ldr r1,[r0,#0x30]
  ldr r2,[r1,#0x7c]
  ldr r3,[r1,#0x160]
  add r2,r2,r3              // ex
  cmp r2,r7
  addgt r3,r2,#0x3000
  movgt r10,#0              // land right of him: face left
  suble r3,r2,#0x3000
  movle r10,#1
  ldr r1,[r6,#0x160]
  sub r1,r3,r1
  str r1,[r6,#0x7c]
  str r3,[r5,#0x148]
  str r3,[r5,#0x180]
  str r3,[r5,#0x210]
  str r3,[r5,#0x2cc]
  mov r0,r5
  mov r1,r10
  bl kit_face
  mov r0,#13                // entering 46 advances to node 14: heavy kick
  str r0,[r4,#0x80]
  ldr r0,=0x02154C20
  mov r1,#1
  str r1,[r0,#0x340]
  mov r0,#1
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}
sense_no:
  mov r0,#0
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}

sense_update:               // r0=actor: the counter flag lasts while node 14 plays
  ldr r1,[r0,#0x30]
  ldr r1,[r1,#0x1f8]
  ldr r3,=0x02154C20
  cmp r1,#0
  beq sense_clear
  ldr r2,[r1,#0x14]
  cmp r2,#46
  bne sense_clear
  ldr r2,[r1,#0x80]
  cmp r2,#14
  cmpne r2,#13
  bxeq lr
sense_clear:
  mov r2,#0
  str r2,[r3,#0x340]
  bx lr

// ---------------------------------------------------------------- enemy registry
// Every live common-health enemy refreshes a slot each update. Entries are
// only trusted for two ticks, so a despawned actor is never dereferenced.
h_observer:
  push {r0,r1,r2,r3,r4,r5,r6,r7,r12,lr}
  mrs r7,cpsr
  ldr r4,[r0]
  ldr r5,=0x02120000
  cmp r4,r5
  blo obs_done
  ldr r5,=0x0213df00
  cmp r4,r5
  bhi obs_done
  ldr r5,=0x0212e3f0
  cmp r4,r5
  beq obs_done
  ldr r5,[r4,#0x150]
  ldr r6,=0x02049304
  cmp r5,r6
  bne obs_done
  ldr r5,[r0,#0x44]
  cmp r5,#0
  ble obs_done
  ldr r1,[r0,#0x30]
  cmp r1,#0
  beq obs_done
  ldr r2,=0x02154C20
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

// kit_target(actor, prefer_behind) -> r0=enemy actor or 0, r2=facing toward it.
// Fresh registry entries within 40 units horizontally and 10 vertically.
kit_target:
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  mov r10,r1
  ldr r4,[r0,#0x30]
  ldr r5,[r4,#0x7c]
  ldr r6,[r4,#0x160]
  add r5,r5,r6              // px
  ldr r6,[r4,#0x80]
  ldr r7,[r4,#0x164]
  add r6,r6,r7              // py
  ldr r11,[r4,#0x180]       // facing (1 = right)
  ldr r4,=0x02154C20
  ldr r9,[r4]               // tick
  add r4,r4,#0x20
  mov r0,#0                 // best actor
  mov lr,#0                 // facing toward best
  ldr r8,=0x7fffffff        // best score
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
  cmp r12,#0x28000
  bgt target_next
  cmp r10,#0
  beq target_score
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
  ldr r3,=0x0212e3f0
  cmp r2,r3
  bne route_out
  ldr r2,[r4,#0x258]        // requested action
  ldr r3,=0x02154b20        // route table (KIT_BASE+0x1F00): {action, kind, sca}
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
  ldr r0,=0x02154C20
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
  ldr r0,=0x02154C20
  ldr r0,[r0,#0x330]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2d:
  cmp r0,#6                 // kind 6: Spider-Sense counter kick
  bne route_kind2e
  ldr r0,=0x02154C20
  ldr r0,[r0,#0x340]
  cmp r0,#0
  bne route_take
  b route_next
route_kind2e:
  cmp r0,#2                 // kind 2: Reflex roll
  bne route_next
  ldr r0,=0x02154C20
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
