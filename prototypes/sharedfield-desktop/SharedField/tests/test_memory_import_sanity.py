import unittest,tempfile,json
from pathlib import Path
from switchlab.memory.store import MemoryStore,rehash_export
from switchlab.memory.service import MemoryService
class ImportSanityTests(unittest.TestCase):
 def test_malformed_privacy_checkpoint_cannot_replace_live_state(self):
  with tempfile.TemporaryDirectory() as t:
   s=MemoryService(t)
   try:
    mid=s.submit('保留我的原始经历')['id'];s.forget([mid],True);s.submit('不能被坏导入覆盖')
    cp=s.store.export();initial=cp['initial'];model=next(r for r in initial['privacy_projection']['models'] if r['key']=='availability');model['body']=json.dumps({'weights':'bad'})
    # An attacker can rehash inputs, but structurally broken state must fail.
    rehash_export(cp)
    probe=MemoryStore(Path(t)/'probe.db',initial=initial)
    try:
     for e in cp['journal']:probe.apply(e['kind'],e['payload'],at=e['at'],dependencies=e['dependencies'])
     cp['projection_sha256']=probe.projection_digest()
    finally:probe.close()
    before=s.store.projection_digest()
    with self.assertRaises(ValueError):s.import_checkpoint(cp,archive_current=True)
    self.assertEqual(before,s.store.projection_digest())
   finally:s.close()
