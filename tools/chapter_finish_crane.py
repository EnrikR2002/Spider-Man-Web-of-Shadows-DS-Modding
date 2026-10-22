"""Exact-owner Freight edge routing and clearer hoist exposure/aftermath."""
import re
import struct
from tools import creature_forge as forge, crane_row, chapter_spectacle_art as art
from tools import midnight_reliability_combat as reliable, chapter_renewal_combat
from tools.chapter_spectacle_combat import replace_once

# Existing solid overhangs, in ascending height. The waypoints clear the actual
# roof and collision capsule before a vertical native jump returns onto its top.
ROOFS = ((40, 88, 17, 20, 28, 100), (80, 124, 39, 42, 68, 136),
         (128, 188, 61, 64, 116, 200), (208, 268, 81, 84, 196, 280),
         (288, 348, 101, 104, 276, 360), (346, 388, 109, 112, 334, 390))


def checked_asm(source, at):
    code = chapter_renewal_combat.asm(source, at)
    values = {name: int(value, 0) & 0xffffffff for name, value in
              re.findall(r'^\s*(\w+):\s*\.word\s+(0x[0-9a-fA-F]+|\d+)\s*$', source, re.M)}
    wanted = [values[name] for name in re.findall(r'^\s*ldr\w*\s+r\d+,\s*(\w+)\s*$', source, re.M)]
    actual = []
    for offset in range(0, len(code), 4):
        word = struct.unpack_from('<I', code, offset)[0]
        if word & 0x0f7f0000 == 0x051f0000 and word >> 28 != 15:
            displacement = word & 0xfff if word & 0x800000 else -(word & 0xfff)
            target = offset+8+displacement
            if not 0 <= target <= len(code)-4:
                raise ValueError('Crane adapter literal wrapped out of range')
            actual.append(struct.unpack_from('<I', code, target)[0])
    if actual != wanted:
        raise ValueError('Crane adapter literal targets differ from source')
    return code


def navigation(at, states, slots, roofs, hero):
    return checked_asm(f'''
        push {{r1-r12,lr}}
        sub sp,sp,#4
        ldr r0,[r7,#12]
        cmp r0,#1
        bne native
        ldr r0,stats
        ldr r0,[r0]
        cmp r0,#0
        beq native
        ldr r0,[r0]
        cmp r0,#97
        bne native
        cmp r5,#26
        bhs native
        ldr r0,[r4,#0x14]
        cmp r0,#7
        bhi native
        ldr r0,[r8,#20]
        cmp r0,#0
        bne native
        ldr r0,slots
        sub r0,r8,r0
        ldr r7,states
        add r7,r7,r0
        ldr r0,[r7]
        cmp r0,r4
        ldr r0,[r7,#4]
        cmpeq r0,r6
        beq same_owner
        str r4,[r7]
        str r6,[r7,#4]
        mov r0,#0
        str r0,[r7,#8]
        str r0,[r7,#16]
        str r0,[r7,#28]
    same_owner:
        ldr r8,[r11,#0x7c]
        ldr r0,[r11,#0x160]
        add r8,r8,r0
        ldr r9,[r11,#0x80]
        ldr r0,[r11,#0x164]
        add r9,r9,r0
        ldr r0,hero
        ldr r0,[r0]
        ldr r0,[r0,#0x30]
        ldr r10,[r0,#0x7c]
        ldr r1,[r0,#0x160]
        add r10,r10,r1
        ldr r11,[r0,#0x80]
        ldr r1,[r0,#0x164]
        add r11,r11,r1
        sub r0,r11,r9
        ldr r1,[r7,#8]
        cmp r1,#0
        beq need_above
        @ Do not drop the route at the jump apex. The actor must travel back
        @ over the roof and actually land before ordinary pursuit resumes.
        cmp r1,#3
        bne phase
        ldr r1,[r6,#0x10]
        tst r1,#0x80
        beq phase
        ldr r1,[r6,#0x1c]
        cmp r1,#0
        bne phase
        cmp r0,#0x9000
        bge phase
        cmn r0,#0x9000
        bgt release
        b phase
    need_above:
        cmp r0,#0x9000
        ble release
        cmp r0,#0x50000
        bgt release
        ldr r0,[r7,#8]
        cmp r0,#0
        bne phase
        ldr r5,roofs
    scan:
        ldr r0,[r5]
        cmp r0,#0
        beq native
        sub r0,r0,#0x4000
        cmp r8,r0
        blt next
        ldr r0,[r5,#4]
        add r0,r0,#0x4000
        cmp r8,r0
        bgt next
        ldr r0,[r5,#8]
        sub r0,r0,#0x1000
        cmp r9,r0
        bge next
        ldr r0,[r5,#12]
        add r0,r0,#0x2000
        cmp r11,r0
        blt next
        ldr r0,[r5,#16]
        ldr r1,[r5,#20]
        subs r2,r8,r0
        rsbmi r2,r2,#0
        subs r3,r8,r1
        rsbmi r3,r3,#0
        cmp r2,r3
        movhi r0,r1
        str r0,[r7,#12]
        ldr r0,[r5,#12]
        add r0,r0,#0x5800
        str r0,[r7,#24]
        mov r0,#1
        str r0,[r7,#8]
        mov r0,#0
        str r0,[r7,#16]
        str r0,[r7,#28]
        str r8,[r7,#20]
        b phase
    next:
        add r5,r5,#24
        b scan
    phase:
        ldr r0,[r7,#16]
        add r0,r0,#1
        str r0,[r7,#16]
        cmp r0,#240
        bhi release
        ldr r0,[r7,#8]
        cmp r0,#1
        beq edge
        cmp r0,#2
        beq lift
        b landing
    edge:
        ldr r0,[r7,#12]
        subs r0,r0,r8
        rsbmi r1,r0,#0
        movpl r1,r0
        cmp r1,#0x2000
        bls edge_clear
        mov r5,r0
        ldr r1,[r7,#20]
        str r8,[r7,#20]
        subs r1,r8,r1
        rsbmi r1,r1,#0
        ldr r2,[r7,#28]
        cmp r1,#64
        movhi r2,#0
        addls r2,r2,#1
        str r2,[r7,#28]
        cmp r2,#12
        blo steer
        ldr r0,[r6,#0x10]
        tst r0,#0x80
        beq steer
        ldr r0,[r6,#0x1c]
        cmp r0,#0
        bne steer
        mov r0,#0
        str r0,[r7,#28]
        bl jump
        b steer
    edge_clear:
        mov r0,#2
        str r0,[r7,#8]
        mov r0,#0
        str r0,[r7,#16]
    lift:
        ldr r0,[r7,#24]
        cmp r9,r0
        bge lift_clear
        mov r5,#0
        ldr r0,[r6,#0x10]
        tst r0,#0x80
        beq steer
        ldr r0,[r6,#0x1c]
        cmp r0,#0
        bne steer
        bl jump
        b steer
    lift_clear:
        mov r0,#3
        str r0,[r7,#8]
        mov r0,#0
        str r0,[r7,#16]
    landing:
        sub r5,r10,r8
        cmp r5,#0x2000
        rsblt r0,r5,#0
        cmplt r0,#0x2000
        movlt r5,#0
    steer:
        ldr r0,slots
        ldr r1,states
        sub r1,r7,r1
        add r0,r0,r1
        cmp r5,#0
        movgt r1,#1
        movle r1,#0
        str r1,[r0,#24]
        ldr r1,speed
        rsblt r1,r1,#0
        moveq r1,#0
        str r1,[r0,#28]
        mvn r1,#5
        str r1,[r0,#16]
        mov r0,#1
        ldr r1,[r6,#0x1c]
        cmp r1,#0
        movne r0,#5
        b done
    jump:
        push {{r0-r3,r12,lr}}
        mov r0,r6
        bl #0x020739b4
        ldr r0,impulse
        str r0,[r6,#0x1c]
        pop {{r0-r3,r12,pc}}
    release:
        mov r0,#0
        str r0,[r7,#8]
        str r0,[r7,#16]
        str r0,[r7,#28]
    native:
        mov r0,#0
    done:
        add sp,sp,#4
        pop {{r1-r12,pc}}
    stats: .word 0x02145c5c
    states: .word 0x{states:x}
    slots: .word 0x{slots:x}
    hero: .word 0x{hero:x}
    roofs: .word 0x{roofs:x}
    speed: .word 3277
    impulse: .word 18842
    ''', at)


def secondary(at, old, states, slots, config):
    return checked_asm(f'''
        push {{r4-r8,lr}}
        mov r4,r0
        bl #0x{old:x}
        mov r5,r0
        cmp r5,#26
        bhs done
        ldr r0,stats
        ldr r0,[r0]
        cmp r0,#0
        beq done
        ldr r0,[r0]
        cmp r0,#97
        bne done
        ldr r6,slots
        ldr r7,states
        mov r8,#32
    scan:
        ldr r0,[r6]
        cmp r0,r4
        beq owned
        add r6,r6,#32
        add r7,r7,#32
        subs r8,r8,#1
        bne scan
        b done
    owned:
        ldr r0,[r7]
        cmp r0,r4
        bne done
        ldr r0,[r4,#0x44]
        ldr r1,[r6,#4]
        cmp r0,r1
        ldr r1,[r7,#4]
        cmpeq r0,r1
        bne done
        ldr r1,[r0,#0x40]
        ldr r2,config
        cmp r1,r2
        bne done
        ldr r1,[r0,#0x44]
        cmp r1,#0
        ble done
        ldr r0,[r7,#8]
        cmp r0,#0
        ldrne r5,keep
    done:
        mov r0,r5
        pop {{r4-r8,pc}}
    stats: .word 0x02145c5c
    states: .word 0x{states:x}
    slots: .word 0x{slots:x}
    config: .word 0x{config:x}
    keep: .word 0x7fffffff
    ''', at)


def source(meta, *, nav=0, states=0):
    f = meta['creature_forge']['runtime']
    r = meta['midnight_reliability']['runtime']
    captured = []
    def transform(text):
        text = reliable.decisions(text, meta['chapter_spectacle']['runtime']['navigation'],
            meta['midnight_encore']['runtime']['poise'], r['state'], r['table'], f['hero'], r['armour'])
        if nav:
            text = replace_once(text, '        mov r12,r3\n        rsbmi r3,r3,#0', f'''        mov r12,r3
        rsbmi r3,r3,#0
        bl #0x{nav:x}
        cmp r0,#0
        movne r5,r0
        bne done''')
            text = replace_once(text, '    fresh:\n', f'''    fresh:
        push {{r0-r3}}
        ldr r0,finish_states
        ldr r1,slots
        sub r1,r8,r1
        add r0,r0,r1
        mov r1,#0
        str r1,[r0]
        pop {{r0-r3}}
''')
            text += f'\n finish_states: .word 0x{states:x}\n'
        captured.append(text)
        return text
    play = f['capture'] + len(forge.parent.combat.capture_hero(f['capture'], f['hero']))
    forge.combat.think(r['think'], f['records'], f['slots'], f['attack_counters'],
                      f['hero'], f['hero']-4, f['move_counters'], play, 653, rewrite=transform)
    return captured[0]


def apply(runtime, meta, names, blobs, native):
    f = meta['creature_forge']['runtime']
    r = meta['midnight_reliability']['runtime']
    parent = source(meta)
    expected = checked_asm(parent, r['think'])
    offset = forge.offset(r['think'])
    if runtime.arm[offset:offset+len(expected)] != expected:
        raise ValueError('Current v0.28 thinker does not reproduce exactly')
    states = runtime.alloc(bytes(32*32))
    roofs = runtime.alloc(b''.join(struct.pack('<6i', *(round(v*4096) for v in row)) for row in ROOFS) + bytes(24))
    nav = runtime.alloc()
    runtime.data.extend(navigation(nav, states, f['slots'], roofs, f['hero']))
    think = runtime.alloc()
    runtime.data.extend(checked_asm(source(meta, nav=nav, states=states), think))
    struct.pack_into('<I', runtime.new, forge.combat.THINK_SLOT-0x02000000, think)
    sec = runtime.alloc()
    runtime.data.extend(secondary(sec, r['secondary'], states, f['slots'], meta['creature_forge']['creatures']['ballast']['config']))
    struct.pack_into('<I', runtime.new, forge.combat.SECOND_SLOT-0x02000000, sec)
    changed = []
    for name, raw in {
        'zz_CS23_motor.nsbmd': machinery('motor'),
        'zz_CS23_motor_dead.nsbmd': machinery('motor', dead=True),
        'zz_CS23_shield.nsbmd': machinery('shield'),
        'zz_CS23_shield_broken.nsbmd': machinery('shield', broken=True),
        'zz_CR_hook.nsbmd': machinery('hook'),
        'zz_CR_warning.nsbmd': warning(),
    }.items():
        i = names.index(name)
        blobs[i] = raw + bytes((len(blobs[i])-len(raw)) % 4)
        changed.append(name)
    return {'modified_resources': changed, 'navigation_state': states, 'navigation': nav,
            'think': think, 'secondary': sec, 'roofs': ROOFS,
            'scope': 'Freight-only Ballast edge-clear, vertical jump, return-to-roof path. Native velocity, collision, damage, hurt and death retained.',
            'hoist': 'High-contrast lane limits and grabber, distinct guarded/open motor and visibly wrecked saved aftermath. Existing core damage, timing, phase, checkpoint, collision and rewards remain.'}


def machinery(kind, *, broken=False, dead=False):
    from tools import room_compiler as rc
    import math
    faces = []
    def face(color, points, orient=True):
        if orient:
            a, b, c = points[:3]
            if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]) < 0:
                points = tuple(reversed(points))
        faces.append((sum(c << (i*5) for i, c in enumerate(color)), tuple((*p, 0, 0) for p in points)))
    def box(a, y, z, b, top, zz, color):
        for q in rc.box(a, y, z, b, top, zz, rc.Look('none'), 1, 'front top left right under'):
            shade = .8 if q.corners[0][1] != q.corners[1][1] else 1
            face(tuple(round(c*shade) for c in color), q.corners, False)
    steel, rim, light = (10, 15, 18), (26, 20, 8), (13, 31, 29)
    if kind == 'hook':
        box(-10, 11, 0, 10, 18, 5, steel)
        box(-9, 14, 5, 9, 17, 6, rim)
        for side in (-1, 1):
            a, b = sorted((side*8, side*12))
            box(a, 0, 0, b, 13, 4, steel)
            a, b = sorted((side*3, side*12))
            box(a, 0, 0, b, 3, 5, rim)
            face((28, 29, 25), ((side*8, 11, 4.2), (side*11, 11, 4.2),
                                 (side*11, 3, 5.2), (side*6, 3, 5.2)))
        for x in (-2, 1):
            box(x, 18, -1, x+1, 62, 1, steel)
        box(-5, 11.5, 6, 5, 13.5, 6.5, (31, 23, 8))
    else:
        if dead:
            steel, rim, light = (5, 7, 8), (11, 10, 7), (3, 5, 5)
        box(-13, 0, 0, 13, 17, 3, steel)
        for a, b in ((-13, -10), (10, 13)):
            box(a, 1, 3, b, 16, 5, rim)
        box(-10, 1, 3, 10, 3, 5, rim)
        box(-10, 15, 3, 10, 17, 5, rim)
        if kind == 'shield':
            box(-9, 3, 5, 9, 15, 7, (10, 13, 15))
            # The guard remains visually closed during the damaged phase;
            # only the bright open motor invites a combo.
            for y in (5, 10):
                face((29, 20, 5), ((-8, y, 7.2), (6, y+3, 7.2),
                                   (8, y+3, 7.2), (-6, y, 7.2)))
            if broken:
                face((3, 4, 5), ((-4, 15, 7.4), (-1, 10, 7.4),
                                   (3, 7, 7.4), (0, 14, 7.4)))
                box(-10, 1, 6, -5, 3, 8, (17, 10, 4))
        else:
            box(-9, 3, 3, 9, 15, 4, (2, 4, 6))
            for n in range(16):
                a, b = n*math.tau/16, (n+1)*math.tau/16
                if dead and n in (2, 3, 9):
                    continue
                face(light if n % 2 == 0 else rim,
                    ((8*math.cos(a), 9+7*math.sin(a), 5), (8*math.cos(b), 9+7*math.sin(b), 5),
                     (5.4*math.cos(b), 9+4.5*math.sin(b), 5), (5.4*math.cos(a), 9+4.5*math.sin(a), 5)))
            if dead:
                box(-7, 2, 5, 5, 4, 7, (7, 8, 8))
                face((10, 10, 8), ((-5, 12, 5.4), (-1, 14, 5.4),
                                     (7, 5, 5.4), (3, 3, 5.4)))
                box(7, 0, 3, 13, 2, 7, (11, 10, 7))
            else:
                box(-3, 5, 5, 3, 13, 6, light)
                box(-1, 6, 6, 1, 12, 6.5, (31, 31, 27))
                for side in (-1, 1):
                    face((27, 29, 24), ((side*9, 7, 5.4), (side*5, 9, 5.4),
                                         (side*9, 11, 5.4), (side*10, 9, 5.4)))
    shifted = []
    for color, vertices in faces:
        if kind == 'hook':
            points = tuple((x, y, z-12, u, v) for x, y, z, u, v in vertices)
        else:
            points = tuple((x*.72, y*.78+1.5, z-10, u, v) for x, y, z, u, v in vertices)
        shifted.append((color, points))
    return art.mesh('CS29_'+kind, shifted)


def warning():
    # Same 24-unit native danger lane, with visible end stops and inward marks.
    # This is still a harmless, non-solid warning object, not early live damage.
    faces = []
    def face(color, points):
        a, b, c = points[:3]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]) < 0:
            points = tuple(reversed(points))
        faces.append((sum(c << (i*5) for i, c in enumerate(color)), tuple((*p, 0, 0) for p in points)))
    face((25, 17, 4), ((-12, .5, -14), (-12, .5, 10), (12, .5, 10), (12, .5, -14)))
    for side in (-1, 1):
        x = side*12
        face((31, 27, 10), ((x, .6, 4), (x, 2.4, 4), (x-side*2, 2.4, 4), (x-side*2, .6, 4)))
        face((4, 5, 5), ((side*8, .8, 4.2), (side*3, 1.5, 4.2),
                           (side*5, 2.0, 4.2), (side*10, 1.3, 4.2)))
    return art.mesh('CS29_Warning', faces)
