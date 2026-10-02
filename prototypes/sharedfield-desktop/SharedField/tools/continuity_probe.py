"""Run bounded continuity interventions. No model API, no user's private data.

Constructed partner-choice histories are synthetic, not samples of emotions.
A frequency counter is included as a stronger simple explanation of this toy.
"""
from pathlib import Path
import json,sys,tempfile,math
from copy import deepcopy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from switchlab.shared.core import SharedCore
from switchlab.shared.service import SharedService
from tests.test_shared_partner_learning import trained_mind
from switchlab.shared.grounding import contract,guard_speech


def run(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    arms={}
    for target in (1,4):
        m=trained_mind(target);f=trained_mind(target,True)
        arms[str(target)]={'trained_updates':m.partner_model['updates'],
             'category_tendencies':m.report()['partner_choice_model']['category_tendencies'],
             'chosen':m.candidates()[0]['action'],'frozen_chosen':f.candidates()[0]['action'],
             'simple_frequency_baseline_chosen':{'kind':'move','target':target},
             'self_value_estimates':deepcopy(m.interests)}
    assert arms['1']['chosen']!=arms['4']['chosen']
    assert arms['1']['frozen_chosen']==arms['4']['frozen_chosen']
    waiting={}
    with tempfile.TemporaryDirectory() as d:
        s=SharedService(d)
        try:
            s.command('activity',{'mode':'wait'});s.start_auto(8);s.run_once(force=True)
            n=len(s.core.events)
            for _ in range(100):s.run_once()
            waiting={'extra_events_over_100_polls':len(s.core.events)-n,'physical_tick':s.core.world.tick,
                     'language_calls':s.core.state['calls'],'remaining_authority':s.auto_remaining}
        finally:s.close()
    result={'scope':'constructed histories and real local service; no semantic/subjectivity test',
       'partner_model':arms,'same_public_evaluation_state':True,
       'frequency_baseline_matches_both_arms':True,
       'waiting':waiting,
       'interpretation':'online adaptation affects collaboration; simple frequency memory explains this toy equally well',
       'claims_not_established':['general social inference','learned value origin','consciousness','overall architecture advantage']}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result
if __name__=='__main__':
    r=run(sys.argv[1] if len(sys.argv)>1 else 'evidence_v05/continuity_probe')
    print(json.dumps(r,ensure_ascii=False,indent=2))
