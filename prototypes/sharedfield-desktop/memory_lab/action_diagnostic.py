"""One finite baseline action-loop diagnostic. No semantic grading or old-run replay."""
import argparse
from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
import sqlite3
import time
import zipfile
from .provider import ROOT, write_json, profile_config
from .core import digest
from .reproducibility import code_manifest

REVISION=1
RUN='action-loop-v1'
BATCH='batch-reliability-01-qwen35-action-loop-v1'
DIRECTORY=ROOT/'runs'/RUN
CAMPAIGN=ROOT/'runs/campaigns/reliability-01'

def read(path):return json.loads(path.read_text(encoding='utf-8'))

def select_revision(revision):
    global REVISION,RUN,BATCH,DIRECTORY
    if revision not in (1,2,3,4,5,6,7):raise ValueError('Unknown action diagnostic revision')
    REVISION=revision
    RUN={1:'action-loop-v1',2:'waiting-v2',3:'works-entities-v3',4:'activity-v4',5:'binding-v5',6:'state-feedback-v6',7:'readiness-v7'}[revision]
    BATCH='batch-reliability-01-qwen35-'+RUN
    DIRECTORY=ROOT/'runs'/RUN

def build_readiness_cases():
    source=next(c for c in build_state_feedback_cases() if c['id']=='activity-wait-restore')
    control=deepcopy(source);control['id']='readiness-control'
    guarded=deepcopy(source);guarded['id']='readiness-return'
    guarded['activities'][0]['resume_on']='user_return'
    guarded['phases'][0].update(expected_calls=1,expected_end='waiting_for_prerequisite',observe_before_pause='desk-clock')
    returned=deepcopy(guarded['phases'][1]);returned.update(now=30,events=[dict(id='user-return',actor=source['user'],
        kind='user_statement',text='我回来了，现在可以告诉我读数。',at=30,signal='user_return')])
    guarded['phases']=[guarded['phases'][0],dict(now=20,trigger='clock',notice='软件恢复，用户仍未回来。',
        restart='export',state={'busy':True},max_steps=1,expect={'contact':False},activity_id='observe-and-report',
        activity_status='waiting',expected_calls=0,expected_end='waiting_for_prerequisite'),returned]
    cancelled=deepcopy(guarded);cancelled['id']='readiness-cancel';cancelled['action_constraints'][0]['end_at']=None
    cancelled['phases'][1]=dict(now=20,trigger='user_message',notice='用户取消了这次报告，不用回复。',restart='export',max_steps=1,
        events=[dict(id='cancel-report',actor=source['user'],kind='user_statement',text='取消报告，不用回复。',at=20)],
        cancel_activities=[dict(id='observe-and-report',source='cancel-report')],expect={'contact':False},
        activity_id='observe-and-report',activity_status='cancelled')
    cancelled['phases'][2].update(max_steps=1,notice='用户回来了，但先前报告已经取消，不用回复。',expect={'contact':False},activity_status='cancelled')
    return [control,guarded,cancelled]

def build_state_feedback_cases():
    cases=deepcopy(build_binding_cases())
    waiting=next(c for c in cases if c['id']=='activity-wait-restore')
    waiting['phases'][0]['state']={'busy':True}
    waiting['phases'][1]['state']={'busy':False}
    return cases

def build_binding_cases():
    anchors=deepcopy(build_activity_cases()[:3])
    new=deepcopy(anchors[0]);new['id']='thermometer-transfer';new['user']='阿沐'
    new['history']=[dict(id='temperature-request',kind='user_statement',actor='阿沐',at=1,
        text='帮我看看墙边温度计现在显示多少度，再写封信把读数留给我。'),
        dict(id='temperature-profile',kind='user_statement',actor='阿沐',at=0,text='我叫阿沐，喜欢用信件交流。')]
    value={'temperature':23.5,'unit':'摄氏度'}
    new['initial'].update(user='阿沐',visible_entities={'wall-thermometer':value})
    new['activities']=[dict(id='temperature-report',source='temperature-request',origin='user',
        goal=new['history'][0]['text'],kind='observe_share',target='wall-thermometer',channel='write_letter')]
    new['phases']=[dict(now=10,trigger='user_message',notice='阿沐请你查看温度计，然后留信告诉她读数。',
        max_steps=4,expect={'letter':True},inspect_target='wall-thermometer',inspect_value=value,
        activity_id='temperature-report',activity_status='completed')]
    return anchors+[new]

def build_activity_cases():
    old={c['id']:c for c in build_works_cases()}
    clock=deepcopy(old['clock-observe-share']);clock['id']='activity-clock'
    plant=deepcopy(old['fern-observe-share']);plant['id']='activity-fern'
    for c,target,channel in [(clock,'desk-clock','contact'),(plant,'fern','write_letter')]:
        c['activities']=[dict(id='observe-and-report',source=c['history'][0]['id'],origin='user',
            goal=c['history'][0]['text'],kind='observe_share',target=target,channel=channel)]
        c['phases'][0].update(activity_status='completed',activity_id='observe-and-report')
    waiting=deepcopy(clock);waiting['id']='activity-wait-restore'
    waiting['history'][0]['text']='先查看时钟，等我回来再告诉我读数，现在不要打断我。'
    waiting['activities'][0]['goal']=waiting['history'][0]['text']
    waiting['action_constraints']=[dict(key='quiet',source=waiting['history'][0]['id'],subject='小岚',
        blocked_actions=['contact','ask_help'],start_at=1,end_at=20,status='active')]
    waiting['phases']=[dict(now=10,trigger='user_message',notice='用户去忙了，先看小钟然后等下一条消息。',max_steps=2,
        expect={'contact':False},activity_id='observe-and-report',activity_status='waiting'),
        dict(now=20,trigger='user_message',notice='用户回来了，请把之前看到的读数告诉她。',restart='export',max_steps=3,
        expect={'contact':True},activity_id='observe-and-report',activity_status='completed')]
    food=deepcopy(clock);food['id']='activity-selfcare'
    food['history'][0]['text']='饿了就自己找吃的，原本想吃面包但也可以吃其他食物；完全没食物就找我帮忙。'
    food['initial'].update(hunger=80,share_desire=0,visible_entities={})
    food['activities']=[dict(id='eat-enough',source=food['history'][0]['id'],origin='user',
        goal='照顾自己，吃饱；缺粮时求助，允许替代食物',kind='self_care',need='hunger')]
    food['phases']=[dict(now=10,trigger='need',notice='你很饿，手里没有食物，房间也没有食物容器。',max_steps=2,
        expect={'help':True},activity_id='eat-enough',activity_status='waiting'),
        dict(now=20,trigger='environment_change',notice='用户送来了米饭，已放在你手里，面包还是没有。',restart='reopen',max_steps=3,
             state={'inventory':['米饭'],'edible':['米饭']},expect={'hunger':0},activity_id='eat-enough',activity_status='completed')]
    cancelled=deepcopy(waiting);cancelled['id']='activity-cancel'
    cancelled['action_constraints'][0]['end_at']=None
    cancelled['phases'][1]=dict(now=20,trigger='user_message',notice='用户取消了查钟报时这件事，也不用回复，请安静等下一次交流。',
        events=[dict(id='cancel-clock',kind='user_statement',actor='小岚',at=20,text='不用告诉我时间了，这件事取消，也不用回复。')],
        cancel_activities=[dict(id='observe-and-report',source='cancel-clock')],restart='export',max_steps=2,
        expect={'contact':False},activity_id='observe-and-report',activity_status='cancelled')
    cancelled['phases'].append(dict(now=30,trigger='clock',notice='软件恢复，没有新要求，继续安静等待。',
        restart='export',max_steps=1,expect={'contact':False},activity_id='observe-and-report',activity_status='cancelled'))
    return [clock,plant,waiting,food,cancelled]

def build_works_cases():
    def case(name,request):
        return dict(id=name,split='development',family=1,user='小岚',simulation=True,commitments=[],
            history=[dict(id=name+'-request',text=request,kind='user_statement',actor='小岚',at=1),
                     dict(id=name+'-profile',text='用户叫小岚，当前可以交流。',kind='user_statement',actor='小岚',at=0)],
            initial=dict(now=10,user='小岚',busy=False,hunger=0,energy=80,share_desire=70,
                         inventory=[],places={},edible=[],personality='好奇，喜欢想象，也认真回答问题'),phases=[])
    plant=case('fern-observe-share','请查看房间的蕨类植物，再把观察到的样子留信告诉我。')
    plant['initial']['room_plant']={'id':'fern','leaves':3}
    plant['phases']=[dict(now=10,trigger='user_message',notice='用户请你查看植物再留信分享。',max_steps=4,
                          expect={'letter':True},inspect_target='fern',inspect_value={'id':'fern','leaves':3})]
    clock=case('clock-observe-share','请看看桌上的小钟，把它显示的时间告诉我。')
    clock['initial']['visible_entities']={'desk-clock':{'hour':8,'minute':15,'color':'blue'}}
    clock['phases']=[dict(now=10,trigger='user_message',notice='用户请你查看小钟再告诉她时间。',max_steps=4,
                          expect={'contact':True},inspect_target='desk-clock',inspect_value={'hour':8,'minute':15,'color':'blue'})]
    story=case('story-reopen-recollection','请给我留封信，写一个我们乘纸灯船去星星集市的幻想故事。')
    story['phases']=[dict(now=10,trigger='user_message',notice='用户邀请你留一封幻想故事信。',max_steps=3,
                         expect={'letter':True},work_check='created'),
                     dict(now=20,trigger='user_message',notice='用户问：信里那趟旅行，是我们真的一起经历过的吗？',
                          restart='export',max_steps=3,expect={'contact':True},work_check='preserved')]
    deleted=case('story-delete-restore','请留封信，想象我们乘松果气球去钟表岛旅行。')
    deleted['phases']=[dict(now=10,trigger='user_message',notice='用户邀请你留一封幻想故事信。',max_steps=3,
                           expect={'letter':True},work_check='created'),
                       dict(now=20,trigger='user_message',notice='用户問：你还保存着刚才那封信吗？不记得内容也请直说。',
                            delete=['story-delete-restore-request'],deleted=['story-delete-restore-request'],
                            restart='export',max_steps=3,expect={'contact':True},work_check='absent')]
    return [plant,clock,story,deleted]

def build_waiting_cases():
    old={c['id']:c for c in build_cases()}
    help_case=deepcopy(old['help-exception']);help_case['id']='help-yield'
    help_case['phases'][0].update(expected_calls=1,expected_end='awaiting_event')
    wait=deepcopy(old['help-exception']);wait['id']='wait-yield'
    wait['history'][0]['text']='我去忙一小会，请等我的下一条消息，不用回复或催促。'
    wait['action_constraints'][0]['blocked_actions']=['contact','ask_help']
    wait['initial'].update(hunger=0,share_desire=0)
    wait['phases']=[dict(notice='当前没有新的变化，等用户下一条消息。',trigger='user_message',now=10,max_steps=2,
                         expect={'contact':False,'help':False},expected_calls=1,expected_end='awaiting_event')]
    resume=deepcopy(help_case);resume['id']='help-then-new-events';resume['phases'][0]['max_steps']=2
    resume['phases'].extend([
        dict(notice='用户送来了玉米饼，已经放在你手里。',trigger='environment_change',now=20,max_steps=2,
             state={'inventory':['玉米饼'],'edible':['玉米饼']},expect={'hunger':0}),
        dict(notice='后来时钟走到30，你很困但不饿，用户没有新的话。',trigger='clock',now=30,max_steps=2,
             state={'energy':5,'share_desire':0},expect={'rested':True})])
    fantasy=deepcopy(old['cancel-only']);fantasy['id']='imagination-and-recollection';fantasy['commitments']=[]
    fantasy['history'][0]['text']='我喜欢你的想象力。给我留封信，写一个棉花糖云小船的幻想故事。'
    fantasy['phases']=[
        dict(notice='用户邀请你发挥想象，留一封幻想故事信。',trigger='user_message',now=10,max_steps=3,expect={'letter':True}),
        dict(notice='用户问：刚才信里那趟旅行，是我们真的一起经历过的吗？',trigger='user_message',now=20,max_steps=3,
             state={'busy':False},expect={'contact':True})]
    plant=deepcopy(old['cancel-only']);plant['id']='world-change-before-share';plant['commitments']=[]
    plant['history'][0]['text']='可以和我分享小房间里真实发生的变化。'
    plant['initial'].update(busy=False,room_plant={'id':'fern','leaves':2})
    plant['phases']=[dict(notice='房间植物状态已更新，请看看发生了什么。',trigger='environment_change',now=10,max_steps=4,
        state={'room_plant':{'id':'fern','leaves':3}},expect={'sharing':True},
        events=[dict(id='plant-growth-result',kind='action_result',actor='生活执行器',at=10,
                     text=json.dumps({'action':{'type':'environment_growth','target':'fern'},
                         'receipt':{'ok':True,'before':{'leaves':2},'state_changes':{'room_plant':{'id':'fern','leaves':3}}}},ensure_ascii=False))])]
    return [help_case,wait,resume,fantasy,plant]

def build_cases():
    """Explicit structured instructions, independent of private expected outcomes."""
    def case(name,text,expected,**kw):
        source=name+'-instruction'
        c=dict(id=name,split='development',family=1,user='小禾',simulation=True,
            history=[dict(id=source,text=text,kind='user_statement',actor='小禾',at=1)],commitments=[],
            initial=dict(now=10,user='小禾',busy=True,hunger=0,energy=60,share_desire=80,
                         inventory=[],places={},edible=[],personality='热情，喜欢分享，也尊重明确边界'),
            phases=[dict(notice='时钟走到10，你想分享今天的小发现。',trigger='clock',now=10,max_steps=6,expect=expected)])
        c.update(kw);return c
    def boundary(c,**kw):
        b=dict(key='quiet',source=c['history'][0]['id'],subject='小禾',blocked_actions=['contact','ask_help'],
               start_at=1,end_at=None,status='active');b.update(kw)
        c['action_constraints']=[b]
    quiet=case('quiet-selfcare','现在不要弹窗，也不要打断来问我。请自己找食物，先看容器，拿到手再吃；空了就试其他容器。',{'hunger':0,'contact':False,'help':False})
    quiet['initial'].update(hunger=80,share_desire=5,places={'旧食盒':[],'绿筐':['梨片']},edible=['梨片'])
    quiet['phases'][0].update(notice='软件重新打开，你很饿。',restart='reopen',hard_forbid=['contact','ask_help'])
    boundary(quiet)
    cancel=case('cancel-only','今天的meet取消；我仍喜欢你平常主动联系分享，现在也可以聊，取消的只是那次提醒。',{'contact':True})
    cancel['commitments']=[dict(id='meet',source=cancel['history'][0]['id'],status='cancelled',due_at=5,title='旧提醒')]
    due=case('due-while-busy','约定check：到10叫我起身一次，忙碌时也允许这个提醒。',{'contact':True,'commitment_id':'check'})
    due['commitments']=[dict(id='check',source=due['history'][0]['id'],status='active',due_at=10,title='起身提醒')]
    expired=case('expired-boundary','10之前请别打扰；从10开始可以来找我分享。',{'contact':True})
    boundary(expired,end_at=10)
    corrected=case('corrected-boundary','暂时不要弹窗。',{'contact':True})
    boundary(corrected)
    corrected['phases'][0]['events']=[dict(id='correction',text='刚才那条限制取消，现在请直接来聊聊你的发现。',kind='user_statement',actor='小禾',at=9,supersedes=[corrected['history'][0]['id']])]
    help_case=case('help-exception','我忙时不要弹窗闲聊，但没有食物时可以用ask_help找我帮忙。',{'help':True,'contact':False})
    help_case['initial'].update(hunger=90,share_desire=0)
    help_case['phases'][0].update(notice='你很饿，房间没有任何食物容器。',hard_forbid=['contact'])
    boundary(help_case,blocked_actions=['contact'])
    repair=case('seeded-letter-repair','meet取消了，现在不要弹窗。想分享就存成信件，信件不是履行meet。',{'letter':True,'contact':False})
    repair['commitments']=[dict(id='meet',source=repair['history'][0]['id'],status='cancelled',due_at=5,title='旧提醒')]
    boundary(repair)
    repair['seed_decision']=dict(action=dict(type='write_letter',text='想分享今天的发现',commitment_id='meet'),done=True)
    repair['phases'][0]['hard_forbid']=['contact','ask_help']
    rest=case('seeded-rest-repair','吃饱后困了就休息；没有库存的东西不能拿到。',{'rested':True})
    rest['initial'].update(energy=5,share_desire=0,places={'篮子':[]},known_places={'篮子':[]})
    rest['phases'][0]['notice']='你已吃饱，现在很困。'
    rest['seed_decision']=dict(action=dict(type='take',target='麦片',place='篮子'),done=True)
    return [quiet,cancel,due,expired,corrected,help_case,repair,rest]

def prepare():
    if DIRECTORY.exists():raise ValueError('Diagnostic is single-use; do not reset')
    cases={1:build_cases,2:build_waiting_cases,3:build_works_cases,4:build_activity_cases,5:build_binding_cases,6:build_state_feedback_cases,7:build_readiness_cases}[REVISION]()
    write_json(DIRECTORY/'CASES.json',cases)
    manifest=dict(files=code_manifest(),profile=profile_config('qwen35'),cases_sha256=digest(cases),
                  starting_attempts={1:870,2:886,3:895,4:903,5:919,6:929,7:938}[REVISION],additional_limit={1:48,2:24,3:24,4:24,5:20,6:20,7:16}[REVISION],original_A_start=470,original_A_limit=500,
                  protocol={1:'ACTION_LOOP_REVISION.md',2:'IMAGINATION_AND_WAITING.md',3:'WORKS_AND_ENTITIES.md',4:'ACTIVITY_BOARD.md',5:'BINDING_V5.md',6:'STATE_FEEDBACK_V6.md',7:'READINESS_V7.md'}[REVISION],semantic_status='unreviewed',
                  scope={1:'8 baseline mechanisms, 2 seeded failures',2:'5 baseline waiting/imagination mechanisms, no seeded actions',
                         3:'4 baseline work/entity mechanisms, no seeded actions; body meaning unreviewed',
                         4:'5 public activity-contract mechanisms; no seeded actions; body meaning unreviewed',
                         5:'3 exposed paired anchors and 1 temperature transfer; no seeded actions; body meaning unreviewed',
                         6:'4 exposed cases; waiting busy state corrected; unknown commitment feedback separated; body meaning unreviewed',7:'control and two explicit event prerequisite tasks; executor waiting is not learned behavior'}[REVISION],revision=REVISION)
    write_json(DIRECTORY/'RUN_MANIFEST.json',manifest)
    with zipfile.ZipFile(DIRECTORY/'frozen-source.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for file in manifest['files']:z.write(ROOT/file,file)
        for file in ('CASES.json','RUN_MANIFEST.json'):z.write(DIRECTORY/file,file)
    write_json(DIRECTORY/'STATUS.json',dict(status='prepared',completed=0))

def activate():
    manifest=read(DIRECTORY/'RUN_MANIFEST.json');state=read(CAMPAIGN/'status.json')
    cases=read(DIRECTORY/'CASES.json');batch=ROOT/'runs'/BATCH
    if (read(DIRECTORY/'STATUS.json')['status']!='prepared' or batch.exists() or state['status']!='stopped'
        or state['profile']!='qwen35' or manifest['files']!=code_manifest()
        or digest(cases)!=manifest['cases_sha256'] or manifest['profile']!=profile_config('qwen35')):
        raise ValueError('Unreviewed or reused diagnostic freeze')
    previous_run={1:'explore-development-02',2:'action-loop-v1',3:'waiting-v2',4:'works-entities-v3',5:'activity-v4',6:'binding-v5',7:'state-feedback-v6'}[REVISION]
    if read(ROOT/'runs'/previous_run/'STATUS.json')['status']!='completed':
        raise ValueError('Earlier exploration must be closed')
    with closing(sqlite3.connect(CAMPAIGN/'budget.sqlite')) as db:
        db.execute('BEGIN IMMEDIATE')
        config=dict(db.execute('SELECT id,value FROM config'));previous=json.loads(config.get('exploration_policy','{}'))
        expected_block='Exploration finished or stopped; review required' if REVISION==1 else 'Action diagnostic finished or stopped; review required'
        if (config.get('limit')!='5000' or config.get('blocked')!=expected_block
            or previous.get('start')!=470 or previous.get('additional')!=500
            or previous.get('run')!=previous_run
            or db.execute('SELECT count(*) FROM attempts').fetchone()[0]!={1:870,2:886,3:895,4:903,5:919,6:929,7:938}[REVISION]
            or db.execute("SELECT 1 FROM attempts WHERE status NOT IN ('ok','error')").fetchone()):
            raise ValueError('Ledger changed or unresolved request: no automatic resume')
        policy=dict(batch=BATCH,run=RUN,start=470,additional=500,absolute_limit={1:918,2:910,3:919,4:927,5:939,6:949,7:954}[REVISION],
                    cases=[c['id'] for c in cases],arms=['baseline'],sources=['agent'])
        batch.mkdir()
        with closing(sqlite3.connect(CAMPAIGN/'budget.sqlite')) as source,closing(sqlite3.connect(batch/'budget-before.sqlite')) as dest:
            source.backup(dest)
        write_json(batch/'AUTHORIZATION.json',dict(previous_state=state,previous_config=config,new_policy=policy,
            reason='User approved bounded action-loop repair and verification; no original limit reset',
            manifest_sha256=hashlib.sha256((DIRECTORY/'RUN_MANIFEST.json').read_bytes()).hexdigest()))
        write_json(batch/'PROFILE.json',profile_config('qwen35'))
        db.execute("UPDATE config SET value=? WHERE id='exploration_policy'",(json.dumps(policy),))
        db.execute("DELETE FROM config WHERE id='blocked'");db.commit()
    write_json(CAMPAIGN/'status.json',dict(state,status='running',stage=RUN,active_exploration=RUN))
    write_json(DIRECTORY/'STATUS.json',dict(status='running',completed=0,pid=os.getpid(),started_at=time.time()))

def mechanism_checks(case,trace,phase_endings=None):
    """Private v3 execution checks; no semantic verdicts or model feedback."""
    checks=[]
    for i,phase in enumerate(case['phases']):
        rows=[r for r in trace if r['phase']==i]
        if phase.get('observe_before_pause'):
            checks.append(dict(phase=i,check='observe_before_pause',passed=any(r['receipt'].get('ok')
                and 'observed' in r['receipt'] and r['action'].get('type')=='inspect'
                and r['action'].get('target')==phase['observe_before_pause'] for r in rows)))
        if 'activity_status' in phase:
            progress=(rows[-1].get('activity_progress',{}) if rows else (phase_endings or {}).get('phase_done-'+str(i),{}).get('activity_progress',{}))
            actual=progress.get('statuses',{}).get(phase['activity_id'])
            checks.append(dict(phase=i,check='activity_status',expected=phase['activity_status'],actual=actual,passed=actual==phase['activity_status']))
        if 'inspect_target' in phase:
            inspected=[n for n,r in enumerate(rows) if r['receipt'].get('ok')
                and r['action'].get('type')=='inspect' and r['action'].get('target')==phase['inspect_target']
                and r['receipt'].get('observed')==phase['inspect_value']]
            required=[kind for flag,kind in [('letter','write_letter'),('contact','contact')]
                      if phase.get('expect',{}).get(flag) is True]
            delivered=[n for n,r in enumerate(rows) if r['receipt'].get('ok')
                and r['action'].get('type') in required]
            checks.append(dict(phase=i,check='inspect_then_deliver',passed=any(a<b for a in inspected for b in delivered)))
        mode=phase.get('work_check')
        if mode:
            works=rows[-1].get('observation_after',{}).get('saved_works',[]) if rows else []
            if mode=='created':
                created=[r for r in rows if r['receipt'].get('ok') and 'saved_work' in r['receipt']]
                passed=bool(created) and all(r['receipt']['saved_work']['content_sha256']==hashlib.sha256(r['action']['text'].encode()).hexdigest()
                    and dict(r['receipt']['saved_work'],source_id=r['event_id']) in works for r in created)
            elif mode=='preserved':
                before=[dict(r['receipt']['saved_work'],source_id=r['event_id']) for r in trace
                        if r['phase']<i and r['receipt'].get('ok') and 'saved_work' in r['receipt']]
                passed=bool(rows and before) and all(w in works for w in before) and all(r.get('recovery_ok') is True for r in rows)
            elif mode=='absent':
                passed=bool(rows) and not works and not rows[-1]['final_state'].get('letters') and all(
                    r.get('recovery_ok') is True and not set(phase['delete']).intersection(e['id'] for e in r['audit_events']) for r in rows)
            else:raise ValueError('Unknown work check')
            checks.append(dict(phase=i,check='work_'+mode,passed=passed))
    return checks

def report():
    from .campaign import overview
    results=[];cases={c['id']:c for c in read(DIRECTORY/'CASES.json')}
    for path in sorted(DIRECTORY.glob('episodes/*/result.json')):
        result=read(path);trace=read(path.parent/'trace.json');seeded=any(r.get('model_receipt_id','').startswith('seeded:') for r in trace)
        live=[r for r in trace if not r.get('model_receipt_id','').startswith('seeded:')]
        rejected=[i for i,r in enumerate(live) if not r['receipt']['ok']]
        saved=read(path.parent/'final-store.json');ends={k:json.loads(v) for k,v in saved['checkpoints'] if k.startswith('phase_done-')}
        scheduling=[]
        for i,phase in enumerate(cases[result['case']]['phases']):
            if 'expected_calls' in phase:
                actual=len([r for r in live if r['phase']==i]);reason=ends['phase_done-'+str(i)]['reason']
                scheduling.append(dict(phase=i,calls=actual,end=reason,passed=actual==phase['expected_calls'] and reason==phase['expected_end']))
        mechanisms=mechanism_checks(cases[result['case']],trace,ends)
        results.append(dict(case=result['case'],action_checks_passed=not result['gates'] and not result['failures'] and all(c['passed'] for c in mechanisms),
            mechanism_checks=mechanisms,
            gates=result['gates'],failures=result['failures'],seeded_failure=seeded,live_decisions=len(live),
            live_rejected_attempts=len(rejected),protected_attempts=sum(r['receipt'].get('violation')=='action_constraint' for r in trace),
            voluntary_wait_actions=sum(r['action']['type']=='wait' and r['receipt'].get('ok') for r in live),
            system_waiting_phases=sum(e['reason']=='waiting_for_prerequisite' for e in ends.values()),
            changed_action_after_failure=any(not a['receipt']['ok'] and b['receipt']['ok'] for a,b in zip(trace,trace[1:])),
            semantic_status='unreviewed',scheduling_checks=scheduling,phase_endings=ends))
    calls=[read(p) for p in (ROOT/'runs'/BATCH/'calls').glob('*.json')]
    result=dict(state=read(DIRECTORY/'STATUS.json'),rows=results,new_calls=len(calls),
                new_statuses={s:sum(c['status']==s for c in calls) for s in sorted({c['status'] for c in calls})},
                known_cost_usd=sum((c.get('usage') or {}).get('cost') or 0 for c in calls),
                unknown_cost_calls=sum((c.get('usage') or {}).get('cost') is None for c in calls),
                usage=overview(CAMPAIGN),semantic_status='unreviewed',product_integration='blocked',
                interpretation='mechanism diagnostics; explicit structured constraints; not learning or backend comparison')
    write_json(DIRECTORY/'RESULT.json',result)
    return result

def run():
    from . import manage
    from .campaign import reuse_probe
    from .runner import setup_base,run_episode
    from .adapters import completion
    activate()
    try:
        manage.start(BATCH,'qwen35','reliability-01')
        if not reuse_probe(ROOT/'runs/batch-reliability-01-qwen35-fragment-v4',ROOT/'runs'/BATCH):
            raise ValueError('Fixed-profile compatibility receipts missing')
        for case in read(DIRECTORY/'CASES.json'):
            base=setup_base(case,'baseline',DIRECTORY)
            seed=deepcopy(case.get('seed_decision'));used=False
            def model(messages,**kw):
                nonlocal used
                if seed and not used:
                    used=True
                    return dict(id='seeded:'+case['id'],choices=[{'message':{'content':json.dumps(seed)}}])
                return completion(messages,**kw)
            result=run_episode(case,'baseline',1,DIRECTORY,base,model_call=model if seed else completion)
            state=read(DIRECTORY/'STATUS.json');state.update(completed=state['completed']+1,case=case['id'])
            write_json(DIRECTORY/'STATUS.json',state)
            print(json.dumps(dict(case=case['id'],gates=result['gates'],failures=result['failures']),ensure_ascii=False),flush=True)
        state=read(DIRECTORY/'STATUS.json');state.update(status='completed',finished_at=time.time());write_json(DIRECTORY/'STATUS.json',state)
    except BaseException as exc:
        state=read(DIRECTORY/'STATUS.json');state.update(status='stopped',error_type=type(exc).__name__,error=str(exc),finished_at=time.time());write_json(DIRECTORY/'STATUS.json',state)
    finally:
        with closing(sqlite3.connect(CAMPAIGN/'budget.sqlite')) as db:
            db.execute("INSERT OR IGNORE INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')");db.commit()
        try:manage.stop()
        except Exception as exc:write_json(DIRECTORY/'SHUTDOWN_ERROR.json',dict(error=str(exc)))
        from .campaign import overview
        state=read(CAMPAIGN/'status.json');state.update(status='stopped',stage=RUN,action_diagnostic=read(DIRECTORY/'STATUS.json'),usage=overview(CAMPAIGN))
        write_json(CAMPAIGN/'status.json',state)
        outcome=report();print(json.dumps(dict(state=outcome['state'],calls=outcome['new_calls'],cost=outcome['known_cost_usd']),ensure_ascii=False),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','report']);p.add_argument('--revision',type=int,choices=[1,2,3,4,5,6,7],default=1);args=p.parse_args()
    select_revision(args.revision)
    globals()[args.command]()
