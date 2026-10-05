import json
from pathlib import Path
import tempfile
import unittest

from u2.run import exclusive, screen_packet
from u2.supplement_v2.check import candidates, check
from .screen import lane, old_pool
from .selection import qualify, draw


class ScreenTests(unittest.TestCase):
    def test_reproduce_sealed_old_pool(self):
        kept, excluded = old_pool()
        self.assertEqual(len(kept), 70)
        self.assertEqual(len(excluded), 74)
        result = draw(kept)
        self.assertFalse(result['passed'])
        self.assertEqual(result['counts'], {'P': 10, 'Q': {'yes': 8, 'no': 4, 'total': 12}, 'W': {'yes': 24, 'no': 24, 'total': 48}})

    def test_minima_balanced_seeded_draw_and_failed_prior(self):
        kept, _ = old_pool()
        additional = [i for i in candidates() if i['id'] in ('P49', 'P50', 'Q61', 'Q62')]
        pool = kept + additional
        result = draw(pool)
        self.assertTrue(result['passed'])
        self.assertEqual(result, draw(list(reversed(pool))))
        selected = [i for i in pool if i['id'] in result['selected_ids']]
        self.assertEqual(sum(i['category'] == 'P' for i in selected), 12)
        self.assertEqual(sum(i.get('should_ask') is True for i in selected), 6)
        self.assertEqual(sum(i.get('should_ask') is False for i in selected), 6)
        self.assertEqual(sum(i.get('applicable') is True for i in selected), 12)
        self.assertEqual(sum(i.get('applicable') is False for i in selected), 12)
        self.assertFalse(draw([i for i in pool if i['id'] != 'P50'])['passed'])
        self.assertFalse(draw([i for i in pool if i['id'] != 'Q62'])['passed'])
        with self.assertRaises(ValueError): draw(pool + [pool[0]])
        rows = {('P49', 'prior'): {'scores': [{'valid': True, 'correct': False}, {'valid': True, 'correct': True}]},
                ('P49', 'ceiling'): {'scores': [{'valid': True, 'correct': True}]}}
        qualified, excluded = qualify([additional[0]], rows)
        self.assertFalse(qualified)
        self.assertEqual(excluded[0]['reasons'], ['prior_already_target'])

    def test_all_96_calls_use_only_frozen_supplement_and_same_packets(self):
        items = candidates()
        self.assertTrue(check(items)['passed'])
        indexed = {i['id']: i for i in items}
        class OfflineClient:
            def __init__(self, folder): self.folder, self.calls = Path(folder), []
            def call(self, messages, context, schema):
                item = indexed[context['item_id']]
                expected, expected_schema, cases = screen_packet(item, context['stage'])
                assert messages == expected and schema == expected_schema
                self.calls.append((item['id'], context['stage']))
                return {'decisions': [{'reason': 'offline', 'interpretation': 'pipeline only', 'action': c['target'], 'reply': 'test'} for c in cases]}, {'cost_usd': 0}
            def parsed(self, valid): assert valid
        with tempfile.TemporaryDirectory() as directory:
            client = OfflineClient(directory)
            for category in ('P', 'Q'):
                for stage in ('prior', 'ceiling'):
                    lane({'category': category, 'screen_stage': stage}, client)
            self.assertEqual(len(client.calls), 96)
            self.assertEqual(set(client.calls), {(i['id'], s) for i in items for s in ('prior', 'ceiling')})
            claim = Path(directory) / 'claim'
            exclusive(claim, {'once': True})
            with self.assertRaises(FileExistsError): exclusive(claim, {'once': False})
            self.assertTrue(json.loads(claim.read_text())['once'])


if __name__ == '__main__': unittest.main()
