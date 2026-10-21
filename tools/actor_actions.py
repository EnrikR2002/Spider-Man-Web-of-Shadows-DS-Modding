"""Read-only actor action rows, grounded in native lookup0x02001F44/0x0200211C.

Six-byte rows name an action byte and a relative vector of existing XBD
resource bindings. Unknown flag bits are preserved. No action IDs are inferred
from a filename's ordinal or from another actor's action set.
"""
from dataclasses import dataclass
import struct
from tools import wos_tool as w
from tools.custom_formats import Xbd

@dataclass(frozen=True)
class Action:
    action:int
    flags:int
    offset:int
    bindings:tuple

@dataclass(frozen=True)
class ActorActions:
    raw:bytes
    actions:tuple

    @classmethod
    def parse(cls,raw,names):
        xbd=Xbd.parse(raw,names);raw=xbd.raw;packed=w.u16(raw,10)
        first=8+(struct.unpack_from('<h',raw,8)[0]<<4)+(packed&15);count=packed>>4
        w.check_range(raw,first,count*6,'Actor action rows');by_offset={b['offset']:b for b in xbd.bindings};rows=[]
        for i in range(count):
            at=first+i*6;word=w.u16(raw,at+2)
            vector=at+(struct.unpack_from('<h',raw,at)[0]<<4)+(word&15);items=[]
            w.check_range(raw,vector,(word>>4)*4,'Actor action vector')
            for p in range(vector,vector+(word>>4)*4,4):
                if p not in by_offset:raise ValueError('Action vector is not an existing XBD resource binding')
                items.append(by_offset[p])
            if not any(b['tag']==0 for b in items):raise ValueError('Action has no SCA')
            rows.append(Action(raw[at+5],raw[at+4],at,tuple(items)))
        if tuple(x.action for x in rows)!=tuple(sorted({x.action for x in rows})):raise ValueError('Actor actions must be unique and sorted')
        return cls(raw,tuple(rows))

    def to_bytes(self):return self.raw
    def lookup(self,action):return next((r for r in self.actions if r.action==action),None)
