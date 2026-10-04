"""Hash-bounded CS5E combat data edits; no executable instructions are changed.

Attack kind 32 is the native Web Kick finisher, selected for animation action 50
by 0x020B2498. Two target-response records contain its horizontal impulse.
Damage, vertical impulse, resistance flags, all instructions and the boss record
are retained. See docs/TASM1_REBOUND.md for the paired runtime evidence.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct

ARM9_SHA256 = 'e541bfcd02441db86b43b8649aaa13570be301d302ddfb198804b78528d215dc'
REBOUND_ARM9_SHA256 = '3298417ae06c47571ea559ebe3e18d33da4ed6f3bfcdcb85025628c440438837'
KNOWN_ARM9_HASHES = (ARM9_SHA256, REBOUND_ARM9_SHA256)
IMPULSE_OFFSETS = (0x11A2B8, 0x11AA98)
NATIVE_IMPULSE, REBOUND_IMPULSE = -9011, -4506


def identify_arm9(raw):
    digest = hashlib.sha256(raw).hexdigest()
    if digest not in KNOWN_ARM9_HASHES:
        raise ValueError('Unknown CS5E ARM9; combat profile/probes unsupported')
    return digest


def apply_rom(rom, enabled=False):
    if not enabled: return rom, []
    if len(rom) < 0x30 or rom[12:16] != b'CS5E': raise ValueError('Expected CS5E ROM')
    start, _, address, size = struct.unpack_from('<4I', rom, 0x20)
    if address != 0x02000000 or not 0 < size <= len(rom)-start:
        raise ValueError('Unsupported ARM9 bounds')
    raw = rom[start:start+size]
    if hashlib.sha256(raw).hexdigest() != ARM9_SHA256:
        raise ValueError('Rebound response edit requires the clean CS5E ARM9')
    out = bytearray(rom); log = []
    for offset in IMPULSE_OFFSETS:
        if struct.unpack_from('<i', raw, offset)[0] != NATIVE_IMPULSE:
            raise ValueError('Native Web Kick response differs')
        struct.pack_into('<i', out, start+offset, REBOUND_IMPULSE)
        log.append({'arm9_offset': offset, 'address': 0x02000000+offset,
                    'field': 'attack_kind_32_horizontal_impulse_q12',
                    'old': NATIVE_IMPULSE, 'new': REBOUND_IMPULSE})
    result = bytes(out)
    if identify_arm9(result[start:start+size]) != REBOUND_ARM9_SHA256:
        raise ValueError('Unexpected Rebound ARM9 result')
    return result, log


def load_recipe(path, overlay):
    """Only the known complete Rebound recipe; required asset hashes prevent drift."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or data.get('schema_version') != 1 or
            data.get('profile') not in ('original', 'tasm-rebound')):
        raise ValueError('Unsupported gameplay recipe')
    if data['profile'] == 'original': return False
    required = data.get('required_overlays')
    if not isinstance(required, dict) or not required:
        raise ValueError('Rebound recipe needs exact overlay hashes')
    for name, digest in required.items():
        if name not in overlay or hashlib.sha256(overlay[name]).hexdigest() != digest:
            raise ValueError(f'Gameplay recipe overlay differs: {name}')
    return True
