"""Shared commitments and source-grounded experience threads.

The commitment automaton and control constraints are engineered priors. The
small softmax model is trained on unique observed choices, not approval or
claimed emotion. It predicts choices, NOT the user's true preferences. Memory
summaries and questions have real event sources; they never count as observations.
"""
from __future__ import annotations
from copy import deepcopy
import math
from .world import KINDS,ROOM_NAMES,edge_key

ACTIVITIES=('independent','together','wait','resume')


def init(m):
    m.activity={'mode':'independent','previous':'independent','source':'initial','history':[]}
    m.partner={'position':0,'stamina':None,'failure_streak':0,'last_source':None,'last_action':None}
    m.partner_model={'weights':{k:0. for k in KINDS},'updates':0,'seen_choices':[],
                     'last_prediction':None,'log_loss_sum':0.}
    m.threads=[];m.memory_cards=[];m.last_reflection=None


def set_activity(m,mode,source):
    if mode not in ACTIVITIES:raise ValueError('共同活动模式无效')
    old=m.activity['mode']
    if mode=='resume':mode=m.activity['previous'] if old=='wait' else old
    if mode=='wait' and old!='wait':m.activity['previous']=old
    if mode=='independent':m.invitation=False
    m.activity['mode']=mode;m.activity['source']=source
    m.activity['history'].append({'from':old,'to':mode,'source':source})
    m.activity['history']=m.activity['history'][-60:]


def choice_probabilities(m,options):
    logits=[m.partner_model['weights'][r['kind']] for r in options]
    if not logits:return []
    mx=max(logits);zs=[math.exp(v-mx) for v in logits];total=sum(zs)
    return [z/total for z in zs]


def _learn_choice(m,event,eid):
    if m.mode=='learning_frozen' or event['actor']!='user' or event['action']['kind']!='move':return
    before=event['before'];target=event['action']['target'];options=before['neighbors']
    key=f"{m.expedition}:{before['position']}:{target}"
    model=m.partner_model
    if key in model['seen_choices']:return
    chosen=next((i for i,r in enumerate(options) if r['id']==target),None)
    if chosen is None:return
    ps=choice_probabilities(m,options)
    model['last_prediction']={'source':eid,'probabilities':{str(r['id']):p for r,p in zip(options,ps)},
                              'actual_target':target,'predicted_before_update':True}
    model['log_loss_sum']-=math.log(max(1e-12,ps[chosen]))
    gradient={k:0. for k in KINDS}
    for i,(r,p) in enumerate(zip(options,ps)):gradient[r['kind']]+=(1. if i==chosen else 0.)-p
    for k in KINDS:model['weights'][k]=max(-3.,min(3.,.999*model['weights'][k]+.18*gradient[k]))
    model['updates']+=1;model['seen_choices'].append(key)


def _thread(m,kind,eid,target=None):
    t=next((t for t in reversed(m.threads) if t['type']==kind and t['status']=='open' and t['expedition']==m.expedition and t.get('target')==target),None)
    if not t:
        t={'id':f'T{len(m.threads)+1:05d}','type':kind,'expedition':m.expedition,'status':'open',
           'source':eid,'sources':[],'checks':[],'target':target,'last_result':None}
        m.threads.append(t)
    if eid not in t['sources']:t['sources'].append(eid)
    return t


def observe(m,event,eid):
    actor=event['actor'];action=event['action'];kind=action['kind'];ok=event['success'];old=event['before'];new=event['after']
    _learn_choice(m,event,eid)
    if actor=='user':
        m.partner.update(position=new['position'],stamina=new['stamina'],last_source=eid,last_action=deepcopy(action))
        if kind=='move' and not ok:
            m.partner['failure_streak']+=1
            t=_thread(m,'partner_route',eid,action['target']);t['last_result']='partner_move_failed'
            t['question']='对方在这段路受阻；是否需要我会合或一起看？不能据此认定对方难过。'
        if kind=='move' and ok:
            m.partner['failure_streak']=0
            for t in m.threads:
                if t['type']=='partner_route' and t['status']=='open' and t.get('target')==action['target']:
                    t.update(status='resolved',closed_by=eid,last_result='partner_moved_successfully')
    if actor=='agent' and kind=='move' and not ok:
        t=_thread(m,'self_or_route',eid,action['target']);t['last_result']='move_failed'
        t['question']='路况与自身能力都可能解释失败；已有校准次数与结果必须一起考虑。'
    if actor=='agent' and kind in ('calibrate','repair'):
        for t in m.threads:
            if t['type']=='self_or_route' and t['status']=='open':
                t['checks'].append(eid);t['last_result']='calibration_observed' if kind=='calibrate' else 'tool_maintained'
                # A successful calibration supplies evidence, not certainty about every cause.
    if actor=='agent' and kind=='move' and ok:
        for t in m.threads:
            if t['type']=='self_or_route' and t['status']=='open' and t['target']==action['target']:
                t.update(status='resolved',closed_by=eid,last_result='target_reached_after_revision')
    if event.get('finding',{}).get('new') or not ok or kind in ('calibrate','repair'):
        f=event.get('finding');desc={'move':'尝试移动','survey':'调查','scan':'观察路况','calibrate':'校准工具','repair':'维护工具','rest':'休整'}.get(kind,kind)
        target=ROOM_NAMES[action['target']] if 'target' in action else old['room']['name']
        card={'source':eid,'actor':actor,'expedition':m.expedition,'tick':new['tick'],
              'action':deepcopy(action),'outcome':'success' if ok else 'failure',
              'summary':f"{'我' if actor=='agent' else '你'}在{old['room']['name']}{desc}「{target}」，{'完成' if ok else '没有达到预期'}。",
              'joint':old['position']==old['partner_position'],'finding':deepcopy(f)}
        m.memory_cards.append(card);m.memory_cards=m.memory_cards[-160:]
    # Progress towards an adopted joint constraint is an actual event, not praise.
    if m.activity['mode']=='together' and old['position']!=old['partner_position'] and new['position']==new['partner_position']:
        m.appraisals.append({'source':eid+':joint','delta':{'valence':.035,'arousal':-.025,'frustration':-.015},
                             'why':'已采纳的共同活动恢复会合；依据实际位置，不依据赞同或沉默'})


def partner_interest(m,kind):
    w=m.partner_model['weights'];mx=max(w.values());z={k:math.exp(v-mx) for k,v in w.items()};return z[kind]/sum(z.values())


def constrain(m,rows):
    mode=m.activity['mode'];r=m.current['position'];p=m.current['partner_position']
    def waiting(reason):
        return [{'key':'wait_partner:'+str(p),'type':'wait_partner','target':p,'action':{'kind':'wait_partner'},
                 'score':0.,'prediction':{'success':1.,'value':0.,'uncertainty':0.},'reason':reason,
                 'commitment_source':m.activity['source']}]
    if mode=='wait':return waiting('共同约定：等你准备好；不反复休整、不替你行动，也不消耗物理步骤')
    if mode!='together':return rows
    if m.current['stamina']<.13:return rows
    if r!=p:
        path=m._path(p)
        if path and (m.partner['failure_streak']>0 or len(path)>2):
            a={'kind':'move','target':path[1]};pr=m.predict(a)
            return [{'key':'rejoin:'+str(p),'type':'rejoin','target':p,'action':a,'prediction':pr,'score':1.,
                     'reason':'共同活动出现分离或受阻；先回到你身边，再继续共同目标',
                     'commitment_source':m.activity['source']}]
        here=[x for x in rows if x['action']['kind']=='survey']
        return here or waiting('我已领先一个地点，先在这里等你；不把同行变成独自跑完全图')
    if m.partner['stamina'] is not None and m.partner['stamina']<.13:
        return waiting('已观察到你的行动资源不足；保留共同目标，等你恢复或改为各自探索')
    # Learned behavioral tendency affects destination ranking only during adopted
    # cooperation. It is deliberately weaker than explicit constraints and risk.
    for row in rows:
        if row['type']=='explore':
            kind=m.known[str(row['target'])]['kind']
            bonus=.10*(partner_interest(m,kind)-.25)
            row['score']+=bonus;row['social_prediction_adjustment']=bonus
    return rows


def reflect(m):
    open_threads=[deepcopy(t) for t in m.threads if t['status']=='open'][-6:]
    m.last_reflection={'sources':[e['source'] for e in m.memory_cards[-8:]],'questions':open_threads,
                       'external_observation_added':False,'model_evidence_added':0}
    return deepcopy(m.last_reflection)


def report(m):
    return {'activity':deepcopy(m.activity),'partner_observation':deepcopy(m.partner),
            'partner_choice_model':{'updates':m.partner_model['updates'],
                'category_tendencies':{k:partner_interest(m,k) for k in KINDS},
                'last_prediction':deepcopy(m.partner_model['last_prediction']),
                'interpretation':'有偏的行为预测；路线可达性、你的测试操作等都是替代解释，不等于读出真实偏好'},
            'shared_concerns':[deepcopy(t) for t in m.threads if t['type']=='partner_route' and t['status']=='open'][-6:],
            'experience_threads':deepcopy(m.threads[-12:]),'memory_cards':deepcopy(m.memory_cards[-12:]),
            'last_reflection':deepcopy(m.last_reflection)}
