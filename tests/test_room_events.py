import struct
import unittest

import mod
from tools import room_events as ev, room_objects as obj


class EventFramingTests(unittest.TestCase):
    SOURCE = bytes.fromhex('080003150d0d000000002900000000000001000100010201')

    def test_omission_keeps_other_operands_and_zero_command_group(self):
        parsed = ev.Events.parse(self.SOURCE, 1)
        self.assertEqual(parsed.to_bytes(), self.SOURCE)
        self.assertEqual(parsed.omit_commands(0), self.SOURCE)
        result = ev.Events.parse(parsed.omit_commands(0,(1,2)),1)
        self.assertEqual(result.groups[0].commands,(parsed.groups[0].commands[0],))
        self.assertEqual(result.to_bytes(),bytes.fromhex('040001150000290000000000'))
        self.assertEqual(parsed.omit_commands(0,(0,1,2)),bytes.fromhex('04000000'))

    def test_native_nonzero_padding_survives(self):
        raw=bytes.fromhex('080003150d0dabcd') + self.SOURCE[8:]
        parsed=ev.Events.parse(raw,1)
        self.assertEqual(parsed.to_bytes(),raw)
        self.assertEqual(ev.Events.parse(parsed.omit_commands(0,(2,)),1).padding,b'\xab\xcd\0')

    def test_rejects_bad_bounds_and_unknown_width(self):
        for raw in (self.SOURCE[:-1], b'\x04\0\x01\xff',b'\x08\0\x01\x1b\0\x01\0\0'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError): ev.Events.parse(raw,1)
        with self.assertRaises(ValueError): ev.Events.parse(b'\0',0)
        with self.assertRaises(ValueError): ev.Events.parse(b'',True)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private ROM not present')
class NativeEventRoundtripTests(unittest.TestCase):
    def test_all_room_event_sections_roundtrip_and_width_table_matches(self):
        rom,glob,manifest=mod.load_clean()
        at,_,_,size=struct.unpack_from('<4I',rom,0x20)
        arm9=rom[at:at+size]
        self.assertEqual(tuple(arm9[0x119ccc:0x119ccc+39]),ev.OPERAND_WIDTHS)
        totals=[0,0,0,0]
        for entry in manifest['entries']:
            if not entry['name'].endswith('_app.obj'): continue
            totals[0]+=1
            room=obj.RoomObjects.parse(glob[entry['offset']:entry['offset']+entry['size']])
            for record,names in zip(room.records,room.names):
                parsed=ev.Events.parse(record.sections[1],record.raw[3])
                self.assertEqual(parsed.to_bytes(),record.sections[1])
                self.assertEqual(len(parsed.groups),names.category_ends[1]-names.category_ends[0])
                totals[1]+=1;totals[2]+=len(parsed.groups)
                totals[3]+=sum(len(g.commands) for g in parsed.groups)
        self.assertEqual(totals,[75,156,1424,2830])


if __name__=='__main__': unittest.main()
