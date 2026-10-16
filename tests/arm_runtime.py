"""Small ARM instruction probe for scoped adapters; rejects unmodelled words."""
import struct

class ArmProbe:
    def __init__(self):self.memory={}
    def put(self,at,value):self.memory.update({at+i:b for i,b in enumerate(struct.pack('<I',value&0xFFFFFFFF))})
    def get(self,at):return int.from_bytes(bytes(self.memory[at+i] for i in range(4)),'little')
    def code(self,at,raw):self.memory.update({at+i:b for i,b in enumerate(raw)})
    def run(self,regs,cpsr,stops,stubs=None):
        regs=list(regs);stubs=stubs or {}
        for _ in range(600):
            pc=regs[15]
            if pc in stops:return regs,cpsr,pc
            if pc in stubs:
                cpsr=stubs[pc](self,regs,cpsr);regs[15]=regs[14];continue
            word=self.get(pc);regs[15]=pc+4;cond=word>>28;z=bool(cpsr>>30&1);c=bool(cpsr>>29&1)
            n=bool(cpsr>>31&1);v=bool(cpsr>>28&1)
            if not {0:z,1:not z,2:c,3:not c,8:c and not z,9:not c or z,11:n!=v,14:True}[cond]:continue
            if word&0xFFFF0FFF==0xE10F0000:regs[word>>12&15]=cpsr
            elif word&0xFFFFFFF0==0xE128F000:cpsr=(cpsr&0x00FFFFFF)|(regs[word&15]&0xFF000000)
            elif word==0xE12FFF1E:regs[15]=regs[14]
            elif word&0x0E000000==0x0A000000:
                delta=word&0xFFFFFF
                if delta&0x800000:delta-=1<<24
                if word&0x01000000:regs[14]=pc+4
                regs[15]=pc+8+delta*4
            elif word&0xFFFF0000 in (0xE92D0000,0xE8BD0000):
                indexes=[i for i in range(16) if word>>i&1]
                if word>>16==0xE92D:
                    regs[13]-=4*len(indexes)
                    for i,r in enumerate(indexes):self.put(regs[13]+4*i,regs[r])
                else:
                    values=[self.get(regs[13]+4*i) for i in range(len(indexes))];regs[13]+=4*len(indexes)
                    for r,value in zip(indexes,values):regs[r]=value
            elif word&0x0FF00000 in (0x03500000,0x01500000):
                a=regs[word>>16&15];b=word&255 if word&0x02000000 else regs[word&15]
                v=(a-b)&0xFFFFFFFF;overflow=bool((a^b)&(a^v)&0x80000000)
                cpsr=(cpsr&0x0FFFFFFF)|(v&0x80000000)|(0x40000000 if not v else 0)|(0x20000000 if a>=b else 0)|(0x10000000 if overflow else 0)
            elif word&0x0FF00000==0x03100000:
                v=regs[word>>16&15]&(word&255)
                cpsr=(cpsr&0x3FFFFFFF)|(v&0x80000000)|(0x40000000 if not v else 0)
            elif word&0x0FE00000==0x03A00000:regs[word>>12&15]=word&255
            elif word&0x0FE00000==0x01A00000:regs[word>>12&15]=regs[word&15]
            elif word&0x0FE00000==0x02800000:regs[word>>12&15]=(regs[word>>16&15]+(word&255))&0xFFFFFFFF
            elif word&0x0FE00000==0x02400000:regs[word>>12&15]=(regs[word>>16&15]-(word&255))&0xFFFFFFFF
            elif word&0x0FE00000==0x00800000:regs[word>>12&15]=(regs[word>>16&15]+regs[word&15])&0xFFFFFFFF
            elif word&0x0FF00000 in (0x05900000,0x05D00000):
                base=word>>16&15;at=(pc+8 if base==15 else regs[base])+(word&0xFFF)
                regs[word>>12&15]=self.memory[at] if word&0x00400000 else self.get(at)
            elif word&0x0FF00000==0x05800000:self.put(regs[word>>16&15]+(word&0xFFF),regs[word>>12&15])
            else:raise AssertionError(f'Unmodelled adapter instruction {word:08x} at {pc:08x}')
        raise AssertionError('Adapter did not return')
