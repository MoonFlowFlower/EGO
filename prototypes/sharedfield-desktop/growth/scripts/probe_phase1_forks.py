import argparse
import json
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.forks import fork_storage,file_hash
from growthlab.state import Store
from growthlab.host import Host
from growthlab.records import ROOT,write_json,telemetry,digest
from probe_p8 import hashes


def child(seed,out):
    h=Host(seed=seed,length=2000);rng=random.Random(500000+seed);rows=[]
    for _ in range(2000):
        # Evaluator-only survival intervention to cover >6 day/night cycles.
        h.env._player.inventory['health']=9;h.done=False
        h.act(rng.choice(h.actions));rows.append(hashes(h.env))
    write_json(out,rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int);p.add_argument('--out');args=p.parse_args()
    if args.seed is not None:return child(args.seed,args.out)
    started=time.perf_counter();samples=[telemetry()];folder=ROOT/'runs/phase1/fork_acceptance';folder.mkdir(parents=True,exist_ok=False)
    source=folder/'source.sqlite';store=Store(source)
    identity=store.put('experience',{'type':'teaching','text':'synthetic marker'},'engineering',world='a'*32);store.close()
    first,second=folder/'first.sqlite',folder/'second.sqlite'
    fork_storage(source,first);fork_storage(source,second);untouched=file_hash(second)
    one=Store(first)
    with one.db:one.db.execute('DELETE FROM records WHERE id=?',(identity,))
    one.close();assert file_hash(second)==untouched
    program="import sys; from growthlab.state import Store; s=Store(sys.argv[1]); print(s.db.execute('select count(*) from records').fetchone()[0]); s.close()"
    read=subprocess.run([sys.executable,'-c',program,str(second)],cwd=ROOT,capture_output=True,text=True,check=True)
    assert read.stdout.strip()=='1'
    pairs=[]
    for seed in (909013,909017):
        paths=[]
        for repeat in (0,1):
            out=folder/f'{seed}_{repeat}.json';paths.append(out)
            subprocess.run([sys.executable,__file__,'--seed',str(seed),'--out',str(out)],check=True,timeout=240)
        a,b=[json.loads(p.read_text()) for p in paths]
        pairs.append({'seed':seed,'steps':len(a),'equal':a==b,'trajectory_sha256':digest(a)})
        assert a==b
        samples.append(telemetry())
    result={'passed':True,'seconds':time.perf_counter()-started,'fork_delete_isolated':True,
        'fresh_process_readback':True,'pairs':pairs,'telemetry':samples,
        'scope':'Evaluator health refill/terminal override; reproducibility diagnostics only, not pilot trajectories.'}
    write_json(ROOT/'evidence/phase1/c7.json',result);print(result)


if __name__=='__main__':main()
