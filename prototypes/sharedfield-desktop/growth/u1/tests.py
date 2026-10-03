"""Zero-cloud engineering acceptance; not an empirical learning result."""
import ast
import contextlib
import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from growthlab.forks import fork_storage
from growthlab.records import ROOT, write_json
from .conventions import ConventionLibrary, normalize, trigger_matches
from .fixtures import build, correction, teaching
from .harness import byte_check, consolidate, decision, ingest
from .plan import BASE, OUT, source_hashes
from .protocol import (DECISION_ORDER, MEMORY_LIMIT, compact, decision_packet, decision_schema,
                       keyword_score, parse_decision, sleep_schema)


class FakeClient:
    """Fixture outputs only; no network and never included in empirical scores."""
    def __init__(self, folder, output):
        self.folder, self.output, self.records = Path(folder), output, []
        self.folder.mkdir(parents=True, exist_ok=True)

    def call(self, messages, schema, context, **kwargs):
        self.records.append({'messages': messages, 'schema': schema, 'context': context})
        return self.output, {'cost_usd': 0, 'latency_s': 0, 'offline_fixture': True}

    def log(self, value):
        self.records.append(value)

    def parsed(self, okay, context):
        self.last_parse = okay


def valid_output(fixture, label='true'):
    return compact({'reason': '工程验收固定输出，不是模型结果。', **fixture['target'][label], 'reply': '收到。'})


class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build()
        BASE.mkdir(parents=True, exist_ok=True)
        cls.directory = Path(tempfile.mkdtemp(prefix='engineering_', dir=BASE))

    def setUp(self):
        self.case_dir = self.directory / self._testMethodName
        self.case_dir.mkdir()
        self.lib = ConventionLibrary(self.case_dir / 'state.sqlite')
        self.addCleanup(self.lib.close)
        self.f = self.data['conventions']['chain_code']

    def propose(self, f=None):
        f = f or self.f
        ids = ingest(self.lib, teaching(f))
        proposal = {'trigger': f['trigger'], 'meaning': f['meaning'], 'source_ids': [ids[0]], 'replaces': ''}
        return self.lib.propose(proposal, allowed_ids=ids), ids, proposal

    def test_citation_rejections(self):
        identity, ids, proposal = self.propose()
        fake = dict(proposal, source_ids=['f' * 32])
        with self.assertRaisesRegex(ValueError, 'missing_user_utterance'):
            self.lib.propose(fake, allowed_ids=fake['source_ids'])
        unrelated = self.lib.utterance('今天的杯子是透明的。', session_id='other')
        with self.assertRaisesRegex(ValueError, 'trigger_absent'):
            self.lib.propose(dict(proposal, source_ids=[unrelated]), allowed_ids=[unrelated])
        wrong = self.lib.utterance('纸鹤：未经明确更正，我也许想去别处。', session_id='vague')
        with self.assertRaisesRegex(ValueError, 'meaning_not_quoted'):
            self.lib.propose(dict(proposal, meaning='完全伪造的含义', source_ids=[wrong], replaces=identity), allowed_ids=[wrong])
        unsupported = self.lib.utterance('纸鹤也可以说短休安排在北侧长椅，只是讨论。', session_id='no-correction')
        with self.assertRaisesRegex(ValueError, 'no_contradictory_utterance'):
            self.lib.propose(dict(proposal, meaning=self.f['new_meaning'], source_ids=[unsupported], replaces=identity), allowed_ids=[unsupported])
        self.assertEqual(self.lib.cards()[0]['meaning'], self.f['meaning'])

    def test_situation_quote_cannot_forge_clock(self):
        f = self.data['conventions']['ua_promise']
        identity, ids, proposal = self.propose(f)
        for field, wrong in [('weekday', 0), ('after', '23:59'), ('event', 'logout')]:
            bad = copy.deepcopy(proposal)
            bad['trigger'][field] = wrong
            with self.assertRaisesRegex(ValueError, 'disagrees_with_quote'):
                self.lib.propose(bad, allowed_ids=ids)
        self.assertEqual(len(self.lib.cards()), 1)

    def test_matching_boundaries_and_superseded(self):
        identity, ids, proposal = self.propose()
        self.assertTrue(self.lib.annotate('  纸　鹤！ ', '2026-10-02T20:00:00', []))
        self.assertFalse(self.lib.annotate('折纸小鸟', '2026-10-02T20:00:00', []))
        new_ids = ingest(self.lib, correction(self.f))
        new = self.lib.propose(dict(proposal, meaning=self.f['new_meaning'], source_ids=[new_ids[0]], replaces=identity), allowed_ids=new_ids)
        annotations = self.lib.annotate('纸鹤', '2026-10-02T20:00:00', [])
        self.assertEqual([a['card_id'] for a in annotations], [new])
        self.assertEqual(next(c for c in self.lib.cards(active_only=False) if c['card_id'] == identity)['card_status'], 'superseded')
        promise = self.data['conventions']['ua_promise']['trigger']
        self.assertTrue(trigger_matches(promise, '你好', '2026-10-02T18:00:00', ['login']))
        for when, events in [('2026-10-02T17:59:00', ['login']), ('2026-10-03T19:00:00', ['login']), ('2026-10-02T19:00:00', [])]:
            self.assertFalse(trigger_matches(promise, '你好', when, events))

    def test_deletion_covers_versions_sources_and_derivatives(self):
        identity, ids, proposal = self.propose()
        sentinel = 'ONLY_DERIVED_SENTINEL_8f24b0'
        self.lib.reflect(sentinel, [ids[0]])
        new_ids = ingest(self.lib, correction(self.f))
        new = self.lib.propose(dict(proposal, meaning=self.f['new_meaning'], source_ids=[new_ids[0]], replaces=identity), allowed_ids=new_ids)
        self.lib.store.put('cache', {'cached': 'DELETION_CACHE_2ce94b'}, 'local_test', personal=True, parents=[new])
        self.lib.forget(new)
        self.assertFalse(self.lib.cards(active_only=False))
        self.assertFalse(self.lib.annotate('纸鹤', '2026-10-02T20:00:00', []))
        self.assertNotIn(ids[0], [s['utterance_id'] for s in self.lib.sources()])
        self.assertNotIn(new_ids[0], [s['utterance_id'] for s in self.lib.sources()])
        scan = byte_check(self.case_dir / 'state.sqlite', [self.f['trigger']['text'], self.f['meaning'], self.f['new_meaning'], sentinel, 'DELETION_CACHE_2ce94b'])
        self.assertTrue(scan['pass'], scan)

    def test_fork_independence_and_actual_fresh_process(self):
        identity, ids, proposal = self.propose()
        source = self.case_dir / 'state.sqlite'
        fork = self.case_dir / 'fork.sqlite'
        fork_storage(source, fork)
        with ConventionLibrary(fork) as other:
            other.forget(identity)
        self.assertEqual(len(self.lib.cards()), 1)
        code = "import json,os,sys; from u1.conventions import ConventionLibrary; x=ConventionLibrary(sys.argv[1]); print(json.dumps({'pid':os.getpid(),'cards':len(x.cards()),'matches':len(x.annotate('纸鹤','2026-10-02T20:00:00',[]))})); x.close()"
        child = subprocess.run([sys.executable, '-c', code, str(source)], capture_output=True, check=True,
                               env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8'))
        result = json.loads(child.stdout)
        self.assertNotEqual(result['pid'], os.getpid())
        self.assertEqual(result['cards'], 1)
        self.assertEqual(result['matches'], 1)
        write_json(self.case_dir / 'restart.json', result)

    def test_strict_order_and_actual_logged_harness_output(self):
        case = self.data['chain_cases'][0]
        text = valid_output(self.f)
        value = parse_decision(text, case)
        self.assertEqual(list(value), DECISION_ORDER)
        self.assertEqual(list(decision_schema(case)['json_schema']['schema']['properties']), DECISION_ORDER)
        fake = FakeClient(self.case_dir / 'mock', text)
        result = decision(self.lib, 'B', fake, case, self.f['target']['true'], {'offline_engineering': True})
        self.assertTrue(result['follows'])
        for invalid in [compact(dict(reversed(list(value.items())))), text[:-1] + ',"reason":"duplicate"}',
                        compact(dict(value, action='not-an-option')), compact(list(value.items())), 'not json']:
            with self.assertRaises((ValueError, TypeError)):
                parse_decision(invalid, case)
        self.assertTrue((fake.folder / 'decisions.jsonl').exists())

    def test_both_selected_fields_required_reply_never_scores(self):
        case = self.data['chain_cases'][0]
        value = json.loads(valid_output(self.f))
        value['action'] = 'A1'
        value['reply'] = self.f['meaning']
        fake = FakeClient(self.case_dir / 'mock', compact(value))
        result = decision(self.lib, 'B', fake, case, self.f['target']['true'], {})
        self.assertFalse(result['follows'])

    def test_A_B_bound_and_baseline_is_bm25(self):
        identity, ids, proposal = self.propose()
        self.lib.reflect('纸鹤表示' + self.f['meaning'], ids)
        for i in range(30):
            self.lib.utterance('无关的太阳能发电记录' * 100, session_id=f'noise{i}')
        case = self.data['chain_cases'][0]
        for arm in ('A', 'B'):
            packet = json.loads(decision_packet(self.lib, arm, case)[-1]['content'])
            self.assertLessEqual(len(compact(packet['memory']).encode()), MEMORY_LIMIT)
            self.assertTrue(any(self.f['meaning'] in compact(x) for x in packet['memory']))
            if arm == 'A':
                self.assertFalse(any(x['memory_kind'] == 'applied_convention' for x in packet['memory']))
                self.assertFalse(any('太阳能' in compact(x) for x in packet['memory']))
            else:
                self.assertTrue(any(x['memory_kind'] == 'applied_convention' for x in packet['memory']))

    def test_proposal_path_only_writes_after_validation(self):
        fixture = self.data['ub'][5]
        ids = ingest(self.lib, fixture['dialogue'])
        wanted = [i for i, r in zip(ids, fixture['dialogue']) if r['speaker'] == 'user']
        payload = {'proposals': [{'trigger': fixture['trigger'], 'meaning': fixture['meaning'], 'source_ids': wanted, 'replaces': ''}]}
        fake = FakeClient(self.case_dir / 'mock', compact(payload))
        report = consolidate(self.lib, 'B', fake, ids, {'offline_engineering': True})
        self.assertTrue(report['accepted'][0]['accepted'])
        self.assertTrue(keyword_score(self.lib.cards()[0], fixture))
        self.assertEqual(len(self.lib.cards()[0]['source_ids']), 2)

    def test_uc_omission_never_removes_or_overwrites(self):
        identity, ids, proposal = self.propose()
        original = copy.deepcopy(self.lib.cards())
        for i in range(10):
            extra = self.lib.utterance(f'花盆第{i}天长了一片叶子', session_id=f'uc{i}')
            fake = FakeClient(self.case_dir / f'mock{i}', compact({'proposals': []}))
            consolidate(self.lib, 'B', fake, ids + [extra], {'round': i})
        self.assertEqual(self.lib.cards(), original)

    def test_scripts_counts_disjointness_and_no_answer_prompt_leakage(self):
        self.assertEqual(len(self.data['ua_cases']), 30)
        self.assertEqual(len(self.data['chain_cases']), 60)
        self.assertEqual(len(self.data['ub']), 10)
        self.assertEqual(sum(x['teaching_mode'] == 'explicit' for x in self.data['ub']), 5)
        forbidden = {x['trigger']['text'] for x in self.data['conventions'].values()}
        self.assertFalse(forbidden & {x['trigger']['text'] for x in self.data['ub']})
        for r, i in zip(self.data['chain_teaching'], self.data['chain_unrelated']):
            self.assertEqual(len(r['utterance_text']), len(i['utterance_text']))
        for case in self.data['ua_cases'] + self.data['chain_cases']:
            packet = json.loads(decision_packet(self.lib, 'B', case)[-1]['content'])
            self.assertFalse({'target', 'keywords', 'fixture_id', 'family', 'condition'} & set(packet))
            self.assertEqual(len(packet['interpretation_choices']), 5)
            self.assertEqual(len(packet['action_choices']), 5)

    def test_reusable_library_has_no_harness_dependencies(self):
        path = ROOT / 'u1/conventions/core.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertNotIn('u1.fixtures', imports)
        self.assertNotIn('u1.protocol', imports)
        self.assertNotIn('u1.harness', imports)
        self.assertIn('growthlab.state', imports)

    def test_inherited_budget_unknown_reservation_and_privacy_payload(self):
        from growthlab.models import Cloud, MODEL, ROUTE
        endpoint = {'data': [{'model_id': MODEL, 'tag': ROUTE,
                             'pricing': {'prompt': '.000001', 'completion': '.000002'},
                             'supported_parameters': ['response_format', 'max_tokens', 'temperature', 'reasoning']}]}
        capture = []
        def fake_request(url, payload, headers=None, timeout=60):
            capture.append(payload)
            return {'choices': [{'message': {'content': '{}'}, 'finish_reason': 'stop'}],
                    'usage': {'cost': .001, 'prompt_tokens': 10, 'completion_tokens': 2}, 'provider': 'offline_mock'}
        with mock.patch('growthlab.models.read_key', return_value='OFFLINE_DUMMY_NOT_A_CREDENTIAL'), \
                mock.patch('growthlab.models.urllib.request.urlopen', side_effect=lambda *a, **k: io.BytesIO(json.dumps(endpoint).encode())):
            cloud = Cloud(budget_path=self.case_dir / 'mock_budget.sqlite')
            try:
                with mock.patch('growthlab.models.request_json', side_effect=fake_request):
                    cloud.decide([{'role': 'user', 'content': 'offline only'}], response_format=sleep_schema('A'))
                payload = capture[0]
                self.assertTrue(payload['provider']['zdr'])
                self.assertEqual(payload['provider']['only'], [ROUTE])
                self.assertFalse(payload['provider']['allow_fallbacks'])
                self.assertEqual(payload['provider']['data_collection'], 'deny')
                with mock.patch('growthlab.models.request_json', side_effect=RuntimeError('http_502')):
                    with self.assertRaisesRegex(RuntimeError, 'http_502'):
                        cloud.decide([{'role': 'user', 'content': 'offline only'}], response_format=sleep_schema('A'))
                ledger = list(cloud.db.execute('SELECT usd,status FROM charges'))
                self.assertEqual(len(ledger), 2)
                self.assertEqual(ledger[0], (.001, 'reported'))
                self.assertGreaterEqual(ledger[1][0], .05)
                self.assertEqual(ledger[1][1], 'reserved_unknown')
                with cloud.db:
                    cloud.db.execute('INSERT INTO charges VALUES (?,?,?)', ('other_component', 4.94, 'reported'))
                with self.assertRaisesRegex(ValueError, 'budget_stop'):
                    cloud.decide([{'role': 'user', 'content': 'offline only'}], response_format=sleep_schema('A'))
                self.assertEqual(cloud.db.execute('SELECT COUNT(*) FROM charges').fetchone()[0], 3)
            finally:
                cloud.db.close()

    def test_ua_full_job_counts_and_false_memory_gate(self):
        from .run import worker_ua
        class ChoiceClient(FakeClient):
            def call(self, messages, schema, context, **kwargs):
                packet = json.loads(messages[-1]['content'])
                # This is a deliberately scripted offline protocol fixture, not
                # a learned response and never included in real gate evidence.
                chosen = next(f for f in build()['conventions'].values()
                              if f['fixture_id'].startswith('ua_') and f['interpretation_choices'] == packet['interpretation_choices'])
                return valid_output(chosen, 'false' if context['condition'] == 'false' else 'true'), {'cost_usd': 0, 'offline_fixture': True}
        folder = self.case_dir / 'ua_mock'
        client = ChoiceClient(folder, '')
        report = worker_ua({'folder': str(folder), 'main_comparison': True, 'config_name': 'offline_mock'}, self.data, client)
        self.assertEqual(report['decisions'], 180)
        self.assertEqual(report['expected'], 180)
        self.assertEqual(len(report['table']), 18)
        self.assertTrue(report['pass'])

    def test_emotion_is_reported_not_promoted_to_chain_gate(self):
        from .run import chain_summary
        def rows(path):
            group, phase = path.split('/')[-2:]
            values = []
            for case in self.data['chain_cases']:
                if phase != 'initial' and case['split'] != 'T1':
                    continue
                f = self.data['conventions'][case['fixture_id']]
                label = 'new' if phase == 'corrected' else 'true'
                selected = dict(f['target'][label])
                if group in ('B_I', 'B_N') or phase == 'deleted' or (phase == 'corrected' and case['family'] == 'emotion'):
                    selected = {'interpretation': 'I5', 'action': 'A5'}
                if phase == 'deleted' and case['family'] == 'emotion':
                    selected = dict(f['target']['true'])
                values.append({'family': case['family'], 'split': case['split'], 'selected': selected,
                               'valid': True, 'follows': selected == f['target'][label]})
            return values
        provenance = []
        for family in ('code', 'emotion', 'promise'):
            for status in ('active', 'superseded'):
                provenance.append({'card_id': family + status, 'card_status': status,
                                   'trigger_text': self.data['conventions']['chain_' + family]['trigger']['text'],
                                   'correction_parents': [family + 'superseded'] if status == 'active' and family != 'emotion' else []})
        result = {'Uc': {'pass': True}, 'steps': {
            'B_R_correct_learn': {'state': {'provenance': provenance}},
            'B_R_delete': {'byte_check': {'pass': True}},
        }}
        with mock.patch('u1.run.load_rows', side_effect=rows), mock.patch('u1.run.read', return_value=self.data):
            summary = chain_summary('offline', result)
        self.assertTrue(summary['pass'])
        self.assertFalse(summary['correction_provenance_by_family']['emotion'])
        self.assertFalse(summary['deletion_rates']['emotion']['true']['pass'])


KEY_MEANINGS = {
    'turn_context': 'public conversation/time/events context',
    'previous_dialogue': 'prior public dialogue rows', 'speaker': 'who said an original utterance',
    'utterance_text': 'verbatim spoken text', 'occurred_at': 'ISO local wall time of event',
    'event_labels': 'public observed event labels', 'scene_description': 'public scene description',
    'current_utterance': 'present user utterance', 'memory': 'bounded recalled memory entries',
    'interpretation_choices': 'allowed interpretation options', 'action_choices': 'allowed action options',
    'choice_id': 'opaque option identifier', 'choice_text': 'option meaning in prose',
    'memory_kind': 'memory entry category', 'card_id': 'persistent convention record identity',
    'source_ids': 'cited user utterance identities', 'annotation_text': 'program-generated applicable convention prose',
    'card_status': 'P6 active/superseded state', 'trigger': 'structured convention trigger',
    'kind': 'trigger matcher type only', 'text': 'verbatim trigger phrase only', 'weekday': 'Monday=0 weekday predicate',
    'after': 'HH:MM inclusive lower clock bound', 'event': 'single required observed event label',
    'meaning': 'quoted user-defined convention meaning', 'utterance_id': 'persistent original utterance identity',
    'session_id': 'original conversation session identity', 'reflection_text': 'plain-text end-session reflection',
    'original_utterances': 'allowed original evidence rows', 'replaces': 'prior active convention identity',
    'proposals': 'untrusted convention proposals',
    'reason': 'pre-choice brief rationale only', 'interpretation': 'selected interpretation option identity only',
    'action': 'selected action option identity only', 'reply': 'free reply text audited but not scored',
}


def audit_keys():
    seen = {}
    def walk(value, path='packet'):
        if isinstance(value, dict):
            for key, item in value.items():
                if key not in KEY_MEANINGS:
                    raise AssertionError('unregistered_key:' + key)
                seen.setdefault(key, set()).add(path + '.' + key)
                walk(item, path + '.' + key)
        elif isinstance(value, list):
            for item in value:
                walk(item, path + '[]')
    data = build()
    with tempfile.TemporaryDirectory(dir=BASE) as tmp:
        for family in ('code', 'emotion', 'promise'):
            f = data['conventions']['chain_' + family]
            with ConventionLibrary(Path(tmp) / (family + '.sqlite')) as lib:
                ids = ingest(lib, teaching(f))
                proposal = {'trigger': f['trigger'], 'meaning': f['meaning'], 'source_ids': [ids[0]], 'replaces': ''}
                lib.propose(proposal, allowed_ids=ids)
                lib.reflect(f['meaning'], ids)
                for arm in ('A', 'B'):
                    for case in data['ua_cases'] + data['chain_cases']:
                        walk(json.loads(decision_packet(lib, arm, case)[-1]['content']))
                    fake = FakeClient(Path(tmp) / 'mock', compact({'reflection_text': '工程文字反思'}) if arm == 'A' else compact({'proposals': []}))
                    consolidate(lib, arm, fake, ids, {})
                    walk(json.loads(fake.records[0]['messages'][-1]['content']))
                walk({'proposals': [proposal]})
                walk(json.loads(valid_output(f)))
    # JSON Schema's type/properties/required refer solely to schema grammar,
    # while message envelopes' role/content refer solely to transport messages.
    return {'pass': True, 'keys': {k: {'meaning': KEY_MEANINGS[k], 'paths': sorted(v)} for k, v in sorted(seen.items())},
            'schema_envelope_keys': 'type/properties/required/additionalProperties/items/enum/minimum/maximum/maxLength/minItems/maxItems are JSON Schema grammar only.',
            'transport_envelope_keys': 'role/content are OpenRouter message envelope only; model input data uses speaker/utterance_text instead.'}


def engineering():
    buffer = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Acceptance)
    result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(suite)
    key_audit = audit_keys()
    OUT.mkdir(parents=True, exist_ok=True)
    value = {'pass': result.wasSuccessful() and key_audit['pass'], 'tests_run': result.testsRun,
             'failures': len(result.failures), 'errors': len(result.errors), 'cloud_calls': 0, 'cloud_cost_usd': 0,
             'run_folder': str(Acceptance.directory), 'source_sha256': source_hashes(),
             'key_audit': key_audit, 'test_output': buffer.getvalue(),
             'claim_ceiling': 'Offline engineering acceptance only. Real model order, learning and causal gates remain untested.'}
    write_json(OUT / 'engineering.json', value)
    (OUT / 'ENGINEERING.md').write_text('# U1 engineering acceptance\n\n'
        + ('PASS' if value['pass'] else 'FAIL') + f" — {value['tests_run']} offline tests, no cloud calls.\n\n"
        + 'Covers forged IDs, unsupported citations, missing contradiction, forged time predicates, annotation hit/miss/status, '
          'correction-chain deletion including derived caches, fresh-process reload, independent forks, strict ordered JSON, '
          'joint interpretation/action scoring, memory byte parity, BM25, corpus separation and prompt key semantics.\n\n'
        + 'The library supports exact quoted triggers and a declared time grammar. It is not a semantic contradiction oracle.\n\n'
        + 'This report does not establish a learning effect or real model compliance; those require the frozen live run.\n', encoding='utf-8')
    return value


if __name__ == '__main__':
    print(json.dumps(engineering(), ensure_ascii=False, indent=2))
