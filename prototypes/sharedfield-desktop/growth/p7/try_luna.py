"""Frozen, no-retry Luna trial. Uses original transport probes and Ua B scripts."""
import argparse
import json
import math
import os
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

from growthlab.models import read_key
from u1.harness import Client, Stop
from u1.plan import verify
from u1.run import worker_ua, ua_summary
from .luna import MODEL, ROUTE, LunaTransport, prepare_luna
from .proxy import ROOT, ProxyServer
from .smoke_routing import PROMPTS, inspect_response, sha, write_new

BASE = ROOT / 'runs/luna/live_v1'
OUT = ROOT / 'evidence/luna'
MANIFEST = OUT / 'frozen_v1.json'
EXTRA_SOURCES = ['p7/luna.py', 'p7/test_luna.py', 'p7/try_luna.py', 'evidence/luna/PRE_RUN.md']


def previous_freezes():
    u1 = json.loads((ROOT/'evidence/u1/frozen_v1.json').read_bytes())
    verify(u1)
    sources = {**u1['source_sha256'], **u1['artifact_sha256']}
    for version in [1, 2]:
        path = ROOT/f'evidence/routing/frozen_v{version}.json'
        frozen = json.loads(path.read_bytes())
        if any(sha(ROOT/p)!=h for p,h in frozen['sources'].items()):
            raise RuntimeError('previous_frozen_source_changed')
        sources.update(frozen['sources'])
    return sources


def freeze():
    sources = previous_freezes()
    sources.update({p:sha(ROOT/p) for p in EXTRA_SOURCES})
    sources['growthlab/records.py'] = sha(ROOT/'growthlab/records.py')
    write_new(MANIFEST, {'version':'luna-trial-v1','created_utc':datetime.now(timezone.utc).isoformat(),
        'source_sha256':sources,'model':MODEL,'route':ROUTE,'reasoning_effort':'none','temperature':'omitted',
        'smoke_prompts':PROMPTS,'description':'Original Ua B-only 90 decisions; not full U1',
        'max_attempts':93,'wall_limit_seconds':900,'additional_budget_usd':.50,'latency_p95_limit_s':10,
        'preflight_metadata_sha256':sha(ROOT/'runs/luna/preflight/zdr.json'),
        'source_paths_unchanged':True,'automatic_fallback':False,'retry_count':0})
    print(json.dumps({'manifest_sha256':sha(MANIFEST),'source_files':len(sources)}))


class TrialClient:
    check_resources = Client.check_resources
    parsed = Client.parsed

    def __init__(self, server, manifest):
        self.server, self.manifest = server, manifest
        self.folder = BASE/'ua_b'
        self.folder.mkdir()
        self.started = time.time()
        self.previous_sample = 0
        self.invalid_streak = 0
        self.calls = 0
        self.rows = []
        self.before_budget = server.transport.ledger.total()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def log(self, row):
        self.server.audit.write('client.jsonl', {'unix_s':time.time(),'pid':os.getpid(),**row})

    def exchange(self, payload, context):
        self.check_resources()
        if time.time()-self.started > self.manifest['wall_limit_seconds']:
            raise Stop('trial_wall_limit')
        if self.calls >= self.manifest['max_attempts']:
            raise Stop('trial_attempt_limit')
        _, _, reserve = prepare_luna(payload, self.server.transport.provider)
        if self.server.transport.ledger.total()-self.before_budget+reserve > self.manifest['additional_budget_usd']:
            raise Stop('trial_additional_budget_stop')
        started = time.perf_counter()
        self.calls += 1
        row = {'attempt':self.calls, 'context':context, 'started_unix_s':time.time()}
        self.log({'record_type':'request','attempt':self.calls,'context':context,'payload':payload})
        request = urllib.request.Request(self.server.base_url+'/chat/completions',
            data=json.dumps(payload,ensure_ascii=False).encode(),
            headers={'Authorization':'Bearer '+self.server.token,'Content-Type':'application/json'})
        try:
            with self.opener.open(request,timeout=45) as response:
                raw=response.read(4_000_001)
                row['http_status']=response.status
            events=[json.loads(line) for line in (self.server.audit.path/'events.jsonl').read_text().splitlines()]
            event=next(e for e in reversed(events) if e.get('endpoint')=='chat')
            row.update(charge_id=event.get('charge_id'),cost_usd=event.get('cost_usd'))
            if event['outcome']!='completed':
                raise Stop('proxy_protocol_failure')
            return raw, row
        except urllib.error.HTTPError as error:
            row.update(http_status=error.code,error='http_'+str(error.code))
            error.close()
            raise Stop(row['error']) from None
        except (urllib.error.URLError,TimeoutError,ConnectionError):
            row['error']='connection_error'
            raise Stop('connection_error') from None
        finally:
            row['latency_s']=round(time.perf_counter()-started,4)
            self.rows.append(row)
            self.log({'record_type':'attempt_result',**row})

    def call(self, messages, schema, context, **kwargs):
        raw,row=self.exchange({'model':MODEL,'messages':messages,'response_format':schema,
                               'max_completion_tokens':1024,'reasoning_effort':'none'},context)
        try:
            result=json.loads(raw)
            content=result['choices'][0]['message']['content']
            row.update(actual_model=result.get('model'),actual_provider=result.get('provider'),usage=result.get('usage'))
            if result.get('model')!=MODEL or not str(result.get('provider','')).casefold().startswith('azure'):
                raise Stop('unexpected_model_or_provider')
            cost=result.get('usage',{}).get('cost')
            if isinstance(cost,bool) or not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost<0:
                raise Stop('missing_usage_cost')
        except (ValueError,KeyError,TypeError):
            raise Stop('invalid_response_envelope') from None
        self.log({'record_type':'response','context':context,'output':content,'meta':row})
        if self.calls%15==0:
            print(json.dumps({'completed_attempts':self.calls,'latest_latency_s':row['latency_s'],
                              'additional_ledger_usd':self.server.transport.ledger.total()-self.before_budget}),flush=True)
        return content,row


def run():
    manifest=json.loads(MANIFEST.read_bytes())
    if any(sha(ROOT/p)!=h for p,h in manifest['source_sha256'].items()):
        raise RuntimeError('frozen_source_changed')
    BASE.mkdir(parents=True,exist_ok=False)
    transport=LunaTransport(api_key=read_key(),log_dir=BASE/'proxy')
    result={'manifest_sha256':sha(MANIFEST),'smoke':[],'status':'started','stopped':None,'claim':'supplied_convention_and_transport_only'}
    with ProxyServer(transport,log_dir=BASE/'proxy') as server:
        client=TrialClient(server,manifest)
        try:
            for probe in manifest['smoke_prompts']:
                raw,row=client.exchange({'model':MODEL,'reasoning_effort':'none','max_completion_tokens':512,**probe['request']},
                                        {'phase':'smoke','kind':probe['kind']})
                valid,details=inspect_response(probe['kind'],raw)
                row.update(details)
                passed=valid and details['actual_model']==MODEL and str(details['actual_provider']).casefold().startswith('azure')
                result['smoke'].append({'kind':probe['kind'],'pass':passed,**row})
                print(json.dumps({'probe':probe['kind'],'pass':passed,'latency_s':row['latency_s'],'cost_usd':row.get('cost_usd')}),flush=True)
                if not passed:
                    raise Stop('smoke_failed')
            data=json.loads((ROOT/'evidence/u1/scripts_v1.json').read_bytes())
            result['ua_b']=worker_ua({'folder':str(client.folder),'main_comparison':False,'config_name':'luna_trial_v1'},data,client)
            result['status']='completed'
        except Stop as error:
            result['status']='stopped'
            result['stopped']=str(error)
        except Exception as error:
            result['status']='stopped'
            result['stopped']=type(error).__name__
        if 'ua_b' not in result:
            result['ua_b']=ua_summary(client.folder,90)
        decisions_path=client.folder/'decisions.jsonl'
        decisions=[json.loads(line) for line in decisions_path.read_text(encoding='utf-8').splitlines()] if decisions_path.exists() else []
        latencies=sorted(row['latency_s'] for row in client.rows if row['context']['phase']=='Ua' and row.get('http_status')==200)
        duration=time.time()-client.started
        p95=latencies[math.ceil(.95*len(latencies))-1] if latencies else None
        result.update(attempts=client.rows,attempt_count=client.calls,wall_s=round(duration,4),
            observed_requests_per_minute=round(client.calls/duration*60,2),
            description_protocol_valid=sum(bool(r['valid']) for r in decisions),
            description_latency_s={'p50':statistics.median(latencies) if latencies else None,'p95':p95,'max':max(latencies) if latencies else None},
            http_429_count=sum(r.get('http_status')==429 for r in client.rows),budget_before_usd=client.before_budget,
            budget_after_usd=transport.ledger.total(),additional_reserved_or_reported_usd=transport.ledger.total()-client.before_budget,
            reported_cost_usd=sum(r.get('cost_usd') or 0 for r in client.rows),temperature='omitted',reasoning_effort='none')
        result['candidate_criterion_pass']=bool(result['status']=='completed' and len(result['smoke'])==3
            and all(p['pass'] for p in result['smoke']) and len(decisions)==90 and all(d['valid'] for d in decisions)
            and result['ua_b']['pass'] and p95 is not None and p95<=manifest['latency_p95_limit_s'])
    result.update(temporary_proxy_closed=True,generated_tools_executed=0,product_defaults_changed=False,u1_v1_changed=False)
    write_new(OUT/'live_v1.json',result)
    write_new(OUT/'decisions_v1.json',decisions)
    print(json.dumps({k:result[k] for k in ['status','stopped','candidate_criterion_pass','attempt_count','http_429_count',
        'description_protocol_valid','description_latency_s','reported_cost_usd','additional_reserved_or_reported_usd','budget_after_usd']}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['freeze','run'])
    args=parser.parse_args()
    freeze() if args.action=='freeze' else run()
