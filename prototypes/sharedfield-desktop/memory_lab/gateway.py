"""Local fixed-model gateway plus shared, revision-pinned Chinese retrieval models."""
import argparse
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from .provider import Client, ROOT, BatchStopped, write_json, PROFILES


class RetrievalModels:
    def __init__(self):
        import torch
        from sentence_transformers import SentenceTransformer, CrossEncoder
        torch.set_num_threads(6)
        self.encoder = SentenceTransformer(str(ROOT/'.cache/models/bge-m3'), device='cpu', local_files_only=True)
        self.encoder.max_seq_length = 2048
        self.reranker = CrossEncoder(str(ROOT/'.cache/models/bge-reranker-v2-m3'), device='cpu',
                                    max_length=2048, local_files_only=True)
        self.lock = threading.Lock()
        self.cache = sqlite3.connect(ROOT/'.cache/vectors.sqlite', check_same_thread=False)
        self.cache.execute('CREATE TABLE IF NOT EXISTS vectors(id TEXT PRIMARY KEY, vector TEXT)')

    def embed(self, texts):
        with self.lock:
            ids=[hashlib.sha256(t.encode()).hexdigest() for t in texts]
            cached=[self.cache.execute('SELECT vector FROM vectors WHERE id=?',(k,)).fetchone() for k in ids]
            missing=list(dict.fromkeys(i for i, c in enumerate(cached) if c is None))
            if missing:
                values=self.encoder.encode([texts[i] for i in missing],batch_size=4,normalize_embeddings=True,
                                           show_progress_bar=False).tolist()
                with self.cache:
                    for i,v in zip(missing,values):
                        self.cache.execute('INSERT OR REPLACE INTO vectors VALUES(?,?)',(ids[i],json.dumps(v)))
                        cached[i]=(json.dumps(v),)
            return [json.loads(v[0]) for v in cached]

    def rerank(self, query, texts):
        if not texts: return []
        with self.lock:
            scores=self.reranker.predict([(query,t) for t in texts],batch_size=4,show_progress_bar=False).tolist()
        return sorted([{'index':i,'score':float(s)} for i,s in enumerate(scores)], key=lambda r:-r['score'])


def make_app(client, retrieval, token):
    app=FastAPI()

    def authorize(request):
        if request.headers.get('authorization') != 'Bearer '+token:
            raise HTTPException(401, 'Local gateway authentication required')

    @app.get('/health')
    def health():
        return {'ready':True,'stopped':(client.directory/'STOPPED.json').exists(),'scope':client.scope,
                'profile':client.profile,'batch':client.directory.name,'campaign':client.campaign.name}

    @app.get('/info')
    def info(): return {'model_id':'BAAI/bge-reranker-v2-m3'}

    @app.post('/control')
    async def control(request:Request):
        authorize(request)
        body=await request.json()
        client.scope=str(body['scope'])
        return {'scope':client.scope}

    @app.post('/{source}/v1/chat/completions')
    async def chat(source:str, request:Request):
        authorize(request)
        body=await request.json()
        try:
            # Serialize paid calls; gateway logs before dispatch. Worker thread leaves health responsive.
            from starlette.concurrency import run_in_threadpool
            return await run_in_threadpool(client.complete, body, source)
        except BatchStopped as exc: raise HTTPException(503,str(exc))

    @app.post('/v1/embeddings')
    async def embeddings(request:Request):
        authorize(request)
        body=await request.json()
        texts=body['input']
        if isinstance(texts,str): texts=[texts]
        if not isinstance(texts,list) or not all(isinstance(t,str) for t in texts):
            raise HTTPException(400,'Text inputs required')
        from starlette.concurrency import run_in_threadpool
        vecs=await run_in_threadpool(retrieval.embed,texts)
        return {'model':'BAAI/bge-m3','object':'list',
                'data':[{'index':i,'object':'embedding','embedding':v} for i,v in enumerate(vecs)],
                'usage':{'prompt_tokens':0,'total_tokens':0}}

    @app.post('/rerank')
    async def rerank(request:Request):
        # Hindsight's TEI client has no API-key option. Bound only to loopback / WSL adapter.
        from starlette.concurrency import run_in_threadpool
        body=await request.json()
        return await run_in_threadpool(retrieval.rerank,body['query'],body['texts'])
    return app


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--wsl-host',required=True)
    p.add_argument('--batch',default=str(ROOT/'runs'/'batch-01'))
    p.add_argument('--max-calls',type=int,default=5000)
    p.add_argument('--profile',choices=list(PROFILES),default='deepseek')
    p.add_argument('--campaign')
    args=p.parse_args()
    secret=ROOT/'state/gateway-token.txt'
    secret.parent.mkdir(parents=True,exist_ok=True)
    if not secret.exists(): secret.write_text(secrets.token_urlsafe(32))
    client=Client(args.batch,max_calls=args.max_calls,profile=args.profile,campaign=args.campaign)
    models=RetrievalModels()
    app=make_app(client,models,secret.read_text())
    write_json(ROOT/'state/gateway.json',{'windows':'http://127.0.0.1:18765',
                 'wsl':'http://'+args.wsl_host+':18765','batch':str(client.directory),
                 'profile':client.profile,'campaign':str(client.campaign)})
    threading.Thread(target=lambda:uvicorn.run(app,host=args.wsl_host,port=18765,log_level='warning'),daemon=True).start()
    uvicorn.run(app,host='127.0.0.1',port=18765,log_level='warning')

if __name__=='__main__': main()
