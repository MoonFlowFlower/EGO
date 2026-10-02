import json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.state import Store
from growthlab.records import EVIDENCE,RUNS,write_json
start=time.perf_counter();path=RUNS/f'p6_v03_{uuid.uuid4().hex}.sqlite';s=Store(path);checks={}
a,b=uuid.uuid4().hex,uuid.uuid4().hex
experience=s.put('experience',{'event':'tree'},'synthetic',world=a)
mapa=s.put('map',{'tree':[0,1]},'synthetic',world=a,parents=[experience])
skill=s.put('skill',{'code':"act('do')"},'synthetic_generalization',parents=[experience])
loaded={r['id'] for r in s.load(b)}
checks['world_a_experience_to_global_skill_in_b']=skill in loaded
checks['world_a_map_not_in_b']=mapa not in loaded
checks['provenance_link_retained']=s.db.execute('SELECT relation FROM deps WHERE child=? AND parent=?',(skill,experience)).fetchone()==('derived',)
try:s.put('map',{},'invalid',world=b,parents=[experience]);checks['cross_world_map_denied']=False
except ValueError:checks['cross_world_map_denied']=True
marker='PRIVATE_CHAIN_'+uuid.uuid4().hex
v1=s.put('experience',{'text':marker},'synthetic',personal=True)
v2=s.correct(v1,{'text':marker+' v2'},'correction');v3=s.correct(v2,{'text':marker+' v3'},'correction')
for v in (v1,v2,v3):s.put('summary',{'text':marker},'derived',parents=[v])
deleted=s.delete_private(v2)
checks['delete_new_version_removes_all_six']=deleted==6
checks['old_versions_absent']=not list(s.db.execute('SELECT id FROM records WHERE id IN (?,?,?)',(v1,v2,v3)))
checks['unrelated_skill_survives']=skill in {r['id'] for r in s.load(b)}
s.close();checks['private_marker_absent_database_bytes']=marker.encode() not in path.read_bytes()
write_json(EVIDENCE/'p6_v03.json',{'seconds':time.perf_counter()-start,'checks':checks,'deleted_records':deleted})
assert all(checks.values()),checks
print(checks)
