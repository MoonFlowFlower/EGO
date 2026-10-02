"""Observed differences only. No recipes, hidden state, or causal explanations."""
from .contract import validate


def cell_at(obs, position):
    return next((c for c in obs['cells'] if [c['dx'], c['dy']] == list(position)), None)


def appearance(cell):
    return {k: cell.get(k) for k in ('material', 'entity', 'visible_state')} if cell else None


def changes(before, after, action):
    before, after = validate(before), validate(after)
    if before['world'] != after['world']: raise ValueError('different_worlds')
    inventory = {k: after['inventory'][k] - v for k, v in before['inventory'].items()
                 if after['inventory'][k] != v}
    needs = {k: after['needs'][k] - v for k, v in before['needs'].items() if after['needs'][k] != v}
    # Match the SAME observed tile, translating by the actual displacement.
    # Turning changes facing, not the contents of the previously facing tile.
    target = before['facing']
    moved = after['displacement']
    old = appearance(cell_at(before, target))
    new = appearance(cell_at(after, [target[i] - moved[i] for i in (0, 1)]))
    front = {'before': old, 'after': new} if old is not None and new is not None and old != new else None
    increases = {k: v for k, v in needs.items() if k in ('food', 'drink') and v > 0}
    effects = {'inventory': inventory, 'displacement': moved, 'front': front,
               'entered_sleep': not before['sleeping'] and after['sleeping'], 'consumption': increases}
    visible = bool(inventory or moved != [0, 0] or front or effects['entered_sleep'] or increases)
    events = []
    if action != 'noop' and not visible: events.append('no_visible_effect')
    if action in ('move_left', 'move_right', 'move_up', 'move_down') and moved == [0, 0]: events.append('blocked')
    if needs.get('health', 0) < 0: events.append('health_lost')
    return {'action': action, 'tick': after['tick'], 'effects': effects,
            'other_needs': {k: v for k, v in needs.items() if k not in increases}, 'events': events}


def repeat_action(action, repeat, observe, act, *, cancel=None, on_step=None):
    if type(repeat) is not int or not 1 <= repeat <= 8: raise ValueError('repeat_limit')
    events = []
    status = 'completed'
    for _ in range(repeat):
        if cancel is not None and cancel.is_set(): status = 'cancelled'; break
        before = observe()
        if before['done']: status = 'episode_finished'; break
        after = act(action)
        event = changes(before, after, action); events.append(event)
        if on_step: on_step(before, after, event)
        if 'health_lost' in event['events']: status = 'injured'; break
        if 'blocked' in event['events']: status = 'blocked'; break
        if after['done']: status = 'episode_finished'; break
    return {'status': status, 'steps': len(events), 'events': events}
