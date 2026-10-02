"""Paired initial-world runs; exact same controller code as the UI, no model API.

Metric fixed before the first run: discovered information - .05 per physical
step - .20 per failed move/calibration. This is a toy utility, not a subjectivity
score. Initial seeds match; action-dependent noise streams need not be identical.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from pathlib import Path
import math,statistics,json
from ..runtime import save_json
from .world import World
from .mind import Mind,MODES

MISSING=['history-conditioned recurrent meta-learner','long-context LLM with matched observations and action budget',
         'learned social world model','oracle with hidden dynamics access (upper reference, not a fair agent)']

def _run(seed,mode,steps):
    w=World(seed=seed,horizon=max(steps,1));m=Mind();m.mode=mode;m.refresh(w.observe('agent'))
    infos=0.;failures=0;losses=[];counts=Counter();diffs={'affect':0,'self':0};n=0;example=None
    for i in range(steps):
        if i==20:w.perturb('tool_fault')
        if i==40:w.perturb('storm')
        p=m.plan();action=p['action']
        if action['kind']=='sleep':break
        if mode=='full':
            for name,ab in (('affect','affect_off'),('self','self_off')):
                shadow=Mind.restore(m.snapshot());shadow.mode=ab;c=shadow.candidates()[0]
                if c['action']!=action:
                    diffs[name]+=1
                    if example is None:example={'seed':seed,'step':i,'ablation':ab,'same_current_observation':deepcopy(m.current),
                        'full':deepcopy(p),'counterfactual':deepcopy(c),'basis':'same learned history; one decision-path ablation; not an alternative full life'}
        outcome=w.act('agent',action);m.observe(outcome,'O%04d'%i);counts[action['kind']]+=1;n+=1
        if action['kind'] in ('move','calibrate'):
            pred=p['prediction']['success'];losses.append(-math.log(max(1e-9,pred if outcome['success'] else 1-pred)))
            if not outcome['success']:failures+=1
        if outcome.get('finding',{}).get('new'):infos+=outcome['finding']['richness']
    return {'seed':seed,'mode':mode,'steps':n,'discovered':len(w.discovered),'information':infos,'failures':failures,
            'utility':infos-.05*n-.20*failures,'prediction_log_loss':statistics.mean(losses) if losses else None,
            'actions':dict(counts),'calibration_count':m.self_stats['n'],'learned_events':m.learned_events,
            'same_history_decision_differences':diffs,'probe_example':example}

def run_experiments(out,seeds=8,steps=80):
    if type(seeds) is not int or not 1<=seeds<=100:raise ValueError('seeds 1..100')
    if type(steps) is not int or not 1<=steps<=500:raise ValueError('steps 1..500')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=[_run(101+31*i,mode,steps) for i in range(seeds) for mode in MODES]
    summary={}
    for mode in MODES:
        selected=[r for r in rows if r['mode']==mode]
        summary[mode]={k:statistics.mean(r[k] for r in selected) for k in ('utility','discovered','information','steps','failures')}
        ll=[r['prediction_log_loss'] for r in selected if r['prediction_log_loss'] is not None]
        summary[mode]['prediction_log_loss']=statistics.mean(ll) if ll else None
    gap=[]
    for seed in sorted({r['seed'] for r in rows}):
        by={r['mode']:r for r in rows if r['seed']==seed};gap.append(by['full']['utility']-by['flat_baseline']['utility'])
    mean=statistics.mean(gap);se=statistics.stdev(gap)/math.sqrt(seeds) if seeds>1 else None
    result={'contract':'paired initial worlds, bounded physical exploration; language NOT tested',
            'metric':'information - 0.05 * physical_steps - 0.20 * failed_actions',
            'seeds':seeds,'maximum_steps':steps,'rows':rows,'summary':summary,
            'full_minus_flat':{'mean':mean,'approx_95_interval':None if se is None else [mean-1.96*se,mean+1.96*se],
                               'paired_differences':gap,'small_sample_caution':True},
            'mechanism_superiority':'NOT_ESTABLISHED','real_language_model_tested':False,'missing_baselines':MISSING,
            'scope':'Bayesian finite-model adaptation, engineered appraisal, internal-goal selection; not true emotion, consciousness, value origin, or lifelong neural learning'}
    save_json(out/'results.json',result)
    probes=[r['probe_example'] for r in rows if r['probe_example']]
    save_json(out/'same_history_probes.json',probes)
    lines=['# Shared Field v0.5 — 实际离线比较','',f'{seeds} 个初始世界 × {len(MODES)} 个方法；每次至多 {steps} 步。第21个循环隐藏工具故障，第41个循环隐藏路况变化；未通知候选。','',
           '评价：新发现的信息收益 − 0.05×动作数 − 0.20×失败动作数。只是本环境的人工效用，不是意识、情感真实性或智能分数。',
           '初始种子配对；不同动作会消耗不同随机序列，因此不声称逐步噪声完全匹配。','',
           '| 方法 | 平均发现数 | 平均步数 | 平均失败 | 平均效用 |','|---|---:|---:|---:|---:|']
    for mode,v in summary.items():lines.append(f"| {mode} | {v['discovered']:.2f} | {v['steps']:.2f} | {v['failures']:.2f} | {v['utility']:.3f} |")
    lines += ['',f'完整候选减平坦基线，平均效用差：{mean:.4f}。不能因正/负单项指标就升级或否定所有机制。',
              '同历史决策干预只检查数值状态是否参与选择，不证明该状态有主观感受，也不证明设计优于更简单替代。','',
              '缺失强基线：'+ '；'.join(MISSING)+'。','',
              '**结论上限：当前机制优越性 NOT_ESTABLISHED。真实语言质量和共同游玩的实际体验需另外测试。**']
    (out/'BENCHMARK.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return result
