import unittest,tempfile,hashlib
from pathlib import Path
from switchlab.memory.store import MemoryStore
try:
 from switchlab.memory.migration import restore_sqlite_backup
except ImportError:restore_sqlite_backup=None
class BackupRestoreTests(unittest.TestCase):
 def test_original_backup_is_readonly_and_restored_state_matches(self):
  self.assertIsNotNone(restore_sqlite_backup)
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);s=MemoryStore(t/'source.db');s.apply('message',{'text':'必须保留的原话'},at=1800000000);h=s.projection_digest();s.backup(t/'backup.db');s.close()
   before=hashlib.sha256((t/'backup.db').read_bytes()).hexdigest()
   restore_sqlite_backup(t/'backup.db',t/'restored.db')
   self.assertEqual(before,hashlib.sha256((t/'backup.db').read_bytes()).hexdigest());r=MemoryStore(t/'restored.db')
   try:self.assertEqual(r.projection_digest(),h)
   finally:r.close()
 def test_empty_file_cannot_become_a_fabricated_restored_life(self):
  self.assertIsNotNone(restore_sqlite_backup)
  with tempfile.TemporaryDirectory() as t:
   t=Path(t);(t/'empty').write_bytes(b'')
   with self.assertRaises(ValueError):restore_sqlite_backup(t/'empty',t/'new')
   self.assertFalse((t/'new').exists())
