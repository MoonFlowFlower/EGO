"""Audit actual finished-episode boundaries, never modify trial state."""
import json
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


def main():
    folder=ROOT/'runs/phase1/pilot';manifest=json.loads((folder/'manifest.json').read_text(encoding='utf8'))
    checks=Counter();errors=[]
    for source,expected in manifest['source_sha256'].items():
        if file_hash(ROOT/source)!=expected:errors.append({'source':source,'error':'frozen_source_changed'})
        else:checks['frozen_source']+=1
    for summary in (folder/'episodes').glob('*/summary.json'):
        info=json.loads(summary.read_text(encoding='utf8'))
        try:
            assert info['source_unchanged']
            assert file_hash(info['job']['source'])==info['fork']['source_sha256']
            checks['independent_source_unchanged']+=1
        except (KeyError,AssertionError):errors.append({'episode':summary.parent.name,'error':'source_snapshot'})
        trace=summary.parent/'trace.jsonl';last_type=None;last_decision=None
        for line in trace.read_text(encoding='utf8').splitlines():
            row=json.loads(line)
            try:
                if row['type']=='input':
                    assert row['messages'][0]=={'role':'system','content':SYSTEM}
                    packet=json.loads(row['messages'][1]['content'])
                    assert set(packet)<= {'observation','goal','memory','recent','previous_changes','fixed_teaching'}
                    validate(packet['observation']);assert len(packet['recent'])<=RECENT
                    assert len(packet['previous_changes'])<=8
                    assert len(compact(packet['memory']).encode())<=MEMORY_TOKENS
                    if 'fixed_teaching' in packet:
                        job=info['job']
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
                    packet=json.loads(row['messages'][1]['content'])
                    assert set(packet)=={'goal','actions','memory','experiences'}
                    assert len(compact(packet['memory']).encode())<=MEMORY_TOKENS
                    checks['bounded_consolidation_inputs']+=1
            except (ValueError,KeyError,TypeError,AssertionError) as error:
                errors.append({'episode':summary.parent.name,'event_type':row['type'],'error':type(error).__name__})
            last_type=row['type']
    result={'passed':not errors,'checks':dict(checks),'errors':errors,
        'scope':'Actual allowlisted packet shapes, byte limits, action/change derivation, fixed teaching schedule, source hashes and independent snapshot integrity. Semantic absence of arbitrary private information in model text is not proven by keyword scanning; pilot stores only game data.'}
    write_json(ROOT/'evidence/phase1/BOUNDARY_AUDIT.json',result);print(result)
    if errors:raise SystemExit(1)


if __name__=='__main__':main()
