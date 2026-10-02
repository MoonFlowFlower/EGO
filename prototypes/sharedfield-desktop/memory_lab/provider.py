"""Single paid transport. Fixed route, durable receipts, finite budget, no retries."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.request
import urllib.error
import uuid
import sqlite3
import hashlib
import math
from contextlib import contextmanager

MODEL = 'deepseek/deepseek-v4-flash-0731'
ROUTE = 'deepinfra/fp8'
PROFILES = {
    'deepseek':dict(model=MODEL,route=ROUTE,provider='DeepInfra'),
    'qwen37':dict(model='qwen/qwen3.7-flash',route='alibaba',provider='Alibaba'),
    'qwen35':dict(model='qwen/qwen3.5-flash-02-23',route='alibaba',provider='Alibaba'),
    'gemini':dict(model='google/gemini-2.5-flash-lite',route='google-ai-studio',provider='Google AI Studio'),
}

def profile_config(name):
    return dict(id=name,**PROFILES[name],temperature=0,top_p=1,seed=20260923,reasoning=False,max_tokens=4096)
KEY_FILE = Path('D:/Project/MyAIWorkspace/openrouter.txt' if os.name=='nt' else '/mnt/d/Project/MyAIWorkspace/openrouter.txt')
ROOT = Path(__file__).resolve().parent


class BatchStopped(RuntimeError):
    pass


def read_key(path=KEY_FILE):
    lines = Path(path).read_text(encoding='utf-8-sig').splitlines()
    found = []
    for i, line in enumerate(lines):
        if 'codex' in line.casefold() and 'key' in line.casefold():
            segment = line + '\n' + (lines[i+1] if i+1 < len(lines) else '')
            found.extend(re.findall(r'sk-or-[A-Za-z0-9_-]+', segment))
    if len(set(found)) != 1:
        raise ValueError('Exactly one credential under the codex key label is required')
    return found[0]


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(tmp, path)


def payload(request, profile='deepseek'):
    cfg=profile_config(profile)
    p = {k: v for k, v in request.items() if k in
         ('messages','tools','tool_choice','response_format','stop')}
    p.update(model=cfg['model'], temperature=0, top_p=1, seed=20260923,
             max_tokens=min(int(request.get('max_tokens',4096)),4096), stream=False,
             reasoning={'enabled':False}, provider={'only':[cfg['route']], 'allow_fallbacks':False,
                                                    'require_parameters':True})
    return p


class Client:
    def __init__(self, directory, key=None, max_calls=5000, campaign=None, profile='deepseek'):
        self.directory = Path(directory)
        (self.directory/'calls').mkdir(parents=True, exist_ok=True)
        self.key = key if key is not None else read_key()
        self.max_calls = max_calls
        self.lock = threading.Lock()
        self.scope = 'smoke'
        self.profile=profile_config(profile)
        cfg=self.directory/'PROFILE.json'
        if cfg.exists() and json.loads(cfg.read_text())!=self.profile:raise ValueError('Immutable batch profile mismatch')
        if not cfg.exists():write_json(cfg,self.profile)
        self.campaign=Path(campaign) if campaign else self.directory/'campaign-budget'
        self.campaign.mkdir(parents=True,exist_ok=True)
        with self.budget_db() as db:
            db.executescript('CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,status TEXT);'
                             'CREATE TABLE IF NOT EXISTS config(id TEXT PRIMARY KEY,value TEXT);')
            old=db.execute("SELECT value FROM config WHERE id='limit'").fetchone()
            if old and int(old[0])!=max_calls:raise ValueError('Campaign budget cannot change on resume')
            db.execute("INSERT OR IGNORE INTO config VALUES('limit',?)",(str(max_calls),))

    @contextmanager
    def budget_db(self):
        db=sqlite3.connect(self.campaign/'budget.sqlite',timeout=30)
        try:
            with db:yield db
        finally:db.close()

    def reserve(self, call_id, source=None):
        status=self.campaign/'status.json'
        if status.exists() and json.loads(status.read_text(encoding='utf-8')).get('status') in ('stopped','complete','exhausted'):
            raise BatchStopped('Campaign is closed; additional paid dispatch is prohibited')
        with self.budget_db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute("SELECT 1 FROM config WHERE id='blocked'").fetchone():
                raise BatchStopped('Campaign has unresolved or non-retriable failure')
            if db.execute("SELECT 1 FROM attempts WHERE status NOT IN ('ok','error')").fetchone():
                raise BatchStopped('Campaign has an unresolved request; replay prohibited')
            policy_row=db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()
            if policy_row:
                policy=json.loads(policy_row[0])
                try:context=json.loads(self.scope)
                except (ValueError,TypeError):context={}
                arm=context.get('arm') if isinstance(context,dict) else None
                if (not isinstance(context,dict) or self.directory.name!=policy['batch']
                    or context.get('run_id')!=policy['run'] or context.get('split')!='development'
                    or context.get('condition')!='memory' or context.get('case') not in policy['cases']
                    or arm not in policy.get('arms',('baseline','memos','hindsight'))
                    or source not in policy.get('sources',('agent','memos','hindsight'))
                    or (source!='agent' and source!=arm)):
                    raise BatchStopped('Request outside the authorized development exploration')
                if db.execute('SELECT count(*) FROM attempts').fetchone()[0]>=policy['start']+policy['additional']:
                    raise BatchStopped('Exploration additional request cap reached')
                if db.execute('SELECT count(*) FROM attempts').fetchone()[0]>=policy.get('absolute_limit',self.max_calls):
                    raise BatchStopped('Revision request cap reached')
            if db.execute('SELECT count(*) FROM attempts').fetchone()[0]>=self.max_calls:
                raise BatchStopped('Cumulative campaign call budget exhausted')
            db.execute('INSERT INTO attempts VALUES(?,?)',(call_id,'pending'))

    def check_exploration_billing(self, receipt):
        with self.budget_db() as db:
            active=db.execute("SELECT 1 FROM config WHERE id='exploration_policy'").fetchone()
        cost=(receipt.get('usage') or {}).get('cost')
        if active and (type(cost) not in (int,float) or not math.isfinite(cost) or cost<0):
            self.finish_attempt(receipt['id'],'received','Unknown billing in exploration')
            self.stop('Billing is unknown; no further exploration dispatch',receipt['id'],'unknown_billing')

    def finish_attempt(self,call_id,status,block=None):
        with self.budget_db() as db:
            db.execute('UPDATE attempts SET status=? WHERE id=?',(status,call_id))
            if block:db.execute("INSERT OR REPLACE INTO config VALUES('blocked',?)",(block,))

    def _request(self, p):
        req = urllib.request.Request('https://openrouter.ai/api/v1/chat/completions',
            data=json.dumps(p).encode(), headers={'Authorization':'Bearer '+self.key,
            'Content-Type':'application/json','X-Title':'EGO memory lab'})
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)

    def stop(self, reason, call_id, reason_code='failed'):
        write_json(self.directory/'STOPPED.json', {'reason':reason,'reason_code':reason_code,'call_id':call_id,'time':time.time()})
        raise BatchStopped(reason)

    def chat(self, messages, source='agent', **kwargs):
        return self.complete(dict(messages=messages, **kwargs), source)

    def check_provider_error(self, receipt, path):
        """Classify application errors even when transport returned HTTP 200.

        Preserve the raw response and explicit usage; an error never authorizes
        redispatch. Only an explicit 429 makes the batch rotation eligible.
        """
        reply=receipt.get('response',{})
        errors=[reply['error']] if reply.get('error') else []
        for choice in reply.get('choices',[]):
            if choice.get('error'):errors.append(choice['error'])
            elif choice.get('finish_reason')=='error':errors.append({'message':'Error finish reason without code'})
        if not errors:return
        # Conflicting errors must not turn a non-429 failure into a fallback.
        normalized=[e if isinstance(e,dict) else {'message':str(e)} for e in errors]
        error=next((e for e in normalized if str(e.get('code'))!='429'),normalized[0])
        code=str(error.get('code',''))
        reason_code='http_'+code if code.isdigit() else 'provider_error'
        receipt.update(status='error',provider_error=error,provider_errors=normalized)
        write_json(path,receipt)
        self.finish_attempt(receipt['id'],'error',None if code=='429' else 'Explicit non-429 provider failure')
        self.stop('Provider returned an explicit completion error; no automatic retry',receipt['id'],reason_code)

    def complete(self, request, source):
        with self.lock:
            if (self.directory/'STOPPED.json').exists():
                raise BatchStopped('Batch is latched stopped; inspect evidence before starting a new batch')
            previous = list((self.directory/'calls').glob('*.json'))
            request=payload(request,self.profile['id'])
            adjustment=None
            with self.budget_db() as db:
                policy_row=db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()
            policy=json.loads(policy_row[0]) if policy_row else {}
            # The pinned MemOS provider uses exactly 300 for judgeDedup.
            # This explicit revision changes transport capacity, not its prompt,
            # merge algorithm or completion acceptance rule.
            if (policy.get('batch')==self.directory.name and source=='memos'
                and request['max_tokens']==300 and policy.get('memos_dedup_output_tokens')==4096):
                adjustment=dict(kind='memos_dedup_output_budget_v2',original_max_tokens=300,effective_max_tokens=4096)
                request['max_tokens']=4096
            signature=hashlib.sha256(json.dumps([self.scope,source,request],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            for file in previous:
                saved=json.loads(file.read_text(encoding='utf-8'))
                if saved['status'] in ('received','error'):
                    self.check_provider_error(saved,file)
                if saved['status']=='received':
                    self.check_exploration_billing(saved)
                    reply=saved.get('response',{})
                    if (reply.get('model')!=self.profile['model'] or reply.get('provider')!=self.profile['provider']
                        or reply.get('error') or not reply.get('choices')
                        or reply['choices'][0].get('finish_reason') not in ('stop','tool_calls')):
                        self.stop('Unusable received response; no redispatch permitted',saved['id'],'invalid_received')
                    saved['status']='ok';write_json(file,saved)
                    self.finish_attempt(saved['id'],'ok')
                if saved.get('signature')==signature and saved['status']=='ok':return saved['response']
            # A crash after dispatch leaves an unknown-billing pending receipt.
            if any(json.loads(p.read_text(encoding='utf-8'))['status']=='pending' for p in previous):
                self.stop('Unresolved pending request; automatic retry prohibited', 'recovery')
            if len(previous) >= self.max_calls:
                self.stop('Finite call budget exhausted', 'budget')
            call_id = f'{len(previous):05d}-{uuid.uuid4().hex[:8]}'
            path = self.directory/'calls'/f'{call_id}.json'
            self.reserve(call_id,source)
            receipt = dict(id=call_id, status='pending', scope=self.scope, source=source,
                           request=request, started_at=time.time(), billing='unknown',signature=signature,
                           profile=self.profile,campaign=self.campaign.name)
            if adjustment:receipt['transport_adjustment']=adjustment
            if self.scope.startswith('{'):receipt['context']=json.loads(self.scope)
            write_json(path, receipt)
            started = time.perf_counter()
            try:
                reply = self._request(request)
            except Exception as exc:
                receipt.update(status='error', error_type=type(exc).__name__,
                               latency_s=time.perf_counter()-started)
                if isinstance(exc, urllib.error.HTTPError):
                    receipt['http_status'] = exc.code
                    receipt['error_body'] = exc.read(32768).decode(errors='replace').replace(self.key,'[redacted]')
                write_json(path, receipt)
                code=receipt.get('http_status')
                # A received HTTP refusal is different from a lost response.
                block=None if code in (429,400,404,422) else 'Non-retriable or unknown request outcome'
                self.finish_attempt(call_id,'error',block)
                self.stop('Provider request failed; batch stopped without retry', call_id,
                          'http_'+str(code) if code else 'unknown_outcome')
            reply=dict(reply,lab_profile=self.profile)
            receipt.update(response=reply, latency_s=time.perf_counter()-started,
                           status='received', usage=reply.get('usage'), billing='see usage receipt')
            write_json(path, receipt)
            self.finish_attempt(call_id,'received')
            self.check_provider_error(receipt,path)
            self.check_exploration_billing(receipt)
            if reply.get('model') != self.profile['model'] or reply.get('provider') != self.profile['provider']:
                self.finish_attempt(call_id,'mismatch','Unexpected model/provider')
                self.stop('Actual model/provider receipt differs from the locked configuration', call_id)
            if reply.get('error') or not reply.get('choices'):
                self.stop('Provider returned no usable completion', call_id)
            if reply['choices'][0].get('finish_reason') not in ('stop', 'tool_calls'):
                self.stop('Incomplete completion; no automatic retry', call_id)
            receipt['status'] = 'ok'
            write_json(path, receipt)
            self.finish_attempt(call_id,'ok')
            return reply


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command', choices=['smoke'])
    parser.add_argument('--batch', default=str(ROOT/'runs'/'provider-smoke'))
    args=parser.parse_args()
    client=Client(args.batch, max_calls=1)
    reply=client.chat([{'role':'user','content':'这是模拟生活实验的连通性检查。只回复 JSON：{"ready":true}'}],
                      response_format={'type':'json_object'}, max_tokens=256)
    print(json.dumps({'model':reply['model'],'provider':reply['provider'],'usage':reply.get('usage'),
                      'content':reply['choices'][0]['message']['content']},ensure_ascii=False))


if __name__ == '__main__': main()
