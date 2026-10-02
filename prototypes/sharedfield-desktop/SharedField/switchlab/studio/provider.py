"""OpenAI-compatible transport. No SDK, paid retries, executable tools or fake fallback."""
from __future__ import annotations
from copy import deepcopy
import json
import socket
import urllib.request
import urllib.error
from urllib.parse import urlsplit
from .protocol import parse_json, text

DEFAULT = {'mode':'manual','base_url':'https://openrouter.ai/api/v1','model':'',
           'json_mode':True,'max_output_tokens':2400,'timeout':90,
           'token_parameter':'max_tokens','network_consent':False,'max_calls':48}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None


class Provider:
    def __init__(self, config=None, key=''):
        self.config=deepcopy(DEFAULT)
        if config:
            if not isinstance(config,dict) or set(config)-set(DEFAULT):raise ValueError('unknown provider settings')
            self.config.update(config)
        c=self.config
        if c['mode'] not in ('manual','api'):raise ValueError('provider mode must be manual or api')
        self.key=text(key,'API key',4096,True)
        if '\r' in self.key or '\n' in self.key:raise ValueError('invalid API key')
        if not isinstance(c['base_url'],str):raise ValueError('base_url must be text')
        c['base_url']=c['base_url'].strip().rstrip('/')
        u=urlsplit(c['base_url'])
        try:port=u.port
        except ValueError as e:raise ValueError('invalid provider port') from e
        self.local=u.hostname in ('127.0.0.1','localhost','::1')
        if u.username or u.password or u.query or u.fragment or not u.hostname:
            raise ValueError('base URL must not contain credentials, query or fragment')
        if u.scheme!='https' and not (u.scheme=='http' and self.local):
            raise ValueError('remote providers require HTTPS; plain HTTP is restricted to loopback')
        if c['base_url'].endswith('/chat/completions'):raise ValueError('enter base URL, not the full /chat/completions endpoint')
        for name,low,high in (('max_output_tokens',256,8192),('timeout',5,180),('max_calls',1,500)):
            if type(c[name]) is not int or not low<=c[name]<=high:raise ValueError(f'{name} must be {low}..{high}')
        for name in ('json_mode','network_consent'):
            if type(c[name]) is not bool:raise ValueError(name+' must be boolean')
        if c['token_parameter'] not in ('max_tokens','max_completion_tokens'):raise ValueError('unknown token parameter')
        c['model']=text(c['model'],'model',200,True)
        if c['mode']=='api' and not self.local and not c['network_consent']:
            raise ValueError('explicit remote-data consent is required')
        self.opener=urllib.request.build_opener(NoRedirect())

    def public(self):
        return {**deepcopy(self.config),'key_present':bool(self.key),'local_endpoint':self.local}

    def _request(self,path,payload=None):
        if self.config['mode']!='api':raise ValueError('manual exchange: paste a real model response; no synthetic reply available')
        if not self.local and not self.key:raise ValueError('remote API key is missing; no request was sent')
        headers={'Accept':'application/json','User-Agent':'SwitchLab-Studio/0.2'}
        if self.key:headers['Authorization']='Bearer '+self.key
        data=None
        if payload is not None:
            data=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8')
            if len(data)>350000:raise ValueError('request payload exceeds local byte budget')
            headers['Content-Type']='application/json'
        req=urllib.request.Request(self.config['base_url']+path,data=data,headers=headers)
        try:
            with self.opener.open(req,timeout=self.config['timeout']) as r:
                raw=r.read(1024*1024+1)
                if len(raw)>1024*1024:raise ValueError('provider response exceeds 1 MiB')
        except urllib.error.HTTPError as e:
            hints={400:'check model ID / JSON mode / output token parameter',401:'check API key',
                   402:'provider credit required',403:'provider denied access',404:'check base URL and model',
                   429:'rate or quota limit; no automatic retry',500:'provider error',502:'provider unavailable',
                   503:'provider unavailable'}
            raise ValueError(f'Provider HTTP {e.code}: '+hints.get(e.code,'request refused; redirects are not followed')) from None
        except (urllib.error.URLError,socket.timeout,TimeoutError,ConnectionError,OSError):
            raise ValueError('provider connection failed or timed out; no automatic retry; check URL/local server/proxy') from None
        try:return json.loads(raw.decode('utf-8'))
        except (UnicodeDecodeError,json.JSONDecodeError):raise ValueError('provider did not return JSON') from None

    def complete(self,messages):
        c=self.config
        if not c['model'] and c['mode']=='api':raise ValueError('set a real provider model ID first')
        payload={'model':c['model'],'messages':messages,'stream':False,c['token_parameter']:c['max_output_tokens']}
        if c['json_mode']:payload['response_format']={'type':'json_object'}
        body=self._request('/chat/completions',payload)
        try:
            choice=body['choices'][0]
            if choice.get('finish_reason')=='length':raise ValueError('model output truncated: increase output limit or reduce scope')
            content=choice['message'].get('content')
            if isinstance(content,list):content=''.join(x.get('text','') for x in content if isinstance(x,dict))
            if not isinstance(content,str) or not content.strip():raise ValueError('provider returned no text (possibly refusal/tool-only output)')
            packet=parse_json(content)
            usage=body.get('usage') or {}
            def count(name):
                x=usage.get(name,0)
                return x if type(x) is int and 0<=x<=1000000 else 0
            return {'packet':packet,'raw':content,'model':str(body.get('model',c['model']))[:200],
                    'usage':{'input_tokens':count('prompt_tokens'),'output_tokens':count('completion_tokens')}}
        except (KeyError,IndexError,TypeError):raise ValueError('unsupported chat-completions response shape') from None

    def models(self):
        data=self._request('/models')
        ids=sorted({str(x['id']) for x in data.get('data',[]) if isinstance(x,dict) and isinstance(x.get('id'),str)})
        return ids[:1500]
