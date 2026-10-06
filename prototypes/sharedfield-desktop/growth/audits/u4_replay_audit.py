"""Post-run integrity and resource audit; does not choose or change U4 criteria."""
import json
import math
import statistics
from collections import Counter

from u3.common import write, utc, sha
from u4.corpus import OUT, rows
from u4.run import verify, FROZEN
from u4.scoring import grade


def audit():
    frozen = verify()
    inputs = {r['id']: r for r in rows(OUT / 'INPUTS.jsonl')}
    summaries, intervals = {}, []
    for judge, config in frozen['judges'].items():
        records = rows(OUT / 'raw' / judge / 'decisions.jsonl')
        assert len(records) == len({r['id'] for r in records}), 'duplicate decision'
        events = rows(OUT / 'raw' / judge / 'calls.jsonl')
        pending, requests, responses = None, [], []
        for event in events:
            if event['event'] == 'request':
                assert pending is None, 'overlapping request in one lane'
                pending = event
                item = inputs[event['input_id']]
                request = event['request']
                expected = dict(item['original_request'], model=config['model'],
                    reasoning=config['reasoning'], max_tokens=config['max_tokens'])
                assert request == expected, 'actual request differs from frozen envelope'
                if judge == 'D2':
                    wire = event['wire_request']
                    messages = item['messages']
                    assert wire['model'] == config['model']
                    assert wire['instructions'] == messages[0]['content']
                    assert wire['input'] == messages[1:]
                    assert wire['text']['format'] == {
                        'type': 'json_schema', **item['response_format']['json_schema']}
                    assert wire['reasoning'] == {'effort': config['reasoning']['effort']}
                    assert wire['store'] is False and wire['stream'] is True
                    assert set(wire) == {'model', 'input', 'instructions', 'store', 'stream', 'text', 'reasoning'}
                requests.append(event)
            elif event['event'] == 'response':
                assert pending is not None, 'response without saved request'
                assert (pending['input_id'], pending['attempt']) == (event['input_id'], event['attempt'])
                assert event['unix_s'] >= pending['unix_s'], 'negative request interval'
                intervals.append((pending['unix_s'], event['unix_s'], judge, event['input_id']))
                responses.append(event)
                pending = None
        successful = Counter(r['input_id'] for r in responses if not r['meta'].get('error'))
        assert not any(n > 1 for n in successful.values()), 'completed decision called again'
        for record in records:
            assert record['score'] == grade(inputs[record['id']], record['output']), 'score mismatch'
            if record['origin'] == 'historical':
                assert record['output'] == inputs[record['id']]['historical']['output']
            else:
                candidates = [r for r in responses if r['input_id'] == record['id']]
                assert candidates, 'new decision without raw response'
                last = candidates[-1]
                assert record['meta'] == last['meta'], 'saved response metadata differs'
                response = last['response']
                if not record['meta'].get('error'):
                    if judge == 'D2':
                        content = ''.join(part['text'] for item in response['output'] if item['type'] == 'message'
                            for part in item['content'] if part['type'] == 'output_text')
                    else:
                        content = response['choices'][0]['message']['content']
                    assert json.loads(content) == record['output'], 'output differs from raw response'
        usage = {'input_tokens': 0, 'output_tokens': 0, 'reasoning_tokens': 0,
                 'calls_without_usage': 0, 'reported_cost_usd': 0.0}
        latency, errors = [], Counter()
        for row in responses:
            meta = row['meta']
            latency.append(meta['latency_s'])
            raw = meta.get('usage') or {}
            prompt, completion = (('input_tokens', 'output_tokens') if judge == 'D2'
                                  else ('prompt_tokens', 'completion_tokens'))
            usage['input_tokens'] += raw.get(prompt) or 0
            usage['output_tokens'] += raw.get(completion) or 0
            details = raw.get('output_tokens_details' if judge == 'D2' else 'completion_tokens_details') or {}
            usage['reasoning_tokens'] += details.get('reasoning_tokens') or 0
            usage['calls_without_usage'] += int(raw.get(prompt) is None or raw.get(completion) is None)
            usage['reported_cost_usd'] += meta.get('cost_usd') or 0
            error = meta.get('error')
            if error:
                errors[error['code'] if isinstance(error, dict) else error] += 1
        latency.sort()
        if judge == 'D2':
            usage['reported_cost_usd'] = None
        summaries[judge] = {'decisions': len(records),
            'historical': sum(r['origin'] == 'historical' for r in records),
            'new': sum(r['origin'] == 'new' for r in records),
            'request_attempts': len(requests), 'response_events': len(responses),
            'pending_request': pending['input_id'] if pending else None,
            'invalid_decisions': sum(not r['score']['valid_output'] for r in records),
            'errors': dict(errors), 'usage': usage,
            'latency_s': {'median': statistics.median(latency) if latency else None,
                'p95_nearest_rank': latency[math.ceil(.95 * len(latency)) - 1] if latency else None},
            'billing': 'subscription' if judge == 'D2' else 'shared_daily_dollar_ledger'}
    intervals.sort()
    assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), 'cross-lane overlap'
    repeated = {r['id']: r for r in rows(OUT / 'raw/D0_repeat/decisions.jsonl')}
    paired = []
    for identity in frozen['D0_repeat_ids']:
        if identity in repeated:
            item = inputs[identity]
            old, new = grade(item, item['historical']['output']), repeated[identity]['score']
            paired.append({'id': identity, 'domain': item['domain'],
                'signature_changed': old['signature'] != new['signature'],
                'original_score': old, 'repeat_score': new})
    write(OUT / 'D0_REPEAT_PAIRED.json', {'manifest_sha256': sha(FROZEN), 'rows': paired,
        'scope': 'The exact preregistered 60 cases, including unchanged rows; descriptive only.'})
    result = {'at_utc': utc(), 'manifest_sha256': sha(FROZEN),
        'scope': 'Observed request bytes, raw outputs, mechanical regrading, single concurrency and resource use. No new outcome criteria.',
        'integrity_pass': True, 'closed_request_intervals': len(intervals), 'judges': summaries}
    write(OUT / 'REPLAY_AUDIT.json', result)
    return result


if __name__ == '__main__':
    result = audit()
    print(json.dumps({'integrity_pass': result['integrity_pass'],
        'decisions': {j: s['decisions'] for j, s in result['judges'].items()}}, ensure_ascii=False))
