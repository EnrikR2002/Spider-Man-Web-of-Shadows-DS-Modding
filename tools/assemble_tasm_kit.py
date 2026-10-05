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
if len(code) > 0x1F00:
    raise SystemExit(f'Kit code overlaps the route table: {len(code)} bytes')
(ROOT / 'tools/tasm_kit.hex').write_text('\n'.join(code[i:i + 32].hex() for i in range(0, len(code), 32)) + '\n',
                                         encoding='utf-8')
print(len(code), 'bytes; SHA256', hashlib.sha256(code).hexdigest())
