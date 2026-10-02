import copy,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.host import Host
from growthlab.contract import validate
from growthlab.sandbox import parse,Denied
from growthlab.records import EVIDENCE,write_json
start=time.perf_counter();obs=Host().observe();checks={}
for name,mutate in [('extra_top',lambda x:x.update(semantic=[])),
        ('extra_cell',lambda x:x['cells'][0].update(secret='x')),
        ('inventory_payload',lambda x:x['inventory'].update(wood='secret')),
        ('material_payload',lambda x:x['cells'][0].update(material='SECRET_PAYLOAD')),
        ('world_payload',lambda x:x.update(world='X'*32))]:
    fixture=copy.deepcopy(obs);mutate(fixture)
    try:validate(fixture);checks[name]=False
    except ValueError:checks[name]=True
try:parse('for _ in x.y():\n act("noop")');checks['malformed_for_denied']=False
except Denied:checks['malformed_for_denied']=True
write_json(EVIDENCE/'boundary_recheck.json',{'seconds':time.perf_counter()-start,'checks':checks})
assert all(checks.values()),checks
print(checks)
