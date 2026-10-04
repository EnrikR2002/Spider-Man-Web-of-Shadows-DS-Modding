"""Guarded, project-authored CS5E ARM9 extension and Rebound juggle revision.

No game resources are included. Own ARM instructions are stored as text hex so
normal builds need no assembler. Reassembly sources live beside this module.
"""
from pathlib import Path
import hashlib
import struct
from tools import wos_tool as w

BASE = 0x02000000
TARGET = 0x0214F420
RESERVE = 0x4000
CODE_SHA256 = '4cfb1099ca1dd86dfc28d87ecce51fed6a9d7495775eb5a7b8dd146d18d1426d'
ARM9_SHA256 = '0cb23de19e5541393bbbe161b98c5104fc06570ba3c149c0f36ec4b2712903cb'
INPUT_ARM9_SHA256 = '6e563225538658c6c8437ede1886037132adc5ed865693727ef60457072529bf'
HOOKS = {0xE7D48:(0,0xE92D4038), 0xE8F30:(0x1000,0xE8BD8038),
         0xE8F38:(0x1100,0xE92D4010), 0xE8F90:(0x1200,0xE92D4010),
         0x5F3F0:(0x1300,0xE92D000F), 0x492A8:(0x1500,0xE92D000F)}
IMPULSES = (0x11A2B8,0x11AA98)
STATE = TARGET+0x3000


def code_bytes():
    code = bytes.fromhex(Path(__file__).with_suffix('.hex').read_text(encoding='utf-8'))
    if len(code) != 0x3400 or hashlib.sha256(code).hexdigest() != CODE_SHA256:
        raise ValueError('Combat feedback extension differs from validated source')
    return code


def branch(source, target):
    displacement = target-source-8
    if displacement % 4 or not -(1<<25) <= displacement < (1<<25):
        raise ValueError('ARM branch target outside aligned range')
    return 0xEA000000 | ((displacement//4) & 0xFFFFFF)


def extend_arm9(rom, raw, code):
    """Add a third SDK autoload entry; relocate later file offsets, never RAM.

    Original ITCM/DTCM copies/table, main BSS bounds and startup stay intact.
    Source is in main BSS, copied before main BSS clearing. Destination begins
    immediately after BSS; the main arena lower bound moves past our reservation.
    """
    h = w.parse_header(rom)
    if (h['arm9_offset'] != 0x4000 or len(raw) != 0x1439B8 or
            h['arm7_offset'] != 0x147A00 or
            struct.unpack_from('<5I',raw,0xB64) !=
            (0x21439A0,0x21439B8,0x213E140,0x213E140,TARGET) or
            struct.unpack_from('<I',raw,0xFF374)[0] != TARGET):
        raise ValueError('Unsupported SDK autoload/BSS/arena layout')
    if (not code or len(code)%4 or len(code)>RESERVE or
            BASE+0x1439A0+len(code)+36 > TARGET or
            any(rom[0x50:0x60])):
        raise ValueError('Unsafe extension size or unsupported overlay layout')
    table = 0x1439A0+len(code)
    new = bytearray(raw[:0x1439A0]+code+raw[0x1439A0:]+
                    struct.pack('<3I',TARGET,len(code),0))
    struct.pack_into('<2I',new,0xB64,BASE+table,BASE+table+36)
    struct.pack_into('<I',new,0xFF374,TARGET+RESERVE)
    boundary = h['arm7_offset']
    delta = w.align_up(h['arm9_offset']+len(new))-boundary
    if (delta<0 or h['used_rom_size']+delta>len(rom) or
            (delta and any(x not in (0,255) for x in rom[-delta:]))):
        raise ValueError('Insufficient verified ROM padding for extension')
    out = bytearray(rom[:boundary]+bytes(delta)+rom[boundary:len(rom)-delta])
    out[h['arm9_offset']:h['arm9_offset']+len(new)] = new
    for field in (0x30,0x40,0x48,0x68):
        offset = struct.unpack_from('<I',rom,field)[0]
        if offset<boundary: raise ValueError('Unsupported header file offset')
        struct.pack_into('<I',out,field,offset+delta)
    for index in range(h['fat_size']//8):
        start,end = struct.unpack_from('<2I',rom,h['fat_offset']+index*8)
        if start<boundary: raise ValueError('Unsupported NitroFS placement')
        struct.pack_into('<2I',out,h['fat_offset']+delta+index*8,start+delta,end+delta)
    struct.pack_into('<I',out,0x2C,len(new))
    struct.pack_into('<I',out,0x80,h['used_rom_size']+delta)
    struct.pack_into('<H',out,0x15E,w.crc16(out[:0x15E]))
    result = bytes(out)
    w.validate_rom(result,target=True)
    return result,delta


def apply_rom(rom):
    h = w.parse_header(rom); start = h['arm9_offset']
    raw = rom[start:start+h['arm9_size']]
    if hashlib.sha256(raw).hexdigest() != INPUT_ARM9_SHA256:
        raise ValueError('Feedback requires the exact accepted Web Vault ARM9')
    changed = bytearray(raw); log = []
    for at in IMPULSES:
        if struct.unpack_from('<2i',raw,at) != (-4506,6554):
            raise ValueError('Accepted Rebound response differs')
        struct.pack_into('<2i',changed,at,-2253,11469)
        log.append({'arm9_offset':at,'field':'rebound_horizontal_vertical_q12',
                    'old':[-4506,6554],'new':[-2253,11469]})
    for at,(offset,original) in HOOKS.items():
        if struct.unpack_from('<I',raw,at)[0] != original:
            raise ValueError('Native feedback hook instruction differs')
        word = branch(BASE+at,TARGET+offset)
        struct.pack_into('<I',changed,at,word)
        log.append({'arm9_offset':at,'field':'combat_feedback_hook',
                    'original_word':original,'new_word':word,'target':TARGET+offset})
    result,delta = extend_arm9(rom,bytes(changed),code_bytes())
    new_size = struct.unpack_from('<I',result,0x2C)[0]
    if hashlib.sha256(result[start:start+new_size]).hexdigest() != ARM9_SHA256:
        raise ValueError('Unexpected feedback ARM9 result')
    log.append({'field':'sdk_autoload_extension','ram_address':TARGET,
                'heap_reservation':RESERVE,'rom_relocation_bytes':delta,
                'own_code_sha256':CODE_SHA256})
    return result,log


def sample(ram):
    """Read our bounded telemetry for isolated validation, never edit game RAM."""
    if len(ram) != 4*1024*1024: raise ValueError('Expected 4 MiB main RAM')
    at = STATE-BASE
    text,initialized,hud,tick = struct.unpack_from('<4I',ram,at)
    count = struct.unpack_from('<I',ram,at+0x100)[0]
    events=[]
    for index in range(max(0,count-16),count):
        values=struct.unpack_from('<8I',ram,at+0x120+(index%16)*32)
        events.append(dict(zip(('actor','loss_q12','old_hp_q12','tick','caller',
                                'taken','requested_q12','new_hp_q12'),values)))
    return {'text_hud':text,'font_initialized':initialized,'combo_hud':hud,
            'tick':tick,'event_count':count,'events':events}
