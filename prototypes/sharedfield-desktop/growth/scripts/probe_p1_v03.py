import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from crafter.objects import Plant,Arrow
from growthlab.host import Host
from growthlab.records import EVIDENCE,write_json
start=time.perf_counter();h=Host();w=h.env._world;p=h.env._player
for obj in w.objects:
    if obj is not p:w.remove(obj)
plant=Plant(w,p.pos+(1,0));w.add(plant)
arrow=Arrow(w,p.pos+(0,1),(0,-1));w.add(arrow)
def cell(dx,dy):return next(x for x in h.observe()['cells'] if (x['dx'],x['dy'])==(dx,dy))
checks={};checks['unripe_texture_state']=cell(1,0)['visible_state']=={'plant_ripe':False}
plant.grown=301;checks['ripe_texture_state']=cell(1,0)['visible_state']=={'plant_ripe':True}
for facing,label in [((1,0),'right'),((-1,0),'left'),((0,1),'down'),((0,-1),'up')]:
    arrow.facing=facing;checks['arrow_'+label]=cell(0,1)['visible_state']=={'arrow_direction':label}
w.move(plant,p.pos+(3,0));w.daylight=.1
checks['night_hidden_plant_not_emitted']=not any(x['visible_state'] and 'plant_ripe' in x['visible_state'] for x in h.observe()['cells'])
checks['hud_counters_not_added']=all(set(x)<= {'dx','dy','material','entity','visible_state'} for x in h.observe()['cells'])
write_json(EVIDENCE/'p1_v03.json',{'seconds':time.perf_counter()-start,'checks':checks,'schema':'growth.obs.v1.1'})
assert all(checks.values()),checks
print(checks)
