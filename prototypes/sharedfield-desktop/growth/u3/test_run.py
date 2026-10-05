from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from growthlab.records import ROOT
from . import run
from .common import write, read, sha


class RunTests(unittest.TestCase):
    def test_direct_worker_replay_rejected_before_client_and_keeps_result(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
            folder = Path(directory)
            write(folder / 'job.json', {'folder': str(folder), 'operation': 'probe'})
            write(folder / 'claim.json', {'consumed': True})
            write(folder / 'result.json', {'status': 'stopped', 'stop': 'original_failure'})
            before = sha(folder / 'result.json')
            with patch.object(run, 'Client') as client:
                with self.assertRaisesRegex(run.Stop, 'already_consumed'):
                    run.worker(folder / 'job.json')
                client.assert_not_called()
            self.assertEqual(before, sha(folder / 'result.json'))

    def test_low_daily_balance_stops_before_claim_or_model_client(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
            folder = Path(directory)
            write(folder / 'freeze.json', {'source_sha256': {}})
            with patch.object(run, 'FROZEN', folder / 'freeze.json'), patch.object(run, 'OUT', folder / 'evidence'), \
                 patch.object(run, 'BASE', folder / 'runtime'), patch.object(run, 'cost', return_value=0), \
                 patch.object(run, 'budget_snapshot', return_value={'remaining_usd': .57}), patch.object(run, 'Client') as client:
                with self.assertRaisesRegex(run.Stop, 'another_day'):
                    run.run()
                client.assert_not_called()
                self.assertFalse((folder / 'runtime').exists())
                self.assertEqual(read(folder / 'evidence/DEFERRED.json')['paid_calls_started_now'], 0)

    def test_policy_conflict_blocks_freeze_without_network(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
            folder = Path(directory)
            write(folder / 'policy.json', {'status': 'pending_owner_answer', 'aligned_policy': None})
            with patch.object(run, 'FROZEN', folder / 'freeze.json'), patch.object(run, 'POLICY', folder / 'policy.json'), \
                 patch.object(run, 'Client') as client:
                with self.assertRaisesRegex(run.Stop, 'requires_owner_answer'):
                    run.freeze()
                client.assert_not_called()
                self.assertFalse((folder / 'freeze.json').exists())


if __name__ == '__main__':
    unittest.main()
