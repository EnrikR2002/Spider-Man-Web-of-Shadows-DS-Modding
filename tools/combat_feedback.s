// Own ARM9 HUD extension, ARM state, loaded at 0214F420.
// Fixed entry offsets: HUD 0000, ctor 1000, cleanup 1100,
// player damage 1300, enemy damage 1500. State at +3000.
push {r0-r12,lr}
mrs r12,cpsr
push {r11,r12}
sub sp,sp,#0x300
ldr r5,state
ldr r6,[r5]
cmp r6,#0
beq hud_done
ldr r1,[r5,#8]
cmp r1,r0
str r0,[r5,#8]
ldr r0,[r5,#12]
add r0,r0,#1
str r0,[r5,#12]
ldr r0,[r5,#4]
cmp r0,#0
bne font_ready
ldr r0,font
mov r1,#3
mov r2,#0
mov r3,#0
bl 0x0200b1dc
mov r0,#1
str r0,[r5,#4]
font_ready:
// Clear only our top readouts and the lower-right numeric label.
add r0,r6,#0x1c
bl 0x02008c94
mov r1,#0
add r2,r0,#64
mov r3,#144
clear_top:
str r1,[r2],#4
subs r3,r3,#1
bne clear_top
add r2,r0,#0x500
mov r3,#4
clear_bottom:
add r2,r2,#32
mov r4,#8
clear_row:
str r1,[r2],#4
subs r4,r4,#1
bne clear_row
subs r3,r3,#1
bne clear_bottom
add r0,sp,#16
add r1,r6,#0x1c
mov r2,#0x200
bl 0x02009328
add r7,sp,#16
ldr r0,combo_model
ldr r0,[r0]
cmp r0,#0
beq draw_damage
ldrb r1,[r0]
ldr r0,[r0,#4]
mov r2,#75
mul r1,r2,r1
add r0,r1,r0,asr #12
cmp r0,#0
movlt r0,#0
ldr r1,buffer
ldr r2,combo_label
bl copy_label
mov r2,#0
bl number
ldr r2,buffer
mov r3,#208
mov r8,#170
mov r9,#94
bl draw_line
draw_damage:
add r4,r5,#0x20
mov r10,#64
ldr r11,dealt_label
bl draw_bucket
add r4,r5,#0x60
mov r10,#192
ldr r11,taken_label
bl draw_bucket
mov r0,r7
bl 0x02009398
add r0,r6,#0x1c
mov r1,#1
bl 0x02008830
hud_done:
add sp,sp,#0x300
pop {r11,r12}
msr cpsr_f,r12
pop {r0-r12,lr}
push {r3,r4,r5,lr}
b 0x020e7d4c

// r4 bucket, r10 centre, r11 title, r7 canvas. Three recent instances.
draw_bucket:
push {r4-r11,lr}
sub sp,sp,#4
ldr r0,[r4,#8]
cmp r0,#0
beq bucket_done
ldr r0,[r5,#12]
ldr r1,[r4]
sub r0,r0,r1
cmp r0,#120
bhi bucket_done
mov r2,r11
mov r3,r10
mov r8,#12
mov r9,#124
bl draw_line
mov r11,#0
hit_loop:
add r0,r4,#0x10
add r0,r0,r11,lsl #3
ldr r1,[r0,#4]
ldr r2,[r5,#12]
sub r2,r2,r1
cmp r2,#60
bhi next_hit
ldr r0,[r0]
cmp r0,#0
beq next_hit
ldr r1,buffer
bl damage_number
ldr r2,buffer
mov r3,r10
mov r0,#12
mul r8,r11,r0
add r8,r8,#24
mov r9,#124
bl draw_line
next_hit:
add r11,r11,#1
cmp r11,#3
blo hit_loop
ldr r0,[r4,#4]
ldr r1,buffer
ldr r2,total_label
bl copy_label
bl damage_number
ldr r2,buffer
mov r3,r10
mov r8,#64
mov r9,#124
bl draw_line
bucket_done:
add sp,sp,#4
pop {r4-r11,pc}

// Native draw uses a 0x238-byte canvas. Caller reserves 0x300, never 0x38.
draw_line:
push {r0-r3,r8,r9,r12,lr}
sub sp,sp,#16
mov r0,#0
mov r1,#1
stm sp,{r8,r9}
str r0,[sp,#8]
str r1,[sp,#12]
ldr r0,font
mov r1,r7
bl 0x0200b3a4
add sp,sp,#16
pop {r0-r3,r8,r9,r12,pc}

// Display 100 HP per native health unit, with two decimal places.
damage_number:
push {r2-r4,lr}
ldr r2,scale
umull r3,r4,r0,r2
adds r3,r3,#0x800
adc r4,r4,#0
mov r0,r3,lsr #12
orr r0,r0,r4,lsl #20
mov r2,#2
bl number
pop {r2-r4,pc}

// r0 unsigned integer, r1 output UTF16, r2 0 or 2 decimal places.
number:
push {r0,r2-r8,lr}
sub sp,sp,#4
mov r4,r0
mov r8,r2
ldr r3,powers
mov r6,#0
number_loop:
ldr r5,[r3],#4
cmp r5,#0
beq number_end
mov r7,#0
subtract_digit:
cmp r4,r5
subhs r4,r4,r5
addhs r7,r7,#1
bhs subtract_digit
cmp r7,#0
bne emit_digit
cmp r6,#0
bne emit_digit
cmp r8,#2
cmpeq r5,#100
beq emit_digit
cmp r5,#1
bne number_loop
emit_digit:
add r7,r7,#48
strh r7,[r1],#2
mov r6,#1
cmp r8,#2
cmpeq r5,#100
moveq r7,#46
strheq r7,[r1],#2
b number_loop
number_end:
mov r7,#0
strh r7,[r1]
add sp,sp,#4
pop {r0,r2-r8,pc}

// Append a constant label while retaining r0 numerical value.
copy_label:
push {r0,r3}
copy_loop:
ldrh r3,[r2],#2
cmp r3,#0
strhne r3,[r1],#2
bne copy_loop
pop {r0,r3}
bx lr

state: .word 0x02152420
font: .word 0x02151c20
buffer: .word 0x02151e20
combo_model: .word 0x02145c44
combo_label: .word 0x02151a20
dealt_label: .word 0x02151a40
taken_label: .word 0x02151a60
total_label: .word 0x02151a80
scale: .word 10000
powers: .word 0x02151aa0
