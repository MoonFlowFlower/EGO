import collections
import hashlib
import json
import math
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

root = Path.cwd()
load = lambda p: json.loads(Path(p).read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
readlines = lambda p: [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
result = load(root/'evidence/u1_resume/results.json')
assert result['status'] != 'running', 'wait_for_completion'
data = load(root/'evidence/u1/scripts_v1.json')
cases = {c['case_id']:c for c in data['ua_cases']+data['chain_cases']}
issues=[]
def check(value, name):
    if not value: issues.append(name)
hashes=[]
for name in ('u1/frozen_v1.json','u1_resume/frozen_v1.json','routing/frozen_v1.json','routing/frozen_v2.json','luna/frozen_v1.json','p7/BODY_FREEZE.json'):
    manifest=load(root/'evidence'/name)
    sources={**manifest.get('source_sha256',manifest.get('sources',{})),**manifest.get('artifact_sha256',{})}
    mismatches=[p for p,h in sources.items() if sha(root/p)!=h]
    check(not mismatches,'hash:'+name)
    hashes.append({'manifest':name,'sha256':sha(root/'evidence'/name),'files':len(sources),'mismatches':mismatches})
old=load(root/'evidence/u1/frozen_v1.json');new=load(root/'evidence/u1_resume/frozen_v1.json')
for name in ('ua','ub','uc','chain'): check(old[name]==new[name],'inherited_criteria:'+name)
responses={};requests=[];errors=[];waits=[];decisions=[];resources=[];wire_count=0
for path in sorted((root/'runs/u1_resume/v1').rglob('calls.jsonl')):
    previous=None;latest_request=None;latest_wire=None
    for row in readlines(path):
        kind=row.get('record_type')
        if kind=='request':
            if previous:
                check(row['unix_s']-previous['unix_s']>=row['config']['minimum_start_interval_s']-.01,'spacing:'+str(path))
            previous=row;latest_request=row;requests.append(row)
        elif kind=='wire_request':
            wire_count+=1
            check(row['payload']['messages']==latest_request['messages'],'wire_messages')
        elif kind=='wire_response': latest_wire=row['response']
        elif kind=='response':
            cid=row['meta']['charge_id'];check(cid not in responses,'duplicate_charge')
            check(latest_wire['choices'][0]['message'].get('content','')==row['output'],'raw_output')
            responses[cid]=(row,latest_request)
        elif kind=='transport_error': errors.append(row)
        elif kind=='retry_wait': waits.append(row)
        elif kind=='telemetry': resources.append(row)
    dpath=path.parent/'decisions.jsonl'
    if dpath.exists():
        decisions += [dict(run=path.parent.relative_to(root/'runs/u1_resume').as_posix(),**r) for r in readlines(dpath)]
valid_count=0
for row in decisions:
    response,request=responses[row['meta']['charge_id']]
    case=cases[row['case_id']];fixture=data['conventions'][case['fixture_id']]
    context=row['context'];label=('false' if context.get('condition')=='false' else 'true') if context['phase']=='Ua' else ('new' if context['phase']=='corrected' else 'true')
    target=fixture['target'][label]
    try:
        pairs=json.loads(response['output'],object_pairs_hook=lambda p:p)
        assert isinstance(pairs,list) and [k for k,_ in pairs]==['reason','interpretation','action','reply']
        selected=dict(pairs)
        assert all(isinstance(v,str) for v in selected.values())
        assert len(selected['reason'])<=500 and len(selected['reply'])<=500
        for field in ('interpretation','action'): assert selected[field] in [x['choice_id'] for x in case[field+'_choices']]
        valid_count+=1
    except (AssertionError,TypeError,ValueError): selected=None
    scored=bool(selected and all(selected[k]==target[k] for k in ('interpretation','action')))
    check(row['selected']==selected and row['valid']==bool(selected),'parse:'+row['case_id'])
    check(row['target']==target and row['follows']==scored,'score:'+row['case_id'])
    packet=json.loads(request['messages'][-1]['content'])
    memory_bytes=len(json.dumps(packet['memory'],ensure_ascii=False,separators=(',',':')).encode())
    check(row['memory_bytes']==memory_bytes and memory_bytes<=2048,'memory_bound')
    check('target' not in packet and 'keywords' not in packet,'answer_leak')
    row['recomputed']=scored
table=collections.defaultdict(lambda:[0,0])
for r in decisions:
    key=(r['run'],r['arm'],r['family'],r['split'],r['context'].get('condition',''))
    table[key][0]+=1;table[key][1]+=r['recomputed']
steps=result.get('steps',{})
restart=[]
for group in ('B_R','B_I','B_N','A_R'):
    a,b=steps[group+'_learn'],steps[group+'_initial']
    row={'group':group,'learn_pid':a['pid'],'test_pid':b['pid'],'state_matches':a['state_sha256']==b['state_before_sha256'],'read_only':b['state_before_sha256']==b['state_after_sha256']}
    check(a['pid']!=b['pid'] and row['state_matches'] and row['read_only'],'restart:'+group);restart.append(row)
deletion=[]
for group in ('B_R','A_R'):
    state=root/'runs/u1_resume/v1/chain'/f'{group}.sqlite'
    with sqlite3.connect(state.resolve().as_uri()+'?mode=ro',uri=True) as db:
        count=db.execute('SELECT COUNT(*) FROM records').fetchone()[0]
    info=steps[group+'_delete'];check(count==0 and info['remaining_records']==0 and info['byte_check']['pass'],'delete:'+group)
    needles=set()
    def collect(value):
        if isinstance(value,dict):
            for key,v in value.items():
                if key in ('utterance_text','meaning','reflection_text') and isinstance(v,str) and v: needles.add(v)
                collect(v)
        elif isinstance(value,list):
            for v in value: collect(v)
    for callfile in (state.parent/group).rglob('calls.jsonl'):
        for row in readlines(callfile):
            if row.get('record_type')=='request': collect(json.loads(row['messages'][-1]['content']))
            if row.get('record_type')=='response': collect(json.loads(row['output']))
    checked=list(state.parent.glob(state.name+'*'))
    hits=[p.name for p in checked if any(n.encode(encoding) in p.read_bytes() for n in needles for encoding in ('utf-8','utf-16-le'))]
    check(not hits,'independent_byte_scan:'+group)
    deletion.append({'group':group,'records':count,'worker_byte_check':info['byte_check'],'independent_needles':len(needles),'files':[p.name for p in checked],'hits':hits})
def count(group,family,phase='initial',label='true'):
    rows=[r for r in decisions if r['context'].get('group')==group and r['context']['phase']==phase and r['family']==family and r['split']=='T1']
    target=data['conventions']['chain_'+family]['target'][label]
    return len(rows),sum(bool(r['selected']) and all(r['selected'][k]==target[k] for k in ('interpretation','action')) for r in rows)
retention=all(count('B_R',f)[0]==10 and count('B_R',f)[1]>=8 for f in ('code','promise'))
causal=count('B_R','code')[1]>=8 and all(count(g,'code')[0]==10 and count(g,'code')[1]<=2 for g in ('B_I','B_N'))
provenance=steps['B_R_correct_learn']['state']['provenance']
linked={}
for f in ('code','emotion','promise'):
    cards=[c for c in provenance if c['trigger_text']==data['conventions']['chain_'+f]['trigger']['text']]
    active=[c for c in cards if c['card_status']=='active'];oldids={c['card_id'] for c in cards if c['card_status']=='superseded'}
    linked[f]=len(active)==1 and all(c['correction_parents'] and set(c['correction_parents'])<=oldids for c in active)
correction=all(linked[f] and count('B_R',f,'corrected','new')[0]==10 and count('B_R',f,'corrected','new')[1]>=8 for f in ('code','promise'))
deleted=all(d['records']==0 and not d['hits'] for d in deletion) and all(count('B_R',f,'deleted',label)[0]==10 and count('B_R',f,'deleted',label)[1]<=count('B_N',f,label=label)[1]+1 for f in ('code','promise') for label in ('true','new'))
gates={'retention_pass':retention,'causal_pass':causal,'correction_pass':correction,'deletion_pass':deleted}
check(all(result['chain'][k]==v for k,v in gates.items()),'independent_chain_gates')
with sqlite3.connect((root/'runs/phase1/budget.sqlite').resolve().as_uri()+'?mode=ro',uri=True) as db:
    ledger={i:(amount,status) for i,amount,status in db.execute('SELECT id,usd,status FROM charges')}
for cid,(r,_) in responses.items():
    check(cid in ledger and math.isclose(ledger[cid][0],r['meta']['cost_usd'],rel_tol=0,abs_tol=1e-12),'settlement:'+cid)
strong=[r for r in requests if r['config']==new['configs']['stronger']]
check(len(strong)==2 and strong[0]['messages']==strong[1]['messages'] and strong[0]['response_format']==strong[1]['response_format'],'identical_retry')
check(len(waits)==2,'retry_wait_count')
for wait in waits:
    pair=[r for r in requests if r['pid']==wait['pid'] and r['context']==wait['context']]
    check(len(pair)==2 and pair[0]['attempt']==1 and pair[1]['attempt']==2,'retry_pair')
    check(pair[0]['messages']==pair[1]['messages'] and pair[0]['response_format']==pair[1]['response_format'],'identical_retry_pair')
    check(pair[1]['unix_s']-wait['unix_s']>=wait['delay_s'] and wait['delay_s']>=max(30,wait['retry_after_s']),'retry_wait')
check(len(decisions)==630 and len(requests)==len(responses)+len(errors)==wire_count,'counts')
check(all(r['ac_online'] is True for r in resources),'ac')
lat=sorted(r['meta']['latency_s'] for r,_ in responses.values())
gpu=[list(map(float,r['gpu_csv_C_MHz_MiB_W'].split(','))) for r in resources if r.get('gpu_returncode')==0 and r.get('gpu_csv_C_MHz_MiB_W')]
out={'reviewed_at_utc':datetime.now(timezone.utc).isoformat(),'paid_calls_added':0,'audit_pass':not issues,'issues':issues,'scientific_status':result['status'],
     'hashes':hashes,'requests':len(requests),'wire_requests':wire_count,'responses':len(responses),'transport_errors':len(errors),'decision_count':len(decisions),'valid_decisions':valid_count,
     'reported_cost_usd':sum(r['meta']['cost_usd'] for r,_ in responses.values()),'latency_median_s':statistics.median(lat),'latency_p95_s':lat[math.ceil(len(lat)*.95)-1],
     'shared_ledger_occupancy_usd':sum(x[0] for x in ledger.values()),'shared_reserved_usd':sum(x[0] for x in ledger.values() if x[1]!='reported'),
     'retry_waits':waits,'restart':restart,'deletion':deletion,'independent_chain_gates':gates,'table':[dict(zip(('run','arm','family','split','condition'),k),n=v[0],follows=v[1]) for k,v in table.items()],
     'resource_samples':len(resources),'all_ac':all(r['ac_online'] is True for r in resources),'gpu_min':[min(g[i] for g in gpu) for i in range(4)],'gpu_max':[max(g[i] for g in gpu) for i in range(4)]}
(root/'evidence/u1_resume/ROOT_AUDIT.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('table','hashes','restart','deletion','retry_waits')},ensure_ascii=False,indent=2))
if issues:
    raise SystemExit(1)
