"""One-shot screening -> freeze -> fresh-process learning/testing -> report."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys
import time

from companion.budget import DailyLedger
from growthlab.records import ROOT
from .client import Client, Stop, append
from .protocol import (CRITERIA, DECISION_SYSTEM, ESTIMATE_USD, SEED, MODEL, ROUTE,
                       compact, decision_schema, ratio, score)
from .study import learn, test, delete, sha, write
from .validate import load_candidates, validate

BASE=ROOT/'runs/u2'
OUT=ROOT/'evidence/u2'
SCREEN=OUT/'SCREEN_FREEZE.json'
FROZEN=OUT/'FROZEN.json'


def exclusive(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def sources():
    files=list((ROOT/'u2').rglob('*.py'))+list((ROOT/'u2/candidates').glob('*.json'))
    files += [ROOT/p for p in ('companion/memory.py','companion/understanding.py','companion/model.py',
        'companion/budget.py','companion/compact.py','growthlab/state.py','growthlab/models.py','growthlab/records.py',
        'u1/conventions/core.py','u1_resume/library.py','u1_resume/client.py','u1/harness.py','u1/protocol.py',
        'p7/proxy.py','p7/routing.py','p7/routing_v2.py','p7/routing_v1.json','p7/routing_v2.json',
        'u2/PRE_RUN.md','u2/requirements.txt','requirements-growth.txt')]
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(files))}


def verify(manifest):
    for name,digest in manifest['source_sha256'].items():
        if sha(ROOT/name)!=digest: raise Stop('frozen_source_changed:'+name)


def reconcile_budget():
    ledger=DailyLedger()
    timestamps={}
    # These audits identify each actual request charge. Only fixed fields are
    # read; no credentials, raw private conversations, or arbitrary log content
    # are copied into evidence.
    for path in (ROOT/'runs').rglob('routing.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                row=json.loads(line)
                if row.get('charge_id') and isinstance(row.get('unix_s'),(int,float)):
                    timestamps.setdefault(row['charge_id'],row['unix_s'])
            except ValueError: continue
    for path in (ROOT/'runs').rglob('calls.jsonl'):
        if BASE in path.parents: continue
        for line in path.read_text(encoding='utf-8').splitlines():
            try:
                row=json.loads(line);stamp=row.get('unix_s')
                if not isinstance(stamp,(int,float)): continue
                meta=row.get('meta',{})
                if isinstance(meta,dict) and meta.get('charge_id'): timestamps.setdefault(meta['charge_id'],stamp)
                for value in row.get('shared_ledger_delta_unattributed',[]):
                    if value.get('charge_id'): timestamps.setdefault(value['charge_id'],stamp)
            except (ValueError,TypeError): continue
    ledger.reconcile(timestamps)
    # The legacy ledger is append-only. Earlier undated rows are historical
    # only when a later insertion has a proven pre-today request timestamp.
    # Do not fabricate individual dates for those old rows.
    with ledger._connect() as db:
        unassigned=db.execute('SELECT COUNT(*),COALESCE(SUM(usd),0) FROM charges WHERE id NOT IN (SELECT id FROM charge_days)').fetchone()
        undated_last=db.execute('SELECT MAX(rowid) FROM charges WHERE id NOT IN (SELECT id FROM charge_days)').fetchone()[0]
        historical_anchor=db.execute('SELECT MAX(c.rowid) FROM charges c JOIN charge_days d ON c.id=d.id WHERE d.local_day<?',(ledger.day(),)).fetchone()[0]
    if undated_last is not None and (historical_anchor is None or undated_last>historical_anchor):
        raise Stop('undated_recent_charge_blocks_budget')
    return {'daily':ledger.snapshot(),'legacy_snapshot':ledger.history(),
            'dated_charge_ids':len(timestamps),'undated_historical_rows':unassigned[0],
            'undated_historical_usd':unassigned[1],
            'append_only_chronology':{'last_undated_row':undated_last,'later_pre_today_row':historical_anchor}}


def freeze_screen():
    if SCREEN.exists(): raise ValueError('screen_freeze_exists')
    items=load_candidates();audit=validate(items)
    if not audit['passed']: raise ValueError('candidate_validation_failed')
    engineering=json.loads((OUT/'ENGINEERING.json').read_bytes())
    if not engineering['passed']: raise ValueError('engineering_not_passed')
    text=(ROOT/'GROWTH_DESIGN_v0.md').read_text(encoding='utf-8')
    if 'v0.9' not in text.splitlines()[0]: raise ValueError('design_version')
    start=text.index('### 18.7 ');end=text.index('### 18.8 ',start)
    criteria_verbatim=text[start:end]
    budget=reconcile_budget()
    if budget['daily']['remaining_usd']<ESTIMATE_USD: raise Stop('daily_balance_below_full_estimate')
    client=Client(BASE/'preflight')
    metadata=client.transport.preflight()
    pricing=[r['pricing'] for r in client.transport._metadata if r.get('model_id')==MODEL and r.get('tag')==ROUTE]
    value={'version':'u2-v1','frozen_at_utc':datetime.now(timezone.utc).isoformat(),
        'seed':SEED,'design_title':text.splitlines()[0],'criteria_verbatim':criteria_verbatim,
        'source_sha256':sources(),'candidate_ids':[i['id'] for i in items],'validation':audit,
        'engineering_sha256':sha(OUT/'ENGINEERING.json'),
        'model':MODEL,'route':ROUTE,'temperature':0,'decision_reasoning':False,'consolidation_effort':'low',
        'estimated_total_usd':ESTIMATE_USD,'daily_budget':budget,'official_preflight':metadata,'pricing':pricing,
        'screen_policy':'Each candidate one no-memory request (P T1+T2 bundled; Q question only); remove any target hit. W has no prior screen. One ceiling request for every candidate (P T1+T2; Q question+use; W boundary). Retain only all-valid/all-correct ceilings.',
        'selection':'Seeded draw, P up to 24. Q/W balanced strata, up to 12 each. Stop if P<12 or either Q/W stratum<6. No primary arm data used.',
        'descriptive_arms':'Packets implemented and tested; optional paid descriptive runs omitted in v1 to prioritize the main comparison under $1/day.',
        'stops':'Concurrency 1; starts >=2s apart; only 429/502/503/504/connection one identical retry after max(30,Retry-After)+0..3s; second failure stops lane; two consecutive invalid outputs stop lane; 3600s/lane; no content retries, resumption or replacement items.',
        'claim_ceiling':'Synthetic implicit learning/use evidence only, not understanding the whole person or subjective experience.'}
    exclusive(SCREEN,value)
    print(json.dumps({'screen_manifest_sha256':sha(SCREEN),'budget':budget},ensure_ascii=False),flush=True)


def screen_packet(item,stage):
    category=item['category']
    cases=([item['question']] if stage=='prior' and category=='Q' else
           [item['question'],*item['tests']] if category=='Q' else item['tests'])
    situations=[]
    for case in cases:
        memory=''
        if stage=='ceiling':
            memory=(item['ceiling_question'] if case['phase']=='ask' else item['ceiling_use']) if category=='Q' else item['ceiling']
        situations.append({'memory':memory,'current':case['situation'],'options':case['options']})
    messages=[{'role':'system','content':DECISION_SYSTEM+'\n这里有若干独立局面。按所列次序各作一次决定；不要在局面之间传递信息。返回 {"decisions":[每个局面的上述四字段对象]}。'},
              {'role':'user','content':compact({'situations':situations})}]
    schema={'type':'json_schema','json_schema':{'name':'u2_screen','strict':True,'schema':{
        'type':'object','properties':{'decisions':{'type':'array','items':decision_schema(cases[0])['json_schema']['schema'],
                                                  'minItems':len(cases),'maxItems':len(cases)}},
        'required':['decisions'],'additionalProperties':False}}}
    # Q use has five choices; the question has four. Union is needed only for
    # this envelope; score still checks each case's own enumerated choices.
    schema['json_schema']['schema']['properties']['decisions']['items']['properties']['action']['enum']=sorted({o['id'] for c in cases for o in c['options']})
    return messages,schema,cases


def screen_lane(job,client):
    result=[]
    for item in load_candidates():
        if item['category']!=job['category']: continue
        messages,schema,cases=screen_packet(item,job['screen_stage'])
        output,meta=client.call(messages,{'item_id':item['id'],'stage':job['screen_stage'],'category':job['category']},schema=schema)
        valid=isinstance(output,dict) and set(output)=={'decisions'} and isinstance(output['decisions'],list) and len(output['decisions'])==len(cases)
        decisions=output['decisions'] if valid else [None]*len(cases)
        scored=[{'phase':case['phase'],**score(value,case)} for value,case in zip(decisions,cases)]
        row={'item_id':item['id'],'stage':job['screen_stage'],'category':job['category'],'output':output,'scores':scored,'meta':meta}
        append(client.folder/'screen.jsonl',row);result.append(row)
        client.parsed(valid and all(r['valid'] for r in scored))
    return result


def execute(name,manifest,operation,**fields):
    verify(manifest)
    folder=BASE/name;folder.mkdir(parents=True,exist_ok=False)
    job={'folder':str(folder),'manifest':str(FROZEN if FROZEN.exists() else SCREEN),'operation':operation,**fields}
    write(folder/'job.json',job)
    env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONIOENCODING='utf-8')
    with (folder/'stdout.txt').open('wb') as stdout,(folder/'stderr.txt').open('wb') as stderr:
        try:
            process=subprocess.run([sys.executable,'-m','u2.run','worker',str(folder/'job.json')],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,timeout=3700)
            code=process.returncode
        except subprocess.TimeoutExpired:
            code='worker_timeout'
    if not (folder/'result.json').exists():
        write(folder/'result.json',{'status':'stopped','stop':'worker_without_result','returncode':code})
    result=json.loads((folder/'result.json').read_bytes())
    print(json.dumps({'lane':name,'status':result['status'],'stop':result.get('stop')},ensure_ascii=False),flush=True)
    return result


def export_raw():
    target=OUT/'raw';target.mkdir(parents=True,exist_ok=True)
    for name in ('calls.jsonl','screen.jsonl','decisions.jsonl','consolidations.jsonl','routing.jsonl','storage_hash.json','deletion_bytes.json','result.json','learned.json'):
        for path in BASE.rglob(name):
            # Only synthetic U2 content; owner state is never copied.
            dest=target/path.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)


def screen_run():
    manifest=json.loads(SCREEN.read_bytes());verify(manifest)
    exclusive(BASE/'screen.claim',{'manifest':sha(SCREEN),'utc':datetime.now(timezone.utc).isoformat()})
    for category,stage in [('P','prior'),('P','ceiling'),('Q','prior'),('Q','ceiling'),('W','ceiling')]:
        result=execute(f'screen/{category}_{stage}',manifest,'screen',category=category,screen_stage=stage)
        export_raw()
        if result.get('stop') in GLOBAL_STOPS: break
    selection()


def selection():
    manifest=json.loads(SCREEN.read_bytes());verify(manifest)
    rows={}
    for path in (BASE/'screen').glob('*/screen.jsonl'):
        for line in path.read_text(encoding='utf-8').splitlines():
            row=json.loads(line);rows[(row['item_id'],row['stage'])]=row
    kept=[];excluded=[]
    for item in load_candidates():
        reasons=[]
        prior=rows.get((item['id'],'prior'));ceiling=rows.get((item['id'],'ceiling'))
        if item['category']!='W':
            if not prior or not all(r['valid'] for r in prior['scores']): reasons.append('prior_missing_or_invalid')
            elif any(r['correct'] for r in prior['scores']): reasons.append('prior_already_target')
        if not ceiling or not all(r['valid'] and r['correct'] for r in ceiling['scores']): reasons.append('ceiling_missing_invalid_or_wrong')
        if reasons: excluded.append({'id':item['id'],'reasons':reasons})
        else: kept.append(item)
    rng=random.Random(SEED);selected=[];counts={}
    for category in ('P','Q','W'):
        pool=[i for i in kept if i['category']==category];rng.shuffle(pool)
        if category=='P': selected.extend(pool[:24]);counts['P']=len(pool)
        else:
            key='should_ask' if category=='Q' else 'applicable'
            yes=[i for i in pool if i[key]];no=[i for i in pool if not i[key]]
            counts[category]={'yes':len(yes),'no':len(no),'total':len(pool)}
            n=min(12,len(yes),len(no))
            for a,b in zip(yes[:n],no[:n]):selected.extend([a,b])
    enough=counts['P']>=12 and all(min(counts[c]['yes'],counts[c]['no'])>=6 for c in ('Q','W'))
    results=list((BASE/'screen').glob('*/result.json'))
    complete=len(results)==5 and all(json.loads(p.read_bytes())['status']=='complete' for p in results)
    report={'counts':counts,'eligible_ids':[i['id'] for i in kept],'excluded':excluded,
            'selected_ids':[i['id'] for i in selected] if enough and complete else [],
            'passed':enough and complete,'status':'ready_to_freeze' if enough and complete else 'stop_insufficient_or_incomplete_screening'}
    write(OUT/'SCREEN_RESULTS.json',report)
    print(json.dumps(report,ensure_ascii=False),flush=True)
    return report


def freeze_main():
    report=json.loads((OUT/'SCREEN_RESULTS.json').read_bytes())
    if not report['passed']: raise Stop('screening_gate_not_passed')
    parent=json.loads(SCREEN.read_bytes());verify(parent)
    items={i['id']:i for i in load_candidates()}
    selected=[items[i] for i in report['selected_ids']]
    people={str(p):[] for p in range(1,4)}
    for category in ('P','Q','W'):
        for n,item in enumerate(i for i in selected if i['category']==category):
            people[str(n%3+1)].append(item)
    p_ids=[i['id'] for i in selected if i['category']=='P']
    random.Random(SEED+1).shuffle(p_ids)
    value={**parent,'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'screen_manifest_sha256':sha(SCREEN),
           'selection':report,'personas':people,'delete_ids':p_ids[:4],
           'raw_screen_sha256':{p.relative_to(OUT).as_posix():sha(p) for p in sorted((OUT/'raw/screen').rglob('*')) if p.is_file()},
           'main_arms':['B_R','B_I','B_N','A_R'],'estimated_main_usd':.65*len(selected)/72}
    exclusive(FROZEN,value)
    print(json.dumps({'main_manifest_sha256':sha(FROZEN),'delete_ids':value['delete_ids']},ensure_ascii=False),flush=True)


def main_run():
    manifest=json.loads(FROZEN.read_bytes());verify(manifest)
    budget=DailyLedger().snapshot()
    if budget['remaining_usd']<manifest['estimated_main_usd']:
        write(OUT/'MAIN_DEFERRED.json',{'reason':'insufficient_daily_balance','budget':budget,'needed_usd':manifest['estimated_main_usd']})
        raise Stop('start_on_another_day')
    exclusive(BASE/'main.claim',{'manifest':sha(FROZEN),'budget':budget,'utc':datetime.now(timezone.utc).isoformat()})
    for persona,items in manifest['personas'].items():
        for arm,group in [('B','R'),('B','I'),('B','N'),('A','R')]:
            name=f'main/person{persona}/{arm}_{group}'
            matched=BASE/f'main/person{persona}/B_R/learn/state.sqlite'
            if group=='I' and not (matched.parent/'learned.json').exists(): continue
            learned=execute(name+'/learn',manifest,'learn',persona=persona,arm=arm,group=group,items=items,matched_store=str(matched))
            if learned.get('stop') in GLOBAL_STOPS:
                export_raw();finish_main(manifest);return
            if learned['status']=='complete':
                tested=execute(name+'/test',manifest,'test',persona=persona,arm=arm,group=group,items=items,store=str(BASE/name/'learn/state.sqlite'))
                if tested.get('stop') in GLOBAL_STOPS:
                    export_raw();finish_main(manifest);return
            export_raw()
    for persona,items in manifest['personas'].items():
        selected=[i for i in items if i['id'] in manifest['delete_ids']]
        if not selected: continue
        base=BASE/f'main/person{persona}/B_R'
        if not (base/'test/result.json').exists() or json.loads((base/'test/result.json').read_bytes())['status']!='complete': continue
        erased=execute(f'delete/person{persona}',manifest,'delete',persona=persona,arm='B',group='R',store=str(base/'learn/state.sqlite'),delete_ids=[i['id'] for i in selected])
        if erased['status']=='complete':
            execute(f'delete/person{persona}/test',manifest,'test',persona=persona,arm='B',group='R',store=str(base/'learn/state.sqlite'),items=selected,stage='deleted')
        export_raw()
    finish_main(manifest)


GLOBAL_STOPS={'operator_stop','actual_exceeded_estimate','estimate_reservation_stop','daily_budget_stop','ac_required'}


def finish_main(manifest):
    from .report import report_main
    report_main(manifest)


def worker(path):
    job=json.loads(Path(path).read_bytes());folder=Path(job['folder'])
    result={'status':'running','pid':os.getpid()}
    try:
        manifest=json.loads(Path(job['manifest']).read_bytes());verify(manifest)
        if job['operation']=='delete': result['deletion']=delete(job)
        else:
            client=Client(folder)
            if job['operation']=='screen': screen_lane(job,client)
            elif job['operation']=='learn': learn(job,client)
            elif job['operation']=='test': test(job,client)
            else: raise ValueError('unknown_operation')
        result['status']='complete'
    except Exception as error:
        result.update(status='stopped',stop=str(error) if isinstance(error,(Stop,ValueError)) else type(error).__name__)
    finally:
        write(folder/'result.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['freeze-screen','screen','freeze-main','main','worker','export','budget'])
    parser.add_argument('argument',nargs='?');args=parser.parse_args()
    if args.command=='worker': worker(args.argument)
    elif args.command=='freeze-screen': freeze_screen()
    elif args.command=='screen': screen_run()
    elif args.command=='freeze-main': freeze_main()
    elif args.command=='main': main_run()
    elif args.command=='budget': print(json.dumps(reconcile_budget(),ensure_ascii=False))
    else: export_raw()
