import unittest,tempfile,json,threading,time
from pathlib import Path
from copy import deepcopy
from switchlab.studio.provider import DEFAULT
from tests.test_memory_store import NOW
try:
    from switchlab.memory.service import MemoryService
except ImportError:MemoryService=None

class Fixture:
    """Explicit model substitute: checks orchestration, not natural understanding."""
    def __init__(self):self.config={**DEFAULT,'mode':'api','model':'MEMORY_TEST_FIXTURE','max_calls':100};self.calls=[]
    def public(self):return {**self.config,'key_present':False,'local_endpoint':True}
    def complete(self,messages):
        d=json.loads(messages[-1]['content']);self.calls.append(d)
        if d['phase']=='interpret':
            packet={'claims':[],'commitments':[],'recall':{'queries':[],'ids':[]}}
            raw=d['selected_input']['text']
            if raw=='测试夹具：1分钟后一起看星空':packet['commitments']=[{'op':'create','title':'一起看星空','category':'activity','quote':raw,'when':'1分钟后','accept':True}]
        elif d['phase']=='contact':packet={'action':'contact','speech':'【TEST FIXTURE】现在方便开始吗？'}
        else:packet={'speech':'【TEST FIXTURE】'+('已经记下' if d['context']['memory']['effective_commitments'] else '查过记录'),'evidence_ids':d['context']['memory']['evidence_ids']}
        return {'packet':packet,'model':'MEMORY_TEST_FIXTURE','usage':{'input_tokens':10,'output_tokens':10}}

class MemoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(MemoryService,'memory is not wired into the actual service')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.clock=[NOW];self.p=Fixture();self.s=MemoryService(self.tmp.name,provider=self.p,clock=lambda:self.clock[0]);self.addCleanup(lambda:self.s.close())
    def chat(self,text='测试夹具：1分钟后一起看星空'):
        self.s.set_options({'language_mode':'api'});self.s.submit(text);self.s.run_once();self.s.run_once()
    def test_real_chat_path_commits_before_expression(self):
        self.s.set_options({'language_mode':'api'});self.s.submit('测试夹具：1分钟后一起看星空');self.s.run_once()
        self.assertEqual(self.s.store.commitments()['total'],1)
        self.assertEqual([m['actor'] for m in self.s.view()['messages']],['user'])
        self.s.run_once();self.assertIn('已经记下',self.s.view()['messages'][-1]['text'])
        self.assertEqual([c['phase'] for c in self.p.calls],['interpret','express'])
    def test_recall_works_after_intervening_history_and_restart(self):
        self.chat();pid=self.s.store.person_id
        for i in range(100):self.s.store.apply('message',{'text':'无关对话'+str(i)},at=NOW)
        self.s.close();self.s=MemoryService(self.tmp.name,provider=self.p,clock=lambda:self.clock[0])
        self.assertEqual(self.s.store.person_id,pid);self.assertFalse(self.s.run_once());self.chat('我们约好做什么')
        self.assertIn('一起看星空',json.dumps(self.p.calls[-1],ensure_ascii=False))
    def test_no_user_message_needed_for_real_clock_and_only_one_contact(self):
        self.chat();self.s.start_background();self.clock[0]+=70
        self.assertTrue(self.s.run_once());self.assertEqual(self.p.calls[-1]['phase'],'contact')
        self.assertFalse(self.s.run_once());self.assertEqual(len([c for c in self.p.calls if c['phase']=='contact']),1)
    def test_pause_invalidates_pending_paid_contact(self):
        self.chat();self.s.start_background();self.clock[0]+=70
        old=self.p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(3);return old(m)
        self.p.complete=slow;t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(1));self.s.pause();release.set();t.join(4)
        self.assertFalse(any('现在方便开始吗' in m['text'] for m in self.s.view()['messages']))
        self.assertFalse(self.s.run_once())
    def test_cancel_during_contact_request_blocks_delivery(self):
        self.chat();c=self.s.store.commitments()['items'][0];self.s.start_background();self.clock[0]+=70
        old=self.p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(3);return old(m)
        self.p.complete=slow;t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(1))
        self.s.edit_commitment({'id':c['id'],'expected_revision':1,'op':'cancel','quote':'取消这次看星空'})
        release.set();t.join(4)
        self.assertFalse(any('现在方便开始吗' in m['text'] for m in self.s.view()['messages']))
    def test_no_permission_no_background_and_restore_paused(self):
        self.chat();self.clock[0]+=80;self.assertFalse(self.s.run_once())
        self.s.close();self.s=MemoryService(self.tmp.name,provider=self.p,clock=lambda:self.clock[0]);self.assertFalse(self.s.run_once())
    def test_manual_same_store_and_local_not_fake_model(self):
        self.s.submit('请记住');self.s.run_once();self.assertEqual(self.p.calls,[]);self.assertEqual(self.s.store.commitments()['total'],0)
        self.assertIn('未连接',self.s.view()['messages'][-1]['text'])
        self.s.set_options({'language_mode':'manual'});self.s.submit('读书');self.s.run_once();r=self.s.manual_request
        self.s.accept_manual(r['id'],json.dumps({'claims':[],'commitments':[]}));self.s.run_once();r=self.s.manual_request
        self.s.accept_manual(r['id'],json.dumps({'speech':'手动测试文本','evidence_ids':[]}));self.assertEqual(self.s.view()['messages'][-1]['text'],'手动测试文本')
    def test_sql_failure_stops_before_llm_ack(self):
        self.s.set_options({'language_mode':'api'})
        self.s.store.db.execute("CREATE TRIGGER fail_commitment BEFORE INSERT ON commitments_current BEGIN SELECT RAISE(ABORT,'test full disk'); END")
        self.s.submit('测试夹具：1分钟后一起看星空');self.s.run_once()
        self.assertEqual([c['phase'] for c in self.p.calls],['interpret']);self.assertTrue(self.s.error)
        self.assertEqual(self.s.store.commitments()['total'],0);self.assertEqual(len(self.s.view()['messages']),1)
    def test_game_adapter_connected_to_same_longterm_observation_store(self):
        self.s.world_command('agent_step',{});self.assertEqual(self.s.view()['world']['world']['tick'],1)
        self.assertTrue(any(x['namespace']=='shared_world' for x in self.s.store.search('调查')['items']))
    def test_pause_cannot_be_overridden_by_provider_packet(self):
        self.chat();self.s.pause();before=len(self.p.calls);self.clock[0]+=300
        for _ in range(20):self.assertFalse(self.s.run_once())
        self.assertEqual(len(self.p.calls),before)
