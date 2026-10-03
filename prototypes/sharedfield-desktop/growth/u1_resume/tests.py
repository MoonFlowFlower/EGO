import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from u1 import tests as legacy
from u1.fixtures import build, teaching
from u1.harness import ingest
from .client import Client, TransportError, retry_delay
from .library import ConventionLibrary


class Regression(legacy.Acceptance):
    def setUp(self):
        patch = mock.patch.object(legacy, 'ConventionLibrary', ConventionLibrary)
        patch.start()
        self.addCleanup(patch.stop)
        super().setUp()


class AddedBoundaries(unittest.TestCase):
    def test_normalized_empty_rejected_without_writing(self):
        f = build()['conventions']['chain_code']
        with tempfile.TemporaryDirectory() as d, ConventionLibrary(Path(d) / 's.sqlite') as lib:
            ids = ingest(lib, teaching(f))
            for meaning in (' ', '！。，', '___', '\n\t', '　？！'):
                with self.assertRaisesRegex(ValueError, 'empty_normalized_meaning'):
                    lib.propose(dict(trigger=f['trigger'], meaning=meaning, source_ids=[ids[0]], replaces=''), allowed_ids=ids)
            self.assertEqual(lib.cards(), [])
            lib.propose(dict(trigger=f['trigger'], meaning=f['meaning'], source_ids=[ids[0]], replaces=''), allowed_ids=ids)
            self.assertEqual(len(lib.cards()), 1)

    def test_retry_after_is_floor_not_cap(self):
        self.assertEqual(retry_delay(TransportError('http_429', 75), 2.5), 77.5)
        self.assertEqual(retry_delay(TransportError('http_502'), 0), 30)

    def test_http_error_does_not_log_private_body_or_headers(self):
        client = object.__new__(Client)
        rows = []
        client.log = rows.append
        client._open = mock.Mock(side_effect=urllib.error.HTTPError(
            'https://openrouter.ai/api/v1/chat/completions', 429, 'private-text',
            {'Retry-After': '73', 'X-Private': 'secret-value'}, io.BytesIO(b'secret-body')))
        with self.assertRaises(TransportError) as caught:
            client.request('https://openrouter.ai/api/v1/chat/completions', {'messages': []}, {'Authorization': 'secret-key'})
        self.assertEqual(caught.exception.retry_after, 73)
        self.assertEqual(str(caught.exception), 'http_429')
        self.assertNotIn('secret', json.dumps(rows))
        self.assertEqual(client._open.call_count, 1)

    def test_reused_worker_uses_new_library(self):
        from u1 import run as original
        from . import run as resumed
        before = original.ConventionLibrary, original.Client, original.BASE, original.execute
        try:
            resumed.configure()
            self.assertIs(original.ConventionLibrary, ConventionLibrary)
            self.assertIs(original.Client, Client)
            self.assertIs(original.execute, resumed.execute)
            self.assertEqual(original.BASE, resumed.BASE)
        finally:
            original.ConventionLibrary, original.Client, original.BASE, original.execute = before

    def test_one_identical_retry_then_stop_without_route_switch(self):
        client = object.__new__(Client)
        client.config = {'reasoning': False, 'minimum_start_interval_s': 2}
        client.next_start = 0
        import time
        client.started = time.time()
        client.calls = 0
        client.log = mock.Mock()
        client.wait_until = mock.Mock()
        client.check_resources = mock.Mock()
        client.refresh = mock.Mock()
        client.cloud = mock.Mock()
        client.cloud.db.execute.return_value = []
        client.cloud.decide.side_effect = [TransportError('http_429', 45), TransportError('http_429')]
        from u1.harness import Stop
        with self.assertRaisesRegex(Stop, 'http_429'):
            client.call([{'role': 'user', 'content': 'same input'}], {'type': 'json_object'}, {'phase': 'test'})
        self.assertEqual(client.cloud.decide.call_count, 2)
        self.assertEqual(client.cloud.decide.call_args_list[0], client.cloud.decide.call_args_list[1])
        waits = [c.args[0] for c in client.log.call_args_list if c.args[0].get('record_type') == 'retry_wait']
        self.assertEqual(len(waits), 1)
        self.assertGreaterEqual(waits[0]['delay_s'], 45)
        self.assertLessEqual(waits[0]['delay_s'], 48)


if __name__ == '__main__':
    unittest.main()
