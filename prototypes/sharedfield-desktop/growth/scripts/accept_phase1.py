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
    parser = argparse.ArgumentParser(); parser.add_argument('component', choices=['c1']); args = parser.parse_args()
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


if __name__ == '__main__': main()
