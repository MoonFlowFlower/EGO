"""Summarize the predeclared P7 windows; never submit local conversation data."""
import collections
import hashlib
import json
from pathlib import Path
from growthlab.records import ROOT


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def main():
    candidates=[]
    for path in (ROOT/'runs/p7/body_connected_v2').glob('*/events.jsonl'):
        rows=read_rows(path)
        if any(row.get('kind')=='task_sent' for row in rows):candidates.append((path,rows))
    if len(candidates)!=1:raise ValueError('expected_one_fixed_task_run')
    path,rows=candidates[0]
    tasks={row['task']:row for row in rows if row.get('kind')=='task_sent'}
    states=[row for row in rows if row.get('kind')=='state' and row.get('state')]
    assert set(tasks)=={'follow','tree','pickaxe','stop'}
    assert all(not row['state']['generated_code_enabled'] for row in states)
    def window(task,seconds):
        start=tasks[task]['unix_ms']
        return [r for r in states if start<=r['unix_ms']<=start+seconds*1000]
    def successful_item(task,seconds,item):
        start=tasks[task]['initial_state']['inventory']['counts'].get(item,0)
        found=next((r for r in window(task,seconds) if r['state']['inventory']['counts'].get(item,0)>start),None)
        return None if found is None else (found['unix_ms']-tasks[task]['unix_ms'])/1000
    follow=window('follow',60)
    stop=window('stop',15)
    stop_command=next((r for r in rows if r.get('unix_ms',0)>=tasks['stop']['unix_ms'] and 'parsed command: {"commandName":"!stop"' in r.get('text','')),None)
    start_s=1791039870 # MC_CONNECTED_PRE_RUN.md: 2026-10-03 15:04:30 UTC
    events=[r for r in read_rows(ROOT/'runs/p7/proxy/events.jsonl') if r.get('unix_s',0)>=start_s]
    routes=[r for r in read_rows(ROOT/'runs/p7/proxy/routing.jsonl') if r.get('unix_s',0)>=start_s]
    charged=[r for r in events if r.get('charge_id')]
    result={
        'raw_relative_path':str(path.relative_to(ROOT)).replace('\\','/'),
        'raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'generated_code_enabled_samples':0,'state_samples':len(states),
        'spawn_observed':any('EgoP7 spawned.'==r.get('text') for r in rows),
        'protocol_read_error_count':sum('PartialReadError' in r.get('text','') for r in rows),
        'follow':{'window_s':60,'samples':len(follow),'owner_observed':any(r['state']['owner'] for r in follow),'initial_position':tasks['follow']['initial_state']['gameplay']['position'],'final_position':follow[-1]['state']['gameplay']['position'],'result':'NOT_DEMONSTRATED'},
        'tree':{'window_s':180,'first_oak_log_s':successful_item('tree',180,'oak_log'),'initial_inventory':tasks['tree']['initial_state']['inventory']['counts'],'inventory_before_next_task':tasks['pickaxe']['initial_state']['inventory']['counts'],'tree_location_before_input':'unknown','result':'INVENTORY_POSTCONDITION_MET'},
        'pickaxe':{'window_s':180,'samples':len(window('pickaxe',180)),'first_pickaxe_s':successful_item('pickaxe',180,'wooden_pickaxe'),'final_inventory':window('pickaxe',180)[-1]['state']['inventory']['counts'],'result':'FAIL'},
        'stop':{'initial_action':tasks['stop']['initial_state']['action'],'command_delay_s':None if stop_command is None else (stop_command['unix_ms']-tasks['stop']['unix_ms'])/1000,'samples_first_15s':len(stop),'all_idle':all(r['state']['action']['isIdle'] and not r['state']['digging'] and not any(r['state']['controls'].values()) for r in stop),'result':'IDLE_ACK_ONLY_NO_INTERRUPTION_PROOF'},
        'proxy':{'outcomes':dict(collections.Counter(r.get('outcome') for r in events)),'charged_events':len(charged),'reported_cost_usd':sum(r.get('cost_usd',0) or 0 for r in charged),'routes':sorted({(r.get('model'),r.get('route')) for r in routes if r.get('model')})},
        'owner_visible_bot':'not_confirmed','owner_15min_trial':'not_done','airi_mc':'blocked_generated_javascript','local_voice':'unavailable',
    }
    target=ROOT/'evidence/p7/MC_CONNECTED_RESULTS.json'
    target.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
