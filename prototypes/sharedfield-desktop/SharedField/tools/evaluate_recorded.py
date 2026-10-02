"""Build-session evaluator; writes an explicit exit record even on failure."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from switchlab.runtime import save_json,source_fingerprint
from switchlab.experiments import run_benchmark

if __name__=='__main__':
    try:
        result=run_benchmark(ROOT/'evidence/benchmark',seeds=16,stress_seeds=8,jobs=4,horizon=96,
            progress=lambda n,t,r:print(f'{n}/{t} {r["scenario"]} seed={r["seed"]} {r["label"]} return={r["return"]:.3f}',flush=True))
        save_json(ROOT/'evidence/benchmark_exit.json',{'exit_code':0,'complete':True,'source_sha256':source_fingerprint()})
        print('COMPLETE',flush=True)
    except BaseException as error:
        save_json(ROOT/'evidence/benchmark_exit.json',{'exit_code':1,'complete':False,'error':repr(error)})
        raise
