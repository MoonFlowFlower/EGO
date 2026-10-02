import argparse
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.records import ROOT,write_json,telemetry
from growthlab.host import Host
from growthlab.state import Store
from growthlab.models import Cloud
from growthlab.agent import Episode


def main():
    p=argparse.ArgumentParser();p.add_argument('--tag',default='c4');p.add_argument('--steps',type=int,default=30)
    p.add_argument('--memory',choices=['A','B']);args=p.parse_args()
    folder=ROOT/'runs/phase1'/args.tag;folder.mkdir(parents=True,exist_ok=False)
    sample=telemetry()
    if sample['ac_online'] is not True:raise RuntimeError('ac_required')
    client=Cloud(budget_path=ROOT/'runs/phase1/budget.sqlite')
    store=Store(folder/'state.sqlite');host=Host(seed=909011,length=args.steps)
    from growthlab.memory import Memory
    from growthlab.consolidation import consolidate
    memory=Memory(store,host.world,host.actions,args.memory) if args.memory else None
    episode=Episode(host,store,folder,client,arm=args.memory or 'B',memory=memory)
    result=episode.play(deadline=time.time()+900)
    if memory and not result['stop']:
        sleep=consolidate(episode);result=episode.summary();result['sleep']=sleep
        write_json(folder/'memory.json',memory.export())
    result['telemetry']=[sample,telemetry()];result['seed']=909011
    write_json(folder/'summary.json',result);write_json(ROOT/'evidence/phase1'/f'{args.tag}.json',result)
    episode.close();store.close();client.db.close()
    print({k:v for k,v in result.items() if k not in ('calls','skill_executions','telemetry')})


if __name__=='__main__':main()
