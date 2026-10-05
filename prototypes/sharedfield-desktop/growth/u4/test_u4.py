from copy import deepcopy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion.chatgpt_oauth import ChatGPTError
from u2.client import Stop
from .corpus import prepare, validate, digest, rows
from .scoring import grade, timing, forgetting
from .client import Client, QUOTA
from .run import already_completed
from . import run as runner
from .report import noise_comparison


class U4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs = prepare()

    def test_complete_grid_and_content_tampering_rejected(self):
        validate(self.inputs)
        tampered = deepcopy(self.inputs)
        tampered[0]['messages'][1]['content'] += ' '
        with self.assertRaises(ValueError):
            validate(tampered)
        self.assertEqual(sum(i['historical'] is None for i in self.inputs), 13)

    def test_original_d0_reproduces_frozen_scores(self):
        values = [{'input': i, 'score': grade(i, i['historical']['output'])} for i in self.inputs if i['historical']]
        b = timing([v for v in values if v['input']['domain'] == 'timing'])
        self.assertEqual(b['utility_by_arm'], {'R': -4, 'I': -5, 'N': -7, 'R_SHUFFLED': -10})
        self.assertEqual(b['comparisons']['H1']['ci95'], [-37.0, -8.0])
        f = forgetting([v for v in values if v['input']['domain'] == 'forget'])
        self.assertEqual((f['deleted']['correct'], f['retained']['correct']), (1, 49))
        self.assertEqual(f['retained']['before_rate'], 62/64)

    def test_wait_never_sleeps_negative_when_check_crosses_deadline(self):
        client = Client.__new__(Client)
        client.check = lambda: None
        with patch('u4.client.time.monotonic', side_effect=[10.01]), patch('u4.client.time.sleep') as sleep:
            client.wait(10)
            sleep.assert_not_called()

    def test_request_changes_only_judge_envelope(self):
        client = Client.__new__(Client)
        client.config = {'model': 'other', 'reasoning': {'enabled': True, 'effort': 'low'}, 'max_tokens': 8192}
        item = self.inputs[0]
        request = client.request(item)
        self.assertEqual(request['messages'], item['messages'])
        self.assertEqual(request['response_format'], item['response_format'])
        self.assertEqual(request['temperature'], 0)

    def test_quota_is_one_attempt_with_no_fallback(self):
        client = Client.__new__(Client)
        client.deepseek, client.next_start = None, 0
        client.request = lambda item: {}
        client.check = lambda: None
        client.wait = lambda t: None
        client.log = lambda *a, **k: None
        client.attribute = lambda: None
        class FakeModel:
            calls = 0
            def complete(self, *args, **kwargs):
                self.calls += 1
                raise ChatGPTError(QUOTA, status=429, body='synthetic test fixture')
        client.model = FakeModel()
        with self.assertRaises(Stop) as failure:
            client.call({'id': 'test'})
        self.assertEqual(str(failure.exception), QUOTA)
        self.assertEqual(client.model.calls, 1)

    def test_completed_rows_retained_and_duplicates_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'decisions.jsonl'
            line = json.dumps({'id': 'completed-once', 'output': {'action': 'o1'}}) + '\n'
            path.write_text(line, encoding='utf-8')
            self.assertEqual(set(already_completed(path)), {'completed-once'})
            path.write_text(line * 2, encoding='utf-8')
            with self.assertRaises(Stop):
                already_completed(path)

    def test_actual_runner_quota_resume_skips_completed_decision(self):
        selected = deepcopy([i for i in self.inputs if i['historical']][:2])
        outputs = {i['id']: i['historical']['output'] for i in selected}
        for i in selected:
            i['historical'] = None
        invocations = []
        class FakeClient:
            stopped = False
            def __init__(self, *args, **kwargs):
                pass
            def check(self):
                pass
            def parsed(self, valid):
                pass
            def call(self, item):
                invocations.append(item['id'])
                if len(invocations) == 2:
                    raise Stop(QUOTA)
                return outputs[item['id']], {}
        with tempfile.TemporaryDirectory() as directory:
            base, out = Path(directory) / 'runs', Path(directory) / 'evidence'
            out.mkdir()
            (out / 'INPUTS.jsonl').write_text(''.join(json.dumps(i) + '\n' for i in selected), encoding='utf-8')
            frozen = out / 'FROZEN.json'; frozen.write_text('{}')
            manifest = {'order': [i['id'] for i in selected], 'judges': {'D2': {}}, 'dollar_cap_usd': 1}
            with patch.object(runner, 'BASE', base), patch.object(runner, 'OUT', out), \
                 patch.object(runner, 'FROZEN', frozen), patch.object(runner, 'verify', return_value=manifest), \
                 patch.object(runner, 'Client', FakeClient), patch('builtins.print'):
                runner.run_judge('D2')
                self.assertEqual(len(already_completed(base / 'D2/decisions.jsonl')), 1)
                runner.run_judge('D2', resume=True)
                self.assertEqual(len(already_completed(base / 'D2/decisions.jsonl')), 2)
                runner.run_judge('D2', resume=True)
            self.assertEqual(invocations, [selected[0]['id'], selected[1]['id'], selected[1]['id']])

    def test_D0_noise_equal_to_between_judge_difference_withholds_claim(self):
        item = next(i for i in self.inputs if i['historical'])
        identity = item['id']
        original = grade(item, item['historical']['output'])
        modified = {**original, 'signature': ['different']}
        decisions = {'D0_repeat': {identity: {'score': modified}}, 'D1': {identity: {'score': modified}},
                     'D2': {identity: {'score': original}}}
        result = noise_comparison({identity: item}, decisions, [identity])
        self.assertTrue(result['all']['judges']['D1']['withhold_attribution'])
        self.assertTrue(result['all']['judges']['D2']['withhold_attribution'])


if __name__ == '__main__':
    unittest.main()
