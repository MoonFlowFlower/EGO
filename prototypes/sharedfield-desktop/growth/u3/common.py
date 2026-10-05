"""Immutable claims, source pins and read-only budget inspection."""
from datetime import datetime, timezone
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo
from companion.budget import DAILY_LIMIT, OWNER_ZONE

from growthlab.records import ROOT
from p7.proxy import DEFAULT_BUDGET
from u2.client import Stop, append

BASE = ROOT / 'runs/u3'
OUT = ROOT / 'evidence/u3'


def read(path):
    return json.loads(Path(path).read_bytes())


def write(path, value, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def budget_snapshot(path=DEFAULT_BUDGET, *, now=None):
    day = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo(OWNER_ZONE)).date().isoformat()
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        used, unknown = db.execute('''SELECT COALESCE(SUM(c.usd),0),
            COALESCE(SUM(CASE WHEN c.status='reserved_unknown' THEN c.usd ELSE 0 END),0)
            FROM charges c JOIN charge_days d ON c.id=d.id WHERE d.local_day=?''', (day,)).fetchone()
    return {'local_day': day, 'timezone': OWNER_ZONE, 'limit_usd': DAILY_LIMIT,
            'used_usd': used, 'unknown_included_usd': unknown, 'remaining_usd': max(0, DAILY_LIMIT-used)}


def pins():
    files = [p for p in (ROOT / 'u3').rglob('*') if p.suffix in ('.py', '.json', '.md')]
    for name in ('companion/memory.py', 'companion/understanding.py', 'companion/model.py',
                 'companion/budget.py', 'companion/compact.py', 'growthlab/state.py',
                 'growthlab/models.py', 'growthlab/records.py', 'u1/conventions/core.py',
                 'u1_resume/library.py', 'u1_resume/client.py', 'u1/harness.py', 'u1/protocol.py', 'u2/client.py', 'u2/protocol.py',
                 'u2/study.py', 'p7/proxy.py', 'p7/routing.py', 'p7/routing_v2.py',
                 'p7/routing_v1.json', 'p7/routing_v2.json'):
        files.append(ROOT / name)
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(set(files))}


def verify(manifest):
    for name, digest in manifest['source_sha256'].items():
        if sha(ROOT / name) != digest:
            raise Stop('frozen_source_changed:' + name)
    for name, digest in manifest.get('evidence_sha256', {}).items():
        if sha(ROOT / name) != digest:
            raise Stop('frozen_evidence_changed:' + name)


def cost(index=BASE / 'charge_ids.jsonl', ledger=DEFAULT_BUDGET):
    ids = {json.loads(s)['id'] for s in Path(index).read_text(encoding='utf-8').splitlines()} if Path(index).exists() else set()
    with closing(sqlite3.connect(Path(ledger).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        return sum(usd for identity, usd in db.execute('SELECT id,usd FROM charges') if identity in ids)
