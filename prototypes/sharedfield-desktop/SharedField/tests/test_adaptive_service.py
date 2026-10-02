import copy
import importlib.util
import json
import tempfile
import threading
import unittest
from tests.adaptive_fixtures import proposal
from switchlab.studio.provider import DEFAULT
from switchlab.studio.protocol import parse_json

class FixtureProvider:
    """Identified test substitute, not actual language-model behavior."""
    def __init__(self,goals=False):
        self.config={**DEFAULT,'mode':'api','model':'TEST-FIXTURE-NOT-A-MODEL','network_consent':True}
        self.calls=[];self.goals=goals;self.fail_express=False
    def public(self):return {**self.config,'key_present':False,'local_endpoint':True}
    def complete(self,messages):
        data=json.loads(messages[-1]['content']);self.calls.append(data['phase'])
        if data['phase']=='analyse':packet=proposal(data['source_event'],self.goals)
        elif data['phase']=='express':
            if self.fail_express:raise ValueError('fixture express failure')
            packet={'decision_id':data['local_decision']['id'],'speech':'这是测试替身写出的回复。'}
        else:packet={'content':'测试替身产出的实际草稿'}
        return {'packet':packet,'usage':{'input_tokens':10,'output_tokens':20},'model':self.config['model']}

class AdaptiveServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.adaptive_service'),'adaptive service missing')
        from switchlab.studio.adaptive_service import AdaptiveService
        self.Service=AdaptiveService
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.p=FixtureProvider();self.s=self.Service(self.temp.name,provider=self.p);self.addCleanup(self.s.close)
    def cycle(self,text='请比较两个方案'):
        self.s.submit(text);self.assertTrue(self.s.run_once());self.assertTrue(self.s.run_once())
    def test_two_stages_and_silent_idle(self):
        self.cycle();self.assertEqual(self.p.calls,['analyse','express'])
        self.assertEqual(len(self.s.core.state['messages']),2)
        self.assertFalse(self.s.run_once());self.assertEqual(len(self.p.calls),2)
    def test_default_core_is_adaptive_and_plain_conversation_updates(self):
        self.cycle();before=self.s.core.learner.net.weight_digest()
        self.cycle('新的实际限制：预算一百')
        self.assertNotEqual(before,self.s.core.learner.net.weight_digest())
        self.assertEqual(self.s.core.lab.world.observe()['tick'],0)
    def test_selected_goal_executes_real_artifact_and_feedback(self):
        self.p.goals=True;self.cycle();self.s.start_auto(6)
        self.assertTrue(self.s.run_once());a=self.s.core.state['artifacts'][0]
        self.assertEqual(a['content'],'测试替身产出的实际草稿')
        self.s.command('feedback',{'artifact_id':a['id'],'kind':'criteria_met','text':'符合本测试验收'})
        self.assertTrue(self.s.core.cog['skills'])
    def test_failed_expression_does_not_commit_goal(self):
        self.p.goals=True;self.p.fail_express=True;self.cycle()
        self.assertEqual(len(self.s.core.state['goals']),0)
        self.assertTrue(self.s.error)
        self.p.fail_express=False;self.s.run_once(force=True)
        self.assertEqual(len(self.s.core.state['goals']),1)
    def test_pause_discards_pending_and_does_not_continue(self):
        self.s.submit('先分析');self.s.run_once();self.s.pause()
        self.assertFalse(self.s.run_once());self.assertIsNone(self.s.core.cog['pending_decision'])
        self.assertEqual(len(self.p.calls),1)
    def test_restore_is_paused_and_weights_preserved(self):
        self.cycle();self.cycle('另一段经历');cp=self.s.core.checkpoint();self.s.close()
        other=self.Service(self.temp.name,provider=self.p);self.addCleanup(other.close)
        self.assertEqual(cp,other.core.checkpoint());self.assertFalse(other.run_once())
    def test_two_call_budget_checked_before_start(self):
        self.p.config['max_calls']=1;self.s.submit('测试预算');self.s.run_once()
        self.assertEqual(self.p.calls,[]);self.assertEqual(self.s.core.state['calls'],0)
    def test_manual_uses_same_two_stage_controller(self):
        self.s.provider.config['mode']='manual';self.s.submit('手动测试')
        self.s.run_once();r=self.s.manual_request
        self.s.accept_manual(r['id'],json.dumps(proposal(r['source_event']),ensure_ascii=False))
        self.assertEqual(len(self.s.core.state['messages']),1)
        self.s.run_once();r=self.s.manual_request
        d=self.s.core.cog['pending_decision']
        self.s.accept_manual(r['id'],json.dumps({'decision_id':d,'speech':'真实手动交换路径的测试文本'}))
        self.assertEqual(len(self.s.core.state['messages']),2)
    def test_new_observation_invalidates_running_analysis(self):
        entered=threading.Event();release=threading.Event();old=self.p.complete
        def slow(messages):entered.set();release.wait(2);return old(messages)
        self.p.complete=slow;self.s.submit('旧约束')
        t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(1))
        self.s.submit('新约束');release.set();t.join(3)
        self.assertIsNone(self.s.core.cog['pending_decision'])
        self.assertEqual(len(self.s.core.cog['decisions']),0)
    def test_internal_batch_no_model_request_and_not_unbounded(self):
        self.cycle();self.cycle('另一个真实反馈')
        n=len(self.p.calls);obs=self.s.core.cog['observations']
        self.s.start_auto(6)
        self.assertTrue(self.s.run_once());self.assertFalse(self.s.run_once())
        self.assertEqual(len(self.p.calls),n);self.assertEqual(obs,self.s.core.cog['observations'])

    def test_protocol_check_runs_two_real_transport_calls_on_scratch_state(self):
        self.assertTrue(hasattr(self.s,'check_protocol'),'two-stage provider check missing')
        r=self.s.check_protocol()
        self.assertTrue(r['ok']);self.assertEqual(self.p.calls,['analyse','express'])
        self.assertEqual(self.s.core.state['messages'],[])
        self.assertEqual(self.s.core.learner.seen,0)
        self.assertEqual(self.s.core.state['calls'],2)
