"""Read-only mechanical result reconstruction. No model grading or new trial."""
import csv
from collections import Counter

from .baselines import evaluate
from .common import BASE, OUT, read, write, sha, utc, verify, budget_snapshot, cost
from .protocol import ARMS
from .statistics import comparisons
from .run import rows, export, FROZEN, verify_phase


def report():
    manifest = read(FROZEN)
    verify(manifest)
    verify_phase(OUT / 'B_MAIN_FREEZE.json')
    material = read(OUT / 'B_MATERIALIZED.json')
    from .audit import audit_b
    audit = audit_b(material)
    fixed = {p: evaluate(data['fitted_baselines'], data['learn'], data['test'])
             for p, data in material['people'].items()}
    write(OUT / 'BASELINES.json', {'people': {p: {'fitted': data['fitted_baselines'], 'tests': fixed[p],
          'prior_alignment': data['prior_alignment'],
          'test_stratum_totals': {name: {stratum: sum(r['utility'] for r in policy['rows']
              if data['prior_alignment'][next(m['cell_id'] for m in data['test'] if m['id'] == r['moment_id'])] == aligned)
              for stratum, aligned in (('prior_aligned', True), ('counter_prior', False))}
              for name, policy in fixed[p].items()}}
          for p, data in material['people'].items()}})
    summary, detail, complete = [], [], True
    verdicts = {}
    for fmt in material['formats']:
        paired, person_results = {}, {}
        d5_total = Counter()
        format_complete = True
        for person, data in material['people'].items():
            by_arm = {}
            test_strata = {m['id']: 'prior_aligned' if data['prior_alignment'][m['cell_id']] else 'counter_prior'
                           for m in data['test']}
            learning_strata = {m['id']: 'prior_aligned' if data['prior_alignment'][m['cell_id']] else 'counter_prior'
                               for m in data['learn']}
            prefix = BASE / f'b/{fmt}/person{person}'
            for arm in ARMS:
                folder = prefix / arm / 'test'
                values = rows(folder / 'decisions.jsonl')
                completed = (folder / 'result.json').exists() and read(folder / 'result.json')['status'] == 'complete'
                expected = {m['id'] for m in data['test']}
                by_arm[arm] = {v['moment_id']: v for v in values}
                completed &= len(values) == 24 and set(by_arm[arm]) == expected
                format_complete &= completed
                learning = rows(prefix / 'R/learn/scores.jsonl') if arm == 'R' else []
                violations = sum(v['d5'] for v in values+learning)
                d5_total[arm] += violations
                for stratum in ('all', 'prior_aligned', 'counter_prior'):
                    selected_values = [v for v in values if stratum == 'all' or test_strata[v['moment_id']] == stratum]
                    selected_learning = [v for v in learning if stratum == 'all' or learning_strata[v['moment_id']] == stratum]
                    moments = [m for m in data['test'] if stratum == 'all' or test_strata[m['id']] == stratum]
                    summary.append({'format': fmt, 'persona': person, 'arm': arm, 'prior_stratum': stratum,
                                    'complete': completed, 'moments': len(selected_values),
                                    'utility': sum(v['utility'] for v in selected_values),
                                    'immediate_utility': sum(v['immediate_utility'] for v in selected_values),
                                    'information_bonus': sum(v['information_bonus'] for v in selected_values),
                                    'd5_learning_and_test': sum(v['d5'] for v in selected_values+selected_learning),
                                    'appropriate_asks': sum(v['appropriate_ask'] for v in selected_values),
                                    'ask_opportunities': sum(m['mode'] == 'ask' for m in moments),
                                    'known_repeats': sum(v['repeat_known'] for v in selected_values),
                                    'intrusions': sum(v['intrusion'] for v in selected_values),
                                    'inconvenient_opportunities': sum(m['mode'] == 'hold' for m in moments)})
                for v in values:
                    detail.append({**{k: v[k] for k in ('format', 'persona', 'arm', 'moment_id', 'action', 'valid',
                        'mode', 'immediate_utility', 'information_bonus', 'utility', 'd5', 'use_correct', 'acquired_before_test')},
                        'prior_stratum': test_strata[v['moment_id']]})
            selected = data['fitted_baselines']['selected']
            fixed_rows = {r['moment_id']: r for r in fixed[person][selected]['rows']}
            if all(set(values) == {m['id'] for m in data['test']} for values in by_arm.values()):
                paired[person] = [{**{arm: by_arm[arm][m['id']]['utility'] for arm in ARMS},
                                   'fixed': fixed_rows[m['id']]['utility']} for m in data['test']]
            person_results[person] = {'selected_baseline': selected,
                'selected_baseline_utility': fixed[person][selected]['total'],
                'oracle_utility': fixed[person]['oracle']['total'],
                'R_utility': sum(v['utility'] for v in by_arm['R'].values())}
        intervals = comparisons(paired) if format_complete else None
        d5_pass = d5_total['R'] == 0
        passed = format_complete and audit['passed'] and d5_pass and all(v['passed'] for v in intervals.values())
        verdicts[fmt] = {'complete': format_complete, 'passed': passed, 'd5_pass': d5_pass,
            'criterion_population': 'all_test_moments; prior strata are descriptive only',
            'd5_by_arm': dict(d5_total), 'all_arms_zero_d5': not any(d5_total.values()),
            'comparisons': intervals, 'people': person_results}
        complete &= format_complete
    for name, values in (('SUMMARY.csv', summary), ('UTILITY_DETAIL.csv', detail)):
        with (OUT / name).open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=list(values[0]) if values else [])
            writer.writeheader()
            writer.writerows(values)
    value = {'at_utc': utc(), 'complete': complete, 'formats': verdicts,
             'cost_usd_including_unknown': cost(), 'daily_budget': budget_snapshot(),
             'claim_ceiling': 'Learning when to speak in these synthetic people, beyond fixed rules; no subjective agency.',
             'F1_status': 'not_started_must_be_a_new_frozen_experiment_after_U3b'}
    write(OUT / 'RESULTS.json', value)
    export()
    raw = {p.relative_to(OUT).as_posix(): sha(p) for p in (OUT / 'raw').rglob('*') if p.is_file()}
    write(OUT / 'CLOSE.json', {'closed_at_utc': utc(), 'complete': complete,
          'source_manifest_sha256': sha(FROZEN), 'results_sha256': sha(OUT / 'RESULTS.json'),
          'raw_sha256': raw, 'source_hashes_verified': True})
    return value
