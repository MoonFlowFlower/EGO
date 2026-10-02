"""Browser JSON serializes 1.0 as 1; actual text must not be normalized."""
import tempfile,unittest
from pathlib import Path
from switchlab.memory.store import MemoryStore

def browser_numbers(x):
    if type(x) is float and x.is_integer():return int(x)
    if isinstance(x,list):return [browser_numbers(v) for v in x]
    if isinstance(x,dict):return {k:browser_numbers(v) for k,v in x.items()}
    return x

class JSONNumberTests(unittest.TestCase):
    def test_semantic_projection_hash_not_serialized_float_spelling(self):
        with tempfile.TemporaryDirectory() as t:
            a=MemoryStore(Path(t)/'a');b=MemoryStore(Path(t)/'b',initial=a._meta('initial'))
            try:
                for s,n in [(a,1.0),(b,1)]:
                    mid=s.apply('message',{'text':'版本原话是1.0，不能改成1'},at=100)['id']
                    s.apply('expression',{'text':'fixture','source':mid,'evidence':[mid],'snapshot':{'n':n}},at=101)
                self.assertEqual(a.projection_digest(),b.projection_digest())
            finally:a.close();b.close()

    def test_browser_roundtrip_keeps_text_and_replays_state(self):
        with tempfile.TemporaryDirectory() as t:
            a=MemoryStore(Path(t)/'a')
            try:
                mid=a.apply('message',{'text':'编号1.0，原文保留'},at=100)['id']
                a.apply('expression',{'text':'fixture','source':mid,'evidence':[mid],'snapshot':{'n':0.0,'p':1.0}},at=101)
                cp=browser_numbers(a.export());b=MemoryStore.from_export(Path(t)/'b',cp)
                try:self.assertEqual(b.observation(mid)['text'],'编号1.0，原文保留')
                finally:b.close()
            finally:a.close()
