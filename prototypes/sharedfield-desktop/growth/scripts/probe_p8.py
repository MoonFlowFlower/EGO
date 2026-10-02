"""Evaluator-only full-state hashes; no output from this probe goes to a model."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import crafter
from growthlab.runtime import GrowthEnv
from growthlab.records import RUNS, EVIDENCE, write_json, digest, telemetry


def normalize(v):
    if isinstance(v, np.ndarray): return v.tolist()
    if isinstance(v, np.generic): return v.item()
    if isinstance(v, dict): return {k: normalize(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)): return [normalize(x) for x in v]
    if isinstance(v, set): return sorted(normalize(x) for x in v)
    if isinstance(v, (str, int, float, bool)) or v is None: return v
    return type(v).__name__


def hashes(e):
    state = {'map': normalize(e._world._mat_map), 'objects': [
        None if obj is None else {'type': type(obj).__name__, 'fields': normalize(vars(obj))}
        for obj in e._world._objects], 'step': e._step, 'unlocked': sorted(e._unlocked)}
    return digest(state), digest(normalize(e._world.random.get_state()))


def trial(fixed, mode, seed, out):
    cls = GrowthEnv if fixed else crafter.Env
    e = cls(seed=seed, length=360, size=(128,128) if mode == 'size128' else (64,64))
    if fixed == 2:  # isolate rendering issue while canonicalizing object order
        from crafter.engine import LocalView
        e._local_view = LocalView(e._world, e._textures, e._local_view._grid)
        e._local_view.visual_random = np.random.RandomState(0)
    env = e
    if mode == 'video':
        env = crafter.Recorder(e, out.parent / (out.stem + '_video'),
                               save_stats=False, save_episode=False, video_size=(128,128))
    env.reset()
    rows = [hashes(e)]
    begin = time.perf_counter()
    for t in range(360):
        _, _, done, _ = env.step(0)
        if mode == 'extra': e.render((128,128))
        rows.append(hashes(e))
        if done: break
    write_json(out, {'seed': seed, 'fixed': fixed, 'mode': mode, 'steps': len(rows)-1,
                     'seconds': time.perf_counter()-begin, 'hashes': rows})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--child', action='store_true'); p.add_argument('--fixed', type=int)
    p.add_argument('--mode'); p.add_argument('--seed', type=int); p.add_argument('--out')
    a = p.parse_args()
    if a.child: return trial(a.fixed, a.mode, a.seed, Path(a.out))
    start = time.perf_counter(); samples = [telemetry()]; results = []
    for fixed in (0, 2, 1):
        for seed in (11, 23):
            runs = {}
            for tag, mode in [('base','base'), ('repeat','base'), ('extra','extra'), ('size128','size128'), ('video','video')]:
                path = RUNS / f'p8_{fixed}_{seed}_{tag}.json'
                child = subprocess.run([sys.executable, __file__, '--child', '--fixed', str(fixed),
                                        '--seed', str(seed), '--mode', mode, '--out', str(path)],
                                       capture_output=True, text=True, timeout=240)
                (RUNS / f'p8_{fixed}_{seed}_{tag}.log').write_text(child.stdout + child.stderr, encoding='utf-8')
                if child.returncode: raise RuntimeError(f'child failed; see {tag} log')
                runs[tag] = json.loads(path.read_text(encoding='utf-8'))
            base = runs['base']['hashes']
            for tag, row in runs.items():
                def first(col):
                    return next((i for i,(x,y) in enumerate(zip(base, row['hashes'])) if x[col] != y[col]), None)
                results.append({'fix': {0:'upstream',2:'order_only',1:'order_and_visual_rng'}[fixed], 'seed': seed, 'mode': tag,
                    'steps': row['steps'], 'seconds': row['seconds'],
                    'first_state_difference_step': first(0), 'first_rng_difference_step': first(1),
                    'equal_length': len(base) == len(row['hashes'])})
            samples.append(telemetry())
    write_json(EVIDENCE / 'p8_reproducibility.json', {'seconds': time.perf_counter()-start,
               'rows': results, 'telemetry': samples, 'scope': '2 seeds, no-op episodes, separate processes'})
    print(json.dumps(results, indent=2))


if __name__ == '__main__': main()
