"""TASM "never stand still" Red kit: guarded ARM9 extension over the v0.1.1 parent.

Rewrites the behavior of the seven Red purchase slots and, since v0.10.0, adds
three Red rows on unused ability bits (Web Rush, Ricochet, Momentum). Native
abilities, the native purchase records, Black form and unowned play keep their
original routes. Own code is stored as pinned text hex (tools/tasm_kit.hex and
tasm_kit2.hex); reassemble from tools/tasm_kit.s and tasm_kit2.s with
tools/assemble_tasm_kit.py (Keystone, research libs).
See docs/TASM_ROADMAP.md (design) and docs/TECHNICAL.md (engine evidence).
"""
from __future__ import annotations
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import wos_tool as w, combat_feedback, release_info, training_room

BASE = 0x02000000
TARGET = combat_feedback.TARGET            # existing extension destination 0214F420
OLD_CODE = 0x3600                          # existing HUD/flow image length
OLD_STATE_END = 0x3800                     # HUD state reaches TARGET+0x3748
KIT_BASE = TARGET + OLD_STATE_END          # 02152C20
CODE_SPACE = 0x2000
ROUTE_OFFSET = 0x1F00                      # animation route table inside code space
STATE_SPACE = 0x400
KIT_STATE = KIT_BASE + CODE_SPACE          # 02154C20
# v0.10.0: second block after the old 24 KiB reserve (the 1 KiB before it stays
# the lab's phantom area): code, the grown Red shop table, zeroed state.
KIT2_OFFSET = 0x6000                       # from TARGET
KIT2_BASE = TARGET + KIT2_OFFSET           # 02155420
KIT2_CODE = 0x1800
SHOP_OFFSET = 0x1800                       # Red purchase rows inside the block
BOTH_OFFSET = 0x1940                       # Both Suits purchase rows (v0.11.0)
DIAL_OFFSET = 0x1B00                       # chapter strength dial: two bytes per room 76..115 (zeros here)
DIAL_ROOMS = 40
KIT2_STATE = KIT2_BASE + 0x1C00            # 02157020
KIT2_SPACE = 0x2000
IMAGE = KIT2_OFFSET + KIT2_SPACE
RESERVE = 0x8000
PARENT_ARM9_SHA256 = release_info.ARM9_SHA256
SOURCE = 0x1439A0                          # extension image start in the ARM9 file
TABLE_POINTERS = 0xB64
ARENA_LOWER = 0xFF374

# site: (kit entry offset, parent instruction word)
HOOKS = {
    0x020B5738: (0x00, 0xE5980044),  # ldr r0,[r8,#0x44]  attack-state stay
    0x020B5334: (0x04, 0xE5981080),  # ldr r1,[r8,#0x80]  string node stay
    0x020B5C58: (0x08, 0xE5950024),  # ldr r0,[r5,#0x24]  evade choice
    0x020C31E4: (0x10, 0xE5972080),  # ldr r2,[r7,#0x80]  string node action
    0x02073B5C: (0x14, 0xEA0375EF),  # Sling physics branch -> kit per update
    0x02073A68: (0x18, 0xEA0377AC),  # HUD observer branch -> kit registry first
    0x02070480: (0x1C, 0xE5DD0040),  # ldrb r0,[sp,#0x40] action record lookup
    0x020B6B54: (0x20, 0xE5940000),  # ldr r0,[r4]        Y+back turn attack choice
    0x020B5464: (0x24, 0xE1D809D3),  # ldrsb r0,[r8,#0x93] Red Scissor repeat limit
    0x020B5508: (0x0C, 0xE5910004),  # ldr r0,[r1,#4]     Scissor repeat queued direction
    0x020B7B18: (0x28, 0xE5D01028),  # ldrb r1,[r0,#0x28] air attack stay
    0x020728F0: (0x2C, 0xEA03798A),  # Sling action-queue branch -> Perch substitution
    0x02078628: (0x30, 0xE12FFF34),  # blx r4: hit dispatch to the victim's ReceiveHit
    0x0205F420: (0x34, 0xE5823084),  # str r3,[r2,#0x84]: player HP store (training floor)
}
# site: (second-block entry offset, parent instruction word)
HOOKS2 = {
    0x020B21B8: (0x10, 0xE5960044),  # ldr r0,[r6,#0x44]  Red attack animation rate (Momentum)
}
# Ownership events 309..381 are ability bits 0..72 (three words at stats+0xC).
# Bits 73..95 of the third word are unused and survive a native save/reload
# (work/shop/bits_save_lab.py): the query/setter bounds rise so events up to
# 404 reach them. 382 stays the menu's "no event" sentinel (bit 73 is never set).
EVENT_BOUNDS = {
    0x020D2460: (0xE282005B, 0xE2820072),  # query: add r0,r2,#0x5b -> #0x72
    0x020D2478: (0xE3550049, 0xE3550060),  # query: cmp r5,#0x49 -> #0x60
    0x020D2634: (0xE283005B, 0xE2830072),  # setter: add r0,r3,#0x5b -> #0x72
    0x020D2658: (0xE3540049, 0xE3540060),  # setter: cmp r4,#0x49 -> #0x60
    0x020D26A8: (0xE3540049, 0xE3540060),
}
RED_TABLE = 0x120340                       # seven native 32-byte purchase rows
RED_POINTER, RED_COUNT = 0x120174, 0x12018C
BOTH_TABLE = 0x120260                      # seven native Both Suits rows
BOTH_POINTER, BOTH_COUNT = 0x120170, 0x120188
NO_EVENT = 382
STRING_COUNT = 1049                        # native string slots; shop texts are appended after them
# New Red rows: (key, ownership event, price, name, title, description). Event - 309 = ability bit.
SHOP_ROWS = (
    ('web_rush', 383, 300, 'Web Rush', 'Web Rush (Combo)',
     'In a ground combo, press \ue602: zip to\nthe next enemy. \ue601 continues the combo.'),
    ('ricochet', 384, 300, 'Ricochet', 'Ricochet',
     'Passive. Enemies you send flying\nknock down the enemies they hit.'),
    ('momentum', 385, 400, 'Momentum', 'Momentum',
     'Passive. Every combo meter tier\nshortens the wind-up and recovery\nof your ground combos.'),
)
# New Both Suits rows (v0.11.0): Vitality I..III, each needing the one before
# (required event) and blocking its refund while the next is owned (dependent).
# Damage to Spidey is divided by 1.25 / 1.5 / 1.75 (tools/tasm_kit2.s k2_damage).
BOTH_ROWS = (
    ('vitality1', 386, 500, 'Vitality I', 'Vitality I',
     'Passive. Your health bar holds\n25% more health. The red bar\nturns orange.'),
    ('vitality2', 387, 750, 'Vitality II', 'Vitality II',
     'Needs Vitality I. Your health\nbar holds 50% more. The red bar\nturns gold.'),
    ('vitality3', 388, 1000, 'Vitality III', 'Vitality III',
     'Needs Vitality II. Your health\nbar holds 75% more. The red bar\nturns green.'),
)
SHOP_BITS = {row[0]: row[1] - 309 for row in (*SHOP_ROWS, *BOTH_ROWS)}     # 74..76, 77..79
SHOP_TEXTS = tuple(text for row in (*SHOP_ROWS, *BOTH_ROWS) for text in row[3:])
PREVIOUS_TEXTS = 3 * len(SHOP_ROWS)        # shop texts in a v0.10.0 kit overlay
# Spider Perch replaces Sling Strike in the Mid-Air Snare slot: restore the
# native action-queue and contact instructions Sling had redirected.
RESTORE = {0x0209515C: (0xEB02EFEF, 0xEBFED051)}
# Web Kick response (attack kind 32): a lower pop-up that Leapfrog vaults.
IMPULSES = (0x11A2B8, 0x11AA98)
PARENT_IMPULSE, LEAP_IMPULSE = (-2253, 11469), (3072, 6144)
COUNT_OFFSET = 0x77F8
PARENT_COUNT = 3736
EXTRA_NAMES: tuple[str, ...] = ('zz_kit_ReflexFlip.sca', 'zz_kit_Spin.sca', 'zz_kit_PerchPound.sca',
                                   'zz_kit_LeapKick.sca', 'zz_kit_SkyAxe.sca', 'zz_kit_SenseCounter.sca',
                                   'zz_kit_ReflexBackflip.sca', 'zz_kit_RushKick.sca')
# Route rows: (action, kind, appended name). Kinds: 1 Spin Cycle repeat, 2 Reflex
# roll, 3 Perch stomp, 4 owned Red web kick (Leapfrog), 5 Skyjack juggle,
# 6 Spider-Sense counter, 7 Perch hop/spring flip, 8 Reflex neutral back tuck,
# 9 Web Rush kick.
# Native actions keep their bindings when unrouted.
ROUTES: tuple[tuple[int, int, str], ...] = ((133, 2, 'zz_kit_ReflexFlip.sca'), (60, 1, 'zz_kit_Spin.sca'), (130, 3, 'zz_kit_PerchPound.sca'),
                                             (50, 4, 'zz_kit_LeapKick.sca'), (4, 5, 'zz_kit_SkyAxe.sca'),
                                             (59, 6, 'zz_kit_SenseCounter.sca'), (133, 7, 'zz_kit_ReflexFlip.sca'),
                                             (139, 8, 'zz_kit_ReflexBackflip.sca'), (58, 9, 'zz_kit_RushKick.sca'))
# Authored clips: overlay name -> (native SCA with the same sample count, clip).
# The Split Decision clips overwrite the dedicated Rush resources (actions 61/60/62).
CLIP_SOURCES = {
    'zz_kit_ReflexFlip.sca': ('spd_RollDodge.sca', 'reflex_flip'),
    'zz_kit_ReflexBackflip.sca': ('spd_SideStepDodge.sca', 'reflex_backflip'),
    'zz_kit_Spin.sca': ('spd_GroundAttack15.sca', 'spin'),
    'zz_kit_PerchPound.sca': ('spd_RapidStompAttack.sca', 'perch_pound'),
    'zz_kit_LeapKick.sca': ('spd_GrapplePullAttackKick.sca', 'leap_kick'),
    'zz_kit_SkyAxe.sca': ('spd_AirAttack4.sca', 'sky_axe'),
    'zz_kit_SenseCounter.sca': ('spd_GroundAttack14.sca', 'sense_counter'),
    'zz_kit_RushKick.sca': ('spd_GroundAttack13.sca', 'rush_kick'),
    'zz_tasm_RushEntry.sca': ('spd_GroundAttack16.sca', 'split_corkscrew'),
    'zz_tasm_RushBridge.sca': ('spd_GroundAttack15.sca', 'split_kick'),
    'zz_tasm_RushFinish.sca': ('spd_GroundAttack17.sca', 'split_sweep'),
}
PROFILE = 'tasm-kit'
VERSION = '0.11.0'
RELEASE_DATE = '2026-10-12'
RELEASE_PROFILE = f'tasm-v{VERSION}'
PARENT_RELEASE = 'tasm-v0.1.1'
# Red purchase names (menu/list) and instructions; boot and Options version.
TEXT_EDITS = {
    50: f'TASM v{VERSION}\nPress a button to start', 74: f'Options v{VERSION}',
    183: 'Leapfrog', 184: 'Leapfrog',
    185: 'Grapple with \ue602, then press \ue601.\nKick, vault over, land behind.',
    186: 'Skyjack', 187: 'Skyjack',
    188: 'Grapple with \ue602, then press up.\nFloating juggle, finisher spikes.',
    189: 'Spider Perch', 190: 'Spider Perch',
    191: 'In mid-air, press \ue602 near an enemy.\n\ue601 pound, \ue602 next head, \ue600 spring.',
    192: 'Split Decision', 193: 'Split Decision',
    194: '\ue601, let the sweep end, \ue601, \ue601, \ue601.\nEach hit picks a side.',
    195: 'Spin Cycle', 196: 'Spin Cycle (Combo)',
    197: 'Needs Split Decision. \ue601, pause,\n\ue601, then mash \ue601. Left/Right steers.',
    198: 'Spider Reflex', 199: 'Spider Reflex',
    200: 'Red: \ue604 cancels any attack.\nHold a side to flip, \ue601 resumes.',
    201: 'Spider-Sense', 202: 'Spider-Sense',
    203: 'Needs Spider Reflex. \ue604 as an\nenemy attacks: flip behind, counter.',
    417: 'Sparring: you heal every 30 s.\nSELECT and Down: refill all.\nPause: Return to Save Point.',
}


def uses_kit(profile):
    return profile == PROFILE or bool(release_info.PROFILE_INFO.get(profile, {}).get('kit'))
CODE_SHA256 = '87b68be09574e0e44d41079ab7c8f51359d7cbfd4715a65c9584cfb7b99aa5de'
CODE2_SHA256 = 'a0d76f922465c9bb8f09e1ea305ea3f41046b94c2c6bcb1c5250f624d320d0b8'
ARM9_SHA256 = '3c6a34e02d38cdfc696f35b576dd2c4f0fcda3512a1c2ea23f876a47e116614c'


def branch(source, target):
    return combat_feedback.branch(source, target)


def code_bytes(block=1):
    path, limit, digest = ((Path(__file__).with_suffix('.hex'), ROUTE_OFFSET, CODE_SHA256) if block == 1 else
                           (Path(__file__).with_name('tasm_kit2.hex'), KIT2_CODE, CODE2_SHA256))
    raw = bytes.fromhex(path.read_text(encoding='utf-8'))
    if not raw or len(raw) > limit or len(raw) % 4:
        raise ValueError('Kit code exceeds its fixed space')
    if digest and w.sha256(raw) != digest:
        raise ValueError('Kit code differs from validated source')
    return raw


def shop_table(raw):
    """The seven parent Red rows (current prices) followed by the new rows."""
    rows = bytearray(raw[RED_TABLE:RED_TABLE + 7 * 32])
    if struct.unpack_from('<I', rows)[0] != 322 or w.u32(raw, RED_POINTER) != BASE + RED_TABLE or w.u32(raw, RED_COUNT) != 7:
        raise ValueError('Native Red purchase table differs')
    for index, (_, event, price, *_texts) in enumerate(SHOP_ROWS):
        first = STRING_COUNT + 3 * index
        rows += struct.pack('<8I', event, NO_EVENT, NO_EVENT, first, first + 1, first + 2, 1, price)
    return bytes(rows)


def both_table(raw):
    """The seven parent Both Suits rows followed by the Vitality chain."""
    rows = bytearray(raw[BOTH_TABLE:BOTH_TABLE + 7 * 32])
    if w.u32(raw, BOTH_POINTER) != BASE + BOTH_TABLE or w.u32(raw, BOTH_COUNT) != 7:
        raise ValueError('Native Both Suits purchase table differs')
    first = STRING_COUNT + 3 * len(SHOP_ROWS)
    for index, (_, event, price, *_texts) in enumerate(BOTH_ROWS):
        required = BOTH_ROWS[index - 1][1] if index else NO_EVENT
        dependent = BOTH_ROWS[index + 1][1] if index + 1 < len(BOTH_ROWS) else NO_EVENT
        text = first + 3 * index
        rows += struct.pack('<8I', event, required, dependent, text, text + 1, text + 2, 1, price)
    return bytes(rows)


def shop_strings(slots, current):
    """Append the shop texts after the native slots (or rewrite them in a previous kit overlay)."""
    from tools.qol_suits_menu import slot_count
    held = slot_count(current) - STRING_COUNT
    if held not in (0, PREVIOUS_TEXTS, len(SHOP_TEXTS)):
        raise ValueError('Unexpected string slot count for the shop texts')
    return slots.grown(current, {STRING_COUNT + i: text for i, text in enumerate(SHOP_TEXTS[:held])},
                       appended=SHOP_TEXTS[held:])


def route_table():
    """Route rows to appended resources: kit clips follow the three Rush additions."""
    rows = b''.join(struct.pack('<3I', action, kind, PARENT_COUNT + EXTRA_NAMES.index(name))
                    for action, kind, name in ROUTES)
    if len(rows) + 12 > CODE_SPACE - ROUTE_OFFSET:
        raise ValueError('Too many animation routes')
    return rows + bytes(12)


def grow_extension(rom, raw, kit_image):
    """Append the kit after the existing extension image; relocate later file data.

    Keeps the original two SDK autoload entries and the extension's third entry;
    only its copy length, the table pointers and the main arena lower bound move.
    """
    h = w.parse_header(rom)
    start = h['arm9_offset']
    table = SOURCE + OLD_CODE
    if (start != 0x4000 or len(raw) != table + 36 or
            struct.unpack_from('<2I', raw, TABLE_POINTERS) != (BASE + table, BASE + table + 36) or
            struct.unpack_from('<3I', raw, table + 24) != (TARGET, OLD_CODE, 0) or
            w.u32(raw, ARENA_LOWER) != TARGET + combat_feedback.RESERVE):
        raise ValueError('Unexpected parent extension layout')
    if len(kit_image) != IMAGE - OLD_CODE:
        raise ValueError('Kit image size differs')
    image = raw[SOURCE:table] + kit_image
    new = bytearray(raw[:SOURCE] + image + raw[table:table + 24] + struct.pack('<3I', TARGET, len(image), 0))
    new_table = SOURCE + len(image)
    struct.pack_into('<2I', new, TABLE_POINTERS, BASE + new_table, BASE + new_table + 36)
    struct.pack_into('<I', new, ARENA_LOWER, TARGET + RESERVE)
    return replace_arm9(rom, bytes(new))


def replace_arm9(rom, new):
    """Store a grown ARM9 binary; relocate ARM7/FNT/FAT/files by the padded growth."""
    h = w.parse_header(rom)
    start = h['arm9_offset']
    boundary = h['arm7_offset']
    delta = w.align_up(start + len(new)) - boundary
    if delta < 0 or h['used_rom_size'] + delta > len(rom) or (delta and any(x not in (0, 255) for x in rom[-delta:])):
        raise ValueError('Insufficient verified ROM padding for kit extension')
    out = bytearray(rom[:boundary] + bytes(delta) + rom[boundary:len(rom) - delta])
    out[start:start + len(new)] = new
    for field in (0x30, 0x40, 0x48, 0x68):
        offset = w.u32(rom, field)
        if offset < boundary: raise ValueError('Unsupported header file offset')
        struct.pack_into('<I', out, field, offset + delta)
    for index in range(h['fat_size'] // 8):
        a, b = struct.unpack_from('<2I', rom, h['fat_offset'] + index * 8)
        if a < boundary: raise ValueError('Unsupported NitroFS placement')
        struct.pack_into('<2I', out, h['fat_offset'] + delta + index * 8, a + delta, b + delta)
    struct.pack_into('<I', out, 0x2C, len(new))
    struct.pack_into('<I', out, 0x80, h['used_rom_size'] + delta)
    struct.pack_into('<H', out, 0x15E, w.crc16(out[:0x15E]))
    result = bytes(out)
    w.validate_rom(result, target=True)
    return result, delta


def apply_rom(rom):
    h = w.parse_header(rom)
    start, size = h['arm9_offset'], h['arm9_size']
    raw = rom[start:start + size]
    if w.sha256(raw) != PARENT_ARM9_SHA256:
        raise ValueError('Red kit requires the exact v0.1.1 ARM9 parent')
    changed = bytearray(raw)
    log = []
    for site, (offset, original) in sorted(HOOKS.items()):
        at = site - BASE
        if w.u32(raw, at) != original:
            raise ValueError(f'Kit hook site differs: {site:08X}')
        word = branch(site, KIT_BASE + offset)
        struct.pack_into('<I', changed, at, word)
        log.append({'field': 'red_kit_hook', 'address': site, 'old': original, 'new': word})
    for site, (offset, original) in sorted(HOOKS2.items()):
        at = site - BASE
        if w.u32(raw, at) != original:
            raise ValueError(f'Kit hook site differs: {site:08X}')
        word = branch(site, KIT2_BASE + offset)
        struct.pack_into('<I', changed, at, word)
        log.append({'field': 'red_kit_hook', 'address': site, 'old': original, 'new': word})
    for site, (original, word) in sorted(EVENT_BOUNDS.items()):
        at = site - BASE
        if w.u32(raw, at) != original:
            raise ValueError(f'Ownership event bound differs: {site:08X}')
        struct.pack_into('<I', changed, at, word)
        log.append({'field': 'ownership_event_bound', 'address': site, 'old': original, 'new': word})
    table = shop_table(raw)
    struct.pack_into('<I', changed, RED_POINTER, KIT2_BASE + SHOP_OFFSET)
    struct.pack_into('<I', changed, RED_COUNT, len(table) // 32)
    log.append({'field': 'red_purchase_rows', 'table': KIT2_BASE + SHOP_OFFSET, 'rows': len(table) // 32,
                'new': {row[0]: {'event': row[1], 'ability_bit': row[1] - 309, 'price': row[2]} for row in SHOP_ROWS}})
    both = both_table(raw)
    if SHOP_OFFSET + len(table) > BOTH_OFFSET or BOTH_OFFSET + len(both) > DIAL_OFFSET:
        raise ValueError('Purchase tables overlap')
    struct.pack_into('<I', changed, BOTH_POINTER, KIT2_BASE + BOTH_OFFSET)
    struct.pack_into('<I', changed, BOTH_COUNT, len(both) // 32)
    log.append({'field': 'both_purchase_rows', 'table': KIT2_BASE + BOTH_OFFSET, 'rows': len(both) // 32,
                'new': {row[0]: {'event': row[1], 'ability_bit': row[1] - 309, 'price': row[2]} for row in BOTH_ROWS}})
    for site, (parent, native) in sorted(RESTORE.items()):
        at = site - BASE
        if w.u32(raw, at) != parent:
            raise ValueError(f'Replaced Sling site differs: {site:08X}')
        struct.pack_into('<I', changed, at, native)
        log.append({'field': 'sling_hook_restored_native', 'address': site, 'old': parent, 'new': native})
    for at in IMPULSES:
        if struct.unpack_from('<2i', raw, at) != PARENT_IMPULSE:
            raise ValueError('Parent Rebound response differs')
        struct.pack_into('<2i', changed, at, *LEAP_IMPULSE)
        log.append({'field': 'web_kick_response_q12', 'arm9_offset': at, 'old': PARENT_IMPULSE, 'new': LEAP_IMPULSE})
    if w.u32(raw, COUNT_OFFSET) != PARENT_COUNT:
        raise ValueError('Glob resource count differs from the Rush parent')
    struct.pack_into('<I', changed, COUNT_OFFSET, PARENT_COUNT + len(EXTRA_NAMES))
    if EXTRA_NAMES:
        log.append({'field': 'Glob_resource_count', 'old': PARENT_COUNT, 'new': PARENT_COUNT + len(EXTRA_NAMES)})
    code = code_bytes()
    space = bytearray(CODE_SPACE)
    space[:len(code)] = code
    if ROUTES:
        rows = route_table()
        space[ROUTE_OFFSET:ROUTE_OFFSET + len(rows)] = rows
    block = bytearray(KIT2_SPACE)
    code2 = code_bytes(2)
    block[:len(code2)] = code2
    block[SHOP_OFFSET:SHOP_OFFSET + len(table)] = table
    block[BOTH_OFFSET:BOTH_OFFSET + len(both)] = both
    kit_image = (bytes(OLD_STATE_END - OLD_CODE) + bytes(space) + bytes(STATE_SPACE)
                 + bytes(KIT2_OFFSET - OLD_STATE_END - CODE_SPACE - STATE_SPACE) + bytes(block))
    result, delta = grow_extension(rom, bytes(changed), kit_image)
    nh = w.parse_header(result)
    digest = w.sha256(result[start:start + nh['arm9_size']])
    if ARM9_SHA256 and digest != ARM9_SHA256:
        raise ValueError(f'Unexpected kit ARM9: {digest}')
    log.append({'field': 'red_kit_extension', 'kit_base': KIT_BASE, 'code_size': len(code),
                'code_sha256': w.sha256(code), 'kit2_base': KIT2_BASE, 'code2_size': len(code2),
                'code2_sha256': w.sha256(code2), 'image_size': OLD_CODE + len(kit_image),
                'reserve': RESERVE, 'rom_relocation_bytes': delta, 'arm9_sha256': digest})
    return result, log


def author_overlays(glob, entries):
    """Bake every kit clip from clean native SCAs (same sample counts)."""
    from tools.animation_rig import AnimationRig
    from tools.kit_choreography import author
    from tools import kit_clips

    def clean(name):
        e = entries[name]
        return glob[e['offset']:e['offset'] + e['size']]
    rig = AnimationRig.parse(clean('spd.nsbmd'))
    idle = clean('spd_Idle.sca')
    return {target: author(clean(source), idle, rig.parents, kit_clips.CLIPS[clip])[0]
            for target, (source, clip) in CLIP_SOURCES.items()}


def generate(output=None):
    """Kit candidate: accepted v0.1.1 (or prior kit) overlays + kit clips + Red text + version."""
    import json
    import mod
    from tools import combat_profile as cp, oscorp_resources as expansion
    from tools.qol_suits_menu import StringSlots
    dest = w.safe_output(mod.project_path(output or f'build/version-{VERSION}'))
    if not dest.is_relative_to((mod.ROOT / 'build').resolve()):
        raise ValueError('Candidates belong in build/')
    rom, glob, manifest = mod.load_clean()
    entries = {e['name']: e for e in manifest['entries']}
    recipe_path = mod.ROOT / 'reference/gameplay_profile.json'
    overlays = mod.overlay_files(mod.ROOT / 'mods', list(entries), added_names=(*expansion.EXTRA_NAMES, *EXTRA_NAMES))
    current = cp.load_recipe(recipe_path, overlays)
    recipe = json.loads(recipe_path.read_text(encoding='utf-8'))
    if current not in (PARENT_RELEASE, RELEASE_PROFILE) and not uses_kit(current):
        raise ValueError('Kit release requires the accepted v0.1.1, a kit release or same-version recipe')
    if current != RELEASE_PROFILE and set(overlays) != set(recipe['required_overlays']):
        raise ValueError('Explicit merge required for additional overlays')
    overlays.update(author_overlays(glob, entries))
    e = entries[training_room.NAME]                      # Test Upgrades sparring Brutes
    overlays[training_room.NAME] = training_room.with_sparring(glob[e['offset']:e['offset'] + e['size']])
    for name in ('English.strings', 'American.strings'):
        e = entries[name]
        slots = StringSlots(glob[e['offset']:e['offset'] + e['size']])
        overlays[name] = shop_strings(slots, slots.repack(overlays[name], TEXT_EDITS))
    for name, data in overlays.items():
        w.atomic_write(dest / 'mods' / name, data, (mod.DEFAULT_ROM,))
    new_recipe = {'schema_version': 1, 'profile': RELEASE_PROFILE, 'release_version': VERSION,
                  'required_overlays': {name: w.sha256(data) for name, data in sorted(overlays.items())}}
    w.write_json(dest / 'gameplay_profile.json', new_recipe)
    result, _, log = mod.create_build(rom, glob, manifest, overlays, gameplay_profile=RELEASE_PROFILE)
    path = dest / 'Versioned.nds'
    w.atomic_write(path, result, (mod.DEFAULT_ROM,))
    w.write_json(path.with_suffix('.build.json'), log)
    h = w.parse_header(result)
    w.write_json(dest / 'release.json', {
        'version': VERSION, 'rom_sha256': w.sha256(result),
        'arm9_sha256': w.sha256(result[h['arm9_offset']:h['arm9_offset'] + h['arm9_size']]),
        'parent_profile': PARENT_RELEASE, 'text_edits': TEXT_EDITS, 'clips': CLIP_SOURCES,
        'qualification': 'Structural candidate; emulator replays and player checks required.'})
    return path


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', default=None)
    args = parser.parse_args()
    try:
        print(generate(args.out))
    except (OSError, ValueError) as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(1)
