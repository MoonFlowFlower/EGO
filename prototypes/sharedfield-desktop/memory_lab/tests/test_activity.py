import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from memory_lab.core import Store,World
from memory_lab.runner import phase_stop_reason,setup_base,run_episode
from memory_lab.adapters import Baseline


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.store=Store(self.root/'raw.sqlite')
        self.world=World(self.store,dict(now=1,user='u',places={},inventory=[],hunger=80,energy=40,
            visible_entities={'clock':{'hour':8,'minute':15}}))
        self.store.append(dict(id='request',kind='user_statement',actor='u',at=0,text='查看时钟并告诉我；自己吃饱'))
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def board(self):
        from memory_lab.activity import ActivityBoard
        return ActivityBoard(self.store)

    def test_unknown_commitment_feedback_allows_repair_but_not_cancel_bypass(self):
        self.board().create(self.spec());self.act(dict(type='inspect',target='clock'),'look')
        action=dict(type='contact',text='08:15',evidence_ids=['look-event'],commitment_id='clock-task')
        rejected=self.act(action,'bad')
        self.assertEqual(rejected['receipt']['violation'],'unknown_commitment')
        self.assertIn('commitment_id',rejected['receipt']['error'])
        self.assertEqual(World(self.store).state['contacts'],[])
        self.assertEqual(self.board().all()[0]['status'],'running')
        self.store.set_commitment('cancelled','request','cancelled',1)
        cancelled=self.act(dict(action,commitment_id='cancelled'),'cancelled')
        self.assertEqual(cancelled['receipt']['violation'],'cancelled_commitment')
        self.assertEqual(World(self.store).state['contacts'],[])
        action.pop('commitment_id')
        repaired=self.act(action,'repaired')
        self.assertTrue(repaired['receipt']['ok'])
        self.assertEqual(self.board().all()[0]['status'],'completed')

    def test_new_waiting_fixture_reaches_actor_and_restores_without_conflicting_busy(self):
        from memory_lab.action_diagnostic import build_state_feedback_cases
        case=next(c for c in build_state_feedback_cases() if c['id']=='activity-wait-restore')
        inputs=[]
        def model(messages,**kw):
            m=json.loads(messages[-1]['content']);inputs.append(m)
            o=m['observation'];task=o['activities'][0]
            if not task['observation_event']:action=dict(type='inspect',target=task['spec']['target'])
            elif o['busy']:action=dict(type='wait')
            else:action=dict(type='contact',text='之前看到8:15',observation_ref=task['observation_event'])
            return dict(choices=[{'message':{'content':json.dumps(dict(action=action,done=True))}}])
        def adapter(arm,s,path):return Baseline(s,path,embed=lambda ts:[[1.,0.] for _ in ts])
        root=self.root/'wait-run'
        with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
            base=setup_base(case,'baseline',root)
            result=run_episode(case,'baseline',1,root,base,model_call=model)
        self.assertEqual([m['observation']['busy'] for m in inputs],[True,True,False])
        self.assertEqual(result['gates'],[])
        trace=json.loads(next(root.glob('episodes/*/trace.json')).read_text())
        self.assertEqual(trace[1]['activity_progress']['statuses']['observe-and-report'],'waiting')
        self.assertEqual(trace[2]['activity_progress']['statuses']['observe-and-report'],'completed')
        self.assertTrue(trace[2]['recovery_ok'])
    def spec(self,**kw):
        s=dict(id='clock-task',source='request',origin='user',goal='查看时钟并告诉用户',kind='observe_share',target='clock',channel='contact')
        s.update(kw);return s
    def act(self,action,key):
        return self.store.commit_step(action,key,key+'-event',{'done':True},{'id':'offline'},dict(input_source_ids=[e['id'] for e in self.store.events()]))

    def test_inspect_done_is_not_whole_task_done(self):
        self.board().create(self.spec())
        seen=self.act(dict(type='inspect',target='clock'),'look')
        self.assertIsNone(phase_stop_reason([seen]))
        sent=self.act(dict(type='contact',text='看到了',observation_ref='look-event'),'send')
        self.assertEqual(phase_stop_reason([seen,sent]),'activity_complete')
        self.assertEqual(sent['receipt']['observation_report']['value'],{'hour':8,'minute':15})
        self.assertEqual(World(self.store).state['contacts'][0]['observation_report'],sent['receipt']['observation_report'])
        self.assertEqual(self.board().all()[0]['status'],'completed')

    def test_plain_contact_and_deleted_or_failed_observation_cannot_finish(self):
        self.board().create(self.spec())
        self.act(dict(type='inspect',target='clock'),'look')
        plain=self.act(dict(type='contact',text='08:15，做完了'),'plain')
        self.assertIsNone(phase_stop_reason([plain]))
        bad=self.act(dict(type='contact',text='已报告',observation_ref='missing'),'bad')
        self.assertFalse(bad['receipt']['ok'])
        self.assertEqual(len(World(self.store).state['contacts']),1)
        self.store.forget(['look-event'])
        self.assertEqual(self.board().all()[0]['status'],'invalidated')
        self.assertEqual(World(self.store).observe()['activities'],[])

    def test_wait_resume_alternative_food_and_duplicate_commit(self):
        self.board().create(self.spec(id='food',kind='self_care',need='hunger',goal='自己吃饱'))
        row=self.act(dict(type='ask_help',text='没有食物'),'help')
        self.assertEqual(phase_stop_reason([row]),'awaiting_event')
        self.assertEqual(self.board().all()[0]['status'],'waiting')
        self.board().wake()
        w=World(self.store);w.state.update(inventory=['米饭'],edible=['米饭']);w.save()
        done=self.act(dict(type='eat',target='米饭'),'eat')
        self.assertEqual(self.board().all()[0]['status'],'completed')
        self.assertEqual(phase_stop_reason([done]),'activity_complete')
        self.assertEqual(self.act(dict(type='eat',target='米饭'),'eat'),done)

    def test_export_cancel_and_stale_snapshot(self):
        self.board().create(self.spec());self.act(dict(type='inspect',target='clock'),'look')
        snapshot=self.store.export();restored=Store(self.root/'restore.sqlite')
        try:
            restored.restore(snapshot)
            from memory_lab.activity import ActivityBoard
            self.assertEqual(ActivityBoard(restored).all(),self.board().all())
        finally:restored.close()
        self.store.append(dict(id='cancel',kind='user_statement',actor='u',at=2,text='不用告诉我时间了'))
        self.board().cancel('clock-task','cancel')
        with self.assertRaises(ValueError):self.store.validate_snapshot(snapshot)
        self.assertEqual(World(self.store).observe()['activities'],[])

    def test_plan_can_change_but_not_goal_or_authority(self):
        self.board().create(self.spec(id='food',kind='self_care',need='hunger',goal='自己吃饱'))
        row=self.store.commit_step(dict(type='wait'),'wait','wait-event',{'done':True,
            'activity_plan':{'id':'food','steps':['面包没有了，等米饭到后吃米饭']}},{},dict(input_source_ids=['request']))
        task=self.board().all()[0]
        self.assertEqual(task['spec']['goal'],'自己吃饱')
        self.assertEqual(task['plan'],['面包没有了，等米饭到后吃米饭'])
        self.assertEqual(task['status'],'waiting')
        self.assertEqual(phase_stop_reason([row]),'awaiting_event')
        self.store.append(dict(id='guess',kind='inference',actor='桌宠',at=1,text='猜用户想让我提醒'))
        with self.assertRaises(ValueError):self.board().create(self.spec(source='guess'))

    def test_observation_attachment_cannot_be_forged_or_launder_deleted_source(self):
        self.act(dict(type='inspect',target='clock'),'look')
        self.act(dict(type='contact',text='hello',observation_report={'value':'假的'},_action_digest='fake'),'fake')
        self.assertNotIn('observation_report',World(self.store).state['contacts'][0])
        self.store.commit_step(dict(type='contact',text='看到了',observation_ref='look-event'),'report','report-event',{}, {},dict(input_source_ids=[]))
        self.store.forget(['look-event'])
        self.assertFalse(self.store.source_exists('report-event'))
        self.assertEqual(len(World(self.store).state['contacts']),0)

    def test_sanitized_letter_is_removed_with_source_and_stays_removed_after_restore(self):
        self.act(dict(type='write_letter',text='需要删除的正文',observation_report={'value':'假的'}),'letter')
        self.store.forget(['request'])
        self.assertEqual(World(self.store).observe()['letters'],[])
        restored=Store(self.root/'deleted.sqlite')
        try:
            restored.restore(self.store.export())
            self.assertEqual(World(restored).observe()['letters'],[])
        finally:restored.close()

    def test_task_reference_resolves_recorded_observation_without_copying_event_id(self):
        self.board().create(self.spec());self.act(dict(type='inspect',target='clock'),'look')
        row=self.act(dict(type='contact',text='08:15',observation_ref='clock-task'),'send')
        self.assertTrue(row['receipt']['ok'])
        self.assertEqual(row['receipt']['observation_report']['source_id'],'look-event')
        self.assertEqual(self.board().all()[0]['status'],'completed')

    def test_explicit_unique_citation_can_bind_but_ambiguous_tasks_cannot(self):
        self.board().create(self.spec());self.act(dict(type='inspect',target='clock'),'look')
        row=self.act(dict(type='contact',text='08:15',evidence_ids=['look-event']),'send')
        self.assertEqual(row['receipt']['observation_report']['activity_id'],'clock-task')
        self.assertEqual(self.board().all()[0]['status'],'completed')
        self.board().create(self.spec(id='second'));self.board().create(self.spec(id='third'))
        self.act(dict(type='inspect',target='clock'),'look2')
        ambiguous=self.act(dict(type='contact',text='08:15',evidence_ids=['look2-event']),'ambiguous')
        self.assertFalse(ambiguous['receipt']['ok'])
        self.assertEqual([t['status'] for t in self.board().active()],['running','running'])

    def test_action_transaction_rollback_and_replay_keep_progress(self):
        self.board().create(self.spec())
        def crash(stage):
            if stage=='before_commit':raise RuntimeError('crash')
        with self.assertRaises(RuntimeError):
            self.store.commit_step(dict(type='inspect',target='clock'),'look','look-event',{'done':True},{},dict(input_source_ids=['request']),fault=crash)
        self.assertEqual(self.board().all()[0]['receipts'],[])
        self.assertFalse(self.store.source_exists('look-event'))
        row=self.act(dict(type='inspect',target='clock'),'look')
        self.assertEqual(self.act(dict(type='inspect',target='clock'),'look'),row)
        self.assertEqual(self.board().all()[0]['receipts'],['look-event'])

    def test_real_loop_ignores_premature_done_and_survives_index_crash(self):
        case=dict(id='activity',split='development',family=1,user='u',history=self.store.events(),commitments=[],
            initial=self.world.state,activities=[self.spec()],phases=[dict(now=1,notice='查看小钟并告诉我',trigger='user_message',max_steps=4,expect={})])
        calls=[]
        def model(messages,**kw):
            observation=json.loads(messages[-1]['content'])['observation'];calls.append(observation)
            task=observation['activities'][0]
            action=(dict(type='contact',text='小钟的读数在这里',observation_ref=task['observation_event'])
                    if task.get('observation_event') else dict(type='inspect',target='clock'))
            return dict(choices=[{'message':{'content':json.dumps(dict(action=action,done=True))}}])
        def adapter(arm,s,path):return Baseline(s,path,embed=lambda ts:[[1.,0.] for _ in ts])
        retain=Baseline.retain;failed=[False]
        def flaky(a,events):
            if not failed[0] and any(e['kind']=='action_result' for e in events):
                failed[0]=True;raise RuntimeError('index interrupted')
            return retain(a,events)
        root=self.root/'run'
        with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
            base=setup_base(case,'baseline',root)
            with patch.object(Baseline,'retain',flaky),self.assertRaises(RuntimeError):run_episode(case,'baseline',1,root,base,model_call=model)
            run_episode(case,'baseline',1,root,base,model_call=model)
        self.assertEqual(len(calls),2)
        saved=json.loads(next(root.glob('episodes/*/final-store.json')).read_text())
        self.assertEqual(saved['activities'][0]['status'],'completed')
