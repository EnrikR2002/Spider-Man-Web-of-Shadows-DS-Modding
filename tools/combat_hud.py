"""Guarded compact combo and live enemy HP-bar extension; no game assets."""
from pathlib import Path
import hashlib
import struct
from tools import combat_feedback as f

BASE, TARGET, RESERVE, STATE = f.BASE, f.TARGET, f.RESERVE, f.STATE
CODE_SHA256 = '40cd7401bb0a89c947084a60b7c1f0077839f6ca9ab9721797785d3700d366ac'
ARM9_SHA256 = '4061f7cbcce487b72dc3f06d2f079f2060759eb3147448743e3de5fd3eeed62d'
INPUT_ARM9_SHA256 = f.INPUT_ARM9_SHA256
HOOKS = f.HOOKS | {0x73A68:(0x1700,0xE92D47F0)}
IMPULSES = f.IMPULSES

def code_bytes():
    code = bytes.fromhex(Path(__file__).with_suffix('.hex').read_text(encoding='utf-8'))
    if len(code) != 0x3600 or hashlib.sha256(code).hexdigest() != CODE_SHA256:
        raise ValueError('Compact HUD differs from validated project source')
    return code

def apply_rom(rom):
    from tools import wos_tool as w
    h = w.parse_header(rom); start = h['arm9_offset']
    raw = rom[start:start+h['arm9_size']]
    if hashlib.sha256(raw).hexdigest() != INPUT_ARM9_SHA256:
        raise ValueError('Compact HUD requires the exact accepted Web Vault ARM9')
    changed = bytearray(raw); log=[]
    for at in IMPULSES:
        if struct.unpack_from('<2i',raw,at) != (-4506,6554):
            raise ValueError('Accepted Rebound response differs')
        struct.pack_into('<2i',changed,at,-2253,11469)
        log.append({'arm9_offset':at,'field':'rebound_horizontal_vertical_q12',
                    'old':[-4506,6554],'new':[-2253,11469]})
    for at,(offset,original) in HOOKS.items():
        if struct.unpack_from('<I',raw,at)[0] != original:
            raise ValueError('Native compact HUD hook instruction differs')
        word=f.branch(BASE+at,TARGET+offset)
        struct.pack_into('<I',changed,at,word)
        log.append({'arm9_offset':at,'field':'compact_hud_hook','old':original,'new':word})
    result,delta=f.extend_arm9(rom,bytes(changed),code_bytes())
    final=w.parse_header(result)
    digest=w.sha256(result[start:start+final['arm9_size']])
    if digest != ARM9_SHA256: raise ValueError(f'Unexpected compact HUD ARM9: {digest}')
    log.append({'field':'sdk_autoload_extension','code_sha256':CODE_SHA256,
                'destination':TARGET,'size':0x3600,'reserved_heap_bytes':RESERVE,
                'file_relocation_delta':delta})
    return result,log

def sample(ram):
    data=f.sample(ram)
    at=STATE-BASE
    data['enemy_bars']=[]
    for i in range(8):
        row=struct.unpack_from('<4I4i',ram,at+0x400+i*32)
        if row[0]:
            data['enemy_bars'].append(dict(zip(('actor','tick','hp_q12','max_hp_q12',
                        'x_q12','y_q12','z_q12','half_height_q12'),row)))
    return data
