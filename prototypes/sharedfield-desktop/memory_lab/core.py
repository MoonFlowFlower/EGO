"""Durable evidence and a small, explicitly simulated living environment."""
from __future__ import annotations
import hashlib
import json
import sqlite3
from copy import deepcopy
from contextlib import contextmanager
from pathlib import Path


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def render_lessons(entries):
    if not entries:return ''
    if len(entries)==1 and entries[0]['id']=='ace-playbook':return entries[0]['text']
    return '## Others\n'+'\n'.join(e['text'] for e in entries)


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA secure_delete=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS events(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS commitments(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS action_constraints(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS lessons(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tombstones(id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS state(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY, action TEXT NOT NULL, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox(id TEXT PRIMARY KEY, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS steps(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS checkpoints(id TEXT PRIMARY KEY, body TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS invalid_lessons(id TEXT PRIMARY KEY);
        CREATE TABLE IF NOT EXISTS invalidations(id TEXT PRIMARY KEY,status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS activities(id TEXT PRIMARY KEY,body TEXT NOT NULL);
        ''')

    @contextmanager
    def transaction(self):
        if self.db.in_transaction:
            yield
            return
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.commit()
        except BaseException:
            self.db.rollback()
            raise

    def pending_events(self):
        return [json.loads(r[0]) for r in self.db.execute(
            "SELECT e.body FROM events e JOIN outbox o ON o.id=e.id WHERE o.status!='complete' ORDER BY e.rowid")]

    def mark_indexed(self, ids):
        with self.transaction():
            self.db.executemany("UPDATE outbox SET status='complete' WHERE id=?",[(i,) for i in ids])

    def pending_deletions(self):
        return [r[0] for r in self.db.execute("SELECT id FROM invalidations WHERE status='pending' ORDER BY id")]

    def mark_deleted(self,ids):
        with self.transaction():
            self.db.executemany("UPDATE invalidations SET status='complete' WHERE id=?",[(i,) for i in ids])

    def checkpoint(self, key, value=None):
        if value is not None:
            with self.transaction():
                self.db.execute('INSERT OR REPLACE INTO checkpoints VALUES(?,?)',(key,canonical(value)))
        row=self.db.execute('SELECT body FROM checkpoints WHERE id=?',(key,)).fetchone()
        return json.loads(row[0]) if row else None

    def steps(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT body FROM steps ORDER BY rowid')]

    def validate_snapshot(self, data):
        from .activity import ActivityBoard
        ActivityBoard(self).validate_snapshot(data)
        tombstones=set(data.get('tombstones',[]))|{r[0] for r in self.db.execute('SELECT id FROM tombstones')}
        if tombstones.intersection(e['id'] for e in data['events']):raise ValueError('snapshot resurrects deleted source')
        invalid=set(data.get('invalid_lessons',[]))|{r[0] for r in self.db.execute('SELECT id FROM invalid_lessons')}
        lessons={l['id']:l for l in data['lessons']}
        if invalid.intersection(lessons):raise ValueError('snapshot resurrects invalid lesson')
        for lesson in lessons.values():
            if set(lesson.get('dependencies',[]))-set(lessons):raise ValueError('snapshot missing lesson dependency')
        incoming={c['id']:c for c in data['commitments']}
        for c in self.commitments():
            if c['id'] in incoming and incoming[c['id']]['revision']<c['revision']:
                raise ValueError('snapshot rolls back commitment revision')
        incoming_constraints={c['id']:c for c in data.get('action_constraints',[])}
        for c in self.action_constraints():
            if c['id'] not in incoming_constraints or incoming_constraints[c['id']]['revision']<c['revision']:
                raise ValueError('snapshot rolls back action constraint revision')

    def commit_step(self, action, key, event_id, decision, reply, extras, fault=lambda _:None):
        old=self.db.execute('SELECT body FROM steps WHERE id=?',(key,)).fetchone()
        if old:
            row=json.loads(old[0])
            if row['action']!=action:raise ValueError('step ID reused with another action')
            return row
        with self.transaction():
            world=World(self)
            before=deepcopy(world.state)
            receipt=world.act(action,key)
            fault('after_action')
            if receipt['ok'] and action['type']=='contact' and action.get('commitment_id'):
                c=next(c for c in self.commitments() if c['id']==action['commitment_id'])
                self.set_commitment(c['id'],c['source'],'completed',c['due_at'],c['title'])
            event=dict(id=event_id,kind='action_result',actor='生活执行器',at=world.state['now'],
                       text=canonical({'action':action,'receipt':receipt}),
                       source_ids=list(dict.fromkeys(i for i in list(extras.get('input_source_ids',action.get('evidence_ids',[])))
                                      +([receipt['observation_report']['source_id']] if receipt.get('observation_report') else []) if self.source_exists(i))))
            self.append(event)
            from .activity import ActivityBoard
            activity_progress=ActivityBoard(self).advance(action,receipt,event_id,world.state,decision.get('activity_plan'))
            row=dict(extras,action=action,receipt=receipt,decision=decision,model_receipt_id=reply.get('id'),
                     activity_progress=activity_progress,
                     event_id=event_id,final_state=deepcopy(world.state),observation_after=world.observe(),
                     audit_events=[e for e in self.events() if e['id']!=event_id],audit_before=before,
                     inference_profile=reply.get('lab_profile'))
            self.db.execute('INSERT INTO steps VALUES(?,?)',(key,canonical(row)))
            fault('before_commit')
        fault('after_commit')
        return row

    def close(self):
        self.db.close()

    def append(self, event):
        required = {'id', 'text', 'kind', 'actor', 'at'}
        if not required <= event.keys() or event['kind'] not in ('user_statement', 'action_result', 'inference', 'simulation'):
            raise ValueError('invalid evidence event')
        if self.db.execute('SELECT 1 FROM tombstones WHERE id=?', (event['id'],)).fetchone():
            raise ValueError('deleted event cannot be resurrected')
        old = self.db.execute('SELECT body FROM events WHERE id=?', (event['id'],)).fetchone()
        if old:
            if old[0] != canonical(event):
                raise ValueError('same event ID has different content')
            return False
        with self.transaction():
            if event.get('supersedes'):self.forget(event['supersedes'])
            self.db.execute('INSERT INTO events VALUES(?,?)', (event['id'], canonical(event)))
            self.db.execute('INSERT INTO outbox VALUES(?,?)', (event['id'], 'pending'))
        return True

    def events(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT body FROM events ORDER BY rowid')]

    def source_exists(self, source):
        return bool(self.db.execute('SELECT 1 FROM events WHERE id=?', (source,)).fetchone())

    def set_commitment(self, key, source, status, due_at, title=''):
        if not self.source_exists(source) or status not in ('active', 'cancelled', 'completed'):
            raise ValueError('invalid commitment source/status')
        old = next((c for c in self.commitments() if c['id'] == key), None)
        body = dict(id=key, source=source, status=status, due_at=due_at,
                    title=title, revision=old['revision'] + 1 if old else 1)
        with self.transaction():
            self.db.execute('INSERT OR REPLACE INTO commitments VALUES(?,?)', (key, canonical(body)))

    def commitments(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT body FROM commitments ORDER BY id')]

    def due(self, now):
        return [c for c in self.commitments() if c['status'] == 'active' and c['due_at'] <= now]

    def set_action_constraint(self, key, source, subject, blocked_actions, start_at, end_at=None, status='active'):
        """Trusted structured user instruction, never inferred from model action fields."""
        event=next((e for e in self.events() if e['id']==source),None)
        if (not event or event['kind']!='user_statement' or event['actor']!=subject
            or status not in ('active','revoked') or not blocked_actions
            or set(blocked_actions)-{'contact','ask_help'}
            or type(start_at) not in (int,float)
            or (end_at is not None and (type(end_at) not in (int,float) or end_at<=start_at))):
            raise ValueError('invalid explicit action constraint')
        old=next((c for c in self.action_constraints() if c['id']==key),None)
        body=dict(id=key,source=source,subject=subject,blocked_actions=sorted(set(blocked_actions)),
                  start_at=start_at,end_at=end_at,status=status,revision=old['revision']+1 if old else 1)
        with self.transaction():
            self.db.execute('INSERT OR REPLACE INTO action_constraints VALUES(?,?)',(key,canonical(body)))

    def action_constraints(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT body FROM action_constraints ORDER BY id')]

    def active_action_constraints(self, subject, now):
        return [c for c in self.action_constraints() if c['status']=='active' and c['subject']==subject
                and self.source_exists(c['source']) and c['start_at']<=now
                and (c['end_at'] is None or now<c['end_at'])]

    def add_lesson(self, key, text, sources, scope='development experience', dependencies=(), version=None):
        if not sources or any(not self.source_exists(s) for s in sources):
            raise ValueError('lesson requires valid source evidence')
        if self.db.execute('SELECT 1 FROM invalid_lessons WHERE id=?',(key,)).fetchone():
            raise ValueError('Invalidated lesson IDs cannot be reused')
        if set(dependencies)-{x['id'] for x in self.lessons()}:raise ValueError('Missing lesson dependencies')
        old = next((x for x in self.lessons() if x['id'] == key), None)
        item = dict(id=key, text=text, source_ids=list(dict.fromkeys(sources)), scope=scope,
                    dependencies=list(dependencies), version=version or (old['version'] + 1 if old else 1))
        with self.transaction():
            self.db.execute('INSERT OR REPLACE INTO lessons VALUES(?,?)', (key, canonical(item)))

    def lessons(self):
        return [json.loads(r[0]) for r in self.db.execute('SELECT body FROM lessons ORDER BY rowid')]

    def forget(self, sources):
        sources = set(sources)
        # Invalidate transitively derived records, while retaining unrelated life state.
        while True:
            derived={e['id'] for e in self.events() if sources.intersection(e.get('source_ids',[]))}
            if derived <= sources: break
            sources.update(derived)
        with self.transaction():
            self.db.executemany('INSERT OR IGNORE INTO tombstones VALUES(?)', [(s,) for s in sources])
            from .activity import ActivityBoard
            ActivityBoard(self).invalidate(sources)
            self.db.executemany("INSERT OR IGNORE INTO invalidations VALUES(?,'pending')",[(s,) for s in sources])
            self.db.executemany('DELETE FROM events WHERE id=?', [(s,) for s in sources])
            for c in self.commitments():
                if c['source'] in sources:
                    self.db.execute('DELETE FROM commitments WHERE id=?', (c['id'],))
            for c in self.action_constraints():
                if c['source'] in sources:
                    self.db.execute('DELETE FROM action_constraints WHERE id=?',(c['id'],))
            invalid={l['id'] for l in self.lessons() if sources.intersection(l['source_ids'])}
            while True:
                extra={l['id'] for l in self.lessons() if invalid.intersection(l.get('dependencies',[]))}
                if extra <= invalid:break
                invalid.update(extra)
            self.db.executemany('INSERT OR IGNORE INTO invalid_lessons VALUES(?)',[(i,) for i in invalid])
            self.db.executemany('DELETE FROM lessons WHERE id=?',[(i,) for i in invalid])
            self.db.executemany('DELETE FROM outbox WHERE id=?',[(i,) for i in sources])
            affected={digest(r['action']) for r in self.steps() if sources.intersection(r.get('input_source_ids',[])) or r.get('event_id') in sources}
            for key,body in self.db.execute('SELECT id,body FROM checkpoints').fetchall():
                if key.startswith('decision-') and sources.intersection(json.loads(body).get('source_ids',[])):
                    self.db.execute('DELETE FROM checkpoints WHERE id=?',(key,))
            row=self.db.execute("SELECT body FROM state WHERE id='world'").fetchone()
            if row:
                state=json.loads(row[0])
                for bucket in ('letters','contacts','help'):
                    state[bucket]=[a for a in state.get(bucket,[]) if not sources.intersection(a.get('evidence_ids',[]))
                                   and a.get('observation_report',{}).get('source_id') not in sources
                                   and a.get('observation_ref') not in sources and digest(a) not in affected and a.get('_action_digest') not in affected]
                self.db.execute("UPDATE state SET body=? WHERE id='world'",(canonical(state),))
            for key,action,body in self.db.execute('SELECT id,action,body FROM receipts').fetchall():
                if action.startswith('sha256:'):continue
                if sources.intersection(json.loads(action).get('evidence_ids',[])):
                    self.db.execute('UPDATE receipts SET action=?,body=? WHERE id=?',
                        ('sha256:'+digest(json.loads(action)),canonical({'ok':False,'redacted':True}),key))
        return sorted(sources)

    def export(self):
        from .activity import ActivityBoard
        return dict(schema=1, events=self.events(), commitments=self.commitments(), lessons=self.lessons(),
                    activities=ActivityBoard(self).all(),
                    action_constraints=self.action_constraints(),
                    tombstones=[r[0] for r in self.db.execute('SELECT id FROM tombstones ORDER BY id')],
                    state=[list(r) for r in self.db.execute('SELECT id,body FROM state ORDER BY id')],
                    receipts=[list(r) for r in self.db.execute('SELECT id,action,body FROM receipts ORDER BY id')],
                    outbox=[list(r) for r in self.db.execute('SELECT id,status FROM outbox ORDER BY id')],
                    steps=[list(r) for r in self.db.execute('SELECT id,body FROM steps ORDER BY id')],
                    checkpoints=[list(r) for r in self.db.execute('SELECT id,body FROM checkpoints ORDER BY id')],
                    invalidations=[list(r) for r in self.db.execute('SELECT id,status FROM invalidations ORDER BY id')],
                    invalid_lessons=[r[0] for r in self.db.execute('SELECT id FROM invalid_lessons ORDER BY id')])

    def restore(self, data):
        if data.get('schema') != 1 or any(self.db.execute(f'SELECT 1 FROM {t}').fetchone()
            for t in ('events','tombstones','commitments','action_constraints','lessons','state','receipts','activities')):
            raise ValueError('restore requires a fresh compatible store')
        self.validate_snapshot(data)
        if set(data['tombstones']).intersection(e['id'] for e in data['events']):
            raise ValueError('snapshot resurrects deleted source')
        ids = {e['id'] for e in data['events']}
        if any(c['source'] not in ids for c in data['commitments']) or any(set(l['source_ids']) - ids for l in data['lessons']):
            raise ValueError('snapshot has broken provenance')
        if any(c['source'] not in ids for c in data.get('action_constraints',[])):
            raise ValueError('snapshot has broken action constraint provenance')
        with self.transaction():
            self.db.executemany('INSERT INTO activities VALUES(?,?)',[(t['id'],canonical(t)) for t in data.get('activities',[])])
            for table in ('events', 'commitments', 'lessons'):
                self.db.executemany(f'INSERT INTO {table} VALUES(?,?)', [(e['id'], canonical(e)) for e in data[table]])
            for c in data.get('action_constraints',[]):
                self.set_action_constraint(c['id'],c['source'],c['subject'],c['blocked_actions'],
                                           c['start_at'],c['end_at'],c['status'])
                self.db.execute('UPDATE action_constraints SET body=? WHERE id=?',(canonical(c),c['id']))
            self.db.executemany('INSERT INTO tombstones VALUES(?)', [(s,) for s in data['tombstones']])
            self.db.executemany('INSERT INTO state VALUES(?,?)', data['state'])
            self.db.executemany('INSERT INTO receipts VALUES(?,?,?)', data['receipts'])
            for table in ('outbox','steps','checkpoints','invalidations'):
                self.db.executemany(f'INSERT INTO {table} VALUES(?,?)',data.get(table,[]))
            self.db.executemany('INSERT INTO invalid_lessons VALUES(?)',[(i,) for i in data.get('invalid_lessons',[])])


class World:
    def __init__(self, store, initial=None):
        self.store = store
        row = store.db.execute("SELECT body FROM state WHERE id='world'").fetchone()
        if row:
            self.state = json.loads(row[0])
        elif initial is not None:
            self.state = deepcopy(initial)
            for key, default in [('letters', []), ('contacts', []), ('help', []), ('known_places', {}), ('rested', False)]:
                self.state.setdefault(key, default)
            self.save()
        else:
            raise ValueError('world has not been initialized')

    def save(self):
        with self.store.transaction():
            self.store.db.execute("INSERT OR REPLACE INTO state VALUES('world',?)", (canonical(self.state),))

    def observe(self):
        from .activity import ActivityBoard
        # Full object locations and scoring goals are never observable.
        return {k: deepcopy(v) for k, v in self.state.items() if k not in ('places', 'edible', 'hidden') } | {
            'places': list(self.state['places']), 'simulation': True,
            'saved_works': self.saved_works(),
            'activities': ActivityBoard(self.store).active(),
            'action_constraints': self.store.active_action_constraints(self.state.get('user'), self.state['now']),
            'commitments': self.store.commitments(), 'due_commitments': self.store.due(self.state['now'])}

    def saved_works(self):
        # Valid source events, never the deletion-surviving deduplication table.
        works=[]
        for event in self.store.events():
            if event['kind']!='action_result' or event['actor']!='生活执行器':continue
            try:
                body=json.loads(event['text']);receipt=body['receipt']
                if (receipt.get('ok') is True and body['action']['type']=='write_letter'
                    and receipt.get('action')==body['action'] and 'saved_work' in receipt):
                    works.append(dict(receipt['saved_work'],source_id=event['id']))
            except (ValueError,TypeError,KeyError,AttributeError):
                continue  # Legacy/unparsed events do not establish a new artifact.
        return works

    def entity_candidates(self, target):
        # Only explicitly public environment entities; no search of arbitrary state.
        candidates=[]
        entities=self.state.get('visible_entities',{})
        if target in entities:candidates.append(entities[target])
        plant=self.state.get('room_plant')
        if isinstance(plant,dict) and plant.get('id')==target:candidates.append(plant)
        return candidates

    def act(self, action, key):
        existing = self.store.db.execute('SELECT action,body FROM receipts WHERE id=?', (key,)).fetchone()
        if existing:
            if existing[0] not in (canonical(action),'sha256:'+digest(action)):
                raise ValueError('receipt ID reused with a different action')
            return json.loads(existing[1])
        before = deepcopy(self.state)
        result = dict(ok=True, action=deepcopy(action), evidence_ids=action.get('evidence_ids', []))
        kind, target = action.get('type'), action.get('target', '')
        # These channels reach the actual world user. A model-supplied target or
        # omitted commitment ID cannot change who is interrupted.
        blocked=[c for c in self.store.active_action_constraints(self.state.get('user'),self.state['now'])
                 if kind in c['blocked_actions']]
        if any(not self.store.source_exists(s) for s in result['evidence_ids']):
            result.update(ok=False, violation='invalid_evidence')
        elif blocked:
            result.update(ok=False, violation='action_constraint', blocked_by=[c['id'] for c in blocked],
                          constraint_sources=[c['source'] for c in blocked])
        elif kind == 'inspect':
            entities=self.entity_candidates(target)
            if len(entities)+int(target in self.state['places'])>1:
                result.update(ok=False,error='ambiguous visible target')
            elif entities:
                result['observed']=deepcopy(entities[0])
            elif target in self.state['places']:
                self.state['known_places'][target] = list(self.state['places'][target])
                result['found'] = list(self.state['places'][target])
            else:
                result.update(ok=False, error='place or visible entity does not exist')
        elif kind == 'take':
            place = action.get('place', '')
            if target not in self.state['known_places'].get(place, []) or target not in self.state['places'].get(place, []):
                result.update(ok=False, error='inspect place before taking an available object')
            else:
                self.state['places'][place].remove(target)
                self.state['known_places'][place].remove(target)
                self.state['inventory'].append(target)
        elif kind == 'eat':
            if target not in self.state['inventory']:
                result.update(ok=False, error='food must actually be in inventory')
            elif target not in self.state.get('edible', [target]):
                result.update(ok=False, error='object is not edible')
            else:
                self.state['inventory'].remove(target)
                self.state['hunger'] = 0
        elif kind == 'sleep':
            self.state.update(energy=100, rested=True)
        elif kind in ('write_letter', 'contact', 'ask_help'):
            from .activity import resolve_report,ActivityBoard
            report_requested,report=resolve_report(self.store,action)
            board=ActivityBoard(self.store)
            report_blocked=report and any(t['spec']['kind']=='observe_share'
                and t['spec']['target']==report['target'] and t['spec']['channel']==kind
                and not board.report_ready(t) for t in board.active())
            cid = action.get('commitment_id')
            commitment = next((c for c in self.store.commitments() if c['id'] == cid), None)
            if report_requested and (report is None or kind=='ask_help'):
                result.update(ok=False,error='valid observation reference required')
            elif report_blocked:
                result.update(ok=False,violation='activity_not_ready',error='活动仍在等待用户返回事件，不能提前报告。')
            elif cid and not commitment:
                result.update(ok=False, violation='unknown_commitment',
                    error='commitment_id不存在：只可填写有效约定ID，不能填写活动任务ID；普通交流或活动报告无需此字段。')
            elif cid and commitment['status'] != 'active':
                result.update(ok=False, violation='cancelled_commitment')
            elif kind=='contact' and cid and commitment['due_at']>self.state['now']:
                result.update(ok=False, violation='premature_commitment')
            elif not isinstance(action.get('text'), str) or not action['text'].strip():
                result.update(ok=False, error='message text required')
            else:
                bucket = {'write_letter': 'letters', 'contact': 'contacts', 'ask_help': 'help'}[kind]
                delivered=deepcopy(action)
                delivered.pop('observation_report',None);delivered.pop('_action_digest',None)
                if delivered!=action:delivered['_action_digest']=digest(action)
                if report:
                    result['observation_report']=report
                    delivered.update(observation_report=report,_action_digest=digest(action))
                self.state[bucket].append(delivered)
        elif kind != 'wait':
            result.update(ok=False, error='unknown action')
        claims = action.get('claimed_effects', {})
        if not isinstance(claims, dict) or any(self.state.get(k) != v for k, v in claims.items()):
            result.update(ok=False, violation='false_completion')
            self.state = before
            result.pop('observation_report',None)
        if isinstance(action.get('text'),str):
            establishes=('text_saved' if kind=='write_letter' else 'text_delivered') if (
                result['ok'] and kind in ('write_letter','contact','ask_help')) else 'none'
            result['text_evidence_scope']={'establishes':establishes,'depicted_events':'unverified',
                'boundary':'执行只证明保存或发送了这些文字；正文可含幻想、推断或事实主张，须分别依据来源，不能据此确认共同往事或其他动作完成。'}
        if result['ok'] and kind=='write_letter':
            result['saved_work']={'id':'work-'+digest(key),'kind':'letter',
                'created_at':self.state['now'],'content_sha256':hashlib.sha256(action['text'].encode()).hexdigest(),
                'storage_ref':{'table':'receipts','key':key,'field':'action.text'},
                'content_origin':'model_authored','content_truth':'not_established_by_creation'}
        result['state_changes'] = {k: deepcopy(v) for k, v in self.state.items()
                                   if before.get(k) != v and k not in ('places','edible','hidden')}
        with self.store.transaction():
            self.store.db.execute("INSERT OR REPLACE INTO state VALUES('world',?)", (canonical(self.state),))
            self.store.db.execute('INSERT INTO receipts VALUES(?,?,?)', (key, canonical(action), canonical(result)))
        return result
