"""Frozen G1/C1 revision. Preserves v2's run/claim and uses no Minecraft client."""
import argparse
import hashlib
import json
import sqlite3
import threading
import time
from datetime import datetime, timezone

from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .harness import Harness
from .model import Model
from .verification_body import SceneBody
from .verify_turn_v2 import ROOT, OWNER, SNAPSHOTS, ReadOnlyBody, logical_state, sha, manifest as source_manifest

EVIDENCE = ROOT / 'evidence/kernel_turn_v3'
FREEZE = EVIDENCE / 'FREEZE.json'


def manifest():
    return {**source_manifest(), 'evidence/kernel_turn_v3/CHECKLIST.md': sha(EVIDENCE / 'CHECKLIST.md')}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    if args.freeze:
        with FREEZE.open('x', encoding='utf-8') as f:
            json.dump({'base_commit': 'fb4a728a', 'created_utc': datetime.now(timezone.utc).isoformat(),
                       'sha256': manifest()}, f, indent=2)
            f.write('\n')
        print(json.dumps({'frozen_files': len(manifest())}))
        return 0
    frozen = json.loads(FREEZE.read_text())['sha256']
    if manifest() != frozen:
        raise RuntimeError('frozen_source_changed')
    base = ROOT / 'runs/kernel_turn_v3'
    base.mkdir(parents=True, exist_ok=True)
    with (base / 'attempt.claim').open('x', encoding='utf-8') as f:
        f.write(str(time.time_ns()))
    folder = base / str(time.time_ns()); folder.mkdir()
    (folder / 'manifest.json').write_text(json.dumps(frozen, indent=2), encoding='utf-8')
    owner_before = sha(OWNER)
    path = folder / 'greeting.sqlite'
    with sqlite3.connect('file:' + OWNER.as_posix() + '?mode=ro', uri=True) as source:
        with sqlite3.connect(path) as target:
            source.backup(target)
    state = next(json.loads(line)['state'] for line in reversed(SNAPSHOTS.read_text(encoding='utf-8').splitlines())
                 if not json.loads(line)['state'].get('offline'))
    key = read_key()
    audit = AuditLog(folder, (key,))
    ledger = BudgetLedger(DEFAULT_BUDGET, 5); total_before = ledger.total()
    batch = json.loads((ROOT / 'runs/kernel_v1/batch_budget.json').read_bytes())
    limit = min(batch['limit'], total_before + .10)
    transport = RoutedTransportV2(api_key=key, mode='pinned', route_index=0,
        budget_path=DEFAULT_BUDGET, limit=limit, log_dir=folder)
    transport.set_audit(audit)
    started, failed = time.monotonic(), threading.Event()

    class RecordedModel(Model):
        def decide(self, prompt, context):
            if failed.is_set() or self.calls >= 16 or time.monotonic() - started >= 120:
                raise RuntimeError('acceptance_limit_or_previous_failure')
            try:
                value = super().decide(prompt, context)
            except Exception:
                failed.set()
                raise
            audit.write('decisions.jsonl', {'call': self.calls, 'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                                           'context': context, 'result': value})
            return value

    model, body, threads, engine = RecordedModel(transport, audit), None, [], None
    result = {'run': folder.name, 'world_connection': False, 'body': 'deterministic_scene',
              'semantic_review': 'pending', 'mechanical_passed': False, 'cases': [], 'budget_start': total_before, 'budget_limit': limit}
    def lifecycle():
        return [json.loads(line) for line in (folder / 'lifecycle.jsonl').read_text(encoding='utf-8').splitlines()]
    try:
        audit.write('preflight.jsonl', transport.preflight())
        readonly = ReadOnlyBody(state)
        before = logical_state(path)
        engine = Harness(path, model, readonly, audit)
        reply = engine.run('greeting', 'verification', '(｡･∀･)ﾉﾞ嗨')
        mode = next((r['mode'] for r in lifecycle() if r.get('event') == 'input_routed' and r['event_id'] == 'greeting'), None)
        g1 = {'case': 'G1', 'reply': reply, 'mode': mode, 'goal_and_cards_unchanged': logical_state(path) == before,
              'action_attempts': len(readonly.actions)}
        g1['mechanical_passed'] = mode == 'chat' and g1['goal_and_cards_unchanged'] and not readonly.actions
        result['cases'].append(g1)
        if not g1['mechanical_passed'] or any(r['event'] == 'turn_failed' for r in lifecycle()):
            raise RuntimeError('greeting_mechanism_failed')

        body = SceneBody(); db = folder / 'continuation.sqlite'
        engine = Harness(db, model, body, audit, max_decisions=12, max_seconds=90)
        outputs = {}
        def run(identity, channel, text):
            outputs[identity] = engine.run(identity, channel, text)
        task = threading.Thread(target=run, args=('task', 'minecraft',
            '请用背包现有木板，在附近空位放置两块橡木板，不需要造房子。'), daemon=True)
        threads.append(task); task.start()
        if not body.first_placement.wait(30):
            raise RuntimeError('first_placement_not_reached')
        original = logical_state(db)['goal']['work']
        chat = threading.Thread(target=run, args=('chat', 'airi', '辛苦啦，现在进展怎么样？'), daemon=True)
        threads.append(chat); chat.start()
        until = time.monotonic() + 5
        while not engine._waiting and time.monotonic() < until:
            time.sleep(.01)
        if engine._waiting != 1:
            raise RuntimeError('chat_not_queued')
        body.release()
        for t in threads:
            t.join(max(0, min(60, 120 - (time.monotonic() - started))))
        if any(t.is_alive() for t in threads):
            raise RuntimeError('continuation_timeout')
        final = logical_state(db)['goal']['work']
        actions = [json.loads(line) for line in (folder / 'actions.jsonl').read_text().splitlines()]
        chat_actions = [a for a in actions if a['event_id'] == 'chat']
        c1 = {'case': 'C1', 'replies': outputs, 'same_task_id': original['task_id'] == final['task_id'],
              'same_source_id': original['source_id'] == final['source_id'], 'same_done_when': original['done_when'] == final['done_when'],
              'status': final['status'], 'distinct_placements': len(body.blocks), 'inventory_net_loss': 2 - body.state['inventory']['oak_planks'],
              'chat_actions': len(chat_actions), 'world_readback': bool(final.get('completion') and final['completion']['world_verified']),
              'resumed': any(r['event'] == 'task_resumed_after_conversation' for r in lifecycle()),
              'actions': [a['name'] for a in body.actions]}
        c1['mechanical_passed'] = (c1['same_task_id'] and c1['same_source_id'] and c1['same_done_when'] and c1['status'] == 'completed'
            and c1['distinct_placements'] == 2 and c1['inventory_net_loss'] == 2 and not chat_actions and c1['world_readback'] and c1['resumed'])
        result['cases'].append(c1)
        result['mechanical_passed'] = all(c['mechanical_passed'] for c in result['cases']) and not failed.is_set()
    except Exception as error:
        failed.set(); result['error_type'] = type(error).__name__
        if type(error) is RuntimeError:
            result['error_code'] = str(error)
    finally:
        failed.set()
        if any(t.is_alive() for t in threads) and engine:
            engine.stop()
        if body:
            body.release()
        for t in threads:
            t.join(5)
        result.update(model_calls=model.calls, cost_usd=ledger.total() - total_before, duration_s=time.monotonic() - started,
                      owner_unchanged=sha(OWNER) == owner_before, source_unchanged=manifest() == frozen,
                      threads_finished=not any(t.is_alive() for t in threads))
        result['mechanical_passed'] = (result['mechanical_passed'] and result['owner_unchanged'] and result['source_unchanged']
                                       and result['threads_finished'] and result['duration_s'] < 120 and model.calls <= 16)
        audit.write('result.jsonl', result)
        (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'cases'}, ensure_ascii=False))
    return 0 if result['mechanical_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
