"""Bounded particle-rollout MPC, not exact Bayes-optimal planning.

All first actions compete. Each is evaluated over model-sampled futures with
an observation-conditioned, deliberately simple continuation policy. That
continuation policy is an ENGINEERED computational prior, shared by candidate,
flat Bayes, cache and informed reference. It is not a learned procedural skill.
Common random numbers reduce root-action comparison noise; no environment seed,
private state, simulator function or future outcome is read.
"""
from __future__ import annotations
import random
from .model import BeliefModel, STATES, LIKELIHOODS, DRIFT, physical_projection
from .planner import available_actions,terminal_value,DOMAIN


def _select(probabilities,u):
    total=0.
    for index,p in enumerate(probabilities):
        total+=p
        if u<total:return index
    return len(probabilities)-1


def continuation_policy(obs,model):
    """Fixed rollout heuristic, disclosed and independently compared as baseline.

    Resource/contract priority follows the obs-only controller; choice between
    uncertain extraction and manual collection depends on model predictions.
    Maintenance and diagnostic decisions are NOT built into this heuristic:
    they must earn value as first actions through their later consequences.
    """
    if obs['energy']<4.:domain='energy'
    elif obs['coolant']<2.5:domain='coolant'
    elif 'work' in available_actions(obs):return 'work'
    else:domain='energy' if obs['energy']/7.<obs['coolant']/5. else 'coolant'
    alternatives=('e0','e1','hand_energy') if domain=='energy' else ('c0','c1','hand_coolant')
    values=[]
    for action in alternatives:
        if action.startswith('hand_'):value=1.8 if domain=='energy' else 1.5
        else:
            p=dict(model.predict(action))['yield']
            value=5*p-.8*(1-p)
        values.append((action,value))
    return max(values,key=lambda x:x[1])[0]


def rollout_plan(obs,model,current_goal=None,viability=True,switching_cost=.15,
                 horizon=10,particles=8):
    if type(horizon) is not int or not 1<=horizon<=16:raise ValueError('horizon must be 1..16')
    if type(particles) is not int or not 1<=particles<=32:raise ValueError('particles must be 1..32')
    rng=random.Random(20260921+1009*obs['tick'])
    initials=[(i+rng.random())/particles for i in range(particles)]
    draws=[[(rng.random(),rng.random()) for _ in range(horizon)] for _ in range(particles)]
    is_bayes=isinstance(model,BeliefModel)
    base=terminal_value(obs,viability)
    nodes=0;scores={};raw_scores={}
    for first in available_actions(obs):
        returns=[]
        for particle in range(particles):
            state=obs;belief=model.copy();value=0.;discount=1.
            imagined=_select(model.belief,initials[particle]) if is_bayes else None
            for k in range(horizon):
                action=first if k==0 else continuation_policy(state,belief)
                outcomes=belief.predict(action);u,v=draws[particle][k]
                if is_bayes:
                    probabilities=[LIKELIHOODS[action][o][imagined] for o,_ in outcomes]
                else:probabilities=[p for _,p in outcomes]
                outcome=outcomes[_select(probabilities,u)][0]
                next_state,reward=physical_projection(state,action,outcome);nodes+=1
                value+=discount*reward;discount*=.97
                belief=belief.condition(action,outcome)
                if is_bayes:
                    if action=='repair':imagined=(imagined//2)*2+1
                    imagined=_select(DRIFT[imagined],v)
                    if model.no_self:imagined=(imagined//2)*2+1
                state=next_state
            value+=discount*terminal_value(state,viability)
            returns.append(value-base)
        raw_scores[first]=sum(returns)/len(returns)
        penalty=switching_cost if current_goal and current_goal['domain']!=DOMAIN[first] else 0.
        scores[first]=raw_scores[first]-penalty
    chosen=max(scores,key=scores.get)
    branches=[]
    for outcome,p in model.predict(chosen):
        after,_=physical_projection(obs,chosen,outcome)
        branches.append({'outcome':outcome,'probability':p,
                         'next_action':continuation_policy(after,model.condition(chosen,outcome)),
                         'predicted_after':after})
    candidates={}
    for action,score in scores.items():
        domain=DOMAIN[action]
        if domain not in candidates or score>candidates[domain]['score']:
            candidates[domain]={'domain':domain,'first_action':action,'score':score}
    return {'action':chosen,'domain':DOMAIN[chosen],'scores':scores,'raw_scores':raw_scores,
            'branches':branches,'candidates':sorted(candidates.values(),key=lambda x:x['score'],reverse=True),
            'nodes':nodes,'depth':horizon,'planning_horizon':horizon,'particles':particles,
            'method':'particle_rollout_mpc','score':scores[chosen]}
