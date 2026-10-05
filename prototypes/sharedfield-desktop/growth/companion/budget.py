"""One shared daily ledger, retaining every historical charge and unknown hold."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import uuid
from contextlib import contextmanager
import os
import time

from p7.proxy import BudgetLedger, ProxyError, DEFAULT_BUDGET, _finite_number

OWNER_ZONE = 'America/Winnipeg'
DAILY_LIMIT = 4.0
BUDGET_MESSAGE = '今天的模型额度用完了，模型调用已暂停。'


class DailyLedger(BudgetLedger):
    def __init__(self, path=DEFAULT_BUDGET, *, clock=None):
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.zone = ZoneInfo(OWNER_ZONE)
        super().__init__(path, DAILY_LIMIT)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS charge_days(id TEXT PRIMARY KEY, local_day TEXT NOT NULL, created_utc TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS budget_history(id TEXT PRIMARY KEY, usd REAL NOT NULL, status TEXT NOT NULL)')
            # Existing charges have no timestamps. Keep an explicit historical
            # snapshot, not a fabricated date; reconcile dated logs before U2.
            db.execute("INSERT OR IGNORE INTO budget_history SELECT id,usd,status FROM charges WHERE id NOT IN (SELECT id FROM charge_days)")

    def day(self):
        return self.clock().astimezone(self.zone).date().isoformat()

    def total(self):
        with self._connect() as db:
            return db.execute('SELECT COALESCE(SUM(c.usd),0) FROM charges c JOIN charge_days d ON c.id=d.id WHERE d.local_day=?', (self.day(),)).fetchone()[0]

    def history(self):
        with self._connect() as db:
            n, usd, unknown = db.execute("SELECT COUNT(*),COALESCE(SUM(usd),0),COALESCE(SUM(CASE WHEN status='reserved_unknown' THEN usd ELSE 0 END),0) FROM budget_history").fetchone()
        return {'count':n,'usd':usd,'unknown_usd':unknown}

    def snapshot(self):
        used = self.total()
        return {'local_day':self.day(),'timezone':OWNER_ZONE,'limit_usd':DAILY_LIMIT,
                'used_usd':used,'remaining_usd':max(0,DAILY_LIMIT-used)}

    def reserve(self, amount):
        if not _finite_number(amount) or amount <= 0:
            raise ValueError('invalid_reservation')
        identity = uuid.uuid4().hex
        now = self.clock()
        day = now.astimezone(self.zone).date().isoformat()
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            used = db.execute('SELECT COALESCE(SUM(c.usd),0) FROM charges c JOIN charge_days d ON c.id=d.id WHERE d.local_day=?',(day,)).fetchone()[0]
            if used + amount > DAILY_LIMIT:
                raise ProxyError('daily_budget_stop',402)
            db.execute('INSERT INTO charges VALUES (?,?,?)',(identity,amount,'reserved_unknown'))
            db.execute('INSERT INTO charge_days VALUES (?,?,?)',(identity,day,now.astimezone(timezone.utc).isoformat()))
        return identity

    def reconcile(self, timestamps):
        """Import dates proven by retained request logs, without changing costs."""
        with self._connect() as db:
            for identity, timestamp in timestamps.items():
                if not db.execute('SELECT 1 FROM charges WHERE id=?',(identity,)).fetchone():
                    continue
                instant = datetime.fromtimestamp(timestamp,timezone.utc)
                db.execute('INSERT OR IGNORE INTO charge_days VALUES (?,?,?)',
                    (identity,instant.astimezone(self.zone).date().isoformat(),instant.isoformat()))

    @contextmanager
    def call_lock(self):
        """One in-flight model call across companion and U2 processes."""
        import msvcrt
        path = self.path.with_suffix('.model-call.lock')
        with path.open('a+b') as stream:
            if stream.tell() == 0:
                stream.write(b'0'); stream.flush()
            started = time.monotonic()
            while True:
                stream.seek(0)
                try:
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                    break
                except OSError:
                    if time.monotonic()-started > 180:
                        raise ProxyError('model_call_lock_timeout',503)
                    time.sleep(.1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
