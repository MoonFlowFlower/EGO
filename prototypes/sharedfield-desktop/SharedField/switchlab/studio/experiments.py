"""Callable, finite and deliberately falsifiable probes. No real LLM is used.

All prediction controls see the same history. This is an offline prediction /
choice probe, NOT an on-policy long-horizon human-interaction evaluation.
"""
from __future__ import annotations
from copy import deepcopy
import json
import math
from pathlib import Path
import random
import time
from .learning import OutcomeLearner
from .neural import TinyNet
from .adaptive_core import AdaptiveCore
from switchlab.runtime import save_json

def _x(context,action):
    x=[0.]*80
    x[:6]=context;x[48+action]=1.;x[72]=.5
    return x

def _value(context,action):
    # Nonlinear, unknown to every learner. Oracle reads it only in the evaluator.
    a,b,c,d,e,f=context
    raw=.8*a-.65*b+.6*c*d+.25*e-.2*f
    return 1./(1.+math.exp(-4.*(raw if action==1 else -raw)))

def run_prediction_probe(seed=1,training=160,testing=64):
    if not 8<=training<=500 or not 4<=testing<=200:raise ValueError('bounded probe sizes required')
    rng=random.Random(seed);l=OutcomeLearner(capacity=128,seed=seed+73)
    # Uniform, method-independent data collection. No candidate-specific truth or tuning.
    for i in range(training):
        context=[rng.uniform(-1,1) for _ in range(6)];a=rng.randrange(2);target=_value(context,a)
        l.learn(f'train:{i}',_x(context,a),[target]*3+[0.]*24,[1.]*3+[0.]*24)
        if i%8==7:l.replay(4)
    before=l.net.weight_digest();rows={m:{'mse':0.,'regret':0.,'optimal_choices':0} for m in ('neural','similarity','adaptive','frozen_prior','oracle')}
    for _ in range(testing):
        context=[rng.uniform(-1,1) for _ in range(6)];truth=[_value(context,a) for a in range(2)]
        for method,row in rows.items():
            if method=='oracle':pred=truth
            elif method=='frozen_prior':pred=[.5,.5]
            else:pred=[l.predict(_x(context,a),method)['utility'] for a in range(2)]
            chosen=max(range(2),key=lambda a:pred[a]);correct=max(range(2),key=lambda a:truth[a])
            row['mse']+=sum((p-t)**2 for p,t in zip(pred,truth))/2/testing
            row['regret']+=(truth[correct]-truth[chosen])/testing
            row['optimal_choices']+=int(chosen==correct)
    assert before==l.net.weight_digest(), 'held-out evaluation must not train'
    for r in rows.values():r['optimal_fraction']=r['optimal_choices']/testing
    return {'seed':seed,'training_observations':training,'heldout_contexts':testing,'methods':rows,
        'label_source':'synthetic_generator','real_language_test':False,'heldout_learning':False,
        'learner':l.summary(),'scope':'same-history finite nonlinear outcome prediction; no on-policy or human utility claim'}

def run_retention_probe(seed=1):
    def sample(task):
        x=[0.]*80;x[task]=1.;x[5]=.6
        return x,[float(task==0)]*3+[0.]*24,[1.]*3+[0.]*24
    results={}
    for condition in ('no_replay','replay','matched_current_only'):
        l=OutcomeLearner(seed=73+seed);x,y,m=sample(0)
        for i in range(100):l.learn(f'a:{i}',x,y,m)
        before=l.net.loss(x,y,m)
        for i in range(100):
            xb,yb,mb=sample(1);l.learn(f'b:{i}',xb,yb,mb)
            if condition=='replay':l.replay(2)
            elif condition=='matched_current_only':
                # Same total updates as replay, but all extra updates use current-task data.
                for _ in range(2):l.net.train(xb,yb,mb)
        results[condition]={'old_task_mse_before':before,'old_task_mse_after':l.net.loss(x,y,m),
            'new_task_mse':l.net.loss(*sample(1)),'new_external_samples':l.seen,'gradient_updates':l.net.updates}
    results['task_keyed_lookup']={'old_task_mse_after':0.,'new_task_mse':0.,
        'note':'A task-keyed table saturates these two deterministic tasks; no neural necessity shown.'}
    return results

def _proposal(source,reverse=False):
    candidates=[]
    for key in ('compare','direct'):
        candidates.append({'id':key,'intent':key+' a bounded solution','kind':'reply','skill':key,
                           'basis':[source],'expected':'a user-reported task outcome','goals':[],'revisions':[]})
    if reverse:candidates.reverse()
    return {'summary':'synthetic control fixture','claims':[],'memories':[],'candidates':candidates}

def run_causal_history(preferred,rounds=12):
    c=AdaptiveCore();c.apply('selection_mode',{'mode':'language_order'})
    for i in range(rounds):
        e=c.apply('message',{'text':'SYNTHETIC PROBE: choose a bounded solution.'})
        a=c.apply('analyse',{'source':e['id'],'packet':_proposal(e['id'],bool(i%2))})
        did=a['result']['decision_id'];chosen=c._decision(did)['selected']['candidate']['id']
        c.apply('express',{'decision_id':did,'speech':'Synthetic fixture, not a real model response.'})
        val=float(chosen==preferred)
        c.apply('outcome',{'decision_id':did,'task':val,'constraint':val,'understanding':val,'note':'synthetic generator label'})
    c.apply('selection_mode',{'mode':'adaptive'})
    e=c.apply('message',{'text':'SYNTHETIC PROBE: choose a bounded solution.'})
    a=c.apply('analyse',{'source':e['id'],'packet':_proposal(e['id'])})
    did=a['result']['decision_id'];d=deepcopy(c._decision(did))
    c.apply('express',{'decision_id':did,'speech':'Synthetic evaluation response.'})
    return c,{'preferred_in_training':preferred,'chosen_on_identical_candidates':d['selected']['candidate']['id'],
              'scores':{r['candidate']['id']:r['score'] for r in d['ranked']},
              'counterfactual_history_scope':'same candidate set, different explicitly supplied histories',
              'evidence_kind':'synthetic_main_controller_intervention_not_real_language_quality'}

def run_all(out,seeds=4,training=160,testing=64):
    if not 1<=seeds<=12:raise ValueError('seeds 1..12')
    start=time.perf_counter();out=Path(out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for i in range(seeds):
        row=run_prediction_probe(100+i,training,testing);rows.append(row)
        save_json(out/'prediction_rows.json',rows)
    aggregate={m:{k:sum(r['methods'][m][k] for r in rows)/len(rows)
                 for k in ('mse','regret','optimal_fraction')} for m in rows[0]['methods']}
    retention=run_retention_probe();causal=[]
    for preference in ('compare','direct'):
        c,result=run_causal_history(preference);causal.append(result)
        save_json(out/f'causal_{preference}.json',c.checkpoint())
    summary={'prediction':aggregate,'seeds':seeds,'retention':retention,'causal_history':causal,
        'seconds':time.perf_counter()-start,'training':training,'testing':testing,
        'claim':'bounded offline evidence under this synthetic trace contract; no real language effectiveness result',
        'neural_superiority_established':False,
        'missing_baselines':['history-conditioned language transformer','long-context LLM','cross-episode meta-learner','amortized learner'],
        'status':'do not expand mechanism claims from this experiment'}
    save_json(out/'summary.json',summary)
    lines=['# v0.3 当前实现的实际离线实验','',
           '标签来自合成生成器，不来自真实模型或人类测试。所有预测器看到同一训练历史；测试集不更新。它不是闭环现实收益评测。','',
           '| 方法 | 测试 MSE ↓ | 平均后悔值 ↓ | 选中最优动作比例 ↑ |','|---|---:|---:|---:|']
    for m,r in aggregate.items():lines.append(f"| {m} | {r['mse']:.6f} | {r['regret']:.6f} | {100*r['optimal_fraction']:.1f}% |")
    lines += ['',f'独立生成种子：{seeds}；每种子 {training} 条训练观测、{testing} 个留出情境。',
              'oracle 使用真实生成函数，仅为有限任务上界。frozen_prior 固定输出 0.5。',
              '', '## 重放与保留（两项确定性任务，非终身学习证明）','', '```json',json.dumps(retention,ensure_ascii=False,indent=2),'```',
              '', 'matched_current_only 与 replay 的真实样本数、总梯度次数相同；它将额外计算全部用于当前任务，而不是旧经历。', '', '## 完整控制器中的历史干预','', '```json',json.dumps(causal,ensure_ascii=False,indent=2),'```',
              '', '两个历史都经过真实 AdaptiveCore.message/analyse/express/outcome 入口；语言候选和回复是明确标注的夹具。',
              '参数变化、候选变化与任务成功是不同结论。即使出现正向差异，也不证明社交理解、主体性、开放价值形成或现实净收益。',
              '', '简单预测器若胜出，默认混合控制器可选择它；不通过重写测试指标保证神经方案获胜。',
              '没有对长上下文语言模型和跨 episode 元学习器完成公平比较；当前架构相对普通 LLM 的净收益为 unknown。']
    (out/'BENCHMARK.md').write_text('\n'.join(lines),encoding='utf-8')
    return summary
