#!/usr/bin/env python3
"""Optional Keystone reassembly of tools/tasm_kit.s and tasm_kit2.s; builds use the pinned hex."""
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'work/research-libs'))
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM  # noqa: E402

KIT_BASE = 0x02152C20
# (source stem, load address, code limit): the kit and its second block (v0.10.0).
BLOCKS = (('tasm_kit', KIT_BASE, 0x1F00), ('tasm_kit2', 0x02155420, 0x1A00))


def literal_errors(code, source):
    """Keystone silently wraps out-of-range literal loads: check every pc-relative
    load ('ldr rX,=V' or 'ldr rX,lit_name' from a '.word' table) reads its value.
    (tools/crowd_backend.py reuses these two validators by name: keep imports local.)"""
    import re
    import struct
    value = r'(-?(?:0x[0-9a-fA-F]+|\d+))'
    table = {m.group(1): int(m.group(2), 0) & 0xFFFFFFFF
             for m in re.finditer(r'^(lit\d*_\w+):\s*\.word\s+' + value, source, re.M)}
    wanted = []
    for m in re.finditer(r'^\s*ldr\w*\s+\w+,\s*(?:=\s*' + value + r'|(lit\d*_\w+))', source, re.M):
        wanted.append(int(m.group(1), 0) & 0xFFFFFFFF if m.group(1) else table.get(m.group(2)))
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


def native_branch_errors(code, source, base=KIT_BASE):
    """Every 'b/bl 0xADDR' (native code or the other kit block) must encode exactly that address, in order."""
    import re
    import struct
    wanted = [int(x, 16) for x in re.findall(r'^\s*b\w*\s+0x([0-9a-fA-F]{8})\b', source, re.M)]
    got = []
    for at in range(0, len(code), 4):
        word = struct.unpack_from('<I', code, at)[0]
        if (word >> 25) & 7 == 5 and word >> 28 != 0xF:
            delta = word & 0xFFFFFF
            if delta & 0x800000: delta -= 0x1000000
            target = base + at + 8 + delta * 4
            if not base <= target < base + len(code): got.append(target)
    return [] if got == wanted else [f'outside branches {[hex(x) for x in got[:4]]} != {[hex(x) for x in wanted[:4]]}']


def self_branch_errors(code):
    """No instruction may branch to itself. Keystone assembles a conditional call such as 'bleq label'
    that way (v0.13.0: Dragnet hung when its lines were dropped; the crash hunt found it)."""
    import struct
    return [f'branch to itself at {at:#x}' for at in range(0, len(code), 4)
            if (struct.unpack_from('<I', code, at)[0] & 0x0EFFFFFF) == 0x0AFFFFFE and code[at + 3] >> 4 != 0xF]


def assemble(stem, base, limit):
    source = (ROOT / f'tools/{stem}.s').read_text(encoding='utf-8')
    code = bytes(Ks(KS_ARCH_ARM, KS_MODE_ARM).asm(source, base)[0])
    errors = literal_errors(code, source) + native_branch_errors(code, source, base) + self_branch_errors(code)
    body = [line.split('//')[0].strip() for line in source.splitlines()]
    if [line for line in body if line][-1] != '.ltorg' or body.count('.ltorg') != 1:
        # Keystone mis-resolves absolute branch targets placed after a mid-file pool.
        errors.append('exactly one .ltorg, at the end of the source')
    if errors:
        raise SystemExit(f'{stem}: literal problem (use the mid-code lit_ table): ' + '; '.join(errors[:3]))
    if len(code) > limit:
        raise SystemExit(f'{stem}: code exceeds its space: {len(code)} bytes')
    (ROOT / f'tools/{stem}.hex').write_text('\n'.join(code[i:i + 32].hex() for i in range(0, len(code), 32)) + '\n',
                                            encoding='utf-8')
    print(stem, len(code), 'bytes; SHA256', hashlib.sha256(code).hexdigest())


if __name__ == '__main__':
    for block in BLOCKS:
        assemble(*block)
