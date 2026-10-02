import argparse
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.state import Store
from growthlab.records import EVIDENCE,RUNS,write_json,telemetry,digest


def main():
    p=argparse.ArgumentParser();p.add_argument('--read');p.add_argument('--world');a=p.parse_args()
    if a.read:
        s=Store(a.read);print(json.dumps(s.load(a.world),sort_keys=True));s.close();return
    start=time.perf_counter(); samples=[telemetry()]; checks={}
    path=RUNS/f'p6_{uuid.uuid4().hex}.sqlite';s=Store(path); w1,w2=uuid.uuid4().hex,uuid.uuid4().hex
    s.put('map',{'home':[0,0]},'synthetic',world=w1)
    s.put('project',{'type':'world','goal':'shelter'},'synthetic',world=w1)
    s.put('project',{'type':'skill','goal':'practice'},'synthetic')
    skill=s.put('skill',{'code':"act('noop')"},'inherited')
    s.put('preference',{'practice':'short'},'synthetic')
    fact=s.put('fact',{'x':1},'synthetic',world=w1)
    revised=s.correct(fact,{'x':2},'correction')
    checks['superseded_retained']=s.db.execute('SELECT status FROM records WHERE id=?',(fact,)).fetchone()[0]=='superseded'
    checks['active_revision_only']=fact not in {r['id'] for r in s.load(w1)} and revised in {r['id'] for r in s.load(w1)}
    checks['new_world_excludes_old_map_project_fact']=len(s.load(w2))==3
    marker='SYNTHETIC_PRIVATE_'+uuid.uuid4().hex
    root=s.put('experience',{'text':marker},'synthetic_private',personal=True)
    prev=root
    for kind in ('summary','index','cache','profile'):
        prev=s.put(kind,{'text':marker},'derived',parents=[prev])
    s.correct(root,{'text':marker+' correction'},'correction')
    checks['personal_not_in_game_context']=marker not in json.dumps(s.load(w1))
    deleted=s.delete_private(root)
    checks['deleted_transitive_records']=deleted==6
    checks['marker_absent_sql']=marker not in str(s.db.execute('SELECT * FROM records').fetchall())
    before=s.load(w1);s.switch_model('stub-A');s.switch_model('stub-B')
    checks['model_switch_state_equal']=s.load(w1)==before
    s.close()
    checks['marker_absent_database_bytes']=marker.encode() not in path.read_bytes()
    child=subprocess.run([sys.executable,__file__,'--read',str(path),'--world',w1],capture_output=True,text=True,check=True)
    checks['new_process_reload_equal']=json.loads(child.stdout)==before
    samples.append(telemetry())
    write_json(EVIDENCE/'p6_state.json',{'seconds':time.perf_counter()-start,'checks':checks,
        'deleted_records':deleted,'retained_active_records':len(before),'before_after_digest':digest(before),
        'model_switch_scope':'two provider labels; no real model behavior comparison','telemetry':samples})
    assert all(checks.values()),checks
    print(json.dumps(checks,indent=2))


if __name__=='__main__':main()
