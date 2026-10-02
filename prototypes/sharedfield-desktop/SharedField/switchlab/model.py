"""Specified-family Bayesian learning and an independent predictive physical kernel.

No World object, seed, private state, intervention schedule or future trace is read.
Parameters of the response family are engineered priors; the online learned object
is the posterior over environmental modes and own actuator health.
"""
from __future__ import annotations
from itertools import product
from copy import deepcopy
import math

STATES=tuple(product((0,1),(0,1),(0,1)))
DEFAULT_PRIOR=tuple(.20 if h else .05 for e,c,h in STATES)
OUTCOMES={
 'e0':('yield','dry'),'e1':('yield','dry'),'c0':('yield','dry'),'c1':('yield','dry'),
 'probe_e':('0','1'),'probe_c':('0','1'),'calibrate':('0','1'),'noise':('0','1'),
 'repair':('repaired',),'hand_energy':('manual',),'hand_coolant':('manual',),
 'work':('worked',),'wait':('waited',)}


def likelihood(action: str, outcome: str, state: tuple) -> float:
    e,c,h=state
    if action in ('e0','e1','c0','c1'):
        correct=(int(action[-1])==(e if action[0]=='e' else c))
        p=({True:.92,False:.18}[correct] if h else {True:.14,False:.04}[correct])
        return p if outcome=='yield' else 1-p
    if action in ('probe_e','probe_c','calibrate'):
        bit=(e,c,h)[{'probe_e':0,'probe_c':1,'calibrate':2}[action]]
        return .90 if int(outcome)==bit else .10
    if action=='noise': return .5
    return 1.


# Transition kernel is the agent's engineered drift prior, not the actual hidden trajectory.
DRIFT=[]
for e,c,h in STATES:
    row=[]
    for ee,cc,hh in STATES:
        pe=.985 if e==ee else .015; pc=.985 if c==cc else .015
        ph=((.992 if hh else .008) if h else (0. if hh else 1.))
        row.append(pe*pc*ph)
    DRIFT.append(tuple(row))
DRIFT=tuple(DRIFT)
LIKELIHOODS={a:{o:tuple(likelihood(a,o,s) for s in STATES) for o in outcomes}
             for a,outcomes in OUTCOMES.items()}
LIKELIHOODS['work']['blocked']=(1.,)*8


class BeliefModel:
    def __init__(self, belief=None, freeze=False, no_self=False):
        self.freeze=bool(freeze); self.no_self=bool(no_self)
        self.belief=list(DEFAULT_PRIOR if belief is None else belief)
        if len(self.belief)!=8 or any(not isinstance(x,(int,float)) or not math.isfinite(x) or x<0 for x in self.belief):
            raise ValueError('belief must be eight finite nonnegative probabilities')
        total=sum(self.belief)
        if abs(total-1.)>1e-8: raise ValueError('belief must sum to one')
        if self.no_self: self._remove_self()

    def _remove_self(self):
        for i in range(0,8,2):
            self.belief[i+1]+=self.belief[i]; self.belief[i]=0.

    def copy(self):
        m=object.__new__(BeliefModel)
        m.belief=self.belief[:]; m.freeze=self.freeze; m.no_self=self.no_self
        return m

    def predict(self, action: str) -> list:
        return [(o,sum(b*l for b,l in zip(self.belief,LIKELIHOODS[action][o])))
                for o in OUTCOMES[action]]

    def condition(self, action: str, outcome: str, advance=True) -> 'BeliefModel':
        m=self.copy()
        if self.freeze: return m
        ls=LIKELIHOODS[action][outcome]
        weights=[b*l for b,l in zip(self.belief,ls)]
        z=sum(weights)
        if z<=0: raise ValueError('zero likelihood observation under model')
        # Avoid numerical evidence changes for exactly uninformative signals.
        if all(v==ls[0] for v in ls): m.belief=self.belief[:]
        else: m.belief=[x/z for x in weights]
        if advance:
            if action=='repair':
                for i in range(0,8,2):
                    m.belief[i+1]+=m.belief[i]; m.belief[i]=0.
            old=m.belief
            m.belief=[sum(old[i]*DRIFT[i][j] for i in range(8)) for j in range(8)]
            total=sum(m.belief);m.belief=[x/total for x in m.belief]
        if m.no_self: m._remove_self()
        return m

    def update(self, action: str, outcome: str) -> None:
        self.belief=self.condition(action,outcome).belief

    def entropy(self) -> float:
        return -sum(p*math.log2(p) for p in self.belief if p>0)

    def marginals(self) -> dict:
        return {name:sum(p for p,s in zip(self.belief,STATES) if s[i])
                for i,name in enumerate(('energy_mode_1','coolant_mode_1','tool_healthy'))}

    def snapshot(self):
        return {'kind':'bayes','belief':self.belief[:],'freeze':self.freeze,'no_self':self.no_self}

    @classmethod
    def from_snapshot(cls,data):
        if data.get('kind')!='bayes': raise ValueError('unknown model kind')
        return cls(data['belief'],data['freeze'],data['no_self'])


def physical_projection(obs: dict, action: str, outcome: str) -> tuple:
    """Predict public resource/contract consequences, not hidden state or outcome.

    This deliberately duplicates the public physics specification instead of
    calling the environment transition function during imagination.
    """
    t=obs['tick']; e=float(obs['energy']); c=float(obs['coolant'])
    progress=obs['progress']; deadline=obs['deadline']; contract=obs['contract_id']
    done=obs['completed']; missed=obs['missed']
    queue=[dict(x) for x in obs['pending']]
    cost=.20 if action in ('probe_e','probe_c','calibrate','noise') else .05
    reward=-cost
    if action in ('e0','e1','c0','c1'):
        if outcome=='yield':
            e+=5. if action.startswith('e') else 0.
            c+=5. if action.startswith('c') else 0.
        else: queue.append({'due':t+2,'energy_loss':.8})
    if action=='hand_energy': e+=1.8
    if action=='hand_coolant': c+=1.5
    if action=='repair': e-=2.;c-=1.;reward=-.40
    if action=='work' and deadline is not None and progress<3 and e>=2 and c>=1:
        e-=2.;c-=1.;progress+=1
        if progress==3: done+=1;reward+=10.
    t+=1;e-=.60;c-=.35
    e-=sum(x['energy_loss'] for x in queue if x['due']<=t)
    queue=[x for x in queue if x['due']>t]
    reward-=5.*(max(0.,-e)+max(0.,-c))
    e=round(min(12.,max(0.,e)),6);c=round(min(10.,max(0.,c)),6)
    if deadline is not None and t>=deadline:
        if progress<3: missed+=1;reward-=6.
        deadline=None;progress=0
    if t%18==0: contract+=1;deadline=t+14;progress=0
    return ({'tick':t,'energy':e,'coolant':c,'progress':progress,'deadline':deadline,
             'contract_id':contract,'pending':queue,'completed':done,'missed':missed},
            round(reward,6))
