import struct
import unittest
from pathlib import Path
import mod
from tools import custom_formats as cf
from tools import grip_compression as gc


def pc_bits(bits, size, table=b'ABCD'):
    """Hand-specified tokens, independent of the production bit writer."""
    bits += '00000000' + '100' + '11111111111111'  # EOF
    bits += '0' * (-len(bits) % 32)
    stream = b''.join(int(bits[i:i+32], 2).to_bytes(4, 'little') for i in range(0, len(bits), 32))
    return struct.pack('<I', (size << 8) | 0x60) + bytes([4, 0, 0, 8]) + table + stream


class CodecTests(unittest.TestCase):
    def test_word_order(self):
        reader = gc.Bits(bytes.fromhex('78 56 34 12'))
        self.assertEqual(reader.read(8), 0x12)
        self.assertEqual(reader.read(4), 3); self.assertEqual(reader.read(4), 4)
        self.assertEqual(reader.read(16), 0x5678)
        with self.assertRaises(ValueError): reader.read(1)

    def test_handcrafted_pucrunch_tokens(self):
        tokens = [
            ('01000001', 1, b'A'),
            ('00000000' + '0' + '10' + '00000000', 1, b'\0'),
            ('01000001' + '00000000' + '0' + '0' + '00000000', 3, b'AAA'),
            ('010000010100001001000011' + '00000000' + '100' + '0' + '00000010', 6, b'ABCABC'),
            ('00000000' + '0' + '11' + '101' + '0', 4, b'AAAA'),
        ]
        for bits, size, expected in tokens:
            with self.subTest(expected=expected): self.assertEqual(gc.decode(pc_bits(bits, size)), expected)
        with self.assertRaisesRegex(ValueError, 'back-reference'):
            gc.decode(pc_bits('00000000' + '0' + '0' + '00000000', 2))
        with self.assertRaisesRegex(ValueError, 'EOF'): gc.decode(pc_bits('', 1))

    def test_handcrafted_lz77_overlap(self):
        self.assertEqual(gc.decode(bytes.fromhex('10 06 00 00 40 41 20 00')), b'AAAAAA')
        with self.assertRaises(ValueError): gc.decode(bytes.fromhex('10 06 00 00 80 20 00'))

    def test_literal_roundtrip_and_corruption(self):
        for kind in (0x10, 0x60):
            for data in (b'', bytes(range(256)), bytes(513), b'opaque\xff\0' * 10):
                encoded = gc.encode_literals(data, kind)
                wrapped = gc.CompressedBlob.parse(encoded)
                self.assertEqual(wrapped.decoded, data)
                self.assertEqual(wrapped.to_bytes(), encoded)
                self.assertEqual(wrapped.replace_decoded(data), encoded)
                self.assertEqual(gc.decode(wrapped.replace_decoded(data + b'new')), data + b'new')
                self.assertEqual(gc.encode_literals(data, kind), encoded)
        for data in (b'', b'\x60\x01\0\0', b'\x70\0\0\0', bytes.fromhex('60 01 00 00 04 00 00 09') + bytes(8)):
            with self.assertRaises(ValueError): gc.decode(data)

    def test_xbd_binding_edit_retains_opaque_bytes(self):
        names = ['walk.sca', 'walk.gmb', 'run.sca', 'action.gab']
        kind = cf.ACTOR_KIND
        raw = (struct.pack('<IIHHII', kind, 24, 1, 0x1234, 0xaabbccdd, 0xdeadbeef)
               + struct.pack('<HHHHhH', 0, 0, 1, 3, -1, 0xbeef) + struct.pack('<I', kind))
        parsed = cf.Xbd.parse(raw, names)
        self.assertEqual(parsed.to_bytes(), raw)
        result = parsed.replace_binding(20, 2, names)
        self.assertEqual(result[:20], raw[:20]); self.assertEqual(result[22:], raw[22:])
        self.assertEqual(cf.Xbd.parse(result, names).bindings[0]['name'], 'run.sca')
        with self.assertRaises(ValueError): parsed.replace_binding(20, 3, names)
        with self.assertRaises(ValueError): parsed.replace_binding(32, 2, names)
        with self.assertRaises(ValueError): cf.Xbd.parse(raw[:-1], names)
        with self.assertRaises(ValueError): cf.Gab.parse(bytes(8))
        with self.assertRaises(ValueError): cf.Bsp.parse(bytes(24))


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class LocalCustomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rom, cls.glob, cls.manifest = mod.load_clean()
    def test_all_custom_envelopes_lossless(self):
        names = [e['name'] for e in self.manifest['entries']]
        for e in self.manifest['entries']:
            data = self.glob[e['offset']:e['offset'] + e['size']]
            ext = Path(e['name']).suffix
            with self.subTest(name=e['name']):
                if ext == '.xbd': self.assertEqual(cf.Xbd.parse(data, names).to_bytes(), data)
                elif ext == '.gab': self.assertEqual(cf.Gab.parse(data).to_bytes(), data)
                elif ext == '.bsp': self.assertEqual(cf.Bsp.parse(data).to_bytes(), data)

    def test_all_supported_compressed_resources_roundtrip(self):
        count = 0
        for e in self.manifest['entries']:
            if Path(e['name']).suffix not in ('.gmb', '.2lz'): continue
            data = self.glob[e['offset']:e['offset'] + e['size']]
            if data[0] not in (0x10, 0x60): continue
            with self.subTest(name=e['name']):
                wrapped = gc.CompressedBlob.parse(data)
                self.assertEqual(wrapped.to_bytes(), data)
                self.assertEqual(wrapped.replace_decoded(wrapped.decoded), data)
                self.assertEqual(gc.decode(gc.encode_literals(wrapped.decoded, data[0])), wrapped.decoded)
            count += 1
        self.assertEqual(count, 918)
