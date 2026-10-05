"""One-shot, model-free reads through the production body in the existing world."""
import hashlib
import json
import socket
import sqlite3
import time
from pathlib import Path

from .body import Body, ROOT
from p7.proxy import AuditLog


def main():
    root = ROOT / 'runs/kernel_perception_v1'
    freeze = ROOT / 'evidence/kernel_perception_v1/FREEZE.json'
    pinned = json.loads(freeze.read_text(encoding='utf-8'))['files']
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in pinned.items())
    with socket.socket() as sock:
        assert sock.connect_ex(('127.0.0.1', 18787)) != 0, 'supervisor_still_running'
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'live_attempt.claim').open('x', encoding='utf-8') as f:
        f.write(str(time.time_ns()))
    folder = root / ('live_' + str(time.time_ns()))
    folder.mkdir()
    body = Body(AuditLog(folder))
    owner = ROOT / 'runs/kernel_v1/owner/state.sqlite'
    owner_hash = hashlib.sha256(owner.read_bytes()).hexdigest()
    def budget():
        with sqlite3.connect('file:' + str(ROOT / 'runs/phase1/budget.sqlite') + '?mode=ro', uri=True) as db:
            return db.execute('select status,count(*),sum(usd) from charges group by status').fetchall()
    before = budget()
    report = {'model_calls': 0, 'actions': [], 'passed': False, 'started_unix_s': time.time()}
    try:
        body.start()
        deadline = time.monotonic() + 60
        while body.snapshot().get('offline') and time.monotonic() < deadline:
            time.sleep(.25)
        report['initial_body'] = body.snapshot()
        assert not report['initial_body'].get('offline'), 'no_live_body'
        center = {'x': 12, 'y': 111, 'z': -58}
        def read(name, args):
            action = {'name': name, 'args': args}
            assert name in ('inspect_area', 'verify_blocks')
            receipt = body.start_action(action).result(timeout=8)
            report['actions'].append({'action': action, 'receipt': receipt})
            assert receipt.get('verified'), receipt.get('status')
            return receipt
        old = read('inspect_area', {'radius': 4, 'center': center, 'below': 1, 'above': 2})
        new = read('inspect_area', {'radius': 4, 'center': center})
        old_cells = {tuple(c[:3]): c[3] for c in old['cells']}
        new_cells = {tuple(c[:3]): c[3] for c in new['cells']}
        assert all(new_cells[p] == name for p, name in old_cells.items()), 'world_changed_between_reads'
        ground = [(p, n) for p, n in new_cells.items() if p[1] == 108 and n in ('grass_block', 'dirt', 'stone')]
        assert ground and all(p not in old_cells for p, _ in ground), 'counterexample_not_present'
        targets = [{'block': n, 'position': dict(zip(('x', 'y', 'z'), p))} for p, n in ground[:4]]
        read('verify_blocks', {'targets': targets})
        report.update(passed=True, old_bounds=old['coverage']['bounds'], new_bounds=new['coverage']['bounds'],
                      newly_observed_ground_at_y108=len(ground), overlap_equal=True,
                      caveat='Current world read, not a replay of the earlier world; no model behavior or construction acceptance.')
    except Exception as error:
        report['error_type'] = type(error).__name__
        report['error'] = str(error)
    finally:
        body.close('perception_read_only_complete')
        report['budget_unchanged'] = before == budget()
        report['owner_unchanged'] = owner_hash == hashlib.sha256(owner.read_bytes()).hexdigest()
        report['source_unchanged'] = all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in pinned.items())
        report['finished_unix_s'] = time.time()
        (folder / 'RESULT.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'folder': str(folder), **{k: v for k, v in report.items() if k not in ('initial_body', 'actions')}}, ensure_ascii=False))
    return 0 if report['passed'] and report['budget_unchanged'] and report['owner_unchanged'] and report['source_unchanged'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
