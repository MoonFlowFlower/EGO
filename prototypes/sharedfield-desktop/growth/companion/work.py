"""Small durable task contract. Completion is computed from effects, not prose."""
import copy
import json
import re
import uuid

from .engine import validate_action as legacy_action


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value)


def position(value):
    return (isinstance(value, dict) and set(value) == {'x', 'y', 'z'}
            and all(type(v) is int for v in value.values())
            and abs(value['x']) <= 29999984 and abs(value['z']) <= 29999984 and -64 <= value['y'] <= 319)


def validate_action(action):
    if not isinstance(action, dict) or set(action) != {'name', 'args'} or not isinstance(action['args'], dict):
        raise ValueError('action_schema')
    name, args = action['name'], action['args']
    if name == 'recover_inventory' and args == {}:
        return action
    if name == 'inspect_area' and set(args) == {'radius'} and type(args['radius']) is int and 1 <= args['radius'] <= 4:
        return action
    if name == 'place_at' and set(args) == {'block', 'position'} and identifier(args['block']) and position(args['position']):
        return action
    return legacy_action(action)


def validate_goal(goal):
    if not isinstance(goal, dict) or set(goal) != {'title', 'steps', 'done_when'}:
        raise ValueError('goal_contract_required')
    if not isinstance(goal['title'], str) or not 1 <= len(goal['title']) <= 300:
        raise ValueError('goal_title')
    if not isinstance(goal['steps'], list) or not 1 <= len(goal['steps']) <= 6 or not all(isinstance(s, str) and 0 < len(s) <= 160 for s in goal['steps']):
        raise ValueError('goal_steps')
    if not isinstance(goal['done_when'], list) or not 1 <= len(goal['done_when']) <= 6:
        raise ValueError('goal_criteria')
    for c in goal['done_when']:
        if not isinstance(c, dict):
            raise ValueError('goal_criterion')
        kind = c.get('kind')
        if kind in ('inventory', 'gained', 'delivered', 'placed'):
            item_key = 'block' if kind == 'placed' else 'item'
            if set(c) != {'kind', item_key, 'count'} or not identifier(c[item_key]) or type(c['count']) is not int or not 1 <= c['count'] <= 128:
                raise ValueError('goal_count')
        elif kind == 'blocks':
            if set(c) != {'kind', 'block', 'positions'} or not identifier(c['block']) or not isinstance(c['positions'], list) or not 1 <= len(c['positions']) <= 64 or not all(position(p) for p in c['positions']):
                raise ValueError('goal_blocks')
            if len({json.dumps(p, sort_keys=True) for p in c['positions']}) != len(c['positions']):
                raise ValueError('goal_duplicate_positions')
        elif kind not in ('inventory_clear', 'near_owner', 'follow_started') or set(c) != {'kind'}:
            raise ValueError('unsupported_goal_criterion')
    if sum(len(c['positions']) if c['kind']=='blocks' else c['count'] if c['kind']=='placed' else 0 for c in goal['done_when']) > 128:
        raise ValueError('goal_world_check_limit')
    return copy.deepcopy(goal)


def create_work(goal, state, source_id):
    return {**validate_goal(goal), 'task_id': uuid.uuid4().hex, 'source_id': source_id,
            'baseline': copy.deepcopy(state.get('inventory', {})), 'placed': [], 'delivered': {},
            'follow_started': False, 'status': 'active', 'decisions': 0, 'actions': 0,
            'checkpoints': 0, 'last_problem': None, 'completion': None}


def save_work(memory, work, parents):
    old = memory.goal()
    body = {'type': 'kernel_goal', 'title': work['title'], 'goal_status': work['status'], 'work': copy.deepcopy(work)}
    if old:
        identity = memory.store.correct(old['record_id'], body, 'harness_checkpoint')
        with memory.db:
            memory.db.executemany('INSERT OR IGNORE INTO deps VALUES (?,?,?)', [(identity, p, 'derived') for p in parents])
    else:
        memory.store.put('project', body, 'harness_checkpoint', personal=True, parents=parents)


def incorporate(work, action, receipt):
    if not work or not receipt.get('verified'):
        return
    name, args = action['name'], action['args']
    if name in ('place', 'place_at') and receipt.get('placement', {}).get('consumed') == 1:
        p = receipt.get('position')
        target = {'block': args['block'], 'position': p}
        if position(p) and target not in work['placed']:
            work['placed'].append(target)
    if name == 'give' and receipt.get('lost') == args['count'] and receipt.get('matching_collected', 0) >= args['count']:
        work['delivered'][args['item']] = work['delivered'].get(args['item'], 0) + args['count']
    if name == 'follow' and receipt.get('status') == 'following_started_only':
        work['follow_started'] = True


def preliminary_completion(work, state):
    checks, targets = [], []
    for c in work['done_when']:
        kind = c['kind']
        if kind == 'inventory':
            ok = state.get('inventory', {}).get(c['item'], 0) >= c['count']
        elif kind == 'gained':
            ok = state.get('inventory', {}).get(c['item'], 0) - work['baseline'].get(c['item'], 0) >= c['count']
        elif kind == 'delivered':
            ok = work['delivered'].get(c['item'], 0) >= c['count']
        elif kind == 'placed':
            placed = [p for p in work['placed'] if p['block'] == c['block']]
            ok = len(placed) >= c['count']
            targets.extend(placed[:c['count']])
        elif kind == 'blocks':
            ok = True
            targets.extend({'block': c['block'], 'position': p} for p in c['positions'])
        elif kind == 'inventory_clear':
            ok = not state.get('crafting_grid') and not state.get('cursor') and not state.get('window')
        elif kind == 'near_owner':
            owner = state.get('owner') or {}
            ok = owner.get('distance', float('inf')) <= 3.25 and owner.get('height_difference', float('inf')) <= 1.25
        else:
            ok = work['follow_started']
        checks.append({'criterion': c, 'satisfied': bool(ok)})
    return {'satisfied': not state.get('offline', True) and all(c['satisfied'] for c in checks), 'checks': checks, 'targets': targets}


def fingerprint(state):
    stable = {k: state.get(k) for k in ('offline', 'inventory', 'crafting_grid', 'cursor', 'window')}
    stable['position'] = {k: round(v, 1) for k, v in (state.get('position') or {}).items()}
    return json.dumps(stable, sort_keys=True)
