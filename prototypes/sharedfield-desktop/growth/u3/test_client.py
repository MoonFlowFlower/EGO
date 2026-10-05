from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from companion.budget import DailyLedger
from growthlab.records import ROOT
from p7.proxy import ProxyError
from . import client as module
from .common import budget_snapshot, append
from .client import Client, Stop


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'runs')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ledger = self.root / 'daily.sqlite'
        with patch.object(module, 'read_key', return_value='offline-dummy'), patch.object(module, 'DEFAULT_BUDGET', self.ledger):
            self.client = Client(self.root / 'lane', base=self.root, cap=.6)
        self.client.check = lambda: None
        self.client.wait = lambda _: None
        self.requests = []

    def stub(self, failures=(), actual=.001):
        def complete(request, **kwargs):
            self.requests.append(deepcopy(request))
            identity = self.client.transport.ledger.reserve(.02)
            append(self.client.folder / 'routing.jsonl', {'charge_id': identity, 'outcome': 'http_error', 'retry_after_s': 31})
            if len(self.requests) <= len(failures):
                raise ProxyError(failures[len(self.requests)-1], 503)
            self.client.transport.ledger.settle(identity, {'cost': actual})
            return {'output': 'fixture'}, {'charge_id': identity}
        self.client.model = SimpleNamespace(complete=complete)

    def call(self):
        return self.client.call([{'role': 'user', 'content': 'offline'}], {}, schema={'type': 'json_object'})

    def test_one_identical_retry_and_unknown_reserve_attribution(self):
        self.stub(('upstream_http_503',))
        self.call()
        self.assertEqual(len(self.requests), 2)
        self.assertEqual(self.requests[0], self.requests[1])
        self.assertAlmostEqual(self.client.cost(), .021)
        snap = budget_snapshot(self.ledger)
        self.assertAlmostEqual(snap['unknown_included_usd'], .02)
        self.assertFalse((self.root / 'u2/charge_ids.jsonl').exists())

    def test_second_failure_and_nonretryable_are_terminal(self):
        self.stub(('upstream_http_429', 'upstream_connection_error'))
        with self.assertRaisesRegex(Stop, 'upstream_connection_error'): self.call()
        self.assertEqual(len(self.requests), 2)
        self.assertAlmostEqual(self.client.cost(), .04)

    def test_nonretryable_not_retried(self):
        self.stub(('upstream_http_400',))
        with self.assertRaisesRegex(Stop, 'upstream_http_400'): self.call()
        self.assertEqual(len(self.requests), 1)

    def test_actual_over_estimate_stops_before_another_request(self):
        self.stub(actual=.61)
        with self.assertRaisesRegex(Stop, 'actual_exceeded_estimate'): self.call()
        self.assertEqual(len(self.requests), 1)

    def test_readonly_daily_snapshot_midnight_and_unknown(self):
        clock = [datetime(2026, 10, 6, 4, 59, tzinfo=timezone.utc)]
        ledger = DailyLedger(self.root / 'midnight.sqlite', clock=lambda: clock[0])
        ledger.reserve(.2)
        before = (self.root / 'midnight.sqlite').read_bytes()
        self.assertAlmostEqual(budget_snapshot(ledger.path, now=clock[0])['remaining_usd'], 3.8)
        clock[0] = datetime(2026, 10, 6, 5, 0, tzinfo=timezone.utc)
        self.assertEqual(budget_snapshot(ledger.path, now=clock[0])['remaining_usd'], 4)
        self.assertEqual((self.root / 'midnight.sqlite').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
