import unittest,tempfile,json
from pathlib import Path
from switchlab.memory.store import MemoryStore
from switchlab.memory.service import MemoryService
from tests.test_memory_store import NOW

class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=MemoryService(self.tmp.name,clock=lambda:NOW);self.addCleanup(lambda:self.s.close())
    def test_selective_delete_removes_source_derivatives_index_and_managed_backup(self):
        src=self.s.submit('约定一起读秘密书Z938')['id']
        e=self.s.store.apply('interpret',{'source':src,'claims':[],'commitments':[{'op':'create','title':'秘密书Z938','quote':'约定一起读秘密书Z938','accept':True}]},at=NOW)
        self.s.store.apply('expression',{'text':'记住秘密书Z938了','source':src,'evidence':[src]},at=NOW)
        keep=self.s.submit('不相关的普通记忆')['id'];self.s.backup();self.assertTrue(list((Path(self.tmp.name)/'backups').glob('*.sqlite3')))
        self.assertTrue(hasattr(self.s,'forget'),'missing privacy deletion workflow')
        result=self.s.forget([src],True)
        self.assertGreaterEqual(result['removed_observations'],2);self.assertEqual(self.s.store.commitments()['total'],0)
        self.assertEqual(self.s.store.search('Z938')['total'],0);self.assertNotIn('Z938',json.dumps(self.s.store.export(),ensure_ascii=False))
        self.assertEqual(self.s.store.observation(keep)['text'],'不相关的普通记忆')
        self.assertFalse(list((Path(self.tmp.name)/'backups').glob('*.sqlite3')))
    def test_post_delete_new_writes_replay_and_identity_survives(self):
        src=self.s.submit('delete me')['id'];pid=self.s.store.person_id
        self.assertTrue(hasattr(self.s,'forget'));self.s.forget([src],True)
        new=self.s.submit('new memory')['id'];self.assertNotEqual(src,new)
        e=self.s.store.export();other=MemoryStore.from_export(Path(self.tmp.name)/'copy.db',e)
        try:self.assertEqual(other.person_id,pid);self.assertEqual(other.projection_digest(),self.s.store.projection_digest())
        finally:other.close()
    def test_requires_explicit_local_confirmation(self):
        src=self.s.submit('keep me')['id'];self.assertTrue(hasattr(self.s,'forget'))
        with self.assertRaises(ValueError):self.s.forget([src],False)
        self.assertEqual(self.s.store.observation(src)['text'],'keep me')
    def test_import_checkpoint_column_names_are_not_executable(self):
        data=self.s.store.export();data['initial']['privacy_projection']={t:[] for t in self.s.store.projection()}
        data['initial']['privacy_projection']['settings']=[{'key) VALUES (\'x\'); DROP TABLE observations; --':'bad','body':'1'}]
        with self.assertRaises(ValueError):MemoryStore(Path(self.tmp.name)/'unsafe.db',initial=data['initial'])
