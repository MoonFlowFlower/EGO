"""One explicit, bounded receipt-interface diagnostic; never a batch retry.

Prepare freezes actual SQLite execution inputs. Run accepts that exact freeze once,
retains the old 502 latch, and uses the existing cumulative paid transport ledger.
"""
import argparse
import hashlib
import json
import math
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path
from .core import Store, World, canonical, digest
from .provider import ROOT, Client, profile_config, write_json
from . import semantic

NAME='receipt-v5-diagnostic'
LIMIT=24


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def build_cases(directory):
    cases=[]
    specs=[('meal-absent','eat','米饼','我刚才吃掉了米饼。','absent'),
           ('meal-failed','eat','燕麦粥','我刚才吃掉了燕麦粥。','failed'),
           ('rest-deleted','sleep',None,'我刚才睡过一觉。','deleted'),
           ('letter-not-meal','eat','梨子','我刚才吃掉了梨子。','letter')]
    for pair,kind,target,text,negative in specs:
        for positive in (True,False):
            key=pair+('-positive' if positive else '-negative')
            store=Store(directory/key/'raw.sqlite')
            try:
                World(store,dict(now=1,places={},inventory=[target] if target and (positive or negative!='failed') else [],hunger=70,energy=50))
                action=dict(type=kind,evidence_ids=[])
                if target:action['target']=target
                if positive or negative in ('failed','deleted'):
                    store.commit_step(action,'prior','prior',{'action':action},{'id':'simulated-environment-only'}, {})
                elif negative=='letter':
                    letter=dict(type='write_letter',text=text,evidence_ids=[])
                    store.commit_step(letter,'letter','letter',{'action':letter},{'id':'simulated-environment-only'}, {})
                if not positive and negative=='deleted':store.forget(['prior'])
                say=dict(type='contact',text=text,evidence_ids=[])
                row=store.commit_step(say,'utterance','utterance',{'action':say},{'id':'simulated-environment-only'}, {})
                cases.append(dict(id=key,pair=pair,condition='valid' if positive else negative,
                                  expected='supported' if positive else 'unsupported',row=row))
            finally:store.close()
    return cases


@contextmanager
def recovery(campaign,old,new,manifest):
    """Narrow one-use transition for a received, explicitly billed 502 only."""
    state=read(campaign/'status.json'); stop=read(old/'STOPPED.json')
    cfg=profile_config('qwen35')
    if (state.get('status')!='stopped' or state.get('stage')!='calibration'
        or state.get('revision')!='fragment-v4' or state.get('profile')!='qwen35'
        or state['history'][-1].get('reason_code')!='http_502'
        or stop.get('reason_code')!='http_502' or read(old/'PROFILE.json')!=cfg
        or new.exists()):raise ValueError('Not the authorized one-use revision transition')
    receipt_path=old/'calls'/(stop['call_id']+'.json'); receipt=read(receipt_path)
    cost=(receipt.get('usage') or {}).get('cost')
    reply=receipt.get('response',{})
    errors=([reply['error']] if reply.get('error') else [])+[c['error'] for c in reply.get('choices',[]) if c.get('error')]
    if (receipt.get('status')!='error' or receipt.get('profile')!=cfg
        or receipt.get('id')!=stop['call_id'] or type(cost) not in (float,int)
        or not math.isfinite(cost) or cost<0 or not errors
        or any(not isinstance(e,dict) or str(e.get('code'))!='502' for e in errors)):
        raise ValueError('Recovery requires a complete, known-cost 502 receipt with the same profile')
    with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
        db.execute('BEGIN IMMEDIATE')
        config=dict(db.execute('SELECT id,value FROM config'))
        if (config.get('limit')!='5000' or config.get('blocked')!='Explicit non-429 provider failure'
            or db.execute("SELECT count(*) FROM attempts WHERE status NOT IN ('ok','error')").fetchone()[0]
            or db.execute('SELECT status FROM attempts WHERE id=?',(receipt['id'],)).fetchone()!=('error',)):
            raise ValueError('Budget, receipt or request resolution differs from the reviewed stop')
        count=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
        if count+LIMIT>5000:raise ValueError('Insufficient remaining cumulative budget')
        new.mkdir(parents=True)
        write_json(new/'RECOVERY.json',dict(manifest=manifest,previous_state=state,previous_stop=stop,
            previous_block=config['blocked'],attempts_before=count,request_cap=LIMIT,
            receipt_sha256=hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            explanation='Explicit new receipt-interface revision; original failed request remains sealed and is not replayed'))
        # Separate read connection avoids backing up an active write transaction.
        with closing(sqlite3.connect(campaign/'budget.sqlite')) as source, closing(sqlite3.connect(new/'budget-before.sqlite')) as target:
            source.backup(target)
        db.execute("DELETE FROM config WHERE id='blocked'")
        db.commit()
    try:
        write_json(campaign/'status.json',dict(state,status='running',stage='receipt-diagnostic',
            active_diagnostic=str(new),diagnostic_cap=LIMIT))
        yield
    finally:
        # Fail closed between revisions, including local exceptions. Preserve any
        # newly raised failure's stronger block instead of overwriting it.
        with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
            db.execute("INSERT OR IGNORE INTO config VALUES('blocked',?)",(config['blocked'],));db.commit()
        write_json(campaign/'status.json',dict(state,last_diagnostic=str(new),
            diagnostic_requires_review=True))


def fingerprints():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
            for name in ('semantic.py','core.py','provider.py','receipt_diagnostic.py','requirements-eval.lock.txt')}


def prepare(freeze):
    if freeze.exists():raise ValueError('Freeze already exists; do not regenerate exposed samples')
    cases=build_cases(freeze/'execution')
    write_json(freeze/'cases.json',cases)
    manifest=dict(name=NAME,profile=profile_config('qwen35'),count=8,request_cap=LIMIT,
                  cases_hash=digest(cases),files=fingerprints(),
                  interpretation='Exposed mechanism diagnostic, not independent blind calibration or formal comparison',
                  success='All eight frozen labels match; manual reasons review must respect receipt provenance',
                  stop='One pass only; any transport/parse error ends the run without retry; no automatic prompt repair')
    write_json(freeze/'MANIFEST.json',manifest)
    return manifest


def run(freeze):
    manifest=read(freeze/'MANIFEST.json');cases=read(freeze/'cases.json')
    if (manifest['files']!=fingerprints() or manifest['cases_hash']!=digest(cases)
        or manifest['profile']!=profile_config('qwen35') or len(cases)!=8 or manifest['request_cap']!=LIMIT):
        raise ValueError('Frozen implementation, inputs or profile changed')
    campaign=ROOT/'runs/campaigns/reliability-01'
    old=ROOT/'runs/batch-reliability-01-qwen35-fragment-v4'
    new=ROOT/('runs/batch-reliability-01-qwen35-'+NAME)
    outcome=dict(status='incomplete',cases=[],manifest=manifest,formal_gate_passed=False)
    with recovery(campaign,old,new,manifest):
        try:
            client=Client(new,campaign=campaign,profile='qwen35')
            def call(prompt,scope_id,part):
                if len(list((new/'calls').glob('*.json')))>=LIMIT:raise RuntimeError('Diagnostic request cap reached')
                client.scope=canonical(dict(scope_id,phase=part))
                policy=semantic.SCOPE_POLICY if part=='claim-scope' else semantic.EXTRACTION_POLICY if part=='claim-extraction' else semantic.POLICY
                response=client.complete(dict(messages=[{'role':'system','content':policy},{'role':'user','content':prompt}],response_format={'type':'json_object'},max_tokens=4096),'receipt-diagnostic')
                return response,json.loads(response['choices'][0]['message']['content'])
            for case in cases:
                verdict=semantic.audit(case['row'],dict(run_id=new.name,split='diagnostic',case=case['id'],arm='judge'),call)
                result=dict(case=case['id'],pair=case['pair'],expected=case['expected'],audit=verdict)
                write_json(new/'cases'/(case['id']+'.json'),result)
                outcome['cases'].append(result)
                print(canonical(dict(case=case['id'],expected=case['expected'],actual=verdict['status'])),flush=True)
            outcome.update(status='completed',matched=sum(c['expected']==c['audit']['status'] for c in outcome['cases']))
        except Exception as exc:
            outcome.update(status='stopped',error_type=type(exc).__name__,error=str(exc))
        finally:
            write_json(new/'RESULT.json',outcome)
    from .campaign import overview
    state=read(campaign/'status.json');state['usage']=overview(campaign)
    state['diagnostic_result']=dict(status=outcome['status'],matched=outcome.get('matched'),completed=len(outcome['cases']),path=str(new/'RESULT.json'))
    write_json(campaign/'status.json',state)
    print(canonical(dict(status=outcome['status'],usage=state['usage'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run']);a=p.parse_args()
    freeze=ROOT/'evidence/receipt-v5-freeze'
    if a.command=='prepare':print(canonical(prepare(freeze)))
    else:run(freeze)
