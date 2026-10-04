"""Task ownership and event context; historical information never grants actions."""
import copy
import math
import time

OBSERVATIONS = {'inspect', 'inspect_area', 'observe_items', 'search', 'recall'}
SCOPES = {
    'approach': {'inspect', 'inspect_area', 'approach', 'stop', 'recall'},
    'follow': {'inspect', 'approach', 'follow', 'stop', 'recall'},
    'pickup': {'inspect', 'observe_items', 'approach', 'pickup_items', 'stop', 'recall', 'recover_inventory'},
}


def input_event(event_id, channel, text, state):
    return {'event_id': event_id, 'channel': channel, 'user': text,
            'received_at': state.get('sampled_at', time.time()*1000)/1000 if channel=='minecraft' else time.time(),
            'body_at_input': {k: copy.deepcopy(state[k]) for k in
                ('offline', 'position', 'owner', 'inventory', 'dropped_items', 'sampled_at') if k in state},
            'semantics': 'spatial anchor at input time; refresh body before action'}


def dialogue(memory):
    return [{**r, 'authority': 'past_utterance_not_current_world_fact'} for r in memory.context()[-8:]]


def bind_request(work, event, kind):
    work.update(request=copy.deepcopy(event), task_kind=kind, revision=1,
                inputs=[copy.deepcopy(event)], awaiting=None)
    if any(c['kind']=='picked_up' for c in work['done_when']):
        work['baseline'] = copy.deepcopy(event['body_at_input'].get('inventory', work['baseline']))


def reconcile_pickups(work, state):
    """Include automatic pickups during authorized approach/observation, not just pickup tool calls."""
    if not work or not work.get('request') or not any(c['kind']=='picked_up' for c in work['done_when']):
        return
    anchor = ((work.get('inputs') or [work['request']])[-1]['body_at_input'].get('owner') or {}).get('position')
    if not anchor:
        return
    recorded = work.setdefault('pickup_entities', [])
    for event in state.get('recent_pickups', []):
        if (event.get('entity_key') in recorded or not isinstance(event.get('entity_key'), str)
                or type(event.get('count')) is not int or event['count']<=0
                or event.get('collected_at',0)<work['request']['received_at']*1000):
            continue
        item = event.get('item')
        if not any(c['kind']=='picked_up' and item_matches(c['item'],item) for c in work['done_when']):
            continue
        p = event.get('position')
        if not p or math.dist([p[k] for k in ('x','y','z')],[anchor[k] for k in ('x','y','z')])>16:
            continue
        old = work.setdefault('picked_up', {}).get(item, 0)
        if state.get('inventory', {}).get(item,0)-work['baseline'].get(item,0)<old+event['count']:
            continue
        work['picked_up'][item]=old+event['count'];recorded.append(event['entity_key'])


def steer_work(work, event):
    work['revision'] = work.get('revision', 0) + 1
    work['inputs'] = [*work.get('inputs', []), copy.deepcopy(event)][-8:]
    work['awaiting'] = None


def goal_problem(kind, goal):
    kinds = {c['kind'] for c in goal['done_when']}
    expected = {'approach': 'near_owner', 'follow': 'follow_started', 'pickup': 'picked_up'}.get(kind)
    if expected and kinds != {expected}:
        return f'task_requires_{expected}_criterion'
    return None


def normalize_transition(intent, work):
    # A concrete primitive with a different result cannot be a correction of
    # an unrelated durable task, even when the model calls it "steer".
    if (intent['mode']=='steer' and work and intent['task_kind'] in ('approach','follow')
            and goal_problem(intent['task_kind'], work)):
        return {**intent, 'mode':'task'}
    return intent


def action_problem(work, action, state):
    kind = work.get('task_kind', 'ordinary')
    kinds = {c['kind'] for c in work['done_when']}
    if kinds == {'near_owner'}:
        kind = 'approach'
    elif kinds == {'follow_started'}:
        kind = 'follow'
    if any(c['kind'] == 'picked_up' for c in work['done_when']):
        kind = 'pickup'
    if kind in SCOPES and action['name'] not in SCOPES[kind]:
        return 'action_outside_current_request'
    if action['name'] != 'pickup_items':
        return None
    args = action['args']
    known = {e['entity_id']: e for e in (state.get('dropped_items') or {}).get('items', [])}
    if not set(args['entity_ids']) <= set(known):
        return 'pickup_requires_current_entity_observation'
    anchors = work.get('inputs') or [work.get('request', {})]
    anchor = ((anchors[-1].get('body_at_input') or {}).get('owner') or {}).get('position')
    if anchor is None:
        return 'pickup_requires_owner_spatial_anchor'
    for entity_id in args['entity_ids']:
        entity = known[entity_id]
        if not item_matches(args['item'], entity['item']):
            return 'pickup_item_mismatch'
        if math.dist([anchor[k] for k in ('x', 'y', 'z')], [entity['position'][k] for k in ('x', 'y', 'z')]) > 16:
            return 'pickup_outside_indicated_area'
    return None


def item_matches(requested, name):
    return requested == name or requested == 'wood' and name in {
        'oak_log', 'spruce_log', 'birch_log', 'jungle_log', 'acacia_log', 'dark_oak_log', 'mangrove_log', 'cherry_log'}


def observation_key(receipt):
    """Ignore sampling time, retain query/scene contents and owner/entity changes."""
    import json
    from .work import fingerprint
    relevant = {k: receipt.get(k) for k in ('status', 'cells', 'found', 'block_position', 'matched_block')}
    relevant['body'] = fingerprint(receipt.get('observed', {}))
    return json.dumps(relevant, sort_keys=True)
