"""Persistent controller. Its public methods receive no environment private object."""
from __future__ import annotations
from dataclasses import dataclass,asdict
from copy import deepcopy
import hashlib
import math
from .model import BeliefModel,STATES
from .cache import CacheModel
from .planner import plan,available_actions,DOMAIN
from .rollout import rollout_plan,continuation_policy

POLICIES=('candidate','flat_bayes','graph_cache','scripted','obs_only','random','oracle_reference','reactive_bayes')
ABLATIONS=('none','freeze_learning','memory_reset','no_self','no_planning',
           'no_viability','no_goal_commitment','no_replay')

@dataclass(frozen=True)
class AgentConfig:
    policy: str = 'candidate'
    ablation: str = 'none'
    planner: str = 'rollout'
    def __post_init__(self):
        if self.planner not in ('rollout','two_step'): raise ValueError('unsupported planner')
        if self.policy not in POLICIES: raise ValueError('unsupported policy')
        if self.ablation not in ABLATIONS: raise ValueError('unsupported ablation')
        if self.policy!='candidate' and self.ablation!='none':
            raise ValueError('ablations apply only to candidate')

class Agent:
    def __init__(self,config:AgentConfig):
        self.config=config
        self.model=self._new_model()
        self.memory=[]
        self.current_goal=None;self.goal_counter=0
        self.workspace=None;self.last_decision=None;self.last_learning=None
        self.total_nodes=0;self.replay_count=0;self.replay_updates=0
        self.total_surprise=0.;self.surprise_events=0;self.internal_computations=0

    def _new_model(self):
        if self.config.policy=='graph_cache':return CacheModel()
        return BeliefModel(freeze=self.config.ablation=='freeze_learning',
                           no_self=self.config.ablation=='no_self')

    def _goal_status(self,o):
        g=self.current_goal
        if not g:return 'none'
        if g['domain'] in ('energy','coolant') and o[g['domain']]>=g['target']:
            return 'completed'
        if g['domain']=='delivery':
            if o['completed']>=g['target']:return 'completed'
            if o['contract_id']!=g['contract_id'] or o['deadline'] is None:return 'abandoned'
        if g['remaining']<=0:
            return 'completed' if g['domain'] not in ('energy','coolant','delivery') else 'budget_exhausted'
        return 'active'

    def _goal_completed(self,o):
        return self._goal_status(o)=='completed'

    def _compute_plan(self,o):
        goal=self.current_goal if self.config.policy=='candidate' and self.config.ablation!='no_goal_commitment' else None
        if self._goal_status(o)!='active':goal=None
        if self.config.planner=='rollout' and self.config.ablation!='no_planning':
            return rollout_plan(o,self.model,current_goal=goal,
                                viability=self.config.ablation!='no_viability')
        return plan(o,self.model,depth=1 if self.config.ablation=='no_planning' else 2,
                    viability=self.config.ablation!='no_viability',current_goal=goal)

    def think(self,obs):
        computed=self._compute_plan(obs)
        self.workspace={'observation':deepcopy(obs),'model':self.model.snapshot(),
                        'goal':deepcopy(self.current_goal),'plan':computed}
        self.total_nodes+=computed['nodes'];self.internal_computations+=1
        return deepcopy(computed)

    def decide(self,obs):
        policy=self.config.policy
        use_cached=bool(policy in ('candidate','flat_bayes','graph_cache','oracle_reference') and self.workspace and self.workspace['observation']==obs
                        and self.workspace['model']==self.model.snapshot()
                        and self.workspace['goal']==self.current_goal)
        if policy in ('candidate','flat_bayes','graph_cache','oracle_reference'):
            result=deepcopy(self.workspace['plan']) if use_cached else self._compute_plan(obs)
        else:
            choices=available_actions(obs)
            if policy=='reactive_bayes':
                action=continuation_policy(obs,self.model)
            elif policy=='random':
                number=int.from_bytes(hashlib.sha256(f'policy:17:{obs["tick"]}'.encode()).digest()[:8],'big')
                action=choices[number%len(choices)]
            elif policy=='obs_only':
                if obs['energy']<4:action='hand_energy'
                elif obs['coolant']<2.5:action='hand_coolant'
                elif 'work' in choices:action='work'
                elif obs['energy']/7 < obs['coolant']/5:action='hand_energy'
                else:action='hand_coolant'
            else:
                if obs['tick']%16==0 and 'repair' in choices:action='repair'
                elif obs['energy']<5:action='e'+str((obs['tick']//5)%2)
                elif obs['coolant']<3:action='c'+str((obs['tick']//5)%2)
                elif 'work' in choices:action='work'
                else:action='wait'
            result={'action':action,'domain':DOMAIN[action],'scores':{},'raw_scores':{},
                    'branches':[],'candidates':[],'nodes':0,'depth':0,'score':None}
        if not use_cached:self.total_nodes+=result['nodes']
        result['used_cached_computation']=use_cached
        event='none';old_goal=deepcopy(self.current_goal)
        use_goals=policy=='candidate' and self.config.ablation!='no_goal_commitment'
        if use_goals:
            previous_outcome=self._goal_status(obs)
            completed=previous_outcome=='completed'
            same=self.current_goal and self.current_goal['domain']==result['domain'] and previous_outcome=='active'
            if same:event='continued'
            else:
                self.goal_counter+=1
                domain=result['domain']
                if domain in ('energy','coolant'):
                    expected=sum(b['probability']*b['predicted_after'][domain] for b in result['branches'])
                    target=round(min(12. if domain=='energy' else 10.,max(obs[domain],expected)),3)
                elif domain=='delivery':target=obs['completed']+1
                else:target=1
                self.current_goal={'id':self.goal_counter,'domain':domain,'target':target,
                                   'adopted_tick':obs['tick'],'contract_id':obs['contract_id'],
                                   'remaining':6 if domain in ('energy','coolant','delivery') else 1,
                                   'source':'predicted_outcome_value'}
                if previous_outcome in ('completed','abandoned','budget_exhausted'):
                    event=previous_outcome+'_then_adopted'
                else:event='revised' if old_goal else 'adopted'
        else:self.current_goal=None
        result['goal']=deepcopy(self.current_goal)
        result['goal_event']=event
        result['previous_goal']=old_goal
        result['previous_goal_outcome']=previous_outcome if use_goals else 'not_applicable'
        result['prediction']=dict(self.model.predict(result['action']))
        result['belief_before']=self.model.snapshot()
        self.last_decision=deepcopy(result);self.workspace=None
        return result

    def learn(self,transition):
        a,o=transition['action'],transition['outcome']
        predictions=dict(self.model.predict(a))
        probability=predictions.get(o,1. if o=='blocked' else 1e-12)
        surprise=-math.log(max(probability,1e-12))
        before=self.model.snapshot()
        self.memory.append(deepcopy(transition))
        self.model.update(a,o)
        if self.config.ablation=='memory_reset':self.model=self._new_model()
        self.total_surprise+=surprise;self.surprise_events+=1
        if self.current_goal:self.current_goal['remaining']-=1
        if (len(self.memory)%18==0 and self.config.ablation not in
                ('no_replay','memory_reset') and self.config.policy!='oracle_reference'):
            self.replay()
        self.last_learning={'surprise_nats':surprise,'predicted_probability':probability,
                            'model_before':before,'model_after':self.model.snapshot(),
                            'memory_events':len(self.memory)}
        return deepcopy(self.last_learning)

    def replay(self):
        if self.config.policy=='oracle_reference':
            return {'status':'not_applicable_to_privileged_reference'}
        rebuilt=self._new_model()
        for tr in self.memory:
            rebuilt.update(tr['action'],tr['outcome'])
            if self.config.ablation=='memory_reset':rebuilt=self._new_model()
        before=self.model.snapshot();after=rebuilt.snapshot()
        self.model=rebuilt;self.replay_count+=1;self.replay_updates+=len(self.memory)
        return {'status':'idempotent_reconstruction','equal':before==after,
                'events_used':len(self.memory)}

    def set_oracle_state(self,hidden):
        if self.config.policy!='oracle_reference':raise PermissionError('candidate cannot receive hidden state')
        belief=[1. if tuple(hidden)==s else 0. for s in STATES]
        self.model=BeliefModel(belief=belief)

    def snapshot(self):
        return {'schema':'switchlab.agent.v1','config':asdict(self.config),
                'model':self.model.snapshot(),'memory':deepcopy(self.memory),
                'current_goal':deepcopy(self.current_goal),'goal_counter':self.goal_counter,
                'workspace':deepcopy(self.workspace),'last_decision':deepcopy(self.last_decision),
                'last_learning':deepcopy(self.last_learning),'total_nodes':self.total_nodes,
                'replay_count':self.replay_count,'replay_updates':self.replay_updates,
                'total_surprise':self.total_surprise,'surprise_events':self.surprise_events,
                'internal_computations':self.internal_computations}

    @classmethod
    def from_snapshot(cls,data):
        if data.get('schema')!='switchlab.agent.v1':raise ValueError('invalid agent schema')
        agent=cls(AgentConfig(**data['config']))
        if set(data)!=set(agent.snapshot()):raise ValueError('invalid agent state fields')
        for key,value in data.items():
            if key not in ('schema','config','model'):setattr(agent,key,deepcopy(value))
        factory=CacheModel if data['model']['kind']=='cache' else BeliefModel
        agent.model=factory.from_snapshot(data['model'])
        return agent
