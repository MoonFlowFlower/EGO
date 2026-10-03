"""Inherited BFS over currently visible JSON cells, never an environment handle."""
import time
from collections import deque
from .contract import MATERIALS, ENTITIES, validate

MOVES = (('move_up', (0, -1)), ('move_left', (-1, 0)), ('move_right', (1, 0)), ('move_down', (0, 1)))
TARGETS = tuple(x for x in (*MATERIALS, *ENTITIES) if x not in ('unknown', 'player'))
# Birth-package movement knowledge, not dynamically read feasibility or recipes.
WALKABLE = {'grass', 'path', 'sand'}


def plan(observation, name):
    if name not in TARGETS: raise ValueError('goto_target')
    obs = validate(observation); cells = {(c['dx'], c['dy']): c for c in obs['cells']}
    targets = {xy for xy, c in cells.items() if c['material'] == name or c['entity'] == name}
    if not targets: return {'status': 'target_not_visible', 'actions': [], 'searched_cells': []}
    def walkable(xy):
        c = cells.get(xy)
        return c is not None and c['material'] in WALKABLE and (c['entity'] is None or xy == (0, 0))
    start = (0, 0, *obs['facing']); queue = deque([(start, [], [])]); visited = {start}; searched = set()
    while queue:
        (x, y, fx, fy), actions, turns = queue.popleft(); searched.add((x, y))
        if (x + fx, y + fy) in targets:
            return {'status': 'arrived' if not actions else 'route', 'actions': actions,
                    'planned_turns': turns, 'target': [x + fx, y + fy], 'searched_cells': sorted(map(list, searched))}
        for action, (dx, dy) in MOVES:
            xy = x + dx, y + dy
            if xy not in cells: continue  # Never probe outside the allowed view.
            turn = not walkable(xy)
            # Lava is physically walkable (fatal), so it cannot be used as a
            # collision turn merely because our planner excludes it.
            if turn and cells[xy]['material'] == 'lava': continue
            state = (x, y, dx, dy) if turn else (*xy, dx, dy)
            if state not in visited:
                visited.add(state); queue.append((state, [*actions, action], [*turns, turn]))
    return {'status': 'no_path', 'actions': [], 'searched_cells': sorted(map(list, searched))}


def goto(name, observe, act, *, max_steps=32, deadline=None, cancel=None, on_step=None):
    start = time.perf_counter(); deadline = deadline if deadline is not None else start + 5
    steps = 0; routes = []
    def result(status):
        return {'status': status, 'reason': status, 'steps': steps, 'target_name': name,
                'seconds': time.perf_counter()-start, 'plans': routes}
    while True:
        if cancel is not None and cancel.is_set(): return result('cancelled')
        if time.perf_counter() >= deadline: return result('timeout')
        before = validate(observe())
        if before['done']: return result('episode_finished')
        route = plan(before, name); routes.append({'tick': before['tick'], **route})
        if route['status'] != 'route': return result(route['status'])
        if steps >= max_steps: return result('step_limit')
        action = route['actions'][0]; after = validate(act(action)); steps += 1
        if on_step: on_step(before, after, action)
        if after['needs']['health'] < before['needs']['health']: return result('injured')
        if after['done']: return result('episode_finished')
        planned_turn = route['planned_turns'][0]
        facing = list(dict(MOVES)[action])
        if after['displacement'] == [0, 0] and not (planned_turn and after['facing'] == facing): return result('blocked')
