"""Inspectable learned beliefs and engineered appraisal/control priors.

Learns action reliability and category information yields from unique real events.
Appraisal updates are explicitly engineered, not a claim of learned emotion or
phenomenology. The state feeds action scores before language generation. No
language output can set these scores or train the physical model as truth.
"""
from __future__ import annotations
from copy import deepcopy
from collections import deque
import math
import heapq
from .world import KINDS, KIND_NAMES, neighbors, edge_key
from . import continuity
from .evidence import digest

MODES=('full','affect_off','self_off','learning_frozen','flat_baseline')

def clip(x,lo=0.,hi=1.):return max(lo,min(hi,x))
def entropy(p):return -sum(x*math.log2(max(1e-12,x)) for x in (p,1-p))
def bayes(prior,l1,l0):return clip(prior*l1/max(1e-12,prior*l1+(1-prior)*l0),.001,.999)

class Mind:
    def __init__(self):
        self.current={};self.known={};self.surveyed=[];self.edges={};self.edge_counts={}
        self.self_stats={'a':9.,'b':1.,'n':0};self.interests={k:{'sum':1.,'n':2.,'seen':0} for k in KINDS}
        self.learned_events=0;self.seen=[];self.episodes=[];self.appraisals=[];self.retracted=[]
        self.mode='full';self.internal_ticks=0;self.replays=0;self.last_replay_size=0
        self.last_error=0.;self.last_event=None;self.focus=None;self.goals=[];self.goal=None
        self.other_reports=[];self.invitation=False;self.goal_serial=0;self.expedition=1
        self.last_plan=None;self.unexplained_failures=0
        continuity.init(self)
        self.plan_signature=None;self.decision_timeline=[]

    def refresh(self,o):
        self.current=deepcopy(o)
        for r in o['visible_rooms']:
            self.known[str(r['id'])]=deepcopy(r)
            if r['surveyed'] and r['id'] not in self.surveyed:self.surveyed.append(r['id'])

    def capability(self):
        if self.mode=='self_off':return .9
        s=self.self_stats;return s['a']/(s['a']+s['b'])

    def interest(self,k):
        x=self.interests[k];return x['sum']/x['n']

    def affect(self):
        e={'valence':0.,'arousal':.12,'frustration':0.}
        for a in self.appraisals:
            if a['source'] in self.retracted:continue
            for k in e:
                e[k]=clip(e[k]*.88+a['delta'].get(k,0),-1. if k=='valence' else 0.,1.)
        return e

    def coefficients(self):
        e=self.affect() if self.mode not in ('affect_off','flat_baseline') else {'frustration':0.,'arousal':0.,'valence':0.}
        return {'risk':.55+1.6*e['frustration'], 'information':.16+.50*e['arousal']+.6*e['frustration'],
                'energy':.18+max(0,.45-self.current.get('stamina',1.)),'persistence':0. if self.mode=='flat_baseline' else .065}

    def predict(self,action,actor='agent',position=None):
        kind=action['kind'];r=self.current.get('position',0) if position is None else position
        ability=self.capability() if actor=='agent' else .98
        if kind=='move':
            stable=self.edges.get(edge_key(r,action['target']),.7)
            p=(.96*stable+.40*(1-stable))*ability
            return {'success':p,'stable':stable,'uncertainty':entropy(stable),'value':0.}
        if kind=='calibrate':return {'success':ability,'uncertainty':1/math.sqrt(self.self_stats['n']+1.),'value':0.}
        if kind=='survey':
            k=self.known.get(str(r),self.current.get('room',{'kind':'flora'}))['kind']
            return {'success':1.,'value':0. if r in self.surveyed else self.interest(k),
                    'uncertainty':1/math.sqrt(self.interests[k]['n'])}
        return {'success':1.,'value':0.,'uncertainty':0.}

    def observe(self,event,eid):
        if eid in self.seen:return
        self.seen.append(eid);self.last_event=eid
        action=event['action'];kind=action['kind'];actor=event['actor'];r=event['before']['position']
        forecast=self.predict(action,actor,r);ok=float(event['success']);err=abs(ok-forecast['success'])
        delta={'valence':0.,'arousal':0.,'frustration':0.};why=[]
        if self.mode!='learning_frozen':
            if kind in ('move','scan'):
                key=edge_key(r,action['target']);prior=.98*self.edges.get(key,.7)+.01
                if kind=='scan':
                    positive=event['sensor_stable'];p=bayes(prior,.86 if positive else .14,.14 if positive else .86)
                else:
                    skill=self.capability() if actor=='agent' else .98
                    p=bayes(prior,.96*skill if ok else 1-.96*skill,.40*skill if ok else 1-.40*skill)
                self.edges[key]=p;self.edge_counts[key]=self.edge_counts.get(key,0)+1
            if kind=='calibrate' and actor=='agent':
                s=self.self_stats
                # Power-posterior forgetting allows a changing actuator to be relearned.
                s['a']=1.+.96*(s['a']-1.)+ok;s['b']=1.+.96*(s['b']-1.)+1.-ok;s['n']+=1
                self.unexplained_failures=max(0,self.unexplained_failures-1)
            if kind=='repair' and actor=='agent':
                self.self_stats={'a':4.,'b':1.,'n':0};self.unexplained_failures=0
            if event.get('finding',{}).get('new'):
                f=event['finding'];x=self.interests[f['kind']];x['sum']+=f['richness'];x['n']+=1.;x['seen']+=1
            self.learned_events+=1
        if kind=='move' and actor=='agent':
            if not ok:
                self.unexplained_failures+=1;delta={'valence':-.20-.12*err,'arousal':.16+.15*err,'frustration':.23}
                why.append('行动未达到预期；自身能力与路况原因仍需区分')
            else:delta={'valence':.06,'arousal':.03,'frustration':-.05};why.append('移动成功，保留对失败原因的不确定性')
        if kind=='calibrate' and actor=='agent':
            delta={'valence':.04 if ok else -.10,'arousal':.09,'frustration':-.02}
            why.append('独立校准提供关于自身执行能力的证据')
        if kind=='scan':delta={'valence':.025,'arousal':.10,'frustration':-.04};why.append('检查路况得到有噪声的证据')
        if kind=='rest' and actor=='agent':delta={'valence':.025,'arousal':-.08,'frustration':-.10};why.append('恢复行动资源，而不是依靠用户赞同')
        if kind=='repair':delta={'valence':.10,'arousal':.04,'frustration':-.12};why.append('维护完成；能力仍需后续结果校验')
        if event.get('finding',{}).get('new'):
            f=event['finding'];expected=forecast.get('value',.5) if kind=='survey' else .5
            err=abs(f['richness']-expected)
            delta={'valence':.12+.14*f['richness'],'arousal':.16+.2*err,'frustration':-.09}
            why.append('新发现的信息收益与事先预测比较；更新类型收益估计')
        self.last_error=err
        self.appraisals.append({'source':eid,'delta':delta,'why':'；'.join(why) or '观察到共同活动的实际进程'})
        self.episodes.append({'source':eid,'expedition':self.expedition,'event':deepcopy(event),
                              'forecast':forecast,'error':err,'learning_enabled':self.mode!='learning_frozen'})
        self.refresh(event['agent_observation'])
        continuity.observe(self,event,eid)
        if self.invitation and self.current['position']==self.current['partner_position']:self.invitation=False
        if self.goal:
            target=self.goal.get('target')
            done=(self.goal['type']=='explore' and target in self.surveyed) or (self.goal['type']=='join' and not self.invitation)
            done=done or (self.goal['type']=='rejoin' and self.current['position']==self.current['partner_position'])
            done=done or (actor=='agent' and self.goal['type']==kind and kind in ('rest','calibrate','repair'))
            if done:self.goal['status']='completed';self.goal['closed_by']=eid;self.goals.append(deepcopy(self.goal));self.goal=None

    def _path(self,target):
        # Expected retry count under learned reliability, not a shortest-hop
        # command table. Unknown edges use the same public prior as prediction.
        start=self.current['position'];queue=[(0.,[start])];costs={start:0.}
        while queue:
            cost,path=heapq.heappop(queue);at=path[-1]
            if cost>costs[at]+1e-12:continue
            if at==target:return path
            for n in neighbors(at):
                if str(n) not in self.known:continue
                p=self.predict({'kind':'move','target':n},position=at)['success']
                candidate=cost+1./max(.05,p)
                if candidate<costs.get(n,float('inf'))-1e-12:
                    costs[n]=candidate;heapq.heappush(queue,(candidate,path+[n]))
        return None

    def candidates(self):
        if not self.current:return []
        r=self.current['position'];energy=self.current['stamina'];coef=self.coefficients();rows=[]
        def add(kind,action,score,target,why):
            key=kind+':'+str(target)
            if self.goal and self.goal['key']==key:score+=coef['persistence']
            rows.append({'key':key,'type':kind,'target':target,'action':action,'score':score,
                         'prediction':self.predict(action),'reason':why})
        if self.activity['mode']=='wait':return continuity.constrain(self,rows)
        if energy<.13:
            add('rest',{'kind':'rest'},10.,r,'行动资源不足，先恢复，不消耗用户的模型调用预算');return rows
        for sid,room in sorted(self.known.items(),key=lambda x:int(x[0])):
            target=int(sid)
            if target in self.surveyed:continue
            path=self._path(target)
            if not path:continue
            k=room['kind'];value=self.interest(k);unseen=1/math.sqrt(self.interests[k]['n'])
            preference=next((a for a in reversed(self.other_reports) if a.get('domain')=='interest' and a.get('holder')=='user' and a['value']==k and not a.get('withdrawn')),None)
            together=r==self.current['partner_position']
            social=.06*preference['confidence'] if preference and together else 0.
            score=(value+.30+coef['information']*.25*unseen+social)/(1+.24*(len(path)-1))
            if target==r:
                add('explore',{'kind':'survey'},score-.035*coef['energy'],target,'验证当前地点的可观察发现，不重复算新证据')
            else:
                action={'kind':'move','target':path[1]};p=self.predict(action)
                score-=coef['risk']*(1-p['success'])*.32
                add('explore',action,score,target,'前往未调查地点；使用已学类型收益、路况和自身能力预测')
                if .12<p['stable']<.94 and self.edge_counts.get(edge_key(r,path[1]),0)<12:
                    info=p['uncertainty']*coef['information']*.25
                    add('investigate',{'kind':'scan','target':path[1]},score-.14+info,path[1],
                        '在风险或预测误差较高时，先用传感证据区分路况')
        if rows:
            if self.unexplained_failures>0:
                score=.10+.16*min(4,self.unexplained_failures)+.12/math.sqrt(self.self_stats['n']+1.)
                add('calibrate',{'kind':'calibrate'},score,r,'之前失败可能来自自身；校准与环境路况分离')
            if self.capability()<.60 and self.self_stats['n']>=3:
                add('repair',{'kind':'repair'},1.0-self.capability()+.25,r,'多次校准降低了能力估计，尝试实际维护')
            if energy<.43:add('rest',{'kind':'rest'},(.43-energy)*4.,r,'预测接下来的行动资源不足，提前恢复')
        if self.invitation:
            target=self.current['partner_position'];path=self._path(target)
            if path and len(path)>1:
                action={'kind':'move','target':path[1]}
                add('join',action,1.15/(1+.20*(len(path)-1)),target,'响应会合邀请；路径和行动仍由本地规划决定')
        if not rows:add('sleep',{'kind':'sleep'},0.,r,'暂时没有新的可调查地点或未决会合目标，不制造空闲动机')
        rows=continuity.constrain(self,rows)
        unique={}
        for row in rows:
            if row['key'] not in unique or row['score']>unique[row['key']]['score']:unique[row['key']]=row
        return sorted(unique.values(),key=lambda x:(-x['score'],x['key']))

    def _decision_signature(self):
        return digest([self.current,self.edges,self.self_stats,self.interests,self.mode,self.goal,
                       self.invitation,self.activity,self.partner,self.partner_model['weights'],
                       self.affect(),self.last_event,self.replays,self.unexplained_failures])

    def plan(self):
        signature=self._decision_signature()
        if self.focus and self.plan_signature==signature:return deepcopy(self.focus)
        self.internal_ticks+=1;rows=self.candidates();choice=rows[0] if rows else None
        if choice is None:return None
        if self.goal and self.goal['key']!=choice['key']:
            self.goal['status']='revised';self.goal['closed_by']='new_evidence_or_changed_cost';self.goals.append(deepcopy(self.goal));self.goal=None
        if self.goal is None:
            self.goal_serial+=1;self.goal={'id':'G%04d'%self.goal_serial,'key':choice['key'],'type':choice['type'],
                'target':choice['target'],'status':'sleep' if choice['type']=='sleep' else 'active',
                'created_at':self.internal_ticks,'basis':self.last_event or 'initial_observation'}
        self.focus={'id':'P%05d'%self.internal_ticks,'goal':deepcopy(self.goal),'action':deepcopy(choice['action']),
                    'prediction':deepcopy(choice['prediction']),'reason':choice['reason'],
                    'basis':self.last_event or 'initial_observation','coefficients':self.coefficients(),
                    'candidates':deepcopy(rows[:16])}
        self.last_plan=deepcopy(self.focus);self.plan_signature=self._decision_signature()
        self.decision_timeline.append({'id':self.focus['id'],'source':self.focus['basis'],
            'goal':self.goal['id'],'action':deepcopy(self.focus['action']),'reason':self.focus['reason']})
        self.decision_timeline=self.decision_timeline[-48:]
        return deepcopy(self.focus)

    def replay(self):
        # Re-evaluates old surprises under the CURRENT model; no extra likelihood factors.
        # This is diagnostic reflection, not neural consolidation or another real experience.
        selected=sorted(self.episodes,key=lambda e:e['error'],reverse=True)[:5]
        self.replays+=1;self.last_replay_size=len(self.episodes);self.internal_ticks+=1
        return {'kind':'counterfactual_review','sources':[x['source'] for x in selected],
                'prediction_errors':[x['error'] for x in selected],'experience_review':continuity.reflect(self),'new_external_evidence':False,
                'updates_to_model_counts':0,'note':'重看真实经历并重排当前计划；不重复计入概率证据'}

    def add_report(self,report,eid):
        r=deepcopy(report);r.update(source=eid,id='R%04d'%(len(self.other_reports)+1),withdrawn=False)
        self.other_reports.append(r)
        if r.get('domain')=='signal':
            table={'shared_enjoyment':{'valence':.045,'arousal':.02,'frustration':-.015},
                   'help_offered':{'valence':.025,'arousal':.03,'frustration':-.025},
                   'misunderstanding':{'valence':-.025,'arousal':.04,'frustration':.015}}
            d=table.get(r['value'],{})
            self.appraisals.append({'source':r['id'],'delta':{k:v*r['confidence'] for k,v in d.items()},
                                   'why':'有来源但可能有误的语言信号；不是任务真值或物理能力奖励'})
        return r

    def withdraw(self,rid):
        r=next((r for r in self.other_reports if r['id']==rid),None)
        if not r:raise ValueError('unknown report')
        r['withdrawn']=True
        if rid not in self.retracted:self.retracted.append(rid)

    def new_expedition(self,o):
        if self.goal:self.goal['status']='archived_at_expedition_end';self.goals.append(deepcopy(self.goal))
        self.current={};self.known={};self.surveyed=[];self.edges={};self.edge_counts={};self.goal=None;self.invitation=False
        self.expedition+=1;self.refresh(o)
        self.partner.update(position=0,stamina=None,failure_streak=0,last_source=None,last_action=None)
        for t in self.threads:
            if t['status']=='open':t['status']='archived_environment_changed'

    def report(self):
        e=self.affect();labels=[]
        if e['frustration']>.20:labels.append('有些受挫，更谨慎')
        if e['valence']>.12:labels.append('探索进展带来积极倾向')
        if e['valence']<-.12:labels.append('对刚才的结果不太满意')
        if e['arousal']>.30:labels.append('关注正在提高')
        if not labels:labels.append('平稳，正在观察')
        return {**continuity.report(self),'decision_timeline':deepcopy(self.decision_timeline[-8:]),'affect':e,'state_words':'；'.join(labels),'focus':deepcopy(self.focus),
                'self_model':{'tool_success_estimate':self.capability(),'calibration_observations':self.self_stats['n']},
                'interests':{k:{'name':KIND_NAMES[k],'expected_information':self.interest(k),
                                'observed_findings':self.interests[k]['seen']} for k in KINDS},
                'attention':{'prediction_error':self.last_error,'source':self.last_event},
                'basis':deepcopy([a for a in self.appraisals if a['source'] not in self.retracted][-6:]),
                'internal_ticks':self.internal_ticks,'learned_events':self.learned_events,'mode':self.mode,
                'interpretation':'工程化持续调节状态与学习后验；不是主观体验检测器'}

    def set_activity(self,mode,source):
        continuity.set_activity(self,mode,source)

    def snapshot(self):return deepcopy(self.__dict__)
    @classmethod
    def restore(cls,s):
        m=cls();m.__dict__.update(deepcopy(s));return m
