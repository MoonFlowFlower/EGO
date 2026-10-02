import json,tempfile,threading,unittest,time
from copy import deepcopy
from switchlab.studio.provider import DEFAULT
try:
    from switchlab.shared.service import SharedService
except ImportError:SharedService=None

class SharedFixture:
    """Explicit deterministic test transport, NEVER evidence of real model quality."""
    def __init__(self):
        self.config={**DEFAULT,'mode':'api','model':'SHARED_TEST_FIXTURE','network_consent':True};self.calls=[]
    def public(self):return {**self.config,'key_present':False,'local_endpoint':True}
    def complete(self,messages):
        d=json.loads(messages[-1]['content']);self.calls.append(d['phase'])
        if d['phase']=='interpret':packet={'reports':[],'request':{'kind':'none'}}
        else:packet={'state_id':d['state_id'],'speech':'【TEST_FIXTURE】表达真实数值快照，仅用于接口测试。'}
        return {'packet':packet,'model':'SHARED_TEST_FIXTURE','usage':{'input_tokens':10,'output_tokens':10}}

class SharedServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(SharedService,'shared main service not implemented')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.p=SharedFixture();self.s=SharedService(self.tmp.name,provider=self.p);self.addCleanup(self.s.close)
    def test_default_is_zero_api_local_state_report(self):
        self.s.submit('你在想什么');self.assertTrue(self.s.run_once())
        self.assertEqual(self.p.calls,[]);self.assertEqual(len(self.s.core.state['messages']),2)
    def test_two_stage_state_precedes_expression(self):
        self.s.set_options({'language_mode':'api'});self.s.submit('你有什么感觉')
        self.s.run_once();self.assertEqual(self.p.calls,['interpret']);self.assertIsNotNone(self.s.core.state['pending'])
        self.s.run_once();self.assertEqual(self.p.calls,['interpret','express'])
        self.assertEqual(self.s.core.world.tick,0)
    def test_no_message_autonomous_local_steps_and_pause(self):
        self.s.start_auto(4)
        for _ in range(4):self.s.run_once(force=True)
        self.assertEqual(self.s.core.world.tick,4);self.assertEqual(self.p.calls,[])
        self.assertFalse(self.s.run_once());self.s.start_auto(4);self.s.pause();self.assertFalse(self.s.run_once())
    def test_restored_life_is_not_enabled(self):
        self.s.run_once(force=True);c=self.s.core.checkpoint();self.s.close()
        other=SharedService(self.tmp.name,provider=self.p);self.addCleanup(other.close)
        self.assertEqual(c,other.core.checkpoint());self.assertFalse(other.run_once())
    def test_game_action_during_interpretation_preserves_paid_question(self):
        self.s.set_options({'language_mode':'api'});self.s.submit('看这里')
        old=self.p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(3);return old(m)
        self.p.complete=slow;t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(1))
        self.s.command('player_action',{'action':{'kind':'survey'}});release.set();t.join(4)
        self.assertIsNotNone(self.s.core.state['pending']);self.assertEqual(len(self.s.core.state['messages']),1)
        self.s.run_once();self.assertEqual(self.p.calls,['interpret','express'])
        self.assertEqual(self.s.core.state['messages'][-1]['role'],'assistant')
    def test_manual_uses_same_kernel_without_synthetic_reply(self):
        self.s.set_options({'language_mode':'manual'});self.s.submit('你想做什么');self.s.run_once()
        r=self.s.manual_request;self.s.accept_manual(r['id'],json.dumps({'reports':[],'request':{'kind':'none'}}))
        self.s.run_once();r=self.s.manual_request
        self.s.accept_manual(r['id'],json.dumps({'state_id':r['state_id'],'speech':'明确手动提供的测试文本'}))
        self.assertEqual(self.s.core.state['messages'][-1]['text'],'明确手动提供的测试文本');self.assertEqual(self.p.calls,[])
    def test_lack_of_two_call_budget_stops_before_network(self):
        self.s.set_options({'language_mode':'api'});self.p.config['max_calls']=1;self.s.submit('测试')
        self.assertFalse(self.s.run_once());self.assertEqual(self.p.calls,[])
    def test_salient_narration_is_opt_in_and_not_idle_timer(self):
        self.s.set_options({'language_mode':'api','narrate':True});self.s.start_auto(1);self.s.run_once(force=True)
        self.s.run_once();self.assertEqual(self.p.calls,['express'])
        count=len(self.p.calls);self.assertFalse(self.s.run_once());self.assertEqual(count,len(self.p.calls))
    def test_no_narration_without_discovery_or_failure(self):
        self.s.set_options({'language_mode':'api','narrate':True});self.s.command('player_action',{'action':{'kind':'rest'}})
        self.assertFalse(self.s.run_once());self.assertEqual(self.p.calls,[])
    def test_save_failure_rolls_back_actual_world(self):
        from unittest.mock import patch
        s=self.s.core.checkpoint()
        with patch('switchlab.studio.service.save_json',side_effect=OSError('disk')):
            with self.assertRaises(ValueError):self.s.command('player_action',{'action':{'kind':'survey'}})
        self.assertEqual(s,self.s.core.checkpoint());self.assertEqual(self.s.auto_remaining,0)
    def test_player_action_does_not_repeat_paid_interpretation(self):
        self.s.set_options({'language_mode':'api'});self.s.submit('观察途中提问')
        old=self.p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(2);return old(m)
        self.p.complete=slow;t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(1))
        self.s.command('player_action',{'action':{'kind':'rest'}});release.set();t.join(3)
        self.assertEqual(self.p.calls,['interpret']);self.assertTrue(self.s.run_once())
        self.assertEqual(self.p.calls,['interpret','express']);self.assertFalse(self.s.run_once())
    def test_protocol_probe_is_two_calls_and_not_experience(self):
        before=self.s.core.mind.snapshot();r=self.s.check_protocol()
        self.assertTrue(r['ok']);self.assertEqual(len(self.p.calls),2);self.assertEqual(before,self.s.core.mind.snapshot())
    def test_single_explicit_grant_can_cover_whole_sandbox_expedition(self):
        self.s.start_auto(600);self.assertEqual(self.s.auto_remaining,600)
        for _ in range(3):self.s.run_once(force=True)
        self.assertEqual(self.s.auto_remaining,597);self.s.pause();self.assertFalse(self.s.run_once())
        for count in (True,0,601):
            with self.assertRaises(ValueError):self.s.start_auto(count)
    def test_auto_does_not_revive_cancelled_paid_question(self):
        self.s.set_options({'language_mode':'api'});self.s.submit('暂不回答');self.s.pause();self.s.start_auto(2)
        self.s.run_once(force=False);self.assertEqual(self.p.calls,[]);self.assertEqual(self.s.core.world.tick,1)
