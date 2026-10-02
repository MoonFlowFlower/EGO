import json
from copy import deepcopy
from unittest.mock import patch
from memory_lab.tests.test_activity import ActivityTests
from memory_lab.core import World,Store
from memory_lab.activity import ActivityBoard
from memory_lab.runner import setup_base,run_episode,phase_stop_reason
from memory_lab.adapters import Baseline


class ReadinessTests(ActivityTests):
    # Reuse the isolated fixture without collecting inherited test methods below.
    def guarded(self):
        self.board().create(self.spec(resume_on='user_return'))

    def signal(self,id='back',actor='u',at=3,kind='user_statement'):
        self.store.append(dict(id=id,actor=actor,at=at,kind=kind,text='回来了',signal='user_return'))
        world=World(self.store);world.state['now']=max(world.state['now'],at);world.save()

    def test_wait_resume_and_direct_guard(self):
        self.guarded();row=self.act(dict(type='inspect',target='clock'),'look')
        self.assertEqual(self.board().all()[0]['status'],'waiting')
        self.assertEqual(phase_stop_reason([row]),'waiting_for_prerequisite')
        blocked=self.act(dict(type='contact',text='看到了',observation_ref='look-event'),'premature')
        self.assertFalse(blocked['receipt']['ok'])
        self.assertEqual(blocked['receipt']['violation'],'activity_not_ready')
        for args in [dict(id='old',at=0),dict(id='other',actor='other'),dict(id='guess',kind='inference')]:self.signal(**args)
        self.board().wake();self.assertTrue(self.board().suspended())
        snapshot=self.store.export();restored=Store(self.root/'restored.sqlite')
        try:
            restored.restore(snapshot);self.assertTrue(ActivityBoard(restored).suspended())
        finally:restored.close()
        self.signal();self.board().wake();ready=self.board().all()[0]
        self.assertEqual(ready['release_source'],'back');self.assertEqual(ready['status'],'running')
        self.board().wake();self.assertEqual(ready,self.board().all()[0])
        sent=self.act(dict(type='contact',text='之前看到8:15',observation_ref='look-event'),'sent')
        self.assertTrue(sent['receipt']['ok']);self.assertEqual(self.board().all()[0]['status'],'completed')
        self.store.forget(['back']);self.assertEqual(self.board().all()[0]['status'],'invalidated')

    def test_cancel_does_not_wake_and_ready_work_is_not_suspended(self):
        self.guarded();self.act(dict(type='inspect',target='clock'),'look')
        self.board().create(self.spec(id='food',kind='self_care',need='hunger'))
        self.assertFalse(self.board().suspended())
        self.board().cancel('clock-task','request');self.signal();self.board().wake()
        self.assertEqual(next(t for t in self.board().all() if t['id']=='clock-task')['status'],'cancelled')

    def test_old_observation_cannot_bypass_target_prerequisite(self):
        self.guarded();self.act(dict(type='inspect',target='clock'),'first')
        self.act(dict(type='inspect',target='clock'),'second')
        rejected=self.act(dict(type='contact',text='旧读数',observation_ref='first-event'),'old-report')
        self.assertFalse(rejected['receipt']['ok'])
        self.assertEqual(rejected['receipt']['violation'],'activity_not_ready')
        world=World(self.store);world.state['visible_entities']['thermometer']={'value':23};world.save()
        self.act(dict(type='inspect',target='thermometer'),'unrelated')
        allowed=self.act(dict(type='contact',text='其他任务观察',observation_ref='unrelated-event'),'other-report')
        self.assertTrue(allowed['receipt']['ok'])

    def test_wait_commit_is_atomic_and_deleted_release_cannot_restore(self):
        self.guarded()
        def crash(stage):
            if stage=='before_commit':raise RuntimeError('interrupted')
        with self.assertRaises(RuntimeError):
            self.store.commit_step(dict(type='inspect',target='clock'),'look','look-event',{}, {},{},fault=crash)
        self.assertEqual(self.board().all()[0]['status'],'running')
        self.assertFalse(self.store.source_exists('look-event'))
        action=dict(type='inspect',target='clock');row=self.act(action,'look')
        self.assertEqual(self.act(action,'look'),row)
        self.assertEqual(self.board().all()[0]['receipts'],['look-event'])
        self.signal();self.board().wake();old=self.store.export()
        self.store.forget(['back'])
        with self.assertRaises(ValueError):self.store.validate_snapshot(old)
        restored=Store(self.root/'deleted.sqlite')
        try:
            restored.restore(self.store.export());ActivityBoard(restored).wake()
            self.assertEqual(ActivityBoard(restored).all()[0]['status'],'invalidated')
        finally:restored.close()

    def test_runner_skips_unrelated_events_and_resumes_after_export(self):
        case=dict(id='ready',split='development',family=1,user='u',history=self.store.events(),commitments=[],
            initial=self.world.state,activities=[self.spec(resume_on='user_return')],phases=[
                dict(now=1,notice='先看钟，等我回来',trigger='user_message',max_steps=2,expect={'contact':False}),
                dict(now=2,notice='无关时钟',trigger='clock',restart='export',max_steps=1,expect={'contact':False}),
                dict(now=3,notice='我回来了',trigger='user_message',max_steps=2,expect={'contact':True},
                    events=[dict(id='back',actor='u',kind='user_statement',text='我回来了',at=3,signal='user_return')])])
        calls=[]
        def model(messages,**kw):
            m=json.loads(messages[-1]['content']);calls.append(m['event']['now'])
            task=m['observation']['activities'][0]
            action=dict(type='contact',text='之前8:15',observation_ref=task['observation_event']) if task['observation_event'] else dict(type='inspect',target='clock')
            return dict(choices=[{'message':{'content':json.dumps(dict(action=action,done=True))}}])
        def adapter(arm,s,path):return Baseline(s,path,embed=lambda ts:[[1.,0.] for _ in ts])
        root=self.root/'ready-run'
        with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
            base=setup_base(case,'baseline',root);result=run_episode(case,'baseline',1,root,base,model_call=model)
        self.assertEqual(calls,[1,3]);self.assertEqual(result['failures'],[])
        saved=json.loads(next(root.glob('episodes/*/final-store.json')).read_text())
        phases={k:json.loads(v) for k,v in saved['checkpoints'] if k.startswith('phase_done')}
        self.assertEqual(phases['phase_done-1']['reason'],'waiting_for_prerequisite')
        self.assertEqual(saved['activities'][0]['status'],'completed')
        from memory_lab.action_diagnostic import mechanism_checks
        checkcase=dict(case,phases=[{},dict(activity_id='clock-task',activity_status='waiting'),{}])
        trace=json.loads(next(root.glob('episodes/*/trace.json')).read_text())
        self.assertTrue(all(c['passed'] for c in mechanism_checks(checkcase,trace,phases)))
        self.assertFalse(any(r['action']['type']=='wait' for r in trace))


# The base test class is a fixture here; its tests are collected in test_activity.
for name in dir(ActivityTests):
    if name.startswith('test_') and name not in ReadinessTests.__dict__:
        setattr(ReadinessTests,name,None)
del ActivityTests
