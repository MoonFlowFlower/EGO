"""Small partially observed shared world. Hidden state never enters agent observations.

Environment outcomes are generated here, not by the language model. The finite
map and generative laws are engineered priors; the controller must learn values
and reliability from observations. This is not a computer-control adapter.
"""
from __future__ import annotations
from copy import deepcopy
import random
import json
from ..studio.protocol import obj

KINDS=('flora','echo','ruins','water')
KIND_NAMES={'flora':'苔光植物','echo':'回声','ruins':'古老构造','water':'水纹'}
ROOM_NAMES=('营地','苔光小径','回声坡','潮汐台','玻璃林','旧石庭','星纹室','溪谷','风塔','镜池','断桥台','远望台')
WIDTH=4

def neighbors(r):
    return [n for n in range(12) if abs(n//WIDTH-r//WIDTH)+abs(n%WIDTH-r%WIDTH)==1]

def edge_key(a,b):return '%d:%d'%tuple(sorted((a,b)))

def _tuple(x):return tuple(_tuple(i) for i in x) if isinstance(x,list) else x

class World:
    def __init__(self,seed=41,horizon=600):
        if type(seed) is not int or not 0<=seed<=2147483647:raise ValueError('seed must be 0..2147483647')
        if type(horizon) is not int or not 1<=horizon<=2000:raise ValueError('horizon must be 1..2000')
        self.seed=seed;self.horizon=horizon;self.tick=0;self.rng=random.Random(seed)
        self.positions={'user':0,'agent':0};self.stamina={'user':1.,'agent':1.}
        order=list(KINDS)*3;self.rng.shuffle(order)
        # Latent category returns vary by island: reward is information richness,
        # not user approval. Repeated readings never create new discoveries.
        means={k:self.rng.uniform(.25,.9) for k in KINDS}
        self.rooms=[{'id':r,'name':ROOM_NAMES[r],'kind':order[r],
                     'richness':min(1.,max(.05,self.rng.gauss(means[order[r]],.12)))} for r in range(12)]
        self.edge_stable={edge_key(a,b):self.rng.random()<.7 for a in range(12) for b in neighbors(a) if b>a}
        self.tool_skill=.90;self.discovered=set();self.visible={0,*neighbors(0)}
        self.total_failures=0

    def observe(self,actor='agent'):
        if actor not in self.positions:raise ValueError('actor must be user or agent')
        r=self.positions[actor]
        return {'tick':self.tick,'horizon':self.horizon,'position':r,
                'partner_position':self.positions['user' if actor=='agent' else 'agent'],
                'stamina':self.stamina[actor],
                'room':{k:self.rooms[r][k] for k in ('id','name','kind')},
                'surveyed':r in self.discovered,
                'neighbors':[{'id':n,'name':ROOM_NAMES[n],'kind':self.rooms[n]['kind']} for n in neighbors(r)],
                'visible_rooms':[{'id':n,'name':ROOM_NAMES[n],'kind':self.rooms[n]['kind'],
                                  'surveyed':n in self.discovered} for n in sorted(self.visible)]}

    def act(self,actor,action):
        if actor not in self.positions:raise ValueError('unknown actor')
        obj(action,('kind','target'),('kind',))
        kind=action['kind'];r=self.positions[actor]
        if self.tick>=self.horizon:raise ValueError('本次探索步数用完；可新探索并保留学习。')
        if kind not in ('move','survey','scan','calibrate','rest','repair'):raise ValueError('not an authorized shared-world action')
        if kind in ('move','scan'):
            target=action.get('target')
            if type(target) is not int or target not in neighbors(r):raise ValueError('target must be an adjacent visible location')
        elif 'target' in action:raise ValueError('target only belongs to move or scan')
        before=self.observe(actor);event={'actor':actor,'action':deepcopy(action),'before':before,'success':True,'cost':0.}
        if kind=='move':
            if self.stamina[actor]<.12:raise ValueError('体力不足，先恢复再行动。')
            stable=self.edge_stable[edge_key(r,target)]
            skill=self.tool_skill if actor=='agent' else .98
            p=(.96 if stable else .40)*skill
            ok=self.rng.random()<p
            cost=.085 if ok else .12
            if self.stamina[actor]<cost:raise ValueError('体力不足，先恢复再行动。')
            event.update(success=ok,cost=cost)
            self.stamina[actor]=max(0.,self.stamina[actor]-cost)
            if ok:self.positions[actor]=target
            else:self.total_failures+=1
        elif kind=='scan':
            if self.stamina[actor]<.025:raise ValueError('体力不足，先恢复。')
            truth=self.edge_stable[edge_key(r,target)]
            event['sensor_stable']=truth if self.rng.random()<.86 else not truth
            event['cost']=.025;self.stamina[actor]-=.025
        elif kind=='calibrate':
            if self.stamina[actor]<.03:raise ValueError('体力不足，先恢复。')
            event['success']=self.rng.random()<(self.tool_skill if actor=='agent' else .98)
            event['cost']=.03;self.stamina[actor]-=.03
        elif kind=='survey':
            if self.stamina[actor]<.035:raise ValueError('体力不足，先恢复。')
            new=r not in self.discovered
            event['finding']={'room':r,'kind':self.rooms[r]['kind'],'richness':self.rooms[r]['richness'],
                              'new':new,'name':ROOM_NAMES[r]}
            self.discovered.add(r);event['cost']=.035;self.stamina[actor]-=.035
        elif kind=='repair':
            if self.stamina[actor]<.10:raise ValueError('体力不足，先恢复。')
            self.tool_skill=.90;event['cost']=.10;self.stamina[actor]-=.10
        else:
            self.stamina[actor]=min(1.,self.stamina[actor]+.38)
        self.tick+=1
        for pos in self.positions.values():self.visible.update({pos,*neighbors(pos)})
        event['after']=self.observe(actor);event['agent_observation']=self.observe('agent')
        return event

    def perturb(self,kind):
        if kind=='storm':
            for k in self.edge_stable:self.edge_stable[k]=not self.edge_stable[k]
        elif kind=='tool_fault':self.tool_skill=.25
        elif kind=='repair':self.tool_skill=.90
        else:raise ValueError('unknown researcher intervention')
        return {'research_intervention':kind,'notified_agent':False,'physical_tick_advanced':False}

    def snapshot(self):
        return {'seed':self.seed,'horizon':self.horizon,'tick':self.tick,'rng':json.loads(json.dumps(self.rng.getstate())),
                'positions':deepcopy(self.positions),'stamina':deepcopy(self.stamina),'rooms':deepcopy(self.rooms),
                'edge_stable':deepcopy(self.edge_stable),'tool_skill':self.tool_skill,
                'discovered':sorted(self.discovered),'visible':sorted(self.visible),'total_failures':self.total_failures}

    @classmethod
    def restore(cls,s):
        w=cls(s['seed'],s['horizon'])
        for k in ('tick','positions','stamina','rooms','edge_stable','tool_skill','total_failures'):setattr(w,k,deepcopy(s[k]))
        w.discovered=set(s['discovered']);w.visible=set(s['visible']);w.rng.setstate(_tuple(s['rng']))
        return w
