"""Canonical, provenance-linked state; UI histories are never imported."""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from u1_resume.library import ConventionLibrary
from .understanding import Understandings


class Memory:
    @classmethod
    def readonly(cls, path):
        """Same schema and interfaces, with SQLite enforcing no test-time writes."""
        from growthlab.state import Store
        value=cls.__new__(cls)
        value.library=ConventionLibrary.__new__(ConventionLibrary)
        value.store=Store.__new__(Store)
        value.db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
        value.db.execute('PRAGMA query_only=ON')
        value.store.db=value.db
        value.library.store=value.store
        value.understandings=Understandings(value.library)
        return value

    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.library = ConventionLibrary(path)
        self.store = self.library.store
        self.db = self.store.db
        self.understandings = Understandings(self.library)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS kernel_turns(
          event_id TEXT PRIMARY KEY, channel TEXT NOT NULL, created TEXT NOT NULL,
          user_id TEXT REFERENCES records(id) ON DELETE SET NULL,
          reply_id TEXT REFERENCES records(id) ON DELETE SET NULL,
          phase TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS kernel_mirrors(digest TEXT PRIMARY KEY, event_id TEXT NOT NULL);
        ''')

    def close(self):
        self.store.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def begin_event(self, event):
        row = self.db.execute('SELECT phase FROM kernel_turns WHERE event_id=?', (event['event_id'],)).fetchone()
        if row:
            return None, self.cached(event['event_id'])
        source = self.append('experience', {'type': 'kernel_event', **event}, event['parents'])
        with self.db:
            # No user_id: an endogenous event is never an utterance or grant.
            self.db.execute('INSERT INTO kernel_turns VALUES (?,?,?,?,?,?)',
                            (event['event_id'], 'initiative', datetime.now().astimezone().isoformat(), None, None, 'running'))
        return source, None

    def begin(self, event_id, channel, text):
        row = self.db.execute('SELECT phase,reply_id FROM kernel_turns WHERE event_id=?', (event_id,)).fetchone()
        if row:
            if row[0] == 'done':
                value = self.record(row[1])
                return None, value.get('text', '该回合的内容已删除。') if value else '该回合的内容已删除。'
            # A crash may have occurred after a real-world side effect. Never replay it.
            return None, '这个回合曾被中断，我不会自动重放动作；请先确认当前游戏状态。'
        identity = self.library.utterance(text, session_id='ego:Moonlight', occurred_at=datetime.now().astimezone().isoformat())
        with self.db:
            self.db.execute('INSERT INTO kernel_turns VALUES (?,?,?,?,?,?)',
                            (event_id, channel, datetime.now().astimezone().isoformat(), identity, None, 'running'))
        return identity, None

    def record(self, identity):
        row = self.db.execute('SELECT body FROM records WHERE id=?', (identity,)).fetchone()
        return json.loads(row[0]) if row else None

    def context(self):
        result = []
        for event_id, channel, user_id, reply_id in self.db.execute(
                'SELECT event_id,channel,user_id,reply_id FROM kernel_turns ORDER BY rowid DESC LIMIT 20').fetchall()[::-1]:
            for identity, role in ((user_id, 'user'), (reply_id, 'assistant')):
                body = self.record(identity)
                if body:
                    text = body.get('utterance_text', body.get('text', ''))
                    result.append({'record_id': identity, 'channel': channel, 'role': role, 'text': text[:2500]})
        # Bound shared history before transport serialization; never import UI history.
        kept, size = [], 0
        for row in reversed(result):
            size += len(row['text'].encode('utf-8'))
            if size > 18000:
                break
            kept.append(row)
        return list(reversed(kept))

    def register_mirror(self, digest, event_id):
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO kernel_mirrors VALUES (?,?)', (digest, event_id))

    def mirror(self, digest):
        row = self.db.execute('SELECT event_id FROM kernel_mirrors WHERE digest=?', (digest,)).fetchone()
        return row[0] if row else None

    def cached(self, event_id):
        row = self.db.execute('SELECT reply_id,phase FROM kernel_turns WHERE event_id=?', (event_id,)).fetchone()
        if not row or row[1] != 'done':
            return '这个回合没有可回显的完成结果；我不会重复执行。'
        body = self.record(row[0])
        return body.get('text', '该回合的内容已删除。') if body else '该回合的内容已删除。'

    def goal(self):
        rows = self.library.rows('project')
        return next(({'record_id': r['record_id'], **r['body']} for r in reversed(rows)
                     if r['body'].get('type') == 'kernel_goal'), None)

    def recent_actions(self):
        rows=self.library.rows('experience')
        actions=[]
        for row in reversed(rows):
            if row['body'].get('type')!='action_receipt':continue
            value={'record_id':row['record_id'],**row['body']}
            if len(json.dumps([value,*actions],ensure_ascii=False).encode('utf-8'))>12000:break
            actions.insert(0,value)
            if len(actions)>=4:break
        return actions

    def update_goal(self, title, status, parents):
        old = self.goal()
        body = {'type': 'kernel_goal', 'title': title, 'goal_status': status}
        if old:
            identity = self.store.correct(old['record_id'], body, 'kernel_goal_transition')
            with self.db:
                self.db.executemany('INSERT OR IGNORE INTO deps VALUES (?,?,?)',
                                    [(identity, p, 'derived') for p in parents])
        else:
            self.store.put('project', body, 'kernel_goal_transition', personal=True, parents=parents)

    def propose(self, proposal, source_id):
        if not isinstance(proposal, dict) or set(proposal) != {'trigger', 'meaning', 'replaces'}:
            raise ValueError('convention_schema')
        text = proposal['trigger']
        if not isinstance(text, str) or not 1 <= len(text) <= 100:
            raise ValueError('convention_trigger')
        trigger = {'kind': 'utterance', 'text': text, 'weekday': -1, 'after': '', 'event': ''}
        match = re.fullmatch(r'周([一二三四五六日天])([0-2]\d:[0-5]\d)以后上线', text.replace(' ', ''))
        if match:
            trigger.update(kind='situation', weekday='一二三四五六日'.index(match[1].replace('天', '日')),
                           after=match[2], event='login')
        return self.library.propose({**proposal, 'trigger': trigger, 'source_ids': [source_id]}, allowed_ids=[source_id])

    def append(self, kind, body, parents):
        return self.store.put(kind, body, 'shared_kernel', personal=True, parents=list(dict.fromkeys(parents)))

    def finish(self, event_id, text, parents):
        reply = self.append('reflection', {'type': 'kernel_reply', 'text': text}, parents)
        with self.db:
            self.db.execute("UPDATE kernel_turns SET reply_id=?,phase='done' WHERE event_id=?", (reply, event_id))

    def forget(self, card_id):
        return self.library.forget(card_id)

    def mark_interrupted(self):
        with self.db:
            self.db.execute("UPDATE kernel_turns SET phase='interrupted' WHERE phase='running'")
