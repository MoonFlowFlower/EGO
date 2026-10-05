"""One frozen real-model test in an explicit inventory simulator; no MC client."""
import argparse
import concurrent.futures
import copy
import hashlib
import json
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .harness import Harness
from .memory import Memory
from .model import Model
from .initiative import projects, records, experience_context

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'evidence/kernel_initiative_v1'
FREEZE = EVIDENCE / 'PAID_FREEZE.json'
RUNS = ROOT / 'runs/kernel_initiative_v1'
REVISION = 1
TEXT = '我忙一会儿。你自己选个有用的事情做，可以使用背包现有材料合成和整理；不采集、不放置。'


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    files = [p for p in (ROOT / 'companion').iterdir() if p.suffix in ('.py', '.mjs', '.txt', '.ps1')]
    files += [EVIDENCE / 'ACCEPTANCE.md']
    if REVISION == 2: files += [EVIDENCE / 'ACCEPTANCE_R2.md']
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(files)}


def ledger_total():
    with sqlite3.connect(DEFAULT_BUDGET.resolve().as_uri() + '?mode=ro', uri=True) as db:
        return db.execute('SELECT sum(usd) FROM charges').fetchone()[0]


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


class InventoryScene:
    """Fixed recipe subset and a single exogenous workspace fault.

    This is a constructed observation/action test, not Minecraft evidence.
    It supplies no goals, tree, priorities or next-action choices to the model.
    """
    def __init__(self, case, revision=1):
        self.actions, self.speech = [], []
        self.case, self.injected = case, False
        self.wood = ('spruce' if revision == 2 else 'oak') if case == 'initial' else 'birch'
        self.state = {'offline': False, 'position': {'x': 12, 'y': 109, 'z': -57},
            'inventory': {self.wood + '_log': 3, 'coal': 2}, 'owner': {'distance': 6, 'height_difference': 0},
            'crafting_grid': {}, 'cursor': None, 'window': None, 'health': 20, 'food': 20}
        if case != 'initial':
            self.state['position'] = {'x': 25, 'y': 70, 'z': 8}
            self.state['inventory'][self.wood + '_log'] -= 1
            self.state['crafting_grid'] = {self.wood + '_log': 1}

    def snapshot(self): return copy.deepcopy(self.state)
    def say(self, text): self.speech.append(text)
    def stop(self): return {'verified': True, 'status': 'stopped'}

    def start_action(self, action, **kw):
        self.actions.append(copy.deepcopy(action))
        name, args = action['name'], action['args']
        receipt = {'verified': True, 'status': 'observed'}
        if name == 'craft':
            if self.case == 'initial' and not self.injected:
                # A change after the initial observation, independent of goal/tree.
                self.injected = True
                self.state['inventory'][self.wood + '_log'] -= 1
                self.state['crafting_grid'] = {self.wood + '_log': 1}
            if self.state['crafting_grid']:
                receipt = {'verified': False, 'status': 'crafting_grid_or_cursor_not_clear'}
            else:
                recipes = {self.wood + '_planks': ({self.wood + '_log': 1}, 4),
                           'stick': ({self.wood + '_planks': 2}, 4),
                           'crafting_table': ({self.wood + '_planks': 4}, 1),
                           'torch': ({'coal': 1, 'stick': 1}, 4)}
                recipe = recipes.get(args['item'])
                if not recipe:
                    receipt = {'verified': False, 'status': 'recipe_unavailable'}
                elif any(self.state['inventory'].get(k, 0) < n * args['count'] for k, n in recipe[0].items()):
                    receipt = {'verified': False, 'status': 'missing_ingredients'}
                else:
                    for item, count in recipe[0].items(): self.state['inventory'][item] -= count * args['count']
                    gained = recipe[1] * args['count']
                    self.state['inventory'][args['item']] = self.state['inventory'].get(args['item'], 0) + gained
                    receipt = {'verified': True, 'status': 'craft_inventory_checked', 'gained': gained}
        elif name == 'recover_inventory':
            for item, count in self.state['crafting_grid'].items():
                self.state['inventory'][item] = self.state['inventory'].get(item, 0) + count
            self.state['crafting_grid'] = {}; self.state['cursor'] = None; self.state['window'] = None
            receipt = {'verified': True, 'status': 'inventory_recovered', 'conserved': True}
        elif name != 'inspect':
            receipt = {'verified': False, 'status': 'simulator_interface_not_available'}
        receipt['observed'] = self.snapshot()
        future = concurrent.futures.Future(); future.set_result(receipt)
        return future


def run_child(folder, case):
    authorization = json.loads((folder.parent / 'AUTHORIZATION.json').read_bytes())
    if manifest() != json.loads(FREEZE.read_bytes())['sha256']: raise ValueError('freeze_mismatch')
    key = read_key()
    audit = AuditLog(folder, (key,))
    transport = RoutedTransportV2(api_key=key, mode='pinned', route_index=0,
        budget_path=DEFAULT_BUDGET, limit=authorization['limit'], log_dir=folder)
    transport.set_audit(audit)
    model, body = Model(transport, audit), InventoryScene(case, REVISION)
    path = folder / 'state.sqlite'
    engine = Harness(path, model, body, audit, max_decisions=20, max_seconds=180)
    with Memory(path) as memory:
        raw = experience_context(memory, projects(memory))
        raw_hash = hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()
        policy_count = len(records(memory, 'skill', 'initiative_policy'))
        previous_tasks = {p['work']['task_id'] for p in projects(memory)}
        previous_projects = [p['project_id'] for p in projects(memory)]
    before = ledger_total()
    engine.run('delegation:' + case, 'verification', TEXT)
    engine.initiative.drain_one()
    engine.stop()
    with Memory(path) as memory:
        saved = memory.goal()
        policies = records(memory, 'skill', 'initiative_policy')
        failures = [r['body']['receipt']['status'] for r in memory.library.rows('experience')
                    if r['body'].get('type') == 'action_receipt' and r['body']['receipt'].get('verified') is False]
        turns = memory.db.execute("SELECT count(*) FROM kernel_turns WHERE event_id=?", ('delegation:' + case,)).fetchone()[0]
        work = saved.get('work', {}) if saved else {}
        fresh = bool(work.get('initiative') and work.get('request', {}).get('channel') == 'initiative'
                     and work.get('task_id') not in previous_tasks)
        status = saved.get('goal_status') if fresh else 'no_new_goal'
    result = {'case': case, 'simulated_body': True, 'status': status, 'new_autonomous_goal': fresh,
        'actions': body.actions, 'state': body.snapshot(), 'injected_fault': body.injected,
        'retained_failures': failures, 'policy_count_before': policy_count, 'policy_count_after': len(policies),
        'latest_policy_based_on': policies[-1].get('based_on_policy') if len(policies) > policy_count else None,
        'project_id': work.get('initiative', {}).get('project_id') if fresh else None,
        'prior_project_ids': previous_projects,
        'raw_experience_sha256_before': raw_hash, 'owner_turn_count': turns, 'model_calls': model.calls,
        'cost_delta': ledger_total() - before, 'budget_total': ledger_total()}
    write(folder / 'RESULT.json', result)
    print(json.dumps({k: result[k] for k in ('case', 'status', 'model_calls', 'cost_delta')}, ensure_ascii=False))


def run():
    frozen = json.loads(FREEZE.read_bytes())
    if manifest() != frozen['sha256']: raise ValueError('freeze_mismatch')
    root = RUNS / ('paid_' + ('r2_' if REVISION == 2 else '') + str(time.time_ns())); root.mkdir(parents=True)
    with (RUNS / f'PAID_V{REVISION}_CONSUMED.json').open('x', encoding='utf-8') as marker:
        json.dump({'root': str(root), 'freeze_sha256': sha(FREEZE)}, marker)
    start = ledger_total()
    batch = json.loads((ROOT / 'runs/kernel_v1/batch_budget.json').read_bytes())
    limit = min(5, batch['limit'], batch['start_total'] + batch['extra_cap'], start + .35)
    if REVISION == 2:
        previous = json.loads((RUNS / 'PAID_V1_CONSUMED.json').read_bytes())
        initial = json.loads((Path(previous['root']) / 'AUTHORIZATION.json').read_bytes())
        limit = min(limit, initial['limit'])
    write(root / 'AUTHORIZATION.json', {'start_total': start, 'extra_cap': max(0, limit-start), 'limit': limit,
        'freeze_sha256': sha(FREEZE), 'source': 'user agreed to DESIGN.md; ACCEPTANCE.md frozen before validation'})
    owner = ROOT / 'runs/kernel_v1/owner/state.sqlite'
    owner_before = sha(owner)
    results = {}
    for case in ('initial', 'transfer', 'masked', 'restored'):
        if case != 'initial' and not (results['initial'].get('status') == 'completed'
                and results['initial'].get('injected_fault') and results['initial'].get('policy_count_after', 0) >= 2):
            results[case] = {'not_run': 'initial did not establish a completed revised policy'}
            continue
        folder = root / case; folder.mkdir()
        if case != 'initial':
            shutil.copyfile(root / 'initial/state.sqlite', folder / 'state.sqlite')
            # Same raw experiences/project summaries. Only compiled policy visibility changes.
            if case in ('masked', 'restored'):
                with sqlite3.connect(folder / 'state.sqlite') as db:
                    db.execute("UPDATE records SET status='masked' WHERE json_extract(body,'$.type')='initiative_policy'")
                    if case == 'restored':
                        db.execute("UPDATE records SET status='active' WHERE json_extract(body,'$.type')='initiative_policy'")
        try:
            done = subprocess.run([sys.executable, '-m', 'companion.verify_initiative_v1', '--revision', str(REVISION), '--child', case, '--folder', str(folder)],
                cwd=ROOT, capture_output=True, text=True, timeout=240,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            results[case] = json.loads((folder / 'RESULT.json').read_bytes()) if (folder / 'RESULT.json').exists() else {'failed': 'child_failed', 'exit_code': done.returncode}
        except subprocess.TimeoutExpired:
            results[case] = {'failed': 'child_timeout_no_retry'}
        print(json.dumps({'case': case, 'status': results[case].get('status'), 'failed': results[case].get('failed')}, ensure_ascii=False), flush=True)
    write(root / 'RESULT.json', {'frozen_source_match': manifest() == frozen['sha256'],
        'owner_unchanged': owner_before == sha(owner), 'start_total': start, 'end_total': ledger_total(),
        'cost_delta': ledger_total() - start, 'cases': results,
        'claim_ceiling': 'constructed inventory scene only; real MC, human conversation and learning advantage unverified'})
    print(str(root), flush=True)


def main():
    global FREEZE, REVISION
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true'); parser.add_argument('--run', action='store_true')
    parser.add_argument('--child', choices=('initial', 'transfer', 'masked', 'restored')); parser.add_argument('--folder', type=Path)
    parser.add_argument('--revision', type=int, choices=(1, 2), default=1)
    args = parser.parse_args()
    REVISION = args.revision
    if REVISION == 2: FREEZE = EVIDENCE / 'PAID_FREEZE_R2.json'
    if args.freeze:
        with FREEZE.open('x', encoding='utf-8', newline='\n') as file:
            json.dump({'base_commit': '6b90aa4' if REVISION == 2 else '98d3781', 'at': datetime.now().astimezone().isoformat(),
                       'sha256': manifest(), 'extra_budget_cap': .35}, file, indent=2)
            file.write('\n')
        print('frozen', len(manifest()), 'files')
    elif args.run: run()
    elif args.child and args.folder: run_child(args.folder, args.child)
    else: parser.error('select freeze, run, or internal child')


if __name__ == '__main__':
    try: main()
    except Exception as error:
        # Neither provider response bodies nor credentials cross stdout/stderr.
        print(json.dumps({'failed': type(error).__name__}), flush=True)
        raise SystemExit(1)
