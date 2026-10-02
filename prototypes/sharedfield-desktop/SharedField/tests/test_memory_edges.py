import unittest,tempfile,json
from pathlib import Path
from switchlab.memory.store import MemoryStore
from tests.test_memory_store import NOW

class MemoryEdgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.s=MemoryStore(Path(self.tmp.name)/'x.db');self.addCleanup(self.s.close)
    def create(self,title,when='1分钟后'):
        text=title+when;mid=self.s.apply('message',{'text':text},at=NOW)['id']
        e=self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'create','title':title,'quote':text,'when':when,'accept':True}]},at=NOW)
        return self.s.commitment(e['result']['commitments'][0])
    def test_many_prepared_items_do_not_starve_remaining_due(self):
        for i in range(101):
            c=self.create('约定'+str(i));self.s.apply('consider',{'id':c['id'],'revision':1},at=NOW+61)
        c=self.create('最后一个')
        self.assertIn(c['id'],[r['id'] for r in self.s.due(NOW+62)])
    def test_recall_cancelled_old_source_also_loads_latest_version(self):
        c=self.create('琥珀之书');mid=self.s.apply('message',{'text':'取消那本书的计划'},at=NOW)['id']
        self.s.apply('interpret',{'source':mid,'claims':[],'commitments':[{'op':'cancel','id':c['id'],'expected_revision':1,'quote':'取消那本书的计划'}]},at=NOW)
        for i in range(50):self.s.apply('message',{'text':'无关的新对话'+str(i)},at=NOW)
        ctx=self.s.context('琥珀之书',budget_bytes=12000)
        self.assertTrue(any(x['id']==c['id'] and x['status']=='cancelled' for x in ctx['effective_commitments']))
    def test_empty_identifier_does_not_mean_merge(self):
        a=self.create('一起看书');b=self.create('一起看书')
        self.assertNotEqual(a['id'],b['id']);self.assertEqual(self.s.commitments()['total'],2)
    def test_rolling_context_keeps_original_whitespace(self):
        text='  这是原话\n结尾  ';mid=self.s.apply('message',{'text':text},at=NOW)['id']
        self.assertEqual(self.s.observation(mid)['text'],text)
