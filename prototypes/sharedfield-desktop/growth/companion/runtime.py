"""Independent, deadline-owning supervisor. Secrets are never passed in argv."""
import json
import math
import os
from pathlib import Path
import threading
import time
import uuid

from growthlab.models import read_key
from p7.proxy import AuditLog, BudgetLedger, DEFAULT_BUDGET
from p7.routing_v2 import RoutedTransportV2
from .airi import AiriBridge
from .body import Body, ROOT
from .engine import STOP
from .harness import Harness
from .model import Model
from .memory import Memory
from .server import KernelServer
from .reconnect import ReconnectSchedule


def batch_limit(budget):
    values = [budget[key] for key in ('start_total', 'extra_cap', 'limit')]
    if any(type(value) not in (int, float) or not math.isfinite(value) or value < 0 for value in values):
        raise ValueError('invalid_batch_budget')
    start, extra, limit = values
    return min(5, start + extra, limit)


class Runtime:
    def __init__(self,*,acceptance=False,minutes=30,acceptance_case='kernel-v1',local_token=None):
        if not 1<=minutes<=30:raise ValueError('session_deadline')
        if acceptance_case not in ('kernel-v1','search-v1.3'):raise ValueError('acceptance_case')
        self.folder=ROOT/'runs/kernel_v1/sessions'/str(time.time_ns())
        self.folder.mkdir(parents=True)
        self.path=ROOT/('runs/kernel_v1/acceptance/state.sqlite' if acceptance else 'runs/kernel_v1/owner/state.sqlite')
        if acceptance and acceptance_case=='search-v1.3':
            self.path=ROOT/'runs/kernel_v1_3/acceptance/state.sqlite'
        self.deadline=time.monotonic()+minutes*60
        self._closed=threading.Event()
        self._close_lock=threading.Lock()
        self._body_lock=threading.RLock()
        self._reconnect=ReconnectSchedule()
        self._reconnect_notice=False
        self._inputs=threading.BoundedSemaphore(8)
        self.body=self.engine=self.server=self.bridge=None
        key=read_key()
        self.audit=AuditLog(self.folder,(key,))
        self.audit.write('lifecycle.jsonl',{'event':'supervisor_start','pid':os.getpid(),
            'unix_s':time.time(),'stop_unix_s':time.time()+minutes*60,'acceptance':acceptance,
            'acceptance_case':acceptance_case if acceptance else None})
        try:
            ledger=BudgetLedger(DEFAULT_BUDGET,5)
            budget_file=ROOT/'runs/kernel_v1/batch_budget.json'
            try:
                with budget_file.open('x',encoding='utf-8') as f:
                    json.dump({'start_total':ledger.total(),'extra_cap':.50,'limit':min(5,ledger.total()+.50)},f)
            except FileExistsError:pass
            budget=json.loads(budget_file.read_bytes())
            limit=batch_limit(budget)
            self.transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,
                budget_path=DEFAULT_BUDGET,limit=limit,log_dir=self.folder)
            self.transport.set_audit(self.audit)
            self.audit.write('preflight.jsonl',{'route':self.transport.preflight(),'budget_start':ledger.total(),'batch_limit':limit})
            self.body=Body(self.audit,self.on_minecraft)
            self.engine=Harness(self.path,Model(self.transport,self.audit),self.body,self.audit)
            self.server=KernelServer(self.engine,self.audit,local_token=local_token)
            self.server.start()
            self.bridge=AiriBridge(self.audit)
            try:self.bridge.start()
            except Exception as error:self.audit.write('lifecycle.jsonl',{'event':'airi_bridge_unavailable','error_type':type(error).__name__})
            self.body.start()
            self.audit.write('lifecycle.jsonl',{'event':'supervisor_ready','pid':os.getpid(),'model':self.transport.model,'base_url':self.server.base_url})
            threading.Thread(target=self._watch,daemon=True).start()
        except Exception:
            self.close('startup_failed')
            raise

    def _watch(self):
        while not self._closed.wait(.5):
            if time.monotonic()>=self.deadline:
                self.close('session_deadline');break
            process=self.body.process
            if self._reconnect.due(time.monotonic(),exited=process is None or process.poll() is not None,deadline=self.deadline):
                try:self.reconnect_body(automatic=True)
                except Exception as error:self.audit.write('lifecycle.jsonl',{'event':'body_reconnect_failed','error_type':type(error).__name__})
            if self._reconnect_notice and not self.body.snapshot().get('offline'):
                self._reconnect_notice=False
                self.body.say('我重新连上了。刚才的任务和回执保留着；没有重放动作。你明确说继续后，我会先重新观察。')
                self.audit.write('lifecycle.jsonl',{'event':'body_reconnected','replayed_actions':0})

    def on_minecraft(self,text,input_state=None):
        if self._closed.is_set():return
        urgent=bool(STOP.fullmatch(text.strip()))
        if not urgent and not self._inputs.acquire(blocking=False):
            self.body.say('输入队列已满，请等这一轮结束。');return
        try:
            identity='mc:'+uuid.uuid4().hex
            self.engine.run(identity,'minecraft',text,input_state=input_state)
            if not self._closed.is_set():
                rendered=self.server.mirror(identity,text)
                self.bridge.publish(identity,rendered)
        finally:
            if not urgent:self._inputs.release()

    def reconnect_body(self,*,automatic=False):
        with self._body_lock:
            if self._closed.is_set() or time.monotonic()>=self.deadline:return
            if self.body.process and self.body.process.poll() is None:return
            self.engine.invalidate('body_reconnect')
            self.body.close('bounded_reconnect' if automatic else 'operator_reconnect')
            if self._closed.is_set() or time.monotonic()>=self.deadline:return
            self.body=Body(self.audit,self.on_minecraft)
            self.engine.body=self.body
            self.body.start()
            self._reconnect_notice=True
            self.audit.write('lifecycle.jsonl',{'event':'body_reconnect_started','automatic':automatic,'attempt':self._reconnect.attempts})

    def replay_latest_mc(self):
        """Explicit display recovery. Reads a finished turn, never calls the model."""
        if self._closed.is_set():return
        memory=Memory(self.path)
        try:
            row=memory.db.execute("SELECT event_id,user_id FROM kernel_turns WHERE channel='minecraft' AND phase='done' ORDER BY rowid DESC LIMIT 1").fetchone()
            body=memory.record(row[1]) if row else None
        finally:memory.close()
        if row and body:
            self.bridge.publish(row[0],self.server.mirror(row[0],body['utterance_text']))
            self.audit.write('lifecycle.jsonl',{'event':'operator_replay_requested','event_id':row[0],'model_called':False})

    def status(self):
        if self._closed.is_set():return '本次运行已结束'
        state=self.body.snapshot()
        return f"MC {'未连接' if state.get('offline') else '已连接'} · AIRI {'已连接' if self.bridge.ready else '等待连接'} · 剩余 {max(0,int(self.deadline-time.monotonic()))} 秒 · 模型调用 {self.engine.model.calls} 次 · {self.engine.progress}"

    def close(self,reason='owner_closed'):
        with self._close_lock:
            if self._closed.is_set():return
            self._closed.set()
            self.audit.write('lifecycle.jsonl',{'event':'supervisor_closing','reason':reason,'unix_s':time.time()})
            if self.engine:self.engine.stop()
            if self.server:self.server.close()
            with self._body_lock:
                if self.body:self.body.close(reason)
            if self.bridge:self.bridge.close()
            self.audit.write('lifecycle.jsonl',{'event':'supervisor_closed','reason':reason,'unix_s':time.time(),
                'budget_total':self.transport.ledger.total() if hasattr(self,'transport') else None})
