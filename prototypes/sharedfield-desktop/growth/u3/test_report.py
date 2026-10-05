"""Analytical fixtures: complete identical controls must never pass learning."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from growthlab.records import ROOT
from . import report as module
from . import audit as auditor
from .common import append, write
from .materials import build
from .selection import b_materialize
from .protocol import ARMS, b_score
from .test_protocol import output


class ReportTests(unittest.TestCase):
    def test_complete_equal_shuffled_control_fails_and_learning_d5_is_counted(self):
        material = build()
        people = b_materialize(material['b'], {f'{p}:{c["id"]}': 'reply' for p, cells in material['b'].items() for c in cells})
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
            base = Path(directory) / 'run'
            out = Path(directory) / 'evidence'
            write(out / 'FROZEN.json', {'source_sha256': {}})
            full = {'people': people, 'formats': ['S1']}
            write(out / 'B_MATERIALIZED.json', full)
            injected = False
            for person, data in people.items():
                prefix = base / f'b/S1/person{person}'
                acquired = {}
                for moment in data['learn']:
                    action = moment['mode'] if moment['mode'] != 'hold' else 'quiet'
                    if not injected and 'd5' in {o['id'] for o in moment['options']}:
                        action = 'd5'
                        injected = True
                    raw = output(moment, action, 'S1')
                    row = {'moment_id': moment['id'], 'output': raw, **b_score(raw, moment, 'S1')}
                    append(prefix / 'R/learn/decisions.jsonl', row)
                    append(prefix / 'R/learn/scores.jsonl', row)
                    acquired[moment['id']] = action == 'ask' and moment['mode'] == 'ask'
                for arm in ARMS:
                    for moment in data['test']:
                        raw = output(moment, moment['mode'] if moment['mode'] != 'hold' else 'quiet', 'S1')
                        score = b_score(raw, moment, 'S1')
                        acquired_here = acquired[moment['use_parent']] if arm in ('R', 'R_SHUFFLED') else False
                        bonus = int(acquired_here)
                        row = {'format': 'S1', 'persona': person, 'arm': arm, 'moment_id': moment['id'],
                               'mode': moment['mode'], 'output': {'decisions': [raw, output(moment['use_probe'], moment['use_probe']['target'], 'S1')]},
                               **score, 'immediate_utility': score['utility'], 'information_bonus': bonus,
                               'utility': score['utility']+bonus, 'use_valid': True,
                               'acquired_before_test': acquired_here, 'use_correct': True}
                        append(prefix / arm / 'test/decisions.jsonl', row)
                    write(prefix / arm / 'test/result.json', {'status': 'complete'})
            real_audit = auditor.audit_b
            with patch.object(module, 'BASE', base), patch.object(module, 'OUT', out), \
                 patch.object(module, 'FROZEN', out / 'FROZEN.json'), patch.object(module, 'verify_phase', lambda _: None), \
                 patch.object(module, 'cost', return_value=0), patch.object(module, 'budget_snapshot', return_value={'offline': True}), \
                 patch.object(module, 'export', lambda: None), \
                 patch.object(auditor, 'audit_b', lambda data: real_audit(data, base=base, output_path=out / 'AUDIT.json')):
                result = module.report()
            self.assertTrue(result['complete'])
            self.assertFalse(result['formats']['S1']['passed'])
            self.assertFalse(result['formats']['S1']['d5_pass'])
            self.assertEqual(result['formats']['S1']['comparisons']['H2_shuffled']['ci95'], [0, 0])
            from .common import read
            self.assertTrue(read(out / 'AUDIT.json')['passed'])
            self.assertEqual(read(out / 'AUDIT.json')['checked_test_moments'], 288)


if __name__ == '__main__':
    unittest.main()
