"""Offline separation of reservation headroom and the original projection gate."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from u2.client import Stop
from .owner_reservation import ReservationClient, LIMIT
from .owner_retry_policy import PolicyClient


class ReservationTests(unittest.TestCase):
    def make_client(self):
        def initialize(client):
            client.manifest = {'dollar_cap_usd': 2.0, 'new_order': {'D0': [], 'D1': []}, 'request_byte_cap': 82946}
            client.deepseek = SimpleNamespace(cap=2.0, check=Mock(), cost=lambda: 1.90135425,
                transport=SimpleNamespace(policy={'provider': {}}))
            client.inputs, client.decisions = {}, {}
        with patch.object(PolicyClient, '__init__', initialize):
            return ReservationClient()

    def test_only_reservation_headroom_changes(self):
        client = self.make_client()
        self.assertEqual((client.cap, client.deepseek.cap), (2.05, 2.05))
        self.assertEqual(client.manifest['dollar_cap_usd'], 2.0)

    def test_projection_still_stops_above_two(self):
        client = self.make_client()
        client.deepseek.cost = lambda: 2.000001
        with tempfile.TemporaryDirectory() as folder, patch('u5.client.BASE', Path(folder)):
            with self.assertRaisesRegex(Stop, 'projected_cost_exceeds_2_usd_requires_owner'):
                client.check()
            self.assertTrue((Path(folder)/'COST_STOP.json').exists())

    def test_current_request_can_fit_without_changing_request(self):
        client = self.make_client()
        with tempfile.TemporaryDirectory() as folder:
            client.folder = Path(folder)
            client.config = {'model': 'same-frozen-model'}
            client.request = Mock(return_value={'frozen': 'unchanged'})
            client.wait, client.check, client.log, client.attribute = Mock(), Mock(), Mock(), Mock()
            client.next_start = 0
            client.model = Mock()
            client.model.complete.return_value = ('same-output', {})
            with patch('u4.client.prepare_request', return_value=(None, None, .09988)):
                self.assertEqual(client.call({'id': 'next'}), ('same-output', {}))
            self.assertEqual(client.model.complete.call_args.args, ({'frozen': 'unchanged'},))
            self.assertEqual(client.model.complete.call_count, 1)
            client.deepseek.cost = lambda: 2.01
            client.model.reset_mock()
            with patch('u4.client.prepare_request', return_value=(None, None, .09988)):
                with self.assertRaisesRegex(Stop, 'estimate_reservation_stop'):
                    client.call({'id': 'later'})
            client.model.complete.assert_not_called()


if __name__ == '__main__':
    unittest.main()
