"""Bounded descriptive pilot; prepare freezes seeds/prompts before any test.
Each episode runs in a new process and its own copied SQLite database.
"""
import argparse
import datetime
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.records import ROOT,write_json,telemetry,digest
from growthlab.forks import fork_storage,file_hash
from growthlab.state import Store
from growthlab.models import Cloud,MODEL,ROUTE
from growthlab.host import Host
from growthlab.contract import ACTIONS
from growthlab.memory import Memory,all_records
from growthlab.agent import Episode
from growthlab.consolidation import consolidate,A_SYSTEM,B_SYSTEM
from growthlab.decision import VERSION,SYSTEM,MEMORY_TOKENS,RECENT
from growthlab.variants import generate

TEACHING='做工具要站在工作台旁边'
BASE=ROOT/'runs/phase1'
CODE_FILES=sorted((ROOT/'growthlab').glob('*.py'))+[Path(__file__).resolve()]


def code_hashes():return {str(p.relative_to(ROOT)):file_hash(p) for p in CODE_FILES}


def prepare():
    folder=BASE/'pilot';folder.mkdir(parents=True,exist_ok=False)
    sampled=[]
    while len(sampled)<19:
        seed=secrets.randbelow(2**31-1)+1
        if seed not in sampled+[909011,909013,909017]:sampled.append(seed)
    manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'purpose':'descriptive pilot, not E1','model':MODEL,'route':ROUTE,'temperature':0,
        'memory_token_cap':MEMORY_TOKENS,'memory_bound':'UTF8 byte upper bound','recent_decisions':RECENT,
        'max_output_tokens':2048,'practice_step_limit':300,'test_step_limit':150,'budget_usd':5,
        'machine_time_limit_s':8*3600,'initial_concurrency':2,'max_concurrency':4,
        'fixed_teaching':TEACHING,'practice_seeds':{'F1':sampled[:3],'F2':sampled[3:6]},
        'test_seeds':{'F1':sampled[6:12],'F2':sampled[12:18]},
        'aliases':generate('rename_actions',sampled[18])['aliases'],
        'prompt_version':VERSION,'prompts':{'decision':SYSTEM,'A_sleep':A_SYSTEM,'B_sleep':B_SYSTEM},
        'source_sha256':code_hashes(),
        'network_retry_policy':'At most 2 attempts per episode, fresh copy each attempt; HTTP 429 reduces new concurrency to 2; retry after 30s. All attempts and charges retained.',
        'protocol_policy':'Two consecutive invalid outputs stops episode and entire batch for analysis.',
        'test_learning':'May update within isolated episode; post-episode consolidation once; never transfer between tests.',
        'schedule':'All B practice (three chains x three episodes), then all B tests; then same A schedule. Unrelated-experience arm omitted as requested.'}
    write_json(folder/'manifest.json',manifest)
    write_json(ROOT/'evidence/phase1/PILOT_MANIFEST.json',manifest)
    empty=Store(folder/'empty.sqlite');empty.close()
    print('Manifest frozen:',folder/'manifest.json')


def check_lock(manifest):
    if manifest['source_sha256']!=code_hashes():raise ValueError('frozen_code_mismatch')


def worker(job_path):
    job=json.loads(Path(job_path).read_text(encoding='utf-8'))
    manifest=json.loads((BASE/'pilot/manifest.json').read_text(encoding='utf-8'));check_lock(manifest)
    folder=Path(job['folder']);source=Path(job['source']);database=folder/'state.sqlite'
    sample=telemetry()
    if sample['ac_online'] is not True:raise ValueError('ac_required')
    fork=fork_storage(source,database)
    store=Store(database);initial=all_records(store);client=None;episode=None
    result={'job':job,'stop':'worker_initialization','pid':os.getpid(),'fork':fork,'initial_record_count':len(initial)}
    try:
        host=Host(seed=job['seed'],length=300 if job['phase']=='practice' else 150,aliases=manifest['aliases'] if job['family']=='F2' else None)
        memory=Memory(store,host.world,host.actions,job['arm'],restarted=True)
        client=Cloud(budget_path=BASE/'budget.sqlite')
        episode=Episode(host,store,folder,client,arm=job['arm'],memory=memory,
            teaching=TEACHING if job['group']=='F1_teach' and job['phase']=='practice' and job['index']==0 else None)
        played=episode.play(deadline=job['deadline'])
        sleep=None
        if played['stop'] is None and time.time()<job['deadline']:
            try:sleep=consolidate(episode)
            except (RuntimeError,ValueError) as error:
                episode.stop=str(error) if str(error).startswith('http_') or str(error) in ('budget_stop','prompt_size_stop','TimeoutError','URLError') else type(error).__name__
                episode.write({'type':'sleep_stop','code':episode.stop})
        result.update(episode.summary(),sleep=sleep)
        exported=memory.export()
        write_json(folder/'storage_full.json',exported)
        write_json(folder/'memory_full.json',{'arm':job['arm'],
            'records':[r for r in exported['records'] if r['kind'] in ('skill','general_rule','fact','reflection')],
            'profiles':exported['profiles'],'self':exported['self']})
    except Exception as error:
        result['stop']=str(error) if isinstance(error,ValueError) and str(error) in ('ac_required','budget_stop','route_preflight_rejected') else type(error).__name__
    finally:
        if episode:episode.close()
        if client:client.db.close()
        store.close()
    result['source_unchanged']=file_hash(source)==fork['source_sha256'];result['telemetry']=[sample,telemetry()]
    write_json(folder/'summary.json',result)
    return result


def run_batch():
    folder=BASE/'pilot';manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));check_lock(manifest)
    if (folder/'status.json').exists():raise ValueError('pilot_already_started')
    started=time.time();deadline=started+manifest['machine_time_limit_s'];capacity=2;completed=0
    status={'started_unix':started,'deadline_unix':deadline,'events':[],'completed':[],'attempts':[],'stop':None,'telemetry':[]}
    last_sample=0
    def save():write_json(folder/'status.json',status)
    def launch(job,attempt):
        attempt_folder=folder/'episodes'/f"{job['arm']}_{job['group']}_{job['phase']}_{job['index']}_a{attempt}"
        attempt_folder.mkdir(parents=True,exist_ok=False)
        full=dict(job,folder=str(attempt_folder),deadline=deadline,attempt=attempt)
        write_json(attempt_folder/'job.json',full)
        log=(attempt_folder/'process.log').open('w',encoding='utf-8')
        process=subprocess.Popen([sys.executable,__file__,'worker',str(attempt_folder/'job.json')],stdout=log,stderr=log,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        return process,log,full
    def execute(jobs):
        nonlocal capacity,completed,last_sample
        pending=[(job,1,0.) for job in jobs];active=[];finished=[]
        while pending or active:
            now=time.time()
            if now-last_sample>=30:
                sample=telemetry();status['telemetry'].append(sample);last_sample=now
                if sample['ac_online'] is not True:status['stop']='ac_required'
            if now>=deadline:status['stop']='machine_time_limit'
            for process,log,job in list(active):
                if process.poll() is None:continue
                log.close();active.remove((process,log,job))
                summary_path=Path(job['folder'])/'summary.json'
                result=json.loads(summary_path.read_text(encoding='utf-8')) if summary_path.exists() else dict(job=job,stop='worker_no_summary')
                status['attempts'].append(str(summary_path))
                stop=result.get('stop')
                if stop=='http_429':
                    capacity=2;status['events'].append({'time':now,'type':'http_429','concurrency':2,'job':job})
                retryable=stop in ('http_429','http_502','http_503','http_504','TimeoutError','URLError')
                if retryable and job['attempt']<2:
                    pending.append(({k:v for k,v in job.items() if k not in ('folder','deadline','attempt')},2,now+30))
                elif stop:
                    status['stop']=stop
                    status['events'].append({'time':now,'type':'batch_stop','stop':stop,'job':job})
                else:
                    completed+=1;finished.append((job,result));status['completed'].append(str(summary_path))
                    if capacity==2 and completed>=2 and not any(e['type']=='http_429' for e in status['events']):
                        capacity=4;status['events'].append({'time':now,'type':'concurrency_increase','concurrency':4})
                save()
            if status['stop']:
                for process,log,job in active:
                    if os.name=='nt':subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
                    else:process.terminate()
                    process.wait(timeout=20);log.close()
                    status['events'].append({'time':time.time(),'type':'cancelled_for_batch_stop','job':job})
                save();return finished
            for entry in list(pending):
                if len(active)>=capacity:break
                job,attempt,ready=entry
                if ready>now:continue
                pending.remove(entry);active.append(launch(job,attempt))
            save();time.sleep(1)
        return finished
    sources={};snapshots={}
    save()
    for arm in ('B','A'):
        for group in ('F1_auto','F1_teach','F2_train'):sources[arm,group]=folder/'empty.sqlite'
        for index in range(3):
            jobs=[{'arm':arm,'group':group,'family':group[:2],'phase':'practice','index':index,
                'seed':manifest['practice_seeds'][group[:2]][index],'source':str(sources[arm,group])} for group in ('F1_auto','F1_teach','F2_train')]
            results=execute(jobs)
            for job,result in results:sources[arm,job['group']]=Path(job['folder'])/'state.sqlite'
            if status['stop']:break
        if status['stop']:break
        for group in ('F1_auto','F1_teach','F2_train','F1_fresh','F2_fresh'):
            snapshot=folder/'snapshots'/f'{arm}_{group}.sqlite'
            fork_storage(sources.get((arm,group),folder/'empty.sqlite'),snapshot);snapshots[arm,group]=snapshot
            # Full learned contents as of practice end; test changes stay in episode copies.
            store=Store(snapshot);m=Memory(store,'0'*32,list(ACTIONS) if group[:2]=='F1' else sorted([manifest['aliases'].get(a,a) for a in ACTIONS]),arm)
            exported=m.export();store.close()
            write_json(folder/'snapshots'/f'{arm}_{group}_memory.json',{'arm':arm,'records':[r for r in exported['records'] if r['kind'] in ('skill','general_rule','fact','reflection')],'profiles':exported['profiles'],'self':exported['self']})
        jobs=[]
        for index in range(6):
            for group in ('F1_auto','F1_teach','F1_fresh','F2_train','F2_fresh'):
                jobs.append({'arm':arm,'group':group,'family':group[:2],'phase':'test','index':index,
                    'seed':manifest['test_seeds'][group[:2]][index],'source':str(snapshots[arm,group])})
        execute(jobs)
        if status['stop']:break
    status['finished_unix']=time.time();status['elapsed_seconds']=time.time()-started
    save();print({'completed':len(status['completed']),'stop':status['stop'],'seconds':status['elapsed_seconds']})


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','worker']);p.add_argument('job',nargs='?');args=p.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='run':run_batch()
    else:worker(args.job)


if __name__=='__main__':main()
