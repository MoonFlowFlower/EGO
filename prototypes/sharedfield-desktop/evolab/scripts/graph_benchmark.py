import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import torch
from evolab.config import Config,setup,generator
from evolab.brains import Brain
from evolab.rollout import rollout,_GRAPH_CACHE
setup(); c=Config();rows=[]
for arm in ('gru_fixed','gru_mb_plastic'):
    b=Brain(arm,c);genomes=b.initial_mean(generator(200))[None].repeat(256,1)
    for graph in (False,True,True):
        torch.cuda.synchronize(); start=time.perf_counter()
        score,_=rollout(c,'drift',arm,8,201,genomes=genomes,use_graph=graph)
        torch.cuda.synchronize();secs=time.perf_counter()-start
        row={'arm':arm,'graph':graph,'seconds':secs,'scheduled_equivalent_steps_per_second':2048*1500/secs,'executed_batch_steps':int(_GRAPH_CACHE[(c,'drift',arm,8,256)].index.item()) if graph else 1500,'mean':score.mean().item()}
        rows.append(row);print(row,flush=True)
Path('evidence/e1_graph_benchmark.json').write_text(json.dumps(rows,indent=2),encoding='utf-8',newline='\n')
