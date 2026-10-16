"""Sound append integrity, preserved opaque bytes and private-room remapping."""
import struct,unittest
import mod
from tools import sdat,crane_audio as a,wos_tool as w
from tests.arm_runtime import ArmProbe

class AudioAdapterTests(unittest.TestCase):
    def test_spore_cues_require_private_config_controller_room_and_selected_entry(self):
        at=0x0215A000;stats=0x02201000;controller=0x02210000;config=0x02159A00
        raw=a.spore_adapter(at,config)
        for room in (38,95,96,100,107,108):
            for state in (0,1,15,16,17,28,29,37,49,52,53):
                for private in (True,False):
                    p=ArmProbe();p.code(at,raw);p.put(0x02145C5C,stats);p.put(stats,room)
                    p.put(controller,0x02133368);p.put(controller+0x48,config if private else config+84)
                    regs=[controller,state,2,3,4,5,6,7,8,9,10,11,12,0x023FF000,0x03000000,at];calls=[]
                    def construct(p,r,flags):p.put(r[0],0x02230000);return 0x0800001F
                    def play(p,r,flags):calls.append((r[1],r[2],r[3],p.get(r[13])));return 0x0800001F
                    def destroy(p,r,flags):return 0x0800001F
                    got,flags,pc=p.run(regs,0xF800001F,{a.STATE_SITE+4},{0x0203D564:construct,a.SITE:play,0x0203D580:destroy})
                    sound={15:588,16:588,28:590,29:590,53:589}.get(state) if private and 96<=room<108 else None
                    self.assertEqual(calls,[(sound,20,0,0)] if sound else [])
                    self.assertEqual(got[:13],regs[:13]);self.assertEqual(got[14],regs[14]);self.assertEqual(flags,0xF800001F)
                    self.assertEqual(got[13],regs[13]-16)

    def test_mapping_changes_only_the_three_families_inside_crane_and_preserves_flags(self):
        at=0x0215A000;stats=0x02201000;raw=a.adapter(at)
        for room in (0,38,70,95,96,100,107,108):
            for sound in (0,305,306,310,311,328,329,456,457,479,480,501,502,581,582):
                p=ArmProbe();p.code(at,raw);p.put(0x02145C5C,stats);p.put(stats,room)
                regs=[0x02200000,sound,20,0,4,5,6,7,8,9,10,11,12,0x023FF000,0x03000000,at]
                got,flags,pc=p.run(regs,0xF800001F,{a.SITE+4})
                slot=next((a.FIRST+i for i,(lo,hi) in enumerate(a.RANGES) if lo<=sound<=hi),sound) if 96<=room<108 else sound
                self.assertEqual(got[1],slot);self.assertEqual(got[0],regs[0]);self.assertEqual(got[2:13],regs[2:13])
                self.assertEqual(got[14],regs[14]);self.assertEqual(got[13],regs[13]-20);self.assertEqual(flags,0xF800001F)

    def test_synthesized_voices_are_deterministic_distinct_non_looping_and_bounded(self):
        voices=[a.voice(k,c) for k in a.KINDS for c in a.CATEGORIES]
        self.assertEqual(len(set(voices)),15)
        for raw,(kind,category) in zip(voices,((k,c) for k in a.KINDS for c in a.CATEGORIES)):
            self.assertEqual(raw,a.voice(kind,category));self.assertEqual(raw[:2],b'\0\0')
            self.assertEqual(w.u16(raw,2),11025);self.assertEqual(w.u32(raw,8)*4,len(raw)-12)
            self.assertLess(len(raw),8000);self.assertGreater(len(set(raw[12:])),40)

@unittest.skipUnless(mod.DEFAULT_ROM.exists(),'Private original missing')
class SoundArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom,_,_=mod.load_clean();e=next(e for e in w.validate_rom(rom,target=True)['nitrofs'] if e['name']=='sound_data.sdat')
        cls.raw=rom[e['start']:e['end']];cls.archive=sdat.Sdat.parse(cls.raw)

    def test_lossless_noop_and_unchanged_native_files(self):
        old=self.archive;self.assertEqual(old.to_bytes(),self.raw);self.assertEqual(old.replace({}),self.raw)
        self.assertEqual(old.replace({22:old.blob(22)}),self.raw)
        result,meta=a.apply(self.raw);new=sdat.Sdat.parse(result)
        changed={old.file_id(1,0),old.file_id(2,20),old.file_id(3,0)}
        for i in range(len(old.entries)):
            if i not in changed:self.assertEqual(new.blob(i),old.blob(i),i)
        self.assertEqual(new.raw[16:0x2C],old.raw[16:0x2C])
        self.assertEqual(new.raw[0x30:old.fat],old.raw[0x30:old.fat])
        self.assertLess(len(result)-len(self.raw),70000);self.assertEqual(meta['count'],15)
        self.assertEqual(a.apply(self.raw)[0],result)

    def test_existing_wave_instrument_and_sequence_data_is_preserved_verbatim(self):
        old=self.archive;new=sdat.Sdat.parse(a.apply(self.raw)[0]);delta=15*4
        for table,index,instrument in ((3,0,False),(2,20,True)):
            before=old.blob(old.file_id(table,index));after=new.blob(new.file_id(table,index))
            count=w.u32(before,0x38);end=0x3C+count*4
            self.assertEqual(w.u32(after,0x38),count+15)
            self.assertEqual(after[end+delta:end+delta+w.u32(before,8)-end],before[end:w.u32(before,8)])
            for i in range(count):
                off=0x3C+i*4
                if instrument:
                    self.assertEqual(after[off],before[off]);self.assertEqual(w.u16(after,off+1),w.u16(before,off+1)+delta)
                else:self.assertEqual(w.u32(after,off),w.u32(before,off)+delta)
        before=old.blob(old.file_id(1,0));after=new.blob(new.file_id(1,0));n=w.u32(before,0x1C)
        self.assertEqual(after[0x20:0x20+n*12],before[0x20:0x20+n*12])
        start=w.u32(after,0x18);old_start=w.u32(before,0x18)
        self.assertEqual(after[start:start+w.u32(before,8)-old_start],before[old_start:w.u32(before,8)])

    def test_invalid_sound_framing_is_rejected(self):
        for raw in (b'',b'SDAT'+bytes(64),self.raw[:-1]):
            with self.assertRaises(ValueError):sdat.Sdat.parse(raw)

if __name__=='__main__':unittest.main()
