"""Offline transport boundary tests; no credentials or live model calls."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from p7.proxy import ProxyError
from u2.client import Stop
from u3.common import append
from u4 import client as inherited
from .owner_retry_policy import PolicyClient, FrozenClient, next_attempt, diagnostic_open


def failed(identity='x', code='upstream_unavailable'):
    return [{'event': 'request', 'input_id': identity, 'attempt': 1, 'request': {'x': 1}},
            {'event': 'response', 'input_id': identity, 'attempt': 1, 'meta': {'error': code}},
            {'event': 'failure', 'input_id': identity, 'attempt': 1, 'unix_s': 0, 'error': {'code': code}}]


class RetryPolicyTests(unittest.TestCase):
    def test_attempt_accounting_and_uncertain_calls(self):
        self.assertEqual(next_attempt([], 'x'), 1)
        self.assertEqual(next_attempt(failed(), 'x'), 2)
        for records in (failed()[:1], failed()[:2], failed()+failed(), failed(code='model_refusal')):
            with self.assertRaises(Stop):
                next_attempt(records, 'x')

    def test_success_never_replayed(self):
        events = failed()
        events[1]['meta']['error'] = None
        with self.assertRaisesRegex(Stop, 'completed_output_must_not_replay'):
            next_attempt(events, 'x')

    def client(self, folder):
        client = PolicyClient.__new__(PolicyClient)
        client.folder = Path(folder)
        client.request = Mock(return_value={'x': 1})
        client.manifest = {'request_byte_cap': 82946}
        client.config = {'model': 'frozen-model'}
        client.deepseek = SimpleNamespace(transport=SimpleNamespace(policy={'provider': {}}), cost=lambda: .5)
        client.cap, client.next_start = 2, 0
        client.wait, client.check, client.log, client.attribute = Mock(), Mock(), Mock(), Mock()
        client.model = Mock()
        return client

    def test_prior_failure_only_attempt_two(self):
        with tempfile.TemporaryDirectory() as folder:
            for row in failed():
                append(Path(folder)/'calls.jsonl', row)
            client = self.client(folder)
            def complete(request, observer, allow_invalid):
                observer('request', {'request': request})
                return {'action': 'synthetic'}, {'cost_usd': .001}
            client.model.complete.side_effect = complete
            with patch('u5.owner_retry_policy.prepare_request', return_value=(None, None, .1)):
                result = client.call({'id': 'x'})
            self.assertEqual(result[0], {'action': 'synthetic'})
            self.assertEqual(client.model.complete.call_count, 1)
            request = next(c for c in client.log.call_args_list if c.args[0] == 'request')
            self.assertEqual(request.kwargs['attempt'], 2)
            self.assertTrue(request.kwargs['owner_authorized_retry'])
            client.attribute.assert_called_once()

    def test_second_failure_has_no_third_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            for row in failed():
                append(Path(folder)/'calls.jsonl', row)
            client = self.client(folder)
            client.model.complete.side_effect = ProxyError('upstream_unavailable', 502)
            with patch('u5.owner_retry_policy.prepare_request', return_value=(None, None, .1)):
                with self.assertRaisesRegex(Stop, 'upstream_unavailable'):
                    client.call({'id': 'x'})
            self.assertEqual(client.model.complete.call_count, 1)
            client.attribute.assert_called_once()

    def test_future_calls_keep_inherited_two_attempts_and_restore_policy(self):
        original = inherited.RETRY_CODES
        with tempfile.TemporaryDirectory() as folder:
            client = self.client(folder)
            client.model.complete.side_effect = ProxyError('upstream_unavailable', 502)
            with patch('u4.client.prepare_request', return_value=(None, None, .1)):
                with self.assertRaisesRegex(Stop, 'upstream_unavailable'):
                    client.call({'id': 'x'})
            self.assertEqual(client.model.complete.call_count, 2)
            self.assertEqual(client.attribute.call_count, 2)
        self.assertIs(inherited.RETRY_CODES, original)

    def test_budget_stop_prevents_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            for row in failed():
                append(Path(folder)/'calls.jsonl', row)
            client = self.client(folder)
            client.check.side_effect = Stop('projected_cost_exceeds_2_usd_requires_owner')
            with patch('u5.owner_retry_policy.prepare_request', return_value=(None, None, .1)):
                with self.assertRaisesRegex(Stop, 'projected_cost_exceeds_2'):
                    client.call({'id': 'x'})
            client.model.complete.assert_not_called()

    def test_diagnostic_never_serializes_error_text(self):
        log = Mock()
        error = RuntimeError('secret must never enter logs')
        wrapped = diagnostic_open(Mock(side_effect=error), log, lambda: 'x')
        with self.assertRaises(RuntimeError):
            wrapped('request containing secret')
        self.assertEqual(log.call_args.kwargs, {'input_id': 'x', 'exception_type': 'RuntimeError'})
        self.assertNotIn('secret', str(log.call_args))


if __name__ == '__main__':
    unittest.main()
