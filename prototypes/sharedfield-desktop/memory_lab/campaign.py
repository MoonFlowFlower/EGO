"""Finite, explicit profile rotation. Every replacement starts a fresh comparison."""
import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from contextlib import closing
from .provider import ROOT,PROFILES,write_json
from .adapters import completion,scope,http
from . import manage

def probe(profile,folder,campaign_id=None):
    if campaign_id:
        previous=[json.loads(p.read_text(encoding='utf-8'))
                  for batch in (ROOT/'runs').glob('batch-'+campaign_id+'-*')
                  for p in (batch/'calls').glob('*.json')]
        count=sum(r.get('source')=='probe' and r.get('profile',{}).get('id')==profile for r in previous)
        if count+3>6:raise RuntimeError('Direct compatibility probe limit exhausted; cannot redispatch missing summary')
    # Probe exactly the parameters used by actor, native indexers and ACE.
    prompts=[
        ('请仅回复JSON：{"ready":true,"中文":"你好"}',lambda o:o.get('ready') is True and o.get('中文')=='你好'),
        ('这是虚构测试。用户忙碌时想分享，请返回JSON：{"action":"write_letter"}',lambda o:o.get('action')=='write_letter'),
        ('只输出JSON：{"operations":[{"type":"ADD","content":"条件：饥饿且有食物；行动：进食"}]}',lambda o:o.get('operations',[{}])[0].get('type')=='ADD'),
    ]
    receipts=[]
    for i,(prompt,validate) in enumerate(prompts):
        scope(dict(run_id=folder.name,split='probe',condition='compatibility',arm='gateway',phase=str(i)))
        reply=completion([{'role':'user','content':prompt}],source='probe',max_tokens=512)
        obj=json.loads(reply['choices'][0]['message']['content'])
        receipts.append(dict(id=reply['id'],profile=reply['lab_profile'],valid=bool(validate(obj))))
        if not receipts[-1]['valid']:raise ValueError('Compatibility probe output rejected')
    write_json(folder/'probes.json',{'passed':True,'calls':receipts,'direct_probe_limit':6})

def command(module,args,log,python=None):
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('a',encoding='utf-8') as out:
        subprocess.run([str(python or sys.executable),'-B','-m',module,*map(str,args)],
                       cwd=ROOT.parent,stdout=out,stderr=subprocess.STDOUT,check=True)

def wait_hindsight():
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        try:
            with urllib.request.urlopen('http://127.0.0.1:18888/health',timeout=3) as r:
                if r.status==200:return
        except (ConnectionError,urllib.error.URLError):pass
        time.sleep(1)
    raise TimeoutError('Hindsight health deadline')

def overview(directory):
    with closing(sqlite3.connect(directory/'budget.sqlite')) as db:
        attempts=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
        statuses=dict(db.execute('SELECT status,count(*) FROM attempts GROUP BY status'))
    rows=[]
    for batch in (ROOT/'runs').glob('batch-'+directory.name+'-*'):
        for file in (batch/'calls').glob('*.json'):rows.append(json.loads(file.read_text(encoding='utf-8')))
    return dict(attempted_calls=attempts,statuses=statuses,
                known_cost_usd=sum((r.get('usage') or {}).get('cost') or 0 for r in rows),
                unknown_cost_calls=sum((r.get('usage') or {}).get('cost') is None for r in rows))



def reuse_probe(previous,folder):
    # Scorer-only revision: compatible inference parameters have not changed.
    # Preserve old probe receipts; do not exceed the six-probe per-profile limit.
    source=previous/'probes.json'
    if not source.exists() or not (previous/'PROFILE.json').exists():return False
    if json.loads((previous/'PROFILE.json').read_text())!=json.loads((folder/'PROFILE.json').read_text()):return False
    receipt=json.loads(source.read_text())
    if not receipt.get('passed'):return False
    write_json(folder/'probes.json',dict(receipt,reused_from=str(source.relative_to(ROOT))))
    return True


def resume_revision(directory,state,revision):
    from copy import deepcopy
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,24}',revision):raise ValueError('Simple revision name required')
    archive=directory/f'before-{revision}.json'
    if (state.get('status')!='stopped' or state.get('stage')!='calibration'
        or not state.get('history') or state['history'][-1].get('reason_code')
        or archive.exists()):raise ValueError('Only an explicit new scorer revision can resume calibration failure once')
    write_json(archive,state)
    state=deepcopy(state)
    state['history'][-1]['superseded_by_revision']=revision
    state['previous_revision']=state.get('revision')
    state.update(status='running',revision=revision)
    state.pop('error',None)
    write_json(directory/'status.json',state)
    return state


def main():
    p=argparse.ArgumentParser();p.add_argument('--id',default='reliability-01')
    p.add_argument('--repair-calibration',action='store_true',help='One explicit same-profile evaluator repair; never resets budget')
    p.add_argument('--revision',help='Explicitly authorized scorer revision after calibration-only stop; retains cumulative budget')
    p.add_argument('--calibration-cases',help='Frozen evaluator-only fixtures')
    a=p.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,48}',a.id):raise ValueError('Simple campaign ID required')
    directory=ROOT/'runs/campaigns'/a.id;directory.mkdir(parents=True,exist_ok=True)
    statefile=directory/'status.json'
    state=json.loads(statefile.read_text(encoding='utf-8')) if statefile.exists() else {'id':a.id,'entered':[],'status':'running','history':[]}
    if a.revision:
        if a.repair_calibration:raise ValueError('Choose one explicit revision mechanism')
        state=resume_revision(directory,state,a.revision)
    if a.calibration_cases:
        cases=str(Path(a.calibration_cases).resolve().relative_to(ROOT.parent)).replace('\\','/')
        if state.get('calibration_cases') and state['calibration_cases']!=cases and not a.revision:raise ValueError('Calibration cases already locked')
        state['calibration_cases']=cases
        write_json(statefile,state)
    if a.repair_calibration:
        if (state['status']!='stopped' or state['stage']!='calibration' or state.get('repair_count',0)
            or state['history'][-1].get('reason_code')):raise ValueError('Only one bounded evaluator repair of a calibration-only failure is allowed')
        write_json(directory/'before-calibration-repair.json',state)
        state['history'][-1]['superseded_by_calibration_repair']=True
        state.update(status='running',repair_count=1)
        write_json(statefile,state)
    if state['status'] in ('complete','stopped','exhausted'):raise RuntimeError('Closed campaign cannot restart automatically')
    evaluator=ROOT/'.eval-venv/Scripts/python.exe'
    for profile in PROFILES:
        closed={h['profile'] for h in state['history'] if not h.get('superseded_by_calibration_repair') and not h.get('superseded_by_revision')}
        if profile in closed:continue
        if profile not in state['entered']:state['entered'].append(profile)
        state.update(profile=profile,stage='startup');write_json(statefile,state)
        suffix=('-'+state['revision']) if state.get('revision') else ''
        batch='batch-'+a.id+'-'+profile+suffix;folder=ROOT/'runs'/batch
        memory='memory-'+a.id+'-'+profile+suffix;growth='growth-'+a.id+'-'+profile+suffix
        phase='startup';monitor=None
        try:
            manage.start(batch,profile,a.id);wait_hindsight()
            stopper=ROOT/'state/stop-resource-monitor'
            if stopper.exists():stopper.unlink()
            resource_log=(ROOT/'evidence'/('resources-'+a.id+'.log')).open('a',encoding='utf-8')
            monitor=subprocess.Popen(manage.wsl(manage.LINUX_PY,'-B','-m','memory_lab.resources','--seconds','43200'),
                stdout=resource_log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            resource_log.close()
            phase='probe';state['stage']=phase;write_json(statefile,state)
            if not (folder/'probes.json').exists():
                previous=state.get('previous_revision')
                previous_folder=ROOT/'runs'/('batch-'+a.id+'-'+profile+('-'+previous if previous else ''))
                if state.get('revision') and reuse_probe(previous_folder,folder):pass
                else:probe(profile,folder,campaign_id=a.id)
            phase='smoke';state['stage']=phase;write_json(statefile,state)
            for arm in ('baseline','memos','hindsight'):
                smoke=ROOT/'runs'/f'smoke-{arm}-{a.id}-{profile}{suffix}'/'result.json'
                if not smoke.exists():command('memory_lab.smoke',[arm,'--id',a.id+'-'+profile+suffix],folder/('smoke-'+arm+'.log'))
            phase='calibration';state['stage']=phase;write_json(statefile,state)
            calibration=folder/('calibration-repair-1' if state.get('repair_count') and not state.get('revision') else 'calibration')/'result.json'
            calibration_args=['calibrate','--output',calibration]
            if state.get('calibration_cases'):calibration_args+=['--cases',state['calibration_cases']]
            command('memory_lab.semantic',calibration_args,folder/'calibration.log',evaluator)
            if not json.loads(calibration.read_text(encoding='utf-8'))['passed']:
                raise RuntimeError('Chinese semantic calibration failed; not a 429, no quality-driven profile switching')
            for split in ('development','heldout'):
                phase='memory-'+split;state['stage']=phase;write_json(statefile,state)
                command('memory_lab.runner',['--split',split,'--run',memory],folder/(phase+'.log'))
            phase='memory-audit';state['stage']=phase;write_json(statefile,state)
            command('memory_lab.semantic',['audit','--output',ROOT/'runs'/memory,'--calibration',calibration],folder/(phase+'.log'),evaluator)
            command('memory_lab.report',['memory','--run',memory],folder/'memory-report.log')
            report=json.loads((ROOT/'runs'/memory/'report.json').read_text(encoding='utf-8'))
            arm=report['selection']['research_backend']
            phase='growth';state['stage']=phase;write_json(statefile,state)
            command('memory_lab.growth',['--arm',arm,'--memory-run',memory,'--run',growth],folder/'growth.log')
            phase='growth-audit';state['stage']=phase;write_json(statefile,state)
            command('memory_lab.semantic',['audit','--output',ROOT/'runs'/growth,'--calibration',calibration],folder/(phase+'.log'),evaluator)
            command('memory_lab.report',['growth','--run',growth],folder/'growth-report.log')
            state.update(status='complete',memory_run=memory,growth_run=growth,stage='complete')
            break
        except Exception as exc:
            stopped=folder/'STOPPED.json'
            info=json.loads(stopped.read_text(encoding='utf-8')) if stopped.exists() else {}
            reason=info.get('reason_code')
            rotate=reason=='http_429' or (phase=='probe' and (reason in ('http_400','http_404','http_422') or isinstance(exc,(ValueError,KeyError))))
            state['history'].append(dict(profile=profile,stage=phase,error_type=type(exc).__name__,reason_code=reason,rotate=rotate))
            write_json(folder/'CAMPAIGN_OUTCOME.json',state['history'][-1])
            if not rotate:
                state.update(status='stopped',stage=phase,error=str(exc));break
        finally:
            try:manage.stop()
            except Exception as stop_error:state['shutdown_error']=type(stop_error).__name__
            if monitor:
                try:monitor.wait(timeout=15)
                except subprocess.TimeoutExpired:monitor.terminate()
            if (directory/'budget.sqlite').exists():state['usage']=overview(directory)
            write_json(statefile,state)
            print(json.dumps(state,ensure_ascii=False),flush=True)
    else:
        state.update(status='exhausted',stage='all_profiles_unavailable');write_json(statefile,state)
    if state['status']!='complete':raise SystemExit(2)

if __name__=='__main__':main()
