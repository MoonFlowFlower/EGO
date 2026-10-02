import json
import tempfile
import unittest
from pathlib import Path
from memory_lab.core import Store, World


class ReliabilityTests(unittest.TestCase):
    def test_clone_retry_after_lost_ack_uses_fresh_native_target(self):
        from memory_lab.adapters import Hindsight
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            a=Hindsight(s,Path(td)/'origin',bank='source');targets=[]
            a.flush=lambda **kw:None
            def api(path,*args):
                if path.startswith('/clone'):
                    targets.append(path)
                    if len(targets)==1:raise KeyboardInterrupt('clone completed; acknowledgement lost')
            a.api=api
            try:
                with self.assertRaises(KeyboardInterrupt):a.snapshot(Path(td)/'target')
                a.snapshot(Path(td)/'target')
                self.assertNotEqual(targets[0],targets[1])
            finally:s.close()

    def test_delete_outbox_keeps_transitive_ids_after_restart(self):
        from memory_lab.runner import retain
        class Backend:
            def __init__(self):self.deleted=[]
            def forget(self,ids):self.deleted.extend(ids)
            def flush(self):pass
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'store.sqlite';s=Store(path)
            s.append(dict(id='a',text='old',kind='user_statement',actor='u',at=1))
            s.append(dict(id='b',text='derived',kind='inference',actor='pet',at=2,source_ids=['a']))
            s.mark_indexed(['a','b']);s.forget(['a']);s.close()
            s=Store(path);backend=Backend()
            try:
                retain(s,backend,[])
                self.assertEqual(set(backend.deleted),{'a','b'})
                self.assertEqual(s.pending_deletions(),[])
            finally:s.close()

    def test_after_commit_crash_preserves_one_step_and_active_commitment_completion(self):
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                s.append(dict(id='promise',text='提醒',kind='user_statement',actor='u',at=1))
                s.set_commitment('c','promise','active',2)
                World(s,dict(now=2,places={},inventory=[],hunger=0,energy=50))
                action={'type':'contact','text':'约定的提醒','commitment_id':'c','evidence_ids':['promise']}
                def crash(point):
                    if point=='after_commit':raise RuntimeError('power loss')
                with self.assertRaises(RuntimeError):s.commit_step(action,'0-0','result',{'action':action,'done':True},{'id':'r'},dict(phase=0,step=0),fault=crash)
                s.commit_step(action,'0-0','result',{'action':action,'done':True},{'id':'r'},dict(phase=0,step=0))
                self.assertEqual(len(World(s).state['contacts']),1)
                self.assertEqual(s.commitments()[0]['status'],'completed')
                self.assertEqual(len([e for e in s.events() if e['kind']=='action_result']),1)
            finally:s.close()

    def test_explicit_correction_invalidates_only_related_learning(self):
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                s.append(dict(id='old',text='喜欢咖啡',kind='inference',actor='pet',at=1))
                s.add_lesson('coffee','送咖啡',['old'])
                s.append(dict(id='new',text='用户纠正：我不喝咖啡',kind='user_statement',actor='u',at=2,supersedes=['old']))
                self.assertFalse(s.source_exists('old'))
                self.assertTrue(s.source_exists('new'))
                self.assertEqual(s.lessons(),[])
            finally:s.close()

    def test_step_rollback_and_recovery_do_not_repeat_side_effect(self):
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                s.append(dict(id='teach',text='请自己吃饭',kind='user_statement',actor='u',at=1))
                w=World(s,dict(now=1,places={},inventory=['米饭'],edible=['米饭'],hunger=90,energy=20))
                action={'type':'eat','target':'米饭','evidence_ids':['teach']}
                def crash(point):
                    if point=='before_commit':raise RuntimeError('injected crash')
                with self.assertRaises(RuntimeError):
                    s.commit_step(action,'0-0','meal',{'action':action,'done':True},{'id':'model-1'},dict(phase=0,step=0),fault=crash)
                self.assertEqual(World(s).state['inventory'],['米饭'])
                self.assertEqual(s.steps(),[])
                first=s.commit_step(action,'0-0','meal',{'action':action,'done':True},{'id':'model-1'},dict(phase=0,step=0))
                second=s.commit_step(action,'0-0','meal',{'action':action,'done':True},{'id':'model-1'},dict(phase=0,step=0))
                self.assertEqual(first,second)
                self.assertEqual(World(s).state['hunger'],0)
                self.assertEqual(len(s.steps()),1)
                self.assertEqual([x['id'] for x in s.pending_events()],['teach','meal'])
                s.mark_indexed(['teach','meal'])
                self.assertEqual(s.pending_events(),[])
            finally:s.close()

    def test_lesson_dependency_invalidation_and_old_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite')
            try:
                for key in ['a','b']:
                    s.append(dict(id=key,text=key,kind='user_statement',actor=key,at=1))
                s.add_lesson('one','来自a',['a'])
                s.add_lesson('two','由one推导',['b'],dependencies=['one'])
                s.add_lesson('independent','只来自b',['b'])
                old=s.export();s.forget(['a'])
                self.assertEqual([x['id'] for x in s.lessons()],['independent'])
                with self.assertRaises(ValueError):s.validate_snapshot(old)
                self.assertNotIn('a',[x['id'] for x in s.pending_events()])
            finally:s.close()

    def test_index_failure_is_recoverable_even_when_raw_event_exists(self):
        from memory_lab.runner import retain
        class Adapter:
            def __init__(self):self.index=set();self.fail=True
            def write_status(self,ids):return {i:('complete' if i in self.index else 'absent') for i in ids}
            def retain(self,events):
                if self.fail:raise RuntimeError('index interruption')
                self.index.update(e['id'] for e in events)
            def flush(self):pass
        with tempfile.TemporaryDirectory() as td:
            s=Store(Path(td)/'raw.sqlite');a=Adapter()
            try:
                e=dict(id='e',text='约定',kind='user_statement',actor='u',at=1)
                with self.assertRaises(RuntimeError):retain(s,a,[e])
                a.fail=False;retain(s,a,[e])
                self.assertEqual(a.index,{'e'})
                self.assertEqual(s.pending_events(),[])
            finally:s.close()

    def test_runner_resumes_after_committed_action_before_indexing(self):
        from unittest.mock import patch
        from memory_lab.adapters import Baseline
        from memory_lab.runner import setup_base,run_episode
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'run'
            case={'id':'recovery','split':'development','family':6,'user':'u','history':[],
                  'commitments':[],'initial':dict(now=1,places={},inventory=['饭'],edible=['饭'],hunger=80,energy=20),
                  'phases':[dict(now=2,notice='吃饭',max_steps=1,expect={'hunger':0})]}
            def adapter(arm,store,path):return Baseline(store,path,embed=lambda texts:[[1.,0.] for t in texts])
            calls=[]
            def model(*args,**kw):
                calls.append(1)
                return {'id':'fixture','choices':[{'message':{'content':json.dumps({'action':{'type':'eat','target':'饭'},'done':True})}}]}
            original=Baseline.retain
            def fail(self,events):
                if any(e['kind']=='action_result' for e in events):raise RuntimeError('injected indexing crash')
                return original(self,events)
            with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
                base=setup_base(case,'baseline',root)
                with patch.object(Baseline,'retain',fail),self.assertRaises(RuntimeError):
                    run_episode(case,'baseline',1,root,base,model_call=model)
                result=run_episode(case,'baseline',1,root,base,model_call=model)
            self.assertTrue(result['success'])
            self.assertEqual(len(calls),1)
            saved=json.loads(next(root.glob('episodes/*/final-store.json')).read_text(encoding='utf-8'))
            self.assertEqual(len(saved['receipts']),1)
