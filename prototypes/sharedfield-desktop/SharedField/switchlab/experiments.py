"""Fixed independent-life comparisons. Negative evidence is never mapped to PASS."""
from __future__ import annotations
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import csv
import math
import json
import statistics
import time
from .world import World,Config
from .agent import Agent,AgentConfig
from .runtime import save_json,source_fingerprint

VARIANTS=[
 {'label':'candidate','policy':'candidate'},
 {'label':'flat_bayes','policy':'flat_bayes'},
 {'label':'reactive_bayes','policy':'reactive_bayes'},
 {'label':'graph_cache','policy':'graph_cache'},
 {'label':'scripted','policy':'scripted'},
 {'label':'obs_only','policy':'obs_only'},
 {'label':'random','policy':'random'},
 {'label':'oracle_reference','policy':'oracle_reference'},
 {'label':'two_step_candidate','policy':'candidate','planner':'two_step'},
]+[{'label':x,'policy':'candidate','ablation':x} for x in
    ('freeze_learning','memory_reset','no_self','no_planning','no_viability','no_goal_commitment','no_replay')]


def run_life(task):
    start=time.perf_counter()
    world=World(Config(seed=task['seed'],horizon=task.get('horizon',96),scenario=task['scenario']))
    agent=Agent(AgentConfig(policy=task['policy'],ablation=task.get('ablation','none'),
                            planner=task.get('planner','rollout')))
    actions=Counter();shortages=0;goal_revisions=0;changed=0
    for _ in range(world.config.horizon):
        if agent.config.policy=='oracle_reference':agent.set_oracle_state(world.snapshot()['hidden'])
        d=agent.decide(world.observe());tr=world.step(d['action']);update=agent.learn(tr)
        actions[d['action']]+=1
        shortages+=int('resource_shortage' in tr['events'])
        goal_revisions+=int(d['goal_event']=='revised')
        changed+=int(update['model_before']!=update['model_after'])
    public=world.observe()
    return {'seed':task['seed'],'scenario':task['scenario'],'label':task['label'],
            'steps':world.config.horizon,'return':world.total_reward,
            'completed':public['completed'],'missed':public['missed'],
            'shortage_steps':shortages,'nodes':agent.total_nodes,
            'return_minus_compute_proxy':world.total_reward-agent.total_nodes*1e-5,
            'goal_count':agent.goal_counter,'goal_revisions':goal_revisions,
            'model_update_steps':changed,'mean_on_policy_surprise':agent.total_surprise/max(1,agent.surprise_events),
            'repairs':actions['repair'],'diagnostics':sum(actions[x] for x in ('probe_e','probe_c','calibrate')),
            'noise_actions':actions['noise'],'manual_actions':actions['hand_energy']+actions['hand_coolant'],
            'replay_count':agent.replay_count,'replay_updates':agent.replay_updates,
            'action_counts':dict(actions),'seconds':time.perf_counter()-start}


def paired_summary(rows,scenario,other):
    first={r['seed']:r for r in rows if r['scenario']==scenario and r['label']=='candidate'}
    second={r['seed']:r for r in rows if r['scenario']==scenario and r['label']==other}
    seeds=sorted(first.keys()&second.keys())
    differences=[first[s]['return']-second[s]['return'] for s in seeds]
    mean=statistics.fmean(differences) if differences else 0.
    se=statistics.stdev(differences)/math.sqrt(len(differences)) if len(differences)>1 else None
    return {'scenario':scenario,'comparison':'candidate minus '+other,'lives':len(seeds),
            'mean_delta':mean,'descriptive_normal_95_interval':None if se is None else [mean-1.96*se,mean+1.96*se],
            'differences':differences,'seeds':seeds,
            'interpretation':'descriptive paired-life interval, not multiplicity-adjusted; no mechanism pass'}


def build_summary(rows):
    aggregate=[]
    for scenario in sorted({r['scenario'] for r in rows}):
        for label in sorted({r['label'] for r in rows if r['scenario']==scenario}):
            group=[r for r in rows if r['scenario']==scenario and r['label']==label]
            result={'scenario':scenario,'label':label,'lives':len(group)}
            for key in ('return','completed','missed','shortage_steps','nodes',
                        'return_minus_compute_proxy','repairs','diagnostics','noise_actions','manual_actions'):
                values=[r[key] for r in group if key in r]
                if values:result['mean_'+key]=statistics.fmean(values)
            aggregate.append(result)
    pairs=[paired_summary(rows,scenario,label)
           for scenario in sorted({r['scenario'] for r in rows})
           for label in sorted({r['label'] for r in rows if r['scenario']==scenario and r['label']!='candidate'})]
    return {'schema':'switchlab.benchmark.v1','mechanism_status':'NOT_ESTABLISHED',
            'scope':'bounded offline fixed-family control experiment',
            'source_sha256':source_fingerprint(),'aggregate':aggregate,'paired':pairs,
            'missing_baselines':['history-conditioned Transformer','long-context LLM / RAG / scratchpad',
                                 'cross-episode recurrent meta-learner','amortized neural learner',
                                 'certified exact optimal upper bound'],
            'warnings':['The informed reference is finite-horizon approximate, not an upper bound.',
                        'Stress changes response parameters, not a held-out causal graph family.',
                        'Goal schemas, response family, continuation policy and utility are engineered priors.',
                        'On-policy surprise uses different selected data; do not compare as a common prediction test.',
                        'Compute proxy costs 0.00001 per imagined public transition; report raw return too.',
                        'Replay is exact evidence reconstruction, not learned consolidation.',
                        'No positive result authorizes integration or establishes agency/autonomy.']}


def prediction_panel(seeds):
    """Same observation/action stream for all filters; no policy selection confound."""
    records=[]
    schedule=('e0','e1','c0','c1','probe_e','probe_c','calibrate','hand_energy',
              'hand_coolant','repair','e0','c0')
    for seed in seeds:
        w=World(Config(seed=seed,horizon=96))
        agents={name:Agent(AgentConfig(ablation=ablation)) for name,ablation in
                (('candidate','none'),('freeze_learning','freeze_learning'),
                 ('no_self','no_self'),('memory_reset','memory_reset'))}
        nll=Counter();count=Counter()
        for t in range(96):
            action=schedule[t%len(schedule)];tr=w.step(action)
            for name,a in agents.items():
                p=dict(a.model.predict(action)).get(tr['outcome'],1.)
                if action in ('e0','e1','c0','c1','probe_e','probe_c','calibrate'):
                    nll[name]+=-math.log(max(1e-12,p));count[name]+=1
                a.learn(tr)
        records += [{'seed':seed,'model':name,'mean_nll':nll[name]/count[name],
                     'predictions':count[name]} for name in agents]
    return records


def run_benchmark(output,seeds=16,stress_seeds=8,jobs=1,horizon=96,progress=None):
    if not 1<=seeds<=100 or not 0<=stress_seeds<=100:raise ValueError('seed counts out of bounds')
    if not 1<=jobs<=8:raise ValueError('jobs must be 1..8')
    configs=[('standard',s) for s in range(101,101+seeds)]+[('stress',s) for s in range(1001,1001+stress_seeds)]
    tasks=[dict(variant,scenario=scenario,seed=seed,horizon=horizon)
           for scenario,seed in configs for variant in VARIANTS]
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    # Save the actual contract before running outcomes.
    save_json(output/'contract.json',{'source_sha256':source_fingerprint(),
              'tasks':tasks,'no_retuning_on_these_seeds':True,'statistical_unit':'independent life'})
    rows=[]
    if jobs==1:iterator=map(run_life,tasks);executor=None
    else:executor=ProcessPoolExecutor(max_workers=jobs);iterator=executor.map(run_life,tasks)
    try:
        with (output/'rows.partial.jsonl').open('w',encoding='utf-8') as partial:
            for row in iterator:
                rows.append(row)
                partial.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');partial.flush()
                if progress:progress(len(rows),len(tasks),row)
    finally:
        if executor:executor.shutdown(wait=True,cancel_futures=True)
    summary=build_summary(rows)
    save_json(output/'rows.json',rows);save_json(output/'summary.json',summary)
    panel=prediction_panel(range(101,101+seeds));save_json(output/'prediction_panel.json',panel)
    summary['prediction_panel_mean_nll']={name:statistics.fmean(r['mean_nll'] for r in panel if r['model']==name)
                                        for name in sorted({r['model'] for r in panel})}
    save_json(output/'summary.json',summary)
    with (output/'rows.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields=[k for k in rows[0] if k!='action_counts'];writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader();writer.writerows({k:r[k] for k in fields} for r in rows)
    from .reports import benchmark_report
    benchmark_report(summary,output/'report.html')
    return summary
