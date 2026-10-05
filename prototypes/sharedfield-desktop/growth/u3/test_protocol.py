from collections import Counter
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest

from .materials import build
from .protocol import FORMATS, packet, a_score, a_verdict, bundle_packet
from .selection import a_materialize, a_screen, b_materialize
from .baselines import fit, evaluate
from .statistics import comparisons


def output(case, action, fmt='S0'):
    selected = next(n+1 for n, o in enumerate(case['options']) if o['id'] == action)
    return {k: f'o{selected}' if k == 'action' else '无' for k in FORMATS[fmt]}


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.materials = build()
        cls.items = a_materialize(cls.materials['a'], {c['id']: 'reply' for c in cls.materials['a']})
        cls.people = b_materialize(cls.materials['b'], {f'{p}:{c["id"]}': 'reply' for p, cells in cls.materials['b'].items() for c in cells})

    def test_wrong_action_not_repaired_by_correct_reason(self):
        item = next(i for i in self.items if i['kind'] == 'known')
        response = output(item, 'ask', 'S1')
        response['known'] = '已经知道答案，原话编号是已提供的那条。'
        scored = a_score(response, item, 'S1')
        self.assertTrue(scored['intrusion'])
        self.assertFalse(scored['correct'])
        response['action'] = output(item, 'reply', 'S1')['action']
        self.assertFalse(a_score(response, item, 'S1')['intrusion'])

    def test_exact_thresholds_and_invalid_does_not_reward_silence(self):
        yes = [{'should_ask': True, 'appropriate_ask': n < 6, 'intrusion': False} for n in range(12)]
        no = [{'should_ask': False, 'appropriate_ask': False, 'intrusion': n < 2} for n in range(12)]
        self.assertTrue(a_verdict(yes+no)['passed'])
        no[2]['intrusion'] = True
        self.assertFalse(a_verdict(yes+no)['passed'])
        known = next(i for i in self.items if i['kind'] == 'known')
        self.assertTrue(a_score(None, known, 'S1')['intrusion'])

    def test_target_rules_and_reactions_never_enter_packet(self):
        for person in self.people.values():
            for moment in person['test']:
                original = packet(moment, [], 'S0')
                changed = deepcopy(moment)
                changed['mode'] = 'a completely different rule'
                changed['utilities'] = {a: 999 for a in changed['utilities']}
                changed['hidden_answer'] = 'HIDDEN_SENTINEL'
                changed['reactions'] = {'reply': 'HIDDEN_SENTINEL'}
                self.assertEqual(packet(changed, [], 'S0'), original)
                wire = json.loads(original[1]['content'])
                self.assertNotIn('HIDDEN_SENTINEL', original[1]['content'])
                self.assertTrue(all(o['id'].startswith('o') for o in wire['current']['options']))
                self.assertEqual(packet(moment, [], 'S0')[1], packet(moment, [], 'S1')[1])

    def test_a_branches_have_required_counts_and_timing(self):
        self.assertEqual(Counter(i['kind'] for i in self.items), {'ask': 12, 'known': 6, 'restriction': 6})
        self.assertTrue(any(i['prior_aligned'] for i in self.items))
        self.assertTrue(any(not i['prior_aligned'] for i in self.items))
        for item in self.items:
            self.assertEqual(item['question_dialogue'], item['teaching_dialogue']+1)
            self.assertNotIn(item['hidden_answer'], packet(item, [], 'S0')[1]['content'])

    def test_pending_policy_fails_closed_and_calibration_is_explicit(self):
        prior = {i['id']: {'valid': True, 'action': i['target']} for i in self.items}
        ceiling = deepcopy(prior)
        with self.assertRaisesRegex(ValueError, 'not_resolved'):
            a_screen(self.items, prior, ceiling, aligned_policy='pending')
        strict = a_screen(self.items, prior, ceiling, aligned_policy='exclude_all_correct')
        self.assertEqual(strict['eligible_ids'], [])
        retained = a_screen(self.items, prior, ceiling, aligned_policy='retain_calibration')
        self.assertEqual(set(retained['eligible_ids']), {i['id'] for i in self.items if i['prior_aligned']})
        self.assertFalse(retained['passed'])  # no replacement of missing ask items

    def test_b_prior_defaults_all_four_human_plausible_choices(self):
        for default in ('quiet', 'reply', 'ask', 'suggest'):
            people = b_materialize(self.materials['b'], {f'{p}:{c["id"]}': default for p, cells in self.materials['b'].items() for c in cells})
            for person in people.values():
                self.assertEqual((person['aligned_cells'], person['contrary_cells']), (3, 5))
                self.assertEqual(len(person['learn']), 32)
                self.assertEqual(len(person['test']), 24)
                self.assertEqual(Counter(m['dialogue'] for m in person['learn']), dict.fromkeys(range(1, 9), 4))
                times = [datetime.fromisoformat(m['occurred_at']) for m in person['learn']]
                self.assertEqual(times, sorted(times))
                for moment, instant in zip(person['learn'], times):
                    self.assertEqual(instant.weekday() < 5, moment['markers']['day_type'] == '工作日')
                    self.assertEqual(instant.hour < 12, moment['markers']['time_band'] == '早上')
                for moment in person['learn']+person['test']:
                    self.assertEqual(moment['utilities']['d5'], -3)
                    self.assertIsNone(moment['reactions']['quiet'])
                    self.assertIn('语气不舒服', moment['reactions']['d5'])

    def test_balanced_reduction_keeps_available_calibration_strata(self):
        items = deepcopy(self.items)
        seen = Counter()
        for item in items:
            item['prior_aligned'] = seen[item['kind']] == 0
            seen[item['kind']] += 1
        prior = {i['id']: {'valid': True, 'action': i['target'] if i['prior_aligned'] else
                 ('reply' if i['kind'] == 'ask' else 'ask')} for i in items}
        ceiling = {i['id']: {'valid': True, 'action': i['target']} for i in items}
        for item in [i for i in items if i['kind'] == 'ask'][-3:]:
            ceiling[item['id']]['action'] = 'repeat'
        result = a_screen(items, prior, ceiling, aligned_policy='retain_calibration')
        self.assertTrue(result['passed'])
        self.assertEqual(len(result['selected_ids']), 16)
        for kind in ('ask', 'known', 'restriction'):
            chosen = [i for i in items if i['id'] in result['selected_ids'] and i['kind'] == kind]
            self.assertEqual({i['prior_aligned'] for i in chosen}, {True, False})

    def test_best_baseline_is_training_only_and_oracle_not_selectable(self):
        person = self.people['1']
        fitted = fit(person['learn'])
        self.assertNotIn('oracle', fitted['policies'])
        original = deepcopy(fitted)
        changed = deepcopy(person['test'])
        for moment in changed:
            moment['utilities'] = {k: -999 for k in moment['utilities']}
        evaluate(fitted, person['learn'], changed)
        self.assertEqual(fitted, original)
        self.assertEqual(fitted['selected'], max(fitted['learning_utilities'], key=fitted['learning_utilities'].get))

    def test_topic_history_marker_agrees_with_simulated_originals(self):
        for person in self.people.values():
            history = []
            for moment in person['learn']:
                if moment.get('background'):
                    history.append(moment['background'])
                self.assertEqual(any(moment['topic'] in text for text in history), moment['markers']['topic_seen'])
                history.append(moment['situation'])
            for moment in person['test']:
                self.assertEqual(any(moment['topic'] in text for text in history), moment['markers']['topic_seen'])

    def test_paired_bootstrap_zero_and_uniform_positive(self):
        equal = {str(p): [dict.fromkeys(('R', 'I', 'N', 'R_SHUFFLED', 'fixed'), 0) for _ in range(24)] for p in range(1, 4)}
        self.assertTrue(all(v['ci95'] == [0, 0] and not v['passed'] for v in comparisons(equal, replicates=100).values()))
        for rows in equal.values():
            for row in rows: row['R'] = 2
        self.assertTrue(all(v['ci95'] == [144, 144] and v['passed'] for v in comparisons(equal, replicates=100).values()))
        for row in equal['1']: row['N'] = 7
        self.assertFalse(comparisons(equal, replicates=100)['H2_controls']['passed'])


if __name__ == '__main__':
    unittest.main()
