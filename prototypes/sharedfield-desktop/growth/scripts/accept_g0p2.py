"""Offline acceptance of revision 3 round 2. No cloud calls or old evidence writes."""
import copy
import json
import sqlite3
import tempfile
import time
from pathlib import Path
from accept_revision3 import fixture,raw_step,save_exp
from growthlab.records import ROOT,write_json,telemetry
from growthlab.contract import validate
from growthlab.spatial import representation
from growthlab.navigation import plan,goto
from growthlab.decision import messages,decision_format,decode,assess_front,VERSION
from growthlab.state import Store
from growthlab.memory import Memory
from growthlab.rules import application
from growthlab.agent import Episode
from growthlab.skills import SkillLibrary
from growthlab.sandbox import run

OUT=ROOT/'evidence/phase1/revision3_round2'


def choice(front=None,**kwargs):
    return dict(front_seen=front or {'material':'grass','entity':'none'},kind='action',action='do',repeat=1,
                name='',description='',source='',completion='',reason='old private rationale marker',**kwargs)


def main():
    started=time.perf_counter();result={'passed':False,'prompt_version':VERSION,'telemetry':[telemetry()]}
    try:
        original=fixture((2,1)).observe();original_copy=copy.deepcopy(original)
        # Exercise every texture-equivalent state, not just nearest instances.
        for xy,entity,state in [((1,1),'plant',{'plant_ripe':True}),((-1,1),'plant',{'plant_ripe':False}),
                                ((1,-1),'arrow',{'arrow_direction':'left'})]:
            c=next(c for c in original['cells'] if (c['dx'],c['dy'])==xy);c.update(entity=entity,visible_state=state)
        expected_original=copy.deepcopy(original)
        checks=[]
        for facing in ([1,0],[-1,0],[0,1],[0,-1]):
            obs=copy.deepcopy(original);obs['facing']=facing
            for mode in ('v2_cells','v2_map'):
                packet=representation(obs,mode);info=packet['observation_aids']
                assert 'player' not in json.dumps(packet) and info['front']['entity']=='none'
                assert [info['front']['dx'],info['front']['dy']]==facing
                assert all(n['offset_steps']>=1 and n['name']!='player' for n in info['nearest'])
                assert len(info['visible_states'])==3 and info['map']['rows'][3][4]=='@'
                if mode=='v2_cells':assert len(packet['observation']['cells'])==62 and all((c['dx'],c['dy'])!=(0,0) for c in packet['observation']['cells'])
                else:assert 'cells' not in packet['observation']
                checks.append({'facing':facing,'mode':mode,'states':info['visible_states']})
        assert original==expected_original
        night=copy.deepcopy(original);night.update(radius=1,light=.1)
        night['cells']=[c for c in night['cells'] if abs(c['dx'])<=1 and abs(c['dy'])<=1]
        for mode in ('v2_cells','v2_map'):
            packet=representation(night,mode)
            assert sum(r.count('?') for r in packet['observation_aids']['map']['rows'])==54
            assert all(abs(n['dx'])<=1 and abs(n['dy'])<=1 for n in packet['observation_aids']['nearest'])
        old_calls=ROOT/'runs/phase1/revision3/g0p/calls.jsonl'
        legacy_checked=0
        for line in old_calls.read_text(encoding='utf-8').splitlines():
            row=json.loads(line)
            if row['type']=='request' and row['context']['id'].endswith('_map'):
                packet=json.loads(row['messages'][1]['content'])
                assert packet==representation(packet['observation'],'map');legacy_checked+=1
        assert legacy_checked>=30
        result['representation']={'checks':checks,'night_supplied':9,'night_unknown':54,'legacy_K0_packets_equal':legacy_checked,
                                  'internal_observation_unchanged':True}
        front={'material':'grass','entity':'none'};valid=choice(front)
        assert next(iter(decision_format(original['actions'])['json_schema']['schema']['properties']))=='front_seen'
        assert decode(json.dumps(valid),original['actions'])['front_seen']==front
        wrong=copy.deepcopy(valid);wrong['front_seen']['entity']='cow'
        assert not assess_front(json.dumps(wrong),original)['correct']
        late={k:v for k,v in valid.items() if k!='front_seen'};late['front_seen']=valid['front_seen']
        assert not assess_front(json.dumps(late),original)['protocol_valid']
        recent=[{'decision':valid,'execution_status':'completed','steps':1}]
        events=[{'effects':{'front':{'after':{'material':'grass','entity':'player'}}}}]
        packet=json.loads(messages(original,'wood',[],recent,events)[1]['content'])
        assert packet['recent']==[{'kind':'action','action':'do','execution_status':'completed','steps':1}]
        assert 'old private rationale marker' not in json.dumps(packet) and '"entity": "player"' not in json.dumps(packet)
        assert events[0]['effects']['front']['after']['entity']=='player'
        result['decision']={'first_property':True,'actual_order_enforced':True,'wrong_front_scored_not_corrected':True,
                            'recent':packet['recent'],'historical_entity_view_only':True}
        nav={}
        h=fixture((3,0));h.env._world[h.env._player.pos+(1,0)]='lava'
        nav['lava_detour']=goto('tree',h.observe,h.act)
        assert nav['lava_detour']['status']=='arrived' and h.observe()['needs']['health']>0
        h=fixture((3,0));p=h.env._player
        for x in range(-4,5):
            for y in range(-3,4):h.env._world[p.pos+(x,y)]='stone'
        for x,m in [(0,'grass'),(1,'lava'),(2,'grass'),(3,'tree')]:h.env._world[p.pos+(x,0)]=m
        nav['lava_only']=goto('tree',h.observe,h.act)
        assert nav['lava_only']['status']=='no_path' and nav['lava_only']['steps']==0
        assert plan(h.observe(),'lava')['status']=='arrived'
        h=fixture((-1,0));nav['behind']=goto('tree',h.observe,h.act)
        assert nav['behind']['status']=='arrived' and nav['behind']['steps']==1 and h.delta==[0,0]
        h=fixture((-1,0));p=h.env._player;h.env._world[p.pos+(1,0)]='tree';p.facing=(0,-1)
        nav['corridor']=goto('tree',h.observe,h.act)
        assert nav['corridor']['status']=='arrived' and nav['corridor']['steps']==1
        h=fixture((3,0))
        def block(action):h.env._world[h.env._player.pos+(1,0)]='stone';return h.act(action)
        nav['unexpected_block']=goto('tree',h.observe,block)
        assert nav['unexpected_block']['status']=='blocked' and nav['unexpected_block']['steps']==1
        h=fixture(None);assert goto('tree',h.observe,h.act)['status']=='target_not_visible'
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'state.sqlite');h=fixture((-1,0));lib=SkillLibrary(s,h.world,h.actions)
            lib.register('turn','turn to tree',"goto('tree')",'False')
            nav['skill_turn']=run('',h.observe,h.act,library=lib,name='turn',max_steps=1,timeout_s=5)
            assert nav['skill_turn']['steps']==1 and nav['skill_turn']['status']=='completed';s.close()
        result['navigation']=nav
        with tempfile.TemporaryDirectory() as tmp:
            s=Store(Path(tmp)/'state.sqlite');h=fixture(None);p=h.env._player
            p.inventory['wood']=2;h.env._world[p.pos+(0,1)]='table'
            row=raw_step(h,'make_wood_pickaxe');eid=save_exp(s,row);b=Memory(s,h.world,h.actions,'B')
            card={'action':'make_wood_pickaxe','preconditions':{'inventory_min':{'wood':2},'nearby':['table'],'front_materials':[],'front_entity':None},
                  'expected':{'inventory':{'wood_pickaxe':1},'needs':{},'front':{}},'experiences':[eid]}
            identity=b.rules.register(card);card=b.rules.cards()[0]
            obs=row['before'];true=application(card,obs);assert true['applicable'] and '+1' in true['text']
            partial=copy.deepcopy(obs)
            for c in partial['cells']:
                if c['material']=='table':c['material']='grass'
            middle=application(card,partial);assert not middle['applicable'] and [c['met'] for c in middle['checks']]==[True,False]
            false=copy.deepcopy(partial);false['inventory']['wood']=0
            negative=application(card,false);assert not negative['applicable'] and not any(c['met'] for c in negative['checks'])
            cowcard={**card,'action':'do','preconditions':{'inventory_min':{},'nearby':[],'front_materials':[],'front_entity':'cow'},
                     'expected':{'inventory':{},'needs':{'health':-2,'food':0},'front':{}}}
            cow=copy.deepcopy(obs);next(c for c in cow['cells'] if [c['dx'],c['dy']]==cow['facing'])['entity']='cow'
            cowprediction=application(cowcard,cow);assert '血量 -2、食物不变' in cowprediction['text']
            assert any(r['type']=='action_rule_prediction' for r in b.retrieve(obs,'wood_pickaxe'))
            a=Memory(s,h.world,h.actions,'A');assert all(r['type'] not in ('action_rule_prediction','rule_card') for r in a.retrieve(obs,'wood_pickaxe'))
            result['rule_applications']={'true':true,'partial':middle,'false':negative,'negative_and_zero':cowprediction,'A_excluded':True}
            s.close()
        with tempfile.TemporaryDirectory() as tmp:
            h=fixture(None);s=Store(Path(tmp)/'state.sqlite');m=Memory(s,h.world,h.actions,'B')
            class Stub:
                def decide(self,prompt,**kwargs):
                    packet=json.loads(prompt[1]['content'])
                    assert 'old private rationale marker' not in prompt[1]['content']
                    assert not packet['memory'] or all(p['type']!='rule_card' for p in packet['memory'])
                    return json.dumps(choice({'material':'stone','entity':'cow'})),{'latency_s':0,'cost_usd':0}
            e=Episode(h,s,Path(tmp)/'episode',Stub(),memory=m,stop_on_success=False)
            summary=e.play(max_decisions=2);e.close()
            trace=[json.loads(x) for x in (Path(tmp)/'episode/trace.jsonl').read_text(encoding='utf-8').splitlines()]
            assessments=[r for r in trace if r['type']=='front_assessment']
            assert len(assessments)==2 and all(not x['correct'] for x in assessments) and summary['steps']==2
            assert sum(r['type']=='decision' for r in trace)==2  # wrong answers still execute, no re-ask
            result['integration']={'decisions':2,'incorrect_front':2,'executed_steps':2,'no_correction_or_retry':True};s.close()
        # Capture actual Cloud payload without a credential/network operation.
        import growthlab.models as models
        cloud=models.Cloud.__new__(models.Cloud);cloud.model=models.MODEL;cloud.route=models.ROUTE;cloud.limit=5;cloud.key='stub'
        cloud.db=sqlite3.connect(':memory:');cloud.db.execute('CREATE TABLE charges (id TEXT PRIMARY KEY, usd REAL, status TEXT)')
        payloads=[];original_request=models.request_json
        def request(url,payload,headers=None,timeout=60):
            payloads.append(payload);return {'usage':{'cost':.001},'choices':[{'message':{'content':'{}'},'finish_reason':'stop'}],'provider':'stub'}
        try:
            models.request_json=request
            cloud.decide([{'role':'user','content':'fixture'}],response_format={'test':True},max_tokens=2048)
            cloud.decide([{'role':'user','content':'fixture'}],response_format={'test':True},max_tokens=8192,reasoning=True)
        finally:models.request_json=original_request;cloud.db.close()
        assert payloads[0]['reasoning']=={'enabled':False} and payloads[1]['reasoning']=={'enabled':True}
        assert {k:v for k,v in payloads[0].items() if k not in ('reasoning','max_tokens')}=={k:v for k,v in payloads[1].items() if k not in ('reasoning','max_tokens')}
        result['reasoning_transport']={'only_reasoning_and_output_limit_differ':True,'max_tokens':[2048,8192]}
        result['passed']=True
    except Exception:
        import traceback
        result['error']=traceback.format_exc()
    result.update(seconds=time.perf_counter()-started,cloud_cost_usd=0);result['telemetry'].append(telemetry())
    OUT.mkdir(parents=True,exist_ok=True)
    attempt=len(list(OUT.glob('engineering_attempt_*.json')))+1
    write_json(OUT/f'engineering_attempt_{attempt}.json',result)
    if result['passed']:write_json(OUT/'engineering.json',result)
    print({k:v for k,v in result.items() if k in ('passed','seconds','error')})
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
