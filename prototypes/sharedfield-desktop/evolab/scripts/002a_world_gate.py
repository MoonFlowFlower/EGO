"""F1: fixed poison staircase, scripted policies only, disjoint f1 domain."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from evolab.config import setup
from evolab.v002.config import ladder
from evolab.v002.rollout import rollout
from evolab.v002.records import write_json, thermal, progress, verify_protected


def gate(c):
    rows = []
    for regime, arms in [('drift', ('H', 'N', 'F')), ('static', ('H',))]:
        for arm in arms:
            begin = time.perf_counter()
            scores, result = rollout(c, regime, arm, 1024, 0, 'f1', telemetry=True)
            raw_dir = Path('runs/002A/F1') / f'energy{c.initial_energy}_poison{c.poison_cost}'
            raw_dir.mkdir(parents=True, exist_ok=True)
            metrics = result['metrics']
            torch.save(dict(scores=scores.cpu(), good=metrics.good.cpu(), bad=metrics.bad.cpu(),
                            survived_first=metrics.survived_first.cpu(),
                            recovery_start=metrics.start.cpu(), recovery_duration=metrics.duration.cpu(),
                            recovery_observed=metrics.observed.cpu()), raw_dir/f'{regime}_{arm}.pt')
            row = dict(regime=regime, arm=arm, episodes=1024, **result['summary'],
                       seconds=time.perf_counter()-begin, thermal=thermal())
            rows.append(row)
            print(row, flush=True)
    h, n, f, static = [row['survival'] for row in rows]
    checks = dict(drift_h=h >= .9, drift_n=n <= .5*h, drift_f=f <= .5*h, static_h=static >= .9)
    return dict(rows=rows, checks=checks, passed=all(checks.values()))


if __name__ == '__main__':
    setup(); verify_protected()
    out = Path('evidence/002A/f1_world_gate.json')
    if out.exists():
        raise RuntimeError('F1 results already exist; do not overwrite/reselect')
    started = time.perf_counter()
    results = dict(domain='f1', domain_id=410000, master_seed=20261002,
                   run_seed=0, episodes=1024, selection='first passing fixed step',
                   initial_thermal=thermal(), levels=[], selected_poison=None)
    try:
        for poison in (.05, .10, .15, .20, .30):
            result = gate(ladder(0, poison))
            result['poison_cost'] = poison
            results['levels'].append(result)
            results['seconds'] = time.perf_counter()-started
            if result['passed']:
                results['selected_poison'] = poison
            write_json(out, results)
            if result['passed']:
                break
        results['status'] = 'PASS' if results['selected_poison'] is not None else 'STOP_W_EXHAUSTED'
        write_json(out, results)
    except BaseException as error:
        results.update(status='FAILED', error=repr(error), seconds=time.perf_counter()-started)
        write_json(out, results)
        progress('F1 工程失败', f'- 证据：{out.as_posix()}；错误：{error!r}。保留全部已完成阶梯，未访问保留集。')
        raise
