"""Independently reconcile G0p scores/requests with the actual source observations."""
import json
from collections import Counter
from gate_common_v3 import ROOT,BASE,OUT,read,check_hashes
from growthlab.forks import file_hash
from growthlab.records import write_json
from growthlab.spatial import representation
from growthlab.contract import validate


def main():
    folder=BASE/'g0p';manifest=read(folder/'manifest.json');report=read(OUT/'G0p.json')
    check_hashes(manifest['source_sha256'])
    cases={c['id']:c for c in manifest['cases']};truth={};checks=Counter();checks['frozen_hashes']=len(manifest['source_sha256'])
    for identity,c in cases.items():
        path=ROOT/c['source'];assert file_hash(path)==c['source_sha256']
        source=json.loads(path.read_text(encoding='utf8').splitlines()[c['line']-1])
        assert source['type']=='input'
        obs=validate(json.loads(source['messages'][1]['content'])['observation']);assert obs==c['observation']
        facing=next(cell for cell in obs['cells'] if [cell['dx'],cell['dy']]==obs['facing'])
        state=facing.get('visible_state') or {}
        front={'material':facing['material'],'entity':facing['entity'] or 'none','plant_ripe':state.get('plant_ripe'),
               'arrow_direction':state.get('arrow_direction','')}
        trees=[cell for cell in obs['cells'] if cell['material']=='tree']
        if trees:
            minimum=min(abs(cell['dx'])+abs(cell['dy']) for cell in trees)
            nearest=[{'visible':True,'dx':cell['dx'],'dy':cell['dy'],'steps':minimum} for cell in trees if abs(cell['dx'])+abs(cell['dy'])==minimum]
        else:nearest=[{'visible':False,'dx':0,'dy':0,'steps':0}]
        assert front==c['answer']['front'] and {tuple(x.values()) for x in nearest}=={tuple(x.values()) for x in c['answer']['nearest_trees']}
        truth[identity]={'front':front,'nearest':nearest};checks['raw_observations_and_oracles']+=1
    lines=[json.loads(line) for line in (folder/'calls.jsonl').read_text(encoding='utf8').splitlines()]
    rows={r['job']['case']+'_'+r['job']['format']:r for r in report['results']}
    for line in lines:
        if line['type']=='request':
            r=rows[line['context']['id']];j=r['job']
            assert line['messages'][0]=={'role':'system','content':manifest['system']}
            assert json.loads(line['messages'][1]['content'])==representation(cases[j['case']]['observation'],j['format'])
            assert line['response_format']==manifest['response_format']
            checks['outbound_packets_exact']+=1
        elif line['type']=='response':
            r=rows[line['context']['id']]
            assert line['output']==r['output'] and line['meta']==r['meta'];checks['responses_match_report']+=1
            assert line['meta']['provider']=='OpenInference';checks['response_provider']=checks.get('response_provider',0)+1
    fields={};mistakes=[];visible_counts={}
    sign=lambda v:(v>0)-(v<0)
    for mode in manifest['formats']:
        group=[r for r in report['results'] if r['job']['format']==mode];front_count=0;direction_count=0;exact_count=0
        fields[mode]={key:0 for key in ('material','entity','plant_ripe','arrow_direction')}
        visible_counts[mode]={'n':0,'direction_correct':0,'exact_correct':0}
        for row in group:
            t=truth[row['job']['case']];output=json.loads(row['output']);tree=output['nearest_tree']
            assert set(output['front'])==set(t['front'])
            for k in fields[mode]:fields[mode][k]+=output['front'][k]==t['front'][k]
            correct_front=output['front']==t['front']
            correct_direction=any(tree['visible']==e['visible'] and (sign(tree['dx']),sign(tree['dy']))==(sign(e['dx']),sign(e['dy'])) for e in t['nearest'])
            correct_exact=tree in t['nearest']
            assert row['score']['front_exact']==correct_front and row['score']['tree_direction']==correct_direction and row['score']['tree_exact']==correct_exact
            front_count+=correct_front;direction_count+=correct_direction;exact_count+=correct_exact
            if t['nearest'][0]['visible']:
                visible_counts[mode]['n']+=1;visible_counts[mode]['direction_correct']+=correct_direction;visible_counts[mode]['exact_correct']+=correct_exact
            if not correct_front:
                case=cases[row['job']['case']]
                mistakes.append({'case':case['id'],'format':mode,'source':case['source'],'line':case['line'],'tick':case['tick'],
                                 'facing':case['observation']['facing'],'expected':t['front'],'returned':output['front']})
        scored=next(g for g in report['formats'] if g['format']==mode)
        assert (scored['front_exact'],scored['tree_direction'],scored['tree_exact'])==(front_count,direction_count,exact_count)
        checks['aggregate_formats']=checks.get('aggregate_formats',0)+1
    assert report['selected']=='map' and report['passed'] is False
    # Historical raw pilot files remain untouched after all revision-3 activity.
    history=read(ROOT/'evidence/phase1/BOUNDARY_AUDIT.json')
    for path,expected in history['raw_evidence_sha256'].items():
        assert file_hash(ROOT/path)==expected;checks['revision2_raw_files_unchanged']+=1
    result={'passed':True,'checks':dict(checks),'front_fields_correct':fields,'visible_tree_only':visible_counts,
            'front_mistakes':mistakes,'gate_passed':False,'missing_downstream':'Revision-3 G0a/G0b/G0c and pilot not started after G0p stop.'}
    write_json(OUT/'BOUNDARY_AUDIT.json',result)
    print({k:result[k] for k in ('passed','checks','front_fields_correct','visible_tree_only','gate_passed')})


if __name__=='__main__':main()
