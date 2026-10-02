import unittest,tempfile,subprocess,sys,json
from pathlib import Path
class MemoryCLI(unittest.TestCase):
    def test_verify_and_import_commands_are_real_entrypoints(self):
        from switchlab.memory.store import MemoryStore
        with tempfile.TemporaryDirectory() as t:
            t=Path(t);s=MemoryStore(t/'a.db');s.apply('message',{'text':'跨窗口原话'},at=1800000000)
            cp=t/'a.json';cp.write_text(json.dumps(s.export(),ensure_ascii=False),encoding='utf8');s.close()
            root=Path(__file__).resolve().parents[1]
            for args in (['memory-verify',str(cp)],['memory-import',str(cp),'--data-dir',str(t/'new')]):
                r=subprocess.run([sys.executable,str(root/'run.py')]+args,capture_output=True,text=True,timeout=20)
                self.assertEqual(r.returncode,0,r.stderr+r.stdout)
            self.assertTrue((t/'new'/'memory.sqlite3').exists())
    def test_launcher_selects_memory_not_old_game(self):
        root=Path(__file__).resolve().parents[1]
        self.assertIn('memory %*',(root/'START_WINDOWS.bat').read_text())
        self.assertIn("or ['memory']",(root/'run.py').read_text())
