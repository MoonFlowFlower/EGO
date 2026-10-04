"""One bounded engineering replay; two placements, no cloud/model calls."""
import argparse
import json
import socket
import time

from p7.proxy import AuditLog
from .body import Body, ROOT
from .engine import Engine
from .memory import Memory


class RecordedPlacementDecisions:
    calls = 0

    def decide(self, _prompt, context):
        self.calls += 1
        base = {'reply': '', 'goal': None, 'convention': None, 'forget_card': None, 'action': None}
        if context.get('execution_blocked'):
            return {**base, 'reply': '工程检查没有得到成功确认，已经暂停。'}
        if len(context['receipts']) < 2:
            return {**base, 'action': {'name': 'place', 'args': {'block': 'oak_planks'}}}
        return {**base, 'reply': '工程检查：连续两次放置已得到回执，检查结束。'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--previous-session', required=True)
    args = parser.parse_args()
    if not args.previous_session.isdigit():
        raise ValueError('invalid_session')
    previous = ROOT / 'runs/kernel_v1/sessions' / args.previous_session / 'lifecycle.jsonl'
    events = [json.loads(line) for line in previous.read_text(encoding='utf-8').splitlines()]
    if not any(row['event'] == 'supervisor_closed' for row in events):
        raise RuntimeError('previous_supervisor_still_open')
    try:
        with socket.create_connection(('127.0.0.1', 18787), timeout=.5):
            raise RuntimeError('formal_kernel_still_listening')
    except (ConnectionRefusedError, TimeoutError):
        pass
    folder = ROOT / 'runs/kernel_repeat_v1/acceptance' / str(time.time_ns())
    folder.mkdir(parents=True)
    audit = AuditLog(folder, ())
    body = Body(audit)
    outcome = {'cloud_model_calls': 0, 'max_placements': 2, 'passed': False}
    try:
        body.start()
        deadline = time.monotonic() + 30
        while body.snapshot().get('offline') and time.monotonic() < deadline:
            time.sleep(.2)
        before = body.snapshot()
        if before.get('offline') or before.get('inventory', {}).get('oak_planks', 0) < 2:
            raise RuntimeError('body_or_material_unavailable')
        model = RecordedPlacementDecisions()
        engine = Engine(folder / 'state.sqlite', model, body, audit)
        engine.run('verification:repeated-placement', 'verification', '工程检查：按已记录动作序列连续放置两块现有橡木板，然后停止。')
        memory = Memory(engine.path)
        try:
            receipts = [row['receipt'] for row in memory.recent_actions()]
        finally:
            memory.close()
        positions = [tuple(r['position'][k] for k in ('x', 'y', 'z')) for r in receipts if r.get('verified')]
        after = receipts[-1].get('observed', {}) if receipts else {}
        consumed = before['inventory']['oak_planks'] - after.get('inventory', {}).get('oak_planks', 0)
        outcome.update(before=before, after=after, receipts=receipts, inventory_consumed=consumed,
                       distinct_positions=len(set(positions)), replay_decisions=model.calls,
                       passed=len(receipts) == 2 and len(set(positions)) == 2 and consumed == 2
                       and all(r.get('verified') and r.get('placement', {}).get('consumed') == 1 for r in receipts))
    except Exception as error:
        outcome['error_type'] = type(error).__name__
    finally:
        body.close('engineering_check_complete')
        outcome['body_exit_code'] = body.process.poll() if body.process else None
        (folder / 'result.json').write_bytes((json.dumps(outcome, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'folder': str(folder), **{k: v for k, v in outcome.items() if k not in ('before', 'after', 'receipts')}}, ensure_ascii=False))
    return 0 if outcome['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
