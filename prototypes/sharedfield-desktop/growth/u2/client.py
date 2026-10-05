"""Frozen U2 pacing/stops over the production model entry and daily ledger."""
import json
import os
import random
import time
import urllib.error
from pathlib import Path

from companion.budget import DailyLedger
from companion.model import Model, DecisionError
from growthlab.models import read_key
from growthlab.records import ROOT, telemetry
from p7.proxy import AuditLog, DEFAULT_BUDGET, ProxyError, prepare_request
from p7.routing_v2 import RoutedTransportV2
from u1_resume.client import retry_delay, TransportError
from .protocol import MODEL, ROUTE, ESTIMATE_USD


class Stop(RuntimeError):
    pass


def append(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')


class Client:
    def __init__(self,folder, *, total_cap=ESTIMATE_USD):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
        self.started=time.monotonic();self.next_start=0;self.sampled=0
        self.total_cap=total_cap
        self.invalid_streak=0
        key=read_key()
        self.audit=AuditLog(self.folder,(key,))
        self.transport=RoutedTransportV2(api_key=key,mode='pinned',route_index=0,
            budget_path=DEFAULT_BUDGET,limit=1,log_dir=self.folder)
        self.transport.timeout=60  # U1 resume's frozen per-attempt deadline.
        self.transport.ledger=DailyLedger(DEFAULT_BUDGET)
        self.transport.set_audit(self.audit)
        if (self.transport.model,self.transport.route)!=(MODEL,ROUTE):
            raise Stop('model_route_changed')
        self.model=Model(self.transport,self.audit)

    def log(self,event,**fields):
        self.audit.write('calls.jsonl',{'event':event,'unix_s':time.time(),'pid':os.getpid(),**fields})

    def cost(self):
        path=ROOT/'runs/u2/charge_ids.jsonl'
        ids={json.loads(s)['id'] for s in path.read_text(encoding='utf-8').splitlines()} if path.exists() else set()
        with self.transport.ledger._connect() as db:
            return sum(usd for identity,usd in db.execute('SELECT id,usd FROM charges') if identity in ids)

    def check(self):
        if (ROOT/'runs/u2/STOP').exists(): raise Stop('operator_stop')
        if time.monotonic()-self.started>=3600: raise Stop('lane_wall_limit')
        if self.cost()>self.total_cap: raise Stop('actual_exceeded_estimate')
        if time.monotonic()-self.sampled>=30:
            info=telemetry();self.sampled=time.monotonic()
            self.log('telemetry',**info)
            if info['ac_online'] is not True: raise Stop('ac_required')

    def wait(self,target):
        while time.monotonic()<target:
            self.check();time.sleep(min(.5,target-time.monotonic()))

    def call(self,messages,context, *, reasoning=False,schema=None,organize=False):
        request={'model':MODEL,'stream':False,'temperature':0,
                 'max_tokens':8192 if reasoning else 1024,
                 'reasoning':{'enabled':True,'effort':'low','exclude':True} if reasoning else {'enabled':False},
                 'response_format':schema or {'type':'json_object'},'messages':messages}
        # Full memory is admitted or stopped; no retrieval/truncation fallback.
        _,_,reserve=prepare_request(request,model=MODEL,provider=self.transport.policy['provider'])
        for attempt in (1,2):
            self.wait(self.next_start);self.check()
            if self.cost()+reserve>self.total_cap: raise Stop('estimate_reservation_stop')
            self.next_start=time.monotonic()+2
            def observe(event,value):
                self.log(event,context=context,attempt=attempt,**value)
            before=set()
            with self.transport.ledger._connect() as db:
                before={r[0] for r in db.execute('SELECT id FROM charges')}
            try:
                output,meta=self.model.complete(request,observer=observe,allow_invalid=True)
            except (ProxyError,DecisionError,ValueError,TimeoutError,ConnectionError,urllib.error.URLError) as error:
                code=getattr(error,'code',type(error).__name__)
                self.log('failure',context=context,attempt=attempt,error=code)
                retryable=code in {'upstream_http_429','upstream_http_502','upstream_http_503','upstream_http_504',
                                  'upstream_connection_error','TimeoutError','ConnectionError','URLError'}
                if not retryable or attempt==2: raise Stop(code) from None
                after=0
                routing=self.folder/'routing.jsonl'
                if routing.exists():
                    for line in reversed(routing.read_text(encoding='utf-8').splitlines()):
                        row=json.loads(line)
                        if row.get('outcome') in ('http_error','connection_error'):
                            after=row.get('retry_after_s',0);break
                delay=retry_delay(TransportError(code,after),random.SystemRandom().uniform(0,3))
                self.log('retry_wait',context=context,delay_s=delay,same_input=True)
                self.wait(time.monotonic()+delay)
                continue
            finally:
                with self.transport.ledger._connect() as db:
                    new=[r[0] for r in db.execute('SELECT id FROM charges') if r[0] not in before]
                # Only the shared model lock may create one U2 charge during
                # this call; attribution is taken from our routing audit below.
                routing=self.folder/'routing.jsonl'
                owned={json.loads(s).get('charge_id') for s in routing.read_text(encoding='utf-8').splitlines()} if routing.exists() else set()
                for identity in new:
                    if identity in owned: append(ROOT/'runs/u2/charge_ids.jsonl',{'id':identity})
            if self.cost()>self.total_cap: raise Stop('actual_exceeded_estimate')
            return output,meta

    def parsed(self,valid):
        self.invalid_streak=0 if valid else self.invalid_streak+1
        if self.invalid_streak>=2: raise Stop('two_consecutive_invalid_outputs')
