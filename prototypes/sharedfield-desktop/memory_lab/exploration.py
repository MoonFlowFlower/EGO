"""User-approved A: finite development-only action exploration, never formal selection."""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path
from .provider import ROOT, profile_config, write_json
from .core import digest
from .reproducibility import code_manifest

REVISION=2
RUN='explore-development-02'
BATCH='batch-reliability-01-qwen35-explore-dev-02'
CAMPAIGN=ROOT/'runs/campaigns/reliability-01'
DIRECTORY=ROOT/'runs'/RUN
ARMS=('baseline','memos','hindsight')


def select_revision(revision):
    global REVISION,RUN,BATCH,DIRECTORY
    REVISION=revision;RUN=f'explore-development-{revision:02d}'
    BATCH=f'batch-reliability-01-qwen35-explore-dev-{revision:02d}'
    DIRECTORY=ROOT/'runs'/RUN


def revised_policy(previous,count,cases):
    if (count!=491 or previous.get('start')!=470 or previous.get('additional')!=500
        or previous.get('batch')!='batch-reliability-01-qwen35-explore-dev-01'
        or previous.get('run')!='explore-development-01' or previous.get('cases')!=cases):
        raise ValueError('Previous A ledger/policy changed; cannot reset budget')
    return dict(previous,batch='batch-reliability-01-qwen35-explore-dev-02',run='explore-development-02',
                memos_dedup_output_tokens=4096)


def read(path):return json.loads(path.read_text(encoding='utf-8'))


def exploratory_row(result):
    return dict(case=result['case'],family=result['family'],arm=result['arm'],repeat=result['repeat'],
                action_goal_success=not result['gates'] and not result['failures'],
                full_success=result['success'],semantic_status='unreviewed',
                semantic_pending=result.get('semantic_pending',[]),gates=result['gates'],failures=result['failures'],
                phases=result['phases'],recall_s=result['recall_s'],write_s=result['write_s'],
                missed_contacts=result['missed_contacts'],false_contacts=result['false_contacts'])


def prepare():
    from .runner import load_cases
    cases=load_cases('development')
    if DIRECTORY.exists():raise ValueError('Exploration freeze already exists; no reset or regeneration')
    if len(cases)!=12 or any(c['split']!='development' for c in cases):raise ValueError('Expected frozen development set')
    DIRECTORY.mkdir(parents=True)
    write_json(DIRECTORY/'RUN_MANIFEST.json',dict(files=code_manifest(),profile=profile_config('qwen35'),
        status='frozen before first episode',kind='exploratory-development',semantic_gate_passed=False,
        authorization='User approved output-budget adjustment' if REVISION==2 else 'User selected A',
        revision=REVISION,additional_request_limit=479 if REVISION==2 else 500,
        original_A_start=470,original_A_limit=500,
        transport_adjustment={'memos_dedup_output_tokens':4096} if REVISION==2 else {},
        episode_limit=36,case_ids=[c['id'] for c in cases],development_hash=digest(cases)))
    write_json(DIRECTORY/'STATUS.json',dict(status='prepared',completed=0,paid_requests=0))


def activate():
    manifest=read(DIRECTORY/'RUN_MANIFEST.json');state=read(CAMPAIGN/'status.json')
    batch=ROOT/'runs'/BATCH
    if (read(DIRECTORY/'STATUS.json')['status']!='prepared' or batch.exists()
        or state['status']!='stopped' or state['profile']!='qwen35'
        or manifest['files']!=code_manifest()):raise ValueError('Not a fresh authorized exploration freeze')
    old=ROOT/('runs/batch-reliability-01-qwen35-explore-dev-01' if REVISION==2 else 'runs/batch-reliability-01-qwen35-fragment-v4')
    stop=read(old/'STOPPED.json');failed=read(old/'calls'/(stop['call_id']+'.json'))
    diagnostic=read(ROOT/'runs/batch-reliability-01-qwen35-receipt-v5-diagnostic/RESULT.json')
    expected_stop='completion_length' if REVISION==2 else 'http_502'
    cost=failed.get('usage',{}).get('cost')
    if (stop['reason_code']!=expected_stop or failed['status']!='error' or type(cost) not in (int,float) or cost<0
        or failed['profile']!=profile_config('qwen35') or diagnostic['status']!='completed'):
        raise ValueError('Earlier failure or diagnostic differs from reviewed evidence')
    if REVISION==2:
        closeout=read(ROOT/'runs/explore-development-01/CLOSEOUT.json')
        response_hash=hashlib.sha256(json.dumps(failed['response'],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if (response_hash!=closeout['raw_response_sha256'] or failed['response']['choices'][0]['finish_reason']!='length'
            or failed['request']['max_tokens']!=300 or failed['usage']['completion_tokens']!=300):
            raise ValueError('Reviewed length receipt differs')
    with closing(sqlite3.connect(CAMPAIGN/'budget.sqlite')) as db:
        db.execute('BEGIN IMMEDIATE')
        config=dict(db.execute('SELECT id,value FROM config'))
        expected_block='Exploration finished or stopped; review required' if REVISION==2 else 'Explicit non-429 provider failure'
        if (config.get('limit')!='5000' or config.get('blocked')!=expected_block
            or db.execute("SELECT 1 FROM attempts WHERE status NOT IN ('ok','error')").fetchone()):
            raise ValueError('Unresolved request, existing policy or changed budget: do not auto-resume')
        count=db.execute('SELECT count(*) FROM attempts').fetchone()[0]
        if count!=(491 if REVISION==2 else 470):raise ValueError('Reviewed starting ledger changed')
        if REVISION==2:policy=revised_policy(json.loads(config.get('exploration_policy','{}')),count,manifest['case_ids'])
        else:
            if config.get('exploration_policy'):raise ValueError('Existing exploration policy')
            policy=dict(batch=BATCH,run=RUN,start=count,additional=500,cases=manifest['case_ids'])
        batch.mkdir()
        write_json(batch/'PROFILE.json',profile_config('qwen35'))
        write_json(batch/'AUTHORIZATION.json',dict(previous_state=state,previous_stop=stop,previous_block=config['blocked'],
            start_attempts=count,additional_limit=970-count,global_limit=5000,authorization='User A and approved output-budget revision',
            previous_policy=config.get('exploration_policy'),new_policy=policy,
            run=RUN,manifest_sha256=hashlib.sha256((DIRECTORY/'RUN_MANIFEST.json').read_bytes()).hexdigest(),
            old_failure_sha256=hashlib.sha256((old/'calls'/(stop['call_id']+'.json')).read_bytes()).hexdigest()))
        with closing(sqlite3.connect(CAMPAIGN/'budget.sqlite')) as source, closing(sqlite3.connect(batch/'budget-before.sqlite')) as dest:
            source.backup(dest)
        db.execute("INSERT OR REPLACE INTO config VALUES('exploration_policy',?)",(json.dumps(policy),))
        db.execute("DELETE FROM config WHERE id='blocked'");db.commit()
    write_json(CAMPAIGN/'status.json',dict(state,status='running',stage='exploratory-development',
        active_exploration=RUN,exploration_start=470,exploration_limit=500,current_revision_start=count))
    write_json(DIRECTORY/'STATUS.json',dict(status='running',pid=os.getpid(),started_at=time.time(),completed=0))


def report():
    from .campaign import overview
    from .report import paired
    state=read(DIRECTORY/'STATUS.json');manifest=read(DIRECTORY/'RUN_MANIFEST.json')
    rows=[exploratory_row(read(p)) for p in sorted((DIRECTORY/'episodes').glob('*/result.json'))]
    failures=[dict(path=str(p.relative_to(DIRECTORY)),**read(p)) for p in sorted(DIRECTORY.glob('**/FAILED.json'))]
    calls=[read(p) for p in sorted((ROOT/'runs'/BATCH/'calls').glob('*.json'))]
    grouped={arm:[r for r in rows if r['arm']==arm] for arm in ARMS}
    summary={arm:dict(completed=len(group),action_goals_met=sum(r['action_goal_success'] for r in group),
        deterministic_gate_failures=sum(bool(r['gates']) for r in group),semantic_status='unreviewed',
        calls=sum(c.get('context',{}).get('arm')==arm for c in calls),
        known_cost_usd=sum((c.get('usage') or {}).get('cost') or 0 for c in calls if c.get('context',{}).get('arm')==arm))
        for arm,group in grouped.items()}
    expected={(case,arm,1) for case in manifest['case_ids'] for arm in ARMS}
    complete={(r['case'],r['arm'],r['repeat']) for r in rows}==expected and len(rows)==36
    comparisons={}
    if complete:
        for arm in ARMS[1:]:
            comparisons[arm]=paired([dict(r,success=r['action_goal_success']) for r in grouped['baseline']],
                                    [dict(r,success=r['action_goal_success']) for r in grouped[arm]])
    outcome=dict(kind='exploratory-development',state=state,complete=complete,rows=rows,summary=summary,
        paired_action_goals=comparisons,failures=failures,new_requests=len(calls),usage=overview(CAMPAIGN),
        known_cost_usd=sum((c.get('usage') or {}).get('cost') or 0 for c in calls),
        unknown_cost_calls=sum((c.get('usage') or {}).get('cost') is None for c in calls),
        semantic_status='unreviewed',product_integration='blocked',winner=None,
        formal_memory_completed=0,formal_growth_completed=0)
    write_json(DIRECTORY/'EXPLORATORY_REPORT.json',outcome)
    lines=['# 开发集行为探索（非正式选型）','',
        '这是**真实模型调用下的模拟生活实验**。正文均未完成语义验收；不证明长期陪伴或无虚构。',
        f"状态：{state['status']}；已完成{len(rows)}/36轮。本修订新增请求{len(calls)}/{manifest['additional_request_limit']}，A累计{outcome['usage']['attempted_calls']-470}/500，全活动{outcome['usage']['attempted_calls']}/5000。",
        f"本轮已知费用USD {outcome['known_cost_usd']:.8f}，{outcome['unknown_cost_calls']}次计费未知。",'',
        '| 底座 | 完成轮数 | 动作目标达成 | 确定性底线失败轮数 | 请求数 | 已知费用USD |',
        '|---|---:|---:|---:|---:|---:|']
    for arm,s in summary.items():lines.append(f"| {arm} | {s['completed']}/12 | {s['action_goals_met']} | {s['deterministic_gate_failures']} | {s['calls']} | {s['known_cost_usd']:.8f} |")
    lines+=['','动作目标达成由原有failures和gates判断，不覆盖原始success或semantic_pending。正文真实性、同名人物语义、共同经历仍待验收。',
            '完整配对前不比较差异、不排名。开发集结果只描述这12个合成场景，不代表真实用户或独立保留测试。']
    if comparisons:
        for arm,p in comparisons.items():lines.append(f"- {arm}相对baseline动作目标差异{p['difference']:+.1%}，场景配对95%区间[{p['ci95'][0]:+.1%}, {p['ci95'][1]:+.1%}]；不作正式选择。")
    lines+=['','逐场景结果、恢复/执行失败和调用归属见EXPLORATORY_REPORT.json；原始trace和retrieval保留于episodes/。',
            '资源采样在resource-samples.jsonl（采样峰值，不是严格最大值）；正文未验收，所有候选禁止产品接入。本批不启动保留测试或ACE。']
    (DIRECTORY/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return outcome


def run():
    from . import manage
    from .campaign import wait_hindsight,reuse_probe,overview
    from .runner import load_cases,setup_base,run_episode
    from .reproducibility import freeze_run
    activate();monitor=None
    try:
        manage.start(BATCH,'qwen35','reliability-01');wait_hindsight();freeze_run(DIRECTORY)
        old=ROOT/'runs/batch-reliability-01-qwen35-fragment-v4'
        if not reuse_probe(old,ROOT/'runs'/BATCH):raise RuntimeError('Exact-profile compatibility evidence missing')
        # These are previous observations, not new backend smoke passes.
        write_json(DIRECTORY/'SMOKE_REFERENCES.json',dict(reused=True,new_probe_calls=0,
            paths=[str(ROOT/'runs'/f'smoke-{arm}-reliability-01-qwen35-fragment-v4/result.json') for arm in ARMS],
            note='Previous same-profile smoke evidence; current scenario indexing/recall exercises running services'))
        stopper=ROOT/'state/stop-resource-monitor'
        if stopper.exists():stopper.unlink()
        log=(DIRECTORY/'resource-monitor.log').open('a',encoding='utf-8')
        # Existing sampler writes a shared historical log; snapshot byte offset
        # lets closeout retain only this run's appended measurements.
        resource=ROOT/'runs/resource-samples.jsonl';offset=resource.stat().st_size if resource.exists() else 0
        write_json(DIRECTORY/'RESOURCE_OFFSET.json',dict(offset=offset))
        monitor=subprocess.Popen(manage.wsl(manage.LINUX_PY,'-B','-m','memory_lab.resources','--seconds','14400'),stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        log.close()
        cases=load_cases('development')
        for index,case in enumerate(cases):
            # Deterministic rotation balances first-arm cache/startup advantage.
            order=ARMS[index%3:]+ARMS[:index%3]
            for arm in order:
                progress=read(DIRECTORY/'STATUS.json');progress.update(case=case['id'],arm=arm)
                write_json(DIRECTORY/'STATUS.json',progress)
                base=setup_base(case,arm,DIRECTORY)
                result=run_episode(case,arm,1,DIRECTORY,base)
                progress['completed']+=1;write_json(DIRECTORY/'STATUS.json',progress)
                report()
                print(json.dumps(dict(case=case['id'],arm=arm,completed=progress['completed'],action_goal_success=not result['gates'] and not result['failures']),ensure_ascii=False),flush=True)
        progress=read(DIRECTORY/'STATUS.json');progress.update(status='completed',finished_at=time.time())
        write_json(DIRECTORY/'STATUS.json',progress)
    except BaseException as exc:
        progress=read(DIRECTORY/'STATUS.json');progress.update(status='stopped',error_type=type(exc).__name__,error=str(exc),finished_at=time.time())
        write_json(DIRECTORY/'STATUS.json',progress)
    finally:
        # Close dispatch before service shutdown; preserve old and new stop files.
        with closing(sqlite3.connect(CAMPAIGN/'budget.sqlite')) as db:
            db.execute("INSERT OR IGNORE INTO config VALUES('blocked','Exploration finished or stopped; review required')");db.commit()
        try:manage.stop()
        except Exception as exc:
            write_json(DIRECTORY/'SHUTDOWN_ERROR.json',dict(error_type=type(exc).__name__,error=str(exc)))
        if monitor:
            try:monitor.wait(timeout=15)
            except subprocess.TimeoutExpired:monitor.terminate()
        resource=ROOT/'runs/resource-samples.jsonl';offset_path=DIRECTORY/'RESOURCE_OFFSET.json'
        if resource.exists() and offset_path.exists():
            with resource.open('rb') as f:f.seek(read(offset_path)['offset']);(DIRECTORY/'resource-samples.jsonl').write_bytes(f.read())
        state=read(CAMPAIGN/'status.json');state.update(status='stopped',stage='exploratory-development',usage=overview(CAMPAIGN),exploration_result=read(DIRECTORY/'STATUS.json'))
        write_json(CAMPAIGN/'status.json',state)
        outcome=report();print(json.dumps(dict(status=outcome['state']['status'],completed=len(outcome['rows']),new_requests=outcome['new_requests'],usage=outcome['usage']),ensure_ascii=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','report']);p.add_argument('--revision',type=int,choices=[1,2],default=2);a=p.parse_args()
    select_revision(a.revision)
    if a.command=='prepare':prepare()
    elif a.command=='run':run()
    else:report()
