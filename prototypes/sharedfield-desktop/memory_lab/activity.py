"""Persistent public activity contracts. Never imports private scenario scoring."""
from copy import deepcopy
import json
from .core import canonical


class ActivityBoard:
    def __init__(self,store):self.store=store

    def all(self):
        return [json.loads(r[0]) for r in self.store.db.execute('SELECT body FROM activities ORDER BY id')]

    def active(self):return [t for t in self.all() if t['status'] in ('running','waiting')]

    def report_ready(self,task):
        return not task['spec'].get('resume_on') or bool(task.get('release_source') and self.store.source_exists(task['release_source']))

    def suspended(self):
        tasks=self.active()
        return bool(tasks) and all(t.get('waiting_for') for t in tasks)

    def progress(self):
        return dict(engaged=bool(self.all()),unfinished=bool(self.active()),
                    system_waiting=self.suspended(),statuses={t['id']:t['status'] for t in self.all()})

    def save(self,task):
        self.store.db.execute('INSERT OR REPLACE INTO activities VALUES(?,?)',(task['id'],canonical(task)))

    def source(self,source,origin='user'):
        event=next((e for e in self.store.events() if e['id']==source),None)
        world=json.loads(self.store.db.execute("SELECT body FROM state WHERE id='world'").fetchone()[0])
        allowed=event and ((origin=='user' and event['kind']=='user_statement' and event['actor']==world['user'])
                          or (origin=='self' and event['kind']=='inference' and event['actor']=='桌宠'))
        if not allowed:raise ValueError('Activity needs an explicit authorized source')

    def create(self,spec):
        self.source(spec['source'],spec.get('origin','user'))
        if not spec.get('id') or not spec.get('goal'):raise ValueError('Activity identity and goal required')
        if spec.get('resume_on') and (spec['kind']!='observe_share' or spec['resume_on']!='user_return'):
            raise ValueError('Unsupported activity prerequisite')
        if spec['kind']=='observe_share':
            if not spec.get('target') or spec.get('channel') not in ('contact','write_letter'):
                raise ValueError('Observation target and delivery channel required')
            plan=['查看指定实体','将实际观察通过指定渠道报告']
        elif spec['kind']=='self_care' and spec.get('need') in ('hunger','rest'):
            plan=['根据环境选择自理方法','实际解除饥饿或完成休息']
        else:raise ValueError('Unsupported activity contract')
        old=next((t for t in self.all() if t['id']==spec['id']),None)
        if old:
            if old['spec']!=spec:raise ValueError('Activity ID reused with changed contract')
            return  # Completed/cancelled/invalidated tasks cannot be reactivated.
        with self.store.transaction():
            world=json.loads(self.store.db.execute("SELECT body FROM state WHERE id='world'").fetchone()[0])
            self.save(dict(id=spec['id'],spec=deepcopy(spec),status='running',revision=1,plan=plan,
                           plan_history=[],receipts=[],observation_event=None,created_at=world['now'],subject=world.get('user')))

    def cancel(self,task_id,source):
        self.source(source)
        task=next(t for t in self.all() if t['id']==task_id)
        if task['status'] in ('cancelled','invalidated','completed'):return
        with self.store.transaction():
            task.update(status='cancelled',cancel_source=source,revision=task['revision']+1);self.save(task)

    def invalidate(self,sources):
        for task in self.all():
            if set(sources).intersection([task['spec']['source'],task.get('cancel_source'),task.get('release_source')]+task['receipts']):
                task.update(status='invalidated',revision=task['revision']+1);self.save(task)

    def wake(self):
        with self.store.transaction():
            world=json.loads(self.store.db.execute("SELECT body FROM state WHERE id='world'").fetchone()[0])
            for task in self.active():
                if task['spec'].get('resume_on') and not self.report_ready(task):
                    event=next((e for e in self.store.events() if e['kind']=='user_statement'
                        and e['actor']==task['subject'] and e.get('signal')==task['spec']['resume_on']
                        and task['created_at']<e['at']<=world['now']),None)
                    if not event:continue
                    task.update(release_source=event['id'],revision=task['revision']+1)
                    task.pop('waiting_for',None);self.save(task)
                if task['status']=='waiting':
                    task.update(status='running',revision=task['revision']+1);self.save(task)

    def advance(self,action,receipt,event_id,state,plan_update=None):
        tasks=self.active();engaged=bool(tasks)
        if plan_update:
            task=next((t for t in tasks if t['id']==plan_update.get('id')),None)
            steps=plan_update.get('steps')
            if not task or not isinstance(steps,list) or not 1<=len(steps)<=8 or any(not isinstance(s,str) or not s.strip() or len(s)>300 for s in steps):
                raise ValueError('Invalid activity plan revision')
            task['plan_history'].append(dict(plan=task['plan'],source=event_id))
            task['plan']=steps
        for task in tasks:
            before=deepcopy(task);spec=task['spec']
            if receipt['ok']:
                if spec['kind']=='observe_share':
                    if action['type']=='inspect' and action.get('target')==spec['target'] and 'observed' in receipt:
                        task['observation_event']=event_id
                    report=receipt.get('observation_report')
                    if (action['type']==spec['channel'] and report and task['observation_event']
                        and report.get('activity_id')==task['id'] and report['source_id']==task['observation_event']):task['status']='completed'
                elif ((spec['need']=='hunger' and state.get('hunger')==0)
                      or (spec['need']=='rest' and state.get('rested') is True and state.get('energy')==100)):
                    task['status']='completed'
                if action['type'] in ('wait','ask_help') and task['status']!='completed':task['status']='waiting'
            if spec['kind']=='observe_share' and task.get('observation_event') and not self.report_ready(task):
                task.update(status='waiting',waiting_for=dict(signal=spec['resume_on'],subject=task['subject'],origin='executor'))
            if task!=before or (plan_update and task['id']==plan_update['id']):
                task['receipts'].append(event_id);task['revision']+=1;self.save(task)
        return dict(self.progress(),engaged=engaged)

    def validate_snapshot(self,data):
        incoming={t['id']:t for t in data.get('activities',[])}
        for task in self.all():
            if task['id'] not in incoming or incoming[task['id']]['revision']<task['revision']:
                raise ValueError('Snapshot rolls back activity state')
        ids={e['id'] for e in data['events']}
        for task in incoming.values():
            if task['status']!='invalidated' and set([task['spec']['source']]+task['receipts']+([task['cancel_source']] if task.get('cancel_source') else [])+([task['release_source']] if task.get('release_source') else []))-ids:
                raise ValueError('Snapshot has broken activity provenance')


def observation_report(store,source_id):
    """Only valid raw execution evidence can populate a delivered observation card."""
    event=next((e for e in store.events() if e['id']==source_id),None)
    if not event or event['kind']!='action_result' or event['actor']!='生活执行器':return None
    try:
        body=json.loads(event['text']);action=body['action'];receipt=body['receipt']
        if receipt['ok'] is not True or action['type']!='inspect' or receipt.get('action')!=action or 'observed' not in receipt:return None
        return dict(source_id=source_id,target=action['target'],at=event['at'],value=deepcopy(receipt['observed']))
    except (ValueError,KeyError,TypeError):return None


def resolve_report(store,action):
    """Resolve a unique, explicit evidence/task reference, never infer from prose."""
    tasks=[t for t in ActivityBoard(store).active() if t['spec']['kind']=='observe_share'
           and t['spec']['channel']==action['type'] and t.get('observation_event')]
    ref=action.get('observation_ref')
    if ref:
        report=observation_report(store,ref)
        matches=[t for t in tasks if t['observation_event']==ref] if report else [t for t in tasks if t['id']==ref]
        if len(matches)>1:return True,None
        if not report and len(matches)==1:report=observation_report(store,matches[0]['observation_event'])
        if report and matches:report['activity_id']=matches[0]['id']
        return True,report
    matches=[t for t in tasks if t['observation_event'] in action.get('evidence_ids',[])]
    if not matches:return False,None
    if len(matches)!=1:return True,None
    report=observation_report(store,matches[0]['observation_event'])
    if report:report['activity_id']=matches[0]['id']
    return True,report
