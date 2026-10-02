import hashlib
import json
import tempfile
import unittest
import subprocess
import sys
import zipfile
from pathlib import Path
from switchlab.memory.store import MemoryStore,code_fingerprint
from switchlab.shared.evidence import digest

class ReadingMigrationTests(unittest.TestCase):
    def test_runtime_fingerprint_is_identical_across_path_separators(self):
        root=Path(__file__).resolve().parents[1]
        paths=sorted([p for p in (root/'switchlab').rglob('*') if p.is_file() and p.suffix in ('.py','.js','.html','.css')]+[root/'run.py'])
        self.assertEqual(code_fingerprint(),digest([(p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]))

    def test_verified_old_life_migrates_without_editing_original_and_replays(self):
        from switchlab.memory import migration_v06
        with tempfile.TemporaryDirectory() as legacy:
            archive=Path(__file__).resolve().parents[1]/'compatibility/shared_v06_runtime.zip'
            with zipfile.ZipFile(archive) as z:z.extractall(legacy)
            script="from switchlab.memory.store import MemoryStore; import json; s=MemoryStore('old.db'); s.apply('message',{'text':'v0.6 preserved source'}); print(json.dumps(s.export())); s.close()"
            run=subprocess.run([sys.executable,'-c',script],cwd=Path(legacy)/'SharedField',capture_output=True,text=True,check=True)
            old=json.loads(run.stdout)
        original=json.dumps(old,ensure_ascii=False,sort_keys=True)
        with tempfile.TemporaryDirectory() as d:
            migrated=migration_v06.import_v06(Path(d)/'new.db',old)
            try:
                self.assertEqual(migrated.person_id,old['initial']['person_id'])
                self.assertEqual(migrated.recent()['items'][0]['text'],'v0.6 preserved source')
                migrated.apply('reading',{'op':'material','title':'新阅读','text':'新版本实际材料'})
                export=migrated.export()
                copy=MemoryStore.from_export(Path(d)/'replay.db',export)
                try:self.assertEqual(copy.projection_digest(),migrated.projection_digest())
                finally:copy.close()
            finally:migrated.close()
        self.assertEqual(json.dumps(old,ensure_ascii=False,sort_keys=True),original)
