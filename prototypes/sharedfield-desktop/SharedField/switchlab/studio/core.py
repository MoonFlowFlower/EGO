"""Deterministic persistent core. Recorded language outputs are EXOGENOUS inputs.

Replay verifies downstream state transitions, not model authorship, truth of text,
or that the same remote model would generate the same output again.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import math
from switchlab.runtime import Session, digest, canonical
from switchlab.world import Config, World, ACTIONS
from switchlab.agent import Agent, AgentConfig
from .protocol import text, obj, turn_packet, STRATEGIES

ROOT = Path(__file__).resolve().parents[2]
LIMIT_EVENTS = 5000
LIMIT_GOALS = 120
LIMIT_ARTIFACTS = 250


def fingerprint():
    paths = [p for p in ROOT.rglob('*') if p.is_file() and p.suffix in ('.py','.js','.css','.html')
             and ('switchlab' in p.relative_to(ROOT).parts or p.name == 'run.py')]
    return digest([(p.relative_to(ROOT).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
                   for p in sorted(paths)])


class Core:
    def __init__(self, seed=41, horizon=240):
        self.config = {'seed':seed,'horizon':horizon}
        self.lab = Session(Config(seed=seed,horizon=horizon), AgentConfig(planner='two_step'))
        self.state = {'messages':[], 'memories':[], 'goals':[], 'artifacts':[], 'observations':[],
                      'handled':[], 'consolidations':[], 'adaptation':True,
                      'strategy_stats':{s:{'alpha':1.0,'beta':1.0,'evaluations':0} for s in STRATEGIES},
                      'calls':0,'usage':{'input_tokens':0,'output_tokens':0}, 'last_result':None}
        self.events = []
        self.metadata = {'source_sha256':fingerprint(), 'config':deepcopy(self.config),
                         'contract':'recorded_language_inputs__deterministic_downstream_replay',
                         'claim':'bounded local engineering trace; mechanism superiority NOT established'}
        self.head = digest(self.metadata)

    def snapshot(self):
        return {'state':deepcopy(self.state),'lab':self.lab._states()}

    def _restore_snapshot(self, data):
        self.state = deepcopy(data['state'])
        self.lab.world = World.from_snapshot(data['lab']['world'])
        self.lab.agent = Agent.from_snapshot(data['lab']['agent'])
        # Studio's own event log is authoritative for interleaved lab controls.
        self.lab.events = []

    def apply(self, kind, payload):
        if len(self.events) >= LIMIT_EVENTS: raise ValueError('lifecycle event budget exhausted; export this life')
        if not isinstance(payload, dict): raise ValueError('operation payload must be an object')
        original = self.snapshot()
        eid = f'E{len(self.events)+1:06d}'
        try:
            result = self._mutate(kind, deepcopy(payload), eid)
            self.state['last_result'] = deepcopy(result)
        except Exception:
            self._restore_snapshot(original)
            raise
        event = {'id':eid,'kind':kind,'payload':deepcopy(payload),'result':deepcopy(result),
                 'previous':self.head,'state_sha256':digest(self.snapshot())}
        event['hash'] = digest(event)
        self.events.append(event); self.head = event['hash']
        return deepcopy(event)

    def evidence_ids(self):
        return {o['id'] for o in self.state['observations']} | {m['id'] for m in self.state['messages'] if m['role']=='user'}

    def _observation(self, eid, kind, content):
        self.state['observations'].append({'id':eid,'kind':kind,'content':deepcopy(content)})

    def _speech(self, eid, content, kind='dialogue'):
        if content:
            self.state['messages'].append({'id':eid,'role':'assistant','text':content,'kind':kind})

    def _goal(self, gid):
        for g in self.state['goals']:
            if g['id'] == gid: return g
        raise ValueError('unknown goal ID')

    def _artifact(self, aid):
        for a in self.state['artifacts']:
            if a['id'] == aid: return a
        raise ValueError('unknown artifact ID')

    def strategy_scores(self):
        return {s:v['alpha']/(v['alpha']+v['beta']) for s,v in self.state['strategy_stats'].items()}

    def choose_strategy(self):
        scores = self.strategy_scores()
        # Finite engineered exploration tie-break, adapted by observed task ratings.
        return max(STRATEGIES, key=lambda s:(scores[s],-self.state['strategy_stats'][s]['evaluations'],
                                             -STRATEGIES.index(s)))

    def pending_turn(self):
        handled = set(self.state['handled'])
        # Conversations take precedence over optional reflections on tool observations.
        for m in self.state['messages']:
            if m['role']=='user' and m['id'] not in handled: return m['id']
        return None

    def pending_reflection(self):
        # Engineering prior for attention routing, NOT learned motivation.
        # Compare observation-conditioned belief BEFORE physical drift; random
        # uninformative outcomes must not acquire information value from time passing.
        candidates=[]
        for o in self.state['observations']:
            r=o['content']
            if isinstance(r,dict) and r.get('kind')=='actual_lab_transition':
                if r.get('information_gain_bits',0)>.08 and r.get('surprise_nats',0)>.8:
                    candidates.append(o['id'])
        if not candidates:return None
        latest=candidates[-1]
        return latest if latest not in self.state['handled'] else None

    def next_work(self):
        choices = [g for g in self.state['goals'] if g['status']=='active' and g['cursor']<len(g['steps'])]
        if not choices: return None
        # Commitment persistence, then corrections before untouched goals. No idle score.
        g = max(choices, key=lambda x:(x['attempts']>0,x['revision'],-int(x['id'][1:])))
        return {'goal_id':g['id'],'revision':g['revision'],'cursor':g['cursor'],
                'step':deepcopy(g['steps'][g['cursor']]),'strategy':self.choose_strategy()}

    def _validate_job(self, j):
        obj(j, ('goal_id','revision','cursor','step','strategy'), ('goal_id','revision','cursor','step','strategy'))
        g = self._goal(j['goal_id'])
        if g['status']!='active' or g['revision']!=j['revision'] or g['cursor']!=j['cursor']:
            raise ValueError('stale, cancelled, paused or already executed work')
        if j['cursor']>=len(g['steps']) or g['steps'][j['cursor']]!=j['step'] or j['strategy'] not in STRATEGIES:
            raise ValueError('job does not match current finite plan')
        return g

    def _advance(self, g):
        g['cursor'] += 1
        if g['cursor'] >= len(g['steps']): g['status']='awaiting_feedback'

    def _lab(self, action):
        if action == 'think':
            result = self.lab.agent.think(self.lab.world.observe())
            return {'kind':'internal_plan','action':result['action'],'score':result.get('score'),
                    'nodes':result['nodes'],'belief_changed':False,'world_advanced':False}
        prior_model=self.lab.agent.model.copy()
        if action == 'auto':
            e = self.lab.step()
            tr = e['result']['transition']; learning = e['result']['learning']
            predicted = e['result']['decision']['prediction']
        else:
            if action not in ACTIONS: raise ValueError('unauthorized sandbox action')
            predicted = dict(self.lab.agent.model.predict(action))
            tr = self.lab.world.step(action)
            learning = self.lab.agent.learn(tr)
            self.lab.agent.workspace = None
            self.lab.agent.last_decision = {'action':action,'origin':'authorized_studio_experiment',
                                            'prediction':predicted,'nodes':0}
        conditioned=prior_model.condition(tr['action'],tr['outcome'],advance=False).belief
        gain=sum(q*math.log2(q/p) for q,p in zip(conditioned,prior_model.belief) if q>0 and p>0)
        return {'kind':'actual_lab_transition','transition':tr,'prediction':predicted,
                'information_gain_bits':max(0.,gain),
                'surprise_nats':learning['surprise_nats'], 'belief_before':learning['model_before'],
                'belief_after':learning['model_after']}

    def _consolidate(self):
        # Rebuild statistics from unique explicit task evaluations; no new evidence.
        rebuilt = {s:{'alpha':1.0,'beta':1.0,'evaluations':0} for s in STRATEGIES}
        for a in self.state['artifacts']:
            f = a.get('evaluation')
            if f and f.get('counted'):
                stat = rebuilt[a['strategy']]
                stat['alpha' if f['kind']=='criteria_met' else 'beta'] += 1
                stat['evaluations'] += 1
        before = deepcopy(self.state['strategy_stats'])
        self.state['strategy_stats'] = rebuilt
        result = {'kind':'exact_outcome_statistic_reconstruction','same_statistics':before==rebuilt,
                  'episodes_used':sum(x['evaluations'] for x in rebuilt.values()),
                  'memory_items':len(self.state['memories']),
                  'new_external_evidence':False,'neural_consolidation':False}
        self.state['consolidations'].append(result)
        return result

    def _mutate(self, kind, p, eid):
        if kind == 'message':
            obj(p, ('text',), ('text',)); s=text(p['text'],'message',6000)
            self.state['messages'].append({'id':eid,'role':'user','text':s,'kind':'user_input'})
            self._observation(eid,'user_statement',s)
            return {'kind':'message_received','evidence_id':eid}
        if kind == 'turn':
            obj(p, ('source','packet'), ('source','packet'))
            if p['source'] not in self.evidence_ids() or p['source'] in self.state['handled']:
                raise ValueError('unknown or already processed source event')
            packet = turn_packet(p['packet'], self.evidence_ids(), {g['id'] for g in self.state['goals']})
            if len(self.state['goals'])+len(packet['goals'])>LIMIT_GOALS: raise ValueError('goal storage budget reached')
            self.state['handled'].append(p['source'])
            self._speech(eid, packet['speech'])
            new_goals=[]; new_memories=[]
            for m in packet['memories']:
                # Existing copies gain source pointers, not Bayesian evidence weight.
                same = next((x for x in self.state['memories'] if x['key']==m['key'] and x['text']==m['text'] and x['kind']==m['kind']),None)
                if same:
                    same['basis']=list(dict.fromkeys(same['basis']+m['basis'])); continue
                conflict = [x for x in self.state['memories'] if x['key']==m['key'] and x['text']!=m['text']]
                for x in conflict: x['disputed']=True
                m.update({'id':f'M{len(self.state["memories"])+1:04d}','verification':'unverified',
                          'disputed':bool(conflict),'created_event':eid})
                self.state['memories'].append(m); new_memories.append(m['id'])
            for g in packet['goals']:
                existing = next((x for x in self.state['goals'] if x['title'].strip().casefold()==g['title'].strip().casefold()
                                 and x['status'] not in ('completed','cancelled')),None)
                if existing: continue
                g.update({'id':f'G{len(self.state["goals"])+1:04d}', 'status':'active','cursor':0,
                          'revision':1,'attempts':0,'created_event':eid,'feedback':[],
                          'origin':'language_proposal_grounded_in_event','last_artifact':None})
                self.state['goals'].append(g); new_goals.append(g['id'])
            for r in packet['revisions']:
                g=self._goal(r['goal_id'])
                if r['action']=='revise':
                    g['steps']=r['steps']; g['cursor']=0; g['status']='active'
                elif r['action']=='cancel': g['status']='cancelled'
                elif r['action']=='pause': g['status']='paused'
                else:
                    if g['cursor']>=len(g['steps']): g['cursor']=max(0,len(g['steps'])-1)
                    g['status']='active'
                g['revision']+=1;g['feedback'].append({'kind':'plan_revision','text':r['reason'],'basis':r['basis']})
            return {'kind':'language_candidates_committed','goals':new_goals,'memories':new_memories,
                    'tool_actions_executed':0,'speech_is_execution_proof':False}
        if kind == 'work':
            obj(p, ('job','content'), ('job',));j=p['job'];g=self._validate_job(j)
            tool=j['step']['tool'];g['attempts']+=1
            if tool in ('draft','ask'):
                content=text(p.get('content'),'work content',20000)
                if tool=='ask':
                    g['status']='waiting_user'
                    self._speech(eid,content,'question')
                    return {'kind':'question_asked','goal_id':g['id'],'waiting':True}
                if len(self.state['artifacts'])>=LIMIT_ARTIFACTS: raise ValueError('artifact budget reached')
                a={'id':f'A{len(self.state["artifacts"])+1:04d}', 'goal_id':g['id'],'title':g['title'],
                   'content':content,'content_sha256':hashlib.sha256(content.encode('utf-8')).hexdigest(),
                   'strategy':j['strategy'],'parent':g['last_artifact'],'created_event':eid,'evaluation':None,
                   'claim':'draft_written_not_real_world_outcome'}
                self.state['artifacts'].append(a);g['last_artifact']=a['id'];g['cursor']+=1;g['status']='awaiting_feedback'
                self._speech(eid,f'草稿「{g["title"]}」已写入本地工作区（{a["id"]}）。这是待验收的产出，不代表现实任务已完成。','actual_result')
                self._observation(eid,'artifact_written',{'artifact_id':a['id'],'goal_id':g['id'],'sha256':a['content_sha256']})
                return {'kind':'artifact_written','artifact_id':a['id'],'goal_id':g['id'],'awaiting_feedback':True}
            if 'content' in p and p['content']: raise ValueError('non-language tool does not accept invented results')
            if tool=='inspect': result={'kind':'workspace_inspected','goals':len(self.state['goals']),
                                       'artifacts':len(self.state['artifacts']),'memory_items':len(self.state['memories'])}
            elif tool=='lab_step': result=self._lab('auto')
            elif tool=='lab_action': result=self._lab(j['step']['action'])
            elif tool=='lab_think': result=self._lab('think')
            elif tool=='consolidate': result=self._consolidate()
            else: raise ValueError('unknown internal tool')
            self._advance(g);self._observation(eid,'tool_result',result)
            return {'kind':'tool_executed','goal_id':g['id'],'tool':tool,'result':result}
        if kind == 'feedback':
            obj(p, ('artifact_id','kind','text'), ('artifact_id','kind','text'))
            a=self._artifact(p['artifact_id']);g=self._goal(a['goal_id'])
            note=text(p['text'],'feedback',3000,True)
            if p['kind'] not in ('criteria_met','criteria_failed','style'): raise ValueError('unknown feedback channel')
            f={'kind':p['kind'],'text':note,'source':eid,'counted':False}
            if p['kind']=='style':
                self.state['memories'].append({'id':f'M{len(self.state["memories"])+1:04d}','kind':'preference',
                     'key':'表达偏好','text':note or '用户提出表达偏好','basis':[eid],
                     'verification':'user_reported_preference','disputed':False,'created_event':eid})
            else:
                if a['evaluation'] is not None: raise ValueError('this artifact already has a task evaluation')
                f['counted']=bool(self.state['adaptation']);a['evaluation']=deepcopy(f)
                if f['counted']:
                    s=self.state['strategy_stats'][a['strategy']]
                    s['alpha' if p['kind']=='criteria_met' else 'beta']+=1;s['evaluations']+=1
                # Feedback about an old draft must not reopen or complete a newer goal revision.
                if g['last_artifact']==a['id'] and g['status'] not in ('cancelled','paused','completed'):
                    if p['kind']=='criteria_met':g['status']='active' if g['cursor']<len(g['steps']) else 'completed'
                    else:
                        g['cursor']=max(0,g['cursor']-1);g['status']='active';g['revision']+=1
            g['feedback'].append(deepcopy(f));self._observation(eid,'user_evaluation',{'artifact_id':a['id'],**f})
            return {'kind':'feedback_applied','channel':p['kind'],'capability_updated':f['counted'],
                    'lab_belief_changed':False,'goal_status':g['status']}
        if kind=='goal_control':
            obj(p, ('goal_id','action'), ('goal_id','action'));g=self._goal(p['goal_id'])
            a=p['action']
            if a not in ('cancel','pause','resume','complete'): raise ValueError('unknown goal control')
            if a=='resume':
                if g['cursor']>=len(g['steps']):g['cursor']=max(0,len(g['steps'])-1)
                g['status']='active'
            else:g['status']={'cancel':'cancelled','pause':'paused','complete':'completed'}[a]
            g['revision']+=1
            return {'kind':'goal_control_applied','goal_id':g['id'],'status':g['status']}
        if kind=='lab':
            obj(p, ('action',), ('action',));result=self._lab(p['action'])
            self._observation(eid,'tool_result',result);return result
        if kind=='intervene':
            obj(p, ('kind',), ('kind',));self.lab.world.intervene(p['kind'])
            # Deliberately no evidence observation: candidate must discover the intervention.
            return {'kind':'operator_intervention_applied','candidate_informed':False}
        if kind=='consolidate':
            obj(p, ());result=self._consolidate();self._observation(eid,'internal_reconstruction',result);return result
        if kind=='adaptation':
            obj(p, ('enabled',), ('enabled',))
            if type(p['enabled']) is not bool:raise ValueError('enabled must be boolean')
            self.state['adaptation']=p['enabled'];return {'kind':'adaptation_switch','enabled':p['enabled']}
        if kind=='usage':
            obj(p, ('usage','model'), ('usage',))
            if not isinstance(p['usage'],dict):raise ValueError('usage must be object')
            for key in ('input_tokens','output_tokens'):
                n=p['usage'].get(key,0)
                if type(n) is not int or not 0<=n<=1000000:raise ValueError('invalid usage')
                self.state['usage'][key]+=n
            return {'kind':'provider_reported_usage','usage':p['usage'],'model':p.get('model','unknown')}
        if kind=='call':
            obj(p, ('phase','usage','model'), ('phase',))
            self.state['calls']+=1
            u=p.get('usage',{})
            if not isinstance(u,dict):raise ValueError('usage must be object')
            for field in ('input_tokens','output_tokens'):
                n=u.get(field,0)
                if type(n) is not int or not 0<=n<=1000000:raise ValueError('invalid token usage')
                self.state['usage'][field]+=n
            return {'kind':'language_call_record','phase':text(p['phase'],'phase',80),
                    'model':text(p.get('model','unknown'),'model',200),'usage':u}
        raise ValueError('unknown core operation')

    def _lab_public(self):
        return {'observation':self.lab.world.observe(),'belief':self.lab.agent.model.marginals(),
                'entropy_bits':self.lab.agent.model.entropy(),'last_learning':deepcopy(self.lab.agent.last_learning),
                'last_decision':deepcopy(self.lab.agent.last_decision),'memory_events':len(self.lab.agent.memory),
                'world_done':self.lab.world.observe()['tick']>=self.lab.world.config.horizon,
                'scope':'finite known model family; estimates are not verified world truth'}

    def context(self, goal_id=None):
        active=[g for g in self.state['goals'] if g['status'] not in ('completed','cancelled')]
        g=self._goal(goal_id) if goal_id else None
        # Bounded working set, not the whole growing transcript. Sources and conflicts retained.
        memories=self.state['memories'][-24:]
        goal_artifacts=[a for a in self.state['artifacts'] if g and a['goal_id']==g['id']]
        artifacts=goal_artifacts[-2:] if g else self.state['artifacts'][-2:]
        artifact_view=[{k:(v[:6500] if k=='content' else v) for k,v in a.items()} for a in artifacts]
        pinned=set(r for goal in ([g] if g else active[:12]) for r in goal['basis'])
        if g:
            for f in g['feedback']: pinned.update(f.get('basis',[]))
        origins=[deepcopy(o) for o in self.state['observations'] if o['id'] in pinned]
        return {'goal_origin_observations':origins,'conversation':deepcopy(self.state['messages'][-14:]), 'memory':deepcopy(memories),
                'goals':deepcopy(active[:12]),'selected_goal':deepcopy(g), 'recent_artifacts':deepcopy(artifact_view),
                'observations':deepcopy(self.state['observations'][-12:]),'lab':self._lab_public(),
                'task_strategy_estimates':self.strategy_scores(),
                'self_capabilities':{'can':['local_draft','local_memory','toy_experiment','bounded_planning'],
                                     'cannot':['browse_web','operate_computer','send_messages','execute_code'],
                                     'task_estimates':'explicit user criteria feedback, not independent objective truth'},
                'memory_contract':{'raw_events_retained':True,'context_is_bounded':True,
                                   'old_content_may_require_user_restatement':True}}

    def view(self):
        return {'version':'0.2.0','messages':deepcopy(self.state['messages'][-120:]),
                'memories':deepcopy(self.state['memories']), 'goals':deepcopy(self.state['goals']),
                'artifacts':deepcopy(self.state['artifacts']), 'lab':self._lab_public(),
                'strategy_scores':self.strategy_scores(),'strategy_stats':deepcopy(self.state['strategy_stats']),
                'adaptation':self.state['adaptation'],'calls':self.state['calls'],'usage':deepcopy(self.state['usage']),
                'events':[{'id':e['id'],'kind':e['kind'],'result':deepcopy(e['result'])} for e in self.events[-20:]],
                'event_count':len(self.events),'head':self.head,'last_result':deepcopy(self.state['last_result'])}

    def checkpoint(self):
        snap=self.snapshot()
        return {'schema':'switchlab.studio.v2','metadata':deepcopy(self.metadata),
                'events':deepcopy(self.events),'head':self.head,'state':snap['state'],'lab':snap['lab']}

    @classmethod
    def restore(cls, data, check_source=True):
        obj(data, ('schema','metadata','events','head','state','lab'), ('schema','metadata','events','head','state','lab'))
        if data['schema']!='switchlab.studio.v2':raise ValueError('not a Studio v0.2 checkpoint')
        if not isinstance(data['events'],list) or len(data['events'])>LIMIT_EVENTS:raise ValueError('event bound exceeded')
        c=cls(**data['metadata']['config'])
        if check_source and data['metadata']['source_sha256']!=fingerprint():raise ValueError('source fingerprint mismatch; preserve the old package with its data')
        c.metadata=deepcopy(data['metadata']);c.head=digest(c.metadata)
        for expected in data['events']:
            actual=c.apply(expected['kind'],expected['payload'])
            if canonical(actual)!=canonical(expected):raise ValueError(f'recorded-input replay mismatch at {expected.get("id")}')
        if c.head!=data['head'] or canonical(c.snapshot())!=canonical({'state':data['state'],'lab':data['lab']}):
            raise ValueError('final persisted state differs from recomputed state')
        return c
