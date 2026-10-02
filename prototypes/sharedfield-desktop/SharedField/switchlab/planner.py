"""Small observation-contingent planner. No outcome/goal-count/novelty reward."""
from __future__ import annotations
from .model import physical_projection

ACTION_ORDER=('e0','e1','c0','c1','hand_energy','hand_coolant','work',
              'probe_e','probe_c','calibrate','repair','wait','noise')
DOMAIN={'e0':'energy','e1':'energy','hand_energy':'energy',
        'c0':'coolant','c1':'coolant','hand_coolant':'coolant','work':'delivery',
        'probe_e':'identify_energy','probe_c':'identify_coolant',
        'calibrate':'identify_self','repair':'restore_capability',
        'wait':'rest','noise':'irrelevant_signal'}


def available_actions(obs):
    return tuple(a for a in ACTION_ORDER
                 if not (a=='work' and (obs['deadline'] is None or obs['progress']>=3
                                       or obs['energy']<2 or obs['coolant']<1))
                 and not (a=='repair' and (obs['energy']<2 or obs['coolant']<1)))


def terminal_value(obs: dict, viability=True) -> float:
    value=0.
    if viability:
        e,c=obs['energy'],obs['coolant']
        value=min(e,7.)+1.3*min(c,5.)-max(0.,3.-e)-1.5*max(0.,2.-c)
        value-=sum(.8 for x in obs['pending'])
    if obs['deadline'] is not None and obs['progress']<3:
        value+=2.8*obs['progress']
        # Deadline consequences also appear in physical_projection; no hidden schedule.
    return value


def plan(obs: dict, model, depth=2, viability=True, current_goal=None,
         switching_cost=.15) -> dict:
    if depth not in (1,2): raise ValueError('this version supports depth 1 or 2')
    nodes=0
    def qvalue(o,m,a,d):
        nonlocal nodes
        value=0.; branches=[]
        for outcome,p in m.predict(a):
            if p<=0: continue
            after,r=physical_projection(o,a,outcome);nodes+=1
            if d==1:
                tail=terminal_value(after,viability);next_action=None
            else:
                post=m.condition(a,outcome)
                choices=[(aa,qvalue(after,post,aa,d-1)[0]) for aa in available_actions(after)]
                next_action,tail=max(choices,key=lambda x:x[1])
            value+=p*(r+.97*tail)
            branches.append({'outcome':outcome,'probability':p,'next_action':next_action,
                             'predicted_after':after})
        return value,branches
    base=terminal_value(obs,viability)
    scores={}; trees={}; raw={}
    for action in available_actions(obs):
        value,branches=qvalue(obs,model,action,depth)
        raw[action]=value-base
        penalty=(switching_cost if current_goal and
                 current_goal['domain']!=DOMAIN[action] else 0.)
        scores[action]=value-base-penalty;trees[action]=branches
    chosen=max(scores,key=scores.get)
    candidates={}
    for a,v in scores.items():
        domain=DOMAIN[a]
        if domain not in candidates or v>candidates[domain]['score']:
            candidates[domain]={'domain':domain,'first_action':a,'score':v}
    return {'action':chosen,'domain':DOMAIN[chosen],'scores':scores,'raw_scores':raw,
            'branches':trees[chosen],'candidates':sorted(candidates.values(),
            key=lambda x:x['score'],reverse=True),'nodes':nodes,'depth':depth,
            'score':scores[chosen]}


def binary_diagnostic_value(prior: float, accuracy: float, cost: float) -> dict:
    """Independent exact decision fixture, NOT an agent performance result.

    Correct risky action +8, wrong -8, safe +2. Tests information value vs noise.
    """
    if not 0<=prior<=1 or not 0<=accuracy<=1 or cost<0: raise ValueError('invalid fixture')
    def best(p): return max(2.,16*p-8,8-16*p)
    expected=0.
    for signal in (0,1):
        ps=prior*(accuracy if signal else 1-accuracy)+(1-prior)*(1-accuracy if signal else accuracy)
        if ps:
            posterior=prior*(accuracy if signal else 1-accuracy)/ps
            expected+=ps*best(posterior)
    return {'without':best(prior),'with':expected-cost}
