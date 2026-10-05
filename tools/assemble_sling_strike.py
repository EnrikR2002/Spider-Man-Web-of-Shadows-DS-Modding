"""Optional Keystone assembler; standard-library builds use pinned own-code hex."""
from pathlib import Path
import hashlib
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM

p = Path(__file__).with_name('sling_strike.s')
source = p.read_text(encoding='utf-8')
action, rest = source.split('// SPLIT DAMAGE')
damage, physics = rest.split('// SPLIT PHYSICS')
ks = Ks(KS_ARCH_ARM, KS_MODE_ARM)
code = bytearray(0x600)
for at, src in ((0, action), (0x200, damage), (0x400, physics)):
    raw = bytes(ks.asm(src, 0x02150f20 + at)[0])
    if len(raw) > 0x200: raise ValueError('Sling stub overlaps another entry')
    code[at:at + len(raw)] = raw
    print(hex(at), len(raw))
p.with_suffix('.hex').write_text('\n'.join(code[i:i+32].hex() for i in range(0, len(code),32))+'\n', encoding='utf-8')
print('SHA256', hashlib.sha256(code).hexdigest())
