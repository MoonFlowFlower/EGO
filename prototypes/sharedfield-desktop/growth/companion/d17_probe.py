"""Synthetic engineering probe, independent of U4's frozen test inputs."""
import argparse
import json
import statistics
import time

from growthlab.records import ROOT
from p7.proxy import AuditLog
from u2.protocol import decision_schema, packet, score
from u3.common import read, write
from u3.statistics import quantile
from .chatgpt import Transport
from .chatgpt_oauth import ChatGPTError
from .model import Model

OUT = ROOT / 'evidence/d17'
MODEL = 'gpt-6-astra'
EFFORT = 'medium'
ROUND = 2


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    client = Model(Transport(MODEL, synthetic=True), AuditLog(ROOT / 'runs/d17/probe'), route='chatgpt')
    target = OUT / 'PILOT_CALLS.jsonl'
    rows = [json.loads(line) for line in target.read_text(encoding='utf-8').splitlines()] if target.exists() else []
    done = {r['id'] for r in rows}
    for enabled in (False, True):
        lane = 'on' if enabled else 'off'
        # An unsupported mode is recorded once, never disguised as another effort.
        if any(r['lane'] == lane and r.get('error') for r in rows):
            continue
        for i in range(20):
            identity = f'v{ROUND}-{lane}-{i:02}'
            if identity in done:
                continue
            case = {'situation': f'合成格式试跑第{i+1}轮：我已经选好蓝色贴纸，请把它放进空盒。',
                    'options': [{'id': 'blue', 'text': '放入蓝色贴纸'}, {'id': 'ask', 'text': '询问贴纸颜色'}],
                    'target': 'blue'}
            request = {'model': MODEL, 'stream': False, 'temperature': 0, 'max_tokens': 8192,
                       'reasoning': {'enabled': enabled, 'effort': EFFORT} if enabled else {'enabled': False},
                       'response_format': decision_schema(case), 'messages': packet(case, {'utterances': [], 'understandings': []})}
            row = {'id': identity, 'round': ROUND, 'lane': lane, 'model': MODEL, 'effort': EFFORT if enabled else 'none',
                   'synthetic': True, 'request': request}
            def observer(event, value):
                row[event] = value
            try:
                output, meta = client.complete(request, observer=observer, allow_invalid=True)
                row.update(output=output, meta=meta, score=score(output, case))
            except ChatGPTError as error:
                row['error'] = error.evidence()
            with target.open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
            rows.append(row)
            print(json.dumps({'id': identity, 'valid': row.get('score', {}).get('valid'),
                              'latency_s': row.get('meta', {}).get('latency_s'), 'error': row.get('error')}, ensure_ascii=False), flush=True)
            summarize(rows)
            if row.get('error'):
                if row['error']['code'] != 'subscription_sharing_unsupported_capability':
                    return
                break
            time.sleep(2)


def summarize(rows):
    lanes = {}
    for lane in ('off', 'on'):
        matched = [r for r in rows if r['lane'] == lane and (r.get('round') == ROUND or lane == 'off')]
        ok = [r for r in matched if 'meta' in r]
        times = [r['meta']['latency_s'] for r in ok]
        lanes[lane] = {'attempts': len(matched), 'completed': len(ok),
            'strict_json_valid': sum(r['score']['valid'] for r in ok),
            'median_s': statistics.median(times) if times else None,
            'p95_s': quantile(times, .95) if times else None,
            'input_tokens': sum(r['meta']['usage'].get('input_tokens', 0) for r in ok),
            'output_tokens': sum(r['meta']['usage'].get('output_tokens', 0) for r in ok),
            'errors': [r['error'] for r in matched if r.get('error')]}
    write(OUT / 'PILOT.json', {'model': MODEL, 'effort': EFFORT, 'synthetic_only': True,
        'probe_round': ROUND, 'prior_engineering_attempts': sum(r.get('round') != ROUND for r in rows),
        'owner_confirmed_subscription_only': True, 'lanes': lanes,
        'ready_for_reasoning_judge': lanes['on']['completed'] == lanes['on']['strict_json_valid'] == 20,
        'quota_error_observed': any(r.get('error', {}).get('code') == 'subscription_sharing_usage_limit_exceeded' for r in rows),
        'revoked_or_expired_grant_observed': False,
        'error_probe_boundary': 'Only actual observed errors are raw evidence; offline fault injection does not prove live quota/revocation.'})


if __name__ == '__main__':
    run()
