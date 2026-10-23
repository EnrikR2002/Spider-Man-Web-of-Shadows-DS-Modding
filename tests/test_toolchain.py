"""Synthetic corruption/resize regressions plus optional local-ROM integration.

No copyrighted test fixtures. Run: python -m unittest discover -s tests -v
"""
import contextlib
import io
import json
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import mod
from tools import wos_tool as w
from tools import nitro_texture as nt


def make_glob(names=None):
    names = names or ['asset.bin', 'GlobFiles.txt', 'other.dat']
    table = b''.join(name.encode().ljust(63, b' ') + b'\n' for name in names)
    return w.pack_glob(names, [b'opaque\x00\xff', table, b'other'])


def make_rom():
    rom = bytearray(b'\xff' * (128 * 1024))
    rom[:0x200] = bytes(0x200)
    rom[:12] = b'SPIDERMANWOS'; rom[12:16] = b'CS5E'
    rom[0x14] = 0
    for off, start, size in [(0x20, 0x200, 0x80), (0x30, 0x400, 0x40),
                             (0x40, 0x600, 34), (0x48, 0x800, 16)]:
        struct.pack_into('<I', rom, off, start)
        struct.pack_into('<I', rom, off + (12 if off in (0x20, 0x30) else 4), size)
    struct.pack_into('<III', rom, 0x80, 0x1800, 0x200, 0)
    struct.pack_into('<I', rom, 0x68, 0xa00); struct.pack_into('<H', rom, 0xa00, 1)
    fnt = struct.pack('<IHH', 8, 0, 1) + b'\x08Glob.bin\x0fsound_data.sdat\x00'
    rom[0x600:0x600 + len(fnt)] = fnt
    glob = make_glob(); sdat = b'SDATopaque\x00unknown'
    rom[0x1400:0x1400 + len(glob)] = glob; rom[0x1600:0x1600 + len(sdat)] = sdat
    struct.pack_into('<IIII', rom, 0x800, 0x1400, 0x1400 + len(glob), 0x1600, 0x1600 + len(sdat))
    struct.pack_into('<H', rom, 0x15e, w.crc16(rom[:0x15e]))
    return bytes(rom)


class GlobTests(unittest.TestCase):
    def test_lossless_and_variable_lengths(self):
        glob = make_glob(); offsets, names, idx = w.parse_glob(glob)
        blobs = [glob[a:b] for a, b in zip(offsets, offsets[1:])]
        self.assertEqual(idx, 1); self.assertEqual(w.pack_glob(names, blobs), glob)
        for size in (0, 1, 7, 513, 2048):
            changed = [b'x' * size, blobs[1], blobs[2]]
            rebuilt = w.pack_glob(names, changed); ro, rn, ri = w.parse_glob(rebuilt)
            self.assertEqual(rn, names); self.assertEqual(ri, idx)
            self.assertEqual([rebuilt[a:b] for a, b in zip(ro, ro[1:])], changed)

    def test_bad_offsets(self):
        source = make_glob()
        for offset, value in [(0, 7), (0, len(source) + 4), (4, 1), (12, len(source) - 1), (4, len(source) + 1)]:
            data = bytearray(source); struct.pack_into('<I', data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(ValueError): w.parse_glob(data)
        for data in (b'', source[:7], source[:-1]):
            with self.assertRaises(ValueError): w.parse_glob(data)

    def test_bad_names_and_duplicates(self):
        for names in [['../asset', 'GlobFiles.txt', 'other.dat'], ['asset.bin', 'GlobFiles.txt', 'ASSET.BIN']]:
            with self.assertRaises(ValueError): make_glob(names)
        for name in ('../escape', '/root', 'a\\b', 'C:/x', 'NUL.txt', 'name.', 'a//b', 'a\x00b'):
            with self.subTest(name=name), self.assertRaises(ValueError): w.safe_name(name)

    def test_extracted_directory_roundtrip_and_manifest_order(self):
        glob = make_glob()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td); w.unpack_glob(glob, out)
            self.assertEqual(w.repack_directory(out), glob)
            mf = json.loads((out / '_glob_manifest.json').read_text())
            self.assertEqual(w.sha256((out / 'asset.bin').read_bytes()), mf['entries'][0]['sha256'])
            mf['entries'].reverse(); w.write_json(out / '_glob_manifest.json', mf)
            with self.assertRaises(ValueError): w.repack_directory(out)


class RomTests(unittest.TestCase):
    def setUp(self): self.rom = make_rom()
    def test_noop_is_exact(self):
        report = w.validate_rom(self.rom, target=True)
        e = report['nitrofs'][0]
        self.assertEqual(w.rebuild_rom(self.rom, {'Glob.bin': self.rom[e['start']:e['end']]}), self.rom)

    def test_growth_shrink_alignment_crc_and_unknown_bytes(self):
        old = w.nitrofs_entries(self.rom)
        for size in (0, 1, 512, 513, 2049):
            blob = bytes([size % 256]) * size
            rebuilt = w.rebuild_rom(self.rom, {'Glob.bin': blob})
            entries = w.nitrofs_entries(rebuilt); h = w.parse_header(rebuilt)
            self.assertEqual(len(rebuilt), len(self.rom))
            self.assertEqual(rebuilt[entries[0]['start']:entries[0]['end']], blob)
            self.assertEqual(rebuilt[entries[1]['start']:entries[1]['end']], self.rom[old[1]['start']:old[1]['end']])
            self.assertEqual(h['header_crc16'], w.crc16(rebuilt[:0x15e]))
            self.assertTrue(all(e['start'] % 512 == 0 for e in entries))
            self.assertEqual(rebuilt[0x200:0x800], self.rom[0x200:0x800])
            self.assertEqual(rebuilt[0xa00:0x1400], self.rom[0xa00:0x1400])
            if size <= old[0]['size']:
                self.assertEqual(entries[1]['start'], old[1]['start'])
                self.assertEqual(rebuilt[0x1400 + size:0x1600], self.rom[0x1400 + size:0x1600])

    def test_reject_capacity_unknown_tail_and_unknown_file(self):
        with self.assertRaises(ValueError): w.rebuild_rom(self.rom, {'Glob.bin': b'x' * len(self.rom)})
        with self.assertRaises(ValueError): w.rebuild_rom(self.rom, {'missing': b'x'})
        changed = bytearray(self.rom); changed[0x1800] = 123
        with self.assertRaisesRegex(ValueError, 'non-padding'): w.rebuild_rom(bytes(changed), {'Glob.bin': b'x' * 4096})

    def test_growth_rejects_occupied_internal_and_trailing_gaps(self):
        for offset, size in ((0x1550, 513), (0x1700, 1024)):
            with self.subTest(offset=offset):
                source = bytearray(self.rom)
                source[offset:offset + 8] = b'UNKNOWN!'
                with self.assertRaisesRegex(ValueError, 'non-padding.*gap'):
                    w.rebuild_rom(bytes(source), {'Glob.bin': b'x' * size})
                unchanged_gap = w.rebuild_rom(bytes(source), {'Glob.bin': b'x'})
                self.assertEqual(unchanged_gap[offset:offset + 8], b'UNKNOWN!')

    def test_frozen_generators_can_reproduce_relocated_file_residue(self):
        first = w.rebuild_rom(self.rom, {'Glob.bin': b'x' * 513})
        with self.assertRaisesRegex(ValueError, 'non-padding.*gap'):
            w.rebuild_rom(first, {'Glob.bin': b'x' * 1024})
        legacy = w.rebuild_rom(first, {'Glob.bin': b'x' * 1024}, legacy_gaps=True)
        entries = w.nitrofs_entries(legacy)
        self.assertEqual(legacy[entries[0]['start']:entries[0]['end']], b'x' * 1024)
        self.assertEqual(legacy[entries[1]['start']:entries[1]['end']], b'SDATopaque\0unknown')

    def test_reject_bad_fat_fnt_header(self):
        changes = [(0x800, '<I', 0x100), (0x804, '<I', 0x1300), (0x80c, '<I', len(self.rom) + 1),
                   (0x808, '<I', 0x1400), (0x4c, '<I', 15), (0x600, '<I', 0), (0x606, '<H', 0),
                   (0x44, '<I', 9)]
        for offset, fmt, value in changes:
            data = bytearray(self.rom); struct.pack_into(fmt, data, offset, value)
            struct.pack_into('<H', data, 0x15e, w.crc16(data[:0x15e]))
            with self.subTest(offset=offset), self.assertRaises(ValueError): w.validate_rom(bytes(data))
        data = bytearray(self.rom); data[1] ^= 1
        with self.assertRaisesRegex(ValueError, 'CRC'): w.validate_rom(bytes(data))

    def test_protect_original_and_input(self):
        with self.assertRaises(ValueError): w.atomic_write(mod.ROOT / 'original/test.nds', b'x')
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'source.nds'; source.write_bytes(self.rom)
            with self.assertRaises(ValueError): w.atomic_write(source, b'x', (source,))
            linked = Path(td) / 'linked.nds'; os.link(source, linked)
            with self.assertRaises(ValueError): w.atomic_write(linked, b'x', (source,))
            self.assertEqual(source.read_bytes(), self.rom)
        with self.assertRaises(ValueError): mod.build_output('work/test.nds')


class DefaultOutputTests(unittest.TestCase):
    def test_raw_build_and_verify_default_to_candidate_without_replacing_stable(self):
        rom = make_rom(); e = w.nitrofs_entries(rom)[0]
        glob = rom[e['start']:e['end']]; manifest = w.glob_manifest(glob)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); mods = root / 'mods'; mods.mkdir()
            stable = root / 'build/Spider-Man-WoS-modded.nds'
            stable.parent.mkdir(); stable.write_bytes(b'published release')
            with patch.object(mod, 'ROOT', root), patch.object(mod, 'load_clean', return_value=(rom, glob, manifest)):
                with contextlib.redirect_stdout(io.StringIO()):
                    for command in ('build', 'verify'):
                        self.assertEqual(mod.main([command, '--mods', str(mods), '--gameplay-profile', 'original']), 0)
            self.assertEqual(stable.read_bytes(), b'published release')
            self.assertEqual((root / 'build/candidate' / stable.name).read_bytes(), rom)

    def test_raw_repack_defaults_to_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / 'source.nds'; source.write_bytes(make_rom())
            glob = Path(td) / 'Glob.bin'; glob.write_bytes(make_glob())
            with patch.object(w, 'atomic_write') as write, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(w.main(['repack-rom', str(source), '--glob', str(glob)]), 0)
            self.assertEqual(write.call_args.args[0].as_posix(), 'build/candidate/Spider-Man-WoS-modded.nds')


class OverlayTests(unittest.TestCase):
    def test_only_exact_manifest_names(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'README.md').write_text('info')
            (root / 'asset.bin').write_bytes(b'new')
            self.assertEqual(mod.overlay_files(root, ['asset.bin', 'GlobFiles.txt']), {'asset.bin': b'new'})
            (root / 'typo.bin').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'Unknown'): mod.overlay_files(root, ['asset.bin'])
            (root / 'typo.bin').unlink(); (root / 'GlobFiles.txt').write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError, 'protected'): mod.overlay_files(root, ['asset.bin', 'GlobFiles.txt'])

    def test_case_mismatch_and_nested_typo(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / 'Asset.bin').write_bytes(b'x')
            with self.assertRaisesRegex(ValueError, 'exact filename'): mod.overlay_files(root, ['asset.bin'])

    def test_deterministic_build_and_all_resources_checked(self):
        rom = make_rom(); e = w.nitrofs_entries(rom)[0]; glob = rom[e['start']:e['end']]
        mf = w.glob_manifest(glob)
        a = mod.create_build(rom, glob, mf, {'asset.bin': b'changed' * 100})
        b = mod.create_build(rom, glob, mf, {'asset.bin': b'changed' * 100})
        self.assertEqual(a, b); self.assertEqual(a[2]['verified_resource_count'], 3)
        self.assertEqual(a[2]['replaced_assets'][0]['old_sha256'], mf['entries'][0]['sha256'])
        self.assertEqual(len(a[2]['replaced_assets']), 1)


@unittest.skipUnless(mod.DEFAULT_ROM.exists(), 'Private clean ROM not present')
class LocalRomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.rom, cls.glob, cls.manifest = mod.load_clean()
    def test_real_noop(self):
        rebuilt, glob, log = mod.create_build(self.rom, self.glob, self.manifest, {})
        self.assertEqual(rebuilt, self.rom); self.assertEqual(glob, self.glob)
        self.assertEqual(log['verified_resource_count'], 3733)

    def test_real_resize(self):
        e = next(e for e in self.manifest['entries'] if e['name'] == 'spd.xbd')
        original = self.glob[e['offset']:e['offset'] + e['size']]
        for changed in (original + b'\x00' * 513, original[:-1], b''):
            rebuilt, glob, log = mod.create_build(self.rom, self.glob, self.manifest, {'spd.xbd': changed})
            self.assertEqual(len(log['replaced_assets']), 1)
            self.assertEqual(log['unchanged_resource_count'], 3732)
            self.assertEqual(w.validate_rom(rebuilt)['header']['header_crc16'], w.crc16(rebuilt[:0x15e]))

    def test_all_nsbtx_lossless(self):
        for e in self.manifest['entries']:
            if e['name'].endswith('.nsbtx'):
                data = self.glob[e['offset']:e['offset'] + e['size']]
                with self.subTest(name=e['name']):
                    self.assertEqual(nt.TextureArchive.parse(data).to_bytes(), data)

    def test_palette_experiment_confined_and_reversible(self):
        e = next(e for e in self.manifest['entries'] if e['name'] == 'spd.nsbtx')
        data = self.glob[e['offset']:e['offset'] + e['size']]
        archive = nt.TextureArchive.parse(data)
        self.assertEqual(archive.replace_palette(data[archive.palette_start:]), data)
        changed, report = nt.green_suit(data)
        self.assertEqual(changed[:archive.palette_start], data[:archive.palette_start])
        self.assertEqual(len(data), len(changed)); self.assertGreater(len(report['color_edits']), 0)
        self.assertEqual(nt.green_suit(data)[0], changed)
        self.assertEqual(nt.TextureArchive.parse(changed).replace_palette(data[archive.palette_start:]), data)
        with self.assertRaises(ValueError): archive.replace_palette(b'bad')
        for corrupt in (data[:8], data[:-1], b'BAD!' + data[4:]):
            with self.assertRaises(ValueError): nt.TextureArchive.parse(corrupt)
        corrupt = bytearray(data)
        struct.pack_into('<I', corrupt, archive.tex0_start + 0x38, w.u32(data, archive.tex0_start + 0x14))
        with self.assertRaisesRegex(ValueError, 'Overlapping'): nt.TextureArchive.parse(bytes(corrupt))


if __name__ == '__main__': unittest.main()
