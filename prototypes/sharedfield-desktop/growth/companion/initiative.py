"""Durable projects and bounded endogenous events, using the existing Harness."""
import copy
import hashlib
import json
import math
import re
import threading
import time
import uuid
from pathlib import Path

from .behavior import validate_tree, next_action, actions
from .memory import Memory
from .work import validate_goal, create_work, preliminary_completion

GRANT_PROMPT = Path(__file__).with_name('initiative_grant_prompt.txt').read_text(encoding='utf-8')
PLAN_PROMPT = Path(__file__).with_name('initiative_prompt.txt').read_text(encoding='utf-8')
READS = {'inspect', 'inspect_area', 'observe_items', 'search', 'recall'}
EFFECTS = {'craft', 'recover_inventory', 'place_at', 'place_many'}


class InitiativeError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def records(memory, kind, record_type):
    return [{'record_id': r['record_id'], **r['body']} for r in memory.library.rows(kind)
            if r['body'].get('type') == record_type]


def projects(memory):
    return records(memory, 'project', 'initiative_project')[-6:]


def project_context(rows):
    return [{k: copy.deepcopy(row[k]) for k in ('record_id', 'project_id', 'concern', 'title', 'status')}
            | {'goal': {k: copy.deepcopy(row['work'][k]) for k in ('title', 'steps', 'done_when')}} for row in rows]


def experience_context(memory, prior):
    tasks = {p['work']['task_id'] for p in prior}
    rows = [r for r in memory.library.rows('experience') if r['body'].get('type') == 'action_receipt'
            and r['body'].get('task_id') in tasks][-16:]
    return [{'record_id': r['record_id'], 'action': r['body']['action'],
             'receipt': {k: copy.deepcopy(v) for k, v in r['body']['receipt'].items() if k != 'observed'},
             'observed_body': {k: copy.deepcopy(r['body']['receipt'].get('observed', {}).get(k))
                               for k in ('inventory', 'crafting_grid', 'cursor', 'window')},
             'authority': 'past execution feedback, not current state or authorization'} for r in rows]


def save_project(memory, work, parents):
    meta = work.get('initiative')
    if not meta: return
    old = next((r for r in projects(memory) if r['project_id'] == meta['project_id']), None)
    body = {'type': 'initiative_project', 'project_id': meta['project_id'], 'concern': meta['concern'],
            'title': work['title'], 'status': work['status'], 'work': copy.deepcopy(work)}
    if old:
        identity = memory.store.correct(old['record_id'], body, 'initiative_project_transition')
        with memory.db:
            memory.db.executemany('INSERT OR IGNORE INTO deps VALUES (?,?,?)',
                                 [(identity, p, 'derived') for p in set(parents)])
    else:
        memory.append('project', body, parents)


def state_key(state):
    # Sampling time and a walking player's coordinates do not create a thought.
    value = {k: state.get(k) for k in ('offline', 'inventory', 'crafting_grid', 'cursor', 'window', 'health', 'food')}
    value['owner_visible'] = bool(state.get('owner'))
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def scope_problem(grant, action):
    name, args = action['name'], action['args']
    if name in READS: return None
    if name not in grant['actions']: return 'initiative_action_outside_delegation'
    if name in ('place_at', 'place_many'):
        if not grant.get('anchor') or not grant['placement_radius']:
            return 'initiative_placement_area_missing'
        targets = args['targets'] if name == 'place_many' else [args]
        for target in targets:
            if target['block'] == 'air' or any(abs(target['position'][k] - grant['anchor'][k]) > grant['placement_radius']
                                             for k in ('x', 'y', 'z')):
                return 'initiative_placement_outside_area'
    return None


class Initiative:
    # Resource bounds, not an activity catalogue or a source of goals.
    MAX_EVENTS = 4
    MAX_MODEL_CALLS = 12
    MAX_EFFECT_ACTIONS = 16
    COOLDOWN_SECONDS = 15

    def __init__(self, engine):
        self.engine = engine
        self.lock = threading.RLock()
        self.grant_id = None
        self.grant_epoch = None
        self.queue = []
        self.seen = set()
        self.worker = None
        self.calls = self.events = self.effects = 0
        self.last_state = None
        self.next_check = 0
        self.not_before = 0

    def pause(self):
        with self.lock:
            self.grant_id = None
            self.queue.clear()

    def grant(self, memory):
        with self.lock:
            identity, epoch = self.grant_id, self.grant_epoch
        if not identity or epoch != self.engine._epoch: return None
        value = memory.record(identity)
        if not value or not memory.record(value['source_id']): return None
        return {'record_id': identity, **value}

    def delegate(self, memory, source, text, state, epoch, *, anchor_state=None):
        previous = projects(memory)
        result = self.engine.model.decide(GRANT_PROMPT, {'current_user': text, 'current_body': state,
            'initiative_stage': 'delegation', 'supported_effects': sorted(EFFECTS),
            'previous_projects': project_context(previous)})
        required = {'request_quote', 'focus', 'actions', 'placement_radius', 'reply'}
        if not isinstance(result, dict) or set(result) != required:
            raise InitiativeError('initiative_delegation_schema')
        if (not isinstance(result['request_quote'], str) or not result['request_quote'] or result['request_quote'] not in text
                or not isinstance(result['focus'], str) or not 1 <= len(result['focus']) <= 400
                or not isinstance(result['reply'], str) or len(result['reply']) > 1000
                or not isinstance(result['actions'], list) or any(a not in EFFECTS for a in result['actions'])
                or len(set(result['actions'])) != len(result['actions'])
                or type(result['placement_radius']) is not int or not 0 <= result['placement_radius'] <= 4):
            raise InitiativeError('initiative_delegation_values')
        spatial = bool(set(result['actions']) & {'place_at', 'place_many'})
        if spatial and not result['placement_radius']:
            raise InitiativeError('initiative_placement_requires_explicit_area')
        if spatial and (not re.search(r'(?<!\d)' + str(result['placement_radius']) + r'\s*格', text)
                        or not any(anchor in text for anchor in ('当前位置', '现在位置', '你身边'))):
            raise InitiativeError('initiative_placement_area_not_grounded_in_input')
        anchor_state = state if anchor_state is None else anchor_state
        position = anchor_state.get('position')
        if spatial and (state.get('offline') is not False or anchor_state.get('offline') is not False or not isinstance(position, dict)
                        or any(type(position.get(k)) not in (int, float) or not math.isfinite(position[k]) for k in ('x','y','z'))):
            raise InitiativeError('initiative_placement_anchor_unknown')
        with self.engine._dispatch_lock:
            if epoch != self.engine._epoch: return None
            identity = memory.append('project', {'type': 'initiative_grant', 'source_id': source,
                **result, 'anchor': {k: math.floor(position[k]) for k in ('x','y','z')} if spatial else None,
                'anchor_source_id': source if spatial else None, 'anchor_sampled_at': anchor_state.get('sampled_at') if spatial else None},
                [source, *[p['record_id'] for p in previous]])
            with self.lock:
                self.grant_id, self.grant_epoch = identity, epoch
                self.queue, self.seen = [], set()
                self.calls = self.events = self.effects = 0
                self.not_before = 0
                self.last_state = state_key(state)
            self.enqueue('delegation:' + identity, 'delegation_granted', [identity, source])
        return result['reply']

    def enqueue(self, key, kind, parents):
        with self.lock:
            if not self.grant_id or key in self.seen or self.events + len(self.queue) >= self.MAX_EVENTS: return
            self.seen.add(key)
            self.queue.append({'event_id': 'initiative:' + uuid.uuid4().hex, 'key': key,
                               'kind': kind, 'parents': list(dict.fromkeys(parents))})

    def pulse(self):
        """Called by the deadline watchdog; never block it on a model/action."""
        with self.lock:
            if not self.grant_id or time.monotonic() < self.next_check: return
            self.next_check = time.monotonic() + 2
            if self.worker and self.worker.is_alive(): return
            if self.events >= self.MAX_EVENTS or self.calls >= self.MAX_MODEL_CALLS: return
            key = state_key(self.engine.body.snapshot())
            if key != self.last_state:
                self.last_state = key
                self.enqueue('body:' + key, 'body_changed', [self.grant_id])
            if not self.queue or time.monotonic() < self.not_before: return
            self.worker = threading.Thread(target=self.drain_one, daemon=True)
            self.worker.start()

    def drain_one(self):
        # Reuse the same serialization as a human turn; queued input wins.
        if not self.engine._turn_lock.acquire(blocking=False): return False
        try:
            with Memory(self.engine.path) as memory:
                with self.lock:
                    grant = self.grant(memory)
                    if not grant:
                        self.pause(); return False
                    if not self.queue or self.engine._waiting: return False
                    old = memory.goal()
                    work = old.get('work') if old else None
                    if work and not work.get('initiative') and work['status'] not in ('completed', 'suspended'): return False
                    if work and work.get('initiative') and work['status'] not in ('completed', 'interrupted', 'suspended', 'not_needed'):
                        if work['status'] != 'blocked' or self.queue[0]['kind'] != 'body_changed': return False
                    if self.events >= self.MAX_EVENTS: return False
                    event = self.queue.pop(0)
                    if any(not memory.record(p) for p in event['parents']): return False
                    self.events += 1
                    epoch = self.engine._epoch
                self.engine._work(event['event_id'], 'initiative', '', lambda _: None, epoch, None,
                    {'event_id': event['event_id'], 'channel': 'initiative', 'user': '',
                     'received_at': time.time(), 'body_at_input': self.engine.body.snapshot(),
                     'semantics': 'endogenous event; not a user utterance or new authorization'},
                    initiative_event=event)
                with self.lock:
                    self.last_state = state_key(self.engine.body.snapshot())
                    self.not_before = time.monotonic() + self.COOLDOWN_SECONDS
                return True
        finally:
            self.engine._turn_lock.release()

    def work_problem(self, memory, work):
        grant = self.grant(memory)
        if not grant or work['initiative']['grant_id'] != grant['record_id']:
            return 'initiative_authority_expired'
        policy = work['initiative']['policy']
        row = memory.db.execute('SELECT status,body FROM records WHERE id=?', (policy['record_id'],)).fetchone()
        if not row or row[0] != 'active': return 'initiative_policy_inactive'
        saved = json.loads(row[1])
        if (saved.get('type') != 'initiative_policy' or saved.get('tree') != policy['tree']
                or saved.get('goal', {}).get('done_when') != work['done_when']):
            return 'initiative_policy_mismatch'

    def action_problem(self, memory, work, action):
        problem = self.work_problem(memory, work)
        if problem: return problem
        if action['name'] not in READS and self.effects >= self.MAX_EFFECT_ACTIONS:
            return 'initiative_action_cap'
        return scope_problem(self.grant(memory), action)

    def plan(self, memory, source, context, work=None):
        grant = self.grant(memory)
        if not grant: raise InitiativeError('initiative_authority_expired')
        with self.lock:
            if self.calls >= self.MAX_MODEL_CALLS: raise InitiativeError('initiative_model_cap')
            self.calls += 1
        prior = projects(memory)
        policies = records(memory, 'skill', 'initiative_policy')[-3:]
        experience = experience_context(memory, prior)
        evidence_ids = [source, grant['record_id'], *[r['record_id'] for r in prior + policies],
                        *[r['record_id'] for r in memory.recent_actions()], *[r['record_id'] for r in experience]]
        evidence_ids = list(dict.fromkeys(evidence_ids))
        result = self.engine.model.decide(PLAN_PROMPT, {**context, 'initiative_stage': 'revise' if work else 'choose',
            'delegation': grant, 'projects': project_context(prior), 'policies': policies, 'evidence_ids': evidence_ids,
            'project_experience': experience, 'current_work': work,
            'remaining_initiative_calls': self.MAX_MODEL_CALLS - self.calls})
        proposal = memory.append('reflection', {'type': 'initiative_proposal', 'event_id': context['current']['event_id'],
                                               'proposal': result}, evidence_ids)
        current_grant = self.grant(memory)
        if not current_grant or current_grant['record_id'] != grant['record_id']:
            raise InitiativeError('initiative_authority_expired')
        required = {'candidates', 'choice', 'project_id', 'concern', 'goal', 'tree', 'based_on_policy', 'evidence_ids', 'reply'}
        if not isinstance(result, dict) or set(result) != required:
            raise InitiativeError('initiative_plan_schema')
        if (not isinstance(result['candidates'], list) or not 1 <= len(result['candidates']) <= 3
                or any(not isinstance(c, str) or not 1 <= len(c) <= 250 for c in result['candidates'])
                or not isinstance(result['reply'], str) or len(result['reply']) > 1000
                or not isinstance(result['evidence_ids'], list) or not result['evidence_ids']
                or any(p not in evidence_ids for p in result['evidence_ids'])):
            raise InitiativeError('initiative_plan_evidence')
        if result['choice'] is None:
            if result['goal'] is not None or result['tree'] is not None: raise InitiativeError('initiative_idle_has_action')
            return None, result['reply']
        if type(result['choice']) is not int or not 0 <= result['choice'] < len(result['candidates']):
            raise InitiativeError('initiative_choice')
        if not isinstance(result['concern'], str) or not 1 <= len(result['concern']) <= 400:
            raise InitiativeError('initiative_concern')
        known_projects = {p['project_id'] for p in prior}
        if result['project_id'] is not None and result['project_id'] not in known_projects:
            raise InitiativeError('initiative_unknown_project')
        if result['based_on_policy'] is not None and result['based_on_policy'] not in {p['record_id'] for p in policies}:
            raise InitiativeError('initiative_unknown_policy')
        goal, tree = validate_goal(result['goal']), validate_tree(result['tree'])
        if not work:
            already = preliminary_completion(create_work(goal, context['body'], source), context['body'])
            if already['satisfied'] and not already['targets']:
                raise InitiativeError('initiative_goal_already_satisfied')
        if work and goal['done_when'] != work['done_when']:
            raise InitiativeError('initiative_result_contract_changed')
        previous_project = next((p for p in prior if p['project_id'] == result['project_id']), None)
        if (not work and previous_project and previous_project['status'] not in ('completed', 'not_needed')
                and goal['done_when'] != previous_project['work']['done_when']):
            raise InitiativeError('initiative_pending_project_contract_changed')
        for action in actions(tree):
            if scope_problem(grant, action): raise InitiativeError(scope_problem(grant, action))
        revision = work['initiative']['policy']['revision'] + 1 if work else 1
        if revision > 3: raise InitiativeError('initiative_revision_cap')
        project_id = work['initiative']['project_id'] if work else result['project_id'] or uuid.uuid4().hex
        policy_id = memory.append('skill', {'type': 'initiative_policy', 'project_id': project_id,
            'revision': revision, 'revision_scope': 'current_task_execution', 'tree': tree, 'goal': goal, 'concern': result['concern'],
            'based_on_policy': result['based_on_policy'], 'proposal_id': proposal},
            [proposal, *result['evidence_ids']])
        return {**goal, 'initiative': {'project_id': project_id, 'concern': result['concern'],
            'grant_id': grant['record_id'], 'policy': {'record_id': policy_id, 'revision': revision,
                'tree': tree, 'outcomes': {}, 'pending': None}}}, result['reply']

    def decision(self, memory, source, work, context):
        problem = self.work_problem(memory, work)
        if problem: raise InitiativeError(problem)
        policy = work['initiative']['policy']
        action = next_action(policy, context['body'])
        reply = ''
        if action is None:
            if policy['revision'] >= 3:
                return {'reply': '这个项目还没通过结果核对，先保留进度。', 'goal': None, 'convention': None,
                        'forget_card': None, 'action': None, 'status': 'blocked'}
            revised, reply = self.plan(memory, source, context, work)
            if revised is None:
                return {'reply': reply or '这个项目先暂停。', 'goal': None, 'convention': None,
                        'forget_card': None, 'action': None, 'status': 'blocked'}
            work['steps'] = revised['steps']
            work['initiative'] = revised['initiative']
            action = next_action(work['initiative']['policy'], context['body'])
        return {'reply': reply, 'goal': None, 'convention': None, 'forget_card': None,
                'action': action, 'status': 'continue'}
