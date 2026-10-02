import importlib.util
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.migration'),'verified migration missing')
        from switchlab.studio.migration import migrate_v02, ARCHIVE
        self.migrate=migrate_v02;self.archive=ARCHIVE
    def test_original_package_sample_verified_and_parked(self):
        with tempfile.TemporaryDirectory(prefix='migration 中文 ') as d:
            p=Path(d)/'old.json'
            with zipfile.ZipFile(self.archive) as z:p.write_bytes(z.read('SwitchLab/examples/studio_sample.json'))
            old=p.read_bytes();target=Path(d)/'new'
            result=self.migrate(p,target)
            self.assertEqual(p.read_bytes(),old)
            self.assertTrue(result['legacy_recorded_input_replay'])
            from switchlab.studio.adaptive_core import AdaptiveCore
            c=AdaptiveCore.restore(json.loads((target/'session.json').read_text()))
            self.assertEqual(c.learner.seen,0);self.assertEqual(c.state['goals'],[])
            self.assertTrue(c.cog['legacy_context']['messages'])
            with self.assertRaises(ValueError):self.migrate(p,target)
    def test_modified_legacy_state_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with zipfile.ZipFile(self.archive) as z:data=json.loads(z.read('SwitchLab/examples/studio_sample.json'))
            data['state']['calls']+=4;p=Path(d)/'bad.json';p.write_text(json.dumps(data))
            with self.assertRaises(ValueError):self.migrate(p,Path(d)/'new')
            self.assertFalse((Path(d)/'new'/'session.json').exists())

    def test_legacy_reader_uses_explicit_utf8_even_with_ascii_pipe_default(self):
        import subprocess,sys
        from switchlab.studio.migration import READER
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with zipfile.ZipFile(self.archive) as z:z.extractall(root)
            command="import sys;sys.stdout.reconfigure(encoding='ascii')\n"+READER
            r=subprocess.run([sys.executable,'-I','-c',command,str(root/'SwitchLab'),str(root/'SwitchLab/examples/studio_sample.json')],capture_output=True,encoding='utf-8',timeout=20)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue(json.loads(r.stdout)['source_verified'])
