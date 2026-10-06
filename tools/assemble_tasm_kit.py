#!/usr/bin/env python3
"""Optional Keystone reassembly of tools/tasm_kit.s; builds use the pinned hex."""
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'work/research-libs'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM  # noqa: E402

KIT_BASE = 0x02152C20
source = (ROOT / 'tools/tasm_kit.s').read_text(encoding='utf-8')
code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, KIT_BASE)[0])


def literal_errors(code, source, base=KIT_BASE):
    """Keystone silently wraps out-of-range literal loads: check each 'ldr rX,=V'."""
    import re
    import struct
    pattern = r'^\s*ldr\w*\s+\w+,\s*=\s*(-?(?:0x[0-9a-fA-F]+|\d+))'
    wanted = [int(v, 0) & 0xFFFFFFFF for v in re.findall(pattern, source, re.M)]
    loads = []
    for at in range(0, len(code), 4):
        word = struct.unpack_from('<I', code, at)[0]
        if (word & 0x0F7F0000) == 0x051F0000 and word >> 28 != 0xF:     # ldr rX,[pc,#+-imm]
            offset = word & 0xFFF if word & 0x00800000 else -(word & 0xFFF)
            target = at + 8 + offset
            loads.append(struct.unpack_from('<I', code, target)[0] if 0 <= target <= len(code) - 4 else None)
    if len(loads) != len(wanted):
        return [f'{len(loads)} pc-relative loads for {len(wanted)} literals']
    return [f'literal {i}: {got} != {want:#x}' for i, (got, want) in enumerate(zip(loads, wanted)) if got != want]


errors = literal_errors(code, source)
body = [line.split('//')[0].strip() for line in source.splitlines()]
if [line for line in body if line][-1] != '.ltorg' or body.count('.ltorg') != 1:
    # Keystone mis-resolves absolute branch targets placed after a mid-file pool.
    errors.append('exactly one .ltorg, at the end of the source')
if errors:
    raise SystemExit('Literal pool problem (build far constants from immediates): ' + '; '.join(errors[:3]))
if len(code) > 0x1F00:
    raise SystemExit(f'Kit code overlaps the route table: {len(code)} bytes')
(ROOT / 'tools/tasm_kit.hex').write_text('\n'.join(code[i:i + 32].hex() for i in range(0, len(code), 32)) + '\n',
                                         encoding='utf-8')
print(len(code), 'bytes; SHA256', hashlib.sha256(code).hexdigest())
