"""Three appended SCA resources, retaining every existing Glob resource ID.

Only the authored Rush profile enables these fixed names. The ordinary overlay
workflow still forbids user edits to GlobFiles.txt and arbitrary new resources.
"""
import struct
from . import wos_tool as w,training_refill
from .sca import Sca

PROFILE='tasm-oscorp-rush-authored'
EXTRA_NAMES=('zz_tasm_RushBridge.sca','zz_tasm_RushEntry.sca','zz_tasm_RushFinish.sca')
FRAMES=(12,39,20)
COUNT_OFFSET=0x77f8
ORIGINAL_COUNT=3733
ARM9_SHA256='72ab438e0998ec2b021bd79a4f36adf5e88a456ccbe51afff100c81461390b12'

def append_resources(names,blobs,extra):
    """Round-trippable append; no existing ID, filename record or payload moves logically."""
    if not extra:return list(names),list(blobs)
    if len(names)!=len(blobs) or len({n.casefold() for n in names})!=len(names):raise ValueError('Invalid base resource mapping')
    index=names.index('GlobFiles.txt');table=blobs[index]
    if len(table)!=len(names)*64:raise ValueError('Filename table length differs')
    if any(w.safe_name(n)!=n or len(n.encode('ascii'))>63 for n in extra):raise ValueError('Invalid appended resource name')
    if len({n.casefold() for n in [*names,*extra]})!=len(names)+len(extra):raise ValueError('Appended resource name collision')
    out=list(blobs);out[index]=table+b''.join(n.encode('ascii').ljust(63,b' ')+b'\n' for n in extra)
    return [*names,*extra],[*out,*extra.values()]

def validate_extra(overlay):
    for name,count in zip(EXTRA_NAMES,FRAMES):
        if name not in overlay:raise ValueError(f'Authored Rush requires {name}')
        a=Sca.parse(overlay[name])
        if (a.frame_count,a.joint_count)!=(count,37) or a.to_bytes()!=overlay[name]:
            raise ValueError('Unexpected appended Rush animation layout')

def apply_rom(rom):
    start,_,address,size=struct.unpack_from('<4I',rom,0x20);raw=rom[start:start+size]
    if address!=0x02000000 or w.sha256(raw)!=training_refill.ARM9_SHA256 or w.u32(raw,COUNT_OFFSET)!=ORIGINAL_COUNT:
        raise ValueError('Glob expansion requires the exact accepted Rush ARM9')
    result=bytearray(rom);struct.pack_into('<I',result,start+COUNT_OFFSET,ORIGINAL_COUNT+len(EXTRA_NAMES))
    if w.sha256(result[start:start+size])!=ARM9_SHA256:raise ValueError('Unexpected expanded Glob ARM9')
    return bytes(result),[{'arm9_offset':COUNT_OFFSET,'address':0x02000000+COUNT_OFFSET,
                         'field':'Glob_resource_count','old':ORIGINAL_COUNT,'new':ORIGINAL_COUNT+len(EXTRA_NAMES)}]
