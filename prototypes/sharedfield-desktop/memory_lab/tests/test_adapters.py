import tempfile
import unittest
from pathlib import Path


class AdapterContract(unittest.TestCase):
    def test_baseline_keeps_original_provenance_and_removes_deleted_source(self):
        from memory_lab.adapters import Baseline
        from memory_lab.core import Store
        with tempfile.TemporaryDirectory() as td:
            store=Store(Path(td)/'raw.sqlite')
            try:
                event=dict(id='e1',text='小禾忙的时候希望留信',kind='user_statement',actor='小禾',at=100)
                store.append(event)
                adapter=Baseline(store,Path(td)/'backend',embed=lambda texts:[[1.,0.] for _ in texts])
                adapter.retain([event]);adapter.flush()
                evidence=adapter.recall('小禾 忙 留信')
                self.assertEqual(evidence[0]['source_ids'],['e1'])
                self.assertEqual(evidence[0]['events'],[event])
                store.forget(['e1']);adapter.forget(['e1'])
                self.assertEqual(adapter.recall('小禾 忙 留信'),[])
                adapter.close()
            finally:store.close()

    def test_context_budget_does_not_truncate_provenance(self):
        from memory_lab.adapters import evidence_budget
        rows=[{'source_ids':['a'],'text':'很多内容'*3000,'events':[{'id':'a','text':'原文'}]},
              {'source_ids':['b'],'text':'简短','events':[{'id':'b','text':'原文'}]}]
        selected=evidence_budget(rows,100)
        self.assertEqual(selected,[rows[1]])
