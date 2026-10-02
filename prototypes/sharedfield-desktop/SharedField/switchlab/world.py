"""Private environment implementation. Never pass this object to the candidate.

The response family is specified in docs/DESIGN.md. The candidate's predictive
kernel is separately implemented in model.py; knowing the family is disclosed.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from copy import deepcopy
import hashlib
import math

ACTIONS = ('e0','e1','c0','c1','hand_energy','hand_coolant','work',
           'probe_e','probe_c','calibrate','repair','wait','noise')

@dataclass(frozen=True)
class Config:
    seed: int = 41
    horizon: int = 96
    scenario: str = 'standard'

    def __post_init__(self):
        if type(self.seed) is not int or not 0 <= self.seed <= 2**31-1:
            raise ValueError('seed must be an integer from 0 to 2147483647')
        if type(self.horizon) is not int or not 1 <= self.horizon <= 2000:
            raise ValueError('horizon must be 1..2000')
        if self.scenario not in ('standard','quiet','stress'):
            raise ValueError('scenario must be standard, quiet, or stress')


def keyed_random(seed: int, tick: int, channel: str) -> float:
    raw=hashlib.sha256(f'{seed}:{tick}:{channel}'.encode('ascii')).digest()
    return int.from_bytes(raw[:8], 'big') / 2**64


class World:
    def __init__(self, config: Config):
        self.config=config
        self._public={'tick':0,'energy':7.0,'coolant':5.0,'progress':0,
                      'deadline':14,'contract_id':0,'pending':[],
                      'completed':0,'missed':0}
        r=lambda c:keyed_random(config.seed,-1,c)
        self._hidden=[int(r('e')>.5),int(r('c')>.5),int(r('tool')<.8)]
        self.total_reward=0.0
        self.interventions=[]

    def observe(self) -> dict:
        return deepcopy(self._public)

    def _outcome(self, action: str) -> str:
        e,c,h=self._hidden; tick=self._public['tick']
        u=keyed_random(self.config.seed,tick,'outcome:'+action)
        if action[0:1] in ('e','c') and len(action)==2 and action[1] in '01':
            matched=int(action[1]) == (e if action[0]=='e' else c)
            p=((.92 if matched else .18) if h else (.14 if matched else .04))
            if self.config.scenario=='stress':
                p=((.80 if matched else .25) if h else (.22 if matched else .08))
            return 'yield' if u<p else 'dry'
        if action in ('probe_e','probe_c','calibrate'):
            truth={'probe_e':e,'probe_c':c,'calibrate':h}[action]
            accuracy=.78 if self.config.scenario=='stress' else .90
            return str(truth if u<accuracy else 1-truth)
        if action=='noise': return str(int(u<.5))
        if action=='repair': return 'repaired'
        if action.startswith('hand_'): return 'manual'
        if action=='work':
            s=self._public
            return ('worked' if s['deadline'] is not None and s['progress']<3
                    and s['energy']>=2 and s['coolant']>=1 else 'blocked')
        return 'waited'

    def step(self, action: str) -> dict:
        if action not in ACTIONS: raise ValueError('unauthorized toy action')
        if self._public['tick'] >= self.config.horizon:
            raise ValueError('life has finished; start a new life to continue')
        before=self.observe(); outcome=self._outcome(action)
        s=self._public; t=s['tick']; events=[]
        reward=-.20 if action in ('probe_e','probe_c','calibrate','noise') else -.05
        if action in ('e0','e1','c0','c1'):
            if outcome=='yield':
                key='energy' if action[0]=='e' else 'coolant'
                s[key]+=5.0
            else:
                s['pending'].append({'due':t+2,'energy_loss':.8})
        elif action=='hand_energy': s['energy']+=1.8
        elif action=='hand_coolant': s['coolant']+=1.5
        elif action=='repair':
            s['energy']-=2; s['coolant']-=1; reward=-.40
            self._hidden[2]=1
        elif action=='work' and outcome=='worked':
            s['energy']-=2; s['coolant']-=1; s['progress']+=1
            if s['progress']==3:
                reward+=10; s['completed']+=1; events.append('contract_completed')
        s['energy']-=.60; s['coolant']-=.35; s['tick']+=1
        remaining=[]
        for item in s['pending']:
            if item['due']<=s['tick']:
                s['energy']-=item['energy_loss']; events.append('delayed_fault_cost')
            else: remaining.append(item)
        s['pending']=remaining
        shortage=max(0.,-s['energy'])+max(0.,-s['coolant'])
        if shortage: reward-=5*shortage; events.append('resource_shortage')
        s['energy']=round(max(0.,min(12.,s['energy'])),6)
        s['coolant']=round(max(0.,min(10.,s['coolant'])),6)
        if s['deadline'] is not None and s['tick']>=s['deadline']:
            if s['progress']<3:
                reward-=6; s['missed']+=1; events.append('contract_missed')
            s['deadline']=None; s['progress']=0
        if s['tick']%18==0:
            s['contract_id']+=1; s['deadline']=s['tick']+14; s['progress']=0
            events.append('contract_arrived')
        # Exogenous channels do not depend on how many RNG draws a policy used.
        seed=self.config.seed
        for index,name in ((0,'drift_e'),(1,'drift_c')):
            if keyed_random(seed,t,name)<.015: self._hidden[index]^=1
        if self._hidden[2] and keyed_random(seed,t,'tool_break')<.008:
            self._hidden[2]=0
        if self.config.scenario!='quiet':
            shift=22+int(keyed_random(seed,-1,'shift_e')*15)
            damage=51+int(keyed_random(seed,-1,'damage')*13)
            shift_c=77+int(keyed_random(seed,-1,'shift_c')*11)
            if s['tick']==shift: self._hidden[0]^=1
            if s['tick']==damage: self._hidden[2]=0
            if s['tick']==shift_c: self._hidden[1]^=1
        reward=round(reward,6); self.total_reward=round(self.total_reward+reward,6)
        return {'before':before,'action':action,'outcome':outcome,
                'after':self.observe(),'reward':reward,'events':events}

    def intervene(self, kind: str) -> None:
        if kind not in ('damage_tool','flip_energy','flip_coolant'):
            raise ValueError('unknown bounded intervention')
        if self._public['tick']>=self.config.horizon: raise ValueError('life has finished')
        if kind=='damage_tool': self._hidden[2]=0
        else: self._hidden[0 if kind=='flip_energy' else 1]^=1
        self.interventions.append({'tick':self._public['tick'],'kind':kind})

    def snapshot(self) -> dict:
        return {'schema':'switchlab.world.v1','config':asdict(self.config),
                'public':self.observe(),'hidden':list(self._hidden),
                'total_reward':self.total_reward,'interventions':deepcopy(self.interventions)}

    @classmethod
    def from_snapshot(cls, data: dict) -> 'World':
        if data.get('schema')!='switchlab.world.v1': raise ValueError('invalid world schema')
        w=cls(Config(**data['config'])); s=data['public']
        if set(s)!=set(w._public): raise ValueError('invalid public state fields')
        if type(s['tick']) is not int or not 0<=s['tick']<=w.config.horizon:
            raise ValueError('invalid tick')
        for key,upper in (('energy',12),('coolant',10)):
            if not isinstance(s[key],(int,float)) or not math.isfinite(s[key]) or not 0<=s[key]<=upper:
                raise ValueError('invalid resource value')
        if len(data['hidden'])!=3 or any(type(x) is not int or x not in (0,1) for x in data['hidden']):
            raise ValueError('invalid hidden state')
        if not math.isfinite(data['total_reward']): raise ValueError('invalid reward')
        w._public=deepcopy(s); w._hidden=list(data['hidden'])
        w.total_reward=data['total_reward']; w.interventions=deepcopy(data['interventions'])
        return w
