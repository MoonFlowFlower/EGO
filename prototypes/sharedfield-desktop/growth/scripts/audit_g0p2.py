"""Independent read-only reconciliation; never writes to runs/ or changes verdict criteria."""
import json
import random
import sqlite3
from collections import Counter
from pathlib import Path
from gate_common_v3 import ROOT,read,check_hashes
from growthlab.forks import file_hash
from growthlab.records import write_json
from growthlab.contract import validate
from growthlab.spatial import representation
from growthlab.decision import decode,decision_format,SYSTEM
from gate_perception_v31 import RUN,OUT,MODES,qa_messages,SCHEMA


def rows(path):return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()]


def oracle(obs):
    front=next(c for c in obs['cells'] if [c['dx'],c['dy']]==obs['facing']);state=front.get('visible_state') or {}
    expected={'material':front['material'],'entity':front['entity'] or 'none',
              'plant_ripe':state.get('plant_ripe'),'arrow_direction':state.get('arrow_direction','')}
    trees=[c for c in obs['cells'] if c['material']=='tree']
    distance=min((abs(c['dx'])+abs(c['dy']) for c in trees),default=None)
    targets=[{'visible':True,'dx':c['dx'],'dy':c['dy'],'steps':distance} for c in trees if abs(c['dx'])+abs(c['dy'])==distance]
    return {'front':expected,'nearest_trees':targets or [{'visible':False,'dx':0,'dy':0,'steps':0}]}


def audit():
    counts=Counter();manifest=read(RUN/'manifest.json');status=read(RUN/'status.json');reported=read(OUT/'G0p2.json')
    assert status.get('finished_unix'),'run_still_active'
    assert manifest==read(OUT/'G0p2_MANIFEST.json')
    check_hashes(manifest['source_sha256']);counts['frozen_sources']=len(manifest['source_sha256'])
    for path,sha in manifest['historical_sha256'].items():assert file_hash(ROOT/path)==sha,path
    counts['historical_files_unchanged']=len(manifest['historical_sha256'])
    excluded={(c['source'],c['line']) for c in manifest['excluded_cases']};rng=random.Random(manifest['sampling_seed']);sampled=[]
    sources=[]
    for c in manifest['cases']:
        if c['source'] not in sources:sources.append(c['source'])
    for source in sources:
        entries=[i for i,r in enumerate(rows(ROOT/source),1) if r['type']=='input' and (source,i) not in excluded]
        for index in sorted(rng.sample(range(len(entries)),20)):sampled.append((source,entries[index]))
    assert sampled==[(c['source'],c['line']) for c in manifest['cases']]
    jobs=[{'case':c['id'],'format':mode} for c in manifest['cases'] for mode in MODES];rng.shuffle(jobs)
    assert jobs==manifest['jobs'];counts['sampling_and_job_order_reproduced']=1
    cases={c['id']:c for c in manifest['cases']}
    for c in cases.values():
        assert file_hash(ROOT/c['source'])==c['source_sha256']
        source=rows(ROOT/c['source'])[c['line']-1]
        assert json.loads(source['messages'][1]['content'])['observation']==c['observation']
        validate(c['observation']);truth=oracle(c['observation'])
        assert truth['front']==c['answer']['front']
        assert sorted(truth['nearest_trees'],key=str)==sorted(c['answer']['nearest_trees'],key=str)
    counts['raw_observations_and_oracles']=len(cases)
    assert not set(manifest['debug_seeds']) & set(manifest['forbidden_pilot_seeds'])
    calls=rows(RUN/'calls.jsonl');requests=[r for r in calls if r['type']=='request'];responses=[r for r in calls if r['type']=='response']
    qa_requests=[r for r in requests if r['context']['stage']=='qa']
    for r in qa_requests:
        cid,label=r['context']['id'].rsplit('_',1)
        assert r['messages']==qa_messages(cases[cid],label) and r['response_format']==SCHEMA and r['max_tokens']==512
        assert not r.get('reasoning',False)
    counts['qa_requests']=len(qa_requests)
    qa_scores=Counter();qa_results={r['job']['case']+'_'+r['job']['format']:r for r in reported['qa_results']}
    sign=lambda x:(x>0)-(x<0)
    for response in responses:
        if response['context']['stage']!='qa':continue
        identity=response['context']['id'];r=qa_results[identity];cid,label=identity.rsplit('_',1);truth=oracle(cases[cid]['observation'])
        assert response['output']==r['output'] and response['meta']==r['meta']
        try:
            v=json.loads(r['output']);t=v['nearest_tree']
            assert set(v)=={'front','nearest_tree'} and set(t)=={'visible','dx','dy','steps'}
            assert type(t['visible']) is bool and all(type(t[k]) is int for k in ('dx','dy','steps'))
            computed={'front_exact':v['front']==truth['front'],
                      'tree_exact':t in truth['nearest_trees'],
                      'tree_direction':any(t['visible']==a['visible'] and sign(t['dx'])==sign(a['dx']) and sign(t['dy'])==sign(a['dy']) for a in truth['nearest_trees']),
                      'invalid':False}
        except (ValueError,KeyError,TypeError,AssertionError):computed={k:k=='invalid' for k in ('front_exact','tree_exact','tree_direction','invalid')}
        for k,value in computed.items():assert r['score'][k]==value;qa_scores[label,k]+=value
        qa_scores[label,'n']+=1
    for group in reported['qa_table']:
        for k in ('n','front_exact','tree_exact','tree_direction','invalid'):assert group[k]==qa_scores[group['format'],k]
    counts['qa_responses']=sum(qa_scores[label,'n'] for label in MODES)
    if all(qa_scores[label,'n']==60 for label in MODES):
        totals={k:qa_scores[k,'front_exact']+qa_scores[k,'tree_exact'] for k in ('K1','K2')}
        assert reported['selected']==('K1' if totals['K1']>totals['K2'] else 'K2')
    totals={arm:Counter() for arm in ('main','reasoning')};starts={};rejected_after_valid=[]
    for folder in sorted((RUN/'episodes').glob('*')):
        if not folder.is_dir():continue
        start=read(folder/'start.json');arm=start['arm'];assert start['records']==[]
        index=int(folder.name.split('_')[1]);assert start['seed']==manifest['debug_seeds'][index]
        connection=sqlite3.connect((folder/'state.sqlite').as_uri()+'?mode=ro',uri=True)
        observations=[json.loads(r[0])['observation'] for r in connection.execute("SELECT body FROM records WHERE kind='experience' AND json_extract(body,'$.type')='observation' ORDER BY rowid")]
        connection.close();trace=rows(folder/'trace.jsonl');inputs=[r for r in trace if r['type']=='input']
        assert len(observations)==len(inputs)
        if observations:
            initial={k:v for k,v in observations[0].items() if k!='world'}
            if index in starts:assert starts[index]==initial
            else:starts[index]=initial
        episode_responses=[r for r in responses if r['context'].get('episode')==folder.name]
        assessments=[r for r in trace if r['type']=='front_assessment'];assert len(assessments)==len(episode_responses)
        reqs=[r for r in requests if r['context'].get('episode')==folder.name]
        for request in reqs:
            i=request['context']['decision'];assert request['messages']==inputs[i]['messages']
            assert request['max_tokens']==manifest['arms'][arm]['max_tokens'] and request['reasoning']==manifest['arms'][arm]['reasoning']
            assert request['response_format']==decision_format(observations[i]['actions'])
        for obs,inp in zip(observations,inputs):
            validate(obs);packet=json.loads(inp['messages'][1]['content']);view=representation(obs,start['observation_format'])
            assert all(packet[k]==v for k,v in view.items()) and inp['messages'][0]['content']==SYSTEM
            assert all(set(r)<={'kind','action','name','execution_status','steps'} for r in packet['recent'])
            assert all('reason' not in r for r in packet['recent'])
            assert all(r.get('type')!='action_rule_prediction' for r in packet['memory'])  # empty B; no sleep updates
            counts['live_inputs_from_raw_observation']+=1
        for i,(obs,r) in enumerate(zip(observations,assessments)):
            expected={k:v for k,v in oracle(obs)['front'].items() if k in ('material','entity')}
            assert expected==r['expected'] and r['output']==episode_responses[i]['output']
            try:v=decode(r['output'],obs['actions']);correct=v['front_seen']==expected;valid=True
            except (ValueError,KeyError,TypeError):correct=False;valid=False
            assert r['correct']==correct and r['protocol_valid']==valid
            totals[arm]['n']+=1;totals[arm]['correct']+=correct
        previous_assessment=None
        for row in trace:
            if row['type']=='front_assessment':previous_assessment=row
            if row['type']=='rejected' and previous_assessment and previous_assessment['protocol_valid']:
                rejected_after_valid.append({'episode':folder.name,'tick':previous_assessment['tick'],'code':row['code']})
        totals[arm]['episodes']+=1;counts['live_requests']+=len(reqs)
    for arm,values in totals.items():
        assert values['n']==reported['live_arms'][arm]['n'] and values['correct']==reported['live_arms'][arm]['front_correct']
    # Rejected executions are exposed explicitly; never silently equate them
    # with valid accepted decisions when reviewing a boundary case.
    complete=len(status['live_completed'])==6 and status['qa_completed']==180 and not status['stop']
    sufficient=totals['main']['episodes']==3 and totals['main']['n']>=90
    qa_pass=bool(reported['selected'] and qa_scores[reported['selected'],'front_exact']>=54 and qa_scores[reported['selected'],'tree_direction']>=48)
    live_pass=sufficient and totals['main']['correct']*10>=totals['main']['n']*9
    batch_verdict='passed' if complete and sufficient and qa_pass and live_pass else ('failed' if complete and sufficient else 'unverified')
    assert batch_verdict==reported['verdict']
    # The frozen reporter combines whole-batch completion with the gate.
    # Keep that record, but the user explicitly excludes the reasoning arm
    # from gate criteria. Its interruption cannot change a complete main score.
    main_summaries=[read(p/'summary.json') for p in (RUN/'episodes').glob('main_*') if (p/'summary.json').exists()]
    main_complete=status['qa_completed']==180 and len(main_summaries)==3 and all(s['stop'] in (None,'decision_limit') for s in main_summaries)
    verdict='passed' if main_complete and sufficient and qa_pass and live_pass else ('failed' if main_complete and sufficient else 'unverified')
    for r in responses:
        assert r['meta']['provider']=='OpenInference'
        if r['context']['stage']=='qa':assert r['meta']['reasoning_enabled'] is False
        else:assert r['meta']['reasoning_enabled']==manifest['arms'][r['context']['episode'].split('_')[0]]['reasoning']
    counts['response_route_metadata']=len(responses)
    result={'audit_passed':True,'gate_verdict':verdict,'frozen_report_batch_verdict':batch_verdict,
            'reasoning_excluded_from_gate':True,'checks':dict(counts),'live_counts':{k:dict(v) for k,v in totals.items()},
            'execution_rejections_after_schema_valid_output':rejected_after_valid,
            'claim_ceiling':'Boundary reconciliation only; no learning conclusion. CPU temperature unverified.'}
    write_json(OUT/'BOUNDARY_AUDIT.json',result);print(result)
    return result


if __name__=='__main__':audit()
