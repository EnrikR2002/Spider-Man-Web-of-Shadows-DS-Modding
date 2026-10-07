// Shared crowd replay over the kit's bounded, observer-owned enemy registry.
// Included in a combined kit assembly; uses existing lit_/kit_ labels.
// kit_area_hit(r0=x, r1=y, r2=x reach, r3=y reach,
//              [entry sp]=excluded actor, [entry sp+4]=maximum template age).
// Returns r0=replay attempts, r1=sum of native result codes, r2=last attempted
// actor. Neither return value is HP damage or a confirmed hit count.
// Preserves r4-r11. No allocation, actor position writes or ownership changes.
// Callers supply the owned-Red gate, attack template kind and contact timing.
// Native ReceiveHit resolves damage/reaction/immunity; kit_replay_hit validates
// each actor's pointers/interface immediately before dispatch.
kit_area_hit:
  push {r4,r5,r6,r7,r8,r9,r10,r11,lr}
  sub sp,sp,#20
  mov r4,r0
  mov r5,r1
  mov r6,r2
  mov r7,r3
  ldr r9,[sp,#56]
  ldr r8,lit_02154c20
  mov r0,#0
  str r0,[sp]
  str r0,[sp,#4]
  str r0,[sp,#8]
  cmp r6,#0
  blt area_hit_out
  cmp r7,#0
  blt area_hit_out
  // An empty or old capture cannot be used as an arbitrary hit template.
  ldr r0,[r8,#0x370]
  bl kit_ram_ok
  cmp r0,#0
  beq area_hit_out
  ldr r0,[r8,#0x370]
  ldr r0,[r0]
  ldr r1,lit_0212e3f0
  cmp r0,r1
  bne area_hit_out
  ldr r0,[r8]
  ldr r1,[r8,#0x36c]
  sub r0,r0,r1
  ldr r1,[sp,#60]
  cmp r0,r1
  bhi area_hit_out
  add r10,r8,#0x20
  mov r11,#12
area_hit_loop:
  ldr r0,[r10]
  cmp r0,#0
  cmpne r0,r9
  beq area_hit_next
  ldr r1,[r10,#12]
  add r1,r1,#2
  ldr r2,[r8]
  cmp r1,r2
  bls area_hit_next
  ldr r1,[r10,#4]
  subs r1,r1,r4
  rsbmi r1,r1,#0
  cmp r1,r6
  bgt area_hit_next
  ldr r1,[r10,#8]
  subs r1,r1,r5
  rsbmi r1,r1,#0
  cmp r1,r7
  bgt area_hit_next
  str r0,[sp,#8]
  bl kit_replay_hit
  ldr r1,[sp,#4]
  add r1,r1,r0
  str r1,[sp,#4]
  ldr r0,[sp]
  add r0,r0,#1
  str r0,[sp]
area_hit_next:
  add r10,r10,#16
  subs r11,r11,#1
  bne area_hit_loop
area_hit_out:
  ldr r0,[sp]
  ldr r1,[sp,#4]
  ldr r2,[sp,#8]
  add sp,sp,#20
  pop {r4,r5,r6,r7,r8,r9,r10,r11,pc}
