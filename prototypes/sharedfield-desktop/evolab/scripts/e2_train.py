import sys,json,hashlib,traceback,time,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import asdict
import torch,yaml
from evolab.config import Config,setup,generator
from evolab.brains import Brain
from evolab.es import OpenES
from evolab.rollout import rollout
from evolab.evaluate import mean_ci

PREREG='B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082'

def load_frozen():
    assert hashlib.sha256(Path('PREREG_E2.md').read_bytes()).hexdigest().upper()==PREREG
    data=Path('configs/e2_frozen.yaml').read_bytes()
    sha=hashlib.sha256(data).hexdigest()
    assert sha==Path('configs/e2_frozen.sha256').read_text().strip()
    c=Config(**yaml.safe_load(data)['world_and_es'])
    assert c.generations==400 and c.population==256 and c.episodes==8
    return c,sha

def log_failure(title,detail):
    p=Path('PROGRESS.md');data=p.read_bytes();i=data.index(b'## ')
    entry=f'## 2026-10-02 — {title}\n\n{detail}\n\n'.encode()
    p.write_bytes(data[:i]+entry+data[i:])

def run(arm,regime,run_seed,attempt=0,budget_seconds=86400):
    if Path('runs/holdout_started.json').exists():
        raise RuntimeError('Holdout already accessed: training or rerun prohibited')
    c,sha=load_frozen();setup()
    label=f'{arm}_{regime}_seed{run_seed}_attempt{attempt}'
    directory=Path('runs')/label; directory.mkdir(exist_ok=False)
    start=time.perf_counter()
    status={'label':label,'arm':arm,'regime':regime,'seed':run_seed,'attempt':attempt,'config_sha256':sha,
            'prereg_sha256':PREREG,'status':'RUNNING','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()}
    (directory/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8',newline='\n')
    try:
        brain=Brain(arm,c)
        # Identical initialization of the common backbone across arms and paired seeds.
        es=OpenES(brain.initial_mean(generator(c.master_seed,run_seed,'initial')),c)
        records=[]
        for gen in range(c.generations):
            if time.perf_counter()-start>=budget_seconds:
                raise TimeoutError('24 GPU-task-hour budget exhausted; stop')
            gen_start=time.perf_counter()
            candidates=es.ask(generator(c.master_seed,run_seed,gen,'mutation'))
            scores,_=rollout(c,regime,arm,c.episodes,run_seed,'train',gen,candidates,use_graph=True)
            fitness=scores.mean(-1)
            es.tell(fitness)
            row={'generation':gen+1,'population_mean':fitness.mean().item(),
                 'population_max':fitness.max().item(),'seconds':time.perf_counter()-gen_start}
            if (gen+1)%c.validation_every==0:
                val,_=rollout(c,regime,arm,c.validation_episodes,run_seed,'dev',0,es.mean[None],use_graph=True)
                row['development_mean']=val.mean().item()
                row['gpu_telemetry_csv']=subprocess.check_output(['nvidia-smi','--query-gpu=temperature.gpu,clocks.current.graphics,clocks.current.memory,power.draw','--format=csv,noheader,nounits'],text=True).strip()
                # Save current, never select intermediate best.
                torch.save({'mean':es.mean.cpu(),'m':es.m.cpu(),'v':es.v.cpu(),'generation':gen+1,'config_sha256':sha},directory/f'generation_{gen+1:04d}.pt')
                print(label,json.dumps(row),f'elapsed={time.perf_counter()-start:.1f}s',flush=True)
            records.append(row)
            with (directory/'generations.jsonl').open('a',encoding='utf-8',newline='\n') as f:f.write(json.dumps(row)+'\n')
        # Engineering gate uses final mean, unobserved development draws, no holdout.
        final,_=rollout(c,regime,arm,1024,run_seed,'dev',1,es.mean[None],use_graph=True)
        random,_=rollout(c,regime,'R',1024,run_seed,'dev',1)
        final_stats,random_stats=mean_ci(final),mean_ci(random)
        status.update(status='COMPLETE',generation=es.t,wall_seconds=time.perf_counter()-start,
                      training_final=final_stats,random_baseline=random_stats,
                      training_survival=final.flatten().cpu().tolist(),random_survival=random.flatten().cpu().tolist(),
                      validity_pass=final_stats['ci95'][0]>random_stats['ci95'][1],curve=records)
        torch.save({'mean':es.mean.cpu(),'generation':es.t,'config_sha256':sha,'arm':arm,'regime':regime,'seed':run_seed},directory/'final_mean.pt')
        Path('evidence/summaries').mkdir(exist_ok=True)
        (Path('evidence/summaries')/(label+'.json')).write_text(json.dumps(status,indent=2),encoding='utf-8',newline='\n')
        (directory/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8',newline='\n')
        return status
    except BaseException:
        status.update(status='FAILED',wall_seconds=time.perf_counter()-start,error=traceback.format_exc())
        (directory/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8',newline='\n')
        log_failure('E2 运行失败',f"- 运行 {label}；证据 {directory.as_posix()}/status.json。配置 {sha}。\n- 错误：```\n{status['error']}\n```\n- 未访问保留集。保留失败目录；相同种子最多一次重跑，需先分析原因。")
        raise

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--arm',choices=['gru_fixed','gru_mb_plastic'],required=True)
    p.add_argument('--regime',choices=['static','drift'],required=True);p.add_argument('--seed',type=int,choices=range(5),required=True)
    p.add_argument('--attempt',type=int,choices=[0,1],default=0);a=p.parse_args()
    print(json.dumps(run(a.arm,a.regime,a.seed,a.attempt),indent=2))
