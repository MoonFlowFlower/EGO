import unittest,tempfile,threading,json
from pathlib import Path
from switchlab.memory.service import MemoryService
from tests.test_memory_service import Fixture
from tests.test_memory_store import NOW

class RuntimeEdges(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Fixture()
        self.s=MemoryService(self.t.name,provider=self.p,clock=lambda:NOW);self.addCleanup(lambda:self.s.close())
    def test_world_motion_does_not_break_valid_personal_memory_interpretation(self):
        self.s.set_options({'language_mode':'api'});self.s.submit('测试夹具：1分钟后一起看星空')
        old=self.p.complete;entered=threading.Event();release=threading.Event()
        def slow(m):entered.set();release.wait(2);return old(m)
        self.p.complete=slow;t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(1));self.s.world_command('agent_step',{});release.set();t.join(3)
        self.assertFalse(self.s.error,self.s.error);self.assertEqual(self.s.store.commitments()['total'],1)
    def test_more_calls_can_be_granted_without_erasing_life(self):
        self.assertTrue(hasattr(self.s,'grant_calls'))
        for i in range(100):self.s.store.apply('call',{'phase':'fixture','model':'fixture'},at=NOW)
        pid=self.s.store.person_id
        self.s.grant_calls(10);self.s._reserve_call('test')
        self.assertEqual(self.s.store.setting('calls'),101);self.assertEqual(self.s.store.person_id,pid)
        with self.assertRaises(ValueError):self.s.grant_calls(501)
    def test_acknowledged_sources_are_marked_but_aborted_remain_resumable(self):
        self.s.set_options({'language_mode':'api'});mid=self.s.submit('你好')['id'];self.s.run_once();self.s.run_once()
        self.assertTrue(self.s.store.setting('responded:'+mid))
        mid2=self.s.submit('新问题')['id'];self.s.pause();self.assertFalse(self.s.store.setting('responded:'+mid2))
        self.s.resume_turn(mid2);self.s.run_once();self.s.run_once();self.assertTrue(self.s.store.setting('responded:'+mid2))
