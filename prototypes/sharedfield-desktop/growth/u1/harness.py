"""Deterministic scoring and auditable single-request transport."""
import json
import os
import time
from pathlib import Path

from growthlab import models
from growthlab.models import Cloud
from growthlab.records import ROOT, telemetry, write_json
from .conventions import ConventionLibrary
from .protocol import (A_SLEEP_SYSTEM, B_SLEEP_SYSTEM, compact, memory, decision_packet,
                       decision_schema, sleep_schema, parse_decision, follows)

RETRYABLE = {'http_429', 'http_502', 'http_503', 'http_504', 'TimeoutError', 'URLError'}


class Stop(RuntimeError):
    pass


class Client:
    def __init__(self, config, folder):
        self.folder, self.config = Path(folder), config
        self.folder.mkdir(parents=True, exist_ok=True)
        self.started = time.time()
        self.previous_sample = 0
        self.invalid_streak = 0
        self.calls = 0
        self.check_resources()
        self.cloud = Cloud(model=config['model'], route=config['route'],
                           budget_path=ROOT / 'runs/phase1/budget.sqlite', limit=5)
        # Growthlab Cloud owns routing/reservation/settlement unchanged. Its
        # transport hook is scoped to this serial worker process to retain the
        # complete HTTP JSON (including reasoning fields), never request headers.
        self.original_request = models.request_json
        def capture(url, payload, headers=None, timeout=60):
            self.log({'record_type': 'wire_request', 'url': url, 'payload': payload})
            response = self.original_request(url, payload, headers, timeout)
            self.log({'record_type': 'wire_response', 'response': response})
            return response
        models.request_json = capture

    def close(self):
        models.request_json = self.original_request
        self.cloud.db.close()

    def log(self, row):
        with (self.folder / 'calls.jsonl').open('a', encoding='utf-8') as out:
            out.write(compact({'unix_s': time.time(), 'pid': os.getpid(), **row}) + '\n')

    def check_resources(self):
        if time.time() - self.started > 3600:
            raise Stop('lane_wall_limit')
        if time.time() - self.previous_sample >= 30:
            info = telemetry()
            self.previous_sample = time.time()
            self.log({'record_type': 'telemetry', **info})
            if info['ac_online'] is not True:
                raise Stop('ac_required')

    def call(self, messages, schema, context, *, sleep=False):
        self.check_resources()
        max_tokens = 8192 if self.config['reasoning'] else (2048 if sleep else 1024)
        for attempt in (1, 2):
            self.check_resources()
            before = {x[0] for x in self.cloud.db.execute('SELECT id FROM charges')}
            self.log({'record_type': 'request', 'context': context, 'attempt': attempt,
                      'messages': messages, 'response_format': schema, 'max_tokens': max_tokens,
                      'reasoning': self.config['reasoning'], 'config': self.config})
            try:
                output, meta = self.cloud.decide(messages, response_format=schema, max_tokens=max_tokens,
                                                 reasoning=self.config['reasoning'])
            except (RuntimeError, ValueError) as error:
                code = str(error)
                charges = [dict(zip(('charge_id', 'usd', 'status'), row))
                           for row in self.cloud.db.execute('SELECT id,usd,status FROM charges') if row[0] not in before]
                self.log({'record_type': 'transport_error', 'context': context, 'attempt': attempt,
                          'error': code, 'shared_ledger_delta_unattributed': charges})
                if code not in RETRYABLE or attempt == 2:
                    raise Stop(code) from None
                time.sleep(30)
                continue
            self.calls += 1
            self.log({'record_type': 'response', 'context': context, 'attempt': attempt, 'output': output, 'meta': meta})
            return output, meta

    def parsed(self, okay, context):
        self.invalid_streak = 0 if okay else self.invalid_streak + 1
        if self.invalid_streak >= 2:
            self.log({'record_type': 'protocol_stop', 'context': context, 'invalid_streak': self.invalid_streak})
            raise Stop('two_consecutive_invalid_outputs')


def ingest(lib, dialogue):
    return [lib.utterance(row['utterance_text'], session_id=row['session_id'], speaker=row['speaker']) for row in dialogue]


def consolidate(lib, arm, client, source_ids, context):
    sources = [{k: v for k, v in s.items() if k != 'type'} for s in lib.sources() if s['utterance_id'] in source_ids]
    if not sources:
        return {'status': 'no_evidence_noop', 'accepted': []}
    query = ' '.join(x['utterance_text'] for x in sources)
    packet = {'original_utterances': sources, 'memory': memory(lib, arm, query)}
    messages = [{'role': 'system', 'content': B_SLEEP_SYSTEM if arm == 'B' else A_SLEEP_SYSTEM},
                {'role': 'user', 'content': compact(packet)}]
    output, meta = client.call(messages, sleep_schema(arm), context, sleep=True)
    results = []
    valid = False
    try:
        payload = json.loads(output)
        if arm == 'A':
            if not isinstance(payload, dict) or set(payload) != {'reflection_text'}:
                raise ValueError('reflection_envelope')
            identity = lib.reflect(payload['reflection_text'], source_ids)
            results.append({'accepted': True, 'record_id': identity})
        else:
            if not isinstance(payload, dict) or set(payload) != {'proposals'} or not isinstance(payload['proposals'], list) or len(payload['proposals']) > 12:
                raise ValueError('proposal_envelope')
            for proposal in payload['proposals']:
                try:
                    identity = lib.propose(proposal, allowed_ids=source_ids)
                    results.append({'accepted': True, 'card_id': identity})
                except (ValueError, KeyError, TypeError) as error:
                    results.append({'accepted': False, 'reason': str(error) if isinstance(error, ValueError) else 'proposal_schema'})
        valid = True
    except (ValueError, TypeError, KeyError):
        results.append({'accepted': False, 'reason': 'invalid_consolidation_envelope'})
    client.log({'record_type': 'consolidation_score', 'context': context, 'results': results, 'valid': valid})
    client.parsed(valid, context)
    return {'status': 'returned', 'accepted': results, 'valid': valid, 'meta': meta}


def decision(lib, arm, client, case, target, context):
    messages = decision_packet(lib, arm, case)
    output, meta = client.call(messages, decision_schema(case), context)
    parsed, error = None, None
    try:
        parsed = parse_decision(output, case)
    except (ValueError, TypeError, KeyError):
        error = 'invalid_decision_protocol'
    supplied = json.loads(messages[-1]['content'])['memory']
    value = {'context': context, 'case_id': case['case_id'], 'family': case['family'], 'split': case['split'],
             'arm': arm, 'valid': parsed is not None, 'selected': parsed,
             'follows': follows(parsed, target), 'target': target, 'error': error,
             'applied_cards': [x for x in supplied if x.get('memory_kind') == 'applied_convention'],
             'memory_bytes': len(compact(supplied).encode('utf-8')), 'meta': meta}
    client.log({'record_type': 'decision_score', **value})
    # Persist score before the second invalid response can halt this lane.
    with (client.folder / 'decisions.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(compact(value) + '\n')
    client.parsed(parsed is not None, context)
    return value


def rate(rows):
    return {'n': len(rows), 'follows': sum(x['follows'] for x in rows),
            'rate': sum(x['follows'] for x in rows) / len(rows) if rows else None,
            'valid': sum(x['valid'] for x in rows)}


def byte_check(path, needles):
    """Only live saved-state files and SQLite sidecars, never fixture/audit logs."""
    path = Path(path)
    files = sorted(path.parent.glob(path.name + '*'))
    hits = []
    for file in files:
        data = file.read_bytes()
        for number, text in enumerate(needles):
            variants = [text.encode('utf-8'), json.dumps(text, ensure_ascii=True)[1:-1].encode('ascii')]
            if any(value and value in data for value in variants):
                hits.append({'file': file.name, 'needle_number': number})
    return {'pass': not hits, 'files_checked': [p.name for p in files], 'needles_checked': len(needles), 'hits': hits}
