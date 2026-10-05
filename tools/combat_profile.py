"""Hash-bounded CS5E combat profiles from the exact clean ARM9.

Historical Rebound/Web Vault profiles remain available as paired controls.
The current flow profile composes matched Vault lift, bounded passing/turning
Sling and continuous bars with reduced drawing through guarded own extensions.
Purchase records and shared input routes stay native.
See docs/COMBAT_FLOW.md; historical profiles remain for paired controls.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
from tools import combat_feedback, combat_hud, tasm_sling_strike, combat_flow, training_refill, oscorp_resources

ARM9_SHA256 = 'e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc'
REBOUND_ARM9_SHA256 = '3298417ae06c47571ea559ebe3e18d33da4ed6f3bfcdcb85025628c440438837'
WEB_VAULT_ARM9_SHA256 = '6e563225538658c6c8437ede1886037132adc5ed865693727ef60457072529bf'
KNOWN_ARM9_HASHES = (ARM9_SHA256, REBOUND_ARM9_SHA256, WEB_VAULT_ARM9_SHA256,
                    combat_feedback.ARM9_SHA256, combat_hud.ARM9_SHA256,
                    tasm_sling_strike.ARM9_SHA256, combat_flow.ARM9_SHA256, training_refill.ARM9_SHA256, oscorp_resources.ARM9_SHA256)
IMPULSE_OFFSETS = (0x11A2B8, 0x11AA98)
NATIVE_IMPULSE, REBOUND_IMPULSE = -9011, -4506
VAULT_OFFSET = 0xC9268
NATIVE_VAULT_WORDS = (0xE3A01025, 0xE3A00B03, 0xE58D14BC, 0xE58D04B8, 0xEA000014)
# mov r0,r4; bl 020BF164; mov r1,#37; mov r0,#0xC00; b 020C925C.
# The shared stores at 020C925C retain native reaction 37 / strength 0xC00.
VAULT_WORDS = (0xE1A00004, 0xEBFFD7BC, 0xE3A01025, 0xE3A00B03, 0xEAFFFFF7)


def identify_arm9(raw):
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in KNOWN_ARM9_HASHES:
        raise ValueError('Unknown CS5E ARM9; combat profile/probes unsupported')
    return digest


def apply_rom(rom, enabled=False):
    if not enabled: return rom, []
    if enabled == oscorp_resources.PROFILE:
        parent,log=apply_rom(rom,'tasm-oscorp-rush')
        result,expansion_log=oscorp_resources.apply_rom(parent)
        return result,log+expansion_log
    if enabled == 'tasm-oscorp-rush':
        flow,log = apply_rom(rom,'tasm-combat-flow')
        result,training_log = training_refill.apply_rom(flow)
        return result,log+training_log
    if enabled == 'tasm-combat-flow':
        sling,log = apply_rom(rom,'tasm-sling-strike')
        result,flow_log = combat_flow.apply_rom(sling)
        return result,log+flow_log
    if enabled == 'tasm-sling-strike':
        hud,log = apply_rom(rom,'tasm-readable-combat')
        result,sling_log = tasm_sling_strike.apply_rom(hud)
        return result,log+sling_log
    if enabled == 'tasm-readable-combat':
        vault,log = apply_rom(rom,'tasm-web-vault')
        result,hud_log = combat_hud.apply_rom(vault)
        return result,log+hud_log
    if enabled == 'tasm-combat-feedback':
        vault,log = apply_rom(rom,'tasm-web-vault')
        result,feedback_log = combat_feedback.apply_rom(vault)
        return result,log+feedback_log
    if enabled not in (True, 'tasm-rebound', 'tasm-web-vault'):
        raise ValueError('Unsupported combat profile')
    if len(rom) < 0x30 or rom[12:16] != b'CS5E': raise ValueError('Expected CS5E ROM')
    start, _, address, size = struct.unpack_from('<4I', rom, 0x20)
    if address != 0x02000000 or not 0 < size <= len(rom)-start:
        raise ValueError('Unsupported ARM9 bounds')
    raw = rom[start:start+size]
    if hashlib.sha256(raw).hexdigest() != ARM9_SHA256:
        raise ValueError('Combat edits require the clean CS5E ARM9')
    out = bytearray(rom); log = []
    for offset in IMPULSE_OFFSETS:
        if struct.unpack_from('<i', raw, offset)[0] != NATIVE_IMPULSE:
            raise ValueError('Native Web Kick response differs')
        struct.pack_into('<i', out, start+offset, REBOUND_IMPULSE)
        log.append({'arm9_offset': offset, 'address': 0x02000000+offset,
                    'field': 'attack_kind_32_horizontal_impulse_q12',
                    'old': NATIVE_IMPULSE, 'new': REBOUND_IMPULSE})
    expected = REBOUND_ARM9_SHA256
    if enabled == 'tasm-web-vault':
        if struct.unpack_from('<5I', raw, VAULT_OFFSET) != NATIVE_VAULT_WORDS:
            raise ValueError('Native paid Web Launch event case differs')
        struct.pack_into('<5I', out, start+VAULT_OFFSET, *VAULT_WORDS)
        log.append({'arm9_offset': VAULT_OFFSET, 'address': 0x02000000+VAULT_OFFSET,
                    'field': 'paid_web_launch_event_native_hop',
                    'old_words': list(NATIVE_VAULT_WORDS), 'new_words': list(VAULT_WORDS)})
        expected = WEB_VAULT_ARM9_SHA256
    result = bytes(out)
    if identify_arm9(result[start:start+size]) != expected:
        raise ValueError('Unexpected combat ARM9 result')
    return result, log


def load_recipe(path, overlay):
    """Known complete recipes; required asset hashes prevent drift."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or data.get('schema_version') != 1 or
            data.get('profile') not in ('original', 'tasm-rebound', 'tasm-web-vault',
                                        'tasm-combat-feedback', 'tasm-readable-combat',
                                        'tasm-sling-strike', 'tasm-combat-flow', 'tasm-oscorp-rush', 'tasm-oscorp-rush-authored')):
        raise ValueError('Unsupported gameplay recipe')
    if data['profile'] == 'original': return False
    required = data.get('required_overlays')
    if not isinstance(required, dict) or not required:
        raise ValueError('Gameplay recipe needs exact overlay hashes')
    for name, digest in required.items():
        if name not in overlay or hashlib.sha256(overlay[name]).hexdigest() != digest:
            raise ValueError(f'Gameplay recipe overlay differs: {name}')
    return True if data['profile'] == 'tasm-rebound' else data['profile']
