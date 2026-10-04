import struct
import unittest
import mod
from tools.gmb import Gmb, RECORD_STRIDES
from tools.grip_compression import CompressedBlob, decode


def fixture(count=2, kinds=(3, 0)):
    parts = [struct.pack('<4H', 0x1234, count, len(kinds), 0xabcd)]
    for index, kind in enumerate(kinds):
        parts.append(struct.pack('<hH', kind, 0xef00 + index))
        stride = RECORD_STRIDES[kind]
        for frame in range(count):
            parts.append(bytes((frame + j + index * 37) % 256 for j in range(stride)))
    return b''.join(parts)


class GmbTests(unittest.TestCase):
    def test_channel_boundaries_and_unknown_bytes_roundtrip(self):
        for kinds in ((3, 3, 3, 0), (0, 2, 3, 4, 5, 6, 12), ()):
            raw = fixture(kinds=kinds)
            parsed = Gmb.parse(raw)
            self.assertEqual(parsed.to_bytes(), raw)
            self.assertEqual(parsed.unknown_u16_00, 0x1234)
            self.assertEqual(parsed.unknown_u16_06, 0xabcd)
            self.assertEqual([c.kind for c in parsed.channels], list(kinds))
            pos = 8
            for c in parsed.channels:
                self.assertEqual(c.offset, pos)
                self.assertEqual(len(c.records), 2)
                pos += 4 + 2 * c.stride
            self.assertEqual(pos, len(raw))
        self.assertEqual(Gmb.parse(fixture(count=0)).to_bytes(), fixture(count=0))

    def test_one_word_edit_is_bounded_and_deterministic(self):
        raw = fixture(kinds=(3, 0, 4))
        parsed = Gmb.parse(raw)
        for value in (-(1 << 31), -27, 0, (1 << 31)-1):
            changed = parsed.replace_word(1, 1, 6, value)
            offset = parsed.channels[1].offset + 4 + 28 + 24
            expected = raw[:offset] + struct.pack('<i', value) + raw[offset+4:]
            self.assertEqual(changed, expected)
            self.assertEqual(Gmb.parse(changed).to_bytes(), changed)
            self.assertEqual(parsed.replace_word(1, 1, 6, value), changed)
        same = parsed.channels[1].words(1)[6]
        self.assertEqual(parsed.replace_word(1, 1, 6, same), raw)
        for args in ((-1, 0, 0, 1), (3, 0, 0, 1), (0, 2, 0, 1),
                     (1, 0, 7, 1), (0, 0, -1, 1), (0, 0, 0, 1 << 31)):
            with self.assertRaises(ValueError): parsed.replace_word(*args)

    def test_truncation_unknown_kind_and_trailing_data_rejected(self):
        raw = fixture()
        for bad in (raw[:7], raw[:-1], raw + bytes(4),
                    raw[:8] + struct.pack('<h', 1) + raw[10:]):
            with self.assertRaises(ValueError): Gmb.parse(bad)
        bad = bytearray(raw); struct.pack_into('<H', bad, 4, 0xffff)
        with self.assertRaises(ValueError): Gmb.parse(bad)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class LocalGmbTests(unittest.TestCase):
    def test_all_769_decoded_resources_roundtrip_and_representative_edits(self):
        _, glob, manifest = mod.load_clean()
        total, kinds, edited = 0, set(), set()
        for entry in manifest['entries']:
            if not entry['name'].endswith('.gmb'): continue
            raw = glob[entry['offset']:entry['offset']+entry['size']]
            wrapped = CompressedBlob.parse(raw)
            with self.subTest(name=entry['name']):
                parsed = Gmb.parse(wrapped.decoded)
                self.assertEqual(parsed.to_bytes(), wrapped.decoded)
                self.assertEqual(wrapped.replace_decoded(parsed.to_bytes()), raw)
                kinds.update(c.kind for c in parsed.channels)
                for index, channel in enumerate(parsed.channels):
                    if parsed.record_count and channel.kind not in edited:
                        old = channel.words(0)[0]
                        changed = parsed.replace_word(index, 0, 0, old ^ 1)
                        self.assertEqual(decode(wrapped.replace_decoded(changed)), changed)
                        edited.add(channel.kind)
            total += 1
        self.assertEqual(total, 769)
        self.assertEqual(kinds, {0, 2, 3, 4, 5})
        self.assertEqual(edited, kinds)
