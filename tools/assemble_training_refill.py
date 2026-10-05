"""Optional Keystone reassembly; normal builds use pinned own-code hex."""
from pathlib import Path
import hashlib
from keystone import Ks,KS_ARCH_ARM,KS_MODE_ARM
root=Path(__file__).resolve().parent
raw=bytes(Ks(KS_ARCH_ARM,KS_MODE_ARM).asm((root/'training_refill.s').read_text(),0x02151920)[0])
if len(raw)>0x180:raise ValueError('Observer crosses its reserved code boundary')
raw=raw+bytes(0x180-len(raw))
(root/'training_refill.hex').write_text('\n'.join(raw[i:i+32].hex() for i in range(0,len(raw),32))+'\n',encoding='utf-8')
print(len(raw),hashlib.sha256(raw).hexdigest())
