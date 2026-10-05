"""TASM "never stand still" Red kit: guarded ARM9 extension over the v0.1.1 parent.

Rewrites the behavior of the seven Red purchase slots only. Native abilities,
purchase records, Black form and unowned play keep their original routes.
Own code is stored as pinned text hex (tools/tasm_kit.hex); reassemble from
tools/tasm_kit.s with tools/assemble_tasm_kit.py (Keystone, research libs).
See docs/TASM_ROADMAP.md (design) and docs/TECHNICAL.md (engine evidence).
"""
from __future__ import annotations
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import wos_tool as w, combat_feedback, release_info

BASE = 0x02000000
TARGET = combat_feedback.TARGET            # existing extension destination 0214F420
OLD_CODE = 0x3600                          # existing HUD/flow image length
OLD_STATE_END = 0x3800                     # HUD state reaches TARGET+0x3748
KIT_BASE = TARGET + OLD_STATE_END          # 02152C20
CODE_SPACE = 0x2000
ROUTE_OFFSET = 0x1F00                      # animation route table inside code space
STATE_SPACE = 0x400
KIT_STATE = KIT_BASE + CODE_SPACE          # 02154C20
IMAGE = OLD_STATE_END + CODE_SPACE + STATE_SPACE
RESERVE = 0x6000
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
    0x020B7B18: (0x28, 0xE5D01028),  # ldrb r1,[r0,#0x28] air attack stay
    0x020728F0: (0x2C, 0xEA03798A),  # Sling action-queue branch -> Perch substitution
}
# Spider Perch replaces Sling Strike in the Mid-Air Snare slot: restore the
# native action-queue and contact instructions Sling had redirected.
RESTORE = {0x0209515C: (0xEB02EFEF, 0xEBFED051)}
# Web Kick response (attack kind 32): a lower pop-up that Leapfrog vaults.
IMPULSES = (0x11A2B8, 0x11AA98)
PARENT_IMPULSE, LEAP_IMPULSE = (-2253, 11469), (3072, 6144)
COUNT_OFFSET = 0x77F8
PARENT_COUNT = 3736
EXTRA_NAMES: tuple[str, ...] = ('zz_kit_ReflexFlip.sca', 'zz_kit_Spin.sca', 'zz_kit_PerchPound.sca',
                                   'zz_kit_LeapKick.sca', 'zz_kit_SkyAxe.sca', 'zz_kit_SenseCounter.sca')
# Route rows: (action, kind, appended name). Kinds: 1 Spin Cycle repeat, 2 Reflex
# roll, 3 Perch stomp, 4 owned Red web kick (Leapfrog), 5 Skyjack juggle,
# 6 Spider-Sense counter. Native actions keep their bindings when unrouted.
ROUTES: tuple[tuple[int, int, str], ...] = ((133, 2, 'zz_kit_ReflexFlip.sca'), (60, 1, 'zz_kit_Spin.sca'), (130, 3, 'zz_kit_PerchPound.sca'),
                                             (50, 4, 'zz_kit_LeapKick.sca'), (4, 5, 'zz_kit_SkyAxe.sca'),
                                             (59, 6, 'zz_kit_SenseCounter.sca'))
# Authored clips: overlay name -> (native SCA with the same sample count, clip).
# The Split Decision clips overwrite the dedicated Rush resources (actions 61/60/62).
CLIP_SOURCES = {
    'zz_kit_ReflexFlip.sca': ('spd_RollDodge.sca', 'reflex_flip'),
    'zz_kit_Spin.sca': ('spd_GroundAttack15.sca', 'spin'),
    'zz_kit_PerchPound.sca': ('spd_RapidStompAttack.sca', 'perch_pound'),
    'zz_kit_LeapKick.sca': ('spd_GrapplePullAttackKick.sca', 'leap_kick'),
    'zz_kit_SkyAxe.sca': ('spd_AirAttack4.sca', 'sky_axe'),
    'zz_kit_SenseCounter.sca': ('spd_GroundAttack14.sca', 'sense_counter'),
    'zz_tasm_RushEntry.sca': ('spd_GroundAttack16.sca', 'split_corkscrew'),
    'zz_tasm_RushBridge.sca': ('spd_GroundAttack15.sca', 'split_kick'),
    'zz_tasm_RushFinish.sca': ('spd_GroundAttack17.sca', 'split_sweep'),
}
PROFILE = 'tasm-kit'
VERSION = '0.2.0'
RELEASE_DATE = '2026-10-05'
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
    191: 'In mid-air, press \ue602 near an enemy.\nRide and pound, \ue601 keeps pounding.',
    192: 'Split Decision', 193: 'Split Decision',
    194: '\ue601, let the sweep end, \ue601, \ue601, \ue601.\nEach hit picks a side.',
    195: 'Spin Cycle', 196: 'Spin Cycle (Combo)',
    197: 'Needs Split Decision. \ue601, pause,\n\ue601, then mash \ue601. Left/Right steers.',
    198: 'Spider Reflex', 199: 'Spider Reflex',
    200: 'Red: \ue604 cancels any attack.\nHold a side to flip, \ue601 resumes.',
    201: 'Spider-Sense', 202: 'Spider-Sense',
    203: 'Needs Spider Reflex. \ue604 as an\nenemy attacks: flip behind, counter.',
}


def uses_kit(profile):
    return profile == PROFILE or bool(release_info.PROFILE_INFO.get(profile, {}).get('kit'))
CODE_SHA256 = '68b22ad3b91e7d608e13d8abba393afec37cf32af562c3d82b97c5445cf851da'
ARM9_SHA256 = '99392f5df4a0d2b37652ca5e0d040ae0d2a14702bd6a4fdfc1be3dbe0a91db77'


def branch(source, target):
    return combat_feedback.branch(source, target)


def code_bytes():
    raw = bytes.fromhex(Path(__file__).with_suffix('.hex').read_text(encoding='utf-8'))
    if not raw or len(raw) > ROUTE_OFFSET or len(raw) % 4:
        raise ValueError('Kit code exceeds its fixed space')
    if CODE_SHA256 and w.sha256(raw) != CODE_SHA256:
        raise ValueError('Kit code differs from validated source')
    return raw


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
    kit_image = bytes(OLD_STATE_END - OLD_CODE) + bytes(space) + bytes(STATE_SPACE)
    result, delta = grow_extension(rom, bytes(changed), kit_image)
    nh = w.parse_header(result)
    digest = w.sha256(result[start:start + nh['arm9_size']])
    if ARM9_SHA256 and digest != ARM9_SHA256:
        raise ValueError(f'Unexpected kit ARM9: {digest}')
    log.append({'field': 'red_kit_extension', 'kit_base': KIT_BASE, 'code_size': len(code),
                'code_sha256': w.sha256(code), 'image_size': OLD_CODE + len(kit_image),
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
    """Candidate v0.2.0: accepted v0.1.1 overlays + kit clips + Red text + version."""
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
    if current not in (PARENT_RELEASE, RELEASE_PROFILE):
        raise ValueError('Kit release requires the accepted v0.1.1 (or same-version) recipe')
    if current == PARENT_RELEASE and set(overlays) != set(recipe['required_overlays']):
        raise ValueError('Explicit merge required for additional overlays')
    overlays.update(author_overlays(glob, entries))
    for name in ('English.strings', 'American.strings'):
        e = entries[name]
        overlays[name] = StringSlots(glob[e['offset']:e['offset'] + e['size']]).repack(overlays[name], TEXT_EDITS)
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
