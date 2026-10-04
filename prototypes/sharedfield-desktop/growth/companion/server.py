"""AIRI-compatible input adapter. UI messages cannot become kernel authority."""
import hashlib
import json
import queue
import re
import secrets
import threading
import time
from datetime import datetime

from p7.proxy import _Handler, _LoopbackHTTPServer, ProxyError, _parse_json, _json_bytes
from .memory import Memory

PUBLIC_MODEL='ego-companion'
MIRROR_PREFIX='MC · Moonlight'


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def last_input(request):
    if not isinstance(request,dict) or request.get('model')!=PUBLIC_MODEL:
        raise ProxyError('kernel_model_required')
    if type(request.get('stream',False)) is not bool:
        raise ProxyError('invalid_stream')
    messages=request.get('messages')
    if not isinstance(messages,list) or not 1<=len(messages)<=500:
        raise ProxyError('invalid_messages')
    user=[m for m in messages if isinstance(m,dict) and m.get('role')=='user']
    if not user:raise ProxyError('user_input_required')
    text=user[-1].get('content')
    if isinstance(text,list) and all(isinstance(p,dict) and p.get('type')=='text' and isinstance(p.get('text'),str) for p in text):
        text='\n'.join(p['text'] for p in text)
    if not isinstance(text,str) or not 0<len(text.strip())<=6500:
        raise ProxyError('text_input_required')
    # History affects only the replay key; it is never sent to the model/store.
    identity=digest(json.dumps([m for m in messages if isinstance(m,dict) and m.get('role') in ('user','assistant')],ensure_ascii=False,sort_keys=True))
    # AIRI v0.12.0-beta.5 adds its public minute-resolution datetime prefix.
    # Remove only that envelope, before stop/forget/mirror classification.
    text=re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}\] ', '', text.strip(), count=1)
    return text,'airi:'+identity


class KernelServer:
    def __init__(self,engine,audit,*,port=18787,local_token=None):
        self.engine,self.audit=engine,audit
        if local_token is not None and (not isinstance(local_token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{43}',local_token)):
            raise ValueError('invalid_local_token')
        self.token=local_token if local_token is not None else secrets.token_urlsafe(32)
        self.allowed_origins=frozenset(('null','http://localhost','app://localhost','http://tauri.localhost','tauri://localhost'))
        self.httpd=_LoopbackHTTPServer(('127.0.0.1',port),Handler)
        self.httpd.owner=self
        self.base_url='http://127.0.0.1:%d/v1'%self.httpd.server_address[1]
        self._thread=None
        self._slots=threading.BoundedSemaphore(8)

    def start(self):
        self._thread=threading.Thread(target=self.httpd.serve_forever,kwargs={'poll_interval':.1},daemon=True)
        self._thread.start()

    def close(self):
        if self._thread:self.httpd.shutdown();self._thread.join(timeout=3)
        self.httpd.server_close()

    def mirror(self,event_id,text):
        # A readable timestamp distinguishes repeated identical MC inputs.
        rendered=f'{MIRROR_PREFIX}（{datetime.now().isoformat(sep=" ",timespec="microseconds")}）：{text}'
        with self.engine._turn_lock:
            m=Memory(self.engine.path)
            try:m.register_mirror(digest(rendered),event_id)
            finally:m.close()
        return rendered

    def respond(self,request,emit):
        text,identity=last_input(request)
        if text.startswith(MIRROR_PREFIX):
            with self.engine._turn_lock:
                m=Memory(self.engine.path)
                try:
                    event=m.mirror(digest(text))
                    result=m.cached(event) if event else '这条 MC 回显没有对应的内核记录，我没有执行新动作。'
                finally:m.close()
            self.audit.write('lifecycle.jsonl',{'event':'airi_replay','event_id':event,'model_called':False})
            emit(result);return result
        return self.engine.run(identity,'airi',text,emit)


class Handler(_Handler):
    server_version='EgoKernel'

    def do_OPTIONS(self):
        try:
            self._check_request(auth=False)
            if self.path not in ('/v1/models','/v1/chat/completions'):raise ProxyError('not_found',404)
            self._headers(204,'application/json',0)
        except ProxyError as error:self._error(error)

    def do_GET(self):
        try:
            self._check_request()
            if self.path!='/v1/models':raise ProxyError('not_found',404)
            self._json(200,{'object':'list','data':[{'id':PUBLIC_MODEL,'object':'model','owned_by':'ego-kernel','created':0}]})
        except ProxyError as error:self._error(error)

    def do_POST(self):
        acquired=False
        try:
            self._check_request()
            if self.path!='/v1/chat/completions':raise ProxyError('not_found',404)
            if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Encoding'):raise ProxyError('encoded_body_refused')
            sizes=self.headers.get_all('Content-Length',[])
            if len(sizes)!=1 or not sizes[0].isdigit():raise ProxyError('content_length_required',411)
            size=int(sizes[0])
            if not 0<size<=256000:raise ProxyError('ui_request_too_large',413)
            if self.headers.get_content_type()!='application/json':raise ProxyError('json_required',415)
            raw=self.rfile.read(size)
            if len(raw)!=size:raise ProxyError('incomplete_body')
            try:request=_parse_json(raw)
            except (ValueError,UnicodeError):raise ProxyError('invalid_json') from None
            last_input(request)
            acquired=self.owner._slots.acquire(blocking=False)
            if not acquired:raise ProxyError('kernel_queue_full',429)
            identity='chatcmpl-'+secrets.token_hex(12)
            base={'id':identity,'created':int(time.time()),'model':PUBLIC_MODEL}
            if not request.get('stream'):
                result=self.owner.respond(request,lambda _:None)
                self._json(200,{**base,'object':'chat.completion','choices':[{'index':0,'message':{'role':'assistant','content':result},'finish_reason':'stop'}]})
                return
            output=queue.Queue()
            def work():
                try:self.owner.respond(request,lambda s:output.put(('text',s)))
                except Exception:output.put(('text','内核暂时无法接收这条输入；没有重试。'))
                finally:output.put(('end',None))
            threading.Thread(target=work,daemon=True).start()
            self._headers(200,'text/event-stream; charset=utf-8')
            def chunk(delta,finish=None):
                value={**base,'object':'chat.completion.chunk','choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
                self.wfile.write(b'data: '+_json_bytes(value)+b'\n\n');self.wfile.flush()
            chunk({'role':'assistant'})
            first=True
            while True:
                try:kind,value=output.get(timeout=5)
                except queue.Empty:
                    self.wfile.write(b': keepalive\n\n');self.wfile.flush();continue
                if kind=='end':break
                chunk({'content':('' if first else '\n')+value});first=False
            chunk({},'stop');self.wfile.write(b'data: [DONE]\n\n');self.wfile.flush()
        except ProxyError as error:
            self.owner.audit.write('http.jsonl',{'event':'rejected','code':error.code})
            self._error(error)
        except (OSError,ConnectionError):
            # A disconnected display does not replay or duplicate the canonical turn.
            self.owner.audit.write('http.jsonl',{'event':'client_disconnected'})
        finally:
            if acquired:self.owner._slots.release()
