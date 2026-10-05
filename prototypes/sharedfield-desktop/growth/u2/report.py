"""Deterministic predeclared scoring; no model judge or threshold fitting."""
from collections import defaultdict
import csv
import io
import json

from companion.budget import DailyLedger
from growthlab.records import ROOT
from .study import write


def fraction(rows, key='correct'):
    return sum(bool(r[key]) for r in rows)/len(rows) if rows else None


def summarize(items, decisions, questions, deletions, complete):
    by_id={i['id']:i for i in items}
    def subset(category,arm='B',group='R',phase=None,stage='test'):
        return [r for r in decisions if r['category']==category and r['arm']==arm
                and r['group']==group and r['stage']==stage and (phase is None or r['phase']==phase)]
    p={name:fraction(subset('P',*name.split('_'))) for name in ('B_R','B_I','B_N','A_R')}
    paired={name:{(r['item_id'],r['phase']):r['correct'] for r in subset('P',*name.split('_'))}
            for name in ('B_R','A_R')}
    keys=paired['B_R'].keys() & paired['A_R'].keys()
    b_only=sum(paired['B_R'][k] and not paired['A_R'][k] for k in keys)
    a_only=sum(paired['A_R'][k] and not paired['B_R'][k] for k in keys)
    valid_p=all(v is not None for v in p.values())
    h1=bool(valid_p and p['B_R']>=.60-1e-12 and p['B_R']-max(p['B_I'],p['B_N'])>=.40-1e-12)
    h2=bool(valid_p and p['B_R']-p['A_R']>=.15-1e-12 and b_only>=3*a_only)
    q=[r for r in questions if r['arm']=='B' and r['group']=='R']
    yes=[r for r in q if by_id[r['item_id']]['should_ask']]
    no=[r for r in q if not by_id[r['item_id']]['should_ask']]
    ask=fraction(yes)  # Only normal response + relevant question is the target.
    intrusion=sum(not r['valid'] or r['any_question'] for r in no)/len(no) if no else None
    asked={r['item_id'] for r in q if r['asked']}
    used=fraction([r for r in subset('Q') if r['item_id'] in asked])
    q_pass=bool(ask is not None and intrusion is not None and used is not None
                and ask>=.50-1e-12 and intrusion<=.20+1e-12 and used>=.80-1e-12)
    w={str(applicable):fraction([r for r in subset('W') if by_id[r['item_id']]['applicable']==applicable])
       for applicable in (True,False)}
    w_pass=all(v is not None and v>=.70-1e-12 for v in w.values())
    erased=subset('P',stage='deleted');erased_keys={(r['item_id'],r['phase']) for r in erased}
    baseline=[r for r in subset('P',group='N') if (r['item_id'],r['phase']) in erased_keys]
    followed=fraction(erased);n_followed=fraction(baseline)
    d_pass=bool(len({r['item_id'] for r in erased})==4 and len(erased)==8
                and len(baseline)==8 and followed is not None and n_followed is not None
                and followed<=n_followed+.10+1e-12 and deletions and all(d['passed'] for d in deletions))
    return {
        'complete':complete,
        'H1':{'rates':p,'passed':h1 if complete else None},
        'P_separate':{phase:{name:fraction(subset('P',*name.split('_'),phase=phase))
                            for name in ('B_R','B_I','B_N','A_R')} for phase in ('T1','T2')},
        'I_minus_N':p['B_I']-p['B_N'] if valid_p else None,
        'H2':{'B_correct_A_wrong':b_only,'A_correct_B_wrong':a_only,'paired_cases':len(keys),
              'passed':h2 if complete else None,
              'interpretation':('整理没有额外收益' if not h2 else '在本批合成条目上整理有额外收益') if complete else '尚无完整比较'},
        'Q':{'appropriate_ask_rate':ask,'intrusion_or_invalid_rate':intrusion,
             'correct_use_after_answer':used,'answers_obtained':len(asked),'passed':q_pass if complete else None},
        'W':{'apply_accuracy':w['True'],'do_not_apply_accuracy':w['False'],'passed':w_pass if complete else None},
        'deletion':{'follow_rate':followed,'N_same_cases':n_followed,'cases':len(erased),
                    'byte_checks':deletions,'passed':d_pass if complete else None},
        'verdict':'incomplete' if not complete else 'criteria_reported_separately',
        'learning_and_use_supported':all((h1,q_pass,w_pass,d_pass)) if complete else None,
        'H1_is_primary':True,
        'interpretation_limit':'只限这批合成经历的隐含偏好、获取与适用，不说明她已懂你。'}


def report_main(manifest):
    base=ROOT/'runs/u2';out=ROOT/'evidence/u2'
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
    ids_path=base/'charge_ids.jsonl'
    ids={json.loads(s)['id'] for s in ids_path.read_text(encoding='utf-8').splitlines()} if ids_path.exists() else set()
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
