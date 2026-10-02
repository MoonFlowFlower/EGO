"""Run the bounded shared-world comparison; no network or model API."""
from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from switchlab.shared.experiments import run_experiments
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',type=int,default=8);p.add_argument('--steps',type=int,default=80)
    p.add_argument('--out',default='outputs/shared_benchmark');a=p.parse_args()
    r=run_experiments(a.out,a.seeds,a.steps)
    print(json.dumps({'summary':r['summary'],'full_minus_flat':r['full_minus_flat'],
          'mechanism_superiority':r['mechanism_superiority']},ensure_ascii=False,indent=2))
