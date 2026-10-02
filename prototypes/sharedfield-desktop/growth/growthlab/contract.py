"""Pure JSON policy contract: no crafter import and no host capabilities."""
import json

ACTIONS = ('noop','move_left','move_right','move_up','move_down','do','sleep',
           'place_stone','place_table','place_furnace','place_plant','make_wood_pickaxe',
           'make_stone_pickaxe','make_iron_pickaxe','make_wood_sword','make_stone_sword','make_iron_sword')
ITEMS = ('sapling','wood','stone','coal','iron','diamond','wood_pickaxe','stone_pickaxe',
         'iron_pickaxe','wood_sword','stone_sword','iron_sword')
MATERIALS = ('water','grass','stone','path','sand','tree','lava','coal','iron','diamond','table','furnace','unknown')
ENTITIES = ('player','cow','zombie','skeleton','arrow','plant','fence')
NEEDS = ('health','food','drink','energy')
FIELDS = {'schema','tick','world','needs','inventory','light','radius','cells','displacement','facing','sleeping','done','actions'}


def validate(obs):
    if set(obs) != FIELDS or obs['schema'] != 'growth.obs.v1': raise ValueError('observation_schema')
    if set(obs['needs']) != set(NEEDS): raise ValueError('needs_schema')
    if any(type(v) is not int or not 0 <= v <= 9 for v in obs['needs'].values()): raise ValueError('needs_value')
    if not isinstance(obs['world'],str) or len(obs['world']) != 32: raise ValueError('world_identity')
    if not 0 <= obs['light'] <= 1 or obs['radius'] not in (1,2,4): raise ValueError('visibility')
    for cell in obs['cells']:
        if set(cell) != {'dx','dy','material','entity'}: raise ValueError('cell_schema')
        if abs(cell['dx']) > obs['radius'] or abs(cell['dy']) > min(3,obs['radius']): raise ValueError('cell_visibility')
    # Serialize once to ensure no object references cross the boundary.
    return json.loads(json.dumps(obs, allow_nan=False))


def public_action(name, actions):
    if type(name) is not str or name not in actions: raise ValueError('action_denied')
    return name
