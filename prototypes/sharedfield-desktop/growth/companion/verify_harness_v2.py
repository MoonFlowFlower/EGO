"""One preregistered real-model task; an isolated DB, at most two placements."""
import argparse
import json
import socket
import threading
import time

from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .body import Body, ROOT
from .harness import Harness
from .memory import Memory
from .model import Model

TASK = '整理合成残留，用已有木材准备木板，在附近已有地基旁连续放置两块橡木板；两块确认后停止。'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--previous-session',required=True)
    args=parser.parse_args()
    if not args.previous_session.isdigit():raise ValueError('session_id')
    previous=ROOT/'runs/kernel_v1/sessions'/args.previous_session/'lifecycle.jsonl'
    if not any(json.loads(line).get('event')=='supervisor_closed' for line in previous.read_text().splitlines()):
        raise RuntimeError('formal_session_still_running')
    try:
        with socket.create_connection(('127.0.0.1',18787),timeout=3):
            raise RuntimeError('formal_api_still_listening')
    except ConnectionRefusedError:pass
    base=ROOT/'runs/kernel_harness_v2';base.mkdir(parents=True,exist_ok=True)
    with (base/'attempt.claim').open('x',encoding='utf-8') as f:f.write(str(time.time_ns()))
    folder=base/'acceptance'/str(time.time_ns());folder.mkdir(parents=True)
    key=read_key();audit=AuditLog(folder,(key,));ledger=BudgetLedger(DEFAULT_BUDGET,5)
    total_before=ledger.total();batch=json.loads((ROOT/'runs/kernel_v1/batch_budget.json').read_text())
    transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,budget_path=DEFAULT_BUDGET,
                                limit=min(batch['limit'],total_before+.15),log_dir=folder)
    transport.set_audit(audit)
    body=Body(audit);model=Model(transport,audit);counter={'place':0,'craft':0}
    def policy(a):
        if a['name'] in ('inspect','inspect_area','recover_inventory','approach'):return True
        if a['name'] in ('place','place_at') and a['args']['block']=='oak_planks' and counter['place']<2:
            counter['place']+=1;return True
        if a['name']=='craft' and a['args']['item']=='oak_planks' and counter['craft']+a['args']['count']<=2:
            counter['craft']+=a['args']['count'];return True
        return False
    outcome={'passed':False,'task':TASK,'max_model_calls':20,'max_seconds':180,'run':folder.name}
    timer=None;started=None
    try:
        audit.write('preflight.jsonl',transport.preflight())
        body.start();ready=time.monotonic()+30
        while body.snapshot().get('offline') and time.monotonic()<ready:time.sleep(.2)
        before=body.snapshot()
        if before.get('offline'):raise RuntimeError('body_not_ready')
        if before.get('inventory',{}).get('oak_log',0)<1 and before.get('inventory',{}).get('oak_planks',0)<2:
            raise RuntimeError('material_precondition_missing')
        engine=Harness(folder/'state.sqlite',model,body,audit,max_decisions=20,max_seconds=180,action_policy=policy)
        def deadline():engine.stop();body.close('acceptance_deadline')
        timer=threading.Timer(180,deadline);timer.daemon=True;timer.start();started=time.monotonic()
        reply=engine.run('verification:harness-v2','verification',TASK)
        m=Memory(engine.path)
        try:
            work=m.goal()
            rows=[r['body'] for r in m.library.rows('experience') if r['body'].get('type')=='action_receipt']
        finally:m.close()
        placed=[r['receipt'] for r in rows if r['action']['name'] in ('place','place_at') and r['receipt'].get('verified')]
        recovery=[r['receipt'] for r in rows if r['action']['name']=='recover_inventory']
        unique={json.dumps(r['position'],sort_keys=True) for r in placed}
        passed=bool(work and work['goal_status']=='completed' and len(placed)==2 and len(unique)==2
                    and all(r.get('placement',{}).get('consumed')==1 for r in placed)
                    and any(r.get('verified') for r in recovery)
                    and any(r['action']['name']=='verify_blocks' and r['receipt'].get('verified') for r in rows))
        outcome.update(passed=passed,task_status=work['goal_status'] if work else None,before=before,
                       after=body.snapshot(),receipts=rows,reply=reply,distinct_placements=len(unique),
                       actual_placements=len(placed),duration_s=time.monotonic()-started)
    except Exception as error:outcome['error_type']=type(error).__name__
    finally:
        if timer:timer.cancel()
        body.close('acceptance_complete')
        outcome.update(model_calls=model.calls,cost_usd=ledger.total()-total_before,
                       body_exit_code=body.process.poll() if body.process else None)
        (folder/'result.json').write_bytes((json.dumps(outcome,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps({k:v for k,v in outcome.items() if k not in ('before','after','receipts','reply','task')},ensure_ascii=False))
    return 0 if outcome['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
