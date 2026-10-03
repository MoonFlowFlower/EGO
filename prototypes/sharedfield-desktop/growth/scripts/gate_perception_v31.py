"""G0p2: one frozen Q&A comparison, then paired real decision loops. No retries for content."""
import argparse
import json
import random
import secrets
import time
from pathlib import Path
from gate_common_v3 import ROOT,read,hashes,check_hashes,Client,GateStop,initial_status,finish,resources
from gate_perception_v3 import SYSTEM as K0_SYSTEM,SCHEMA,answer,score
from growthlab.records import write_json
from growthlab.forks import file_hash
from growthlab.spatial import representation
from growthlab.decision import SYSTEM as DECISION_SYSTEM,VERSION,decision_format
from growthlab.models import MODEL,ROUTE
from growthlab.host import Host
from growthlab.state import Store
from growthlab.memory import Memory
from growthlab.agent import Episode

OUT=ROOT/'evidence/phase1/revision3_round2'
RUN=ROOT/'runs/phase1/revision3_round2/g0p2'
MODES={'K0':'map','K1':'v2_cells','K2':'v2_map'}
V2_SYSTEM=K0_SYSTEM.replace('all cells are relative to the CURRENT player at (0,0).\nFacing is a direction vector.',
    'all offsets are relative to you NOW at the origin (0,0).\nThe self entry describes your underfoot material and facing direction/vector; @ marks you.\nFront explicitly gives the facing cell direction/offset. Facing is a direction vector.')


def qa_messages(case,label):
    return [{'role':'system','content':K0_SYSTEM if label=='K0' else V2_SYSTEM},
            {'role':'user','content':json.dumps(representation(case['observation'],MODES[label]),ensure_ascii=False,separators=(',',':'))}]


def prepare():
    assert read(OUT/'engineering.json')['passed']
    RUN.mkdir(parents=True,exist_ok=False)
    old=read(ROOT/'runs/phase1/revision3/g0p/manifest.json')
    excluded={(c['source'],c['line']) for c in old['cases']}
    pilot=read(ROOT/'runs/phase1/pilot/manifest.json')
    completed=read(ROOT/'runs/phase1/pilot/status.json')['completed']
    sampling_seed=secrets.randbits(64);rng=random.Random(sampling_seed);cases=[]
    for summary in completed:
        path=Path(summary).parent/'trace.jsonl';source=str(path.relative_to(ROOT));entries=[]
        for line,raw in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
            row=json.loads(raw)
            if row['type']=='input' and (source,line) not in excluded:
                entries.append((line,json.loads(row['messages'][1]['content'])['observation']))
        for index in sorted(rng.sample(range(len(entries)),20)):
            line,obs=entries[index];truth=answer(obs);under=next(c for c in obs['cells'] if (c['dx'],c['dy'])==(0,0))
            cases.append({'id':f'p2_{len(cases):02}','source':source,'source_sha256':file_hash(path),'line':line,'tick':obs['tick'],
                          'observation':obs,'answer':truth,
                          'front_differs_from_underfoot':truth['front']['material']!=under['material'] or truth['front']['entity']!=(under['entity'] or 'none'),
                          'front_material_differs_from_underfoot':truth['front']['material']!=under['material']})
    assert len(cases)==60 and not any((c['source'],c['line']) in excluded for c in cases)
    jobs=[{'case':c['id'],'format':mode} for c in cases for mode in MODES];rng.shuffle(jobs)
    forbidden={s for field in ('practice_seeds','test_seeds') for seeds in pilot[field].values() for s in seeds}
    debug=[]
    while len(debug)<3:
        value=secrets.randbelow(2**31-1)+1
        if value not in forbidden and value not in debug:debug.append(value)
    manifest={'implementation_revision':'3 round 2','created_unix':time.time(),'sampling_seed':sampling_seed,
              'sampling':'Uniform 20 input observations per completed revision-2 practice, without replacement, excluding all 30 original G0p observations.',
              'cases':cases,'excluded_cases':[{'source':a,'line':b} for a,b in sorted(excluded)],'jobs':jobs,'formats':MODES,
              'qa_systems':{'K0':K0_SYSTEM,'K1':V2_SYSTEM,'K2':V2_SYSTEM},'qa_schema':SCHEMA,'qa_max_tokens':512,
              'debug_seeds':debug,'forbidden_pilot_seeds':sorted(forbidden),'decision_prompt':DECISION_SYSTEM,'prompt_version':VERSION,
              'model':MODEL,'route':ROUTE,'temperature':0,'concurrency':1,'budget_path':'runs/phase1/budget.sqlite','phase1_usd_limit':5,
              'machine_time_limit_s':7200,'max_decisions_per_episode':40,'world_step_limit':1280,'stop_on_goal':False,
              'live_order':['main_0','main_1','main_2','reasoning_0','reasoning_1','reasoning_2'],
              'arms':{'main':{'reasoning':False,'max_tokens':2048,'gate':True},'reasoning':{'reasoning':True,'max_tokens':8192,'gate':False}},
              'live_memory':'B; separate empty store per episode, no sleep call or cross-episode transfer. Real decision-time skill writes remain available.',
              'criteria':{'selection':'K1/K2 maximize front_exact + tree_exact; tie selects K2. K0 never selected.',
                          'qa_front_min':54,'qa_tree_direction_min':48,'qa_denominator':60,
                          'live_min_decisions':90,'live_front_min_fraction':.9,
                          'live_scoring':'Material+entity exact on every returned main-arm decision; strict full decision schema and first front_seen required. Invalid outputs count incorrect; no correction/re-ask.',
                          'invalid_policy':'Two consecutive invalid decisions/skills stop the episode and batch as in P2.',
                          'stop':'Incomplete gate is unverified. Failure/unverified prevents G0a/b/c and pilot; no third representation repair.',
                          'descriptive_arm':'Run paired reasoning episodes even if main score is below threshold, unless a transport/power/budget/protocol/time stop occurs. Reasoning never enters selection or criteria.'},
              'retry_policy':'Same transport: at most two requests, 30s wait for 429/502/503/504/timeout/URL error; unknown reservations retained; second error stops whole batch.',
              'descriptive_methods':{'tree_reason':'For do decisions, case-insensitive tree/trees/树 plus front/ahead/facing/前方/面前/正前 in the reason. Includes negation; keyword audit only.',
                                     'position':'Explicit I am/I am at/I\'m at/my position/当前位置/我在/我位于 followed within 30 characters by numeric (x,y); nonzero pair.',
                                     'similarity':'Adjacent accepted decisions within each episode, lowercase and collapse whitespace, difflib.SequenceMatcher ratio >=0.9.',
                                     'historical_comparison':'Apply these same frozen heuristics to old and new traces; Claude keyword script was not supplied, so exact reproduction of 85/87 etc is unverified.',
                                     'subsets':'Report both front material+entity differs from underfoot, and material alone differs; self entity makes the former less selective.'},
              'source_sha256':hashes([Path(__file__).resolve(),ROOT/'scripts/gate_perception_v3.py',ROOT/'scripts/report_g0p2.py']),
              'historical_sha256':{str(p.relative_to(ROOT)):file_hash(p) for folder in ('runs/phase1/pilot','runs/phase1/revision3/g0p') for p in (ROOT/folder).rglob('*') if p.is_file()}}
    write_json(RUN/'manifest.json',manifest);write_json(OUT/'G0p2_MANIFEST.json',manifest)
    print({'prepared':True,'qa':180,'live_max':240,'debug_seeds':debug,'selected_format':'not yet selected'})


class G0p2Client(Client):
    def sample(self):
        from growthlab.records import telemetry
        now=time.time()
        if now-self.status['started_unix']>=7200:raise GateStop('machine_time_limit')
        if now-self.last_sample>=30:
            value=telemetry();self.status['telemetry'].append(value);self.last_sample=now
            if value['ac_online'] is not True:raise GateStop('ac_required')


class LiveClient:
    def __init__(self,base,identity,settings):self.base,self.identity,self.settings,self.count=base,identity,settings,0
    def decide(self,prompt,**kwargs):
        self.base.context={'stage':'live','episode':self.identity,'decision':self.count}
        kwargs.update(max_tokens=self.settings['max_tokens'],reasoning=self.settings['reasoning'])
        result=self.base.decide(prompt,**kwargs);self.count+=1
        return result


def select(results):
    totals={mode:sum(r['score']['front_exact']+r['score']['tree_exact'] for r in results if r['job']['format']==mode) for mode in ('K1','K2')}
    return 'K1' if totals['K1']>totals['K2'] else 'K2'


def run_gate():
    manifest=read(RUN/'manifest.json');check_hashes(manifest['source_sha256'])
    if (RUN/'status.json').exists():raise ValueError('g0p2_already_started')
    status=initial_status();status.update(qa_completed=0,live_completed=[],selected=None);write_json(RUN/'status.json',status)
    client=None
    try:
        client=G0p2Client(RUN,status);cases={c['id']:c for c in manifest['cases']};results=[]
        for job in manifest['jobs']:
            case=cases[job['case']];identity=job['case']+'_'+job['format'];client.context={'stage':'qa','id':identity}
            output,meta=client.decide(qa_messages(case,job['format']),response_format=SCHEMA,max_tokens=512)
            result={'job':job,'output':output,'score':score(output,case['answer']),'meta':meta};results.append(result)
            write_json(RUN/'qa'/(identity+'.json'),result);status['completed'].append(identity);status['qa_completed']+=1
            write_json(RUN/'status.json',status)
        status['selected']=select(results);status['qa_finished_unix']=time.time();write_json(RUN/'status.json',status)
        for identity in manifest['live_order']:
            arm,index=identity.split('_');settings=manifest['arms'][arm];folder=RUN/'episodes'/identity
            folder.mkdir(parents=True,exist_ok=False);store=Store(folder/'state.sqlite');episode=None
            try:
                host=Host(seed=manifest['debug_seeds'][int(index)],length=manifest['world_step_limit'])
                memory=Memory(store,host.world,host.actions,'B')
                write_json(folder/'start.json',{'seed':manifest['debug_seeds'][int(index)],'world':host.world,'arm':arm,'settings':settings,
                                               'records':memory.export()['records'],'observation_format':MODES[status['selected']]})
                episode=Episode(host,store,folder,LiveClient(client,identity,settings),memory=memory,
                                observation_format=MODES[status['selected']],stop_on_success=False)
                summary=episode.play(max_decisions=40,deadline=status['started_unix']+7200)
                summary.update(episode=identity,arm=arm,seed=manifest['debug_seeds'][int(index)])
                write_json(folder/'summary.json',summary);write_json(folder/'memory_full.json',memory.export())
                status['live_completed'].append(identity);write_json(RUN/'status.json',status)
                if summary['stop'] not in (None,'decision_limit'):raise GateStop(summary['stop'])
            finally:
                if episode:episode.close()
                store.close()
    except Exception as error:
        status['stop']=str(error) if isinstance(error,(GateStop,ValueError)) else type(error).__name__
    finally:
        finish(RUN,status,client,manifest['source_sha256'])
    from report_g0p2 import report
    report()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','run','report']);args=p.parse_args()
    if args.mode=='prepare':prepare()
    elif args.mode=='run':run_gate()
    else:
        from report_g0p2 import report
        report()
