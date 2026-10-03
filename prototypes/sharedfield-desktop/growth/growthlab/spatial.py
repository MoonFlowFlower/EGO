"""Inherited spatial representation, derived ONLY from a validated observation."""
from .contract import validate
from .changes import cell_at, appearance

FORMATS = ('cells', 'assisted', 'map')
V2_FORMATS = ('v2_cells', 'v2_map')
DIRECTIONS = {(0, -1): '上', (0, 1): '下', (-1, 0): '左', (1, 0): '右'}
MATERIAL_GLYPHS = {'grass': '.', 'path': '=', 'sand': ':', 'water': '~', 'stone': '#', 'tree': 'T',
                   'lava': '!', 'coal': 'c', 'iron': 'i', 'diamond': 'd', 'table': 'W', 'furnace': 'F', 'unknown': '?'}
ENTITY_GLYPHS = {'cow': 'C', 'zombie': 'Z', 'skeleton': 'K', 'plant': 'p', 'fence': 'f'}


def direction(dx, dy):
    parts = []
    if dy: parts.append(f"{'下' if dy > 0 else '上'} {abs(dy)} 步")
    if dx: parts.append(f"{'右' if dx > 0 else '左'} {abs(dx)} 步")
    return '、'.join(parts) or '脚下，0 步'


def nearest_cells(obs, name):
    found = [c for c in obs['cells'] if c['material'] == name or c['entity'] == name]
    if not found: return []
    distance = min(abs(c['dx']) + abs(c['dy']) for c in found)
    return sorted((c for c in found if abs(c['dx']) + abs(c['dy']) == distance), key=lambda c: (c['dy'], c['dx']))


def aids(observation, *, with_map=False):
    obs = validate(observation)
    symbols = sorted({c[k] for c in obs['cells'] for k in ('material', 'entity') if c[k] is not None})
    nearest = []
    for name in symbols:
        c = nearest_cells(obs, name)[0]; distance = abs(c['dx']) + abs(c['dy'])
        nearest.append({'name': name, 'dx': c['dx'], 'dy': c['dy'], 'direction': direction(c['dx'], c['dy']),
                        'offset_steps': distance, 'adjacent': distance == 1, 'underfoot': distance == 0,
                        'visible_state': c.get('visible_state')})
    result = {'front': appearance(cell_at(obs, obs['facing'])), 'nearest': nearest,
              'distance_definition': 'Relative offset, vertical then horizontal; Manhattan steps, not a guaranteed walkable route. Adjacent means one cardinal step. Ties choose dy then dx.'}
    if with_map:
        lookup = {(c['dx'], c['dy']): c for c in obs['cells']}; rows = []
        for y in range(-3, 4):
            line = ''
            for x in range(-4, 5):
                c = lookup.get((x, y)); glyph = '?' if c is None else MATERIAL_GLYPHS.get(c['material'], '?')
                if c:
                    entity = c['entity']; state = c.get('visible_state') or {}
                    if entity == 'player': glyph = {(1, 0): '>', (-1, 0): '<', (0, 1): 'v', (0, -1): '^'}[tuple(obs['facing'])]
                    elif entity == 'plant': glyph = 'P' if state.get('plant_ripe') else 'p'
                    elif entity == 'arrow': glyph = 'a'
                    elif entity: glyph = ENTITY_GLYPHS.get(entity, '?')
                line += glyph
            rows.append(line)
        result['map'] = {'rows': rows, 'top_left_offset': [-4, -3], 'x_positive': 'right', 'y_positive': 'down',
                         'legend': {**{v: k for k, v in MATERIAL_GLYPHS.items()}, **{v: k for k, v in ENTITY_GLYPHS.items()},
                                    'P': 'ripe plant', 'a': 'arrow; direction in visible_state', '> < v ^': 'player facing', '?': 'not supplied/unknown'}}
    return result


def representation(observation, mode):
    if mode in V2_FORMATS: return representation_v2(observation, cells=mode == 'v2_cells')
    if mode not in FORMATS: raise ValueError('observation_format')
    packet = {'observation': validate(observation)}
    if mode != 'cells': packet['observation_aids'] = aids(observation, with_map=mode == 'map')
    return packet


def representation_v2(observation, *, cells=True):
    # Keep v1 functions intact for the frozen K0 comparison. This is a view,
    # never an internal observation accepted by rules/changes/navigation.
    obs = validate(observation)
    here = cell_at(obs, (0, 0)); facing = DIRECTIONS[tuple(obs['facing'])]
    visible = [c for c in obs['cells'] if (c['dx'], c['dy']) != (0, 0)]
    for c in visible:
        if c['entity'] == 'player': raise ValueError('unexpected_self_outside_origin')
        c['entity'] = c['entity'] or 'none'
    front = next(c for c in visible if [c['dx'], c['dy']] == obs['facing'])
    symbols = sorted({c[k] for c in visible for k in ('material', 'entity') if c[k] != 'none'})
    nearest = []
    for name in symbols:
        c = min((c for c in visible if name in (c['material'], c['entity'])),
                key=lambda c: (abs(c['dx'])+abs(c['dy']), c['dy'], c['dx']))
        distance = abs(c['dx'])+abs(c['dy'])
        nearest.append({'name': name, 'dx': c['dx'], 'dy': c['dy'],
                        'direction': direction(c['dx'], c['dy']), 'offset_steps': distance,
                        'adjacent': distance == 1, 'visible_state': c.get('visible_state')})
    chart = aids(observation, with_map=True)['map']
    chart['rows'][3] = chart['rows'][3][:4]+'@'+chart['rows'][3][5:]
    chart['legend'].pop('> < v ^')
    chart['legend']['@'] = f'你自己，面朝{facing}'
    info = {'representation_version': 2,
            'self': {'underfoot_material': here['material'], 'facing_direction': facing, 'facing_vector': obs['facing']},
            'front': {**front, 'direction': facing}, 'nearest': nearest, 'map': chart,
            'visible_states': [{k: c[k] for k in ('dx', 'dy', 'material', 'entity', 'visible_state')}
                               for c in visible if c.get('visible_state') is not None],
            'distance_definition': 'Offsets are from you now. Vertical then horizontal; Manhattan steps, not a path. Adjacent means one cardinal step. Ties choose dy then dx.'}
    obs.pop('cells')
    if cells: obs['cells'] = visible
    return {'observation': obs, 'observation_aids': info}


def context_view(value):
    # Changes/memories can describe the tile we just moved onto. Retain that
    # observation as "self", without reintroducing a scene entity named player.
    if isinstance(value, list): return [context_view(x) for x in value]
    if isinstance(value, dict):
        return {k: ('self' if k == 'entity' and v == 'player' else context_view(v)) for k, v in value.items()}
    return value
