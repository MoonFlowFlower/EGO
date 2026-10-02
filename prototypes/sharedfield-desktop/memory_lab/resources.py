"""Bounded resource sampling; reports sampled peaks, not unobserved exact maxima."""
import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path
import psutil
from .provider import ROOT

def main():
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=14400);a=p.parse_args()
    path=ROOT/'runs/resource-samples.jsonl';stop=ROOT/'state/stop-resource-monitor'
    deadline=time.monotonic()+a.seconds
    with path.open('a',encoding='utf-8') as out:
        while time.monotonic()<deadline and not stop.exists():
            row={'time':time.time(),'kind':'WSL','system_used_bytes':psutil.virtual_memory().used}
            try:
                with urllib.request.urlopen('http://127.0.0.1:18765/health',timeout=2) as r:row['scope']=json.load(r)['scope']
                processes=[]
                for proc in psutil.process_iter(['pid','cmdline','memory_info']):
                    cmd=' '.join(proc.info['cmdline'] or [])
                    if 'memory_lab.gateway' in cmd and proc.name().startswith('python'):
                        processes.append({'pid':proc.pid,'rss':proc.info['memory_info'].rss})
                row['gateway_processes']=processes
                result=subprocess.run(['docker','stats','--no-stream','--format','{{json .}}','ego-memory-db','ego-memory-hindsight'],capture_output=True,text=True,timeout=8)
                row['containers']=[json.loads(line) for line in result.stdout.splitlines()]
            except Exception as exc:row['sampling_error']=type(exc).__name__
            out.write(json.dumps(row)+'\n');out.flush();time.sleep(2)

if __name__=='__main__':main()
