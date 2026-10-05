"""Read-only canonical NSBMD object order and verified SBC ancestry.

The DCC export's compact joint ordinals are not SCA indices. Unknown model data
and node flag bytes are retained, not interpreted. No model/skeleton editor.
"""
from dataclasses import dataclass
import struct
from . import wos_tool as w
from .nitro_texture import dictionary

LENGTHS = {0:0, 1:0, 2:2, 3:1, 4:1, 5:1, 6:3, 7:1, 8:1,
           0x0b:0, 0x0c:2, 0x0d:2, 0x24:1, 0x26:4, 0x2b:0,
           0x40:0, 0x44:1, 0x46:4, 0x47:2, 0x66:5, 0x80:0}


def node_ancestry(stream, count):
    """Require explicit NODE parent bytes to agree with matrix-stack lineage."""
    position, current, stack, parents, records = 0, (), {}, {}, []
    while position < len(stream):
        start=position; op=stream[position]; position+=1
        if op==9:
            w.check_range(stream,position,2,'SBC skin header')
            length=2+3*stream[position+1]
        elif op in LENGTHS:length=LENGTHS[op]
        else:raise ValueError(f'Unsupported SBC opcode {op:02x}')
        w.check_range(stream,position,length,'SBC parameters')
        args=tuple(stream[position:position+length]); position+=length
        records.append((start,op,args))
        if op==1:break
        if op==3:
            if args[0] not in stack:raise ValueError('SBC loads an unknown matrix stack slot')
            current=stack[args[0]]
        elif op in (6,0x26,0x46,0x66):
            joint,parent,unknown=args[:3]
            if joint>=count or parent>=count or joint in parents:
                raise ValueError('Invalid/duplicate SBC node index')
            if op in (0x46,0x66):
                slot=args[3 if op==0x46 else 4]
                if slot not in stack:raise ValueError('NODE loads an unknown matrix stack slot')
                current=stack[slot]
            if current is None:raise ValueError('Cannot infer a parent after a skin matrix')
            actual=current[-1] if current else None
            if (actual is not None and parent!=actual) or (actual is None and parent!=joint):
                raise ValueError('NODE parent disagrees with matrix-stack ancestry')
            if joint in current:raise ValueError('Cyclic SBC ancestry')
            parents[joint]=actual; current=(*current,joint)
            if op in (0x26,0x66):stack[args[3]]=current
        elif op==9:
            # A weighted skin matrix is not a single bone's parent transform.
            current=None; stack[args[0]]=None
    else:raise ValueError('SBC lacks its END opcode')
    if set(parents)!=set(range(count)):raise ValueError('SBC does not establish every object parent')
    return tuple(parents[i] for i in range(count)),tuple(records),position


@dataclass(frozen=True)
class AnimationRig:
    raw: bytes
    names: tuple[str,...]
    parents: tuple[int|None,...]
    object_offsets: tuple[int,...]
    node_records: tuple
    sbc_start: int
    sbc_end: int

    @classmethod
    def parse(cls,raw):
        raw=bytes(raw);w.check_range(raw,0,20,'NSBMD header')
        if raw[:4]!=b'BMD0' or w.u32(raw,8)!=len(raw):raise ValueError('Invalid NSBMD header')
        block=w.u32(raw,16);w.check_range(raw,block,8,'MDL0 block')
        if raw[block:block+4]!=b'MDL0':raise ValueError('First block is not MDL0')
        models=dictionary(raw,block+8,4)
        if len(models)!=1:raise ValueError('Rig extraction requires one model')
        model=block+w.u32(models[0][1],0);w.check_range(raw,model,64,'Model prefix')
        size=w.u32(raw,model);w.check_range(raw,model,size,'Model section')
        objects=model+64;rows=dictionary(raw,objects,4)
        if len(rows)!=raw[model+23]:raise ValueError('Model object count mismatch')
        offsets=tuple(objects+w.u32(entry,0) for _,entry in rows)
        if any(not objects<=at<model+size for at in offsets):raise ValueError('Object data outside model')
        start=model+w.u32(raw,model+4);end=model+w.u32(raw,model+8)
        if not model+64<=start<end<=model+size:raise ValueError('SBC section bounds are invalid')
        parents,records,used=node_ancestry(raw[start:end],len(rows))
        return cls(raw,tuple(name for name,_ in rows),parents,offsets,records,start,start+used)

    def to_bytes(self):return self.raw

    def report(self):
        return {'model_sha256':w.sha256(self.raw),'joint_count':len(self.names),
            'joints':[{'joint':i,'name':name,'parent':self.parents[i],
                       'object_offset':self.object_offsets[i]} for i,name in enumerate(self.names)],
            'unknowns':['Node flags and other raw model fields are not assigned semantics.'],
            'sbc_start':self.sbc_start,'sbc_end':self.sbc_end}
