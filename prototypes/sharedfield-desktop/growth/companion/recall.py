"""Bounded, source-linked candidate retrieval. Relevance is not truth or authority.

Lexical terms and Chinese bigrams are a transparent initial index, not a claim of
general semantic recall. The actor can reformulate its query after a miss.
"""
import json
import re
from collections import Counter


def terms(text):
    result = set(re.findall(r'[a-z][a-z0-9_]+', text.lower()))
    for word in re.findall(r'[\u3400-\u9fff]+', text):
        result.update(word[i:i+2] for i in range(len(word)-1))
    return result - {'现在', '一下', '什么', '怎么', '这个', '那个', '我们', '你的', '我的', '可以', '记得'}


def recall(memory, query, limit=5):
    if not isinstance(query, str) or not 1 <= len(query) <= 200:
        raise ValueError('recall_query')
    candidates = []
    wanted = terms(query)
    # Filter the durable corpus by the information need BEFORE imposing a bound.
    # Hundreds of unrelated new events must not push an old convention out of recall.
    searchable = "CASE json_extract(body,'$.type') WHEN 'convention' THEN " \
        "json_extract(body,'$.trigger.text') || ' ' || json_extract(body,'$.meaning') " \
        "WHEN 'action_receipt' THEN COALESCE(json_extract(body,'$.task_title'),'') || ' ' || " \
        "COALESCE(json_extract(body,'$.action'),'') || ' ' || COALESCE(json_extract(body,'$.receipt.status'),'') ELSE '' END"
    predicates = ' OR '.join(f'instr(lower({searchable}),?)>0' for _ in wanted)
    rows = memory.db.execute("SELECT id,kind,body FROM records WHERE personal=1 AND status='active' "
                             "AND kind IN ('preference','experience') AND ("+predicates+") ORDER BY rowid DESC LIMIT 512",
                             sorted(wanted)).fetchall() if wanted else []
    for identity, kind, serialized in rows:
        body = json.loads(serialized)
        if body.get('type') == 'convention':
            sources = body.get('source_ids', [])
            if not sources or not all(memory.record(s) for s in sources):
                continue
            value = {'record_id': identity, 'kind': 'explicit_user_convention', 'source_ids': sources,
                     'trigger': body['trigger'], 'meaning': body['meaning'],
                     'authority': 'quoted_convention_candidate_check_trigger_and_current_request'}
            searchable = body['trigger']['text'] + ' ' + body['meaning']
        elif body.get('type') == 'action_receipt':
            receipt = body.get('receipt', {})
            source = memory.db.execute('SELECT user_id,created FROM kernel_turns WHERE event_id=?', (body.get('event_id'),)).fetchone()
            value = {'record_id': identity, 'kind': 'past_action_result', 'task_id': body.get('task_id'),
                     'source_ids': [source[0]] if source and source[0] else [], 'occurred_at': source[1] if source else None,
                     'action': body.get('action'), 'task_title': body.get('task_title'),
                     'result': {k: receipt[k] for k in ('verified', 'executed', 'status', 'gained', 'lost', 'pickup_events') if k in receipt},
                     'authority': 'historical_result_not_current_state_or_new_permission'}
            searchable = json.dumps({k: value[k] for k in ('task_title', 'action', 'result')}, ensure_ascii=False)
        else:
            continue
        candidates.append((value, terms(searchable)))
    frequencies = Counter(t for _, ts in candidates for t in ts)
    ranked = []
    for value, ts in candidates:
        matched = wanted & ts
        if matched:
            score = sum(1 / frequencies[t] for t in matched)
            ranked.append((score, {**value, 'retrieval': {'matched_terms': sorted(matched), 'applicability': 'not_yet_established'}}))
    ranked.sort(key=lambda row: row[0], reverse=True)
    return {'query': query, 'candidates': [r[1] for r in ranked[:limit]], 'searched_active_records': len(rows),
            'scope': 'up_to_512_query_matching_active_conventions_and_action_records',
            'semantics': 'candidate evidence only; verify conditions against current body and input; a miss is not proof of no memory'}


def matched_cards(memory, annotations):
    ids = {a['card_id'] for a in annotations}
    return [c for c in memory.library.cards() if c['card_id'] in ids]
