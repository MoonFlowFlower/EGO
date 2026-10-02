import copy,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.variants import generate,arena
from growthlab.records import EVIDENCE,write_json
start=time.perf_counter();base=generate('rename',42);base['aliases']={};other=copy.deepcopy(base)
other['make']['wood_pickaxe']['uses']={'wood':3}
rows=[];ids=[]
for world,rules in [('A',base),('B',other)]:
    for name,actions in [('direct',['make_wood_pickaxe']),('universal',['do','make_wood_pickaxe']),
                         ('diagnose_then_gather',['make_wood_pickaxe','do','make_wood_pickaxe'])]:
        h=arena(rules);ids.append(h.world)
        for action in actions:h.act(action)
        rows.append({'world_evaluator_only':world,'strategy':name,'steps':len(actions),'wood_pickaxe':h.observe()['inventory']['wood_pickaxe']})
checks={'A_optimal_1_step':rows[0]['wood_pickaxe']==1,
        'B_direct_fails':rows[3]['wood_pickaxe']==0,
        'universal_2_steps_both_succeed':rows[1]['wood_pickaxe']>=1 and rows[4]['wood_pickaxe']>=1,
        'world_ids_random_v4':all(uuid.UUID(x).version==4 for x in ids) and len(set(ids))==len(ids)}
result={'seconds':time.perf_counter()-start,'rows':rows,'checks':checks,
    'information_channel':'P1 inventory delta after make_wood_pickaxe','diagnostic_cost_steps':1,
    'optimal_steps':{'A':1,'B':2},'universal_steps':{'A':2,'B':2},'universal_excess_steps':{'A':1,'B':0},
    'suitability':'not suitable for success-only rule-recognition test; only 1 step overhead in A, zero in B',
    'lower_bound':'A needs at least a make action; B starts with 2 wood and requires 3, so at least one collection plus one make. Facing tree permits do immediately.'}
write_json(EVIDENCE/'p4_v03.json',result);assert all(checks.values()),checks;print(checks)
