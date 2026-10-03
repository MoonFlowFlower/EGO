"""Audit every launched pilot trace, including cancelled prefixes, read-only."""
import json
import math
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.records import ROOT,write_json
from growthlab.contract import validate
from growthlab.changes import changes
from growthlab.memory import compact
from growthlab.decision import SYSTEM,RECENT,MEMORY_TOKENS
from growthlab.forks import file_hash
from growthlab.consolidation import A_SYSTEM,B_SYSTEM
from report_phase1 import trace_rows,trace_metrics


def main():
    folder=ROOT/'runs/phase1/pilot';manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    checks=Counter();errors=[];unverified=[];partial_tails=[]
    status=json.loads((folder/'status.json').read_text(encoding='utf8'))
    report=json.loads((ROOT/'evidence/phase1/pilot_summary.json').read_text(encoding='utf8'))
    raw_files=[p for p in folder.rglob('*') if p.is_file()]
    raw_hashes={str(p.relative_to(ROOT)):file_hash(p) for p in raw_files}
    assert report['status']==status and report['manifest']==manifest
    assert len(report['attempts'])==len(list((folder/'episodes').glob('*/job.json')))
    assert sum(r['completed'] for r in report['attempts'])==len(status['completed'])
    checks['report_status_manifest_and_attempt_count']=1
    for source,expected in manifest['source_sha256'].items():
        if file_hash(ROOT/source)!=expected:errors.append({'source':source,'error':'frozen_source_changed'})
        else:checks['frozen_source']+=1
    for job_path in sorted((folder/'episodes').glob('*/job.json')):
        job=json.loads(job_path.read_text(encoding='utf8'));summary=job_path.parent/'summary.json'
        if summary.exists():
            info=json.loads(summary.read_text(encoding='utf8'))
            try:
                assert info['source_unchanged']
                assert file_hash(info['job']['source'])==info['fork']['source_sha256']
                checks['independent_source_unchanged']+=1
            except (KeyError,AssertionError):errors.append({'episode':summary.parent.name,'error':'source_snapshot'})
        else:unverified.append({'episode':summary.parent.name,'check':'worker source-copy hash attestation absent after cancellation'})
        trace=summary.parent/'trace.jsonl';last_type=None;last_decision=None
        rows,tail=trace_rows(trace)
        if tail:partial_tails.append({'episode':summary.parent.name,**tail})
        observed=trace_metrics(rows,manifest)
        reported=next(r for r in report['attempts'] if r['episode_id']==summary.parent.name)
        for field in ('steps','failure_attempts','decisions','cloud_calls','events','prediction_eligible_actions',
                      'predicted_actions','prediction_count','prediction_matches','reported_cost_usd'):
            actual=observed[field];stored=reported[field]
            equal=math.isclose(actual,stored,abs_tol=1e-12) if isinstance(actual,float) else actual==stored
            if not equal:errors.append({'episode':summary.parent.name,'error':'summary_metric_mismatch','field':field})
            else:checks['trace_metrics_match_report']+=1
        checks['attempt_traces']+=1
        for row in rows:
            try:
                if row['type']=='input':
                    assert row['messages'][0]=={'role':'system','content':SYSTEM}
                    packet=json.loads(row['messages'][1]['content'])
                    assert set(packet)<= {'observation','goal','memory','recent','previous_changes','fixed_teaching'}
                    validate(packet['observation']);assert len(packet['recent'])<=RECENT
                    assert len(packet['previous_changes'])<=8
                    assert len(compact(packet['memory']).encode())<=MEMORY_TOKENS
                    if 'fixed_teaching' in packet:
                        assert packet['fixed_teaching']==manifest['fixed_teaching']
                        assert job['phase']=='practice' and job['group']=='F1_teach' and job['index']==0
                    checks['allowed_decision_inputs']+=1
                elif row['type']=='decision':last_decision=row
                elif row['type']=='step':
                    assert last_decision is not None
                    before,after=validate(row['before']),validate(row['observation'])
                    assert row['change']['action'] in before['actions']
                    assert row['change']==changes(before,after,row['change']['action'])
                    assert last_type=='prediction'
                    assert set(row['change'])=={'action','tick','effects','other_needs','events'}
                    assert last_decision['tick']<after['tick']
                    checks['whitelisted_steps_and_noncausal_changes']+=1
                elif row['type']=='sleep_input':
                    assert row['messages'][0]=={'role':'system','content':B_SYSTEM if job['arm']=='B' else A_SYSTEM}
                    packet=json.loads(row['messages'][1]['content'])
                    assert set(packet)=={'goal','actions','memory','experiences'}
                    assert len(compact(packet['memory']).encode())<=MEMORY_TOKENS
                    checks['bounded_consolidation_inputs']+=1
            except (ValueError,KeyError,TypeError,AssertionError) as error:
                errors.append({'episode':summary.parent.name,'event_type':row['type'],'error':type(error).__name__})
            last_type=row['type']
    after_hashes={str(p.relative_to(ROOT)):file_hash(p) for p in raw_files}
    if raw_hashes!=after_hashes:errors.append({'error':'audit_modified_raw_files'})
    else:checks['raw_files_unchanged_during_audit']=len(raw_files)
    result={'passed':not errors,'checks':dict(checks),'errors':errors,'unverified':unverified,
        'interrupted_partial_lines':partial_tails,'raw_evidence_sha256':raw_hashes,
        'scope':'All 8 launched pilot attempts including cancelled written prefixes. Actual allowlisted packet shapes, byte limits, action/change derivation, fixed teaching schedule, frozen source hashes, report reconciliation. Independent snapshot attestations only where worker summary exists (6/8). Missing future responses/actions are not audited or imputed. Semantic absence of arbitrary private information in model text is not proven by keyword scanning; pilot stores only game data.'}
    write_json(ROOT/'evidence/phase1/BOUNDARY_AUDIT.json',result);print(result)
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
