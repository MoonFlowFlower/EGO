"""Idempotent, task-named research containers. No restart policy or published database port."""
import argparse
import json
import secrets
import subprocess
from .provider import ROOT, MODEL, write_json

IMAGE='ghcr.io/vectorize-io/hindsight@sha256:b4d3b76f363aa40cf348450e7f8f52a50653008731b99824b14623a196182e73'

def docker(*args,check=True):
    return subprocess.run(['wsl','-d','Ubuntu','-u','root','--','docker',*args],
                          capture_output=True,text=True,check=check)

def linux_path(p):
    s=str(p.resolve()).replace('\\','/')
    return '/mnt/'+s[0].lower()+s[2:]

def start():
    state=ROOT/'state';state.mkdir(exist_ok=True)
    password=state/'database-password.txt'
    if not password.exists():password.write_text(secrets.token_urlsafe(24))
    cfg=json.loads((state/'gateway.json').read_text())
    token=(state/'gateway-token.txt').read_text()
    env={'HINDSIGHT_API_LLM_PROVIDER':'openai', 'HINDSIGHT_API_LLM_MODEL':cfg.get('profile',{}).get('model',MODEL),
         'HINDSIGHT_API_LLM_BASE_URL':cfg['wsl']+'/hindsight/v1',
         'HINDSIGHT_API_LLM_API_KEY':token,'HINDSIGHT_API_LLM_MAX_RETRIES':'0',
         'HINDSIGHT_API_LLM_MAX_CONCURRENT':'1','HINDSIGHT_API_LLM_TIMEOUT':'200',
         'HINDSIGHT_API_DATABASE_URL':'postgresql://lab:'+password.read_text()+'@ego-memory-db:5432/lab',
         'HINDSIGHT_API_VECTOR_EXTENSION':'pgvector','HINDSIGHT_API_TEXT_SEARCH_EXTENSION':'pgroonga',
         'HINDSIGHT_API_EMBEDDINGS_PROVIDER':'openai','HINDSIGHT_API_EMBEDDINGS_OPENAI_MODEL':'BAAI/bge-m3',
         'HINDSIGHT_API_EMBEDDINGS_OPENAI_BASE_URL':cfg['wsl']+'/v1',
         'HINDSIGHT_API_EMBEDDINGS_OPENAI_API_KEY':token,'HINDSIGHT_API_EMBEDDINGS_OPENAI_DIMENSIONS':'1024',
         'HINDSIGHT_API_RERANKER_PROVIDER':'tei','HINDSIGHT_API_RERANKER_TEI_URL':cfg['wsl'],
         'HINDSIGHT_API_RERANKER_TEI_HTTP_TIMEOUT':'200','HINDSIGHT_API_RERANKER_MAX_RETRIES':'0',
         'HINDSIGHT_API_RETAIN_MAX_CONCURRENT':'1', 'HINDSIGHT_API_RETAIN_CHUNK_SIZE':'1500',
         'HINDSIGHT_API_ENABLE_BANK_CONFIG_API':'true','HINDSIGHT_API_LOG_LEVEL':'info',
         'HINDSIGHT_API_ENABLE_DOCUMENT_EXPORT_API':'true','HINDSIGHT_API_ENABLE_DOCUMENT_IMPORT_API':'true',
         'HINDSIGHT_API_OTEL_TRACES_ENABLED':'false'}
    (state/'hindsight.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
    (state/'postgres.env').write_text('POSTGRES_USER=lab\nPOSTGRES_DB=lab\nPOSTGRES_PASSWORD='+password.read_text()+'\n')
    docker('network','create','ego-memory-net',check=False)
    for name in ['ego-memory-db','ego-memory-hindsight']:
        if name=='ego-memory-hindsight':
            existing=docker('inspect',name,check=False)
            if existing.returncode==0:
                values=json.loads(existing.stdout)[0]['Config']['Env']
                if 'HINDSIGHT_API_LLM_MODEL='+env['HINDSIGHT_API_LLM_MODEL'] not in values:
                    docker('stop',name);docker('rm',name)
        if docker('inspect',name,check=False).returncode==0:
            docker('start',name)
            continue
        if name.endswith('db'):
            docker('run','-d','--name',name,'--network','ego-memory-net',
                   '--label','ego.memory_lab=true','--env-file',linux_path(state/'postgres.env'),
                   '-v','ego-memory-pg:/var/lib/postgresql/data','ego-memory-pgroonga:4.0.8')
        else:
            docker('run','-d','--name',name,'--network','ego-memory-net',
                   '--label','ego.memory_lab=true','--env-file',linux_path(state/'hindsight.env'),
                   '-p','127.0.0.1:18888:8888',IMAGE)
    write_json(ROOT/'evidence/docker-images.json',json.loads(docker('image','inspect',IMAGE,'ego-memory-pgroonga:4.0.8').stdout))
    print('Started named research containers; inspect /health before running experiments.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['start','stop']);a=p.parse_args()
    if a.command=='start':start()
    else:docker('stop','ego-memory-hindsight','ego-memory-db');print('Research containers stopped; data retained.')
