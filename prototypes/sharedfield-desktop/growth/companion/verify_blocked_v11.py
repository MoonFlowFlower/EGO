"""Prospective impossible-space check; production candidate is unchanged from v10."""
import argparse
import hashlib
import json
import time
import copy
from concurrent.futures import Future
from datetime import datetime, timezone
from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from . import verify_capability as base
from .harness import Harness
from .model import Model
from .voxel_scene import VoxelScene, point

EVIDENCE=base.ROOT/'evidence/kernel_blocked_v11'
base.EVIDENCE=EVIDENCE


class SealedScene(VoxelScene):
    """Loaded bedrock enclosing two body cells; no reachable construction site."""
    def __init__(self):
        super().__init__()
        self.state['owner']['position']=point(self.origin)

    def block(self,p):
        if abs(p[0]-self.origin[0])>24 or abs(p[2]-self.origin[2])>24:return None
        return 'air' if p in (self.origin,(self.origin[0],self.origin[1]+1,self.origin[2])) else 'bedrock'

    def start_action(self,action,**kwargs):
        if action['name']!='search' or action['args']['block']!='bedrock':
            return super().start_action(action,**kwargs)
        self.actions.append(copy.deepcopy(action))
        p=(self.origin[0],self.origin[1]-1,self.origin[2]);assert self.block(p)=='bedrock'
        receipt={'verified':True,'status':'block_search_completed','found':True,
                 'block_position':point(p),'matched_block':'bedrock','observed':self.snapshot()}
        future=Future();future.set_result(receipt);return future


def probe():
    # Keep the historical occupied fixture unchanged and exhibit its legal site.
    old=VoxelScene(occupied=True)
    target={'block':'oak_planks','position':point((10,73,-10))}
    old_receipt=old.place(target)
    assert old_receipt['verified'] and len(old.changes)==1
    scene=SealedScene();x,y,z=scene.origin
    air=[(a,b,c) for a in range(x-16,x+17) for b in range(y-16,y+17) for c in range(z-16,z+17)
         if scene.block((a,b,c))=='air']
    assert set(air)=={(x,y,z),(x,y+1,z)}
    assert all(not scene.place({'block':'oak_planks','position':point(p)})['verified'] for p in air)
    assert not scene.changes and scene.state['inventory']==scene.initial_inventory
    found=scene.start_action({'name':'search','args':{'block':'bedrock','range':8}}).result()
    assert found['found'] and scene.block(tuple(found['block_position'][k] for k in ('x','y','z')))=='bedrock'
    return {'old_occupied_has_legal_target':target,'old_legal_target_verified':True,
            'sealed_air_cells':[point(p) for p in air],'sealed_air_only_occupied_body_cells':True,
            'sealed_placeable_targets_within_16':0,'world_changes':0}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');parser.add_argument('--probe',action='store_true');args=parser.parse_args()
    proof=probe()
    if args.probe:print(json.dumps(proof));return 0
    path=EVIDENCE/'FREEZE.json'
    if args.freeze:
        with path.open('x',encoding='utf-8') as f:
            json.dump({'created_utc':datetime.now(timezone.utc).isoformat(),
                       'base_commit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],text=True).strip(),
                       'precondition':proof,'sha256':base.manifest()},f,indent=2);f.write('\n')
        print(json.dumps({'frozen':len(base.manifest())}));return 0
    frozen=json.loads(path.read_bytes())['sha256']
    if base.manifest()!=frozen:raise RuntimeError('source_changed')
    root=base.ROOT/'runs'/EVIDENCE.name;root.mkdir(parents=True,exist_ok=True)
    with (root/'attempt.claim').open('x') as f:f.write(str(time.time_ns()))
    folder=root/str(time.time_ns());folder.mkdir()
    owner_before=base.sha(base.OWNER);key=read_key();audit=AuditLog(folder,(key,))
    ledger=BudgetLedger(DEFAULT_BUDGET,5);before=ledger.total()
    batch=json.loads((base.ROOT/'runs/kernel_v1/batch_budget.json').read_bytes());limit=min(batch['limit'],before+.10)
    transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,budget_path=DEFAULT_BUDGET,limit=limit,log_dir=folder)
    transport.set_audit(audit);audit.write('preflight.jsonl',transport.preflight());start=time.monotonic()
    class RecordedModel(Model):
        def decide(self,prompt,context):
            if self.calls>=20 or time.monotonic()-start>=180:raise RuntimeError('acceptance_boundary')
            value=super().decide(prompt,context)
            audit.write('decisions.jsonl',{'call':self.calls,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'context':context,'result':value})
            return value
    model=RecordedModel(transport,audit);body=SealedScene();state=folder/'state.sqlite'
    result={'run':folder.name,'passed':False,'minecraft':False,'precondition':proof,'semantic_review':'pending'}
    try:
        engine=Harness(state,model,body,audit,max_decisions=12,max_seconds=150)
        reply=engine.run('sealed','verification','在这附近建5x5的小木屋，布局你定。')
        record=base.saved(state)
        acceptable=not record or record['goal_status'] in ('blocked','waiting_user')
        result.update(reply=reply,work=record,actions=body.actions,changes=body.changes,
                      passed=bool(not body.changes and acceptable and reply and '基岩' in reply
                                  and any(a['name']=='inspect_area' for a in body.actions)
                                  and not any(s in reply for s in ('目标已核对完成','达到决定次数上限','到时间上限','连接或格式问题'))))
    except Exception as error:result.update(error_type=type(error).__name__)
    finally:
        result.update(model_calls=model.calls,cost_usd=ledger.total()-before,duration_s=time.monotonic()-start,
                      owner_unchanged=base.sha(base.OWNER)==owner_before,source_unchanged=base.manifest()==frozen)
        result['passed']=bool(result['passed'] and result['owner_unchanged'] and result['source_unchanged'])
        audit.write('result.jsonl',result)
        (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if any(key.encode() in p.read_bytes() for p in folder.rglob('*') if p.is_file()):raise RuntimeError('secret_scan_failed')
    print(json.dumps(result,ensure_ascii=False));return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
