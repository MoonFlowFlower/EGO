import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from growthlab.records import ROOT
from u2.study import sha, write
from u2.test_protocol import FakeClient
from u2.report import summarize
from u2.supplement_v2.check import candidates
from . import main, report
from .leakage import assign, audit, conflicting_pairs
from .screen import old_pool, read


def fake_worker(path):
    job = read(path)
    with patch.object(main, 'FROZEN', Path(job['test_manifest'])), patch.object(main, 'Client', lambda folder, total_cap: FakeClient(folder, job['items'])):
        main.worker(path)


class MainTests(unittest.TestCase):
    def test_unmodified_scorer_and_semantic_leak_checks(self):
        self.assertIs(report.summarize, summarize)
        items = old_pool()[0] + candidates()
        indexed = {i['id']: i for i in items}
        group = [indexed[i] for i in ('P02', 'Q51', 'Q59', 'W41', 'P71', 'Q08', 'Q58', 'Q65', 'Q49')]
        self.assertFalse(audit({'1': group})['passed'])
        people, pairs = assign(group)
        self.assertTrue(audit(people)['passed'])
        self.assertEqual(set(i['id'] for g in people.values() for i in g), set(i['id'] for i in group))
        self.assertEqual(people, assign(group)[0])
        self.assertTrue(any(p['a'] == 'Q49' and p['b'] == 'Q65' for p in pairs))
        leaked = copy.deepcopy(indexed['P02'])
        leaked['teaching'][0]['messages'][0]['text'] = indexed['Q51']['hidden_answer']
        self.assertFalse(audit({'1': [indexed['Q51'], leaked]})['passed'])

    def test_actual_worker_fresh_process_and_readonly_store(self):
        indexed = {i['id']: i for i in old_pool()[0] + candidates()}
        items = [indexed[i] for i in ('P01', 'Q49', 'W01')]
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs/u2') as temporary:
            base = Path(temporary); manifest = base / 'manifest.json'
            write(manifest, {'source_sha256': {}, 'cumulative_cap_usd': .90})
            store = base / 'learn/state.sqlite'
            results = []
            for operation in ('learn', 'test'):
                folder = base / operation; folder.mkdir()
                job = {'folder': str(folder), 'test_manifest': str(manifest), 'manifest_sha256': sha(manifest),
                       'operation': operation, 'items': items, 'persona': '1', 'arm': 'B', 'group': 'R', 'store': str(store)}
                write(folder / 'job.json', job)
                p = subprocess.run([sys.executable, '-m', 'u2.round2.test_main', 'worker', str(folder / 'job.json')], cwd=ROOT, capture_output=True, timeout=60,
                                   env=dict(os.environ, PYTHONIOENCODING='utf-8'))
                self.assertEqual(p.returncode, 0, p.stderr.decode())
                results.append(read(folder / 'result.json'))
                self.assertEqual(results[-1]['status'], 'complete', results[-1])
            self.assertNotEqual(results[0]['pid'], results[1]['pid'])
            hashes = read(base / 'test/storage_hash.json')
            self.assertTrue(hashes['unchanged'])
            learned = read(base / 'learn/learned.json')
            self.assertTrue(learned['questions'][0]['asked'])
            from companion.memory import Memory
            with Memory.readonly(store) as memory:
                self.assertIn(indexed['Q49']['hidden_answer'], [s['utterance_text'] for s in memory.library.sources()])

    def test_underfunded_main_creates_no_claim_and_does_not_call_worker(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'runs/u2') as directory:
            base = Path(directory); frozen = base / 'frozen.json'
            write(frozen, {'source_sha256': {}})
            class Underfunded:
                def snapshot(self): return {'remaining_usd': .899, 'used_usd': .101}
            with patch.object(main, 'BASE', base), patch.object(main, 'OUT', base), patch.object(main, 'FROZEN', frozen), patch.object(main, 'DailyLedger', Underfunded), patch.object(main, 'execute') as execute:
                with self.assertRaisesRegex(main.Stop, 'start_on_another_day'): main.run()
                execute.assert_not_called()
            self.assertFalse((base / 'main.claim').exists())
            self.assertEqual(read(base / 'MAIN_DEFERRED.json')['needed_usd'], .90)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'worker': fake_worker(sys.argv[2])
    else: unittest.main()
