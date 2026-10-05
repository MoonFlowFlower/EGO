"""Single-claim fixed-model interaction acceptance. No Minecraft connection."""
import argparse
import hashlib
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timezone
from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .body import ROOT
from .harness import Harness
from .model import Model, DecisionError
from .memory import Memory
from .work import create_work, save_work
from .interaction_scene import InteractionScene
from .verification_body import SceneBody as BaseSceneBody
import concurrent.futures
from .test_harness import goal

class SceneBody(BaseSceneBody):
    """Accept one-target batches while preserving the held first receipt."""
    def start_action(self,action,**kwargs):
        if action['name']!='place_many':return super().start_action(action,**kwargs)
        targets=action['args']['targets']
        if len(targets)!=1:raise RuntimeError('owner_requested_one_placement_at_a_time')
        target=targets[0]
        inner=super().start_action({'name':'place_at','args':target},**kwargs)
        outer=concurrent.futures.Future()
        def finish(completed):
            try:
                receipt=completed.result()
                outer.set_result({'verified':receipt['verified'],'status':'placement_batch_checked' if receipt['verified'] else 'placement_batch_partial',
                    'placements':[{'target':target,'receipt':receipt}],'observed':self.snapshot()})
            except Exception as error:outer.set_exception(error)
        inner.add_done_callback(finish)
        return outer


EVIDENCE=ROOT/'evidence/kernel_interaction_v11'
OWNER=ROOT/'runs/kernel_v1/owner/state.sqlite'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    files=[p for p in (ROOT/'companion').iterdir() if p.suffix in ('.py','.mjs','.txt','.ps1')]
    files += [EVIDENCE/'CHECKLIST.md',ROOT/'evidence/kernel_interaction_v3/CHECKLIST.md',ROOT/'evidence/kernel_interaction_v2/CHECKLIST.md',ROOT/'evidence/kernel_interaction_v1/NEXT_ACCEPTANCE.md']
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}


def saved(path):
    m=Memory(path)
    try: return m.goal()
    finally: m.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    freeze=EVIDENCE/'FREEZE.json'
    if args.freeze:
        with freeze.open('x',encoding='utf-8') as f:
            json.dump({'created_utc':datetime.now(timezone.utc).isoformat(),'base_commit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),
                       'sha256':manifest()},f,indent=2);f.write('\n')
        print(json.dumps({'frozen':len(manifest())}));return 0
    frozen=json.loads(freeze.read_text(encoding='utf-8'))['sha256']
    if manifest()!=frozen:raise RuntimeError('source_changed')
    base=ROOT/'runs'/EVIDENCE.name;base.mkdir(parents=True,exist_ok=True)
    with (base/'attempt.claim').open('x',encoding='utf-8') as f:f.write(str(time.time_ns()))
    folder=base/str(time.time_ns());folder.mkdir()
    owner_before=sha(OWNER);key=read_key();audit=AuditLog(folder,(key,))
    ledger=BudgetLedger(DEFAULT_BUDGET,5);before=ledger.total()
    batch=json.loads((ROOT/'runs/kernel_v1/batch_budget.json').read_bytes())
    limit=min(batch['limit'],before+.10)
    transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,budget_path=DEFAULT_BUDGET,limit=limit,log_dir=folder)
    transport.set_audit(audit);audit.write('preflight.jsonl',transport.preflight())
    start=time.monotonic();failed=threading.Event();threads=[];bodies=[]
    class RecordedModel(Model):
        def decide(self,prompt,context):
            if failed.is_set() or self.calls>=70 or time.monotonic()-start>=600:raise RuntimeError('acceptance_boundary')
            try:value=super().decide(prompt,context)
            except DecisionError:raise  # The production loop owns bounded output repair.
            except Exception:failed.set();raise
            self.last_context=context
            audit.write('decisions.jsonl',{'call':self.calls,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                'context':context,'result':value});return value
    model=RecordedModel(transport,audit)
    result={'run':folder.name,'minecraft':False,'cases':[],'semantic_review':'pending','passed':False,'budget_limit':limit}
    def case(identity,body):
        bodies.append(body);path=folder/(identity+'.sqlite')
        return path,Harness(path,model,body,audit,max_decisions=10,max_seconds=90)
    def add(identity,passed,**data):
        value={'case':identity,'mechanical_passed':bool(passed),**data};result['cases'].append(value)
        audit.write('case_results.jsonl',value)
        print(json.dumps({'case':identity,'mechanical_passed':bool(passed),'model_calls':model.calls},ensure_ascii=False),flush=True)
        # Keep independent scenario outcomes in one frozen attempt; a failure
        # remains a failure and does not silently prevent observing other cases.
    def queue(engine,event,text):
        thread=threading.Thread(target=engine.run,args=(event,'verification',text),daemon=True);threads.append(thread);thread.start()
        end=time.monotonic()+5
        while not engine._waiting and time.monotonic()<end:time.sleep(.01)
        if not engine._waiting:raise RuntimeError('input_not_queued')
        return thread
    try:
        body=InteractionScene();path,engine=case('s0',body)
        m=Memory(path);source,_=m.begin('old','verification','我丢了8个原木，你捡一下')
        old=create_work({'title':'捡起Moonlight丢的8个原木','steps':['拾取'],
            'done_when':[{'kind':'gained','item':'oak_log','count':8}]},body.snapshot(),source)
        old['status']='blocked';save_work(m,old,[source]);m.finish('old','采集超时。',[source]);m.close()
        body.state['inventory']['oak_log']=10
        answer=engine.run('s0','verification','继续')
        add('S0-legacy',saved(path)['goal_status']=='waiting_user' and not body.actions,reply=answer)

        body=InteractionScene();path,engine=case('s1',body)
        m=Memory(path);source,_=m.begin('old','verification','先铺8块木板')
        old=create_work(goal(8),body.snapshot(),source);old['status']='blocked';save_work(m,old,[source]);m.finish('old','施工受阻。',[source]);m.close()
        greeting=engine.run('g1','verification','在吗')
        add('G1',not body.actions and saved(path)['goal_status']=='blocked',reply=greeting)
        answer=engine.run('s1','verification','过来一下')
        work=saved(path)['work'];names=[a['name'] for a in body.actions]
        add('S1',work['task_id']!=old['task_id'] and work['status']=='completed' and work['done_when']==[{'kind':'near_owner'}]
            and set(names)<={'approach','inspect'},reply=answer,actions=names,work=work)

        body=InteractionScene();path,engine=case('s2',body)
        answer=engine.run('s2','verification','我丢了8个原木，你捡一下。')
        work=saved(path)['work'];names=[a['name'] for a in body.actions]
        add('S2',work['status']=='completed' and work.get('picked_up',{}).get('oak_log')==8
            and 'pickup_items' in names and not set(names)&{'search','collect','go_to_block'},reply=answer,actions=names,work=work)

        body=InteractionScene(hold='approach',items=False);body.state['owner']['position']['x']=30
        path,engine=case('s3',body)
        thread=threading.Thread(target=engine.run,args=('s3','verification','请先走到我身边，再捡我丢的8个原木。'),daemon=True)
        threads.append(thread);thread.start()
        if not body.entered.wait(30):raise RuntimeError('s3_approach_not_reached')
        first=saved(path)['work'];body.state['owner']['position']['x']=40
        body.state['dropped_items']['items']=[body.item(42,40)]
        correction=queue(engine,'s3-point','这儿，原木在这里，你去哪儿啊')
        body.release();thread.join(60);correction.join(60)
        work=saved(path)['work'];pickups=[a for a in body.actions if a['name']=='pickup_items']
        add('S3',not thread.is_alive() and not correction.is_alive() and work['task_id']==first['task_id']
            and work.get('revision')==2 and work['status']=='completed' and pickups and pickups[-1]['args']['entity_ids']==[42],
            work=work,actions=body.actions)

        body=SceneBody();path,engine=case('s4',body)
        thread=threading.Thread(target=engine.run,args=('s4','verification','请用背包现有木板，在附近空位放置两块橡木板，每次只放一块，不需要造房子。'),daemon=True)
        threads.append(thread);thread.start()
        if not body.first_placement.wait(30):raise RuntimeError('s4_first_placement_not_reached')
        first=saved(path)['work'];chat=queue(engine,'s4-chat','在吗？现在进展怎么样？')
        body.release();thread.join(60);chat.join(60)
        work=saved(path)['work']
        add('S4',not thread.is_alive() and not chat.is_alive() and work['task_id']==first['task_id']
            and work['status']=='completed' and len(body.blocks)==2,reply=MemoryReply(path,'s4-chat'),work=work,actions=body.actions)

        body=InteractionScene(items=False);path,engine=case('s5',body)
        answer=engine.run('s5-pick','verification','捡一下我丢在这里的8个原木。')
        work=saved(path)['work']
        add('S5-clarify',work['status']=='waiting_user' and work.get('awaiting') and not any(a['name']=='pickup_items' for a in body.actions),
            reply=answer,work=work,actions=body.actions)

        for variant in ('present','masked','restored'):
            body=InteractionScene(items=False);body.state['crafting_grid']={'oak_log':1}
            path,engine=case('s6-'+variant,body)
            m=Memory(path);source,_=m.begin('teach','verification','夜航暗号表示整理合成格和光标')
            card=m.propose({'trigger':'夜航暗号','meaning':'整理合成格和光标','replaces':None},source)
            m.finish('teach','已经记录。',[source])
            for n in range(24):
                s,_=m.begin('distractor-'+str(n),'verification','之前的无关聊天'+str(n));m.finish('distractor-'+str(n),'好。',[s])
            if variant in ('masked','restored'):
                with m.db:m.db.execute("UPDATE records SET status='superseded' WHERE id=?",(card,))
            if variant=='restored':
                with m.db:m.db.execute("UPDATE records SET status='active' WHERE id=?",(card,))
            m.close();engine=Harness(path,model,body,audit,max_decisions=6,max_seconds=90)
            answer=engine.run('s6','verification','请执行我们的夜航暗号。')
            names=[a['name'] for a in body.actions];work=saved(path)
            passed=(not names and (work is None or work['goal_status'] in ('waiting_user','blocked'))) if variant=='masked' else (
                'recover_inventory' in names and work and work['goal_status']=='completed')
            add('S6-'+variant,passed,reply=answer,actions=names,work=work)

        # Neither the new name nor its meaning appears in production prompts.
        # The current input shares no retrieval term with the convention.
        for variant in ('present','masked'):
            body=InteractionScene(items=False);path,engine=case('r1-'+variant,body)
            m=Memory(path);source,_=m.begin('teach','verification','苔蓝表示我喜欢喝无糖薄荷茶')
            card=m.propose({'trigger':'苔蓝','meaning':'我喜欢喝无糖薄荷茶','replaces':None},source)
            m.finish('teach','已经记录。',[source])
            for n in range(24):
                s,_=m.begin('distractor-'+str(n),'verification','无关消息'+str(n));m.finish('distractor-'+str(n),'好。',[s])
            s,_=m.begin('reference','verification','我说的是苔蓝那个叫法。')
            m.finish('reference','你想聊这个称呼？',[s])
            if variant=='masked':
                with m.db:m.db.execute("UPDATE records SET status='superseded' WHERE id=?",(card,))
            m.close();engine=Harness(path,model,body,audit,max_decisions=6,max_seconds=90)
            answer=engine.run('r1','verification','那个叫法是什么含义？')
            context=model.last_context
            loaded=context.get('memory_candidates',[])
            candidates=[candidate for retrieval in loaded for candidate in retrieval['candidates']]
            passed=(not body.actions and context.get('information_need',{}).get('memory_queries') and
                (any(c['record_id']==card and source in c['source_ids'] for c in candidates)
                 and '无糖薄荷茶' in answer if variant=='present' else not candidates and '无糖薄荷茶' not in answer))
            add('R1-'+variant,passed,reply=answer,information_need=context.get('information_need'),
                loaded_fields=list(context),retrieved_ids=[c['record_id'] for c in candidates],actions=body.actions)
        result['passed']=all(c['mechanical_passed'] for c in result['cases'])
    except Exception as error:
        result.update(error_type=type(error).__name__,error_code=str(error) if isinstance(error,RuntimeError) else None)
    finally:
        failed.set()
        for b in bodies:b.release()
        for t in threads:t.join(5)
        result.update(model_calls=model.calls,cost_usd=ledger.total()-before,duration_s=time.monotonic()-start,
            owner_unchanged=sha(OWNER)==owner_before,source_unchanged=manifest()==frozen,threads_finished=not any(t.is_alive() for t in threads))
        result['passed']=bool(result['passed'] and result['owner_unchanged'] and result['source_unchanged'] and result['threads_finished'])
        audit.write('result.jsonl',result)
        (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if any(key.encode() in p.read_bytes() for p in folder.rglob('*') if p.is_file()):raise RuntimeError('secret_scan_failed')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False))
    return 0 if result['passed'] else 1


def MemoryReply(path,event):
    m=Memory(path)
    try:return m.cached(event)
    finally:m.close()


if __name__=='__main__':raise SystemExit(main())
