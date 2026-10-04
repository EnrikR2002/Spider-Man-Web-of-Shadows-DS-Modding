import unittest
import mod
from tools.custom_formats import Xbd, Gab
from tools.tasm_suit import opening_kick


class GabRecordsTests(unittest.TestCase):
    def test_observed_records_and_padding_roundtrip(self):
        import struct
        for records in ((), ((1, 1, 5),), ((1, 9, 2), (2, 1, 5))):
            raw = b''.join(struct.pack('<HHH', *r) for r in records) + b'\xff'*6
            raw += bytes(-len(raw) % 4)
            parsed = Gab.parse(raw)
            self.assertEqual(parsed.to_bytes(), raw)
            self.assertEqual(parsed.records, records)
        with self.assertRaisesRegex(ValueError, 'three-u16'):
            Gab.parse(b'\x01\x00' + b'\xff'*6)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class LocalTasmTests(unittest.TestCase):
    def test_exact_three_bindings_changed_and_other_bytes_retained(self):
        _, glob, manifest = mod.load_clean()
        names = [e['name'] for e in manifest['entries']]
        entry = next(e for e in manifest['entries'] if e['name'] == 'spd.xbd')
        raw = glob[entry['offset']:entry['offset']+entry['size']]
        changed, report = opening_kick(raw, names)
        before, after = Xbd.parse(raw, names), Xbd.parse(changed, names)
        allowed = {offset for r in report for offset in (r['offset'], r['offset']+1)}
        self.assertEqual(len(report), 3)
        self.assertEqual(len(changed), len(raw))
        self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(raw, changed)) if i not in allowed))
        self.assertEqual(changed[0x4f0:], raw[0x4f0:])
        for a, b in zip(before.bindings, after.bindings):
            if a['offset'] not in allowed: self.assertEqual(a, b)
        self.assertEqual([r['new_name'] for r in report],
                         ['spd_GroundAttack15.sca', 'spd_GroundAttack15.gmb', 'spd_GroundAttack15.gab'])
        self.assertEqual(opening_kick(raw, names), (changed, report))
        with self.assertRaises(ValueError): opening_kick(changed, names)
