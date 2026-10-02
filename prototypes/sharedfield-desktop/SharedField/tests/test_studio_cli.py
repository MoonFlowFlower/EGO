import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from switchlab.studio.core import Core
from switchlab.runtime import save_json
ROOT=Path(__file__).resolve().parents[1]

class StudioCliTests(unittest.TestCase):
    def test_studio_help(self):
        r=subprocess.run([sys.executable,str(ROOT/'run.py'),'studio','--help'],capture_output=True,text=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn('--data-dir',r.stdout)
    def test_studio_recorded_input_verify(self):
        with tempfile.TemporaryDirectory() as d:
            c=Core();c.apply('message',{'text':'实际CLI检查'});p=Path(d)/'sample.json';save_json(p,c.checkpoint())
            r=subprocess.run([sys.executable,str(ROOT/'run.py'),'studio-verify',str(p)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(r.stdout);self.assertTrue(data['recorded_input_replay']);self.assertFalse(data['remote_model_rerun'])
    def test_import_does_not_overwrite_existing_life(self):
        with tempfile.TemporaryDirectory() as d:
            from switchlab.studio.adaptive_core import AdaptiveCore
            c=AdaptiveCore();c.apply('message',{'text':'import fixture'});p=Path(d)/'sample.json';save_json(p,c.checkpoint())
            target=Path(d)/'imported data'
            cmd=[sys.executable,str(ROOT/'run.py'),'studio-import',str(p),'--data-dir',str(target)]
            a=subprocess.run(cmd,capture_output=True,text=True,timeout=10);self.assertEqual(a.returncode,0,a.stderr)
            b=subprocess.run(cmd,capture_output=True,text=True,timeout=10);self.assertNotEqual(b.returncode,0)
            self.assertTrue((target/'session.json').exists())
