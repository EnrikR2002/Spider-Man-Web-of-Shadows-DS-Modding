#!/usr/bin/env python3
"""Optional Keystone reassembly; normal builds use the pinned own-code hex."""
from pathlib import Path
import hashlib
from keystone import Ks, KS_ARCH_ARM, KS_MODE_ARM
ROOT=Path(__file__).resolve().parent
ks=Ks(KS_ARCH_ARM,KS_MODE_ARM)
code=bytearray(bytes.fromhex((ROOT/'combat_hud.hex').read_text()))
# Carry the historical constructor's extended marker cleanup forward.
code[0x1000+0x20:0x1000+0x24]=bytes.fromhex('6e2fa0e3')
s=(ROOT/'combat_flow_sling.s').read_text()
a,rest=s.split('// SPLIT DAMAGE');d,p=rest.split('// SPLIT PHYSICS')
for offset,source,limit in ((0,(ROOT/'combat_flow_hud.s').read_text(),0x1000),
 (0x1b00,a,0x200),(0x1d00,d,0x200),(0x1f00,p,0x200),
 (0x2100,(ROOT/'combat_flow_vault.s').read_text(),0x400),
 (0x2500,(ROOT/'combat_flow_observer.s').read_text(),0x180)):
 raw=bytes(ks.asm(source,0x0214f420+offset)[0])
 if len(raw)>limit: raise ValueError(f'Own-code entry {offset:x} overlaps next entry: {len(raw)}')
 code[offset:offset+limit]=bytes(limit)
 code[offset:offset+len(raw)]=raw
 print(hex(offset),len(raw))
(ROOT/'combat_flow.hex').write_text('\n'.join(code[i:i+32].hex() for i in range(0,len(code),32))+'\n',encoding='utf-8')
print('SHA256',hashlib.sha256(code).hexdigest())
