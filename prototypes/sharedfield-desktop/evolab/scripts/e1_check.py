import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import json,time
import torch
from evolab.config import Config,setup,generator,config_dict
from evolab.brains import Brain
from evolab.rollout import rollout
from evolab.evaluate import mean_ci
from evolab.render import render

def main():
    setup(); c=Config(); result={'config':config_dict(c),'baselines':{},'throughput':[]}
    Path('evidence').mkdir(exist_ok=True)
    for arm in ('R','H'):
        torch.cuda.synchronize(); start=time.perf_counter()
        score,frames=rollout(c,'static',arm,256,71,trace=arm=='H')
        torch.cuda.synchronize(); seconds=time.perf_counter()-start
        result['baselines'][arm]={**mean_ci(score),'wall_seconds':seconds,'survival':score.flatten().tolist()}
        print(arm,result['baselines'][arm]['mean'],result['baselines'][arm]['ci95'],seconds,flush=True)
        if frames: render(frames,'evidence/e1_hand_static.gif')
    result['baseline_pass']=result['baselines']['H']['ci95'][0]>result['baselines']['R']['ci95'][1]
    for batch in (2048,4096,8192):
        torch.cuda.synchronize(); start=time.perf_counter()
        score,_=rollout(c,'drift','R',batch,72)
        torch.cuda.synchronize(); elapsed=time.perf_counter()-start
        row={'arm':'R','batch':batch,'seconds':elapsed,'scheduled_individual_steps_per_second':batch*c.horizon/elapsed,
             'alive_steps_per_second':score.sum().item()*c.horizon/elapsed}
        result['throughput'].append(row);print(row,flush=True)
    for arm in ('gru_fixed','gru_mb_plastic'):
        brain=Brain(arm,c)
        mean=brain.initial_mean(generator(c.master_seed,'initial',arm))
        genomes=mean[None,:].repeat(c.population,1)
        torch.cuda.synchronize(); start=time.perf_counter()
        score,_=rollout(c,'drift',arm,c.episodes,73,genomes=genomes)
        torch.cuda.synchronize();elapsed=time.perf_counter()-start
        row={'arm':arm,'batch':c.population*c.episodes,'seconds':elapsed,'parameters':brain.nparams,
             'scheduled_individual_steps_per_second':c.population*c.episodes*c.horizon/elapsed}
        result['throughput'].append(row); print(row,flush=True)
    result['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
    Path('evidence/e1_world.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
    if not result['baseline_pass']:raise RuntimeError('H versus R engineering gate failed')

if __name__=='__main__':main()
