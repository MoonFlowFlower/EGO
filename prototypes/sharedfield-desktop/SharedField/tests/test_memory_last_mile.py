import unittest,tempfile
from switchlab.memory.service import MemoryService
from tests.test_memory_store import NOW
from tests.test_memory_service import Fixture
class LastMileTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.clock=[NOW]
  self.s=MemoryService(self.t.name,provider=Fixture(),clock=lambda:self.clock[0]);self.addCleanup(lambda:self.s.close())
 def test_due_backlog_does_not_flood_chat_on_restore(self):
  for i in range(4):self.s.edit_commitment({'op':'create','title':'活动'+str(i),'quote':'1秒后一起玩'+str(i),'when':'1秒后','accept':True})
  self.s.set_options({'language_mode':'api'});self.clock[0]+=3;self.s.start_background();self.s.run_once()
  count=len(self.s.provider.calls)
  for _ in range(6):self.s.run_once()
  self.assertEqual(len(self.s.provider.calls),count,'overdue backlog caused repeated contacts without a rate limit')
 def test_default_predictor_uses_unique_evidence_counts_not_replay_multiplicity(self):
  from switchlab.memory import learning
  self.assertTrue(hasattr(learning,'forecast'),'stronger simple predictor not selected for default')
  m=learning.initial();x=[1.,1.,0.,0.]
  self.assertTrue(hasattr(learning,'observe'))
  learning.observe(m,x,0.)
  p=learning.forecast(m,x)
  for _ in range(20):learning.update(m,x,0.)
  self.assertEqual(learning.forecast(m,x),p);self.assertLess(p,.5)
