"""Lossless model_sheet.xbd resource-group framing and append-only extension.

Each group holds native NSBMD/XBD/NSBTX resource IDs. Numeric kind, prefix and
opaque trailing bytes are retained. This is not the actor action-XBD format.
"""
from dataclasses import dataclass
import struct
from tools import wos_tool as w

@dataclass(frozen=True)
class ModelSheet:
    raw:bytes
    start:int
    groups:tuple
    tail:bytes

    @classmethod
    def parse(cls,raw):
        raw=bytes(raw)
        if len(raw)<16 or len(raw)%4 or raw[:4]!=raw[-4:] or w.u32(raw,4)!=len(raw)-12:
            raise ValueError('Invalid resource-sheet envelope')
        offset,packed=struct.unpack_from('<hH',raw,8)
        start=8+(offset<<4)+(packed&15);count=packed>>4;end=start+count*6
        if start<12 or start%2 or end>len(raw)-4:raise ValueError('Invalid resource-group bounds')
        groups=tuple(struct.iter_unpack('<3H',raw[start:end]))
        return cls(raw,start,groups,raw[end:-4])

    def to_bytes(self):return self.raw

    def append(self,groups):
        groups=tuple(tuple(row) for row in groups)
        if not groups:return self.raw
        if len(self.groups)+len(groups)>4095:raise ValueError('Resource-group count exceeds12 bits')
        if any(len(row)!=3 or any(type(x) is not int or not 0<=x<=65535 for x in row) for row in groups):
            raise ValueError('Expected three unsigned16-bit resource IDs per group')
        end=self.start+len(self.groups)*6
        body=self.raw[:end]+b''.join(struct.pack('<3H',*row) for row in groups)+self.tail
        body+=bytes((-len(body)-4)%4)
        result=bytearray(body+self.raw[-4:])
        struct.pack_into('<I',result,4,len(result)-12)
        packed=w.u16(self.raw,10)
        struct.pack_into('<H',result,10,((len(self.groups)+len(groups))<<4)|(packed&15))
        parsed=self.parse(result)
        if parsed.groups!=self.groups+groups or not parsed.tail.startswith(self.tail):
            raise ValueError('Resource-sheet extension changed existing groups/tail')
        return bytes(result)
