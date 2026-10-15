"""Execute the router's ARM loads/compares/branches against guarded memory."""
import struct,unittest
import mod
from tools import roof_waves as rw,midnight_chapter as ch

class RoofWaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom,_,_=mod.load_clean();at,_,_,size=struct.unpack_from('<4I',rom,0x20)
        cls.arm9=rom[at:at+size]

    def route(self,room,hp,vtable=rw.NORMAL,stats=0x02210000):
        at=ch.ML_BASE+ch.ML_SPACE-0x180;code,patch=rw.adapter(self.arm9,at)
        memory={at+i:struct.unpack_from('<I',code,i)[0] for i in range(0,len(code),4)}
        actor=0x02220000;memory.update({rw.STATS:stats,stats:room,actor:vtable,actor+0x44:hp&0xffffffff})
        regs=[actor+4,actor]+[0]*13+[at];z=n=v=False
        for _ in range(30):
            pc=regs[15]
            if pc in (rw.LIVE,rw.DEAD):return pc,regs[0]
            word=memory[pc];cond=word>>28
            execute={0:z,1:not z,13:z or n!=v,14:True}[cond]
            regs[15]=pc+4
            if not execute:continue
            if word>>25&7==5:
                off=word&0xffffff
                if off&0x800000:off-=1<<24
                regs[15]=pc+8+off*4
            elif word&0x0ff00000==0x05900000:
                base=(word>>16)&15;dest=(word>>12)&15
                address=(pc+8 if base==15 else regs[base])+(word&0xfff)
                regs[dest]=memory[address]
            elif word&0x0df00000==0x01500000:
                left=regs[(word>>16)&15];right=word&255 if word>>25&1 else regs[word&15]
                result=(left-right)&0xffffffff;z=result==0;n=bool(result>>31)
                v=bool((left^right)&(left^result)&0x80000000)
            else:self.fail(f'Unsupported router instruction {word:08x}')
        self.fail('Router did not return to native code')

    def test_only_defeated_roof_normal_enemies_release_their_cost(self):
        for room,hp,vt,stats,target in ((93,0,rw.NORMAL,0x02210000,rw.DEAD),
            (93,-1,rw.NORMAL,0x02210000,rw.DEAD),(93,1,rw.NORMAL,0x02210000,rw.LIVE),
            (94,0,rw.NORMAL,0x02210000,rw.LIVE),(93,0,0x0212F7A0,0x02210000,rw.LIVE),
            (93,0,rw.NORMAL,0,rw.LIVE)):
            with self.subTest(room=room,hp=hp,vt=vt,stats=stats):
                endpoint,arg=self.route(room,hp,vt,stats)
                self.assertEqual(endpoint,target);self.assertEqual(arg,0x02220004)

    def test_hook_keeps_null_weak_references_on_the_original_path(self):
        code,patch=rw.adapter(self.arm9,ch.ML_BASE+ch.ML_SPACE-0x180)
        self.assertEqual(len(code),72)
        self.assertEqual(patch[:2],(rw.SITE,rw.OLD))
        self.assertEqual(patch[2]>>28,1)
        altered=bytearray(self.arm9);struct.pack_into('<I',altered,rw.SITE-rw.BASE,0)
        with self.assertRaises(ValueError):rw.adapter(altered,ch.ML_BASE)

if __name__=='__main__':unittest.main()
