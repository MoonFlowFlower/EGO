"""Persistent language-coupled adaptive controller (finite offline mechanism proxy).

The same outcome learner sees real language observations and sandbox transitions.
No controller can execute arbitrary code, modify permissions or label its own
speech as successful. Two-stage language packets are recorded external inputs.
"""
from __future__ import annotations
from copy import deepcopy
import json
import math
from .core import Core, fingerprint, LIMIT_EVENTS
from .protocol import text, obj
from .adaptive_protocol import analyse_packet
from .learning import OutcomeLearner, features, text_vector
from .beliefs import BeliefGraph
from switchlab.runtime import digest, canonical

class AdaptiveCore(Core):
    def __init__(self,seed=41,horizon=240):
        super().__init__(seed,horizon)
        self.learner=OutcomeLearner(seed=73);self.beliefs=BeliefGraph()
        self.state['cognition']={'observations':0,'internal_steps':0,'decisions':[],
            'pending_decision':None,'pending_prediction':None,'working':[0.]*24,
            'last_text':'','last_learning':None,'last_replayed_seen':0,
            'opportunities':[],'issued_conflicts':[],'mode':'adaptive','skills':{},
            'self_outcomes':{},'last_deliberation':None,'legacy_context':None}
        self.metadata['version']='0.3.0'
        self.metadata['contract']='recorded_external_inputs__recompute_plastic_control_and_tools'
        self.metadata['claim']='bounded offline mechanism evidence only; real language benefit unknown'
        self.head=digest(self.metadata)

    def snapshot(self):
        snap=super().snapshot()
        if hasattr(self,'learner'):snap['learner']=self.learner.snapshot();snap['beliefs']=self.beliefs.snapshot()
        return snap

    def _restore_snapshot(self,data):
        super()._restore_snapshot(data)
        self.learner=OutcomeLearner.restore(data['learner']);self.beliefs=BeliefGraph.restore(data['beliefs'])

    @property
    def cog(self):return self.state['cognition']

    def source_texts(self):
        return {o['id']:(o['content'] if isinstance(o['content'],str) else json.dumps(o['content'],ensure_ascii=False,sort_keys=True))
                for o in self.state['observations']}

    def state_features(self):
        active=[g for g in self.state['goals'] if g['status']=='active']
        completed=sum(g['status']=='completed' for g in self.state['goals'])
        caps=list(self.cog['self_outcomes'].values())
        return {'uncertainty':self.lab.agent.model.entropy()/3.,'commitments':min(1.,len(active)/8.),
                'conflicts':min(1.,len(self.beliefs.conflicts())/5.),'budget_used':min(1.,self.state['calls']/100.),
                'knowledge':min(1.,self.learner.active_samples/100.),
                'capability':sum((s['success']+1)/(s['total']+2) for s in caps)/max(1,len(caps)),
                'social':min(1.,sum(c['holder'].startswith('other:') for c in self.beliefs.claims)/20.),
                'progress':completed/max(1,len(self.state['goals']))}

    def _real_observation(self,eid,kind,content,consume_prediction=True):
        rendered=content if isinstance(content,str) else json.dumps(content,ensure_ascii=False,sort_keys=True)
        self.cog['observations']+=1;self.cog['last_text']=rendered[:16000]
        target=text_vector(rendered)
        self.cog['working']=[.75*a+.25*b for a,b in zip(self.cog['working'],target)]
        pending=self.cog['pending_prediction']
        if pending and consume_prediction:
            update=self.learner.learn('transition:'+eid,pending['x'],[0.]*3+target,[0.]*3+[1.]*24)
            update['forecast_event']=pending['decision_id'];update['observation_event']=eid
            update['forecast_mse']=sum((a-b)**2 for a,b in zip(pending['prediction'],target))/24.
            self.cog['last_learning']=update;self.cog['pending_prediction']=None

    def _decision(self,did):
        d=next((d for d in self.cog['decisions'] if d['id']==did),None)
        if not d:raise ValueError('unknown decision ID')
        return d

    def _action_features(self,action,observation_text=None):
        x=features(self.cog['last_text'] if observation_text is None else observation_text,action,self.state_features())
        # Engineered recurrent state; observations, not imagined futures, update it.
        x[:24]=[.8*a+.2*b for a,b in zip(x[:24],self.cog['working'])]
        return x

    def _score_candidates(self,packet):
        rows=[];n=len(packet['candidates']);sf=self.state_features()
        for i,c in enumerate(packet['candidates']):
            action=c['skill']+' '+c['intent'];x=self._action_features(action)
            p=self.learner.predict(x,'adaptive' if self.cog['mode']=='language_order' else self.cog['mode'])
            # Utility dimensions are fixed; conditional consequence estimates are learned.
            # Cold start retains model proposal order. No fabricated personal training history.
            prior=(n-i)/max(1,n)
            strength=p['confidence'] if self.cog['mode']!='language_order' else 0.
            score=(1-strength)*prior+strength*p['utility']
            steps=sum(len(g['steps']) for g in c['goals'])
            score-=.005*steps
            rows.append({'candidate':deepcopy(c),'features':x,'prediction':p,
                         'score':score,'language_rank':i,'engineered_plan_cost':.005*steps})
        return rows

    def internal_ready(self):
        fresh=self.learner.enabled and self.learner.samples and self.learner.seen>self.cog['last_replayed_seen']
        conflicts=[digest(x['claims']) for x in self.beliefs.conflicts()]
        return bool(fresh or any(k not in self.cog['issued_conflicts'] for k in conflicts))

    def pending_reflection(self):
        if any(g['status'] in ('waiting_user','awaiting_feedback') for g in self.state['goals']):return None
        for o in self.cog['opportunities']:
            if o['source_event'] not in self.state['handled']:return o['source_event']
        return super().pending_reflection()

    def _consolidate(self):
        result=self.learner.replay(8)
        self.cog['internal_steps']+=1;self.cog['last_replayed_seen']=self.learner.seen
        return {'kind':'actual_neural_replay','result':result,'new_external_evidence':False}

    def _mutate(self,kind,p,eid):
        if kind=='analyse':
            obj(p,('source','packet'),('source','packet'))
            source=p['source']
            if source not in self.evidence_ids() or source in self.state['handled']:raise ValueError('unknown or handled input')
            if self.cog['pending_decision'] is not None:raise ValueError('finish or discard pending decision first')
            packet=analyse_packet(p['packet'],self.evidence_ids(),{g['id'] for g in self.state['goals']})
            self.beliefs.add(packet['claims'],self.source_texts())
            rows=self._score_candidates(packet)
            chosen=max(rows,key=lambda r:r['score'])
            if len(self.cog['decisions'])>=700:raise ValueError('decision budget reached; export this life')
            did=f'D{len(self.cog["decisions"])+1:05d}'
            d={'id':did,'source':source,'created_event':eid,'summary':packet['summary'],'ranked':rows,
               'selected':deepcopy(chosen),'memories':packet['memories'],'status':'proposed',
               'outcome':None,'goals':[],'source_observation_count':self.cog['observations']}
            self.cog['decisions'].append(d);self.cog['pending_decision']=did
            return {'kind':'local_candidate_selected','decision_id':did,'selected':chosen['candidate']['id'],
                    'scores':[{'id':r['candidate']['id'],'score':r['score'],'utility':r['prediction']['utility']} for r in rows],
                    'weights_sha256':self.learner.net.weight_digest(),'plans_executed':0}
        if kind=='express':
            obj(p,('decision_id','speech'),('decision_id','speech'))
            d=self._decision(p['decision_id'])
            if self.cog['pending_decision']!=d['id'] or d['status']!='proposed' or d['source_observation_count']!=self.cog['observations']:
                raise ValueError('stale or discarded decision')
            c=d['selected']['candidate']
            result=super()._mutate('turn',{'source':d['source'],'packet':{
                'speech':text(p['speech'],'speech',8000,True),'memories':d['memories'],
                'goals':c['goals'],'revisions':c['revisions']}},eid)
            d['status']='expressed';d['expression_event']=eid;d['goals']=result['goals']
            for gid in d['goals']:
                g=self._goal(gid);g['decision_id']=d['id'];g['skill']=c['skill']
                if any(o['source_event']==d['source'] for o in self.cog['opportunities']):g['origin']='grounded_internal_issue'
            self.cog['pending_decision']=None
            self.cog['pending_prediction']={'decision_id':d['id'],'x':d['selected']['features'],
                'prediction':d['selected']['prediction']['next_observation']}
            return {**result,'kind':'selected_intent_expressed','decision_id':d['id'],
                    'pre_action_prediction_recorded':True}
        if kind=='discard_decision':
            obj(p,())
            did=self.cog['pending_decision']
            if did:self._decision(did)['status']='discarded'
            self.cog['pending_decision']=None
            return {'kind':'uncommitted_decision_discarded','decision_id':did}
        if kind=='outcome':
            obj(p,('decision_id','task','constraint','understanding','note'),('decision_id',))
            d=self._decision(p['decision_id'])
            if d['status']!='expressed' or (d['outcome'] is not None and not d['outcome']['withdrawn']):raise ValueError('only one active explicit outcome per expressed decision')
            y=[];mask=[]
            for k in ('task','constraint','understanding'):
                v=p.get(k)
                if v is not None and (type(v) not in (float,int) or not math.isfinite(v) or not 0<=v<=1):raise ValueError('outcomes must be null or numbers in 0..1')
                y.append(0. if v is None else float(v));mask.append(0. if v is None else 1.)
            if not any(mask):raise ValueError('at least one observed outcome is required; liking is not a task label')
            note=text(p.get('note',''),'outcome note',3000,True)
            sid='outcome:'+eid
            update=self.learner.learn(sid,d['selected']['features'],y+[0.]*24,mask+[0.]*24)
            if d['outcome']:d.setdefault('outcome_history',[]).append(deepcopy(d['outcome']))
            d['outcome']={'source':eid,'sample_id':sid,'values':y,'mask':mask,'note':note,'withdrawn':False,
                          'label_source':'explicit_user_report_not_independent_truth','learning_enabled_when_observed':self.learner.enabled}
            self._record_capability(d['selected']['candidate']['skill'],y,mask)
            self._observation(eid,'explicit_decision_outcome',d['outcome'])
            self._real_observation(eid,'explicit_decision_outcome',d['outcome'],False)
            self.cog['last_learning']=update
            return {'kind':'confirmed_outcome_learned','decision_id':d['id'],'learning':update}
        if kind=='withdraw_outcome':
            obj(p,('decision_id',),('decision_id',));d=self._decision(p['decision_id']);f=d['outcome']
            if not f or f['withdrawn']:raise ValueError('no active explicit outcome to withdraw')
            f['withdrawn']=True;r=self.learner.retract(f['sample_id']);self._rebuild_capabilities()
            correction={'decision_id':d['id'],'withdrawn_source':f['source'],'new_label':False}
            self._observation(eid,'user_outcome_withdrawal',correction)
            self._real_observation(eid,'user_outcome_withdrawal',correction,False)
            self.cog['last_replayed_seen']=self.learner.seen
            return {'kind':'outcome_withdrawn','result':r}
        if kind=='belief_control':
            obj(p,('claim_id','action','note'),('claim_id','action'))
            self.beliefs.resolve(p['claim_id'],p['action'],eid)
            note=text(p.get('note',''),'belief correction',1600,True)
            observation={'claim_id':p['claim_id'],'action':p['action'],'note':note}
            self._observation(eid,'user_claim_correction',observation);self._real_observation(eid,'correction',observation)
            return {'kind':'claim_report_corrected','world_truth_inferred':False}
        if kind=='selection_mode':
            obj(p,('mode',),('mode',))
            if p['mode'] not in ('adaptive','neural','similarity','language_order'):raise ValueError('unknown selection mode')
            self.cog['mode']=p['mode'];return {'kind':'selection_mode','mode':p['mode']}
        if kind=='deliberate':
            obj(p,())
            replay=None;opportunities=[]
            if self.learner.enabled and self.learner.samples and self.learner.seen>self.cog['last_replayed_seen']:
                replay=self.learner.replay(8);self.cog['last_replayed_seen']=self.learner.seen
            new=[x for x in self.beliefs.conflicts() if digest(x['claims']) not in self.cog['issued_conflicts']]
            if new:
                # A structural inconsistency is an engineered trigger, not an invented emotion.
                item=new[0];self.cog['issued_conflicts'].append(digest(item['claims']))
                opportunity={'kind':'possible_belief_conflict_or_change','source_event':eid,
                    'issue':deepcopy(item),'new_external_evidence':False,'origin':'computed_from_source_separated_claims'}
                self.cog['opportunities'].append(opportunity);opportunities.append(opportunity)
                self._observation(eid,'derived_internal_issue',opportunity)
            did=bool(replay or opportunities)
            if did:self.cog['internal_steps']+=1
            result={'kind':'internal_computation' if did else 'sleep','replay':replay,'opportunities':opportunities,
                    'new_external_evidence':False,'world_advanced':False}
            self.cog['last_deliberation']=result
            return result
        if kind=='consolidate':
            obj(p,());r=self.learner.replay(8);self.cog['internal_steps']+=1
            self.cog['last_replayed_seen']=self.learner.seen
            return {'kind':'actual_neural_replay','result':r,'new_external_evidence':False}
        if kind=='legacy_context':
            obj(p,('messages','memories','goals','old_head','source_verified'),('messages','memories','goals','old_head','source_verified'))
            if self.cog['legacy_context'] is not None:raise ValueError('legacy import only once')
            if p['source_verified'] is not True:raise ValueError('legacy source verification required')
            self.cog['legacy_context']=deepcopy(p)
            self._observation(eid,'legacy_import_not_new_training_evidence',{'archive_head':p['old_head'],'note':'Historical context only; old IDs are not current event IDs.'})
            return {'kind':'legacy_context_preserved','neural_history_imported':False,'legacy_goals_auto_enabled':False}
        # Before a real sandbox action record a forecast using only public observation.
        physical=kind=='lab' and p.get('action')!='think'
        if kind=='work' and isinstance(p.get('job'),dict):
            physical=p['job'].get('step',{}).get('tool') in ('lab_step','lab_action')
        lab_x=None
        if physical:
            actual_action=p.get('action') if kind=='lab' else p['job']['step'].get('action','auto')
            lab_x=self._action_features(str(actual_action),json.dumps(self.lab.world.observe(),sort_keys=True))
        if kind=='message' and self.cog['pending_decision']:
            self._decision(self.cog['pending_decision'])['status']='discarded';self.cog['pending_decision']=None
        result=super()._mutate(kind,p,eid)
        if kind=='message':self._real_observation(eid,'message',p['text'])
        elif kind=='adaptation':self.learner.enabled=p['enabled']
        elif kind=='feedback':
            self._real_observation(eid,'feedback',result,False)
            if p['kind']!='style':
                a=self._artifact(p['artifact_id']);g=self._goal(a['goal_id']);did=g.get('decision_id')
                if did:
                    d=self._decision(did);v=float(p['kind']=='criteria_met')
                    update=self.learner.learn('artifact:'+eid,d['selected']['features'],[v,v,0.]+[0.]*24,[1.,1.,0.]+[0.]*24)
                    self.cog['last_learning']=update;self._record_capability(g.get('skill','draft'),[v,v,0.],[1.,1.,0.])
                    a['evaluation']['learning_enabled_when_observed']=self.learner.enabled
                    if v and self.learner.enabled:
                        self.cog['skills'][g.get('skill','draft')]={'steps':deepcopy(g['steps']),
                            'success_condition':g['success'],'basis':[eid],'verification':'one_user_reported_success_not_general_skill_proof'}
        elif kind=='lab' and physical:
            target=text_vector(json.dumps(result,ensure_ascii=False,sort_keys=True))
            self.cog['last_learning']=self.learner.learn('lab:'+eid,lab_x,[0.]*3+target,[0.]*3+[1.]*24)
            self._real_observation(eid,'lab',result,False)
        elif kind=='work':
            tool=p['job']['step']['tool']
            if physical:
                observed=result['result']
                target=text_vector(json.dumps(observed,ensure_ascii=False,sort_keys=True))
                self.cog['last_learning']=self.learner.learn('lab:'+eid,lab_x,[0.]*3+target,[0.]*3+[1.]*24)
            if tool in ('inspect','lab_think','consolidate'):
                # Internal computations are not fresh observations of the external world.
                if tool!='consolidate':self.cog['internal_steps']+=1
            elif result.get('kind') in ('artifact_written','tool_executed'):
                self._real_observation(eid,'actual_tool_result',result,False)
        return result

    def _record_capability(self,skill,values,mask,force=False):
        if mask[0] and (self.learner.enabled or force):
            s=self.cog['self_outcomes'].setdefault(skill,{'success':0.,'total':0})
            s['success']+=values[0];s['total']+=1

    def _rebuild_capabilities(self):
        self.cog['self_outcomes']={}
        for d in self.cog['decisions']:
            f=d.get('outcome')
            if f and not f['withdrawn'] and f.get('learning_enabled_when_observed',True):self._record_capability(d['selected']['candidate']['skill'],f['values'],f['mask'],True)
        # Artifact evaluations are separate externally confirmed outcomes.
        for a in self.state['artifacts']:
            f=a.get('evaluation');g=self._goal(a['goal_id'])
            if f and f.get('learning_enabled_when_observed',True):self._record_capability(g.get('skill','draft'),[float(f['kind']=='criteria_met'),0,0],[1,0,0],True)

    def context(self,goal_id=None):
        ctx=super().context(goal_id)
        ctx['cognitive_state']={k:deepcopy(self.cog[k]) for k in ('observations','internal_steps','working','last_learning','self_outcomes','skills','mode')}
        ctx['cognitive_state']['learner']=self.learner.summary()
        ctx['claims']=self.beliefs.retrieve(self.cog['last_text'])
        ctx['withdrawn_outcome_sources']=[f['source'] for d in self.cog['decisions']
            for f in ([d['outcome']] if d.get('outcome') else [])+d.get('outcome_history',[]) if f['withdrawn']]
        ctx['open_claim_conflicts']=self.beliefs.conflicts()[:8]
        ctx['internal_opportunities']=deepcopy(self.cog['opportunities'][-6:])
        ctx['recent_decisions']=[{'id':d['id'],'intent':d['selected']['candidate']['intent'],'status':d['status'],
                                  'expected':d['selected']['candidate']['expected']} for d in self.cog['decisions'][-4:]]
        ctx['model_boundary']='Finite lexical feature predictions and source-separated reports; not a verified unified social world model.'
        if self.cog['legacy_context']:
            old=self.cog['legacy_context'];ctx['legacy_context']={k:old[k] for k in ('messages','memories','goals')}
            ctx['legacy_context']['contract']='Old IDs are not current IDs. Do not revise parked old goals; use new goals grounded in the current user request. No old outcomes are new training evidence.'
        return ctx

    def view(self):
        v=super().view();v['version']='0.3.0'
        v['cognition']={k:deepcopy(self.cog[k]) for k in ('observations','internal_steps','pending_decision','last_learning','opportunities','self_outcomes','skills','mode','last_deliberation')}
        v['cognition']['learner']=self.learner.summary()
        v['cognition']['decisions']=[{k:deepcopy(d[k]) for k in ('id','source','status','summary','selected','ranked','outcome','goals')} for d in self.cog['decisions'][-12:]]
        v['beliefs']=self.beliefs.snapshot();v['belief_conflicts']=self.beliefs.conflicts()
        v['internal_ready']=self.internal_ready()
        return v

    def checkpoint(self):
        s=self.snapshot()
        return {'schema':'switchlab.studio.v3','metadata':deepcopy(self.metadata),'events':deepcopy(self.events),
                'head':self.head,**s}

    @classmethod
    def restore(cls,data,check_source=True):
        obj(data,('schema','metadata','events','head','state','lab','learner','beliefs'),
            ('schema','metadata','events','head','state','lab','learner','beliefs'))
        if data['schema']!='switchlab.studio.v3':raise ValueError('not a v0.3 checkpoint; use explicit legacy migration')
        if not isinstance(data['events'],list) or len(data['events'])>LIMIT_EVENTS:raise ValueError('event budget')
        if check_source and data['metadata']['source_sha256']!=fingerprint():raise ValueError('source fingerprint mismatch; preserve matching package')
        c=cls(**data['metadata']['config']);c.metadata=deepcopy(data['metadata']);c.head=digest(c.metadata)
        for expected in data['events']:
            actual=c.apply(expected['kind'],expected['payload'])
            if canonical(actual)!=canonical(expected):raise ValueError('recorded-input replay mismatch at '+str(expected.get('id')))
        if c.head!=data['head'] or canonical(c.snapshot())!=canonical({k:data[k] for k in ('state','lab','learner','beliefs')}):
            raise ValueError('final adaptive state differs from recomputed state')
        return c
