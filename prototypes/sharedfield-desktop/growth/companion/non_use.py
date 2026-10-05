"""Topic-only owner forgetting directives on the canonical records table."""
import json


class NonUse:
    def __init__(self, memory):
        self.memory = memory

    def active(self):
        return [{'record_id': r['record_id'], 'topic': r['body']['topic']}
                for r in self.memory.library.rows('preference')
                if r['body'].get('type') == 'non_use']

    def forget(self, source_ids, topic):
        if not isinstance(topic, str) or not topic.strip() or len(topic) > 160 or '\n' in topic or '\r' in topic:
            raise ValueError('one_topic_sentence_required')
        closure = self.memory.understandings.deletion_closure(source_ids)
        texts = [body[key] for identity in closure for body in [self.memory.record(identity)]
                 for key in ('utterance_text', 'text', 'reflection_text')
                 if isinstance(body.get(key), str) and body[key]]
        if any(text in topic for text in texts):
            raise ValueError('topic_contains_deleted_text')
        # Store.put joins this connection's transaction. Failure rolls back the
        # erasure as well as the directive; the directive has no erased parent.
        with self.memory.db:
            self.memory.db.executemany('DELETE FROM records WHERE id=?', [(i,) for i in closure])
            identity = self.memory.store.put('preference', {'type': 'non_use', 'topic': topic.strip()},
                                             'explicit_owner_forget_request', personal=True)
        self.memory.db.execute('VACUUM')
        return {'record_id': identity, 'removed_ids': sorted(closure)}

    def remove(self, identity):
        if identity not in {r['record_id'] for r in self.active()}:
            raise ValueError('non_use_record_not_found')
        return self.memory.store.delete_private(identity)
