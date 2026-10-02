import copy
import importlib.util
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from tests.test_studio_core import packet

class ScriptedTransport:
    """Explicit test double. No real language understanding is evaluated here."""
    def __init__(self):
        self.config={'mode':'api','max_calls':48,'base_url':'http://127.0.0.1:1/v1','model':'TEST_DOUBLE'}
        self.requests=[];self.key='never-export-me';self.block=None;self.entered=threading.Event();self.fail=False
    def public(self):return {**self.config,'key_present':True,'local_endpoint':True}
    def complete(self,messages):
        self.requests.append(copy.deepcopy(messages));self.entered.set()
        if self.block:self.block.wait(3)
        if self.fail:raise ValueError('test-only provider failure')
        prompt=json.loads(messages[-1]['content'])
        p=packet(prompt['source_event']) if prompt['phase']=='turn' else {'content':'# 已生成的测试草稿\n限制：这只是测试夹具。'}
        return {'packet':p,'model':'TEST_DOUBLE','usage':{'input_tokens':10,'output_tokens':20},'raw':json.dumps(p,ensure_ascii=False)}

class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.service'),'persistent service required')
        from switchlab.studio.service import Service
        self.tmp=tempfile.TemporaryDirectory();self.provider=ScriptedTransport()
        self.s=Service(Path(self.tmp.name),provider=self.provider)
    def tearDown(self):
        if hasattr(self,'s'):self.s.close()
        if hasattr(self,'tmp'):self.tmp.cleanup()
    def test_language_to_goal_to_real_artifact_to_feedback_context(self):
        self.s.submit('帮我比较关卡设计方案');self.s.run_once(force=True)
        self.assertEqual(len(self.s.core.state['goals']),1)
        self.s.run_once(force=True);a=self.s.core.state['artifacts'][0]
        self.s.command('feedback',{'artifact_id':a['id'],'kind':'criteria_failed','text':'必须补上手柄操作'})
        self.s.run_once(force=True)
        self.assertIn('必须补上手柄操作',self.provider.requests[-1][-1]['content'])
        self.assertEqual(len(self.s.core.state['artifacts']),2)
    def test_autosave_and_restart_paused(self):
        from switchlab.studio.service import Service
        self.s.submit('创建方案');self.s.run_once(force=True)
        snapshot=copy.deepcopy(self.s.core.state);self.s.close()
        self.s=Service(Path(self.tmp.name),provider=self.provider)
        self.assertEqual(self.s.core.state,snapshot);self.assertEqual(self.s.auto_remaining,0)
        self.assertFalse(self.s.run_once())
    def test_manual_transport_is_real_exchange_not_demo(self):
        from switchlab.studio.provider import Provider
        self.s.provider=Provider({'mode':'manual'})
        self.s.submit('比较两种方案');self.s.run_once(force=True)
        request=self.s.manual_request
        self.assertIsNotNone(request);self.assertFalse(self.s.core.state['goals'])
        self.s.accept_manual(request['id'],json.dumps(packet(request['source_event']),ensure_ascii=False))
        self.assertEqual(len(self.s.core.state['goals']),1)
        with self.assertRaises(ValueError):self.s.accept_manual(request['id'],'{}')
    def test_no_idle_model_call(self):
        self.s.start_auto(5)
        for _ in range(3):self.assertFalse(self.s.run_once())
        self.assertFalse(self.provider.requests)
    def test_failure_no_fake_reply_and_call_budget_consumed(self):
        self.provider.fail=True;self.s.submit('hello');self.s.run_once(force=True)
        self.assertTrue(self.s.error);self.assertEqual(self.s.core.state['calls'],1)
        self.assertFalse([x for x in self.s.core.state['messages'] if x['role']=='assistant'])
        self.assertFalse(self.s.run_once());self.assertEqual(len(self.provider.requests),1)
    def test_pause_discards_inflight_result(self):
        self.provider.block=threading.Event();self.s.submit('hello')
        t=threading.Thread(target=lambda:self.s.run_once(force=True));t.start()
        self.provider.entered.wait(2);self.s.pause();self.provider.block.set();t.join(4)
        self.assertFalse(self.s.core.state['goals']);self.assertEqual(self.s.auto_remaining,0)
    def test_credentials_not_in_saved_state_or_public_view(self):
        self.s.submit('hello');self.s.run_once(force=True)
        self.assertNotIn('never-export-me',json.dumps(self.s.view()))
        self.assertNotIn('never-export-me',(Path(self.tmp.name)/'session.json').read_text())
    def test_quota_stops_without_request(self):
        self.provider.config['max_calls']=1;self.s.submit('hello');self.s.run_once(force=True)
        self.s.run_once(force=True)
        self.assertEqual(len(self.provider.requests),1);self.assertTrue(self.s.error)
    def test_single_writer_lock(self):
        from switchlab.studio.service import Service
        with self.assertRaises(ValueError):Service(Path(self.tmp.name),provider=self.provider)
    def test_invalid_manual_json_does_not_erase_request(self):
        from switchlab.studio.provider import Provider
        self.s.provider=Provider({'mode':'manual'});self.s.submit('hello');self.s.run_once(force=True)
        r=self.s.manual_request
        with self.assertRaises(ValueError):self.s.accept_manual(r['id'],'not json')
        self.assertEqual(self.s.manual_request['id'],r['id'])
    def test_future_context_contains_tool_result_before_report(self):
        e=self.s.core.apply('message',{'text':'检查工具并报告'})
        p=packet(e['id']);p['goals'][0]['steps']=[{'tool':'lab_action','action':'calibrate','instruction':'校准'},
                                                 {'tool':'draft','instruction':'报告观测，不猜真值'}]
        self.s.core.apply('turn',{'source':e['id'],'packet':p})
        self.s.run_once(force=True);self.s.run_once(force=True)
        self.assertIn('actual_lab_transition',self.provider.requests[-1][-1]['content'])
    def test_completed_draft_waits_instead_of_generating_forever(self):
        self.s.submit('hello');self.s.start_auto(8)
        self.s.run_once();self.s.run_once()
        self.assertFalse(self.s.run_once());self.assertEqual(len(self.provider.requests),2)
