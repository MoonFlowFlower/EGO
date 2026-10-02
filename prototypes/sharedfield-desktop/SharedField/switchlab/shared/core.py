"""Atomic event-sourced shared-world cognition; report snapshots precede language.

The world is private. Only public observations and source-tagged reports enter
Mind or remote context. Recorded-input replay checks computation, not model
truth, authorship, phenomenology, or general intelligence.
"""
from __future__ import annotations
from copy import deepcopy
import math
from ..studio.protocol import obj,text,arr
from ..studio.core import fingerprint,LIMIT_EVENTS
from .evidence import digest,canonical
from .world import World,KIND_NAMES
from .mind import Mind,MODES
from .grounding import contract,guard_speech

DOMAINS={'mood':{'happy','sad','frustrated','tired','curious','calm','unknown'},
         'interest':set(KIND_NAMES),'signal':{'shared_enjoyment','help_offered','misunderstanding'}}
ACTION_NAMES={'move':'前往','survey':'调查','scan':'观察路况','calibrate':'校准自己的工具','rest':'休整',
              'repair':'维护工具','sleep':'暂时休息','wait_partner':'等你准备好'}

class SharedCore:
    def __init__(self,seed=41,horizon=600):
        self.config={'seed':seed,'horizon':horizon};self.world=World(seed,horizon);self.mind=Mind()
        self.mind.refresh(self.world.observe('agent'));self.mind.plan()
        self.state={'messages':[],'observations':[],'handled':[],'calls':0,'usage':{'input_tokens':0,'output_tokens':0},
                    'last_result':None,'pending':None,'reports':[],'revision':0,'name':'澄','last_narrated':None,
                    'history_context':None}
        self.events=[];self.origin=None;self.metadata={'source_sha256':fingerprint(),'config':deepcopy(self.config),'version':'0.5.0',
            'contract':'shared-v5 finite numeric JSON normalization; 12 decimal comparison; language outputs exogenous',
            'claim_ceiling':'bounded offline mechanism evidence under a specified environment/trace/replay contract'}
        self.head=digest(self.metadata)

    def snapshot(self):return {'state':deepcopy(self.state),'world':self.world.snapshot(),'mind':self.mind.snapshot()}
    def _load(self,s):
        self.state=deepcopy(s['state']);self.world=World.restore(s['world']);self.mind=Mind.restore(s['mind'])

    def apply(self,kind,payload):
        if len(self.events)>=LIMIT_EVENTS:raise ValueError('生命周期事件上限5000；请导出后保留旧目录再开始新个体。')
        if not isinstance(payload,dict):raise ValueError('payload must be object')
        before=self.snapshot();eid='E%06d'%(len(self.events)+1+self.metadata.get('event_offset',0))
        try:
            r=self._mutate(kind,deepcopy(payload),eid);self.state['last_result']=deepcopy(r)
            if kind not in ('expression','call','usage') and self.mind.focus:
                for message in self.state['messages']:
                    receipt=message.get('intention')
                    if receipt and receipt['status']=='selected_not_executed' and receipt['action']!=self.mind.focus['action']:
                        receipt.update(status='revised_on_new_observation',revised_by=eid,
                                       new_action=deepcopy(self.mind.focus['action']))
        except Exception:self._load(before);raise
        e={'id':eid,'kind':kind,'payload':deepcopy(payload),'result':deepcopy(r),'previous':self.head,
           'state_sha256':digest(self.snapshot())};e['hash']=digest(e);self.events.append(e);self.head=e['hash']
        return deepcopy(e)

    def _change(self,preserve_pending=False):
        self.state['revision']+=1
        if not preserve_pending:self.state['pending']=None

    def _report(self,source):
        report={'id':'S%05d'%(len(self.state['reports'])+1),'source':source,'revision':self.state['revision'],
                'report':self.mind.report(),'world_tick':self.world.tick,'observation':self.world.observe('agent')}
        report['hash']=digest(report);self.state['reports'].append(report);return deepcopy(report)

    def pending_turn(self):
        return next((m['id'] for m in reversed(self.state['messages']) if m['role']=='user' and m['id'] not in self.state['handled']),None)

    def _source(self,eid):
        m=next((m for m in self.state['messages'] if m['id']==eid and m['role']=='user'),None)
        if not m:raise ValueError('unknown user source')
        return m['text']

    def _interpret(self,source,packet):
        obj(packet,('reports','request'),('reports','request'));raw=self._source(source)
        changed=False;ids=[]
        for proposed in arr(packet['reports'],6,'reports'):
            obj(proposed,('domain','holder','value','confidence','quote','kind'),('domain','holder','value','confidence','quote','kind'))
            domain=proposed['domain'];value=proposed['value'];holder=proposed['holder'];confidence=proposed['confidence']
            if domain not in DOMAINS or value not in DOMAINS[domain]:raise ValueError('unsupported report value')
            if not isinstance(holder,str) or (holder!='user' and not holder.startswith('other:')) or len(holder)>80:raise ValueError('holder must be user or other:name')
            if domain=='signal' and holder!='user':raise ValueError('only direct user interaction can be a social appraisal source')
            if type(confidence) not in (int,float) or not math.isfinite(confidence) or not 0<=confidence<=1:raise ValueError('invalid confidence')
            if proposed['kind'] not in ('explicit','inferred'):raise ValueError('report kind must be explicit or inferred')
            quote=text(proposed['quote'],'quote',600)
            if quote not in raw:raise ValueError('report must quote this actual user message exactly')
            clean=deepcopy(proposed);clean['quote']=quote
            clean['confidence']=min(confidence,.9 if clean['kind']=='explicit' else .55)
            if any(r['source']==source and all(r[k]==clean[k] for k in clean) for r in self.mind.other_reports):continue
            r=self.mind.add_report(clean,source);ids.append(r['id']);changed=True
        request=packet['request'];obj(request,('kind','quote'),('kind',))
        if request['kind'] not in ('none','join','pause','together','wait','independent','resume'):raise ValueError('request is a local invitation, not arbitrary action authority')
        if request['kind']!='none':
            quote=text(request.get('quote'),'request quote',600)
            if quote not in raw:raise ValueError('request must quote current message')
        if request['kind']=='join':self.mind.invitation=True;changed=True
        if request['kind'] in ('together','wait','independent','resume'):
            self.mind.set_activity(request['kind'],source);changed=True
        if changed:self.mind.plan()
        return {'reports':ids,'request':request['kind'],'physical_model_training':False,
                'semantic_extraction_verified':False}

    def _mutate(self,kind,p,eid):
        if kind=='message':
            obj(p,('text',),('text',));raw=text(p['text'],'message',6000)
            self._change()
            for m in self.state['messages']:
                if m['role']=='user' and m['id'] not in self.state['handled']:self.state['handled'].append(m['id'])
            self.state['messages'].append({'id':eid,'role':'user','text':raw})
            self.state['observations'].append({'id':eid,'kind':'message','content':raw})
            r=self._report(eid)
            return {'kind':'real_user_observation','pre_language_state':r['id'],'world_advanced':False,
                    'note':'提问没有制造新的情感数值；状态来自此前共同经历'}
        if kind in ('agent_step','player_action'):
            obj(p,() if kind=='agent_step' else ('action',),() if kind=='agent_step' else ('action',))
            self._change(preserve_pending=kind=='player_action')
            if kind=='agent_step':
                plan=self.mind.plan();action=plan['action'];actor='agent'
                if action['kind']=='wait_partner':return {'kind':'waiting_for_partner','reason':plan['reason'],'world_tick':self.world.tick,'activity_source':self.mind.activity['source'],'no_model_call':True}
                if action['kind']=='sleep':return {'kind':'sleep','reason':plan['reason'],'no_model_call':True}
            else:action=p['action'];actor='user'
            before=self.mind.report();event=self.world.act(actor,action)
            self.mind.observe(event,eid);self.mind.plan()
            if actor=='agent':
                for message in self.state['messages']:
                    receipt=message.get('intention')
                    if receipt and receipt['status']=='selected_not_executed':
                        receipt.update(status='executed' if receipt['action']==action else 'revised_on_new_observation',
                            result_event=eid,actual_action=deepcopy(action),success=event['success'])
            self.state['observations'].append({'id':eid,'kind':'world','content':deepcopy(event)})
            return {'kind':'actual_shared_transition','transition':event,'prior_affect':before['affect'],
                    'after_affect':self.mind.affect(),'next_focus':deepcopy(self.mind.focus)}
        if kind=='reflect':
            obj(p,());self._change();r=self.mind.replay();self.mind.plan();return r
        if kind=='activity':
            obj(p,('mode',),('mode',));self._change(preserve_pending=True);self.mind.set_activity(p['mode'],eid);self.mind.plan()
            return {'kind':'joint_commitment_changed','mode':self.mind.activity['mode'],'source':eid,'authority_expanded':False}
        if kind=='invite':
            obj(p,());self._change(preserve_pending=True);self.mind.invitation=True;self.mind.plan()
            return {'kind':'invitation_received','no_external_authority_granted':True}
        if kind=='intervene':
            obj(p,('kind',),('kind',));self._change();return self.world.perturb(p['kind'])
        if kind=='ablation':
            obj(p,('mode',),('mode',))
            if p['mode'] not in MODES:raise ValueError('unknown ablation')
            self._change();self.mind.mode=p['mode'];self.mind.plan();return {'kind':'ablation_changed','mode':p['mode']}
        if kind=='new_expedition':
            obj(p,());self._change();old=self.world;new_seed=(old.seed+7919)%2147483647
            self.world=World(new_seed,old.horizon);self.world.tool_skill=old.tool_skill
            self.mind.new_expedition(self.world.observe('agent'));self.mind.last_event=eid
            self.state['observations'].append({'id':eid,'kind':'new_expedition','content':self.world.observe('agent')})
            self.mind.plan()
            return {'kind':'new_expedition','retained':'type-yield/self-capability/social history; old map cleared',
                    'expedition':self.mind.expedition}
        if kind=='name':
            obj(p,('name',),('name',));self._change();self.state['name']=text(p['name'],'name',24)
            return {'kind':'display_name_changed','not_new_identity_evidence':True}
        if kind=='interpret':
            obj(p,('source','packet'),('source','packet'))
            if p['source']!=self.pending_turn():raise ValueError('stale interpretation')
            r=self._interpret(p['source'],p['packet']);self._change()
            report=self._report(p['source'])
            self.state['pending']={'source':p['source'],'state_id':report['id'],'revision':self.state['revision'],'narration':False}
            return {**r,'kind':'source_grounded_interpretation','state_id':report['id']}
        if kind=='prepare_narration':
            obj(p,());source=self.mind.last_event
            if not source or source==self.state['last_narrated']:raise ValueError('no new real event to narrate')
            report=self._report(source);self.state['last_narrated']=source
            self.state['pending']={'source':source,'state_id':report['id'],'revision':self.state['revision'],'narration':True}
            return {'kind':'prepared_grounded_narration','state_id':report['id']}
        if kind=='expression':
            obj(p,('state_id','speech','decision_id'),('state_id','speech'));pending=self.state['pending']
            if not pending or pending['state_id']!=p['state_id']:raise ValueError('stale expression state')
            pinned=next(r for r in self.state['reports'] if r['id']==p['state_id'])
            receipt=contract(pinned)
            if p.get('decision_id',receipt['decision_id'])!=receipt['decision_id']:raise ValueError('expression names an unselected decision')
            historical=pinned['world_tick']!=self.world.tick or pinned['revision']!=self.state['revision']
            raw=text(p['speech'],'speech',6500);speech,guard=guard_speech(raw,receipt,historical)
            receipt['status']='superseded_before_delivery' if historical else 'selected_not_executed'
            self.state['messages'].append({'id':eid,'role':'assistant','text':speech,
                'state_id':p['state_id'],'kind':'language_expression','narration':pending['narration'],
                'intention':receipt,'speech_guard':guard,'temporal_status':'earlier_snapshot' if historical else 'current_snapshot',
                'delivery_world_tick':self.world.tick})
            if not pending['narration']:self.state['handled'].append(pending['source'])
            self.state['pending']=None
            return {'kind':'state_grounded_language_submitted','state_id':p['state_id'],'speech_guard':guard,
                    'temporal_status':'earlier_snapshot' if historical else 'current_snapshot',
                    'semantic_fidelity':'finite action contradiction checks only; general semantics NOT independently established'}
        if kind=='local_reply':
            obj(p,());source=self.pending_turn()
            if source is None:raise ValueError('no pending message')
            r=self._report(source);report=r['report'];f=report['focus'];action=f['action']
            room=self.mind.known.get(str(action.get('target',f['goal']['target'])),{}).get('name','当前地点')
            body=('【本地状态报告 · 未调用语言模型】\n'+report['state_words']+'。\n'
                  +'我正在处理：'+f['reason']+'。下一步倾向：'+ACTION_NAMES[action['kind']]+('「'+room+'」' if action['kind'] in ('move','scan') else '')+'。\n'
                  +'依据：'+str(f['basis'])+'；状态快照 '+r['id']+'。\n'
                  +'这是一份数值状态的直接呈现，不是对你这句话的通用语言理解；连接模型后可自然对话。')
            self.state['messages'].append({'id':eid,'role':'assistant','text':body,'state_id':r['id'],'kind':'local_state_report'})
            self.state['handled'].append(source);self.state['pending']=None
            return {'kind':'local_report_rendered','state_id':r['id'],'model_called':False}
        if kind=='withdraw_report':
            obj(p,('id',),('id',));self._change();self.mind.withdraw(p['id']);self.mind.plan()
            return {'kind':'report_withdrawn','id':p['id'],'current_social_affect_recomputed':True,'past_actions_not_erased':True}
        if kind=='discard':
            obj(p,());self.state['pending']=None;return {'kind':'uncommitted_expression_discarded'}
        if kind=='call':
            obj(p,('phase','model'),('phase','model'));self.state['calls']+=1
            return {'kind':'request_reserved','call':self.state['calls'],'phase':text(p['phase'],'phase',80)}
        if kind=='usage':
            obj(p,('usage','model'),('usage','model'))
            if not isinstance(p['usage'],dict):raise ValueError('usage must be object')
            for k in self.state['usage']:
                value=p['usage'].get(k,0)
                if type(value) is not int or not 0<=value<=1000000:raise ValueError('invalid provider usage')
                self.state['usage'][k]+=value
            return {'kind':'provider_reported_usage','model':text(p['model'],'model',200,True)}
        raise ValueError('unsupported shared kernel operation')

    def context(self,expression=False):
        pending=self.state['pending']
        pinned=next((deepcopy(r) for r in self.state['reports'] if pending and r['id']==pending['state_id']),None)
        report=pinned['report'] if pinned else self.mind.report()
        data={'agent_name':self.state['name'],
                'shared_observation':deepcopy(pinned.get('observation',self.world.observe('agent'))) if pinned else self.world.observe('agent'),
                'state_report':pinned if pinned else report,
                'recent_dialogue':deepcopy(self.state['messages'][-16:]),
                'reported_other_states':deepcopy(self.mind.other_reports[-24:]),
                'autobiographical_events':deepcopy(report.get('memory_cards',[])),
                'open_invitation':self.mind.invitation,
                'permissions':['speech','source-grounded interpretation','shared-environment commitment; no authority escalation'],
                'boundary':'持续调节状态参与规划，但不认证主观体验。不要用生硬边界声明替代普通感觉问题的回答。'}
        if expression and pinned:
            data['intention_contract']=contract(pinned)
            data['state_report']['report']['focus'].pop('candidates',None)
            data['state_report']['report']['focus'].pop('coefficients',None)
            data['language_guidance']='先回应对方当前的话。当前选择是已选而非犹豫未定；回顾使用有来源的事件与检查进度。无需逐项报分数。'
        return data

    def view(self):
        return {'version':'0.5.0','name':self.state['name'],'world':self.world.observe('agent'),
                'player':self.world.observe('user'),'cognition':self.mind.report(),
                'messages':deepcopy(self.state['messages'][-100:]),'reports':deepcopy(self.state['reports'][-30:]),
                'other_reports':deepcopy(self.mind.other_reports[-50:]),'goal_history':deepcopy(self.mind.goals[-25:]),
                'observations':len(self.state['observations']),'events':len(self.events),'calls':self.state['calls'],
                'usage':deepcopy(self.state['usage']),'last_events':[{'id':e['id'],'kind':e['kind'],
                    'result':deepcopy(e['result'])} for e in self.events[-16:] if e['kind'] not in ('call','usage')],
                'edges':deepcopy(self.mind.edges),'expedition':self.mind.expedition,
                'remaining_discoveries':12-len(self.world.discovered),'replays':self.mind.replays,'migration_notice':deepcopy(self.state.get('migration_notice'))}

    def checkpoint(self):
        return {'schema':'switchlab.shared.v5','metadata':deepcopy(self.metadata),'events':deepcopy(self.events),
                'head':self.head,'origin':deepcopy(self.origin),**self.snapshot()}
    @classmethod
    def from_v04(cls,data):
        from .migration import verify_v04
        verified=verify_v04(data)
        c=cls(**data['metadata']['config']);c._load(verified['snapshot'])
        c.origin=deepcopy(data)
        # Reconstruct summaries from already-verified observations. Do not update
        # old physical posteriors, affect, or pretend v5 predictor was trained online.
        from . import continuity
        mode=c.mind.mode;expedition=c.mind.expedition;c.mind.mode='learning_frozen'
        for episode in c.mind.episodes:
            c.mind.expedition=episode['expedition']
            continuity.observe(c.mind,episode['event'],episode['source'])
        c.mind.mode=mode;c.mind.expedition=expedition
        c.metadata.update(origin_kind='verified_v04_continuation',origin_digest=digest(data),
                          event_offset=verified['events'],origin_head=verified['head'])
        # A request in flight at export is not a completed answer. Preserve the
        # original in origin; no automatic paid retry or imagined response.
        unfinished=[m['id'] for m in c.state['messages'] if m['role']=='user' and m['id'] not in c.state['handled']]
        c.state['handled'].extend(unfinished);c.state['pending']=None
        c.state['migration_notice']={'unfinished_questions':unfinished,'old_events':verified['events'],
            'physical_tick':c.world.tick,'original_hashes_match':True,
            'comparison':verified['comparison'],'past_errors_not_rewritten':True}
        c.mind.plan();c.head=digest(c.metadata)
        return c

    @classmethod
    def restore(cls,data,check_source=True):
        obj(data,('schema','metadata','events','head','state','world','mind','origin'),('schema','metadata','events','head','state','world','mind','origin'))
        if data['schema']!='switchlab.shared.v5':raise ValueError('不是共享探索v0.5状态；v0.4请使用显式迁移，不覆盖旧目录。')
        if check_source and data['metadata']['source_sha256']!=fingerprint():raise ValueError('源码版本不匹配；保留生成数据的原包，不要修改JSON绕过。')
        if not isinstance(data['events'],list) or len(data['events'])>LIMIT_EVENTS:raise ValueError('event budget')
        c=cls.from_v04(data['origin']) if data.get('origin') is not None else cls(**data['metadata']['config'])
        if canonical(c.metadata)!=canonical(data['metadata']):raise ValueError('初始元数据或迁移来源被改变')
        c.metadata=deepcopy(data['metadata']);c.head=digest(c.metadata)
        for e in data['events']:
            actual=c.apply(e['kind'],e['payload'])
            if canonical(actual)!=canonical(e):raise ValueError('记录输入复算不一致：'+str(e.get('id')))
        if c.head!=data['head'] or canonical(c.snapshot())!=canonical({k:data[k] for k in ('state','world','mind')}):raise ValueError('最终状态不等于重新计算的结果')
        return c
