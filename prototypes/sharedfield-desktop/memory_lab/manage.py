"""Local setup/start/stop entry. Does not launch experiments in the background."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
from .provider import ROOT, write_json

LINUX_PY='/root/ego-memory-lab/.venv/bin/python'

def run(args,**kwargs):return subprocess.run(args,check=True,cwd=ROOT.parent,**kwargs)
def wsl(*args):return ['wsl','-d','Ubuntu','-u','root','--cd',str(ROOT.parent),'--',*args]

def setup():
    from .provenance import PINS
    sources={'hindsight':'https://github.com/vectorize-io/hindsight.git',
             'MemOS':'https://github.com/MemTensor/MemOS.git','ace':'https://github.com/ace-agent/ace.git'}
    for name,commit in PINS.items():
        path=ROOT/'vendor'/name
        if not path.exists():
            run(['git','clone','--filter=blob:none','--no-checkout',sources[name],str(path)])
            run(['git','-C',str(path),'checkout',commit])
        else:
            head=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True).strip()
            if head!=commit:raise ValueError('Refusing to overwrite a different upstream checkout: '+name)
    run(['uv','pip','sync','--python',str(ROOT/'.venv/Scripts/python.exe'),str(ROOT/'requirements.lock.txt'),
         '--extra-index-url','https://download.pytorch.org/whl/cpu'])
    run(wsl('/root/.local/bin/uv','venv','--allow-existing','--python','3.11.15','/root/ego-memory-lab/.venv'))
    linux_lock='/mnt/'+str(ROOT)[0].lower()+str(ROOT)[2:].replace('\\','/')+'/requirements-linux.lock.txt'
    run(wsl('/root/.local/bin/uv','pip','sync','--python',LINUX_PY,linux_lock,'--extra-index-url','https://download.pytorch.org/whl/cpu'))
    plugin=ROOT/'vendor/MemOS/apps/memos-local-openclaw'
    import shutil
    shutil.copyfile(ROOT/'memos-package-lock.json',plugin/'package-lock.json')
    env=dict(os.environ,PUPPETEER_SKIP_DOWNLOAD='true',TELEMETRY_ENABLED='false')
    subprocess.run(['npm.cmd','ci','--ignore-scripts','--no-audit','--no-fund'],cwd=plugin,env=env,check=True)
    subprocess.run(['npm.cmd','rebuild','better-sqlite3'],cwd=plugin,env=env,check=True)
    run([str(plugin/'node_modules/.bin/tsc.cmd'),'-p',str(ROOT/'memos-tsconfig.json')])
    from huggingface_hub import snapshot_download
    revisions=json.loads((ROOT/'model-revisions.json').read_text())
    for name,revision in revisions.items():
        snapshot_download(name,revision=revision,local_dir=ROOT/'.cache/models'/name.split('/')[-1],
                          allow_patterns=['*.json','*.safetensors','*.txt','*.model','pytorch_model.bin','1_Pooling/*','2_Normalize/*'])
    run(wsl('service','docker','start'))
    run(wsl('docker','pull','ghcr.io/vectorize-io/hindsight@sha256:b4d3b76f363aa40cf348450e7f8f52a50653008731b99824b14623a196182e73'))
    dockerfile='/mnt/'+str(ROOT)[0].lower()+str(ROOT)[2:].replace('\\','/')+'/vendor/hindsight/docker/docker-compose/pgroonga'
    run(wsl('docker','build','-t','ego-memory-pgroonga:4.0.8',dockerfile))
    print('Setup complete. No paid experiment started.')

def start(batch='batch-01',profile='deepseek',campaign='reliability-01'):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',batch):raise ValueError('Batch ID must be a simple local name')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',campaign):raise ValueError('Campaign ID must be a simple local name')
    try:
        with urllib.request.urlopen('http://127.0.0.1:18765/health',timeout=2) as r:
            state=json.load(r)
        if state.get('stopped'):raise RuntimeError('Existing batch is stopped; inspect it before creating a new batch')
        if state.get('batch')!=batch or state.get('profile',{}).get('id')!=profile:
            raise RuntimeError('Another immutable batch/profile is running')
        run([sys.executable,'-B','-m','memory_lab.infra','start'])
        print('Existing gateway is healthy; research containers started.');return
    except (ConnectionError,urllib.error.URLError):pass
    run(wsl('service','docker','start'))
    log=(ROOT/'evidence/gateway-managed.log').open('a',encoding='utf-8')
    linux_batch='/mnt/'+str(ROOT)[0].lower()+str(ROOT)[2:].replace('\\','/')+'/runs/'+batch
    linux_campaign='/mnt/'+str(ROOT)[0].lower()+str(ROOT)[2:].replace('\\','/')+'/runs/campaigns/'+campaign
    proc=subprocess.Popen(wsl(LINUX_PY,'-B','-m','memory_lab.gateway','--wsl-host','172.17.0.1','--batch',linux_batch,
                              '--profile',profile,'--campaign',linux_campaign),
                          cwd=ROOT.parent,stdout=log,stderr=subprocess.STDOUT,
                          creationflags=subprocess.CREATE_NO_WINDOW)
    write_json(ROOT/'state/launcher.json',{'pid':proc.pid,'kind':'wsl gateway launcher'})
    deadline=time.monotonic()+90
    while time.monotonic()<deadline:
        if proc.poll() is not None:raise RuntimeError('Gateway exited; inspect evidence/gateway-managed.log')
        try:
            with urllib.request.urlopen('http://127.0.0.1:18765/health',timeout=2) as r:json.load(r)
            break
        except (ConnectionError,urllib.error.URLError):time.sleep(1)
    else:raise TimeoutError('Gateway startup did not finish within 90 seconds')
    run([sys.executable,'-B','-m','memory_lab.infra','start'])

def stop():
    run([sys.executable,'-B','-m','memory_lab.infra','stop'])
    (ROOT/'state/stop-resource-monitor').touch()
    # Identify only this workspace's gateway process; do not terminate unrelated Python apps.
    code="import os,signal,psutil; root=os.getcwd(); targets=[p for p in psutil.process_iter(['cmdline','cwd']) if p.info['cwd']==root and 'memory_lab.gateway' in (p.info['cmdline'] or [])]; [os.kill(p.pid,signal.SIGTERM) for p in targets]"
    run(wsl(LINUX_PY,'-c',code))
    print('Experiment services stopped; databases and raw evidence retained.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['setup','start','stop']);p.add_argument('--batch',default='batch-01')
    p.add_argument('--profile',default='deepseek');p.add_argument('--campaign',default='reliability-01');a=p.parse_args()
    if a.command=='start':start(a.batch,a.profile,a.campaign)
    else:globals()[a.command]()
