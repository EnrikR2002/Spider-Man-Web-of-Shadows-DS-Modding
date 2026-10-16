"""Lossless SDAT framing; extend selected files while retaining opaque bytes.

Unknown headers, symbols, INFO records, original file bytes and padding stay
intact. Only FAT locations/lengths and enclosing size words are rewritten.
"""
from dataclasses import dataclass
import struct
from tools import wos_tool as w

@dataclass(frozen=True)
class Sdat:
    raw:bytes
    fat:int
    file:int
    entries:tuple

    @classmethod
    def parse(cls,raw):
        raw=bytes(raw);w.check_range(raw,0,64,'SDAT header')
        if raw[:4]!=b'SDAT' or w.u32(raw,8)!=len(raw):raise ValueError('Invalid SDAT framing')
        fat,size,file,length=struct.unpack_from('<4I',raw,0x20)
        w.check_range(raw,fat,size,'SDAT FAT');w.check_range(raw,file,length,'SDAT FILE')
        if raw[fat:fat+4]!=b'FAT ' or raw[file:file+4]!=b'FILE' or file+length!=len(raw):raise ValueError('Unsupported SDAT blocks')
        count=w.u32(raw,fat+8)
        if 12+count*16>size:raise ValueError('SDAT FAT count exceeds block')
        entries=tuple(struct.unpack_from('<2I',raw,fat+12+i*16) for i in range(count))
        for at,n in entries:
            if at<file+12 or at+n>len(raw):raise ValueError('SDAT file outside FILE block')
        return cls(raw,fat,file,entries)

    def to_bytes(self):return self.raw

    def file_id(self,table,index):
        info=w.u32(self.raw,0x18);record=info+w.u32(self.raw,info+8+table*4)
        if not 0<=index<w.u32(self.raw,record):raise ValueError('SDAT INFO index outside table')
        entry=info+w.u32(self.raw,record+4+index*4)
        return w.u16(self.raw,entry)

    def blob(self,index):
        at,n=self.entries[index];return self.raw[at:at+n]

    def replace(self,changes):
        changes={i:bytes(raw) for i,raw in changes.items() if bytes(raw)!=self.blob(i)}
        if not changes:return self.raw
        out=bytearray();cursor=0;segments=[]
        for i,raw in sorted(changes.items(),key=lambda item:self.entries[item[0]][0]):
            at,n=self.entries[i]
            if at<cursor:raise ValueError('Overlapping changed SDAT files')
            # Whole32-byte growth preserves all later native file alignments.
            payload=raw+bytes(-(len(raw)-n)%32)
            out.extend(self.raw[cursor:at]);out.extend(payload)
            segments.append((at,n,len(payload)-n,i,len(payload)));cursor=at+n
        out.extend(self.raw[cursor:])
        for i,(at,n) in enumerate(self.entries):
            moved=at+sum(delta for start,size,delta,_,_ in segments if start+size<=at)
            length=next((length for _,_,_,changed,length in segments if changed==i),n)
            struct.pack_into('<2I',out,self.fat+12+i*16,moved,length)
        struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,0x2C,len(out)-self.file)
        struct.pack_into('<I',out,self.file+4,len(out)-self.file)
        return self.parse(out).to_bytes()

def append_indexed(raw,magic,items,*,instrument=False):
    """SWAR/SBNK: append entries while preserving every existing payload byte."""
    if raw[:4]!=magic or not 0<w.u32(raw,8)<=len(raw):raise ValueError('Invalid indexed sound file')
    if not items:return raw
    size=w.u32(raw,8);tail=raw[size:];raw=raw[:size]
    count=w.u32(raw,0x38);end=0x3C+count*4;delta=len(items)*4
    w.check_range(raw,0,end,'Sound index')
    out=bytearray(raw[:end]+bytes(delta)+raw[end:])
    for i in range(count):
        at=0x3C+i*4
        if instrument:
            offset=w.u16(raw,at+1)
            if offset:
                if offset+delta>=65536:raise ValueError('Instrument offset overflow')
                struct.pack_into('<H',out,at+1,offset+delta)
        else:struct.pack_into('<I',out,at,w.u32(raw,at)+delta)
    for i,item in enumerate(items):
        at=len(out)
        if instrument:
            if at>=65536:raise ValueError('Instrument offset overflow')
            struct.pack_into('<BHx',out,end+i*4,1,at)
        else:struct.pack_into('<I',out,end+i*4,at)
        out.extend(item)
    struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,0x14,len(out)-0x10)
    struct.pack_into('<I',out,0x38,count+len(items))
    return bytes(out)+tail

def append_sequences(raw,sequences):
    """SSAR: sequences are (native metadata row index, new event bytes)."""
    if raw[:4]!=b'SSAR' or not 0<w.u32(raw,8)<=len(raw):raise ValueError('Invalid SSAR framing')
    if not sequences:return raw
    size=w.u32(raw,8);tail=raw[size:];raw=raw[:size]
    start,count=struct.unpack_from('<2I',raw,0x18);delta=len(sequences)*12
    if start<0x20+count*12:raise ValueError('SSAR data overlaps metadata')
    headers=[];events=bytearray(raw[start:])
    for template,payload in sequences:
        if not 0<=template<count:raise ValueError('SSAR template outside metadata')
        row=bytearray(raw[0x20+template*12:0x20+(template+1)*12])
        struct.pack_into('<I',row,0,len(events));headers.append(row);events.extend(payload)
    out=bytearray(raw[:0x20+count*12]+b''.join(headers)+raw[0x20+count*12:start]+events)
    struct.pack_into('<I',out,8,len(out));struct.pack_into('<I',out,0x14,len(out)-0x10)
    struct.pack_into('<2I',out,0x18,start+delta,count+len(sequences))
    return bytes(out)+tail
