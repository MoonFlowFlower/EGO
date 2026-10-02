"""Actual wired runtime plus transparent, deterministic trace/checkpoint verification.

Hash chains detect edits, not authorship. Semantic replay also checks rehashed
fabrications. A newly regenerated valid run is not an authenticated historical run.
Floats are compared/hash-canonicalized to 12 decimal places, not claimed bit-identical
across all Python/OS implementations. Checkpoint JSON retains full float precision.
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import math
import os
import platform
import tempfile
from .world import World,Config
from .agent import Agent,AgentConfig

ROOT=Path(__file__).resolve().parents[1]
MAX_JSON_BYTES=64*1024*1024


def _normal(value):
    if isinstance(value,float):
        if not math.isfinite(value):raise ValueError('non-finite number in artifact')
        x=round(value,12)
        return 0.0 if x==0 else x
    if isinstance(value,dict):return {str(k):_normal(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [_normal(x) for x in value]
    return value


def canonical(value):
    return json.dumps(_normal(value),sort_keys=True,separators=(',',':'),
                      ensure_ascii=False,allow_nan=False)


def digest(value):return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def source_fingerprint():
    files=sorted((ROOT/'switchlab').rglob('*.py'))
    files+=sorted((ROOT/'switchlab'/'web').glob('*'))
    if (ROOT/'run.py').exists():files.append(ROOT/'run.py')
    records=[(p.relative_to(ROOT).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest())
             for p in files if p.is_file()]
    return digest(records)


def save_json(path,data):
    encoded=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=path.parent,
                                         prefix='.'+path.name+'.',suffix='.tmp',delete=False) as f:
            temporary=Path(f.name);f.write(encoded);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temporary,path);temporary=None
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def load_json(path):
    p=Path(path)
    if p.stat().st_size>MAX_JSON_BYTES:raise ValueError('JSON exceeds 64 MiB bound')
    def reject_constant(x):raise ValueError('invalid JSON constant '+x)
    def unique(pairs):
        d={}
        for key,value in pairs:
            if key in d:raise ValueError('duplicate JSON key: '+key)
            d[key]=value
        return d
    with p.open(encoding='utf-8') as f:
        return json.load(f,parse_constant=reject_constant,object_pairs_hook=unique)


class Session:
    def __init__(self,world_config=None,agent_config=None):
        self.world=World(world_config or Config())
        self.agent=Agent(agent_config or AgentConfig())
        self.metadata={'world_config':asdict(self.world.config),'agent_config':asdict(self.agent.config),
                       'source_sha256':source_fingerprint(),'python':platform.python_version(),
                       'scope':'bounded_offline_only','float_comparison_decimals':12}
        self.initial=self._states();self.events=[]
        self.head=digest({'metadata':self.metadata,'initial':self.initial})

    def _states(self):return {'world':self.world.snapshot(),'agent':self.agent.snapshot()}

    def _append(self,op,result):
        payload={'index':len(self.events),'op':deepcopy(op),'result':deepcopy(result)}
        event=dict(payload,previous=self.head)
        event['hash']=digest(event);self.head=event['hash'];self.events.append(event)
        return deepcopy(event)

    def step(self):
        if self.world.observe()['tick']>=self.world.config.horizon:raise ValueError('life has finished')
        if self.agent.config.policy=='oracle_reference':
            self.agent.set_oracle_state(self.world.snapshot()['hidden'])
        # This is the only normal policy input: a copied public observation.
        decision=self.agent.decide(self.world.observe())
        transition=self.world.step(decision['action'])
        learning=self.agent.learn(transition)
        return self._append({'kind':'step'}, {'decision':decision,'transition':transition,
                                              'learning':learning})

    def compute(self):
        if self.world.observe()['tick']>=self.world.config.horizon:raise ValueError('life has finished')
        before=self.agent.model.snapshot()
        result=self.agent.think(self.world.observe())
        return self._append({'kind':'compute'}, {'plan':result,
                            'belief_unchanged':before==self.agent.model.snapshot()})

    def replay_memory(self):
        return self._append({'kind':'replay_memory'},self.agent.replay())

    def intervene(self,kind):
        before=self.world.observe();belief=self.agent.model.snapshot()
        self.world.intervene(kind)
        return self._append({'kind':'intervene','intervention':kind},
                            {'public_observation_unchanged':before==self.world.observe(),
                             'belief_unchanged':belief==self.agent.model.snapshot()})

    def export_trace(self):
        final=self._states()
        return {'schema':'switchlab.trace.v1','metadata':deepcopy(self.metadata),
                'initial':deepcopy(self.initial),'events':deepcopy(self.events),
                'head':self.head,'final':final,'final_hash':digest(final)}

    def checkpoint(self):return {'schema':'switchlab.checkpoint.v1','trace':self.export_trace()}

    @classmethod
    def from_checkpoint(cls,data):
        if data.get('schema')!='switchlab.checkpoint.v1' or set(data)!= {'schema','trace'}:
            raise ValueError('invalid checkpoint schema')
        trace=data['trace'];verify_trace(trace)
        session=cls(Config(**trace['metadata']['world_config']),AgentConfig(**trace['metadata']['agent_config']))
        # Readback of serialized final states is used, not merely the replayed objects.
        session.world=World.from_snapshot(deepcopy(trace['final']['world']))
        session.agent=Agent.from_snapshot(deepcopy(trace['final']['agent']))
        session.metadata=deepcopy(trace['metadata']);session.initial=deepcopy(trace['initial'])
        session.events=deepcopy(trace['events']);session.head=trace['head']
        return session

    def public_view(self):
        o=self.world.observe();a=self.agent
        return {'observation':o,'config':asdict(self.world.config),'agent_config':asdict(a.config),
                'done':o['tick']>=self.world.config.horizon,'total_reward':self.world.total_reward,
                'marginals':a.model.marginals(),'entropy_bits':a.model.entropy(),
                'goal':deepcopy(a.current_goal),'goal_counter':a.goal_counter,
                'memory_count':len(a.memory),'replay_count':a.replay_count,
                'planning_nodes':a.total_nodes,'internal_computations':a.internal_computations,
                'decision':deepcopy(a.last_decision),'learning':deepcopy(a.last_learning),
                'workspace_ready':a.workspace is not None,
                'preview_plan':deepcopy(a.workspace['plan']) if a.workspace else None,
                'events':deepcopy(self.events[-16:]),'head':self.head,
                'evaluator_truth':{'energy_mode':self.world.snapshot()['hidden'][0],
                                   'coolant_mode':self.world.snapshot()['hidden'][1],
                                   'tool_healthy':bool(self.world.snapshot()['hidden'][2])},
                'scope':'离线有限模型族；无主体性、真实自主或优越性结论'}


def rechain(trace):
    """Public utility intentionally available: hash integrity is NOT authenticity."""
    head=digest({'metadata':trace['metadata'],'initial':trace['initial']})
    for i,event in enumerate(trace['events']):
        event['index']=i;event['previous']=head
        event.pop('hash',None);event['hash']=digest(event);head=event['hash']
    trace['head']=head;trace['final_hash']=digest(trace['final'])
    return trace


def verify_trace(trace,check_source=True):
    expected_fields={'schema','metadata','initial','events','head','final','final_hash'}
    if not isinstance(trace,dict) or set(trace)!=expected_fields or trace.get('schema')!='switchlab.trace.v1':
        raise ValueError('invalid trace schema')
    if not isinstance(trace['events'],list) or len(trace['events'])>10000:
        raise ValueError('invalid trace event bound')
    source_matches=trace['metadata']['source_sha256']==source_fingerprint()
    if check_source and not source_matches:raise ValueError('source fingerprint mismatch; do not claim same-source replay')
    head=digest({'metadata':trace['metadata'],'initial':trace['initial']})
    for i,event in enumerate(trace['events']):
        if set(event)!= {'index','op','result','previous','hash'}:raise ValueError('invalid event fields')
        if event['index']!=i or event['previous']!=head:raise ValueError(f'chain sequence mismatch at {i}')
        payload={k:v for k,v in event.items() if k!='hash'}
        if digest(payload)!=event['hash']:raise ValueError(f'event hash mismatch at {i}')
        head=event['hash']
    if head!=trace['head'] or digest(trace['final'])!=trace['final_hash']:
        raise ValueError('trace head or final state digest mismatch')
    session=Session(Config(**trace['metadata']['world_config']),AgentConfig(**trace['metadata']['agent_config']))
    if canonical(session.initial)!=canonical(trace['initial']):raise ValueError('noncanonical initial state')
    # Preserve recorded metadata (including Python version) for portable replay.
    session.metadata=deepcopy(trace['metadata']);session.initial=deepcopy(trace['initial'])
    session.head=digest({'metadata':session.metadata,'initial':session.initial})
    for i,expected in enumerate(trace['events']):
        op=expected['op'];kind=op.get('kind')
        if kind=='step' and set(op)=={'kind'}:actual=session.step()
        elif kind=='compute' and set(op)=={'kind'}:actual=session.compute()
        elif kind=='replay_memory' and set(op)=={'kind'}:actual=session.replay_memory()
        elif kind=='intervene' and set(op)=={'kind','intervention'}:actual=session.intervene(op['intervention'])
        else:raise ValueError(f'unsupported trace operation at {i}')
        if canonical(actual)!=canonical(expected):raise ValueError(f'semantic replay mismatch at event {i}')
    if canonical(session._states())!=canonical(trace['final']):raise ValueError('serialized final state differs from replay')
    return {'integrity':True,'semantic_replay':True,'events':len(trace['events']),
            'source_matches':source_matches,'final_hash':trace['final_hash'],
            'float_comparison_decimals':12,'authenticity_proven':False}
