import unittest,tempfile,json
from copy import deepcopy
from pathlib import Path
from switchlab.memory.store import MemoryStore
from switchlab.memory.service import MemoryService
from tests.test_memory_store import NOW
from tests.test_memory_service import Fixture

class MemoryRegressions(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        self.s=MemoryService(self.t.name,provider=Fixture(),clock=lambda:NOW);self.addCleanup(self.s.close)
    def test_long_current_message_kept_while_retrieval_cues_are_bounded(self):
        text='开始'+('长内容。'*1500)+'最后关键原文';self.s.set_options({'language_mode':'api'});self.s.submit(text)
        self.s.run_once();self.s.run_once()
        self.assertFalse(self.s.error,self.s.error)
        self.assertEqual(self.s.provider.calls[0]['selected_input']['text'],text)
    def test_invalid_optional_feedback_rolls_back_other_interpretation_changes(self):
        mid=self.s.submit('1分钟后一起看星空')['id']
        p={'source':mid,'claims':[],'commitments':[{'op':'create','title':'看星空','quote':'1分钟后一起看星空','when':'1分钟后','accept':True}],
           'feedback':{'contact':'missing','outcome':'busy','quote':'一起看星空'}}
        with self.assertRaises(ValueError):self.s.store.apply('interpret',p,at=NOW)
        self.assertEqual(self.s.store.commitments()['total'],0)
        self.assertFalse(self.s.store.setting('interpreted:'+mid))
    def test_valid_feedback_and_commitment_are_one_atomic_interpretation(self):
        self.s.edit_commitment({'op':'create','title':'准备','quote':'1秒后准备','when':'1秒后','accept':True})
        c=self.s.store.commitments()['items'][0]
        k=self.s.store.apply('consider',{'id':c['id'],'revision':1},at=NOW+2)['result']['contact']['key']
        self.s.store.apply('expression',{'text':'现在方便吗','source':None,'evidence':[c['source']],'contact':k},at=NOW+2)
        mid=self.s.submit('现在忙，明天再一起看书')['id']
        result=self.s.store.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'create','title':'看书','quote':'明天再一起看书','when':'明天','accept':True}],
           'feedback':{'contact':k,'outcome':'busy','quote':'现在忙'}},at=NOW+4)
        self.assertTrue(result['result']['feedback']['updated']);self.assertEqual(self.s.store.outcome_count(),1)
    def test_source_window_can_read_detail_beyond_first_thousand(self):
        raw='引言。'*1000+'精确约定：青蓝星书第七章';oid=self.s.store.apply('message',{'text':raw},at=NOW)['id']
        ctx=self.s.store.context('那本书',windows=[{'id':oid,'start':2990,'length':100}])
        self.assertIn('青蓝星书第七章',json.dumps(ctx,ensure_ascii=False))
        self.assertEqual(self.s.store.observation(oid)['text'],raw)
    def test_database_does_not_silently_open_with_other_runtime_fingerprint(self):
        self.s.store.db.execute("UPDATE meta SET value=? WHERE key='initial'",(json.dumps({**self.s.store._meta('initial'),'source_sha256':'bad'}),))
        self.s.close()
        with self.assertRaisesRegex(ValueError,'源代码'):MemoryStore(Path(self.t.name)/'memory.sqlite3')
    def test_prepared_contact_waits_for_explicit_busy_until_before_network(self):
        self.s.edit_commitment({'op':'create','title':'准备','quote':'1秒后准备','when':'1秒后','accept':True})
        c=self.s.store.commitments()['items'][0];self.s.store.apply('consider',{'id':c['id'],'revision':1},at=NOW+2)
        mid=self.s.store.apply('message',{'text':'我忙到1小时后'},at=NOW)['id']
        self.s.store.apply('interpret',{'source':mid,'claims':[],'commitments':[],'availability':{'quote':'我忙到1小时后','until':'1小时后'}},at=NOW)
        self.s.set_options({'language_mode':'api'});self.s.start_background();self.s.run_once()
        self.assertEqual(self.s.provider.calls,[]);self.assertFalse(self.s.error)
