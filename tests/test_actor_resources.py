"""Resource-sheet appends preserve all existing records and unknown bytes."""
import struct,unittest
import mod
from tools.actor_resources import ModelSheet

class ResourceSheetTests(unittest.TestCase):
    def fixture(self):
        raw=bytearray(struct.pack('<IIhH3H',0x12345678,0,0,1<<4|4,10,20,30)+b'XY'+struct.pack('<I',0x12345678))
        struct.pack_into('<I',raw,4,len(raw)-12)
        return bytes(raw)

    def test_noop_and_append_keep_unknown_tail_prefix_and_old_record(self):
        raw=self.fixture();a=ModelSheet.parse(raw)
        self.assertEqual(a.to_bytes(),raw);self.assertEqual(a.append(()),raw)
        b=ModelSheet.parse(a.append(((40,50,60),(70,80,90))))
        self.assertEqual(b.groups,((10,20,30),(40,50,60),(70,80,90)))
        self.assertTrue(b.tail.startswith(b'XY'));self.assertEqual(b.raw[:4],raw[:4]);self.assertEqual(b.raw[8:10],raw[8:10])
        self.assertEqual(b.to_bytes(),ModelSheet.parse(b.to_bytes()).to_bytes())

    def test_corruption_and_out_of_range_rows_rejected(self):
        raw=self.fixture()
        for data in (raw[:-1],raw[:4]+bytes(4)+raw[8:],raw[:-4]+bytes(4)):
            with self.assertRaises(ValueError):ModelSheet.parse(data)
        for rows in (((1,2),),((1,-1,3),),((True,2,3),),((1,2,65536),)):
            with self.assertRaises(ValueError):ModelSheet.parse(raw).append(rows)

    def test_clean_native_sheet_roundtrip_and_append_preserve_every_native_group(self):
        if not mod.DEFAULT_ROM.exists():self.skipTest('Private original missing')
        _,g,m=mod.load_clean();e=next(e for e in m['entries'] if e['name']=='model_sheet.xbd')
        raw=g[e['offset']:e['offset']+e['size']];a=ModelSheet.parse(raw)
        self.assertEqual(len(a.groups),182);self.assertEqual(a.to_bytes(),raw)
        names=[e['name'] for e in m['entries']]
        self.assertEqual(tuple(names[i] for i in a.groups[24]),('brt.nsbmd','brt.xbd','brt.nsbtx'))
        new=ModelSheet.parse(a.append(((4000,4001,4002),)*3))
        self.assertEqual(new.groups[:182],a.groups)
        self.assertEqual(new.raw[a.start:a.start+182*6],raw[a.start:a.start+182*6])

if __name__=='__main__':unittest.main()
