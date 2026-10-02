"""Loopback browser UI; tokens/Origin checks and no arbitrary file endpoint."""
from __future__ import annotations
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
import json
import secrets
import threading
import webbrowser
from .protocol import parse_json

ASSETS=Path(__file__).resolve().parent/'web'


class StudioServer(ThreadingHTTPServer):
    allow_reuse_address=True
    daemon_threads=True
    def __init__(self,service,port):
        super().__init__(('127.0.0.1',port),Handler)
        self.service=service;self.token=secrets.token_urlsafe(32)


from ..http_util import RejectBodyMixin

class Handler(RejectBodyMixin,BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def _send(self,status,data,kind='application/json; charset=utf-8',filename=None):
        if isinstance(data,(dict,list)):data=json.dumps(data,ensure_ascii=False,allow_nan=False).encode('utf-8')
        if isinstance(data,str):data=data.encode('utf-8')
        self.send_response(status)
        for k,v in {'Content-Type':kind,'Content-Length':str(len(data)),'Cache-Control':'no-store',
          'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer',
          'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"}.items():self.send_header(k,v)
        if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
        self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass
    def _host(self):
        p=self.server.server_port
        return self.headers.get('Host') in (f'localhost:{p}',f'127.0.0.1:{p}')
    def _token(self):return secrets.compare_digest(self.headers.get('X-SwitchLab-Token',''),self.server.token)
    def do_GET(self):
        if not self._host():return self._send(403,{'error':'loopback Host required'})
        parts=urlsplit(self.path);path=parts.path
        if path=='/':return self._send(200,(ASSETS/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token),'text/html; charset=utf-8')
        if path in ('/app.js','/style.css'):
            kind='text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8'
            return self._send(200,(ASSETS/path[1:]).read_bytes(),kind)
        if not self._token():return self._send(403,{'error':'session token required'})
        service=self.server.service
        try:
            if path=='/api/state':return self._send(200,service.view())
            if path=='/api/export':
                with service.lock:data=service.core.checkpoint()
                return self._send(200,data,filename='SwitchLab_Studio_checkpoint.json')
            if path=='/api/artifact':
                aid=parse_qs(parts.query).get('id',[''])[0]
                with service.lock:a=service.core._artifact(aid)
                return self._send(200,a['content'],'text/markdown; charset=utf-8',filename=a['id']+'.md')
            return self._send(404,{'error':'not found'})
        except (ValueError,KeyError):return self._send(400,{'error':'invalid local resource'})
    def do_POST(self):
        p=self.server.server_port
        if not self._host() or not self._token() or self.headers.get('Origin') not in (f'http://localhost:{p}',f'http://127.0.0.1:{p}'):
            return self._reject(403,{'error':'same-origin request and session token required'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self._reject(415,{'error':'application/json required'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 1<=n<=256000:raise ValueError('request byte budget is 256000')
            raw=self.rfile.read(n).decode('utf-8')
            data=json.loads(raw)
            if not isinstance(data,dict):raise ValueError('JSON object required')
            s=self.server.service;path=urlsplit(self.path).path
            if path=='/api/chat':s.submit(data.get('text'));result={'ok':True}
            elif path=='/api/advance':s.request_step();result={'ok':True}
            elif path=='/api/auto':s.start_auto(data.get('steps',6));result={'ok':True}
            elif path=='/api/pause':s.pause();result={'ok':True}
            elif path=='/api/manual':s.accept_manual(data.get('request_id'),data.get('text'));result={'ok':True}
            elif path=='/api/command':s.command(data.get('kind'),data.get('payload',{}));result={'ok':True}
            elif path=='/api/config':result=s.configure(data.get('config',{}),data.get('key'),data.get('clear_key',False))
            elif path=='/api/models':result={'models':s.provider.models()}
            elif path=='/api/check':result=s.check_connection()
            elif path=='/api/protocol-check':result=s.check_protocol()
            elif path=='/api/new':s.new_life();result={'ok':True}
            else:return self._send(404,{'error':'unknown endpoint'})
            return self._send(200,result)
        except (ValueError,KeyError,TypeError,UnicodeDecodeError,json.JSONDecodeError,OSError) as e:
            return self._send(400,{'error':str(e)})


def create_server(service,port=8770):
    if type(port) is not int or not 0<=port<=65535:raise ValueError('invalid port')
    return StudioServer(service,port)


def serve(directory,port=8771,open_browser=True):
    from .adaptive_service import AdaptiveService
    service=AdaptiveService(directory)
    try:server=create_server(service,port)
    except Exception:service.close();raise
    service.start_worker()
    url=f'http://127.0.0.1:{server.server_port}'
    print('SwitchLab Adaptive Studio v0.3: '+url,flush=True)
    print('Local sandbox only. State autosaves. No remote call before configuration/use. Ctrl+C stops.',flush=True)
    if open_browser:webbrowser.open(url)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:print('\nStopped. State retained in '+str(service.directory),flush=True)
    finally:server.server_close();service.close()
