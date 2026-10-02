"""Server-only transports. Never log headers, credential text or HTTP bodies."""
import json
import re
import sqlite3
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path
from .records import RUNS

MODEL='deepseek/deepseek-v4-flash-0731'
ROUTE='open-inference/fp8'


def action_format(messages):
    actions=json.loads(messages[-1]['content'])['observation']['actions']
    schema={'type':'object','properties':{'action':{'type':'string','enum':actions},
        'repeat':{'type':'integer','enum':[1,2,3,4]},'reason':{'type':'string','maxLength':400}},
        'required':['action','repeat','reason'],'additionalProperties':False}
    return {'type':'json_schema','json_schema':{'name':'action','strict':True,'schema':schema}}


def read_key():
    # Same label parsing as desktop_pet -> memory_lab.provider.read_key.
    lines=Path('D:/Project/MyAIWorkspace/openrouter.txt').read_text(encoding='utf-8-sig').splitlines()
    found=[]
    for i,line in enumerate(lines):
        if 'codex' in line.casefold() and 'key' in line.casefold():
            found.extend(re.findall(r'sk-or-[A-Za-z0-9_-]+',line+'\n'+(lines[i+1] if i+1<len(lines) else '')))
    if len(set(found))!=1: raise ValueError('credential_label_not_unique')
    return found[0]


def request_json(url,payload,headers=None,timeout=60):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: return json.load(r)
    except urllib.error.HTTPError as e: raise RuntimeError(f'http_{e.code}') from None
    except Exception as e: raise RuntimeError(type(e).__name__) from None


class Cloud:
    def __init__(self,model=MODEL,route=ROUTE,*,budget_path=None,limit=5):
        self.model,self.route=model,route
        self.limit=limit
        self.db=sqlite3.connect(budget_path or RUNS/'p2_budget.sqlite',timeout=30)
        self.db.execute('CREATE TABLE IF NOT EXISTS charges (id TEXT PRIMARY KEY, usd REAL NOT NULL, status TEXT NOT NULL)')
        self.key=read_key()
        req=urllib.request.Request('https://openrouter.ai/api/v1/endpoints/zdr',headers={'Authorization':'Bearer '+self.key})
        with urllib.request.urlopen(req,timeout=20) as response: endpoints=json.load(response)['data']
        compatible=[x for x in endpoints if x.get('model_id')==model and x.get('tag')==route
                    and float(x['pricing']['prompt'])<=.000001 and float(x['pricing']['completion'])<=.000002
                    and {'response_format','max_tokens','temperature','reasoning'}<=set(x.get('supported_parameters',[]))]
        if not compatible: raise ValueError('route_preflight_rejected')

    def decide(self,messages,*,response_format=None,max_tokens=512):
        # Upper bound: <=16k UTF8 bytes plus framing, output <=512 tokens,
        # provider max prices 1/2 USD per million input/output; reserve 0.05 USD.
        schema=response_format or action_format(messages)
        request_bytes=len(json.dumps({'messages':messages,'response_format':schema}).encode())
        if request_bytes>60000 or not 1<=max_tokens<=2048: raise ValueError('prompt_size_stop')
        # Conservative byte-token bound including schema/framing, with fixed
        # provider price ceilings. Concurrent requests reserve under one lock.
        reserve=max(.05,(request_bytes+2048)*.000001+max_tokens*.000002)
        identity=uuid.uuid4().hex
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            spent=self.db.execute('SELECT COALESCE(SUM(usd),0) FROM charges').fetchone()[0]
            if spent+reserve>self.limit: raise ValueError('budget_stop')
            self.db.execute('INSERT INTO charges VALUES (?,?,?)',(identity,reserve,'reserved_unknown'))
        payload={'model':self.model,'messages':messages,'temperature':0,'max_tokens':max_tokens,
            'reasoning':{'enabled':False},'response_format':schema,'stream':False,
            'provider':{'only':[self.route],'allow_fallbacks':False,'data_collection':'deny','zdr':True,
                        'require_parameters':True,'max_price':{'prompt':1,'completion':2}}}
        start=time.perf_counter()
        data=request_json('https://openrouter.ai/api/v1/chat/completions',payload,{'Authorization':'Bearer '+self.key})
        usage=data.get('usage',{});cost=usage.get('cost')
        if isinstance(cost,(int,float)) and cost>=0:
            with self.db:self.db.execute('UPDATE charges SET usd=?,status=? WHERE id=?',(cost,'reported',identity))
        meta={'latency_s':time.perf_counter()-start,'input_tokens':usage.get('prompt_tokens'),
              'output_tokens':usage.get('completion_tokens'),'cost_usd':cost,'provider':data.get('provider'),
              'charge_id':identity,'reserved_usd':reserve,
              'budget_reserved_or_reported_usd':self.db.execute('SELECT SUM(usd) FROM charges').fetchone()[0]}
        return data['choices'][0]['message'].get('content',''),meta


class Local:
    def __init__(self,model):self.model=model
    def decide(self,messages):
        start=time.perf_counter()
        data=request_json('http://127.0.0.1:11434/api/chat',{'model':self.model,'messages':messages,
            'stream':False,'format':'json','think':False,'keep_alive':'5m',
            'options':{'temperature':0,'num_predict':512,'num_ctx':8192}},timeout=120)
        return data['message']['content'],{'latency_s':time.perf_counter()-start,
            'input_tokens':data.get('prompt_eval_count'),'output_tokens':data.get('eval_count'),
            'eval_ns':data.get('eval_duration'),'load_ns':data.get('load_duration'),'cost_usd':0}


class LMStudio:
    def __init__(self,model):self.model=model
    def decide(self,messages):
        start=time.perf_counter()
        data=request_json('http://127.0.0.1:1234/v1/chat/completions',{'model':self.model,'messages':messages,
            'stream':False,'temperature':0,'max_tokens':512,
            'response_format':action_format(messages)},timeout=120)
        usage=data.get('usage',{})
        return data['choices'][0]['message'].get('content',''),{'latency_s':time.perf_counter()-start,
            'input_tokens':usage.get('prompt_tokens'),'output_tokens':usage.get('completion_tokens'),'cost_usd':0}
