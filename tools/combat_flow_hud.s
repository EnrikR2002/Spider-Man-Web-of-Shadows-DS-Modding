// Revised HUD: column-major bars, bounded dirty rectangles, 15Hz drawing and idle exit.
// No stored actor pointer is dereferenced by rendering; update snapshots expire.
push {r0-r12,lr}
mrs r12,cpsr
push {r11,r12}
sub sp,sp,#0x300
ldr r5,state
ldr r6,[r5]
cmp r6,#0
beq hud_done
str r0,[r5,#8]
ldr r0,[r5,#12]
add r0,r0,#1
str r0,[r5,#12]
// Warm the stock font at room entry, avoiding asset initialization on a first hit.
ldr r0,[r5,#4]
cmp r0,#0
bne font_warmed
ldr r0,font
mov r1,#0
mov r2,#0
mov r3,#0
bl 0x0200b1dc
mov r0,#1
str r0,[r5,#4]
font_warmed:
ldr r0,[r5,#12]
// Rendering runs every second HUD update; expiry still uses every native tick.
tst r0,#1
bne hud_done
mov r0,#0
str r0,[r5,#0x6a4]
str r0,[r5,#0x6c0]
ldr r0,[r5,#0x28]
cmp r0,#0
beq check_active_bars
ldr r0,[r5,#12]
ldr r1,[r5,#0x20]
sub r0,r0,r1
cmp r0,#30
bhi check_active_bars
ldr r0,combo_model
ldr r0,[r0]
cmp r0,#0
beq check_active_bars
ldrb r1,[r0]
ldr r0,[r0,#4]
mov r2,#75
mul r1,r2,r1
add r0,r1,r0,asr #12
cmp r0,#0
movle r0,#0
str r0,[r5,#0x6a4]
check_active_bars:
ldr r10,[r5,#0x6a4]
add r4,r5,#0x400
mov r7,#8
active_scan:
ldr r0,[r4]
cmp r0,#0
beq active_next
ldr r0,[r5,#12]
ldr r1,[r4,#4]
sub r0,r0,r1
cmp r0,#2
bhi active_next
ldr r0,[r4,#8]
ldr r1,[r4,#12]
cmp r0,#0
ble active_next
cmp r0,r1
movlt r10,#1
active_next:
add r4,r4,#32
subs r7,r7,#1
bne active_scan
ldr r0,[r5,#0x6a0]
orrs r0,r0,r10
bne canvas_needed
ldr r0,[r5,#0x6b4]
add r0,r0,#1
str r0,[r5,#0x6b4]
b hud_done
canvas_needed:
ldr r0,[r5,#0x6b0]
add r0,r0,#1
str r0,[r5,#0x6b0]
font_ready:
// Clear only last draw's rectangles, and only cells still holding our tile IDs.
add r0,r6,#0x1c
bl 0x02008c94
mov r8,r0
ldr r7,[r5,#0x6a0]
add r4,r5,#0x700
mov r0,#0
str r0,[r5,#0x6a0]
clear_rect:
cmp r7,#0
beq cleared
ldr r0,[r4],#4
ldr r1,[r4],#4
and r2,r1,#255
mov r1,r1,lsr #8
clear_row:
mov r3,r2
add r9,r8,r0,lsl #1
clear_cell:
ldrh r11,[r9]
bic r11,r11,#0xfc00
sub r11,r11,#0x200
cmp r11,#0x100
mov r12,#0
strhlo r12,[r9]
ldr r12,[r5,#0x6b8]
add r12,r12,#1
str r12,[r5,#0x6b8]
add r9,r9,#2
subs r3,r3,#1
bne clear_cell
add r0,r0,#32
subs r1,r1,#1
bne clear_row
sub r7,r7,#1
b clear_rect
cleared:
cmp r10,#0
beq flush_layer
add r0,sp,#16
add r1,r6,#0x1c
mov r2,#0x200
bl 0x02009328
add r7,sp,#16
ldr r0,[r5,#0x6a4]
cmp r0,#0
beq draw_bars
ldr r1,buffer
mov r2,#0
bl number
ldr r2,buffer
mov r3,#239
mov r8,#160
mov r9,#30
bl draw_line
mov r0,#192
mov r1,#152
mov r2,#64
mov r3,#24
bl remember_rectangle
draw_bars:
mov r10,#0
add r4,r5,#0x400
bar_loop:
ldr r0,[r4]
cmp r0,#0
beq next_bar
ldr r0,[r5,#12]
ldr r1,[r4,#4]
sub r0,r0,r1
cmp r0,#2
bhi next_bar
ldr r0,[r4,#8]
ldr r1,[r4,#12]
cmp r0,#0
ble next_bar
cmp r0,r1
bge next_bar
// Project through the current native perspective camera, including movement.
bl project_bar
cmp r0,#0
beq next_bar
mov r8,r1
mov r9,r2
ldr r0,[r4,#8]
ldr r1,[r4,#12]
mov r2,#22
mul r0,r2,r0
mov r11,#0
bar_fraction:
cmp r0,r1
subhs r0,r0,r1
addhs r11,r11,#1
bhs bar_fraction
// Keep one red pixel for a living target below the bar resolution.
cmp r11,#0
moveq r11,#1
// Native canvas reads columns first: each column is four packed pixels.
ldr r0,bitmap
mov r1,#0
column_loop:
mov r2,#3
cmp r1,#0
cmpne r1,#23
beq column_store
cmp r1,r11
movls r2,#15
movhi r2,#2
column_store:
mov r3,#3
orr r3,r3,r2,lsl #4
orr r3,r3,r2,lsl #8
orr r3,r3,#0x3000
strh r3,[r0],#2
add r1,r1,#1
cmp r1,#24
blo column_loop
mov r0,r8
mov r1,r9
mov r2,#24
mov r3,#4
bl remember_rectangle
mov r0,r7
mov r1,#0
mov r2,r8
mov r3,r9
bl 0x020093f0
// SetXY has flushed the prior shape. Bound this shape to its own four rows.
mov r0,#0
str r0,[r7,#0x18]
mov r0,#4
str r0,[sp]
mov r0,#0
str r0,[sp,#4]
mov r0,r7
ldr r1,bitmap
mov r2,#4
mov r3,#24
bl 0x02009498
next_bar:
add r4,r4,#32
add r10,r10,#1
cmp r10,#8
blo bar_loop
mov r0,r7
bl 0x02009398
flush_layer:
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

// r4 snapshot -> r0 validity, r1 left pixel, r2 top pixel.
// Native renderer stores rotation at +0C, eye at +30 and FOV sin/cos +94/+98.
project_bar:
push {r3-r11,lr}
sub sp,sp,#32
ldr r0,camera
ldr r0,[r0]
cmp r0,#0
beq project_fail
ldr r8,[r0,#0x3c]
cmp r8,#0
beq project_fail
ldr r0,[r8]
ldr r1,perspective_vtable
cmp r0,r1
bne project_fail
ldr r0,[r4,#16]
ldr r1,[r8,#0x30]
sub r0,r0,r1
str r0,[sp]
ldr r0,[r4,#20]
ldr r1,[r4,#28]
add r0,r0,r1
ldr r1,[r8,#0x34]
sub r0,r0,r1
str r0,[sp,#4]
ldr r0,[r4,#24]
ldr r1,[r8,#0x38]
sub r0,r0,r1
str r0,[sp,#8]
mov r0,sp
add r1,r8,#12
add r2,sp,#16
bl 0x020f961c
ldr r0,[sp,#24]
rsb r9,r0,#0
cmp r9,#0x1000
ble project_fail
ldr r0,[r5,#0x6bc]
add r0,r0,#1
str r0,[r5,#0x6bc]
ldr r0,[r5,#0x6c0]
cmp r0,r8
beq projection_cached
ldr r0,[r8,#0x98]
ldr r1,[r8,#0x94]
cmp r1,#0
ble project_fail
bl 0x020fa840
str r0,[r5,#0x6c4]
ldr r1,[r8,#0x8c]
cmp r1,#0
ble project_fail
bl 0x020fa840
str r0,[r5,#0x6c8]
str r8,[r5,#0x6c0]
projection_cached:
ldr r10,[r5,#0x6c8]
ldr r0,[sp,#16]
mov r1,r9
bl 0x020fa840
smull r2,r3,r0,r10
mov r0,r2,lsr #12
orr r0,r0,r3,lsl #20
mov r1,#128
mul r0,r1,r0
mov r1,r0,asr #12
add r1,r1,#116
ldr r10,[r5,#0x6c4]
ldr r0,[sp,#20]
str r1,[sp,#28]
mov r1,r9
bl 0x020fa840
smull r2,r3,r0,r10
mov r0,r2,lsr #12
orr r0,r0,r3,lsl #20
mov r1,#96
mul r0,r1,r0
mov r2,r0,asr #12
rsb r2,r2,#90
ldr r1,[sp,#28]
cmp r1,#0
blt project_fail
cmp r1,#232
bgt project_fail
cmp r2,#4
blt project_fail
cmp r2,#152
bgt project_fail
mov r0,#1
b project_done
project_fail:
mov r0,#0
project_done:
add sp,sp,#32
pop {r3-r11,pc}

// r0 X, r1 Y, r2 width, r3 height. Up to eight bars and one numeral region.
remember_rectangle:
push {r0-r4,r12,lr}
ldr r4,[r5,#0x6a0]
cmp r4,#9
bhs remembered
and r12,r0,#7
add r2,r2,r12
add r2,r2,#7
mov r2,r2,lsr #3
and r12,r1,#7
add r3,r3,r12
add r3,r3,#7
mov r3,r3,lsr #3
orr r2,r2,r3,lsl #8
mov r0,r0,lsr #3
mov r1,r1,lsr #3
add r0,r0,r1,lsl #5
add r12,r5,#0x700
add r12,r12,r4,lsl #3
str r0,[r12]
str r2,[r12,#4]
add r4,r4,#1
str r4,[r5,#0x6a0]
remembered:
pop {r0-r4,r12,pc}

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

// Integer UTF16 decimal formatter, no label or inferred damage values.
number:
push {r0,r2-r8,lr}
sub sp,sp,#4
mov r4,r0
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
cmpne r6,#0
// Leading zeros skipped until a nonzero digit or the units place.
cmp r7,#0
bne emit_digit
cmp r6,#0
bne emit_digit
cmp r5,#1
bne number_loop
emit_digit:
add r7,r7,#48
strh r7,[r1],#2
mov r6,#1
b number_loop
number_end:
mov r7,#0
strh r7,[r1]
add sp,sp,#4
pop {r0,r2-r8,pc}

state: .word 0x02152420
font: .word 0x02151c20
buffer: .word 0x02151e20
bitmap: .word 0x02151f20
combo_model: .word 0x02145c44
camera: .word 0x02145c54
perspective_vtable: .word 0x02128a4c
powers: .word 0x02151aa0
