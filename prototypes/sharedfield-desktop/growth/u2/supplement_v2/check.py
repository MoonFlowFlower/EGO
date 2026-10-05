"""Offline checks of the uncalled supplement; does not select or run items."""
from collections import Counter
import json
from pathlib import Path
from u2.validate import load_candidates, validate, words

HERE=Path(__file__).parent


def candidates():
    return [json.loads(p.read_bytes()) for p in sorted((HERE/'candidates').glob('*.json'))]


def explicit_gap(item):
    query=next(o['text'] for o in item['question']['options'] if o['id']==item['question']['relevant_ask_ids'][-1])
    return bool(words(query)&words(item['ceiling_question'])) and '还不知道' in item['ceiling_question']


def check(items):
    original=load_candidates();audit=validate(original+items)
    # The immutable v1 validator hard-codes 48/category and 24 Q-yes. The
    # supplement has its own explicit 24 P + 24 Q (12/12) cardinality below.
    # All case-level, timing, citation-free content and lexical checks remain.
    errors=[e for e in audit['format_errors']
            if e!='Q_balance' and not (isinstance(e,dict) and set(e)=={'counts'})]
    counts=Counter(i['category'] for i in items)
    if counts!={'P':24,'Q':24}:errors.append('supplement_counts')
    if sum(i.get('should_ask') is True for i in items)!=12:errors.append('supplement_Q_balance')
    if {i['id'] for i in items}&{i['id'] for i in original}:errors.append('old_id_reused')
    for item in items:
        if item['category']=='Q' and item['should_ask'] and not explicit_gap(item):
            errors.append((item['id'],'ceiling_missing_specific_unknown'))
    return {'kind':'unscreened_supplement','new_ids':[i['id'] for i in items],
        'new_counts':dict(counts),'Q_should_ask':sum(i.get('should_ask') is True for i in items),
        'format_errors':errors,'overlaps':audit['overlaps'],'passed':not errors and not audit['overlaps'],
        'batch_count_note':'v1 48/category checks remain unchanged. New supplement requires 24 P and 24 Q (12/12), checked separately. No screening or main threshold is relaxed.',
        'cloud_calls':0,'semantic_limit':'Word overlap checks do not prove naturalness or that an upper-bound decision will succeed.'}


if __name__=='__main__':
    result=check(candidates())
    (HERE/'VALIDATION.json').write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps(result,ensure_ascii=False))
