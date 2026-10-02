import unittest,tempfile,time
from switchlab.memory.service import MemoryService
from tests.test_memory_service import Fixture
class WallClockTests(unittest.TestCase):
 def test_background_thread_delivers_due_item_on_real_time_without_new_message(self):
  with tempfile.TemporaryDirectory() as t:
   s=MemoryService(t,provider=Fixture())
   try:
    s.set_options({'language_mode':'api'});s.edit_commitment({'op':'create','title':'实际时钟测试','quote':'1秒后联系','when':'1秒后','accept':True})
    before=len(s.store.recent()['items']);s.start_worker();s.start_background();deadline=time.monotonic()+6
    while time.monotonic()<deadline:
     if any(m['source'].get('contact') for m in s.view()['messages']):break
     time.sleep(.08)
    delivered=[m for m in s.view()['messages'] if m['source'].get('contact')]
    self.assertEqual(len(delivered),1);self.assertGreaterEqual(delivered[0]['at'],s.store.commitments()['items'][0]['due_at'])
    self.assertEqual(len(s.store.recent()['items']),before+1)
   finally:s.close()
