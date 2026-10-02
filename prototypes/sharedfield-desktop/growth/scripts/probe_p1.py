import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.host import Host, walk_until
from growthlab.contract import ACTIONS, ITEMS, MATERIALS, ENTITIES
from growthlab.records import EVIDENCE, write_json, telemetry

start=time.perf_counter(); h=Host(); checks={}; samples=[telemetry()]
counts=[]
for light in (1.,.49,.19):
    h.env._world.daylight=light
    o=h.observe(); counts.append(len(o['cells']))
    checks[f'visibility_{light}']=max(abs(c['dx']) for c in o['cells']) == o['radius']
# Fixture sets local adjacent wall; evaluator only, not an adapter input.
p=h.env._player
h.env._world[p.pos+(-1,0)]='stone'
checks['blocked_displacement_zero']=h.act('move_left')['displacement']==[0,0]
checks['host_does_not_construct_semantic_map']=h.env._sem_view() is None
before=h.env._step
try: h.act('__import__')
except ValueError: pass
checks['invalid_action_no_step']=h.env._step==before
checks['bounded_macro']=walk_until(h,'move_right','never',8)<=8
names=set(ACTIONS+ITEMS+MATERIALS+ENTITIES)
aliases={name:f's{i:03}' for i,name in enumerate(sorted(names))}
a=Host(aliases=aliases); obs=a.observe()
checks['renamed_action_inventory_cells']=not (set(obs['actions'])|set(obs['inventory'])|{c['material'] for c in obs['cells']}) & names
checks['no_privileged_keys']=all(x not in json.dumps(obs) for x in ('semantic','player_pos','achievements','recipe','seed','_world'))
checks['fresh_world_identity']=Host().world != h.world
samples.append(telemetry())
result={'seconds':time.perf_counter()-start,'checks':checks,'visible_cell_counts_day_dusk_night':counts,'telemetry':samples}
write_json(EVIDENCE/'p1_observation.json',result)
assert all(checks.values()), result
print(json.dumps(result,indent=2))
