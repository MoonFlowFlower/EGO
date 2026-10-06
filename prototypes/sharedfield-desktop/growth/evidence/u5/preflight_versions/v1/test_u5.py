"""Offline checks target experimental contrasts, leakage and stopping rules."""
from collections import Counter
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from growthlab.records import ROOT
from u3.common import read
from u3.protocol import bundle_packet
from u3.f1 import DIRECTIVE
from u4.corpus import rows, historical
from .corpus import OUT, ARMS, PREFIX, NARROW, NOISE_IDS, prepare, interventions, label, validate
from .scoring import grade, bootstrap, timing
from .client import projection, Client


class U5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = prepare()
        cls.u4 = {v['id']: v for v in rows(ROOT/'evidence/u4/INPUTS.jsonl')}
        cls.people = read(ROOT/'evidence/u3/B_MATERIALIZED.json')['people']

    def test_population_and_reuse(self):
        validate(self.inputs)
        old = [i for i in self.inputs if i['historical']]
        self.assertEqual(Counter(i['arm'] for i in old), {'N': 72, 'R': 63})
        missing = [i for i in self.inputs if i['domain'] == 'timing' and i['arm'] == 'R' and not i['historical']]
        self.assertEqual(len(missing), 9)
        self.assertEqual({i['person'] for i in missing}, {'3'})

    def test_f1_only_authorized_changes(self):
        for i in self.inputs:
            if i['domain'] != 'forget':
                continue
            old = self.u4[i['provenance']['u4_id']]
            a, b = json.loads(i['messages'][1]['content']), json.loads(old['messages'][1]['content'])
            notes = b['memory'].pop('do_not_use')
            if i['related']:
                self.assertEqual(len(a['memory']['do_not_use']), 1)
                self.assertIn(a['memory'].pop('do_not_use')[0], notes)
                self.assertEqual(i['messages'][0]['content'], old['messages'][0]['content']+NARROW)
            else:
                self.assertNotIn('do_not_use', a['memory'])
                self.assertEqual(i['messages'][0]['content']+DIRECTIVE, old['messages'][0]['content'])
            self.assertEqual(a, b)
            self.assertEqual(i['response_format'], old['response_format'])
        self.assertEqual(Counter((r['deleted'], r['related']) for r in read(OUT/'F1B_RELEVANCE.json')),
                         {(True, True): 18, (False, False): 64})

    def test_only_memory_changes_in_s0(self):
        for i in self.inputs:
            if i['domain'] != 'timing':
                continue
            sources = read(OUT/f'memories/person{i["person"]}/R.json')
            messages, schema = bundle_packet(i['case'], sources, 'S0')
            actual, expected = json.loads(i['messages'][1]['content']), json.loads(messages[1]['content'])
            actual.pop('utterances'); expected.pop('utterances')
            self.assertEqual(actual, expected)
            self.assertEqual(i['messages'][0], messages[0])
            self.assertEqual(i['response_format'], schema)
            self.assertFalse(i['acquired'])

    def test_noise_exact_original(self):
        noise = [i for i in self.inputs if i['domain'] == 'noise']
        self.assertEqual(Counter(i['case']['id'] for i in noise), {i: 3 for i in NOISE_IDS})
        for i in noise:
            self.assertEqual(i['original_request'], self.u4[i['provenance']['u4_id']]['original_request'])

    def test_paired_feedback_no_answers_or_labels(self):
        forbidden = {'mode', 'utilities', 'hidden_answer', 'reactions', 'target', 'arm', 'persona'}
        for person in ('1', '2', '3'):
            original = read(OUT/f'memories/person{person}/R.json')
            original_ids = {r['utterance_id'] for r in original}
            full = read(OUT/f'memories/person{person}/feedback.json')
            control = read(OUT/f'memories/person{person}/feedback_control.json')
            self.assertEqual([r for r in full if r['utterance_id'] in original_ids], original)
            self.assertEqual(len(full), len(control))
            supplements = 0
            for a, b in zip(full, control):
                self.assertFalse(forbidden & set(a))
                if a['utterance_id'] in original_ids:
                    self.assertEqual(a, b)
                    continue
                supplements += 1
                self.assertEqual(a['speaker'], 'program')
                self.assertTrue(a['utterance_text'].startswith(PREFIX+'如果选「'))
                self.assertTrue(b['utterance_text'].startswith(PREFIX))
                self.assertNotIn('答案是', a['utterance_text'])
                self.assertEqual(len(a['utterance_text']), len(b['utterance_text']))
                self.assertEqual({k:v for k,v in a.items() if k != 'utterance_text'},
                                 {k:v for k,v in b.items() if k != 'utterance_text'})
            self.assertEqual(supplements, 128)

    def test_precedent_changes_do_not_depend_on_hidden_labels(self):
        for person, data in self.people.items():
            original = read(OUT/f'memories/person{person}/R.json')
            learned = read(ROOT/f'evidence/u3/raw/b/S0/person{person}/R/learn/learned.json')
            decisions = [d for d, _, _ in historical(ROOT/f'evidence/u3/raw/b/S0/person{person}/R/learn')]
            derived, audit = interventions(person, data, original, learned, decisions)
            self.assertEqual(derived['precedent'], read(OUT/f'memories/person{person}/precedent.json'))
            self.assertEqual([r['precedent_action'] for r in audit], ['ask', 'suggest']*16)
            assistant = [r for r in derived['precedent'] if r['speaker'] == 'assistant']
            self.assertEqual(len(assistant), 32)
            for idx, r in enumerate(derived['precedent']):
                if r['speaker'] == 'assistant':
                    self.assertEqual(derived['precedent'][idx+1]['utterance_text'], '嗯。')

    def test_scope_matches_and_shuffled_is_different(self):
        n = 0
        for person, info in read(OUT/'CONSTRUCTION.json').items():
            real = read(OUT/f'memories/person{person}/scope.json')
            fake = read(OUT/f'memories/person{person}/scope_shuffled.json')
            original = read(OUT/f'memories/person{person}/R.json')
            self.assertEqual(len(real), len(original))
            for a, b, c in zip(real, fake, original):
                self.assertEqual(len(a['utterance_text']), len(b['utterance_text']))
                if a != c:
                    n += 1
                    self.assertNotEqual(a['utterance_text'], b['utterance_text'])
                    self.assertTrue(a['utterance_text'].endswith(c['utterance_text']))
                    self.assertTrue(b['utterance_text'].endswith(c['utterance_text']))
            for r in info['audit']:
                if r['negative_reaction']:
                    self.assertNotEqual(r['visible_markers'], r['donor_markers'])
                    self.assertEqual(len(label(r['visible_markers'])), len(label(r['donor_markers'])))
        self.assertEqual(n, 4)

    def test_original_decisions_regrade_unchanged(self):
        for i in self.inputs:
            if not i['historical']:
                continue
            result = grade(i, i['historical']['output'])
            old = next(d for d in rows(ROOT/i['provenance']['decisions_file']) if d['meta']['charge_id'] == i['historical']['meta']['charge_id'])
            for field in ('utility', 'd5', 'action', 'information_bonus', 'valid'):
                self.assertEqual(result[field], old[field])

    def test_invalid_is_not_passive(self):
        case = next(i for i in self.inputs if i['domain'] == 'timing')
        score = grade(case, None)
        self.assertEqual(score['utility'], -3)
        self.assertFalse(score['passive'])
        self.assertFalse(score['active'])

    def test_bootstrap_pairs_and_gate(self):
        row = {a: {'active': a in ('N', 'precedent'), 'utility': int(a == 'feedback')} for a in ARMS}
        result = bootstrap({p: [deepcopy(row) for _ in range(24)] for p in ('1', '2', '3')}, replicates=100)
        self.assertEqual(result['phenomenon']['ci95'], [72, 72])
        self.assertEqual(result['C1']['ci95'], [72, 72])
        self.assertFalse(result['C5']['threshold_met'])
        i = next(i for i in self.inputs if i['domain'] == 'timing')
        score = grade(i, None)
        score['d5'] = True
        r = timing([{'input': i, 'score': score}])
        self.assertIsNone(r['comparisons'])
        self.assertEqual(r['interpretation'], 'D5_stop_all_interpretation_for_this_judge')

    def test_projection_stops_before_next_call(self):
        ids = {'a': {'domain': 'timing', 'arm': 'feedback'}}
        manifest = {'new_order': {'D0': ['a'], 'D1': []}, 'dollar_cap_usd': 2.0}
        self.assertTrue(projection(manifest, ids, {}, 2.01)['stop'])
        self.assertFalse(projection(manifest, ids, {}, 0)['stop'])

    def test_judge_configuration_and_no_request_mutation(self):
        frozen = read(ROOT/'evidence/u4/FROZEN.json')
        for judge in ('D0', 'D1'):
            client = Client.__new__(Client)
            client.config = frozen['judges'][judge]
            original = deepcopy(self.inputs[0])
            request = client.request(self.inputs[0])
            self.assertEqual(self.inputs[0], original)
            self.assertEqual(request['messages'], original['messages'])
            self.assertEqual(request['temperature'], 0)
            self.assertEqual(request['reasoning'], client.config['reasoning'])


if __name__ == '__main__':
    unittest.main()
