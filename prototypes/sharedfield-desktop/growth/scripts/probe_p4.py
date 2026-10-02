import copy
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from growthlab.variants import generate,check_rules,arena
from growthlab.records import EVIDENCE,write_json,telemetry,digest

start=time.perf_counter();rows=[];samples=[telemetry()]
for kind in ('rename','recipe','consequence','composition'):
    rules=generate(kind,42);h=arena(rules)
    # Open-loop evaluator witness, no privileged policy input; map fixed above.
    actions=['move_right','do','move_up','do','move_down','do','make_wood_pickaxe','make_wood_sword']
    for act in actions:h.act(rules['aliases'].get(act,act))
    rows.append({'kind':kind,'structural_check':check_rules(rules),'witness_steps':len(actions),
                 'wood_pickaxe_achievement':h.env._player.achievements['make_wood_pickaxe'],
                 'wood_sword_achievement':h.env._player.achievements['make_wood_sword']})
base=generate('rename',42);base['aliases']={}
different=copy.deepcopy(base);different['make']['wood_pickaxe']['uses']={'wood':3}
a,b=arena(base),arena(different);checks={}
checks['paired_pixels_equal_before_actions']=np.array_equal(a.render(),b.render())
oa,ob=a.observe(),b.observe();oa.pop('world');ob.pop('world')
checks['paired_public_observation_equal']=oa==ob
a.act('make_wood_pickaxe');b.act('make_wood_pickaxe')
checks['same_action_different_consequence']=a.observe()['inventory']['wood_pickaxe']==1 and b.observe()['inventory']['wood_pickaxe']==0
for action in ('move_right','do','make_wood_pickaxe'):b.act(action)
checks['second_world_alternative_witness']=b.observe()['inventory']['wood_pickaxe']==1
invalid=copy.deepcopy(base);invalid['make']['wood_pickaxe']['uses']={'wood':10}
checks['over_cap_rejected']=not check_rules(invalid)['accepted']
invalid=copy.deepcopy(base);invalid['make']['wood_pickaxe']['uses']={'stone':1}
checks['circular_dependency_rejected']=not check_rules(invalid)['accepted']
checks['all_four_actual_witnesses']=all(r['wood_pickaxe_achievement']==1 and r['wood_sword_achievement']==1 for r in rows)
samples.append(telemetry())
write_json(EVIDENCE/'p4_variants.json',{'seconds':time.perf_counter()-start,'rows':rows,'checks':checks,
    'paired_actions':{'world_a':['make_wood_pickaxe'],'world_b':['move_right','do','make_wood_pickaxe']},'telemetry':samples})
assert all(checks.values()),checks
print(checks)
