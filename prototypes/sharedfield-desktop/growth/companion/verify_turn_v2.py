"""One frozen model replay and simulated-body continuation; never opens Minecraft."""
import argparse
import concurrent.futures
import copy
import hashlib
import json
import sqlite3
import threading
import time
from datetime import datetime, timezone

from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .body import ROOT
from .harness import Harness
from .memory import Memory
from .model import Model
from .test_harness import Body as SimulatedBody, goal
from .work import create_work, save_work

EVIDENCE = ROOT / 'evidence/kernel_turn_v2'
FREEZE = EVIDENCE / 'FREEZE.json'
OWNER = ROOT / 'runs/kernel_v1/owner/state.sqlite'
SNAPSHOTS = ROOT / 'runs/kernel_v1/sessions/1791081296568067100/body_states.jsonl'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def manifest():
    files = sorted(p for p in (ROOT / 'companion').iterdir() if p.suffix in ('.py', '.mjs', '.txt', '.ps1'))
    files.append(EVIDENCE / 'CHECKLIST.md')
    return {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in files}


def freeze():
    with FREEZE.open('x', encoding='utf-8') as f:
        json.dump({'base_commit': 'f0477b5b', 'created_utc': datetime.now(timezone.utc).isoformat(),
                   'sha256': manifest()}, f, indent=2)
        f.write('\n')


def logical_state(path):
    m = Memory(path)
    try:
        return {'goal': m.goal(), 'cards': m.library.cards()}
    finally:
        m.close()


def synthetic_history(path, body):
    m = Memory(path)
    try:
        source, _ = m.begin('fixture', 'verification', '请放两块木板')
        w = create_work(goal(), body.snapshot(), source)
        w['status'], w['last_problem'] = 'blocked', 'crafting_grid_or_cursor_not_clear'
        save_work(m, w, [source])
        m.finish('fixture', '合成格和光标已经清空了。', [source])
    finally:
        m.close()


class ReadOnlyBody:
    def __init__(self, state):
        self.state, self.actions = copy.deepcopy(state), []
    def snapshot(self):
        return copy.deepcopy(self.state)
    def say(self, text):
        pass
    def start_action(self, action, **kw):
        self.actions.append(action)
        raise RuntimeError('acceptance_action_forbidden')
    def stop(self):
        return self.start_action({'name': 'stop', 'args': {}})


class InterruptedBody(SimulatedBody):
    def __init__(self):
        super().__init__()
        self.state['inventory'] = {'oak_planks': 2}
        self.state.update(model_client_initialized=False, generated_code_enabled=False)
        self.first_placement = threading.Event()
        self.held = None
        self.held_receipt = None

    def start_action(self, action, **kw):
        if action['name'] not in ('inspect', 'place', 'place_at', 'verify_blocks'):
            raise RuntimeError('simulated_action_boundary')
        future = super().start_action(action, **kw)
        if action['name'] in ('place', 'place_at') and len(self.blocks) == 1 and self.held is None:
            self.held_receipt, self.held = future.result(), concurrent.futures.Future()
            self.first_placement.set()
            return self.held
        return future

    def release(self):
        if self.held and not self.held.done():
            self.held.set_result(self.held_receipt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    if args.freeze:
        freeze()
        print(json.dumps({'freeze': str(FREEZE), 'files': len(manifest())}))
        return 0
    frozen = json.loads(FREEZE.read_text(encoding='utf-8'))['sha256']
    if manifest() != frozen:
        raise RuntimeError('frozen_source_changed')
    base = ROOT / 'runs/kernel_turn_v2'
    base.mkdir(parents=True, exist_ok=True)
    with (base / 'attempt.claim').open('x', encoding='utf-8') as f:
        f.write(str(time.time_ns()))
    folder = base / str(time.time_ns())
    folder.mkdir()
    (folder / 'manifest.json').write_text(json.dumps(frozen, indent=2) + '\n', encoding='utf-8')
    owner_hash = sha(OWNER)
    path = folder / 'facts.sqlite'
    with sqlite3.connect('file:' + OWNER.as_posix() + '?mode=ro', uri=True) as source:
        with sqlite3.connect(path) as target:
            source.backup(target)
    original = logical_state(path)
    if original['goal']['goal_status'] != 'blocked':
        raise RuntimeError('blocked_goal_fixture_required')
    state = next(json.loads(line)['state'] for line in reversed(SNAPSHOTS.read_text(encoding='utf-8').splitlines())
                 if not json.loads(line)['state'].get('offline'))
    if state['crafting_grid'] or state['cursor'] is not None or state['window'] is not None:
        raise RuntimeError('clear_body_fixture_required')
    key = read_key()
    audit = AuditLog(folder, (key,))
    ledger = BudgetLedger(DEFAULT_BUDGET, 5)
    total_before = ledger.total()
    batch = json.loads((ROOT / 'runs/kernel_v1/batch_budget.json').read_bytes())
    transport = RoutedTransportV2(api_key=key, mode='pinned', route_index=0, budget_path=DEFAULT_BUDGET,
                                  limit=min(batch['limit'], total_before + .15), log_dir=folder)
    transport.set_audit(audit)
    started = time.monotonic()
    failed = threading.Event()

    class RecordedModel(Model):
        def decide(self, prompt, context):
            if failed.is_set() or self.calls >= 24 or time.monotonic() - started >= 180:
                raise RuntimeError('acceptance_limit_or_previous_failure')
            try:
                result = super().decide(prompt, context)
            except Exception:
                failed.set()
                raise
            audit.write('decisions.jsonl', {'call': self.calls, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                                           'context': context, 'result': result})
            return result

    model = RecordedModel(transport, audit)
    result = {'run': folder.name, 'world_connection': False, 'body': 'deterministic_simulation',
              'semantic_review': 'pending', 'mechanical_passed': False, 'cases': []}

    def conversation(case, engine, db, body, text, expected_mode):
        before = logical_state(db)
        identity = 'verification:turn-v2:' + case
        reply = engine.run(identity, 'verification', text)
        m = Memory(db)
        try:
            routes = [r['body']['route'] for r in m.library.rows('reflection')
                      if r['body'].get('type') == 'input_route' and r['body'].get('event_id') == identity]
        finally:
            m.close()
        actual = routes[-1]['mode'] if routes else None
        check = {'case': case, 'input': text, 'reply': reply, 'mode': actual, 'expected_mode': expected_mode,
                 'goal_and_cards_unchanged': logical_state(db) == before, 'action_attempts': len(body.actions)}
        check['mechanical_passed'] = actual == expected_mode and check['goal_and_cards_unchanged'] and not body.actions
        result['cases'].append(check)
        if not check['mechanical_passed'] or failed.is_set() or 'turn_failed' in (folder / 'lifecycle.jsonl').read_text():
            raise RuntimeError('conversation_failed')

    threads, body = [], None
    try:
        audit.write('preflight.jsonl', transport.preflight())
        readonly = ReadOnlyBody(state)
        engine = Harness(path, model, readonly, audit)
        for case, text, mode in [('F1-greeting', '(｡･∀･)ﾉﾞ嗨', 'chat'), ('F1-status', '你怎么不动了', 'status'),
                                 ('F1-thought', '你现在在想做什么', 'status')]:
            conversation(case, engine, path, readonly, text, mode)
        for case, snapshot in [
            ('F2-residue', {**state, 'crafting_grid': {'acacia_log': 1}, 'cursor': {'name': 'acacia_planks', 'count': 2}}),
            ('F3-offline', {**state, 'offline': True, 'reason': 'no_fresh_body_state'})]:
            db = folder / (case + '.sqlite')
            readonly = ReadOnlyBody(snapshot)
            synthetic_history(db, readonly)
            conversation(case, Harness(db, model, readonly, audit), db, readonly,
                         '你现在在线吗？合成格和光标里还有东西吗？', 'status')

        body = InterruptedBody()
        db = folder / 'continuation.sqlite'
        engine = Harness(db, model, body, audit, max_decisions=12, max_seconds=90)
        outputs = {}
        def run(identity, channel, text):
            outputs[identity] = engine.run(identity, channel, text)
        task = threading.Thread(target=run, args=('task', 'minecraft', '请用背包现有木板，在附近空位放置两块橡木板，不需要造房子。'), daemon=True)
        threads.append(task); task.start()
        if not body.first_placement.wait(30):
            raise RuntimeError('first_placement_not_reached')
        initial = logical_state(db)['goal']['work']
        chat = threading.Thread(target=run, args=('chat', 'airi', '辛苦啦，现在进展怎么样？'), daemon=True)
        threads.append(chat); chat.start()
        until = time.monotonic() + 5
        while not engine._waiting and time.monotonic() < until:
            time.sleep(.01)
        if engine._waiting != 1:
            raise RuntimeError('chat_not_queued')
        body.release()
        for thread in threads:
            thread.join(max(0, min(60, 180 - (time.monotonic() - started))))
        if any(t.is_alive() for t in threads):
            raise RuntimeError('continuation_timeout')
        final = logical_state(db)['goal']['work']
        rows = [json.loads(line) for line in (folder / 'actions.jsonl').read_text().splitlines()]
        chat_actions = [row for row in rows if row['event_id'] == 'chat']
        check = {'case': 'C1', 'replies': outputs, 'same_task_id': initial['task_id'] == final['task_id'],
                 'same_source_id': initial['source_id'] == final['source_id'], 'same_done_when': initial['done_when'] == final['done_when'],
                 'status': final['status'], 'distinct_placements': len(body.blocks), 'inventory_net_loss': 2 - body.state['inventory']['oak_planks'],
                 'chat_actions': len(chat_actions), 'world_readback': bool(final.get('completion', {}).get('world_verified')),
                 'resumed': 'task_resumed_after_conversation' in (folder / 'lifecycle.jsonl').read_text()}
        check['mechanical_passed'] = (check['same_task_id'] and check['same_source_id'] and check['same_done_when']
            and check['status'] == 'completed' and check['distinct_placements'] == 2 and check['inventory_net_loss'] == 2
            and not chat_actions and check['world_readback'] and check['resumed'])
        result['cases'].append(check)
        result['mechanical_passed'] = all(c['mechanical_passed'] for c in result['cases']) and not failed.is_set()
    except Exception as error:
        failed.set()
        result['error_type'] = type(error).__name__
        # Only local fixed validation errors are included; never exception reprs.
        if type(error) is RuntimeError:
            result['error_code'] = str(error)
    finally:
        failed.set()
        if body:
            body.release()
        for thread in threads:
            thread.join(5)
        result.update(model_calls=model.calls, cost_usd=ledger.total() - total_before, duration_s=time.monotonic() - started,
                      owner_unchanged=sha(OWNER) == owner_hash, source_unchanged=manifest() == frozen,
                      threads_finished=not any(t.is_alive() for t in threads))
        result['mechanical_passed'] = (result['mechanical_passed'] and result['owner_unchanged'] and result['source_unchanged']
                                       and result['threads_finished'] and result['duration_s'] < 180 and model.calls <= 24)
        audit.write('result.jsonl', result)
        (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'cases'}, ensure_ascii=False))
    return 0 if result['mechanical_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
