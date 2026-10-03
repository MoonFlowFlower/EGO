"""AIRI native input:text mirror, with an in-memory local token and bounded job."""
import json
import os
from pathlib import Path
import subprocess
import threading

from p7.body_session_v2 import Job
from .body import NODE

CONFIG = Path(os.environ['APPDATA']) / 'ai.moeru.airi/server-channel-config.json'


class AiriBridge:
    def __init__(self, audit):
        self.audit, self.ready = audit, False
        self.process, self.job = None, None
        self._lock = threading.Lock()

    def start(self):
        config = json.loads(CONFIG.read_bytes())
        if config.get('hostname') != '127.0.0.1' or config.get('tlsConfig'):
            raise ValueError('unreviewed_airi_channel_configuration')
        token = config.get('authToken')
        if not isinstance(token, str) or not token:
            raise ValueError('local_airi_token_missing')
        env = {k:v for k,v in os.environ.items() if not any(w in k.upper() for w in ('KEY','TOKEN','SECRET','PASSWORD'))}
        self.job = Job()
        try:
            self.process = subprocess.Popen([NODE,str(Path(__file__).with_name('airi_bridge.mjs'))],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                text=True,encoding='utf-8',env=env,creationflags=subprocess.CREATE_NO_WINDOW)
            self.job.assign(self.process)
            threading.Thread(target=self._read,daemon=True).start()
            self._send({'url':'ws://127.0.0.1:6121/ws','token':token})
        except Exception:
            self.close()
            raise

    def _send(self, row):
        with self._lock:
            if not self.process or self.process.poll() is not None:
                raise RuntimeError('airi_bridge_offline')
            self.process.stdin.write(json.dumps(row,ensure_ascii=False)+'\n')
            self.process.stdin.flush()

    def _read(self):
        for line in self.process.stdout:
            try:row=json.loads(line)
            except ValueError:continue
            if row.get('kind')=='bridge_ready':self.ready=True
            elif row.get('kind') in ('bridge_disconnected','bridge_connection_error'):self.ready=False
            self.audit.write('airi_events.jsonl',row)
        self.ready=False

    def publish(self, identity, text):
        try:self._send({'op':'publish','id':identity,'text':text})
        except (RuntimeError,OSError):self.audit.write('airi_events.jsonl',{'kind':'mirror_unavailable','id':identity})

    def close(self):
        self.ready=False
        if self.process:
            try:self._send({'op':'shutdown'});self.process.wait(timeout=3)
            except (OSError,RuntimeError,subprocess.TimeoutExpired):pass
        if self.job:self.job.close();self.job=None
