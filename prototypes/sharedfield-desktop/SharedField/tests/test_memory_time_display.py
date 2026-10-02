import unittest,tempfile
from pathlib import Path
from switchlab.memory.store import MemoryStore
from tests.test_memory_store import NOW
class TimeDisplayTests(unittest.TestCase):
 def test_display_uses_stored_timezone_not_browser_timezone(self):
  with tempfile.TemporaryDirectory() as t:
   s=MemoryStore(Path(t)/'db')
   try:
    s.apply('setting',{'timezone':'UTC+08:00'},at=NOW)
    src=s.apply('message',{'text':'今天20:00一起看书'},at=NOW)['id']
    r=s.apply('interpret',{'source':src,'claims':[],'commitments':[{'op':'create','title':'看书','quote':'今天20:00一起看书','when':'今天20:00','accept':True}]},at=NOW)
    c=s.commitment(r['result']['commitments'][0]);self.assertIn('20:00:00+08:00',c.get('due_display',''))
   finally:s.close()
