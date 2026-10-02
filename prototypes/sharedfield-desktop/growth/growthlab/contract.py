"""Pure JSON policy contract: no crafter import and no host capabilities."""
import json
import re

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
    if set(obs) != FIELDS or obs['schema'] not in ('growth.obs.v1','growth.obs.v1.1'): raise ValueError('observation_schema')
    if set(obs['needs']) != set(NEEDS): raise ValueError('needs_schema')
    if any(type(v) is not int or not 0 <= v <= 9 for v in obs['needs'].values()): raise ValueError('needs_value')
    if not isinstance(obs['world'],str) or not re.fullmatch('[0-9a-f]{32}',obs['world']): raise ValueError('world_identity')
    if not 0 <= obs['light'] <= 1 or obs['radius'] not in (1,2,4): raise ValueError('visibility')
    if type(obs['tick']) is not int or obs['tick']<0:raise ValueError('tick_value')
    if type(obs['done']) is not bool or type(obs['sleeping']) is not bool:raise ValueError('bool_value')
    if obs['facing'] not in [[1,0],[-1,0],[0,1],[0,-1]] or obs['displacement'] not in [[0,0],[1,0],[-1,0],[0,1],[0,-1]]:raise ValueError('motion_value')
    def symbol(x,known):return type(x) is str and (x in known or re.fullmatch(r's\d{3}',x))
    if len(obs['actions'])!=17 or len(set(obs['actions']))!=17 or any(not symbol(x,ACTIONS) for x in obs['actions']):raise ValueError('actions_value')
    if len(obs['inventory'])!=12 or any(not symbol(k,ITEMS) or type(v) is not int or not 0<=v<=9 for k,v in obs['inventory'].items()):raise ValueError('inventory_value')
    positions=set()
    for cell in obs['cells']:
        expected_fields={'dx','dy','material','entity'}|({'visible_state'} if obs['schema']=='growth.obs.v1.1' else set())
        if set(cell) != expected_fields: raise ValueError('cell_schema')
        if type(cell['dx']) is not int or type(cell['dy']) is not int:raise ValueError('cell_position')
        if abs(cell['dx']) > obs['radius'] or abs(cell['dy']) > min(3,obs['radius']): raise ValueError('cell_visibility')
        if not symbol(cell['material'],MATERIALS) or (cell['entity'] is not None and not symbol(cell['entity'],ENTITIES)):raise ValueError('cell_symbol')
        positions.add((cell['dx'],cell['dy']))
        state=cell.get('visible_state')
        if state is not None:
            if not isinstance(state,dict):raise ValueError('visible_state_schema')
            if set(state)=={'plant_ripe'}:
                if type(state['plant_ripe']) is not bool:raise ValueError('plant_state')
            elif set(state)=={'arrow_direction'}:
                if state['arrow_direction'] not in ('up','down','left','right'):raise ValueError('arrow_state')
            else:raise ValueError('visible_state_denied')
    expected=(2*obs['radius']+1)*(2*min(3,obs['radius'])+1)
    if len(positions)!=expected or len(obs['cells'])!=expected:raise ValueError('cell_coverage')
    # Serialize once to ensure no object references cross the boundary.
    return json.loads(json.dumps(obs, allow_nan=False))


def public_action(name, actions):
    if type(name) is not str or name not in actions: raise ValueError('action_denied')
    return name
