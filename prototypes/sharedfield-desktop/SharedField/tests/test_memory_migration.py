import unittest,tempfile,zipfile,subprocess,sys,json
from pathlib import Path
from switchlab.memory.service import MemoryService
from switchlab.memory.store import MemoryStore
from tests.test_memory_store import NOW

class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as t:
            with zipfile.ZipFile(root/'compatibility/shared_v05_runtime.zip') as z:z.extractall(t)
            code="from switchlab.shared.core import SharedCore;import json;c=SharedCore();c.apply('message',{'text':'旧的第一条'});c.apply('message',{'text':'旧的第二条'});c.apply('agent_step',{});print(json.dumps(c.checkpoint(),ensure_ascii=False))"
            r=subprocess.run([sys.executable,'-c',code],cwd=Path(t)/'SharedField',capture_output=True,check=True)
            cls.data=json.loads(r.stdout)
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.s=MemoryService(self.t.name,clock=lambda:NOW);self.addCleanup(lambda:self.s.close())
    def test_old_source_verified_and_chronology_preserved(self):
        result=self.s.import_checkpoint(self.data)
        self.assertTrue(result['paused']);v=self.s.view();self.assertEqual(v['world']['world']['tick'],1)
        self.assertEqual([m['text'] for m in v['messages']],['旧的第一条','旧的第二条'])
        self.assertTrue(all(m['at'] is None for m in v['messages']))
        cp=self.s.store.export();r=MemoryStore.from_export(Path(self.t.name)/'replay.db',cp)
        self.assertEqual(r.projection_digest(),self.s.store.projection_digest());r.close()
    def test_forged_snapshot_is_not_accepted_on_legacy_command(self):
        self.s.import_checkpoint(self.data);e=self.s.store.export()['journal'][0]
        altered=json.loads(json.dumps(e['payload']));altered['snapshot']['world']['tick']=99
        other=MemoryStore(Path(self.t.name)/'bad.db')
        try:
            with self.assertRaises(ValueError):other.apply('legacy',altered,at=NOW)
        finally:other.close()
    def test_invalid_import_keeps_active_memory_unchanged(self):
        self.s.submit('新生活的记忆');before=self.s.store.projection_digest()
        d=json.loads(json.dumps(self.data));d['state']['messages'][0]['text']='假记忆'
        with self.assertRaises(ValueError):self.s.import_checkpoint(d,archive_current=True)
        self.assertEqual(before,self.s.store.projection_digest())
