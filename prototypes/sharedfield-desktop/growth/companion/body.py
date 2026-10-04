"""Own one model-free Node body in the existing Windows kill-on-close job."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import threading
import time
import uuid

from p7.body_session_v2 import Job

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = Path('D:/Project/AIProject/MyProject/Ego_proejct_restart/p7_tools/mindcraft')
NODE = r'C:\Program Files\nodejs\node.exe'


class Body:
    def __init__(self, audit, on_input=lambda text, state=None: None):
        self.audit, self.on_input = audit, on_input
        self.process, self.job = None, None
        self._state = {'offline': True}
        self._at = 0
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._pending = {}
        self.exit_reason = None

    def start(self):
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=OFFICIAL, text=True,
                                          creationflags=subprocess.CREATE_NO_WINDOW).strip()
        dirty = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=OFFICIAL, text=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW).strip()
        if revision != 'b36eaf7e61b3f6bd031fdb531812b2e3c42b6c73' or dirty:
            raise ValueError('unreviewed_official_checkout')
        env = {k:v for k,v in os.environ.items() if not any(w in k.upper() for w in ('KEY','TOKEN','SECRET','PASSWORD'))}
        self.job = Job()
        try:
            self.process = subprocess.Popen([NODE, str(Path(__file__).with_name('body.mjs'))], cwd=OFFICIAL,
                env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
            self.job.assign(self.process)
            threading.Thread(target=self._read, daemon=True).start()
            threading.Thread(target=self._stderr, daemon=True).start()
            self._send({'root':str(OFFICIAL), 'host':'127.0.0.1', 'port':25565})
        except Exception:
            self.close('startup_failed')
            raise

    def _stderr(self):
        for _ in self.process.stderr:
            self.audit.write('body_events.jsonl', {'kind':'stderr_line', 'unix_s':time.time()})

    def _read(self):
        for line in self.process.stdout:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            kind = row.get('kind')
            if kind in ('state','ready'):
                with self._lock:
                    self._state, self._at = row['state'], time.monotonic()
                # Raw state has no conversation text; remains local under runs.
                self.audit.write('body_states.jsonl', row)
            elif kind == 'receipt':
                with self._lock:
                    future = self._pending.pop(row['id'], None)
                    if isinstance(row.get('receipt', {}).get('observed'), dict):
                        self._state, self._at = row['receipt']['observed'], time.monotonic()
                if future and not future.done():
                    future.set_result(row['receipt'])
            elif kind == 'owner_input':
                # The reader must keep draining receipts while this input waits for a turn.
                threading.Thread(target=self.on_input, args=(row['text'], row.get('state')), daemon=True).start()
            else:
                if kind == 'action_deadline_exit':self.exit_reason='action_timeout'
                elif kind in ('disconnected','spawn_timeout') and not self.exit_reason:self.exit_reason=kind
                self.audit.write('body_events.jsonl', row)
        code = self.process.wait()
        with self._lock:
            self._state = {'offline':True,'reason':self.exit_reason or 'body_exit'}
            self._at = time.monotonic()
            for future in self._pending.values():
                if not future.done():future.set_result({'verified':False,'status':'body_disconnected'})
            self._pending.clear()
        self.audit.write('lifecycle.jsonl', {'event':'body_exit','unix_s':time.time(),'exit_code':code,'reason':self.exit_reason})

    def _send(self, value):
        with self._write_lock:
            if not self.process or self.process.poll() is not None:
                raise RuntimeError('body_offline')
            self.process.stdin.write(json.dumps(value, ensure_ascii=False)+'\n')
            self.process.stdin.flush()

    def snapshot(self):
        with self._lock:
            if time.monotonic()-self._at > 4:
                return {'offline':True,'reason':self.exit_reason or 'no_fresh_body_state'}
            return json.loads(json.dumps(self._state))

    def start_action(self, action, timeout=60):
        identity = uuid.uuid4().hex
        future = concurrent.futures.Future()
        with self._lock:
            self._pending[identity] = future
        try:
            self._send({'op':'action','id':identity,'action':action,'timeout':timeout})
        except Exception:
            with self._lock:self._pending.pop(identity,None)
            future.set_result({'verified':False,'status':'body_offline'})
        return future

    def stop(self):
        future = self.start_action({'name':'stop','args':{}})
        try:return future.result(timeout=3)
        except concurrent.futures.TimeoutError:
            self.close('stop_timeout')
            return {'verified':False,'status':'body_terminated_without_stop_receipt'}

    def say(self, text):
        try:self._send({'op':'say','text':text})
        except (RuntimeError,OSError):pass

    def close(self, reason='owner_closed'):
        self.audit.write('lifecycle.jsonl', {'event':'body_close_requested','reason':reason,'unix_s':time.time()})
        if self.process:
            try:
                self._send({'op':'shutdown'})
                self.process.wait(timeout=4)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):pass
        if self.job:
            self.job.close()
            self.job = None
        if self.process:
            try:self.process.wait(timeout=4)
            except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=3)
            if self.process.stdin:self.process.stdin.close()
