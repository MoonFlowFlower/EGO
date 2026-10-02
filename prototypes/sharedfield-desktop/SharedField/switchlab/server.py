"""Loopback-only bounded dashboard. No arbitrary filesystem or shell endpoint."""
from __future__ import annotations
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit
import json
import secrets
import threading
import webbrowser
from .runtime import Session
from .world import Config
from .agent import AgentConfig

ASSETS=Path(__file__).resolve().parent/'web'

class LocalServer(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True
    def __init__(self,session,port):
        super().__init__(('127.0.0.1',port),Handler)
        self.session=session;self.token=secrets.token_urlsafe(32);self.lock=threading.RLock()

from .http_util import RejectBodyMixin

class Handler(RejectBodyMixin,BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def _send(self,status,payload,kind='application/json; charset=utf-8',download=None):
        if isinstance(payload,(dict,list)):payload=json.dumps(payload,ensure_ascii=False,allow_nan=False).encode('utf-8')
        if isinstance(payload,str):payload=payload.encode('utf-8')
        self.send_response(status);self.send_header('Content-Type',kind)
        self.send_header('Content-Length',str(len(payload)));self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        self.send_header('Referrer-Policy','no-referrer')
        if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
        self.end_headers()
        try:self.wfile.write(payload)
        except (BrokenPipeError,ConnectionResetError):pass
    def _host_ok(self):
        port=self.server.server_port
        return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
    def do_GET(self):
        if not self._host_ok():return self._send(403,{'error':'loopback Host required'})
        path=urlsplit(self.path).path
        with self.server.lock:
            if path=='/':
                html=(ASSETS/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token)
                return self._send(200,html,'text/html; charset=utf-8')
            if path in ('/app.js','/style.css'):
                kind='text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8'
                return self._send(200,(ASSETS/path[1:]).read_bytes(),kind)
            if path=='/api/state':return self._send(200,self.server.session.public_view())
            if path=='/api/export/trace':return self._send(200,self.server.session.export_trace(),download='trace.json')
            if path=='/api/export/checkpoint':return self._send(200,self.server.session.checkpoint(),download='checkpoint.json')
            return self._send(404,{'error':'not found'})
    def do_POST(self):
        if not self._host_ok():return self._reject(403,{'error':'loopback Host required'})
        port=self.server.server_port
        if self.headers.get('Origin') not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
            return self._reject(403,{'error':'same-origin request required'})
        if not secrets.compare_digest(self.headers.get('X-SwitchLab-Token',''),self.server.token):
            return self._reject(403,{'error':'invalid session token'})
        if self.path!='/api/command':return self._reject(404,{'error':'not found'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':
            return self._reject(415,{'error':'application/json required'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 1<=length<=4096:raise ValueError('request body bound is 4096 bytes')
            data=json.loads(self.rfile.read(length))
            if not isinstance(data,dict):raise ValueError('JSON object required')
            with self.server.lock:
                command=data.get('command');s=self.server.session
                if command=='step':
                    count=data.get('count',1)
                    if type(count) is not int or not 1<=count<=12:raise ValueError('step count must be 1..12')
                    count=min(count,s.world.config.horizon-s.world.observe()['tick'])
                    for _ in range(count):s.step()
                elif command=='compute':s.compute()
                elif command=='replay':s.replay_memory()
                elif command=='intervene':s.intervene(data.get('kind'))
                elif command=='reset':
                    self.server.session=Session(Config(seed=data.get('seed',41),horizon=data.get('horizon',96),
                           scenario=data.get('scenario','standard')),
                           AgentConfig(policy=data.get('policy','candidate'),planner=data.get('planner','rollout')))
                else:raise ValueError('unknown bounded command')
                result=self.server.session.public_view()
            return self._send(200,result)
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as error:
            return self._send(400,{'error':str(error)})


def create_server(session=None,port=8765):
    if type(port) is not int or not 0<=port<=65535:raise ValueError('port out of range')
    return LocalServer(session or Session(),port)


def serve(session=None,port=8765,open_browser=True):
    server=create_server(session,port)
    url=f'http://127.0.0.1:{server.server_port}'
    print(f'SwitchLab local dashboard: {url}',flush=True)
    print('Offline toy actions only. Press Ctrl+C to stop. Export checkpoint before closing.',flush=True)
    if open_browser:webbrowser.open(url)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:print('\nStopped.',flush=True)
    finally:server.server_close()
