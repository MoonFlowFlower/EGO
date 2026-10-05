"""Plain-language understanding on the canonical owner records/deps tables.

Checks establish provenance, not the semantic truth of a model inference.
Time/weekday/clock conditions stay in the original natural language.
"""
import json
from datetime import datetime


class Understandings:
    def __init__(self, library):
        self.library, self.store = library, library.store
        self.db = self.store.db

    def active(self):
        return [{'record_id': row['record_id'], **row['body']}
                for row in self.library.rows('preference')
                if row['body'].get('type') == 'understanding']

    def propose(self, value):
        keys = {'operation','record_id','text','source_ids','conditions',
                'open_questions','update_source_ids','update_quote'}
        if not isinstance(value, dict) or set(value) != keys:
            raise ValueError('understanding_schema')
        if value['operation'] not in ('add','update','invalidate'):
            raise ValueError('understanding_operation')
        if not isinstance(value['text'], str) or not 1 <= len(value['text'].strip()) <= 500:
            raise ValueError('understanding_text')
        conditions = value['conditions']
        if (not isinstance(conditions, dict) or set(conditions) != {'when','who'}
                or not all(isinstance(v,str) and 0 < len(v) <= 300 for v in conditions.values())):
            raise ValueError('conditions_keep_natural_language')
        questions = value['open_questions']
        if not isinstance(questions,list) or not all(isinstance(v,str) and 0 < len(v) <= 300 for v in questions):
            raise ValueError('open_questions_schema')
        sources = {row['utterance_id']: row for row in self.library.sources()}
        ids = value['source_ids']
        if not isinstance(ids,list) or not ids or not all(isinstance(i,str) for i in ids) or len(set(ids)) != len(ids):
            raise ValueError('source_ids_schema')
        if not set(ids) <= sources.keys():
            raise ValueError('missing_utterance')
        old = {row['record_id']:row for row in self.active()}.get(value['record_id'])
        if value['operation'] == 'add':
            if value['record_id'] is not None or value['update_source_ids'] or value['update_quote']:
                raise ValueError('add_has_update_fields')
        else:
            if old is None:
                raise ValueError('replacement_not_active')
            updated = value['update_source_ids']
            quote = value['update_quote']
            if (not isinstance(updated,list) or not updated or not all(isinstance(i,str) for i in updated)
                    or not set(updated) <= set(ids) or set(updated) & set(old['source_ids'])
                    or not isinstance(quote,str) or not quote.strip()
                    or not any(quote in sources[i]['utterance_text'] for i in updated)):
                raise ValueError('update_evidence_requires_new_quoted_utterance')
            try:
                times={i:datetime.fromisoformat(sources[i]['occurred_at']) for i in set(old['source_ids'])|set(updated)}
                if any(t.tzinfo is None for t in times.values()): raise ValueError('timezone_required')
                latest=max(times[i] for i in old['source_ids'])
            except (ValueError,KeyError,TypeError):
                raise ValueError('update_evidence_time_unavailable') from None
            if any(times[i] <= latest for i in updated):
                raise ValueError('update_evidence_not_later')
        body = {k:value[k] for k in ('text','source_ids','conditions','open_questions')}
        body['type'] = 'understanding'
        if old:
            identity = self.store.correct(old['record_id'], body, 'model_understanding_revision')
            with self.db:
                self.db.executemany('INSERT OR IGNORE INTO deps VALUES (?,?,?)', [(identity,i,'derived') for i in ids])
                if value['operation'] == 'invalidate':
                    self.db.execute("UPDATE records SET status='invalidated' WHERE id=?", (identity,))
            return identity
        return self.store.put('preference',body,'model_understanding',personal=True,parents=ids)

    def deletion_closure(self, source_ids):
        known = {r['utterance_id'] for r in self.library.sources()}
        if not source_ids or not set(source_ids) <= known:
            raise ValueError('missing_utterance')
        ids = set(source_ids)
        edges = list(self.db.execute('SELECT child,parent,relation FROM deps'))
        while True:
            extended = ids | {child for child,parent,_ in edges if parent in ids}
            extended |= {parent for child,parent,relation in edges if child in ids and relation == 'correction'}
            if ids == extended:
                return ids
            ids = extended

    def forget_sources(self, source_ids):
        ids = self.deletion_closure(source_ids)
        with self.db:
            self.db.executemany('DELETE FROM records WHERE id=?', [(i,) for i in ids])
        self.db.execute('VACUUM')
        return {'status':'deleted','removed_records':len(ids),'removed_ids':sorted(ids)}
