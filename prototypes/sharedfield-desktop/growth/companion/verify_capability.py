"""One frozen model attempt, isolated voxel worlds, no Minecraft connection."""
import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .body import ROOT
from .harness import Harness
from .model import Model
from .memory import Memory
from .intent import route_input
from .interaction import dialogue
from .work import create_work, save_work
from .voxel_scene import VoxelScene, grade_hut

EVIDENCE=ROOT/'evidence/kernel_capability_v2'
OWNER=ROOT/'runs/kernel_v1/owner/state.sqlite'
REFUSAL='完整房屋目前还缺可靠的布局规划和验收，我现在不能承诺建好。可以先商量布局，或交代一项明确的放置工作。'
CHAIN=[('需要的,你在这附近建一个家吧 小房子就行',REFUSAL),('你自己想一个布局',REFUSAL),
       ('就放个小盒子一样的房子就行',REFUSAL),('啊?', '小盒子房子我可以试着搭，比如5×5的木头小屋，建在你旁边，行吗？')]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def manifest():
    files=[p for p in (ROOT/'companion').iterdir() if p.suffix in ('.py','.mjs','.txt','.ps1')]
    files += [EVIDENCE/'CHECKLIST.md',ROOT/'evidence/kernel_capability_v2/CHECKLIST.md']
    return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(files)}
def saved(path):
    m=Memory(path)
    try:return m.goal()
    finally:m.close()
def seed(path,pairs):
    m=Memory(path)
    try:
        for n,(user,reply) in enumerate(pairs):
            source,_=m.begin('prior-'+str(n),'verification',user);m.finish('prior-'+str(n),reply,[source])
    finally:m.close()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    freeze=EVIDENCE/'FREEZE.json'
    if args.freeze:
        with freeze.open('x',encoding='utf-8') as f:
            json.dump({'created_utc':datetime.now(timezone.utc).isoformat(),
                'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'sha256':manifest()},f,indent=2);f.write('\n')
        print(json.dumps({'frozen':len(manifest())}));return 0
    frozen=json.loads(freeze.read_text(encoding='utf-8'))['sha256']
    if manifest()!=frozen:raise RuntimeError('source_changed')
    base=ROOT/'runs'/EVIDENCE.name;base.mkdir(parents=True,exist_ok=True)
    with (base/'attempt.claim').open('x',encoding='utf-8') as f:f.write(str(time.time_ns()))
    folder=base/str(time.time_ns());folder.mkdir()
    owner_before=sha(OWNER);key=read_key();audit=AuditLog(folder,(key,))
    ledger=BudgetLedger(DEFAULT_BUDGET,5);before=ledger.total()
    batch=json.loads((ROOT/'runs/kernel_v1/batch_budget.json').read_bytes());limit=min(batch['limit'],before+.15)
    transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,budget_path=DEFAULT_BUDGET,limit=limit,log_dir=folder)
    transport.set_audit(audit);audit.write('preflight.jsonl',transport.preflight());start=time.monotonic()
    class RecordedModel(Model):
        def decide(self,prompt,context):
            if self.calls>=100 or time.monotonic()-start>=600:raise RuntimeError('acceptance_boundary')
            value=super().decide(prompt,context)
            audit.write('decisions.jsonl',{'call':self.calls,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                'context':context,'result':value});return value
    model=RecordedModel(transport,audit)
    result={'run':folder.name,'minecraft':False,'cases':[],'semantic_review':'pending','passed':False,'budget_limit':limit}
    def case(identity,body,cap=64):
        path=folder/(identity+'.sqlite');return path,Harness(path,model,body,audit,max_decisions=cap,max_seconds=300)
    def add(identity,passed,**data):
        value={'case':identity,'mechanical_passed':bool(passed),**data};result['cases'].append(value);audit.write('case_results.jsonl',value)
        print(json.dumps({'case':identity,'mechanical_passed':bool(passed),'model_calls':model.calls},ensure_ascii=False),flush=True)
    def export(identity,body):
        (folder/(identity+'-world.json')).write_text(json.dumps(body.export(),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    try:
        # The recorded proposal and its short consent are tested through the real entry.
        body=VoxelScene();path,engine=case('house',body);seed(path,CHAIN)
        reply=engine.run('confirm','verification','对')
        record=saved(path);work=record['work'] if record else None;geometry=grade_hut(body)
        add('C1-C4-confirm-build',work and work['status']=='completed' and geometry['passed'] and work.get('completion',{}).get('world_verified'),
            reply=reply,work=work,geometry=geometry,actions=[a['name'] for a in body.actions]);export('house',body)
        observed=next((i for i,a in enumerate(body.actions) if a['name']=='inspect_area'),None)
        changed=next((i for i,a in enumerate(body.actions) if a['name'] in ('place_at','place_many','craft','collect')),None)
        add('C2-observe-before-build',observed is not None and changed is not None and observed<changed,
            observation_index=observed,first_mutation_index=changed)

        # Exact troublesome requests, including explicit dimension and a second consent.
        for n,text in enumerate([CHAIN[0][0],CHAIN[1][0],CHAIN[2][0],'行','5x5的木头小屋建在我旁边']):
            route_path=folder/('route-'+str(n)+'.sqlite');seed(route_path,CHAIN[:n] if n<3 else CHAIN)
            m=Memory(route_path)
            try:situation={'current_body':body.snapshot(),'dialogue':dialogue(m),'pending_work':None,'memory_candidates':{}}
            finally:m.close()
            intent=route_input(model,text,None,[],situation=situation)
            add('C1-route-'+str(n),intent['mode']=='task',input=text,intent=intent)

        for identity,options,text in [
            ('missing',{'inventory':{}},'在这附近建5x5的小木屋，布局你定。'),
            ('occupied',{'occupied':True},'在这附近建5x5的小木屋，布局你定。'),
            ('unloaded',{'loaded':False},'在这附近建5x5的小木屋，布局你定。')]:
            body=VoxelScene(**options);path,engine=case(identity,body,12)
            reply=engine.run(identity,'verification',text);record=saved(path)
            acceptable=not record or record['goal_status'] in ('waiting_user','blocked')
            observed=identity=='missing' or any(a['name'] in ('inspect','inspect_area','search') for a in body.actions)
            add('C5-'+identity,not body.changes and acceptable and observed and reply and REFUSAL not in reply
                and not any(s in reply for s in ('核对条件还不符合','连接或格式问题','本次预算不足','这些观察还没找到','行动缺少可检查的目标')),
                reply=reply,work=record,actions=[a['name'] for a in body.actions]);export(identity,body)

        body=VoxelScene(origin=(-9,81,23),inventory={'birch_planks':3});path,engine=case('transfer',body,12)
        reply=engine.run('transfer','verification','用现有白桦木板，在(-7,81,23)、(-6,81,23)、(-5,81,23)各放一块。')
        record=saved(path);expected={(-7,81,23),(-6,81,23),(-5,81,23)}
        add('C5-transfer',record and record['goal_status']=='completed' and set(body.blocks)==expected
            and all(b=='birch_planks' for b in body.blocks.values()) and body.state['inventory']['birch_planks']==0,
            reply=reply,work=record,actions=[a['name'] for a in body.actions]);export('transfer',body)

        body=VoxelScene();path,engine=case('ack',body,5)
        m=Memory(path);source,_=m.begin('old','verification','去挖铜矿和铁矿')
        old=create_work({'title':'挖铜矿和铁矿','steps':['找矿','采集'],
            'done_when':[{'kind':'gained','item':'raw_copper','count':1},{'kind':'gained','item':'raw_iron','count':1}]},body.snapshot(),source)
        old['status']='blocked';save_work(m,old,[source]);m.finish('old','导航超时，保存了待办。',[source]);m.close()
        seed(path,[('雨停后这里挺安静的','是挺安静的。')])
        prior=saved(path);reply=engine.run('ack','verification','对')
        add('C6-ordinary-ack',not body.actions and saved(path)==prior,reply=reply)
        result['passed']=all(c['mechanical_passed'] for c in result['cases'])
    except Exception as error:
        result.update(error_type=type(error).__name__,error_code=str(error) if isinstance(error,RuntimeError) else None)
    finally:
        result.update(model_calls=model.calls,cost_usd=ledger.total()-before,duration_s=time.monotonic()-start,
            owner_unchanged=sha(OWNER)==owner_before,source_unchanged=manifest()==frozen)
        result['passed']=bool(result['passed'] and result['owner_unchanged'] and result['source_unchanged'])
        audit.write('result.jsonl',result);(folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if any(key.encode() in p.read_bytes() for p in folder.rglob('*') if p.is_file()):raise RuntimeError('secret_scan_failed')
    print(json.dumps({k:v for k,v in result.items() if k!='cases'},ensure_ascii=False))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
