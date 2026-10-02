"""Engineering fixtures; their privileged setup never enters agent input."""
import argparse
import json
import sys
import time
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from growthlab.host import Host
from growthlab.changes import changes, repeat_action
from growthlab.sandbox import run
from growthlab.records import ROOT, write_json, telemetry


def fixture():
    h = Host(length=500); p = h.env._player; w = h.env._world
    for obj in w.objects:
        if obj is not p: w.remove(obj)
    for dx in range(-6, 7):
        for dy in range(-6, 7): w[p.pos + (dx, dy)] = 'grass'
    p.facing = (1, 0)
    h.env._balance_chunk = lambda *args: None
    return h


def c1():
    from crafter.objects import Cow, Arrow
    import copy
    import threading
    rows = {}
    h = fixture(); p = h.env._player; w = h.env._world
    w[p.pos + (-1, 0)] = 'stone'
    h.act('move_left'); rows['stone'] = h.last_event
    assert h.last_event['events'] == ['no_visible_effect', 'blocked']
    p.inventory['wood'] = 2
    h.act('make_wood_pickaxe'); rows['no_table'] = h.last_event
    assert h.last_event['events'] == ['no_visible_effect']
    h = fixture(); p = h.env._player; w = h.env._world
    p.inventory['food'] = 1
    cow = Cow(w, p.pos + (1, 0)); w.add(cow)
    cow.update = lambda: w.remove(cow) if cow.health <= 0 else None
    cow_events = []
    for _ in range(3): h.act('do'); cow_events.append(h.last_event)
    assert all(e['events'] == ['no_visible_effect'] for e in cow_events[:2])
    assert cow_events[2]['effects']['consumption'] == {'food': 6}
    rows['cow'] = cow_events
    def attack_host():
        host = fixture(); player = host.env._player
        host.env._world.add(Arrow(host.env._world, player.pos + (0, 1), (0, -1)))
        return host
    h = attack_host()
    repeated = repeat_action('do', 8, h.observe, h.act)
    assert repeated['status'] == 'injured' and repeated['steps'] == 1
    rows['repeat_hurt'] = repeated
    h = attack_host()
    result = run("for _ in range(8):\n act('do')", h.observe, h.act, timeout_s=5)
    assert result['status'] == 'injured' and result['steps'] == 1
    rows['skill_hurt'] = result
    h = fixture(); before = h.observe(); after = copy.deepcopy(before)
    after['needs'].update(health=8, energy=8, food=8, drink=8)
    event = changes(before, after, 'do')
    assert event['events'] == ['no_visible_effect', 'health_lost'] and not event['effects']['consumption']
    rows['need_drift'] = event
    after = copy.deepcopy(before); after['facing'] = [-1, 0]
    after['cells'][0]['material'] = 'stone'
    assert changes(before, after, 'do')['effects']['front'] is None
    cancel = threading.Event(); cancel.set()
    assert repeat_action('do', 8, h.observe, h.act, cancel=cancel)['steps'] == 0
    assert 'reason' not in json.dumps(rows) or 'health_lost' in json.dumps(rows)
    return rows


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('component', choices=['c1','c2','c3']); args = parser.parse_args()
    started = time.perf_counter(); samples = [telemetry()]
    result = {'component': args.component, 'passed': False}
    try:
        result['checks'] = globals()[args.component](); result['passed'] = True
    except Exception:
        result['error'] = traceback.format_exc()
    result.update(seconds=time.perf_counter()-started, telemetry=samples+[telemetry()])
    path = ROOT/'evidence/phase1'/f'{args.component}.json'; write_json(path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result['passed']: raise SystemExit(1)


def c2():
    import tempfile
    import threading
    from crafter.objects import Arrow
    from growthlab.state import Store
    from growthlab.skills import SkillLibrary
    from growthlab.sandbox import Denied, parse, completed
    rows = {}
    with tempfile.TemporaryDirectory() as folder:
        h = fixture(); store = Store(Path(folder)/'state.sqlite'); lib = SkillLibrary(store,h.world,h.actions)
        lib.register('child','step',"act('do')", "count('wood') >= 1")
        lib.register('parent','call',"run('child')", "count('wood') >= 1")
        lib.register('outer','call',"run('parent')", "count('wood') >= 1")
        for label, name, source in [('direct','loop',"run('loop')"), ('indirect','child',"run('parent')"), ('depth','four',"run('outer')")]:
            try: lib.register(name,'bad',source,'False')
            except Denied as error: rows[label] = str(error)
            else: raise AssertionError(label)
        for source in ["x = 1", "1 + 2", "open('x')", "__import__('os')", 'observe().__class__']:
            try: parse(source)
            except Denied: pass
            else: raise AssertionError(source)
        assert completed("not seen('water') and (need('health') > 0 or count('wood') > 2)",h.observe())
        h.env._world[h.env._player.pos+(1,0)] = 'tree'
        result = run('',h.observe,h.act,library=lib,name='outer',timeout_s=5)
        assert result['steps'] == 1 and [c['outcome'] for c in result['calls']] == ['success']*3
        rows['success'] = result
        result = run('',h.observe,h.act,library=lib,name='outer',timeout_s=5)
        assert result['status'] == 'not_needed' and result['steps'] == 0
        rows['not_needed'] = result
        lib.register('child','many',"for _ in range(8):\n act('noop')",'False')
        lib.register('parent','call',"act('noop')\nrun('child')",'False')
        result = run('',h.observe,h.act,library=lib,name='parent',max_steps=3,timeout_s=5)
        assert result['status'] == 'step_limit' and result['steps'] == 3
        assert result['calls'][1]['steps'] == 2 and result['calls'][1]['version'] == 2
        assert all(c['outcome'] == 'unsuccessful' for c in result['calls'])
        rows['budget_version_unsuccessful'] = result
        lib.register('child','loop','while True:\n 1','False')
        result = run('',h.observe,h.act,library=lib,name='parent',timeout_s=.8)
        assert result['status'] == 'timeout' and result['seconds'] < 2
        rows['shared_time'] = result
        # Bypass registry to test runtime independently against poisoned records.
        poisoned = {'a':dict(source="run('b')",completion='False',version=1), 'b':dict(source="run('a')",completion='False',version=1)}
        result = run('',h.observe,h.act,library=poisoned,name='a',timeout_s=5)
        assert result['reason'] == 'recursive_skill'; rows['runtime_cycle'] = result
        poisoned = {str(i):dict(source=f"run('{i+1}')",completion='False',version=1) for i in range(4)}
        result = run('',h.observe,h.act,library=poisoned,name='0',timeout_s=5)
        assert result['reason'] == 'depth_limit'; rows['runtime_depth'] = result
        lib.register('child','hurt',"for _ in range(8):\n act('do')",'False')
        lib.register('parent','call',"run('child')",'False')
        p = h.env._player; h.env._world.add(Arrow(h.env._world,p.pos+(0,1),(0,-1)))
        result = run('',h.observe,h.act,library=lib,name='parent',timeout_s=5)
        assert result['status'] == 'injured' and result['steps'] == 1 and len(result['calls']) == 2
        rows['nested_injury'] = result
        cancel = threading.Event()
        def act(action):
            obs = h.act(action); cancel.set(); return obs
        result = run('',h.observe,act,library=lib,name='parent',timeout_s=5,cancel=cancel)
        assert result['status'] == 'cancelled' and result['steps'] == 1
        rows['nested_takeover'] = result
        store.close()
    return rows


def known_rule(action, experience, scope='global'):
    return {'action':action,'preconditions':{'inventory_min':{'wood':1},'nearby':['table'],'front_materials':[],'front_entity':None},
            'expected':{'inventory':{'wood_pickaxe':1,'wood':-1},'needs':{},'front':{}},'scope':scope,'experiences':[experience]}


def c3():
    import tempfile
    from growthlab.state import Store
    from growthlab.rules import Rules
    with tempfile.TemporaryDirectory() as folder:
        h = fixture(); store = Store(Path(folder)/'state.sqlite'); rules = Rules(store,h.world,h.actions)
        exp = store.put('experience',{'type':'observation','observation':h.observe()},'experienced',world=h.world)
        identity = rules.register(known_rule('make_wood_pickaxe',exp))
        local = rules.register(known_rule('make_wood_pickaxe',exp,'world'))
        def step():
            before = h.observe(); predictions = rules.predict(before,'make_wood_pickaxe'); after = h.act('make_wood_pickaxe')
            exp_id = store.put('experience',dict(before=before,after=after,action='make_wood_pickaxe'),'experienced',world=h.world)
            scores = rules.score(before,after,'make_wood_pickaxe',exp_id)
            assert rules.score(before,after,'make_wood_pickaxe',exp_id) == []
            return predictions,scores
        assert step() == ([],[])
        p = h.env._player; p.inventory['wood'] = 3; h.env._world[p.pos+(-1,0)] = 'table'
        assert all(x['match'] for x in step()[1])
        p.inventory['energy'] = 5; p.sleeping = True
        # An observed counterexample: prerequisites hold but the sleeping player does not craft.
        assert all(not x['match'] for x in step()[1])
        cards = rules.cards(); assert all(c['support']==1 and c['counterexamples']==1 for c in cards)
        try: rules.register(known_rule('make_wood_pickaxe','invented'))
        except ValueError as e: assert str(e) == 'unknown_experience'
        else: raise AssertionError('fabricated id accepted')
        other = Rules(store,'f'*32,h.actions)
        assert [c['id'] for c in other.cards()] == [identity]
        try: other.register(known_rule('make_wood_pickaxe',exp,'world'))
        except ValueError as e: assert str(e) == 'scope_leak'
        else: raise AssertionError('scope accepted')
        store.close()
    return {'counts':cards,'false_preconditions_not_counted':True,'duplicate_not_counted':True,
            'fake_id_rejected':True,'scope_enforced':True,'truth_judge':'program_only'}


if __name__ == '__main__': main()
