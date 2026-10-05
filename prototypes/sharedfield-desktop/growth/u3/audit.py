"""Regrade retained raw model choices against frozen labels, no model call."""
from .common import BASE, OUT, read, write
from .protocol import ARMS, b_score, parse


def audit_b(material, *, base=BASE, output_path=OUT / 'AUDIT.json'):
    import json
    def rows(path):
        return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    issues, checked = [], 0
    for fmt in material['formats']:
        for person, data in material['people'].items():
            prefix = base / f'b/{fmt}/person{person}'
            learning = {m['id']: m for m in data['learn']}
            acquired = {}
            learn_rows = rows(prefix / 'R/learn/decisions.jsonl')
            for row in learn_rows:
                moment = learning[row['moment_id']]
                parsed = parse(row['output'], moment, fmt)
                acquired[moment['id']] = parsed['valid'] and parsed['action'] == 'ask' and moment['mode'] == 'ask'
            for arm in ARMS:
                values = rows(prefix / arm / 'test/decisions.jsonl')
                tests = {m['id']: m for m in data['test']}
                if len(values) != 24 or len({r['moment_id'] for r in values}) != 24:
                    issues.append({'format': fmt, 'persona': person, 'arm': arm, 'reason': 'incomplete_test_grid'})
                for row in values:
                    moment = tests[row['moment_id']]
                    output = row['output']
                    envelope = isinstance(output, dict) and set(output) == {'decisions'} and isinstance(output['decisions'], list) and len(output['decisions']) == 2
                    primary, use = output['decisions'] if envelope else (None, None)
                    score = b_score(primary, moment, fmt)
                    usage = parse(use, moment['use_probe'], fmt)
                    has_answer = bool(acquired.get(moment['use_parent'])) if arm in ('R', 'R_SHUFFLED') else False
                    correct = usage['valid'] and usage['action'] == moment['use_probe']['target']
                    bonus = int(has_answer and correct)
                    expected = {**score, 'immediate_utility': score['utility'], 'information_bonus': bonus,
                                'utility': score['utility']+bonus, 'use_correct': correct,
                                'acquired_before_test': has_answer, 'use_valid': usage['valid']}
                    mismatch = [key for key, value in expected.items() if row.get(key) != value]
                    if mismatch:
                        issues.append({'format': fmt, 'persona': person, 'arm': arm, 'moment_id': moment['id'], 'fields': mismatch})
                    checked += 1
    value = {'kind': 'offline_regrading_not_new_trial', 'passed': not issues, 'checked_test_moments': checked, 'issues': issues}
    write(output_path, value)
    return value
