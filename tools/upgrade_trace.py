"""Read-only purchase/currency observations for the identified USA CS5E engine.

This is a RAM view, not a save editor. Addresses identify exact known ARM9 profiles;
heap pointers are discovered for each snapshot and never assumed constant.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import player_trace
from tools.combat_profile import identify_arm9, KNOWN_ARM9_HASHES

BASE = player_trace.BASE
ARM9_SHA256 = player_trace.ARM9_SHA256
STATS_POINTER_ADDRESS = 0x02145C5C
ABILITY_WORDS_OFFSET = 0x0C
CURRENCY_OFFSET = 0x44
PLAYER_ABILITIES_POINTER_OFFSET = 0xE8
RED_BITS = {
    'Web Kick': 13, 'Web Launch': 14, 'Mid-Air Snare': 15,
    'Spider Dance': 16, 'Scissor-Kick Special': 17,
    'Amazing Speed Boost': 18, 'Ultimate Speed Boost': 19,
}


def verify_rom(rom: bytes) -> str:
    """Require CS5E and a known combat-data profile before interpreting RAM fields."""
    if len(rom) < 0x30 or rom[12:16] != b'CS5E':
        raise ValueError('Expected a CS5E ROM header')
    offset, _, address, size = struct.unpack_from('<4I', rom, 0x20)
    if address != BASE or size <= 0 or offset > len(rom) - size:
        raise ValueError('ARM9 location outside the supported ROM layout')
    return identify_arm9(rom[offset:offset + size])


def snapshot(ram: bytes, *, arm9_sha256: str) -> dict:
    if arm9_sha256 not in KNOWN_ARM9_HASHES:
        raise ValueError('Purchase probe requires a known CS5E combat profile')
    player = player_trace.sample(ram)
    stats = struct.unpack_from('<I', ram, STATS_POINTER_ADDRESS - BASE)[0]
    offset = stats - BASE
    if stats % 4 or not 0 <= offset <= len(ram) - CURRENCY_OFFSET - 4:
        raise ValueError('Stats pointer outside aligned main RAM')
    actor_offset = player['actor_address'] - BASE
    if actor_offset + PLAYER_ABILITIES_POINTER_OFFSET + 4 > len(ram):
        raise ValueError('Player ability pointer outside main RAM')
    ability_pointer = struct.unpack_from('<I', ram,
        actor_offset + PLAYER_ABILITIES_POINTER_OFFSET)[0]
    if ability_pointer != stats + ABILITY_WORDS_OFFSET:
        raise ValueError('Player/stats ability pointers disagree')
    words = struct.unpack_from('<3I', ram, offset + ABILITY_WORDS_OFFSET)
    def owned(bit): return bool(words[bit // 32] & (1 << (bit % 32)))
    return {
        'actor_address': player['actor_address'], 'stats_address': stats,
        'ability_words_address': ability_pointer,
        'ability_words': list(words),
        'currency': struct.unpack_from('<I', ram, offset + CURRENCY_OFFSET)[0],
        'red_skills': {name: {'ability_bit': bit, 'event_id': bit + 309,
                            'owned': owned(bit)} for name, bit in RED_BITS.items()},
        'black_ability_bits': {str(bit): owned(bit) for bit in range(20, 27)},
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--ram', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        digest = verify_rom(args.rom.read_bytes())
        print(json.dumps(snapshot(args.ram.read_bytes(), arm9_sha256=digest), indent=2))
    except (OSError, ValueError, struct.error) as exc:
        print(f'error: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__': raise SystemExit(main())
