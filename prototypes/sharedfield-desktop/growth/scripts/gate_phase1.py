"""G0 probes around the frozen runtime. No pilot state or runtime edits.

prepare constructs and freezes fixtures/criteria before any paid request.
run makes 180 decisions (without executing them) and 20 consolidations,
serially, using the existing phase-1 route and shared reservation ledger.
"""
import argparse
import ast
import copy
import datetime
import json
import random
import secrets
import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from growthlab.agent import Episode
from growthlab.changes import changes
from growthlab.consolidation import consolidate
from growthlab.contract import ACTIONS, ITEMS, validate
from growthlab.decision import messages, decision_format, decode, MEMORY_TOKENS
from growthlab.forks import file_hash
from growthlab.host import Host
from growthlab.memory import Memory, compact
from growthlab.models import Cloud, MODEL, ROUTE
from growthlab.records import ROOT, write_json, telemetry
from growthlab.rules import validate_card, applicable, matches
from growthlab.sandbox import parse
from growthlab.state import Store
from growthlab.variants import generate

RUN = ROOT / 'runs/phase1/g0'
OUT = ROOT / 'evidence/phase1'
DIRS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
MOVES = {(1, 0): 'move_right', (-1, 0): 'move_left', (0, 1): 'move_down', (0, -1): 'move_up'}
RETRYABLE = {'http_429', 'http_502', 'http_503', 'http_504', 'TimeoutError', 'URLError'}


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def card(action, *, inventory=None, nearby=None, front=None, entity='none', delta=None, needs=None, final=None, ids=None):
    return {'action': action, 'scope': 'global', 'experiences': ids or [uuid.uuid4().hex],
            'preconditions': {'inventory_min': inventory or {}, 'nearby': nearby or [],
                              'front_materials': front or [], 'front_entity': entity},
            'expected': {'inventory': delta or {}, 'needs': needs or {}, 'front': final or {}}}


def note(c):
    """Plain text with the same named constraints/predictions, no action command."""
    p, e = c['preconditions'], c['expected']
    return ('过去记录的候选规律：动作 ' + c['action'] + '；背包最低数量 ' + compact(p['inventory_min'])
            + '；身边 3×3 材质 ' + compact(p['nearby']) + '；面前材质任选其一 ' + compact(p['front_materials'])
            + '；面前实体 ' + str(p['front_entity']) + '（none 表示无实体）；预期背包数量变化 ' + compact(e['inventory'])
            + '；预期需求变化 ' + compact(e['needs']) + '；预期面前同一格的最终内容 ' + compact(e['front'])
            + '。空字段不约束。作用域 global；来源经历 ' + ','.join(c['experiences']) + '；支持 0，反例 0。')


def make_a_case(fact, i, aliases):
    facing = DIRS[i % 4]
    side = DIRS[(i % 4 + (1 if i % 2 else 3)) % 4]
    cells = [{'dx': x, 'dy': y, 'material': 'grass', 'entity': 'player' if (x, y) == (0, 0) else None,
              'visible_state': None} for x in range(-4, 5) for y in range(-3, 4)]
    cells[0]['material'] = 'stone' if i % 2 else 'water'
    actions = sorted(aliases.get(a, a) for a in ACTIONS) if fact == 'neutral' else list(ACTIONS)
    obs = {'schema': 'growth.obs.v1.1', 'world': uuid.uuid4().hex, 'tick': i * 7,
           'needs': {'health': 9, 'food': 2 if fact == 'contrary' else 6 + i % 3, 'drink': 7 + i % 3, 'energy': 6 + i % 4},
           'inventory': {k: (2 if k == 'wood' else i % 2 if k == 'sapling' else 0) for k in ITEMS},
           'light': 1.0, 'radius': 4, 'cells': cells, 'displacement': [0, 0], 'facing': list(facing),
           'sleeping': False, 'done': False, 'actions': actions}
    ids = [uuid.uuid4().hex]
    if fact == 'neutral':
        true_action, false_action = aliases['place_table'], aliases['place_furnace']
        true = card(true_action, inventory={'wood': 2}, nearby=['grass'], front=['grass'],
                    delta={'wood': -2}, final={'material': 'table', 'entity': None}, ids=ids)
        false = dict(copy.deepcopy(true), action=false_action)
        goal = '放一个工作台 (table)'
    elif fact == 'supplement':
        true_action, false_action = 'place_table', 'make_wood_pickaxe'
        true = card('make_wood_pickaxe', inventory={'wood': 1}, nearby=['table'],
                    entity=None, delta={'wood': -1, 'wood_pickaxe': 1}, ids=ids)
        false = copy.deepcopy(true)
        false['preconditions']['nearby'] = []
        goal = '做木镐 (wood_pickaxe)'
    else:
        distance = 2 + i % 2
        for cell in cells:
            if (cell['dx'], cell['dy']) == facing:
                cell['entity'] = 'cow'
            elif (cell['dx'], cell['dy']) == (side[0] * distance, side[1] * distance):
                cell['entity'] = 'plant'; cell['visible_state'] = {'plant_ripe': True}
        true_action, false_action = MOVES[side], 'do'
        true = card('do', entity='cow', needs={'health': -2, 'food': 0}, ids=ids)
        false = card('do', entity='cow', needs={'health': 0, 'food': 6}, ids=ids)
        goal = '补充食物 (food)'
    validate(obs)
    for c in (true, false): validate_card(c, actions)
    return {'id': f'{fact}_{i:02}', 'fact': fact, 'index': i, 'observation': obs, 'goal': goal,
            'true_card': true, 'false_card': false, 'true_target': true_action, 'false_target': false_action}


def fixture(seed, aliases=None, facing=(1, 0), wood=3):
    host = Host(seed=seed, length=300, aliases=aliases)
    player, world = host.env._player, host.env._world
    for obj in world.objects:
        if obj is not player: world.remove(obj)
    for x in range(-7, 8):
        for y in range(-7, 8): world[player.pos + (x, y)] = 'grass'
    player.facing = facing; player.inventory['wood'] = wood
    host.env._balance_chunk = lambda *args: None
    return host


def transition(host, action):
    before = host.observe(); after = host.act(action)
    return {'type': 'transition', 'before': before, 'after': after, 'action': action,
            'change': changes(before, after, action)}


def make_b_case(i, seed, aliases):
    renamed = i >= 5
    host = fixture(seed, aliases if renamed else None, DIRS[i % 4], 6 if renamed else 3 + i % 3)
    rows = []
    if renamed:
        facing = DIRS[i % 4]; side = DIRS[(i % 4 + 1) % 4]
        for j in range(3):
            host.env._player.facing = facing
            rows.append(transition(host, aliases['place_table']))
            if j < 2:
                host.act(MOVES[side]); host.act(MOVES[side])
        assert all(r['change']['effects']['inventory'].get('wood') == -2 for r in rows)
    else:
        for action in ('make_wood_pickaxe', 'place_table', 'make_wood_pickaxe'):
            rows.append(transition(host, action))
        assert 'no_visible_effect' in rows[0]['change']['events']
        assert rows[-1]['change']['effects']['inventory']['wood_pickaxe'] == 1
    return {'id': f'b_{i:02}', 'seed': seed, 'family': 'renamed' if renamed else 'workbench',
            'observation': host.observe(), 'transitions': rows}


def a_messages(case, arm, condition):
    if condition == 'none': memory = []
    else:
        c = case[f'{condition}_card']
        memory = ([{'type': 'rule_card', **c, 'support': 0, 'counterexamples': 0}]
                  if arm == 'B' else [{'type': 'reflection', 'content': {'text': note(c)}}])
    assert len(compact(memory).encode()) <= MEMORY_TOKENS
    return messages(case['observation'], case['goal'], memory, [], [])


def first_action(choice):
    if choice['kind'] == 'action': return choice['action'], 'direct'
    if choice['kind'] == 'write':
        tree = parse(choice['source'])
        if tree.body:
            node = tree.body[0]
            if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                    and node.value.func.id == 'act'):
                return node.value.args[0].value, 'literal_first_statement'
    return None, 'unresolved_program_or_run'


def prepare():
    RUN.mkdir(parents=True, exist_ok=False)
    pilot = read(ROOT / 'runs/phase1/pilot/manifest.json')
    forbidden = {s for groups in (pilot['practice_seeds'], pilot['test_seeds']) for values in groups.values() for s in values}
    seeds = []
    while len(seeds) < 22:
        value = secrets.randbelow(2**31 - 1) + 1
        if value not in forbidden and value not in seeds: seeds.append(value)
    aliases = generate('rename_actions', seeds[0])['aliases']
    cases = [make_a_case(fact, i, aliases) for fact in ('neutral', 'supplement', 'contrary') for i in range(10)]
    jobs = [{'case': c['id'], 'arm': arm, 'condition': cond} for c in cases for arm in ('B', 'A') for cond in ('none', 'true', 'false')]
    random.Random(seeds[1]).shuffle(jobs)
    b_cases = [make_b_case(i, seeds[i + 2], aliases) for i in range(10)]
    unrelated = []
    for i, seed in enumerate(seeds[12:]):
        host = fixture(seed, wood=0)
        rows = [transition(host, a) for a in ('move_up', 'move_right', 'noop')]
        unrelated.append({'observation': host.observe(), 'transitions': rows})
    for c in cases:
        packets = [a_messages(c, arm, cond) for arm in ('A', 'B') for cond in ('none', 'true', 'false')]
        stripped = []
        for msg in packets:
            p = json.loads(msg[1]['content']); p.pop('memory'); stripped.append(p)
        assert all(p == stripped[0] for p in stripped)
    manifest = {'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                'purpose': 'G0 engineering gates only; not E1 or a learning claim', 'model': MODEL, 'route': ROUTE,
                'temperature': 0, 'concurrency': 1, 'phase1_shared_budget_usd': 5, 'max_wall_seconds': 3600,
                'source_sha256': {**pilot['source_sha256'], str(Path(__file__).relative_to(ROOT)): file_hash(__file__)},
                'pilot_prompt_version': pilot['prompt_version'], 'seeds': seeds, 'pilot_seeds_disjoint': not (set(seeds) & forbidden),
                'aliases': aliases, 'a_cases': cases, 'a_jobs': jobs, 'b_cases': b_cases, 'c_unrelated': unrelated,
                'planned_calls': {'a_next_decisions': 180, 'b_consolidations': 10, 'c_consolidations': 10},
                'criteria': {
                    'G0a': 'B neutral true AND false: each >=8/10 following the injected card target. Other facts and A are descriptive only.',
                    'a_scoring': 'No model action/program is executed. Strict-decode outputs; direct action or literal act in the first top-level source statement supplies the next action. Other programs/invalid outputs count as non-following, never retried for content. None-memory is reported against both target actions, not assigned a memory-follow score.',
                    'a_targets': 'neutral: injected symbol for place_table; supplement true: place_table, false: make_wood_pickaxe; contrary true: unique clear first move toward the ripe plant, false: do toward facing cow. These narrow next-action targets are frozen before responses.',
                    'a_fixtures': 'Allowed synthetic observation packets, no sampled pilot world and no privileged field. Contrary truth is a stipulated counterfactual, not a live gameplay test. All arms/conditions for a case have identical observation/goal/system; only memory differs. Cards and equivalent plain notes bypass retrieval.',
                    'G0b': '>=8/10 datasets: at least one accepted rule; EVERY accepted rule cites only supplied valid transition IDs, applies to at least one cited transition, and matches every applicable transition in that dataset. No vacuous successes; zero/rejected-only proposals fail. Program applicable/matches only, no LLM grading.',
                    'b_fixtures': 'Five workbench and five renamed-placement datasets, three selected actual transitions each in evaluator-cleared arenas. Setup/facing changes and intervening moves are fixture construction; datasets are selected synthetic records, not autonomous trajectories.',
                    'G0c': 'Reuse b_00 evidence IDs plus three unrelated transitions in a new world per round; ten serial consolidations of the same store. Begin with two injected, program-checked global rules (table placement and pickaxe with table), independent of G0b outcome. Each seed prediction must remain available under at least one active rule with all its named expected fields; no active rule may contradict applicable fixed evidence. Any loss/corruption fails G0c but does not stop pilot. No enforcement added to frozen writes.',
                    'stopping': 'G0a/G0b failure prohibits resuming pilot; this pilot was already stopped for HTTP502 before G0. G0 still reports all gates unless resource/transport stop. No automatic fixes or rerun.',
                    'transport': 'Single concurrency. At most one retry after 30s for retryable transport failures on an identical input; two failures stop G0. Successful invalid content is not retried. Unknown reservations retained; shared $5 and AC/time stops.'}}
    write_json(RUN / 'manifest.json', manifest); write_json(OUT / 'G0_MANIFEST.json', manifest)
    print({'prepared': True, 'calls': 200, 'seeds_disjoint': True, 'runtime_unchanged': check_lock(manifest)})


def check_lock(manifest):
    for source, expected in manifest['source_sha256'].items():
        if file_hash(ROOT / source) != expected: raise ValueError('frozen_source_changed:' + source)
    return True


class GateStop(RuntimeError): pass


class Client:
    def __init__(self, status):
        self.status = status; self.context = {}; self.last_sample = 0
        self.base = Cloud(budget_path=ROOT / 'runs/phase1/budget.sqlite')

    def log(self, value):
        with (RUN / 'calls.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(compact(value) + '\n')

    def decide(self, prompt, **kwargs):
        for attempt in (1, 2):
            now = time.time()
            if now - self.status['started_unix'] >= 3600: raise GateStop('machine_time_limit')
            if now - self.last_sample >= 30:
                sample = telemetry(); self.status['telemetry'].append(sample); self.last_sample = now
                if sample['ac_online'] is not True: raise GateStop('ac_required')
            self.status['current'] = dict(self.context, attempt=attempt)
            write_json(RUN / 'status.json', self.status)
            before = {r[0] for r in self.base.db.execute('SELECT id FROM charges')}
            self.log({'type': 'request', 'time': now, 'context': self.context, 'attempt': attempt, 'messages': prompt, **kwargs})
            try:
                output, meta = self.base.decide(prompt, **kwargs)
            except (RuntimeError, ValueError) as error:
                code = str(error)
                charges = [dict(zip(('id', 'usd', 'status'), r)) for r in self.base.db.execute('SELECT id,usd,status FROM charges') if r[0] not in before]
                self.log({'type': 'error', 'time': time.time(), 'context': self.context, 'attempt': attempt, 'code': code, 'charges': charges})
                self.status['errors'].append({'context': self.context, 'attempt': attempt, 'code': code, 'charges': charges})
                write_json(RUN / 'status.json', self.status)
                if code not in RETRYABLE or attempt == 2: raise GateStop(code) from None
                time.sleep(30)
                continue
            self.log({'type': 'response', 'time': time.time(), 'context': self.context, 'attempt': attempt, 'output': output, 'meta': meta})
            self.status['returned_calls'] += 1
            return output, meta


def record_checks(memory, evidence, supplied_ids):
    checked = []
    for c in memory.rules.cards():
        cited = c['experiences']
        valid_ids = bool(cited) and set(cited) <= set(supplied_ids) and set(cited) <= set(evidence)
        relevant = [key for key, row in evidence.items() if applicable(c, row['before'], row['action'])]
        cited_applicable = [key for key in relevant if key in cited]
        failures = [key for key in relevant if not matches(c, evidence[key]['before'], evidence[key]['after'])]
        checked.append({'id': c['id'], 'card': c, 'valid_citations': valid_ids,
                        'applicable_ids': relevant, 'cited_applicable_ids': cited_applicable, 'mismatched_ids': failures,
                        'correct': valid_ids and bool(cited_applicable) and not failures})
    return checked


def synthetic_episode(folder, store, client, fixture_data, base_ids=()):
    obs = fixture_data['observation']
    host = SimpleNamespace(world=obs['world'], actions=obs['actions'], observe=lambda: copy.deepcopy(obs))
    memory = Memory(store, host.world, host.actions, 'B', restarted=bool(base_ids))
    episode = Episode(host, store, folder, client, memory=memory)
    episode.experiences.extend(base_ids)
    evidence = {}
    for row in fixture_data['transitions']:
        identity = episode.experience(row, 'synthetic_gate_fixture'); evidence[identity] = row
    return episode, memory, evidence


def run():
    manifest = read(RUN / 'manifest.json'); check_lock(manifest)
    if (RUN / 'status.json').exists(): raise ValueError('g0_already_started')
    status = {'started_unix': time.time(), 'completed': [], 'current': None, 'returned_calls': 0,
              'errors': [], 'stop': None, 'telemetry': []}
    write_json(RUN / 'status.json', status)
    client = None
    try:
        client = Client(status)
        cases = {c['id']: c for c in manifest['a_cases']}
        for job in manifest['a_jobs']:
            name = 'a_' + job['case'] + '_' + job['arm'] + '_' + job['condition']
            client.context = {'stage': 'G0a', 'id': name}
            c = cases[job['case']]; prompt = a_messages(c, job['arm'], job['condition'])
            output, meta = client.decide(prompt, response_format=decision_format(c['observation']['actions']), max_tokens=2048)
            error = None; choice = None; action = None; method = None
            try:
                choice = decode(output, c['observation']['actions']); action, method = first_action(choice)
            except (ValueError, KeyError, TypeError) as caught: error = type(caught).__name__
            result = {'job': job, 'output': output, 'choice': choice, 'decode_error': error, 'next_action': action,
                      'classification': method, 'follow_true_target': action == c['true_target'],
                      'follow_false_target': action == c['false_target'], 'executed_actions': 0, 'meta': meta}
            write_json(RUN / 'results' / (name + '.json'), result)
            status['completed'].append(name); write_json(RUN / 'status.json', status)
        for c in manifest['b_cases']:
            name = c['id']; folder = RUN / name; folder.mkdir()
            store = Store(folder / 'state.sqlite'); client.context = {'stage': 'G0b', 'id': name}
            episode, memory, evidence = synthetic_episode(folder, store, client, c)
            try:
                sleep = consolidate(episode)
                checks = record_checks(memory, evidence, sleep.get('supplied_experiences', []))
                result = {'case': name, 'sleep': sleep, 'evidence': evidence, 'cards': checks,
                          'passed': bool(checks) and all(c['correct'] for c in checks), 'memory': memory.export()}
                write_json(RUN / 'results' / (name + '.json'), result)
            finally: episode.close(); store.close()
            status['completed'].append(name); write_json(RUN / 'status.json', status)
        # Seed correct memories explicitly, so empty G0b output cannot make G0c vacuous.
        folder = RUN / 'c'; folder.mkdir(); store = Store(folder / 'state.sqlite')
        base = manifest['b_cases'][0]
        seed_episode, seed_memory, evidence = synthetic_episode(folder / 'seed', store, client, base)
        base_ids = list(evidence)
        place_id = next(k for k, r in evidence.items() if r['action'] == 'place_table')
        make_id = next(k for k, r in evidence.items() if r['action'] == 'make_wood_pickaxe' and r['change']['effects']['inventory'].get('wood_pickaxe') == 1)
        templates = [card('place_table', inventory={'wood': 2}, front=['grass'], delta={'wood': -2},
                          final={'material': 'table', 'entity': None}, ids=[place_id]),
                     card('make_wood_pickaxe', inventory={'wood': 1}, nearby=['table'], entity=None,
                          delta={'wood': -1, 'wood_pickaxe': 1}, ids=[make_id])]
        roots = [seed_memory.rules.register(c) for c in templates]
        assert all(c['correct'] for c in record_checks(seed_memory, evidence, base_ids))
        write_json(folder / 'seed.json', {'roots': roots, 'templates': templates, 'evidence': evidence, 'memory': seed_memory.export()})
        seed_episode.close()
        try:
            for index, irrelevant in enumerate(manifest['c_unrelated']):
                name = f'c_{index:02}'; client.context = {'stage': 'G0c', 'id': name}
                episode, memory, extra = synthetic_episode(folder / name, store, client, irrelevant, base_ids)
                try:
                    sleep = consolidate(episode)
                    evidence.update(extra)
                    active = memory.rules.cards()
                    retained = []
                    for root, template in zip(roots, templates):
                        witness = evidence[template['experiences'][0]]
                        equivalents = [c['id'] for c in active if applicable(c, witness['before'], witness['action'])
                                       and matches(c, witness['before'], witness['after'])
                                       and all(all(c['expected'][field].get(k) == v for k, v in expected.items())
                                               for field, expected in template['expected'].items())]
                        retained.append({'root': root, 'equivalent_active_ids': equivalents})
                    contradictions = [{'card': c['id'], 'experience': key} for c in active for key, row in evidence.items()
                                      if applicable(c, row['before'], row['action']) and not matches(c, row['before'], row['after'])]
                    result = {'round': index + 1, 'sleep': sleep, 'retained': retained, 'contradictions': contradictions,
                              'passed': all(r['equivalent_active_ids'] for r in retained) and not contradictions,
                              'memory': memory.export(), 'new_unrelated_evidence': extra}
                    write_json(RUN / 'results' / (name + '.json'), result)
                finally: episode.close()
                status['completed'].append(name); write_json(RUN / 'status.json', status)
        finally: store.close()
    except Exception as error:
        status['stop'] = str(error) if isinstance(error, (GateStop, ValueError)) else type(error).__name__
    finally:
        if client: client.base.db.close()
        status['finished_unix'] = time.time(); status['elapsed_seconds'] = time.time() - status['started_unix']
        status['frozen_sources_unchanged'] = check_lock(manifest)
        write_json(RUN / 'status.json', status)
        print({k: status[k] for k in ('stop', 'elapsed_seconds', 'returned_calls', 'frozen_sources_unchanged')})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode', choices=['prepare', 'run']); args = parser.parse_args()
    (prepare if args.mode == 'prepare' else run)()
