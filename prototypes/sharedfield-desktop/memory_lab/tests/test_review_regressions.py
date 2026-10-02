import tempfile
import unittest
from pathlib import Path

class ReviewRegressions(unittest.TestCase):
    def test_deleted_derivation_closure_reaches_native_index(self):
        from memory_lab.core import Store
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                for key,sources in [('a',[]),('b',['a']),('c',['b']),('other',[])]:
                    s.append(dict(id=key,text=key,kind='action_result',actor='env',at=1,source_ids=sources))
                self.assertEqual(set(s.forget(['a'])),{'a','b','c'})
            finally:s.close()

    def test_partial_sources_cannot_launder_deleted_text(self):
        from memory_lab.adapters import Adapter
        from memory_lab.core import Store
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                s.append(dict(id='valid',text='还在',kind='user_statement',actor='u',at=1))
                a=Adapter(s,Path(td)/'index')
                self.assertIsNone(a.evidence(['deleted','valid'],'SECRET and 还在'))
            finally:s.close()

    def test_receipt_does_not_reveal_uninspected_location(self):
        from memory_lab.core import Store,World
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                w=World(s,{'now':1,'places':{'a':['米糕'],'b':['秘密物品']},'inventory':[],'hunger':80,'energy':50})
                w.act({'type':'inspect','target':'a'},'inspect')
                receipt=w.act({'type':'take','target':'米糕','place':'a'},'take')
                self.assertNotIn('秘密物品',str(receipt))
                self.assertEqual(w.state['places']['b'],['秘密物品'])
            finally:s.close()

    def test_ace_feedback_does_not_get_private_world_locations(self):
        from memory_lab.growth import learning_input
        case={'id':'c','split':'development','phases':[]}
        row={'action':{'type':'wait'},'receipt':{'ok':True},
             'final_state':{'places':{'b':['SECRET']}},'observation_after':{'hunger':80,'places':['b']}}
        self.assertNotIn('SECRET',learning_input(case,[row],[]))

    def test_cost_filter_is_structured_and_run_split_specific(self):
        from memory_lab.report import attributable_calls
        rows=[{'context':{'run_id':'r1','split':'heldout','condition':'memory','arm':'baseline'}},
              {'context':{'run_id':'r2','split':'heldout','condition':'memory','arm':'baseline'}},
              {'context':{'run_id':'r1','split':'development','condition':'memory','arm':'baseline'}}]
        self.assertEqual(attributable_calls(rows,'r1','baseline','memory'),rows[:1])

    def test_export_then_reopen_preserves_post_export_changes(self):
        from memory_lab.core import Store,World
        from memory_lab.runner import reopen_store
        with tempfile.TemporaryDirectory() as td:
            original=Store(Path(td)/'raw.sqlite')
            World(original,{'now':1,'places':{},'inventory':[],'hunger':80,'energy':20})
            restored=Store(Path(td)/'restored.sqlite');restored.restore(original.export());original.close()
            w=World(restored);w.act({'type':'sleep'},'sleep-after-export')
            reopened=reopen_store(restored)
            try:self.assertEqual(World(reopened).state['energy'],100)
            finally:reopened.close()
