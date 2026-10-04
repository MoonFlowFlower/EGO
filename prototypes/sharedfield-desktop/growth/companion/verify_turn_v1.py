"""One frozen real-model replay of reported conversational inputs. No game process."""
import copy
import hashlib
import json
import sqlite3
import time

from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .body import ROOT
from .harness import Harness
from .memory import Memory
from .model import Model

CASES=[('(｡･∀･)ﾉﾞ嗨','chat'),('你怎么不动了','status'),('你现在在想做什么','status')]


def main():
    base=ROOT/'runs/kernel_turn_v1';base.mkdir(parents=True,exist_ok=True)
    with (base/'attempt.claim').open('x',encoding='utf-8') as f:f.write(str(time.time_ns()))
    folder=base/str(time.time_ns());folder.mkdir()
    files=sorted(p for p in (ROOT/'companion').iterdir() if p.suffix in ('.py','.mjs','.txt','.ps1'))
    files.append(ROOT/'evidence/kernel_turn_v1/CHECKLIST.md')
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    with sqlite3.connect('file:'+str((ROOT/'runs/kernel_v1/owner/state.sqlite').as_posix())+'?mode=ro',uri=True) as source:
        with sqlite3.connect(folder/'state.sqlite') as target:source.backup(target)
    path=folder/'state.sqlite';m=Memory(path)
    try:original=m.goal();cards=m.library.cards()
    finally:m.close()
    if not original or original['goal_status']!='blocked':raise RuntimeError('blocked_goal_fixture_required')
    states=ROOT/'runs/kernel_v1/sessions/1791081296568067100/body_states.jsonl'
    state=next(json.loads(line)['state'] for line in reversed(states.read_text(encoding='utf-8').splitlines()) if not json.loads(line)['state'].get('offline'))
    class ReadOnlyBody:
        def __init__(self):self.actions=[];self.speech=[]
        def snapshot(self):return copy.deepcopy(state)
        def say(self,text):self.speech.append(text)
        def start_action(self,action,**kw):self.actions.append(action);raise RuntimeError('acceptance_action_forbidden')
        def stop(self):self.actions.append({'name':'stop'});raise RuntimeError('acceptance_action_forbidden')
    key=read_key();audit=AuditLog(folder,(key,));ledger=BudgetLedger(DEFAULT_BUDGET,5)
    total_before=ledger.total();batch=json.loads((ROOT/'runs/kernel_v1/batch_budget.json').read_text())
    transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,budget_path=DEFAULT_BUDGET,
        limit=min(batch['limit'],total_before+.15),log_dir=folder)
    transport.set_audit(audit);body=ReadOnlyBody();started=time.monotonic()
    class RecordedModel(Model):
        def decide(self,prompt,context):
            if self.calls>=12 or time.monotonic()-started>=120:raise RuntimeError('acceptance_limit')
            result=super().decide(prompt,context)
            audit.write('decisions.jsonl',{'call':self.calls,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'result':result})
            return result
    model=RecordedModel(transport,audit)
    outcome={'passed':False,'run':folder.name,'cases':[],'world_connection':False}
    try:
        audit.write('preflight.jsonl',transport.preflight())
        engine=Harness(path,model,body,audit)
        for i,(text,expected) in enumerate(CASES):
            identity='verification:turn-v1:'+str(i)
            reply=engine.run(identity,'verification',text)
            m=Memory(path)
            try:
                unchanged=m.goal()==original and m.library.cards()==cards
                routes=[r['body']['route'] for r in m.library.rows('reflection') if r['body'].get('type')=='input_route' and r['body'].get('event_id')==identity]
            finally:m.close()
            actual=routes[-1]['mode'] if routes else None
            outcome['cases'].append({'input':text,'expected':expected,'actual':actual,'goal_and_cards_unchanged':unchanged,
                'action_attempts':len(body.actions),'reply':reply,'passed':actual==expected and unchanged and not body.actions})
        unchanged_source=all(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest for name,digest in manifest.items())
        outcome.update(source_unchanged=unchanged_source)
        outcome['passed']=all(c['passed'] for c in outcome['cases']) and unchanged_source and time.monotonic()-started<120 and model.calls<=12
    except Exception as error:outcome['error_type']=type(error).__name__
    finally:
        outcome.update(model_calls=model.calls,cost_usd=ledger.total()-total_before,duration_s=time.monotonic()-started,action_attempts=len(body.actions))
        (folder/'result.json').write_text(json.dumps(outcome,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in outcome.items() if k!='cases'},ensure_ascii=False))
    return 0 if outcome['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
