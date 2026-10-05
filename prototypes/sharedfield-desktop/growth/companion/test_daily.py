"""D14 engineering acceptance, offline except local loopback tests."""
import concurrent.futures
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
import sqlite3
import tempfile
import unittest
import os
import time
import hashlib
import subprocess
import sys

from companion.budget import DailyLedger
from companion.tokens import persistent_token
from companion.supervisor import RestartWindow, Supervisor
from p7.proxy import ProxyError


def crash_then_restore(connection, options):
    """Real child process crash after a simulated effect, with canonical recovery."""
    from companion.harness import Harness
    from companion.memory import Memory
    from companion.test_kernel import Audit, Body, Model
    path = Path(options['path'])
    body, model = Body(), Model()
    engine = Harness(path,model,body,Audit())
    with Memory(path) as memory:
        source, cached = memory.begin('one-effect','minecraft','一次离线效果')
        if source:
            body.start_action({'name':'recover_inventory','args':{}}).result()
            path.with_suffix('.effect').write_text(str(len(body.actions)),encoding='utf-8')
            memory.append('experience',{'type':'action_receipt','text':'效果已经发生'},[source])
            os._exit(17)
    result = engine.run('one-effect','minecraft','一次离线效果')
    connection.send({'event':'status','text':f'restored:{len(body.actions)}:{model.calls}:{result}'})
    while connection.recv() != 'close': pass
    connection.close()


class DailyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'budget.sqlite'
        self.now = [datetime(2026, 10, 5, 4, 59, tzinfo=timezone.utc)]

    def ledger(self):
        return DailyLedger(self.path, clock=lambda: self.now[0])

    def test_midnight_and_late_settlement_keep_original_day(self):
        ledger = self.ledger()
        first = ledger.reserve(3.8)
        self.assertAlmostEqual(ledger.total(), 3.8)
        self.now[0] = datetime(2026, 10, 5, 5, 0, tzinfo=timezone.utc)
        self.assertEqual(ledger.total(), 0)
        ledger.reserve(3.7)
        ledger.settle(first, {'cost': 3.6})
        self.assertAlmostEqual(ledger.total(), 3.7)
        with self.assertRaises(ProxyError):
            ledger.reserve(.31)

    def test_unknown_reservation_survives_restart_and_atomic_cap(self):
        ledger = self.ledger()
        ledger.reserve(3.6)
        self.assertAlmostEqual(self.ledger().total(), 3.6)
        def reserve(_):
            try:
                self.ledger().reserve(.3)
                return True
            except ProxyError:
                return False
        with concurrent.futures.ThreadPoolExecutor(4) as pool:
            self.assertEqual(sum(pool.map(reserve, range(4))), 1)
        self.assertAlmostEqual(ledger.total(), 3.9)

    def test_companion_and_experiment_share_four_dollars_including_unknown(self):
        companion, experiment = self.ledger(), self.ledger()
        self.assertEqual(companion.limit, 4)
        paid = companion.reserve(3.6)
        companion.settle(paid, {'cost': 3.5})
        experiment.reserve(.25)  # Unknown hold survives a separate caller.
        snapshot = self.ledger().snapshot()
        self.assertEqual(snapshot['limit_usd'], 4)
        self.assertAlmostEqual(snapshot['used_usd'], 3.75)
        self.assertAlmostEqual(snapshot['remaining_usd'], .25)
        with self.assertRaisesRegex(ProxyError, 'daily_budget_stop'):
            companion.reserve(.26)
        self.assertAlmostEqual(experiment.total(), 3.75)

    def test_legacy_ledger_is_retained_as_history(self):
        with sqlite3.connect(self.path) as db:
            db.execute('CREATE TABLE charges(id TEXT PRIMARY KEY, usd REAL, status TEXT)')
            db.execute("INSERT INTO charges VALUES ('old',5,'reserved_unknown')")
        db.close()
        ledger = self.ledger()
        self.assertEqual(ledger.total(), 0)
        self.assertEqual(ledger.history()['usd'], 5)
        self.assertEqual(ledger.history()['unknown_usd'], 5)
        ledger.reserve(.5)

    def test_dst_midnight_uses_owner_timezone(self):
        ledger = self.ledger()
        midnight = datetime(2026, 11, 2, tzinfo=ZoneInfo('America/Winnipeg')).astimezone(timezone.utc)
        self.now[0] = midnight - timedelta(seconds=1)
        ledger.reserve(3.9)
        self.now[0] = midnight
        self.assertEqual(ledger.total(), 0)

    def test_dpapi_token_survives_restart_ciphertext_has_no_token(self):
        path = Path(self.tmp.name) / 'token.dpapi'
        token = persistent_token(path)
        self.assertEqual(persistent_token(path), token)
        self.assertNotIn(token.encode(), path.read_bytes())
        replacement = persistent_token(path, rotate=True)
        self.assertNotEqual(replacement, token)
        self.assertEqual(persistent_token(path), replacement)

    def test_rolling_hour_restart_cap(self):
        window = RestartWindow()
        self.assertTrue(window.allow(0))
        self.assertTrue(window.allow(100))
        self.assertTrue(window.allow(200))
        self.assertFalse(window.allow(3599))
        self.assertTrue(window.allow(3600))

    def test_real_crash_auto_restore_has_no_replayed_actions(self):
        supervisor = Supervisor({'path':str(Path(self.tmp.name)/'owner.sqlite')},target=crash_then_restore)
        self.addCleanup(supervisor.close)
        supervisor.start()
        end = time.monotonic()+12
        while time.monotonic()<end and not supervisor.status.startswith('restored:'):
            supervisor.tick(); time.sleep(.05)
        self.assertTrue(supervisor.status.startswith('restored:0:0:'),supervisor.status)
        self.assertEqual(len(supervisor.window.restarts),1)
        self.assertEqual((Path(self.tmp.name)/'owner.effect').read_text(encoding='utf-8'),'1')

    def test_absent_owner_requires_current_grant_and_autonomy_sends_no_chat(self):
        from companion.runtime import Runtime
        from companion.harness import Harness
        from companion.test_harness import Body, Model
        from companion.test_kernel import Audit
        from companion.test_initiative import grant, proposal, route, TEXT
        runtime=Runtime.__new__(Runtime)
        runtime.path=Path(self.tmp.name)/'absence.sqlite'
        runtime.body=Body();observed=runtime.body.snapshot
        present=[False]
        runtime.body.snapshot=lambda:{**observed(),'owner':{'distance':2} if present[0] else None}
        runtime.engine=Harness(runtime.path,Model(grant,proposal),runtime.body,Audit(),input_router=route)
        runtime.engine.action_policy=runtime.owner_authorized
        self.assertFalse(runtime.owner_authorized(None))
        runtime.engine.run('delegate','airi',TEXT)
        self.assertTrue(runtime.owner_authorized(None))
        before=list(runtime.body.speech)
        self.assertTrue(runtime.engine.initiative.drain_one())
        self.assertEqual(runtime.body.speech,before)
        self.assertTrue(runtime.body.actions)
        runtime.engine.stop()
        self.assertFalse(runtime.owner_authorized(None))
        present[0]=True
        self.assertTrue(runtime.owner_authorized(None))

    def test_token_read_in_fresh_process(self):
        path = Path(self.tmp.name)/'fresh.dpapi'
        token = persistent_token(path)
        command = 'import hashlib,sys;from companion.tokens import persistent_token;print(hashlib.sha256(persistent_token(sys.argv[1]).encode()).hexdigest())'
        result = subprocess.check_output([sys.executable,'-c',command,str(path)],text=True).strip()
        self.assertEqual(result,hashlib.sha256(token.encode()).hexdigest())

    def test_exhausted_budget_stops_model_and_says_one_sentence(self):
        from companion.harness import Harness
        from companion.test_kernel import Audit, Body
        from companion.budget import BUDGET_MESSAGE
        ledger=self.ledger(); ledger.reserve(4)
        class Model:
            calls=0
            def decide(inner,*args):
                ledger.reserve(.05)
                inner.calls+=1
        model,body=Model(),Body()
        engine=Harness(Path(self.tmp.name)/'message.sqlite',model,body,Audit())
        reply=engine.run('budget','airi','聊一句')
        self.assertEqual(reply,BUDGET_MESSAGE)
        self.assertEqual(model.calls,0)
        self.assertEqual(body.speech,[BUDGET_MESSAGE])


if __name__ == '__main__':
    unittest.main()
