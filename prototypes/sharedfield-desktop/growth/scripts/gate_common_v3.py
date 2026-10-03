"""Single-concurrency transport accounting for revision-3 gates."""
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.models import Cloud
from growthlab.records import ROOT,write_json,telemetry
from growthlab.forks import file_hash

BASE=ROOT/'runs/phase1/revision3'
OUT=ROOT/'evidence/phase1/revision3'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))


def hashes(scripts=()):
    files=list((ROOT/'growthlab').glob('*.py'))+[ROOT/'scripts/gate_common_v3.py',*map(Path,scripts)]
    return {str(p.relative_to(ROOT)):file_hash(p) for p in files}


def check_hashes(expected):
    assert all(file_hash(ROOT/p)==value for p,value in expected.items()),'frozen_gate_source_changed'


class GateStop(RuntimeError):pass


class Client:
    def __init__(self,folder,status):
        self.folder,self.status=folder,status;self.context={};self.last_sample=0
        self.sample()
        self.base=Cloud(budget_path=ROOT/'runs/phase1/budget.sqlite')

    def sample(self):
        now=time.time()
        if now-self.status['started_unix']>=3600:raise GateStop('machine_time_limit')
        if now-self.last_sample>=30:
            value=telemetry();self.status['telemetry'].append(value);self.last_sample=now
            if value['ac_online'] is not True:raise GateStop('ac_required')

    def log(self,value):
        with (self.folder/'calls.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n')

    def decide(self,prompt,**kwargs):
        for attempt in (1,2):
            self.sample();self.status['current']=dict(self.context,attempt=attempt)
            write_json(self.folder/'status.json',self.status)
            before={r[0] for r in self.base.db.execute('SELECT id FROM charges')}
            self.log({'type':'request','time':time.time(),'context':self.context,'attempt':attempt,'messages':prompt,**kwargs})
            try:output,meta=self.base.decide(prompt,**kwargs)
            except (RuntimeError,ValueError) as error:
                code=str(error);charges=[dict(zip(('id','usd','status'),r)) for r in self.base.db.execute('SELECT id,usd,status FROM charges') if r[0] not in before]
                entry={'type':'error','time':time.time(),'context':self.context,'attempt':attempt,'code':code,'charges':charges}
                self.log(entry);self.status['errors'].append(entry);write_json(self.folder/'status.json',self.status)
                if code not in ('http_429','http_502','http_503','http_504','TimeoutError','URLError') or attempt==2:raise GateStop(code) from None
                time.sleep(30);continue
            self.log({'type':'response','time':time.time(),'context':self.context,'attempt':attempt,'output':output,'meta':meta})
            self.status['returned_calls']+=1
            return output,meta


def initial_status():
    return {'started_unix':time.time(),'current':None,'completed':[],'returned_calls':0,'errors':[],'telemetry':[],'stop':None}


def finish(folder,status,client,source_hashes):
    if client:client.base.db.close()
    status['finished_unix']=time.time();status['elapsed_seconds']=time.time()-status['started_unix']
    check_hashes(source_hashes);status['sources_unchanged']=True
    write_json(folder/'status.json',status)


def resources(folder):
    import sqlite3,statistics
    status=read(folder/'status.json');path=folder/'calls.jsonl'
    calls=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    returned=[c for c in calls if c['type']=='response']
    ids={c['meta']['charge_id'] for c in returned}|{r['id'] for c in calls if c['type']=='error' for r in c['charges']}
    connection=sqlite3.connect((ROOT/'runs/phase1/budget.sqlite').as_uri()+'?mode=ro',uri=True)
    rows=[dict(zip(('id','usd','status'),r)) for r in connection.execute('SELECT id,usd,status FROM charges')];connection.close()
    def cost(rows):
        return {'requests':len(rows),'reported_usd':sum(r['usd'] for r in rows if r['status']=='reported'),
                'unknown_reserved_usd':sum(r['usd'] for r in rows if r['status']!='reported'),'occupied_usd':sum(r['usd'] for r in rows)}
    latency=[r['meta']['latency_s'] for r in returned];gpu=[]
    for t in status['telemetry']:
        try:gpu.append([float(v) for v in t['gpu_csv_C_MHz_MiB_W'].split(',')])
        except (ValueError,KeyError):pass
    return {'cost':cost([r for r in rows if r['id'] in ids]),'phase1_all_cost':cost(rows),
            'returned_calls':len(returned),'requests_including_retries':sum(r['type']=='request' for r in calls),
            'latency_s':{'median':statistics.median(latency) if latency else None,'max':max(latency) if latency else None},
            'elapsed_seconds':status.get('elapsed_seconds'),'concurrency':1,
            'telemetry':{'samples':len(status['telemetry']),'all_ac':all(t['ac_online'] is True for t in status['telemetry']),
                         'gpu_min_C_MHz_MiB_W':[min(v[i] for v in gpu) for i in range(4)] if gpu else None,
                         'gpu_max_C_MHz_MiB_W':[max(v[i] for v in gpu) for i in range(4)] if gpu else None}}
