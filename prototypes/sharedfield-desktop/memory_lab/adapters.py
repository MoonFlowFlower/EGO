"""Comparable original-evidence adapters. The simulation owns commitments, not retrieval."""
from __future__ import annotations
import json
import re
import shutil
import sqlite3
import subprocess
import time
import urllib.request
import urllib.error
from urllib.parse import quote
import threading
import queue
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from contextlib import closing
import numpy as np
import tiktoken
from .core import canonical, digest
from .provider import ROOT, MODEL, write_json

TOKENIZER=tiktoken.get_encoding('cl100k_base')

def http(url, data=None, method=None, auth=False, timeout=240):
    headers={'Content-Type':'application/json'}
    if auth: headers['Authorization']='Bearer '+(ROOT/'state/gateway-token.txt').read_text()
    request=urllib.request.Request(url,data=canonical(data).encode() if data is not None else None,
                                   headers=headers,method=method)
    with urllib.request.urlopen(request,timeout=timeout) as r:
        b=r.read()
        return json.loads(b) if b else {}

def scope(value):
    return http('http://127.0.0.1:18765/control',{'scope':canonical(value) if isinstance(value,dict) else value},auth=True)

def check_gateway():
    if http('http://127.0.0.1:18765/health')['stopped']:
        raise RuntimeError('Gateway batch stopped; inspect raw provider receipt')

def embed(texts):
    if not texts:return []
    result=http('http://127.0.0.1:18765/v1/embeddings',{'input':texts,'model':'BAAI/bge-m3'},auth=True)
    return [r['embedding'] for r in result['data']]

def completion(messages, source='agent', max_tokens=1024, json_mode=True):
    body={'messages':messages,'model':MODEL,'max_tokens':max_tokens}
    if json_mode:body['response_format']={'type':'json_object'}
    return http(f'http://127.0.0.1:18765/{source}/v1/chat/completions',body,auth=True)

def evidence_budget(rows, max_tokens=2500):
    out=[];used=0
    for row in rows:
        n=len(TOKENIZER.encode(canonical(row)))
        if used+n>max_tokens:continue
        out.append(row);used+=n
    return out

def terms(text):
    # SQLite unicode61 alone does not segment unspaced Chinese. Chinese bigrams
    # plus Latin words make this a meaningful full-text baseline.
    chinese=re.findall(r'[\u3400-\u9fff]+',text)
    return ' '.join(re.findall(r'[a-z0-9_]+',text.lower())+
                    [s[i:i+2] for s in chinese for i in range(max(1,len(s)-1))])

class Adapter:
    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        original=cls.__dict__.get('retain')
        if original is None:return
        def recorded(self,events):
            if not events:return original(self,events)
            path=self.directory/'writes.json'
            journal=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
            for e in events:journal[e['id']]={'status':'pending','hash':digest(e)}
            write_json(path,journal)
            result=original(self,events)
            for e in events:journal[e['id']]={'status':'complete','hash':digest(e)}
            write_json(path,journal)
            return result
        cls.retain=recorded

    def __init__(self,store,directory):
        self.store=store;self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.last_raw=None

    def evidence(self,ids,text=None):
        raw={e['id']:e for e in self.store.events()}
        ids=list(dict.fromkeys(s for s in ids if s is not None))
        if any(s not in raw for s in ids):return None
        if not ids:return None
        return {'source_ids':ids,'text':text or '\n'.join(raw[s]['text'] for s in ids),
                'events':[raw[s] for s in ids]}

    def flush(self):pass
    def write_status(self,ids):
        path=self.directory/'writes.json'
        journal=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
        return {i:('complete' if journal.get(i,{}).get('status')=='complete' else
                   'unknown' if i in journal else 'absent') for i in ids}
    def rebuild(self,events):raise NotImplementedError('Backend must recover uncertain writes')
    def close(self):pass
    def snapshot(self,path):
        self.flush()
        path=Path(path)
        if path.exists():raise ValueError('Snapshot destination already exists')
        shutil.copytree(self.directory,path)
    def reopen(self):pass
    def export_portable(self,path):self.snapshot(path)
    def import_portable(self,path):
        self.close()
        self.directory=Path(path)
        self.reopen()

class Baseline(Adapter):
    def __init__(self,store,directory,embed=embed):
        super().__init__(store,directory);self.embed=embed;self.reopen()
    def reopen(self):
        self.db=sqlite3.connect(self.directory/'baseline.sqlite')
        self.db.executescript('CREATE TABLE IF NOT EXISTS vectors(id TEXT PRIMARY KEY, value TEXT);'
                             'CREATE VIRTUAL TABLE IF NOT EXISTS text_index USING fts5(id UNINDEXED, terms);')
    def retain(self,events):
        existing={r[0] for r in self.db.execute('SELECT id FROM vectors')}
        events=[e for e in events if e['id'] not in existing]
        values=self.embed([e['text'] for e in events]) if events else []
        with self.db:
            for e,v in zip(events,values):
                self.db.execute('INSERT INTO vectors VALUES(?,?)',(e['id'],canonical(v)))
                self.db.execute('INSERT INTO text_index VALUES(?,?)',(e['id'],terms(e['text'])))
    def recall(self,query):
        rows=list(self.db.execute('SELECT id,value FROM vectors'))
        if not rows:return []
        q=np.asarray(self.embed([query])[0]);scores=np.array([json.loads(v) for _,v in rows])@q
        semantic=[rows[i][0] for i in np.argsort(-scores)]
        ts=list(dict.fromkeys(terms(query).split()))
        lexical=[]
        if ts:
            expr=' OR '.join('"'+t.replace('"','""')+'"' for t in ts)
            lexical=[r[0] for r in self.db.execute('SELECT id FROM text_index WHERE text_index MATCH ? ORDER BY rank',(expr,))]
        fused={}
        for ranking in [semantic,lexical]:
            for i,key in enumerate(ranking):fused[key]=fused.get(key,0)+1/(60+i+1)
        ordered=sorted(fused,key=lambda k:-fused[k])[:12]
        self.last_raw={'semantic':semantic[:12],'lexical':lexical[:12],'fusion':ordered}
        return [r for key in ordered if (r:=self.evidence([key]))]
    def forget(self,ids):
        with self.db:
            for key in ids:
                self.db.execute('DELETE FROM vectors WHERE id=?',(key,))
                self.db.execute('DELETE FROM text_index WHERE id=?',(key,))
    def write_status(self,ids):
        vectors={r[0] for r in self.db.execute('SELECT id FROM vectors')}
        fulltext={r[0] for r in self.db.execute('SELECT id FROM text_index')}
        return {i:('complete' if i in vectors and i in fulltext else
                   'absent' if i not in vectors and i not in fulltext else 'unknown') for i in ids}
    def rebuild(self,events):
        with self.db:
            self.db.execute('DELETE FROM vectors');self.db.execute('DELETE FROM text_index')
        self.retain(events)
    def close(self):self.db.close()
    def snapshot(self,path):
        self.db.commit();super().snapshot(path)

class MemOS(Adapter):
    def __init__(self,store,directory):
        super().__init__(store,directory);self.reopen()
    def reopen(self):
        self.log=open(self.directory/'bridge.log','a',encoding='utf-8')
        self.proc=subprocess.Popen(['node',str(ROOT/'memos_bridge.cjs')],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=self.log,text=True,encoding='utf-8',bufsize=1)
        self.send({'op':'init','directory':str(self.directory.resolve())})
    def send(self,message):
        self.proc.stdin.write(canonical(message)+'\n');self.proc.stdin.flush()
        result=queue.Queue(maxsize=1)
        threading.Thread(target=lambda:result.put(self.proc.stdout.readline()),daemon=True).start()
        try:line=result.get(timeout=600)
        except queue.Empty:
            self.proc.kill();self.proc.wait(timeout=10)
            raise TimeoutError('MemOS bridge exceeded its finite 600-second operation deadline')
        if not line:raise RuntimeError('MemOS bridge exited; inspect bridge.log')
        reply=json.loads(line)
        if 'error' in reply:raise RuntimeError(reply['error'])
        self.peak_rss_bytes=reply.get('metrics',{}).get('peak_rss_bytes')
        return reply['result']
    def retain(self,events):
        self.send({'op':'retain','events':events});check_gateway()
    def flush(self):self.send({'op':'flush'});check_gateway()
    def recall(self,query):
        result=self.send({'op':'recall','query':query});self.last_raw=result
        evidence=[]
        for hit in result.get('hits',[]):
            ids=[hit.get('ref',{}).get('sessionKey')]
            # Merged native chunks may contain more than one original event.
            ids+=re.findall(r'"id"\s*:\s*"([^"]+)"',hit.get('original_excerpt',''))
            row=self.evidence(ids,hit.get('summary'))
            if row:evidence.append(row)
        return evidence
    def forget(self,ids):
        # Native deleteSession does not remove derived task summaries. Rebuild the
        # entire candidate index from canonical surviving sources, then discard it.
        self.close()
        old=self.directory/'memos.db'
        for suffix in ('','-wal','-shm'):
            p=Path(str(old)+suffix)
            if p.exists():p.unlink()
        self.reopen();self.retain(self.store.events())
    def write_status(self,ids):
        states=super().write_status(ids)
        path=self.directory/'memos.db'
        if not path.exists():return {i:'absent' for i in ids}
        with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as db:
            present={r[0] for r in db.execute('SELECT DISTINCT session_key FROM chunks')}
        return {i:('complete' if states[i]=='complete' and i in present else
                   'absent' if states[i]=='absent' and i not in present else 'unknown') for i in ids}
    def rebuild(self,events):self.forget([])
    def close(self):
        try:
            if self.proc.poll() is None:self.send({'op':'close'})
        finally:
            self.proc.stdin.close();self.proc.wait(timeout=15);self.log.close()
    def snapshot(self,path):
        self.close()
        try:shutil.copytree(self.directory,path)
        finally:self.reopen()

class Hindsight(Adapter):
    def __init__(self,store,directory,bank=None):
        super().__init__(store,directory)
        config=self.directory/'bank.json'
        if config.exists():self.bank=json.loads(config.read_text())['bank']
        elif bank:
            self.bank=bank;write_json(config,{'bank':bank})
        else:raise ValueError('A unique bank ID is required for a new Hindsight index')
    def api(self,path='',data=None,method=None):
        return http('http://127.0.0.1:18888/v1/default/banks/'+self.bank+path,data,method,timeout=600)
    def retain(self,events):
        if not events:return
        self.api('/memories',{'items':[{'content':canonical(e),'document_id':e['id'],
                  'context':'模拟生活材料。kind 区分陈述、执行结果、推断；推断不代表实际发生。',
                  'timestamp':(datetime(2026,1,1,tzinfo=timezone.utc)+timedelta(seconds=e['at'])).isoformat(),
                  'metadata':{'event_id':e['id'],'kind':e['kind']}}
                 for e in events],'async':False})
        self.flush()
    def flush(self,require_model=True):
        deadline=time.monotonic()+600
        while time.monotonic()<deadline:
            if require_model:check_gateway()
            failed=self.api('/operations?status=failed&limit=1')
            if failed.get('total'):raise RuntimeError('Hindsight indexing operation failed: '+canonical(failed))
            pending=self.api('/operations?status=pending&limit=1').get('total',0)
            active=self.api('/operations?status=processing&limit=1').get('total',0)
            if not pending and not active:return
            time.sleep(1)
        raise TimeoutError('Hindsight did not finish indexing within 600 seconds')
    def recall(self,query):
        result=self.api('/memories/recall',{'query':query,'budget':'mid','max_tokens':2500,
                          'include':{'entities':None,'source_facts':{'max_tokens':-1}},'trace':True})
        self.last_raw=result;out=[]
        source=result.get('source_facts') or {}
        for hit in result.get('results',[]):
            ids=[hit.get('document_id')]
            if any(s not in source for s in (hit.get('source_fact_ids') or [])):continue
            ids += [source[s].get('document_id') for s in (hit.get('source_fact_ids') or []) if s in source]
            row=self.evidence(ids,hit.get('text'))
            if row:out.append(row)
        return out
    def forget(self,ids):
        for key in ids:
            try:self.api('/documents/'+quote(key,safe=''),method='DELETE')
            except urllib.error.HTTPError as exc:
                if exc.code!=404:raise
        self.flush()
    def write_status(self,ids):
        states={};raw={e['id']:e for e in self.store.events()}
        journal=super().write_status(ids)
        for key in ids:
            try:doc=self.api('/documents/'+quote(key,safe=''))
            except urllib.error.HTTPError as exc:
                if exc.code!=404:raise
                states[key]='absent';continue
            # A durable local completion acknowledgement plus the native source
            # prevents an uncertain, partly processed document being called complete.
            text=doc.get('original_text',doc.get('content'))
            states[key]='complete' if journal[key]=='complete' and text==canonical(raw[key]) else 'unknown'
        return states
    def rebuild(self,events):
        config=self.directory/'bank.json'
        old=json.loads(config.read_text(encoding='utf-8'))
        generation=old.get('generation',0)+1
        self.bank='egolab-rebuild-'+digest([str(self.directory.resolve()),generation])[:24]
        write_json(config,{'bank':self.bank,'generation':generation,'previous_bank':old['bank']})
        self.retain(events)
    def snapshot(self,path):
        self.flush();path=Path(path)
        target='egolab-clone-'+uuid.uuid4().hex[:24]
        self.api('/clone?target_bank_id='+target,{},'POST');self.flush()
        path.mkdir(parents=True);write_json(path/'bank.json',{'bank':target})
    def export_portable(self,path):
        self.flush(require_model=False);path=Path(path);path.mkdir(parents=True,exist_ok=False)
        submitted=self.api('/transfer/export',{},'POST');self.flush(require_model=False)
        operation=self.api('/operations/'+submitted['operation_id'])
        write_json(path/'export-operation.json',operation)
        url=operation['result_metadata']['download_url']
        if url.startswith('/'):url='http://127.0.0.1:18888'+url
        # Only the configured local service can supply an archive; never send credentials elsewhere.
        if not url.startswith('http://127.0.0.1:18888/'):raise ValueError('Unexpected archive host')
        with urllib.request.urlopen(url,timeout=120) as r:(path/'bank.zip').write_bytes(r.read())
    def import_portable(self,path):
        import httpx
        path=Path(path);old_bank=self.bank
        target='egolab-restore-'+digest(str(path.resolve()))[:24]
        with (path/'bank.zip').open('rb') as archive:
            r=httpx.post('http://127.0.0.1:18888/v1/default/banks/'+old_bank+'/transfer/import',
                params={'target_bank_id':target,'mode':'restore'},files={'file':('bank.zip',archive,'application/zip')},timeout=240)
            r.raise_for_status();submission=r.json()
        self.flush(require_model=False)
        operation=self.api('/operations/'+submission['operation_id'])
        if operation['status']!='completed':raise RuntimeError('Portable import incomplete')
        self.bank=target;write_json(self.directory/'bank.json',{'bank':target})

ADAPTERS={'baseline':Baseline,'memos':MemOS,'hindsight':Hindsight}
