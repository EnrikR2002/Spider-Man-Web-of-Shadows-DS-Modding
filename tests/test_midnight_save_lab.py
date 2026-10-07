import json
from pathlib import Path
import unittest
from unittest import mock

from tools import midnight_save_lab as lab


class SaveVerificationTests(unittest.TestCase):
    def reports(self, unrelated_change=False):
        control=bytes(512)
        fixture=bytearray(control)
        fixture[16:20]=b'crc!'
        fixture[84:88]=lab.PATTERN.to_bytes(4,'little')
        if unrelated_change: fixture[32]=1
        stats=bytearray(88)
        stats[64:68]=lab.PATTERN.to_bytes(4,'little')
        reports={}
        for mode,word in [('control',0),('fixture',lab.PATTERN),('reload',lab.PATTERN)]:
            reports['save-'+mode+'.json']=json.dumps({'source_unchanged':True,'flag_word':word,
                'stats_hex':stats.hex(),'battery':mode+'.sav'}).encode()
        reports['control.sav']=control
        reports['fixture.sav']=bytes(fixture)
        return reports

    def test_native_roundtrip_comparison_rejects_unrelated_battery_changes(self):
        for changed in (False,True):
            reports=self.reports(changed)
            def read(path): return reports[path.name]
            def read_text(path,*args,**kwargs): return reports[path.name].decode()
            with mock.patch.object(Path,'read_bytes',read), mock.patch.object(Path,'read_text',read_text), mock.patch.object(lab.w,'write_json'):
                report=lab.verify()
            self.assertEqual(report['passed'],not changed)


if __name__ == '__main__': unittest.main()
