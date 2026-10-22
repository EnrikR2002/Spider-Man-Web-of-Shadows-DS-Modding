"""Scoped Skyjack velocity correction over the immutable published kit source.

Normal builds read frozen hex. Reassembly is optional and verifies the parent,
literal loads, native branches and unchanged fixed entry/route boundaries.
"""
from pathlib import Path
import argparse
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import crowd_backend, tasm_kit as kit, wos_tool as w

HEX = Path(__file__).with_suffix('.hex')
CODE_SHA256 = '454bddea22b244984b6fbabebc119e4e2ff7f7a2f6b3d082f483fef1d9507365'


def source():
    original = (ROOT / 'tools/tasm_kit.s').read_text(encoding='utf-8')
    return crowd_backend.candidate_source(original, 'sky-velocity')


def assemble():
    original = (ROOT / 'tools/tasm_kit.s').read_text(encoding='utf-8')
    if crowd_backend.assemble(original) != kit.code_bytes():
        raise ValueError('Published kit source no longer reproduces its pinned code')
    code = crowd_backend.assemble(source())
    if any((w.u32(code, at) & 0x0effffff) == 0x0afffffe
           for at in range(0, len(code), 4)):
        raise ValueError('Self-branch in corrected player kit')
    if code[:0x54] != kit.code_bytes()[:0x54]:
        # Branch destinations change after the shorter drift block, while the
        # entry vector instructions/offsets must remain ARM branches.
        for at in range(0, 0x54, 4):
            if w.u32(code, at) >> 24 != w.u32(kit.code_bytes(), at) >> 24:
                raise ValueError('Kit entry vector ABI changed')
    return code


def code_bytes():
    code = bytes.fromhex(HEX.read_text(encoding='utf-8'))
    if not CODE_SHA256 or w.sha256(code) != CODE_SHA256:
        raise ValueError('Skyjack corrected kit differs from its frozen pin')
    if len(code) > kit.ROUTE_OFFSET or len(code) % 4:
        raise ValueError('Skyjack code overlaps the existing route table')
    return code


def apply(rom):
    header = w.parse_header(rom)
    start = header['arm9_offset']
    arm = bytearray(rom[start:start + header['arm9_size']])
    at = kit.SOURCE + kit.OLD_STATE_END
    old = kit.code_bytes()
    expected = old + bytes(kit.ROUTE_OFFSET - len(old))
    if arm[at:at + kit.ROUTE_OFFSET] != expected:
        raise ValueError('Skyjack patch requires the exact published kit and padding')
    corrected = code_bytes()
    before = bytes(arm[kit.SOURCE:kit.SOURCE + kit.RESERVE])
    arm[at:at + kit.ROUTE_OFFSET] = corrected + bytes(kit.ROUTE_OFFSET - len(corrected))
    after = bytes(arm[kit.SOURCE:kit.SOURCE + kit.RESERVE])
    prefix = kit.OLD_STATE_END
    if before[:prefix] != after[:prefix] or before[prefix + kit.ROUTE_OFFSET:] != after[prefix + kit.ROUTE_OFFSET:]:
        raise ValueError('Skyjack patch changed unowned kit code/data/state')
    result, _ = kit.replace_arm9(rom, bytes(arm))
    return result, {'parent_code_sha256': w.sha256(old), 'code_sha256': w.sha256(corrected),
                    'bytes': len(corrected), 'kit_bytes': kit.RESERVE,
                    'scope': 'First kit code only; existing entry vectors, route table, second block, ownership, prices and state layout retained.',
                    'movement': 'Clamped juggle correction goes to actor horizontal velocity; native physics/collision apply travel.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assemble', action='store_true', required=True)
    parser.parse_args()
    raw = assemble()
    HEX.write_text(raw.hex() + '\n', encoding='utf-8')
    print(f'{len(raw)} bytes; SHA256 {w.sha256(raw)}')
