import unittest,tempfile,subprocess,sys,re,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class SharedCLITests(unittest.TestCase):
    def test_shared_entrypoint_really_starts_new_kernel(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.Popen([sys.executable,str(ROOT/'run.py'),'shared','--port','0','--no-browser','--data-dir',d],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                line=p.stdout.readline();url=re.search(r'http://127\.0\.0\.1:\d+',line)
                self.assertIsNotNone(url,line)
                with urllib.request.urlopen(url.group(),timeout=3) as r:html=r.read().decode()
                token=re.search('name="studio-token" content="([^"]+)"',html).group(1)
                with urllib.request.urlopen(urllib.request.Request(url.group()+'/api/state',headers={'X-SwitchLab-Token':token}),timeout=3) as r:s=json.load(r)
                self.assertEqual(s['version'],'0.5.0');self.assertEqual(s['runtime']['auto_remaining'],0)
            finally:p.terminate();p.communicate(timeout=5)
    def test_verify_and_import_into_new_directory_only(self):
        from switchlab.shared.core import SharedCore
        from switchlab.runtime import save_json
        with tempfile.TemporaryDirectory(prefix='共享 space ') as d:
            c=SharedCore();c.apply('agent_step',{});source=Path(d)/'snapshot.json';save_json(source,c.checkpoint());target=Path(d)/'imported'
            for args in (['shared-verify',str(source)],['shared-import',str(source),'--data-dir',str(target)]):
                r=subprocess.run([sys.executable,str(ROOT/'run.py'),*args],capture_output=True,text=True,timeout=10)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            r=subprocess.run([sys.executable,str(ROOT/'run.py'),'shared-import',str(source),'--data-dir',str(target)],capture_output=True,text=True,timeout=10)
            self.assertNotEqual(r.returncode,0)
