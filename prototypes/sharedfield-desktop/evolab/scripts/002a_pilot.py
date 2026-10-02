"""F2 preregistered cumulative ladder. No holdout code or B-A selection."""
import sys, json, time, traceback, hashlib, importlib.util
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataclasses import asdict
import torch, yaml
from evolab.config import setup, generator
from evolab.es import OpenES
from evolab.v002.config import ladder, DOMAINS
from evolab.v002.brains import Brain
from evolab.v002.rollout import rollout, _CACHE
from evolab.v002.metrics import Collapse
from evolab.v002.gates import learnability
from evolab.v002.records import write_json, thermal, progress, verify_protected

LIMIT = 6*3600


def check_budget(start):
    if time.perf_counter()-start >= LIMIT:
        raise TimeoutError('F2 six GPU-task-hour budget exhausted; user decision required')


def run(c, level, arm, regime, run_seed, budget_start, full_probe=False):
    label = f'L{level}_{arm}_{regime}_seed{run_seed}'
    directory = Path('runs/002A/F2')/label
    directory.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    cfg = Path(f'configs/002a_pilot_L{level}.yaml').read_bytes()
    row = dict(label=label, level=level, arm=arm, regime=regime, seed=run_seed,
               status='RUNNING', config_sha256=hashlib.sha256(cfg).hexdigest(),
               thermal=[thermal()], curve=[], full_scale_probe=full_probe)
    write_json(directory/'status.json', row)
    try:
        brain = Brain(arm, c)
        es = OpenES(brain.initial_mean(generator(c.master_seed, DOMAINS['pilot_train'], run_seed, 'initial')), c)
        collapse = Collapse()
        for gen in range(c.generations):
            check_budget(budget_start)
            tick = time.perf_counter()
            candidates = es.ask(generator(c.master_seed, DOMAINS['pilot_train'], run_seed, gen, 'mutation'))
            scores, _ = rollout(c, regime, arm, c.episodes, run_seed, 'pilot_train', gen, candidates, use_graph=True)
            fitness = scores.mean(-1)
            std = fitness.double().std(unbiased=False).item()
            es.tell(fitness)
            collapse.update(gen+1, std)
            item = dict(generation=gen+1, population_mean=fitness.mean().item(),
                        population_max=fitness.max().item(), population_std=std,
                        seconds=time.perf_counter()-tick, collapsed_at=collapse.collapsed_at)
            if (gen+1) % 20 == 0:
                dev, _ = rollout(c, regime, arm, 128, run_seed, 'pilot_dev', 0, es.mean[None], use_graph=True)
                item['development_mean'] = dev.mean().item()
                row['thermal'].append(thermal())
                row['curve'].append(dict(item))
                print(label, json.dumps(item), f'elapsed={time.perf_counter()-start:.2f}', flush=True)
                torch.save(dict(mean=es.mean.cpu(), m=es.m.cpu(), v=es.v.cpu(), generation=es.t,
                                config_sha256=row['config_sha256']), directory/f'generation_{es.t:04d}.pt')
            with (directory/'generations.jsonl').open('a', encoding='utf-8') as f:
                f.write(json.dumps(item)+'\n')
            if collapse.collapsed_at is not None and not full_probe:
                break
        check_budget(budget_start)
        scores, result = rollout(c, regime, arm, 512, run_seed, 'pilot_dev', 1, es.mean[None], telemetry=True)
        metrics = result['metrics']
        torch.save(dict(scores=scores.cpu(), good=metrics.good.cpu(), bad=metrics.bad.cpu(),
                        survived_first=metrics.survived_first.cpu(), start=metrics.start.cpu(),
                        duration=metrics.duration.cpu(), observed=metrics.observed.cpu()), directory/'development.pt')
        torch.save(dict(mean=es.mean.cpu(), generation=es.t, config_sha256=row['config_sha256']), directory/'final_mean.pt')
        row.update(status='COMPLETE', generation=es.t, collapsed_at=collapse.collapsed_at,
                   selection='generation_400_mean' if es.t == 400 else 'collapse_detection_mean',
                   development=result['summary'], episodes=512, seconds=time.perf_counter()-start)
        row['thermal'].append(thermal())
        write_json(directory/'status.json', row)
        write_json(Path('evidence/002A/pilot_summaries')/(label+'.json'), row)
        print('COMPLETED', label, json.dumps(row['development']), f'seconds={row["seconds"]:.3f}', flush=True)
        return row
    except BaseException:
        row.update(status='FAILED', error=traceback.format_exc(), seconds=time.perf_counter()-start)
        write_json(directory/'status.json', row)
        write_json(Path('evidence/002A/pilot_summaries')/(label+'.json'), row)
        progress('F2 运行失败/停止', f'- {label}；证据 {directory.as_posix()}/status.json。\n- {row["error"]}\n- 保留失败目录，未访问保留集。')
        raise


def main():
    setup(); verify_protected()
    f1 = json.loads(Path('evidence/002A/f1_world_gate.json').read_text())
    assert f1['status'] == 'PASS'
    path = Path('evidence/002A/f2_learnability.json')
    if path.exists():
        raise RuntimeError('F2 already started; inspect evidence before any retry')
    result = dict(status='RUNNING', levels=[], selected_level=None, budget_seconds=LIMIT,
                  full_probe='L0/gru_mb_plastic/drift/seed0; 400 generations even if collapsed')
    start = time.perf_counter()
    write_json(path, result)
    try:
        for level in range(4):
            check_budget(start)
            c = ladder(level, f1['selected_poison'])
            configuration = dict(world_and_es=asdict(c), seed_domains=DOMAINS,
                pilot_seeds=[0, 1, 2], gate_episodes=512, validation_episodes=128,
                fitness='mean survival fraction only', selection='400 mean or collapse_detection_mean',
                collapsed_at='first generation ending 20 consecutive exact-zero population stds',
                full_probe=result['full_probe'])
            config_path = Path(f'configs/002a_pilot_L{level}.yaml')
            with config_path.open('x', encoding='utf-8', newline='\n') as f:
                yaml.safe_dump(configuration, f, sort_keys=True)
            current = dict(level=level, config=asdict(c), runs=[], gate=None)
            result['levels'].append(current)
            if level == 3:
                spec = importlib.util.spec_from_file_location('world_gate', Path(__file__).with_name('002a_world_gate.py'))
                module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
                current['world_recheck'] = module.gate(c)
                if not current['world_recheck']['passed']:
                    result['status'] = 'STOP_W_RECHECK_FAILED'
                    result['seconds'] = time.perf_counter()-start
                    write_json(path, result)
                    return
            else:
                current['world_recheck'] = 'F1 reused: view/ES-only changes do not affect scripted world trajectories'
            # Fixed order announced before outcomes; every arm/world/seed retained.
            order = [('gru_mb_plastic', 'drift', 0)]
            order += [(arm, world, seed) for arm in ('gru_fixed', 'gru_mb_plastic')
                      for world in ('static', 'drift') for seed in range(3)
                      if (arm, world, seed) != order[0]]
            for arm, world, seed in order:
                check_budget(start)
                row = run(c, level, arm, world, seed, start, full_probe=(level == 0 and len(current['runs']) == 0))
                current['runs'].append(row)
                result['seconds'] = time.perf_counter()-start
                if level == 0 and len(current['runs']) == 1:
                    result['full_probe_seconds'] = row['seconds']
                    # L0/L1 baseline + L2/L3 doubled population; conservative rough planning.
                    result['projected_all_four_levels_seconds'] = row['seconds']*12*6
                    print('FULL_PROBE', result['full_probe_seconds'], 'PROJECTED_FOUR_LEVELS', result['projected_all_four_levels_seconds'], flush=True)
                    if result['projected_all_four_levels_seconds'] > LIMIT:
                        result['status'] = 'STOP_PROJECTED_BUDGET'
                        write_json(path, result)
                        return
                write_json(path, result)
            current['gate'] = learnability(current['runs'], 3)
            print('LEVEL_GATE', level, json.dumps(current['gate']), flush=True)
            progress(f'F2 L{level} 试跑闸门', '- ' + json.dumps(current['gate'], ensure_ascii=False) +
                     f'\n- 完整12次结果 evidence/002A/f2_learnability.json、pilot_summaries；累计{result["seconds"]:.1f}秒。未访问保留集。')
            if current['gate']['passed']:
                result.update(status='PASS', selected_level=level)
                write_json(path, result)
                return
            write_json(path, result)
            _CACHE.clear()  # release old level graph buffers, no policy state carried across runs
        result['status'] = 'STOP_L_EXHAUSTED'
        result['seconds'] = time.perf_counter()-start
        write_json(path, result)
    except BaseException:
        result.update(status='FAILED_OR_BUDGET_STOP', error=traceback.format_exc(), seconds=time.perf_counter()-start)
        write_json(path, result)
        raise


if __name__ == '__main__':
    main()
