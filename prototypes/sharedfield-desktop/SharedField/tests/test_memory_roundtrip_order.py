"""Dict property ordering is transport metadata, never semantic event order."""
import json,tempfile,unittest
from pathlib import Path
from switchlab.memory.store import MemoryStore

class RoundTripOrderingTests(unittest.TestCase):
    def test_setting_receipt_is_independent_of_object_key_order(self):
        with tempfile.TemporaryDirectory() as t:
            a=MemoryStore(Path(t)/'a.db');b=MemoryStore(Path(t)/'b.db')
            try:
                x=a.apply('setting',{'timezone':'UTC+08:00','memory_budget_bytes':18000},at=100)
                y=b.apply('setting',{'memory_budget_bytes':18000,'timezone':'UTC+08:00'},at=100)
                self.assertEqual(x['result'],y['result'])
            finally:a.close();b.close()

    def test_multikey_settings_export_replays_after_json_serialization(self):
        with tempfile.TemporaryDirectory() as t:
            a=MemoryStore(Path(t)/'a.db')
            try:
                a.apply('setting',{'timezone':'UTC+08:00','memory_budget_bytes':18000,'learning':False},at=100)
                a.apply('message',{'text':'原话不应因为设置字典字段顺序变化而无法接续'},at=101)
                cp=json.loads(json.dumps(a.export(),ensure_ascii=False,sort_keys=True))
                b=MemoryStore.from_export(Path(t)/'b.db',cp)
                try:self.assertEqual(a.projection_digest(),b.projection_digest())
                finally:b.close()
            finally:a.close()
