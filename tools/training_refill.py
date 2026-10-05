"""Bounded native training-flag HP refill; no ownership or persistent state."""
from pathlib import Path
import struct
from tools import combat_flow as f,wos_tool as w
OFFSET=f.SOURCE_OFFSET+0x2500
CODE_SHA256='40d275bfffe23d13b31435dbf7f18e4c343fd5796d1f58ec1e0a484febb353c9'
ARM9_SHA256='acab7b96db674e5984de4fb034492f7a898be8641ae4da4bb8054dbad8d4313d'

def code_bytes():
    raw=bytes.fromhex(Path(__file__).with_suffix('.hex').read_text())
    if len(raw)!=0x180 or w.sha256(raw)!=CODE_SHA256:raise ValueError('Training refill code differs from validated source')
    return raw

def apply_rom(rom):
    h=w.parse_header(rom);start=h['arm9_offset'];size=h['arm9_size']
    raw=rom[start:start+size]
    if w.sha256(raw)!=f.ARM9_SHA256:raise ValueError('Training refill requires the accepted combat-flow ARM9')
    out=bytearray(rom);out[start+OFFSET:start+OFFSET+0x180]=code_bytes()
    digest=w.sha256(out[start:start+size])
    if digest!=ARM9_SHA256:raise ValueError(f'Unexpected training-refill ARM9: {digest}')
    return bytes(out),[{'field':'training_select_down_hp_refill','arm9_offset':OFFSET,'size':0x180,'sha256':CODE_SHA256}]
