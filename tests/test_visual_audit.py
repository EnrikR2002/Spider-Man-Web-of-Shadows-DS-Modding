"""Texture census accepts the build's Rush/kit additions without relaxing asset names."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import nitro_build as nb, oscorp_resources, tasm_kit, visual_audit


class VisualAuditTests(unittest.TestCase):
    def test_current_overlay_additions_are_accepted_but_unknown_files_are_rejected(self):
        texture = nb.texture_archive((nb.Texture('test', 8, 8, 3, bytes(32)),),
                                     (nb.Palette('test_pl', bytes(32)),))
        manifest = {'entries': [{'name': 'spd.nsbtx', 'offset': 0, 'size': len(texture)}]}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for name in (*oscorp_resources.EXTRA_NAMES, *tasm_kit.EXTRA_NAMES):
                (root / name).write_bytes(b'private motion fixture')
            with patch.object(visual_audit.mod, 'load_clean', return_value=(b'ROM', texture, manifest)):
                result = visual_audit.audit(str(root))
                self.assertEqual(result['archive_count'], 1)
                self.assertEqual(result['dimensions'], {'8x8': 1})
                (root / 'unknown.sca').write_bytes(b'bad')
                with self.assertRaisesRegex(ValueError, 'Unknown overlay asset'):
                    visual_audit.audit(str(root))
