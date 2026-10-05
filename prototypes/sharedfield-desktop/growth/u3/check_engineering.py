"""Zero-cloud verification; fake decisions are explicitly engineering fixtures."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest

from growthlab.records import ROOT
from companion.memory import Memory
from p7.proxy import prepare_request, PROVIDER
from .common import read, write, sha, OUT, budget_snapshot, pins
from .materials import build
from .selection import b_materialize
from .protocol import MODEL, bundle_packet
from .study import learn, fork_store, b_test
from .test_protocol import output


class OfflineClient:
    def __init__(self, job):
        self.folder = Path(job['folder'])
        self.job = job
        self.by_id = {m['id']: m for stage in ('learn', 'test') for m in job['person'][stage]}
        self.calls = 0
        self.max_request_bytes = 0

    def call(self, messages, context, *, schema):
        request = {'model': MODEL, 'stream': False, 'temperature': 0, 'max_tokens': 1024,
            'reasoning': {'enabled': False}, 'response_format': schema, 'messages': messages}
        prepare_request(request, model=MODEL, provider=PROVIDER)
        self.max_request_bytes = max(self.max_request_bytes, len(json.dumps(request, ensure_ascii=False).encode()))
        moment = self.by_id[context['moment_id']]
        chosen = moment['mode'] if moment['mode'] != 'hold' else 'quiet'
        primary = output(moment, chosen, self.job['format'])
        self.calls += 1
        if context['stage'] == 'b_test':
            return {'decisions': [primary, output(moment['use_probe'], moment['use_probe']['target'], self.job['format'])]}, {'offline_fixture': True, 'cost_usd': 0}
        return primary, {'offline_fixture': True, 'cost_usd': 0}

    def parsed(self, valid):
        if not valid:
            raise AssertionError('invalid_offline_fixture')


def offline_worker(path):
    def denied(*args, **kwargs):
        raise RuntimeError('network_forbidden_in_engineering')
    socket.socket = denied
    job = read(path)
    client = OfflineClient(job)
    if job['operation'] == 'learn': learn(job, client)
    elif job['operation'] == 'fork': fork_store(job)
    elif job['operation'] == 'test': b_test(job, client)
    else: raise ValueError('unknown_offline_operation')
    write(Path(job['folder']) / 'offline_result.json', {'pid': os.getpid(), 'operation': job['operation'],
          'simulated_decisions': client.calls, 'cloud_calls': 0, 'max_request_bytes': client.max_request_bytes})


def process_check():
    material = build()
    person = b_materialize(material['b'], {f'{p}:{c["id"]}': 'reply' for p, cs in material['b'].items() for c in cs})['1']
    results = []
    with tempfile.TemporaryDirectory(dir=ROOT / 'runs') as directory:
        base = Path(directory)
        def execute(name, operation, arm, **fields):
            folder = base / name
            folder.mkdir(parents=True)
            job = {'folder': str(folder), 'operation': operation, 'arm': arm,
                   'persona': '1', 'format': 'S1', 'person': person, **fields}
            write(folder / 'offline_job.json', job)
            subprocess.run([sys.executable, '-m', 'u3.check_engineering', 'worker', str(folder / 'offline_job.json')],
                           cwd=ROOT, capture_output=True, check=True, timeout=60)
            result = read(folder / 'offline_result.json')
            result['stage'] = name
            results.append(result)
            return folder
        original = execute('R/learn', 'learn', 'R') / 'state.sqlite'
        original_hash = sha(original)
        for arm in ('R', 'I', 'N', 'R_SHUFFLED'):
            if arm != 'R':
                store = execute(arm+'/learn', 'fork', arm, related_store=str(original)) / 'state.sqlite'
            else:
                store = original
            tested = execute(arm+'/test', 'test', arm, store=str(store))
            check = read(tested / 'storage_hash.json')
            assert check['unchanged'] and check['learning_pid'] != check['testing_pid']
            scored = [json.loads(s) for s in (tested / 'decisions.jsonl').read_text(encoding='utf-8').splitlines()]
            assert len(scored) == 24
            if arm in ('N', 'I'):
                assert sum(r['information_bonus'] for r in scored) == 0, 'guessed answers cannot receive acquisition bonus'
        assert sha(original) == original_hash
    return {'passed': True, 'fresh_process_checks': 4, 'network_blocked_in_workers': True,
            'stages': results, 'claim': 'scripted fixtures only, no model learning evidence'}


def check():
    start = time.monotonic()
    suite = unittest.defaultTestLoader.loadTestsFromNames([
        'u3.test_protocol', 'u3.test_study', 'u3.test_client', 'u3.test_run', 'u3.test_report', 'u2.test_storage', 'companion.test_daily'])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    process = process_check() if result.wasSuccessful() else {'passed': False, 'not_run': 'unit_failure'}
    report = {'at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
              'passed': result.wasSuccessful() and process['passed'], 'tests_run': result.testsRun,
              'failures': len(result.failures), 'errors': len(result.errors),
              'seconds': time.monotonic()-start, 'process_checks': process, 'cloud_calls': 0,
              'new_cloud_cost_usd': 0, 'daily_budget_readonly': budget_snapshot(),
              'code_sha256': {p: h for p, h in pins().items() if p.endswith('.py')},
              'not_verified': ['U3a screening or model effects', 'U3b learning beyond baselines',
                               'F1 behavioural forgetting', 'real owner use or MC/AIRI integration']}
    write(OUT / 'ENGINEERING.json', report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('process_checks', 'code_sha256')}, ensure_ascii=False))
    if not report['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs='?', choices=('check', 'worker'), default='check')
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()
    offline_worker(args.path) if args.command == 'worker' else check()
