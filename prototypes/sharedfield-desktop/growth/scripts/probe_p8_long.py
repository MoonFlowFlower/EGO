import argparse,collections,json,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from growthlab.runtime import GrowthEnv
from growthlab.records import EVIDENCE,RUNS,write_json,telemetry,digest
from probe_p8 import hashes


def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int);p.add_argument('--out');a=p.parse_args()
    if a.seed is not None:
        sequence=np.random.default_rng(908000+a.seed).integers(0,17,size=2000).tolist()
        e=GrowthEnv(seed=a.seed,length=2000);e.reset();rows=[hashes(e)];used=[]
        for action in sequence:
            _,_,done,_=e.step(action);used.append(action);rows.append(hashes(e))
            if done:break
        write_json(a.out,{'steps':len(used),'done':bool(done),'dead':e._player.health<=0,'hashes':rows,
            'action_stream_sha256':digest(sequence),'executed_action_counts':dict(collections.Counter(used))})
        return
    start=time.perf_counter();rows=[];samples=[telemetry()]
    for seed in (11,23,37):
        paths=[]
        for repeat in range(2):
            path=RUNS/f'p8_long_{seed}_{repeat}.json';paths.append(path)
            cp=subprocess.run([sys.executable,__file__,'--seed',str(seed),'--out',str(path)],capture_output=True,text=True,timeout=180)
            (RUNS/f'p8_long_{seed}_{repeat}.log').write_text(cp.stdout+cp.stderr,encoding='utf-8');cp.check_returncode()
        a,b=[json.loads(x.read_text()) for x in paths]
        rows.append({'seed':seed,'steps':a['steps'],'dead':a['dead'],'cross_process_equal':a==b,
            'action_stream_sha256':a['action_stream_sha256'],'executed_action_counts':a['executed_action_counts']})
        samples.append(telemetry())
    write_json(EVIDENCE/'p8_long.json',{'seconds':time.perf_counter()-start,'max_steps':2000,'rows':rows,'telemetry':samples})
    assert all(x['cross_process_equal'] for x in rows),rows
    print(rows)


if __name__=='__main__':main()
