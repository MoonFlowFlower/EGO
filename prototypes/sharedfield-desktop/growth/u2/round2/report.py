"""Deterministic predeclared scoring; no model judge or threshold fitting."""
from collections import defaultdict
import csv
import io
import json

from companion.budget import DailyLedger
from growthlab.records import ROOT
from u2.study import write


from u2.report import fraction, summarize


def report_main(manifest):
    base=ROOT/'runs/u2/round2';out=ROOT/'evidence/u2/round2'
    decisions=[];questions=[];deletions=[];lane_results=[];hashes=[]
    for path in (base/'main').rglob('decisions.jsonl'):
        decisions.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines())
    for path in (base/'delete').rglob('decisions.jsonl'):
        decisions.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines())
    for path in (base/'main').rglob('learned.json'):
        questions.extend(json.loads(path.read_bytes())['questions'])
    for path in (base/'delete').rglob('deletion_bytes.json'):
        deletions.append(json.loads(path.read_bytes()))
    for branch in ('main','delete'):
        for path in (base/branch).rglob('result.json'):
            lane_results.append({'lane':path.parent.relative_to(base).as_posix(),**json.loads(path.read_bytes())})
        for path in (base/branch).rglob('storage_hash.json'):
            hashes.append(json.loads(path.read_bytes()))
    expected=24+2*sum(any(i['id'] in manifest['delete_ids'] for i in items) for items in manifest['personas'].values())
    complete=(len(lane_results)==expected and all(r['status']=='complete' for r in lane_results)
              and all(h['unchanged'] and h['learning_pid']!=h['testing_pid'] for h in hashes))
    length_checks=[]
    for person in manifest['personas']:
        paths=[base/f'main/person{person}/{arm}/learn/learned.json' for arm in ('B_R','B_I')]
        matched=all(p.exists() for p in paths) and json.loads(paths[0].read_bytes())['lengths']==json.loads(paths[1].read_bytes())['lengths']
        length_checks.append({'persona':person,'matched':matched})
    complete=complete and all(r['matched'] for r in length_checks)
    items=[i for values in manifest['personas'].values() for i in values]
    expected_cases={(i['id'],case['phase'],arm,group,'test') for i in items for case in i['tests']
                    for arm,group in [('B','R'),('B','I'),('B','N'),('A','R')]}
    expected_cases|={(i['id'],'ask',arm,'R','learning') for i in items if i['category']=='Q' for arm in ('A','B')}
    expected_cases|={(i['id'],case['phase'],'B','R','deleted') for i in items if i['id'] in manifest['delete_ids'] for case in i['tests']}
    actual_cases=[tuple(r[k] for k in ('item_id','phase','arm','group','stage')) for r in decisions]
    complete=complete and len(actual_cases)==len(expected_cases) and set(actual_cases)==expected_cases
    result=summarize(items,decisions,questions,deletions,complete)
    result.update(lanes=lane_results,storage_hash_checks=hashes,irrelevant_length_checks=length_checks)
    ids=set()
    for branch in ('main','delete'):
        for path in (base/branch).rglob('routing.jsonl'):
            ids.update(json.loads(s).get('charge_id') for s in path.read_text(encoding='utf-8').splitlines())
    ledger=DailyLedger()
    with ledger._connect() as db:
        charges=[{'id':identity,'usd':usd,'status':status} for identity,usd,status in db.execute('SELECT * FROM charges') if identity in ids]
    result['cost']={'total_including_unknown_holds':sum(r['usd'] for r in charges),'charges':charges,'daily':ledger.snapshot()}
    write(out/'MAIN_RESULTS.json',result)
    grouped=defaultdict(list)
    for row in decisions:
        key=tuple(row[k] for k in ('category','group','arm','stage','phase'))
        grouped[key].append(row)
    stream=io.StringIO(newline='');writer=csv.writer(stream)
    writer.writerow(['category','group','arm','stage','phase','n','valid','correct','rate','latency_seconds','reported_cost_usd'])
    for key,rows in sorted(grouped.items()):
        writer.writerow([*key,len(rows),sum(r['valid'] for r in rows),sum(r['correct'] for r in rows),fraction(rows),
                         sum(r['meta']['latency_s'] for r in rows),sum(r['meta']['cost_usd'] or 0 for r in rows)])
    (out/'SUMMARY.csv').write_text(stream.getvalue(),encoding='utf-8-sig')
    return result
