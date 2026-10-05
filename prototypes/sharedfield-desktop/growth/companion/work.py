"""Small durable task contract. Completion is computed from effects, not prose."""
import copy
import json
import re
import uuid

from .engine import validate_action as legacy_action


class GoalError(ValueError):
    def __init__(self, code, **details):
        super().__init__(code)
        self.details = details


def identifier(value):
    return isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value)


def position(value):
    return (isinstance(value, dict) and set(value) == {'x', 'y', 'z'}
            and all(type(v) is int for v in value.values())
            and abs(value['x']) <= 29999984 and abs(value['z']) <= 29999984 and -64 <= value['y'] <= 319)


def validate_action(action):
    if not isinstance(action, dict) or set(action) != {'name', 'args'} or not isinstance(action['name'], str) or not isinstance(action['args'], dict):
        raise ValueError('action_schema')
    name, args = action['name'], action['args']
    if name == 'place_many' and set(args) == {'targets'}:
        targets=args['targets']
        if (not isinstance(targets,list) or not 1<=len(targets)<=8 or any(not isinstance(t,dict)
                or set(t)!={'block','position'} or not identifier(t['block']) or t['block']=='air'
                or not position(t['position']) for t in targets)):
            raise ValueError('placement_targets')
        if len({json.dumps(t['position'],sort_keys=True) for t in targets})!=len(targets):
            raise ValueError('placement_duplicate_targets')
        return action
    if name == 'recall' and set(args) == {'query'} and isinstance(args['query'], str) and 1 <= len(args['query']) <= 200:
        return action
    if name == 'observe_items' and set(args) == {'range'} and type(args['range']) is int and 1 <= args['range'] <= 32:
        return action
    if name == 'pickup_items' and set(args) == {'entity_ids', 'item', 'count'} and identifier(args['item']) and type(args['count']) is int and 1 <= args['count'] <= 16:
        ids = args['entity_ids']
        if isinstance(ids, list) and 1 <= len(ids) <= 16 and all(type(i) is int and i >= 0 for i in ids) and len(set(ids)) == len(ids):
            return action
        raise ValueError('pickup_entities')
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
    goal=copy.deepcopy(goal)
    for index, c in enumerate(goal['done_when']):
        path = f'done_when[{index}]'
        if not isinstance(c, dict):
            raise ValueError('goal_criterion')
        kind = c.get('kind')
        if kind in ('inventory', 'gained', 'delivered', 'placed', 'picked_up'):
            item_key = 'block' if kind == 'placed' else 'item'
            if set(c) != {'kind', item_key, 'count'} or not identifier(c[item_key]) or type(c['count']) is not int or not 1 <= c['count'] <= 128:
                raise ValueError('goal_count')
        elif kind == 'blocks':
            if set(c)=={'kind','block','regions'}:
                regions=c.pop('regions')
                if not isinstance(regions,list) or not 1<=len(regions)<=16:
                    raise ValueError('goal_regions')
                positions={}
                for region_index, region in enumerate(regions):
                    if (not isinstance(region,dict) or set(region)!={'min','max'}
                            or not position(region['min']) or not position(region['max'])):
                        raise ValueError('goal_region_bounds')
                    a,b=region['min'],region['max']
                    sizes=[b[k]-a[k]+1 for k in ('x','y','z')]
                    if min(sizes)<1:
                        raise GoalError('goal_region_bounds', path=f'{path}.regions[{region_index}]',
                                        requirement='min must not exceed max on any axis')
                    if sizes[0]*sizes[1]*sizes[2]>64:
                        raise GoalError('goal_region_size', path=f'{path}.regions[{region_index}]',
                                        actual=sizes[0]*sizes[1]*sizes[2], limit=64)
                    for x in range(a['x'],b['x']+1):
                        for y in range(a['y'],b['y']+1):
                            for z in range(a['z'],b['z']+1):positions[(x,y,z)]={'x':x,'y':y,'z':z}
                c['positions']=list(positions.values())
            if set(c) != {'kind', 'block', 'positions'} or not identifier(c['block']) or not isinstance(c['positions'], list) or not all(position(p) for p in c['positions']):
                raise ValueError('goal_blocks')
            if not 1 <= len(c['positions']) <= 64:
                raise GoalError('goal_blocks_limit', path=f'{path}.positions', actual=len(c['positions']),
                                minimum=1, limit=64, requirement='count the unique union of regions for this criterion')
            if len({json.dumps(p, sort_keys=True) for p in c['positions']}) != len(c['positions']):
                raise ValueError('goal_duplicate_positions')
        elif kind not in ('inventory_clear', 'near_owner', 'follow_started') or set(c) != {'kind'}:
            raise ValueError('unsupported_goal_criterion')
    world_checks = sum(len(c['positions']) if c['kind']=='blocks' else c['count'] if c['kind']=='placed' else 0 for c in goal['done_when'])
    if world_checks > 128:
        raise GoalError('goal_world_check_limit', path='done_when', actual=world_checks, limit=128)
    targets={}
    for c in goal['done_when']:
        if c['kind']=='blocks':
            for p in c['positions']:
                key=tuple(p[k] for k in ('x','y','z'))
                if key in targets and targets[key]!=c['block']:raise ValueError('goal_conflicting_blocks')
                targets[key]=c['block']
    return copy.deepcopy(goal)


def create_work(goal, state, source_id):
    return {**validate_goal(goal), 'task_id': uuid.uuid4().hex, 'source_id': source_id,
            'baseline': copy.deepcopy(state.get('inventory', {})), 'placed': [], 'delivered': {},
            'picked_up': {}, 'pickup_entities': [], 'follow_started': False, 'status': 'active', 'decisions': 0, 'actions': 0,
            'checkpoints': 0, 'last_problem': None, 'completion': None}


def save_work(memory, work, parents):
    old = memory.goal()
    body = {'type': 'kernel_goal', 'title': work['title'], 'goal_status': work['status'], 'work': copy.deepcopy(work)}
    if old:
        if old.get('work', {}).get('task_id') != work['task_id']:
            memory.append('project', {'type': 'suspended_task', 'work': old.get('work'),
                                      'replaced_by_task': work['task_id']}, [old['record_id']])
        identity = memory.store.correct(old['record_id'], body, 'harness_checkpoint')
        with memory.db:
            memory.db.executemany('INSERT OR IGNORE INTO deps VALUES (?,?,?)', [(identity, p, 'derived') for p in parents])
    else:
        memory.store.put('project', body, 'harness_checkpoint', personal=True, parents=parents)


def incorporate(work, action, receipt):
    if work and action['name']=='place_many':
        for child in receipt.get('placements',[]):
            target=child.get('target')
            if target in action['args']['targets']:
                incorporate(work,{'name':'place_at','args':target},child.get('receipt',{}))
        return
    if work and action['name'] == 'pickup_items' and receipt.get('evidence') == 'self_collect_events_and_inventory':
        # Partial pickups are durable effects even when the requested total failed.
        recorded = work.setdefault('pickup_entities', [])
        gained = receipt.get('inventory_gained', {})
        events = receipt.get('pickup_events', [])
        totals = {}
        for event in events:
            if (event.get('entity_id') not in action['args']['entity_ids'] or event.get('entity_key') in recorded
                    or not isinstance(event.get('entity_key'), str) or type(event.get('count')) is not int or event['count'] <= 0):
                continue
            item = event.get('item')
            from .interaction import item_matches
            if not item_matches(action['args']['item'], item):
                continue
            totals[item] = totals.get(item, 0) + event['count']
        if totals and all(type(gained.get(item)) is int and gained[item] >= n for item, n in totals.items()):
            for item, n in totals.items():
                work.setdefault('picked_up', {})[item] = work['picked_up'].get(item, 0) + n
            recorded.extend(e['entity_key'] for e in events if e.get('item') in totals and e['entity_key'] not in recorded)
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
        elif kind == 'picked_up':
            from .interaction import item_matches
            verified_count = sum(n for item, n in work.get('picked_up', {}).items() if item_matches(c['item'], item))
            net = sum(n - work['baseline'].get(item, 0) for item, n in state.get('inventory', {}).items() if item_matches(c['item'], item))
            ok = verified_count >= c['count'] and net >= c['count']
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
    stable['owner'] = state.get('owner')
    stable['items'] = (state.get('dropped_items') or {}).get('items')
    return json.dumps(stable, sort_keys=True)
