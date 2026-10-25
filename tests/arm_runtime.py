"""Small ARM instruction probe for scoped adapters; rejects unmodelled words."""
import struct

class ArmProbe:
    def __init__(self):self.memory={}
    def put(self,at,value):self.memory.update({at+i:b for i,b in enumerate(struct.pack('<I',value&0xFFFFFFFF))})
    def get(self,at):return int.from_bytes(bytes(self.memory[at+i] for i in range(4)),'little')
    def code(self,at,raw):self.memory.update({at+i:b for i,b in enumerate(raw)})
    @staticmethod
    def operand(word,regs):
        if word&0x02000000:
            value=word&255;rotate=((word>>8)&15)*2
            return ((value>>rotate)|(value<<(32-rotate)))&0xFFFFFFFF if rotate else value
        value=regs[word&15];kind=(word>>5)&3
        shift=(regs[(word>>8)&15]&255) if word&16 else (word>>7)&31
        if kind==0:return (value<<shift)&0xFFFFFFFF if shift<32 else 0
        if kind==1:return value>>shift if shift else (value if word&16 else 0)
        if kind==2:
            if not shift:shift=0 if word&16 else 32
            signed=value-(1<<32) if value&0x80000000 else value
            return (signed>>shift)&0xFFFFFFFF
        raise AssertionError('Unmodelled rotate operand')
    def run(self,regs,cpsr,stops,stubs=None):
        regs=list(regs);stubs=stubs or {}
        for _ in range(10000):
            pc=regs[15]
            if pc in stops:return regs,cpsr,pc
            if pc in stubs:
                cpsr=stubs[pc](self,regs,cpsr);regs[15]=regs[14];continue
            word=self.get(pc);regs[15]=pc+4;cond=word>>28;z=bool(cpsr>>30&1);c=bool(cpsr>>29&1)
            n=bool(cpsr>>31&1);v=bool(cpsr>>28&1)
            if not {0:z,1:not z,2:c,3:not c,4:n,5:not n,6:v,7:not v,8:c and not z,9:not c or z,10:n==v,11:n!=v,12:not z and n==v,13:z or n!=v,14:True}[cond]:continue
            if word&0xFFFF0FFF==0xE10F0000:regs[word>>12&15]=cpsr
            elif word&0xFFFFFFF0==0xE128F000:cpsr=(cpsr&0x00FFFFFF)|(regs[word&15]&0xFF000000)
            elif word&0x0FC000F0==0x00000090:
                # ARM MUL/MLA, used by the room/Vitality damage multiplier.
                value=regs[word&15]*regs[word>>8&15]
                if word&0x00200000:value+=regs[word>>12&15]
                value&=0xFFFFFFFF;regs[word>>16&15]=value
                if word&0x00100000:cpsr=(cpsr&0x3FFFFFFF)|(value&0x80000000)|(0x40000000 if value==0 else 0)
            elif word==0xE12FFF1E:regs[15]=regs[14]
            elif word&0x0E000000==0x0A000000:
                delta=word&0xFFFFFF
                if delta&0x800000:delta-=1<<24
                if word&0x01000000:regs[14]=pc+4
                regs[15]=pc+8+delta*4
            elif word&0x0FFF0000 in (0x092D0000,0x08BD0000):
                indexes=[i for i in range(16) if word>>i&1]
                if word&0x0FFF0000==0x092D0000:
                    regs[13]-=4*len(indexes)
                    for i,r in enumerate(indexes):self.put(regs[13]+4*i,regs[r])
                else:
                    values=[self.get(regs[13]+4*i) for i in range(len(indexes))];regs[13]+=4*len(indexes)
                    for r,value in zip(indexes,values):regs[r]=value
            elif word&0x0FF00000 in (0x03700000,0x01700000):
                a=regs[word>>16&15];b=self.operand(word,regs);result=a+b;v=result&0xFFFFFFFF
                overflow=bool((~(a^b))&(a^v)&0x80000000)
                cpsr=(cpsr&0x0FFFFFFF)|(v&0x80000000)|(0x40000000 if not v else 0)|(0x20000000 if result>>32 else 0)|(0x10000000 if overflow else 0)
            elif word&0x0FF00000 in (0x03500000,0x01500000):
                a=regs[word>>16&15];b=self.operand(word,regs)
                v=(a-b)&0xFFFFFFFF;overflow=bool((a^b)&(a^v)&0x80000000)
                cpsr=(cpsr&0x0FFFFFFF)|(v&0x80000000)|(0x40000000 if not v else 0)|(0x20000000 if a>=b else 0)|(0x10000000 if overflow else 0)
            elif word&0x0FF00000 in (0x03100000,0x01100000):
                v=regs[word>>16&15]&self.operand(word,regs)
                cpsr=(cpsr&0x3FFFFFFF)|(v&0x80000000)|(0x40000000 if not v else 0)
            elif word&0x0FE00000 in (0x03A00000,0x01A00000):
                value=self.operand(word,regs);regs[word>>12&15]=value
                if word&0x00100000:cpsr=(cpsr&0x3FFFFFFF)|(value&0x80000000)|(0x40000000 if value==0 else 0)
            elif word&0x0FE00000 in (0x03E00000,0x01E00000):regs[word>>12&15]=~self.operand(word,regs)&0xFFFFFFFF
            elif word&0x0FE00000 in (0x02800000,0x00800000):regs[word>>12&15]=((pc+8 if word>>16&15==15 else regs[word>>16&15])+self.operand(word,regs))&0xFFFFFFFF
            elif word&0x0FE00000 in (0x02400000,0x00400000):
                a=regs[word>>16&15];b=self.operand(word,regs);result=(a-b)&0xFFFFFFFF;regs[word>>12&15]=result
                if word&0x00100000:
                    overflow=bool((a^b)&(a^result)&0x80000000)
                    cpsr=(cpsr&0x0FFFFFFF)|(result&0x80000000)|(0x40000000 if not result else 0)|(0x20000000 if a>=b else 0)|(0x10000000 if overflow else 0)
            elif word&0x0FE00000 in (0x02600000,0x00600000):
                a=regs[word>>16&15];b=self.operand(word,regs);result=(b-a)&0xFFFFFFFF;regs[word>>12&15]=result
                if word&0x00100000:
                    overflow=bool((b^a)&(b^result)&0x80000000)
                    cpsr=(cpsr&0x0FFFFFFF)|(result&0x80000000)|(0x40000000 if not result else 0)|(0x20000000 if b>=a else 0)|(0x10000000 if overflow else 0)
            elif word&0x0FE00000 in (0x02000000,0x00000000):regs[word>>12&15]=regs[word>>16&15]&self.operand(word,regs)
            elif word&0x0FE00000 in (0x03800000,0x01800000):regs[word>>12&15]=regs[word>>16&15]|self.operand(word,regs)
            elif word&0x0FE00000 in (0x02200000,0x00200000):regs[word>>12&15]=regs[word>>16&15]^self.operand(word,regs)
            elif word&0x0F000000==0x04000000:
                base=word>>16&15;dest=word>>12&15;at=regs[base];delta=word&0xFFF
                if not word&0x00800000:delta=-delta
                if word&0x00100000:
                    if base==dest:raise AssertionError('Unpredictable post-index load writeback')
                    regs[dest]=self.memory[at] if word&0x00400000 else self.get(at)
                elif word&0x00400000:self.memory[at]=regs[dest]&255
                else:self.put(at,regs[dest])
                regs[base]=(at+delta)&0xFFFFFFFF
            elif word&0x0FF000F0==0x01D000B0:
                base=word>>16&15;at=(pc+8 if base==15 else regs[base])+((word>>4&0xF0)|(word&15))
                regs[word>>12&15]=int.from_bytes(bytes(self.memory[at+i] for i in range(2)),'little')
            elif word&0x0FF00000 in (0x07900000,0x07D00000):
                base=word>>16&15;at=regs[base]+self.operand(word&~0x02000000,regs)
                regs[word>>12&15]=self.memory[at] if word&0x00400000 else self.get(at)
            elif word&0x0FF00000 in (0x05900000,0x05D00000,0x05100000,0x05500000):
                base=word>>16&15;delta=word&0xFFF
                at=(pc+8 if base==15 else regs[base])+(delta if word&0x00800000 else -delta)
                regs[word>>12&15]=self.memory[at] if word&0x00400000 else self.get(at)
            elif word&0x0FF00000==0x05800000:self.put(regs[word>>16&15]+(word&0xFFF),regs[word>>12&15])
            elif word&0x0FF00000==0x05C00000:self.memory[regs[word>>16&15]+(word&0xFFF)]=regs[word>>12&15]&255
            else:raise AssertionError(f'Unmodelled adapter instruction {word:08x} at {pc:08x}')
        raise AssertionError('Adapter did not return')
