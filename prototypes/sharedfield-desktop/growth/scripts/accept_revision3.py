"""Focused engineering acceptance for representation, navigation and memory writes."""
import copy
import json
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.host import Host
from growthlab.contract import validate
from growthlab.spatial import aids,nearest_cells,representation
from growthlab.navigation import goto,plan
from growthlab.changes import changes
from growthlab.state import Store
from growthlab.rules import Rules
from growthlab.skills import SkillLibrary
from growthlab.sandbox import run
from growthlab.memory import Memory
from growthlab.agent import Episode
from growthlab.consolidation import consolidate,packet,successful_sequences,sleep_format
from growthlab.decision import decode,messages
from growthlab.records import ROOT,write_json,telemetry


def fixture(tree=(2,1)):
    h=Host(seed=9300303,length=300);p=h.env._player;w=h.env._world
    for obj in w.objects:
        if obj is not p:w.remove(obj)
    for x in range(-7,8):
        for y in range(-7,8):w[p.pos+(x,y)]='grass'
    p.facing=(1,0);p.inventory['wood']=0;h.env._balance_chunk=lambda *args:None
    if tree:w[p.pos+tree]='tree'
    return h


def raw_step(h,action):
    before=h.observe();after=h.act(action)
    return {'type':'transition','before':before,'after':after,'action':action,'change':changes(before,after,action)}


def save_exp(store,row):return store.put('experience',row,'engineering_fixture',world=row['before']['world'])


def candidate(identity,amount=1):
    return {'action':'do','preconditions':{'inventory_min':{},'nearby':[],'front_materials':['tree'],'front_entity':'none'},
            'expected':{'inventory':{'wood':amount},'needs':{},'front':{}},'experiences':[identity]}


def rejected(fn,code):
    try:fn()
    except ValueError as error:
        assert str(error)==code,(str(error),code)
        return code
    raise AssertionError('accepted_invalid_write')


def main():
    started=time.perf_counter();result={'implementation_revision':3,'passed':False,'telemetry':[telemetry()]}
    try:
        obs=fixture().observe();copy_before=copy.deepcopy(obs)
        info=aids(obs,with_map=True)
        assert info['front']=={'material':'grass','entity':None,'visible_state':None}
        tree=next(r for r in info['nearest'] if r['name']=='tree')
        assert tree['direction']=='下 1 步、右 2 步' and tree['offset_steps']==3 and not tree['adjacent']
        assert obs==copy_before and len(info['map']['rows'])==7 and all(len(line)==9 for line in info['map']['rows'])
        night=copy.deepcopy(obs);night.update(radius=1,light=.1)
        night['cells']=[c for c in night['cells'] if abs(c['dx'])<=1 and abs(c['dy'])<=1]
        validate(night);dark=aids(night,with_map=True)
        assert not nearest_cells(night,'tree') and all(r['name']!='tree' for r in dark['nearest'])
        assert sum(line.count('?') for line in dark['map']['rows'])==54
        assert plan(night,'tree')['status']=='target_not_visible'
        assert set(representation(obs,'cells'))=={'observation'}
        result['observation']={'front':info['front'],'nearest_tree':tree,'night_unknown_cells':54,'pure_json_and_input_unchanged':True}
        h=fixture((2,2));diagonal=goto('tree',h.observe,h.act)
        assert diagonal['status']=='arrived' and diagonal['steps']==3
        h=fixture((2,0));p=h.env._player
        for y in range(-2,3):h.env._world[p.pos+(1,y)]='stone'
        obstacle=goto('tree',h.observe,h.act)
        assert obstacle['status']=='arrived' and obstacle['steps']>1
        for r in diagonal['plans']+obstacle['plans']:
            assert all(abs(x)<=4 and abs(y)<=3 for x,y in r['searched_cells'])
        h=fixture(None);unseen=goto('tree',h.observe,h.act)
        assert unseen['status']=='target_not_visible' and unseen['steps']==0
        h=fixture((2,2));p=h.env._player
        for delta in ((1,0),(-1,0),(0,1),(0,-1)):h.env._world[p.pos+delta]='stone'
        no_path=goto('tree',h.observe,h.act);assert no_path['status']=='no_path' and no_path['steps']==0
        h=fixture((3,0));blocked_once=False
        def obstruct(action):
            nonlocal blocked_once
            if not blocked_once:
                h.env._world[h.env._player.pos+(1,0)]='stone';blocked_once=True
            return h.act(action)
        blocked=goto('tree',h.observe,obstruct);assert blocked['status']=='blocked' and blocked['steps']==1
        from crafter.objects import Arrow
        h=fixture((3,0));h.env._world.add(Arrow(h.env._world,h.env._player.pos+(1,1),(0,-1)))
        hurt=goto('tree',h.observe,h.act);assert hurt['status']=='injured' and hurt['steps']==1
        h=fixture();cancel=threading.Event();cancel.set()
        assert goto('tree',h.observe,h.act,cancel=cancel)['status']=='cancelled'
        timeout=goto('tree',h.observe,h.act,deadline=time.perf_counter()-1);assert timeout['steps']==0 and timeout['status']=='timeout'
        h.done=True;assert goto('tree',h.observe,h.act)['status']=='episode_finished'
        result['navigation']={'diagonal':diagonal,'obstacle':obstacle,'unseen':unseen,'no_path':no_path,'blocked':blocked,'hurt':hurt,
                              'timeout_and_cancellation':True,'visible_bounds_only':True}
        with tempfile.TemporaryDirectory() as temporary:
            store=Store(Path(temporary)/'state.sqlite');h=fixture((3,0));library=SkillLibrary(store,h.world,h.actions)
            library.register('reach','reach tree',"goto('tree')","False")
            library.register('parent','nested',"run('reach')","False")
            limited=run('',h.observe,h.act,library=library,name='parent',max_steps=1,timeout_s=5)
            assert limited['steps']==1 and limited['status']=='step_limit' and all(c['steps']==1 for c in limited['calls'])
            h=fixture((3,0));h.env._world.add(Arrow(h.env._world,h.env._player.pos+(1,1),(0,-1)))
            hurt_skill=run('',h.observe,h.act,library=library,name='parent',timeout_s=5)
            assert hurt_skill['steps']==1 and hurt_skill['status']=='injured'
            h=fixture((3,0));cancel=threading.Event()
            def takeover(action):
                after=h.act(action);cancel.set();return after
            cancelled=run('',h.observe,takeover,library=library,name='parent',timeout_s=5,cancel=cancel)
            assert cancelled['status']=='cancelled' and cancelled['steps']==1
            decoded=decode(json.dumps({'kind':'goto','name':'tree','repeat':1,'action':'','source':'','completion':'','description':'','reason':'observed tree'}),h.actions)
            result['skill_goto']={'shared_budget':limited,'nested_hurt':hurt_skill,'nested_takeover':cancelled,'decision_kind':decoded['kind']}
            store.close()
        with tempfile.TemporaryDirectory() as temporary:
            store=Store(Path(temporary)/'state.sqlite');h=fixture((1,0));one=raw_step(h,'do');eid=save_exp(store,one)
            rules=Rules(store,h.world,h.actions);identity=rules.register(candidate(eid));first=rules.cards()[0]
            assert first['support']==1 and first['world_counts'][h.world]['support']==1 and first['evidence_worlds']==[h.world]
            assert rules.score(one['before'],one['after'],'do',eid)==[]
            second=copy.deepcopy(one);world2=uuid.uuid4().hex
            second['before']['world']=second['after']['world']=world2
            second['after']['inventory']['wood']+=1;second['change']=changes(second['before'],second['after'],'do')
            eid2=save_exp(store,second);other=Rules(store,world2,h.actions)
            assert other.cards()[0]['id']==identity
            other.score(second['before'],second['after'],'do',eid2)
            counts=other.cards()[0]['world_counts'];assert counts[world2]['counterexamples']==1 and counts[h.world]['support']==1
            store.put('map',{'note':'world-bound'},'fixture',world=h.world)
            store.put('project',{'type':'world'},'fixture',world=h.world)
            assert not any(r['kind'] in ('map','project') for r in store.load(world2))
            reasons=[rejected(lambda:other.register(candidate('f'*32)),'unknown_experience'),
                     rejected(lambda:other.register(candidate(eid,2)),'prediction_mismatch'),
                     rejected(lambda:other.register(candidate(eid),replaces=identity),'replacement_requires_counterexample')]
            empty=candidate(eid);empty['preconditions']['front_materials']=['stone']
            reasons.append(rejected(lambda:other.register(empty),'no_applicable_supporting_evidence'))
            new=other.register(candidate(eid2,2),replaces=identity)
            assert [r['id'] for r in other.cards()]==[new]
            assert store.db.execute('SELECT status FROM records WHERE id=?',(identity,)).fetchone()[0]=='superseded'
            memory=Memory(store,uuid.uuid4().hex,h.actions,'B')
            assert any(x.get('type')=='rule_card' and x['id']==new for x in memory.retrieve(second['before'],'wood'))
            result['rules']={'world_counts_before_correction':counts,'rejection_reasons':reasons,'old':identity,'new':new,
                             'new_world_prompt_contains_rule':True,'world_map_project_remain_scoped':True,'registered':other.cards()}
            store.close()
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);h=fixture();store=Store(folder/'state.sqlite');memory=Memory(store,h.world,h.actions,'B')
            class Stub:
                def decide(self,prompt,**kwargs):
                    packet=json.loads(prompt[1]['content']);sequences=packet['successful_sequences']
                    assert sequences and sequences[-1]['observed_increase']['name']=='wood'
                    assert 'scope' not in kwargs['response_format']['json_schema']['schema']['properties']['rules']['items']['properties']
                    value={'rules':[],'skills':[{'name':'collect_visible_tree','description':'Observed movement and collection sequence',
                        'source':"goto('tree')\nact('do')",'completion':"count('wood') >= 1",'experiences':sequences[-1]['experiences']}]}
                    return json.dumps(value),{'cost_usd':0,'purpose':'engineering_stub'}
            episode=Episode(h,store,folder/'episode',Stub(),memory=memory)
            goto('tree',h.observe,episode.step);episode.step('do')
            sleep=consolidate(episode);assert sleep['results'][0]['accepted']
            assert memory.library.current()['collect_visible_tree']['completion']=="count('wood') >= 1"
            fresh=fixture();executed=run('',fresh.observe,fresh.act,library=memory.library,name='collect_visible_tree',timeout_s=5)
            assert executed['calls'][0]['outcome']=='success' and fresh.observe()['inventory']['wood']==1
            result['sleep_skills']={'sleep':sleep,'executed':executed,'real_model_extraction':'unverified; engineering transport stub'}
            episode.close();store.close()
        result['passed']=True
    except Exception:
        import traceback
        result['error']=traceback.format_exc()
    result.update(seconds=time.perf_counter()-started);result['telemetry'].append(telemetry())
    write_json(ROOT/'evidence/phase1/revision3/engineering.json',result)
    print({k:v for k,v in result.items() if k in ('passed','seconds','error')})
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
