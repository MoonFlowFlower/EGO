"""Local quoted-evidence conventions built on the P6 version/deletion store.

Scope is global to this one user's store. Provenance retains utterance IDs and
session IDs separately. A model may propose a card but cannot approve its own
citations or replacements. No source is evaluated by another model.
"""
import json
import re
import unicodedata
from datetime import datetime

from growthlab.state import Store


def normalize(text):
    return re.sub(r'[\s\W_]+', '', unicodedata.normalize('NFKC', text).casefold())


def validate_trigger(trigger):
    if not isinstance(trigger, dict) or set(trigger) != {'kind', 'text', 'weekday', 'after', 'event'}:
        raise ValueError('trigger_schema')
    if not isinstance(trigger['text'], str) or not normalize(trigger['text']):
        raise ValueError('empty_trigger')
    if trigger['kind'] == 'utterance':
        if trigger['weekday'] != -1 or trigger['after'] or trigger['event']:
            raise ValueError('utterance_trigger_fields')
    elif trigger['kind'] == 'situation':
        if type(trigger['weekday']) is not int or not 0 <= trigger['weekday'] <= 6:
            raise ValueError('weekday')
        if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', trigger['after']):
            raise ValueError('after_time')
        if not isinstance(trigger['event'], str) or not trigger['event'].strip():
            raise ValueError('event')
        # Supported public grammar is deliberately narrow and deterministic.
        # The model cannot attach an arbitrary clock predicate to a real quote.
        match = re.fullmatch(r'周([一二三四五六日天])([0-2]\d:[0-5]\d)以后上线',
                             unicodedata.normalize('NFKC', trigger['text']).replace(' ', ''))
        if not match:
            raise ValueError('unsupported_situation_grammar')
        day = '一二三四五六日'.index(match[1].replace('天', '日'))
        if (trigger['weekday'], trigger['after'], trigger['event']) != (day, match[2], 'login'):
            raise ValueError('situation_predicate_disagrees_with_quote')
    else:
        raise ValueError('trigger_kind')


def trigger_matches(trigger, current_utterance, occurred_at, event_labels):
    validate_trigger(trigger)
    if trigger['kind'] == 'utterance':
        return normalize(trigger['text']) in normalize(current_utterance)
    instant = datetime.fromisoformat(occurred_at)
    return (instant.weekday() == trigger['weekday']
            and instant.strftime('%H:%M') >= trigger['after']
            and trigger['event'] in event_labels)


class ConventionLibrary:
    def __init__(self, path):
        self.store = Store(path)

    def close(self):
        self.store.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def utterance(self, text, *, session_id, speaker='user', occurred_at='', event_labels=()):
        if speaker not in ('user', 'assistant') or not isinstance(text, str) or not text.strip():
            raise ValueError('utterance_schema')
        return self.store.put('experience', {
            'type': 'utterance', 'utterance_text': text, 'speaker': speaker,
            'session_id': session_id, 'occurred_at': occurred_at,
            'event_labels': list(event_labels),
        }, 'direct_utterance', personal=True)

    def rows(self, kind=None, *, active_only=True):
        sql = 'SELECT id,kind,scope,world,status,body,source FROM records WHERE personal=1'
        args = []
        if kind:
            sql += ' AND kind=?'
            args.append(kind)
        if active_only:
            sql += " AND status='active'"
        return [dict(zip(('record_id', 'record_kind', 'scope', 'world', 'status', 'body', 'source'),
                         (*r[:5], json.loads(r[5]), r[6])))
                for r in self.store.db.execute(sql, args)]

    def sources(self):
        return [{'utterance_id': r['record_id'], **r['body']}
                for r in self.rows('experience') if r['body'].get('type') == 'utterance']

    def cards(self, *, active_only=True):
        return [{'card_id': r['record_id'], 'card_status': r['status'], **r['body']}
                for r in self.rows('preference', active_only=active_only)
                if r['body'].get('type') == 'convention']

    def propose(self, proposal, *, allowed_ids):
        expected = {'trigger', 'meaning', 'source_ids', 'replaces'}
        if not isinstance(proposal, dict) or set(proposal) != expected:
            raise ValueError('proposal_schema')
        trigger, meaning = proposal['trigger'], proposal['meaning']
        validate_trigger(trigger)
        if not isinstance(meaning, str) or not 1 <= len(meaning) <= 500:
            raise ValueError('meaning_schema')
        ids = proposal['source_ids']
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            raise ValueError('source_ids_schema')
        if not set(ids) <= set(allowed_ids):
            raise ValueError('unsupplied_utterance')
        sources = {s['utterance_id']: s for s in self.sources()}
        if not all(i in sources and sources[i]['speaker'] == 'user' for i in ids):
            raise ValueError('missing_user_utterance')
        cited = [sources[i]['utterance_text'] for i in ids]
        # Exact quoted spans are mechanically checkable. Paraphrase correctness
        # cannot be silently delegated to an LLM. All source quotes must contain
        # the trigger; at least one must contain the quoted meaning too.
        if not all(normalize(trigger['text']) in normalize(s) for s in cited):
            raise ValueError('trigger_absent_from_citation')
        if not any(normalize(meaning) in normalize(s) for s in cited):
            raise ValueError('meaning_not_quoted')
        previous = proposal['replaces']
        body = {'type': 'convention', 'trigger': trigger, 'meaning': meaning, 'source_ids': ids}
        cards = {c['card_id']: c for c in self.cards()}
        same = [c for c in cards.values() if normalize(c['trigger']['text']) == normalize(trigger['text'])]
        if previous:
            if previous not in cards:
                raise ValueError('replacement_not_active')
            old = cards[previous]
            if old['trigger'] != trigger:
                raise ValueError('replacement_trigger_changed')
            if normalize(old['meaning']) == normalize(meaning):
                return previous  # Evidence-preserving idempotent proposal.
            # Public, reusable correction grammar; both sides must be quoted.
            pattern = ('不再是' + re.escape(normalize(old['meaning']))
                       + '现在改成' + re.escape(normalize(meaning)))
            if not any(re.search(pattern, normalize(s)) for s in cited):
                raise ValueError('no_contradictory_utterance')
            identity = self.store.correct(previous, body, 'validated_user_correction')
            with self.store.db:
                self.store.db.executemany('INSERT INTO deps VALUES (?,?,?)',
                                         [(identity, i, 'derived') for i in ids])
            return identity
        if same:
            if all(c['trigger'] == trigger and normalize(c['meaning']) == normalize(meaning) for c in same):
                return same[0]['card_id']
            raise ValueError('replacement_requires_existing_id')
        return self.store.put('preference', body, 'validated_quoted_convention', personal=True, parents=ids)

    def reflect(self, text, source_ids):
        if not isinstance(text, str) or not text.strip() or len(text) > 6000:
            raise ValueError('reflection_schema')
        known = {s['utterance_id'] for s in self.sources()}
        if not source_ids or not set(source_ids) <= known:
            raise ValueError('reflection_provenance')
        return self.store.put('reflection', {'reflection_text': text}, 'model_reflection',
                              personal=True, parents=source_ids)

    def annotate(self, current_utterance, occurred_at, event_labels):
        return [{'card_id': c['card_id'], 'source_ids': c['source_ids'],
                 'annotation_text': f"按约定卡 {c['card_id']}（来源：原话 "
                                    f"{', '.join('#' + s for s in c['source_ids'])}）："
                                    f"「{c['trigger']['text']}」= {c['meaning']}"}
                for c in self.cards()
                if trigger_matches(c['trigger'], current_utterance, occurred_at, event_labels)]

    def forget(self, card_id):
        """Erase original quotes, every card version and all derived records.

        P6 follows correction parents upwards and every dependent downwards.
        Finding the quote roots additionally removes the original utterances,
        rather than deleting only their derived convention card.
        """
        all_cards = {c['card_id']: c for c in self.cards(active_only=False)}
        if card_id not in all_cards:
            raise ValueError('unknown_card')
        chain = {card_id}
        edges = list(self.store.db.execute("SELECT child,parent FROM deps WHERE relation='correction'"))
        while True:
            extended = chain | {a for a, b in edges if b in chain} | {b for a, b in edges if a in chain}
            if extended == chain:
                break
            chain = extended
        roots = {s for c in chain if c in all_cards for s in all_cards[c]['source_ids']}
        removed = 0
        for identity in sorted(roots | chain):
            if self.store.db.execute('SELECT 1 FROM records WHERE id=?', (identity,)).fetchone():
                removed += self.store.delete_private(identity)
        return {'status': 'deleted', 'removed_records': removed}

    def forget_sources(self, source_ids):
        removed = 0
        for identity in source_ids:
            if self.store.db.execute('SELECT 1 FROM records WHERE id=?', (identity,)).fetchone():
                removed += self.store.delete_private(identity)
        return {'status': 'deleted', 'removed_records': removed}
