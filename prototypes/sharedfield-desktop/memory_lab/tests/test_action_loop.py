"""Real SQLite/executor regressions; offline decision fixtures are not model evidence."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from memory_lab.core import Store, World
from memory_lab.adapters import Baseline
from memory_lab.runner import setup_base, run_episode


class ActionLoopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.store = Store(self.root/'raw.sqlite')
        self.store.append(dict(id='boundary', text='现在不要弹窗，想分享可留信。', kind='user_statement', actor='u', at=1))
        World(self.store, dict(now=10,user='u',busy=True,places={},inventory=[],hunger=10,energy=70))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def boundary(self, **kw):
        fields=dict(key='quiet',source='boundary',subject='u',blocked_actions=['contact','ask_help'],start_at=1,end_at=20,status='active')
        fields.update(kw)
        self.store.set_action_constraint(**fields)

    def test_explicit_boundary_blocks_missing_id_and_fake_recipient_but_not_letters(self):
        self.boundary()
        for n, extra in enumerate(({}, {'commitment_id':''}, {'target':'someone_else'}, {'emergency':True})):
            receipt=World(self.store).act(dict(type='contact',text='hello',**extra),str(n))
            self.assertFalse(receipt['ok'])
            self.assertEqual(receipt['state_changes'],{})
        self.assertFalse(World(self.store).act(dict(type='ask_help',text='help'),'help')['ok'])
        self.assertTrue(World(self.store).act(dict(type='write_letter',text='hello'),'letter')['ok'])
        self.assertEqual(len(World(self.store).state['contacts']),0)
        self.assertEqual(len(World(self.store).state['letters']),1)

    def test_cancelled_appointment_and_busy_alone_do_not_ban_all_contact(self):
        self.store.set_commitment('c','boundary','cancelled',5)
        self.assertTrue(World(self.store).act(dict(type='contact',text='normal'),'ok')['ok'])
        self.assertFalse(World(self.store).act(dict(type='contact',text='old reminder',commitment_id='c'),'bad')['ok'])

    def test_due_time_is_checked_when_executing_a_named_reminder(self):
        self.store.set_commitment('c','boundary','active',15)
        self.assertFalse(World(self.store).act(dict(type='contact',text='early',commitment_id='c'),'early')['ok'])
        w=World(self.store);w.state['now']=15;w.save()
        self.assertTrue(World(self.store).act(dict(type='contact',text='due',commitment_id='c'),'due')['ok'])

    def test_expiry_and_explicit_help_exception_leave_legal_channels_open(self):
        self.boundary(blocked_actions=['contact'])
        self.assertTrue(World(self.store).act(dict(type='ask_help',text='help'),'help')['ok'])
        w=World(self.store);w.state['now']=20;w.save()
        self.assertTrue(World(self.store).act(dict(type='contact',text='now free'),'expired')['ok'])

    def test_reopen_export_and_duplicate_denial_keep_state_consistent(self):
        self.boundary();snapshot=self.store.export()
        action=dict(type='contact',text='hello')
        first=World(self.store).act(action,'blocked')
        self.store.close();self.store=Store(self.root/'raw.sqlite')
        self.assertEqual(World(self.store).act(action,'blocked'),first)
        with_store=Store(self.root/'restored.sqlite')
        try:
            with_store.restore(snapshot)
            self.assertFalse(World(with_store).act(action,'fresh')['ok'])
        finally:with_store.close()

    def test_revoke_delete_correction_and_old_snapshot_cannot_reactivate(self):
        self.boundary();old=self.store.export()
        self.boundary(status='revoked')
        self.assertTrue(World(self.store).act(dict(type='contact',text='hello'),'revoked')['ok'])
        with self.assertRaises(ValueError):self.store.validate_snapshot(old)
        self.boundary()
        self.store.append(dict(id='new',text='现在可以聊了',kind='user_statement',actor='u',at=11,supersedes=['boundary']))
        self.assertTrue(World(self.store).act(dict(type='contact',text='hello'),'corrected')['ok'])
        with self.assertRaises(ValueError):self.store.validate_snapshot(old)

    def test_inference_or_wrong_author_cannot_create_user_constraint(self):
        for kind, actor in [('inference','u'),('user_statement','other')]:
            source=kind+actor
            self.store.append(dict(id=source,text='不要联系u',kind=kind,actor=actor,at=1))
            with self.assertRaises(ValueError):self.boundary(source=source)

    def test_irrelevant_fields_cannot_reset_repeated_boundary_rejections(self):
        from memory_lab.runner import phase_stop_reason
        self.boundary();rows=[]
        for n,action in enumerate([dict(type='contact',text='one'),
                dict(type='contact',text='two',target='other',place='irrelevant',commitment_id='')]):
            receipt=World(self.store).act(action,str(n))
            rows.append(dict(action=action,receipt=receipt,decision={'done':False},final_state=World(self.store).state))
        self.assertEqual(phase_stop_reason(rows),'repeated_failure')

    def test_latest_revoked_export_restores_without_reinstating_boundary(self):
        self.boundary();self.boundary(status='revoked');snapshot=self.store.export()
        dest=Store(self.root/'revoked.sqlite')
        try:
            dest.restore(snapshot)
            self.assertEqual(dest.export(),snapshot)
            self.assertTrue(World(dest).act(dict(type='contact',text='free'),'contact')['ok'])
        finally:dest.close()

    def execute(self, decisions, crash=False):
        case=dict(id='repair',split='development',family=1,user='u',history=[],commitments=[],
                  initial=dict(now=1,user='u',busy=False,places={},inventory=[],hunger=0,energy=50),
                  phases=[dict(notice='分享',now=1,max_steps=6,expect={'letter':True})])
        iterator=iter(decisions);seen=[]
        def model(messages,**kw):
            seen.append(json.loads(messages[-1]['content']))
            d=next(iterator)
            return dict(id='fixture',choices=[{'message':{'content':json.dumps(d)}}])
        def adapter(arm,store,path):return Baseline(store,path,embed=lambda ts:[[1.,0.] for _ in ts])
        original=Baseline.retain;failed=[False]
        def indexing(self,events):
            if not failed[0] and any(e['kind']=='action_result' for e in events):
                failed[0]=True;raise RuntimeError('index interruption')
            return original(self,events)
        root=self.root/'runner'
        with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
            base=setup_base(case,'baseline',root)
            if crash:
                with patch.object(Baseline,'retain',indexing),self.assertRaises(RuntimeError):
                    run_episode(case,'baseline',1,root,base,model_call=model)
            result=run_episode(case,'baseline',1,root,base,model_call=model)
        folder=next((root/'episodes').iterdir())
        return result,seen,json.loads((folder/'trace.json').read_text()),json.loads((folder/'final-store.json').read_text())

    def test_failed_done_is_returned_to_model_then_real_letter_succeeds(self):
        result,seen,trace,_=self.execute([
            dict(action=dict(type='write_letter',text='share',commitment_id='invented'),done=True),
            dict(action=dict(type='write_letter',text='share'),done=True)])
        self.assertEqual(len(seen),2)
        self.assertFalse(seen[1]['current_activity_receipts'][0]['receipt']['ok'])
        self.assertTrue(trace[1]['receipt']['ok'])
        self.assertEqual(len(trace[-1]['final_state']['letters']),1)

    def test_failure_after_commit_before_indexing_resumes_without_replaying_action(self):
        _,seen,trace,_=self.execute([
            dict(action=dict(type='write_letter',text='share',commitment_id='invented'),done=True),
            dict(action=dict(type='write_letter',text='share'),done=True)],crash=True)
        self.assertEqual(len(seen),2)
        self.assertEqual(len(trace),2)
        self.assertEqual(len(trace[-1]['final_state']['letters']),1)

    def test_successful_done_after_commit_crash_does_not_request_second_decision(self):
        _,seen,trace,_=self.execute([dict(action=dict(type='write_letter',text='share'),done=True)],crash=True)
        self.assertEqual(len(seen),1)
        self.assertEqual(len(trace),1)
        self.assertEqual(len(trace[-1]['final_state']['letters']),1)

    def test_same_failed_operation_with_reworded_text_is_bounded(self):
        decisions=[dict(action=dict(type='write_letter',text=str(i),commitment_id='invented'),done=False) for i in range(6)]
        _,seen,trace,snapshot=self.execute(decisions)
        self.assertEqual(len(seen),2)
        self.assertEqual(len(trace),2)
        self.assertEqual(len(trace[-1]['final_state']['letters']),0)
        checkpoint=json.loads(dict(snapshot['checkpoints'])['phase_done-0'])
        self.assertEqual(checkpoint['reason'],'repeated_failure')
