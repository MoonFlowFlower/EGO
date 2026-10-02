from contextlib import ExitStack
import json,tempfile,threading,unittest
from copy import deepcopy
from switchlab.shared.core import SharedCore
from switchlab.shared.service import SharedService
from tests.test_shared_service import SharedFixture

class IntentionTests(unittest.TestCase):
    def prepare(self):
        c=SharedCore();c.apply('agent_step',{})
        source=c.apply('message',{'text':'你接下来准备做什么？'})['id']
        c.apply('interpret',{'source':source,'packet':{'reports':[],'request':{'kind':'none'}}})
        return c,deepcopy(c.state['pending'])
    def test_same_information_does_not_manufacture_new_plan_history(self):
        c=SharedCore();before=c.mind.snapshot();a=c.mind.plan();b=c.mind.plan()
        self.assertEqual(a['id'],b['id'],'a read of an unchanged plan was treated as new thinking')
    def test_commitment_cannot_say_calibrate_when_selected_move(self):
        c,p=self.prepare();self.assertEqual(c.mind.focus['action']['kind'],'move')
        c.apply('expression',{'state_id':p['state_id'],'speech':'刚才的收获让我挺好奇。我打算先做一次校准，然后再决定往哪走。'})
        message=c.state['messages'][-1]
        self.assertNotIn('我打算先做一次校准',message['text'],'unselected action presented as own actual next plan')
        self.assertIn('好奇',message['text']);self.assertTrue(message.get('speech_guard',{}).get('corrected'))
        self.assertEqual(message['intention']['action'],c.mind.focus['action'])
        e=c.apply('agent_step',{})['result'];self.assertEqual(e['transition']['action'],message['intention']['action'])
    def test_unselected_alternative_is_not_reported_as_undecided(self):
        c,p=self.prepare();c.apply('expression',{'state_id':p['state_id'],'speech':'两个地方都值得看，我还没完全定下来。'})
        self.assertNotIn('还没完全定下来',c.state['messages'][-1]['text'])
    def test_historical_action_and_hypothetical_are_not_claimed_next_action(self):
        c,p=self.prepare();raw='刚才我做过校准。以后遇到问题，可以考虑先检查工具。'
        c.apply('expression',{'state_id':p['state_id'],'speech':raw})
        self.assertEqual(c.state['messages'][-1]['text'],raw)
    def test_users_undecided_state_is_not_rewritten_as_my_action(self):
        c,p=self.prepare();raw='你还没完全决定先去哪里吗？我可以先听听你的想法。'
        c.apply('expression',{'state_id':p['state_id'],'speech':raw})
        self.assertEqual(c.state['messages'][-1]['text'],raw)
    def test_intention_receipt_records_real_attempt_not_just_expression(self):
        c,p=self.prepare();c.apply('expression',{'state_id':p['state_id'],'speech':'我们看看那边。'})
        self.assertEqual(c.state['messages'][-1]['intention']['status'],'selected_not_executed')
        event=c.apply('agent_step',{})
        receipt=c.state['messages'][-1]['intention']
        self.assertEqual(receipt['status'],'executed');self.assertEqual(receipt['result_event'],event['id'])
        self.assertEqual(receipt['success'],event['result']['transition']['success'])
    def test_false_returned_decision_id_rejected_before_submit(self):
        c,p=self.prepare()
        with self.assertRaises(ValueError):c.apply('expression',{'state_id':p['state_id'],'decision_id':'FORGED','speech':'你好'})
    def test_express_context_separates_selected_plan_from_candidate_scores(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as cleanup:
            s=SharedService(d);cleanup.callback(s.close);s.set_options({'language_mode':'manual'});s.submit('想做什么')
            s.run_once();r=s.manual_request;s.accept_manual(r['id'],json.dumps({'reports':[],'request':{'kind':'none'}}));s.run_once()
            c=json.loads(s.manual_request['messages'][-1]['content'])['context']
            self.assertIn('intention_contract',c,'no selected action contract at language boundary')
            self.assertNotIn('candidates',c['state_report']['report']['focus'],'renderer sees undifferentiated scoring table')

class LiveContinuityTests(unittest.TestCase):
    def make(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=SharedFixture();s=SharedService(t.name,provider=p);self.addCleanup(s.close)
        s.set_options({'language_mode':'api'});return s,p
    def test_player_move_during_response_keeps_answer_without_paid_retry(self):
        s,p=self.make();s.submit('你现在想做什么？');s.run_once()
        old=p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(3);return old(m)
        p.complete=slow;t=threading.Thread(target=s.run_once);t.start();self.assertTrue(entered.wait(1))
        s.command('player_action',{'action':{'kind':'survey'}});release.set();t.join(4)
        self.assertEqual(len(p.calls),2);self.assertEqual(s.core.state['messages'][-1]['role'],'assistant','game input silently discarded paid answer')
        self.assertEqual(s.core.state['messages'][-1]['temporal_status'],'earlier_snapshot')
        self.assertFalse(s.run_once());self.assertEqual(len(p.calls),2)
    def test_waiting_does_not_fill_event_log_or_spend_action_budget(self):
        s,p=self.make();s.command('activity',{'mode':'wait'});s.start_auto(8);s.run_once(force=True)
        n=len(s.core.events);tick=s.core.world.tick
        for _ in range(10):s.run_once()
        self.assertEqual(len(s.core.events),n);self.assertEqual(s.core.world.tick,tick);self.assertEqual(p.calls,[])
        self.assertEqual(s.auto_remaining,8)
    def test_pause_still_discards_inflight_expression(self):
        s,p=self.make();s.submit('你想做什么');s.run_once()
        old=p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(3);return old(m)
        p.complete=slow;t=threading.Thread(target=s.run_once);t.start();self.assertTrue(entered.wait(1));s.pause();release.set();t.join(4)
        self.assertEqual(len(s.core.state['messages']),1);self.assertFalse(s.run_once())

    def test_joint_invitation_and_wait_do_not_erase_the_current_question(self):
        for kind,payload in [('invite',{}),('activity',{'mode':'wait'})]:
            with self.subTest(kind=kind):
                s,p=self.make();s.submit('你现在想做什么？');s.run_once()
                old=p.complete;entered=threading.Event();release=threading.Event()
                def slow(m):entered.set();release.wait(3);return old(m)
                p.complete=slow;t=threading.Thread(target=s.run_once);t.start();self.assertTrue(entered.wait(1))
                s.command(kind,payload);release.set();t.join(4)
                self.assertEqual(s.core.state['messages'][-1]['role'],'assistant')
                self.assertEqual(s.core.state['messages'][-1]['temporal_status'],'earlier_snapshot')
                self.assertEqual(len(p.calls),2);self.assertFalse(s.run_once())
