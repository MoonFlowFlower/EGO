"""Loopback-only UI, reusing Studio's response and same-origin security helpers."""
from __future__ import annotations
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import json,secrets,webbrowser
from ..studio.http import Handler as BaseHandler
from ..studio.protocol import parse_json

ASSETS=Path(__file__).resolve().parent/'web'
class Handler(BaseHandler):
    def do_GET(self):
        if not self._host():return self._send(403,{'error':'loopback Host required'})
        parts=urlsplit(self.path);path=parts.path
        if path=='/':return self._send(200,(ASSETS/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token),'text/html; charset=utf-8')
        if path in ('/app.js','/style.css'):
            return self._send(200,(ASSETS/path[1:]).read_bytes(),'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
        if not self._token():return self._send(403,{'error':'session token required'})
        s=self.server.service
        try:
            if path=='/api/state':return self._send(200,s.view())
            if path=='/api/export':
                with s.lock:cp=s.core.checkpoint()
                return self._send(200,cp,filename='SharedField_v05_checkpoint.json')
            if path=='/api/report':
                rid=parse_qs(parts.query).get('id',[''])[0]
                with s.lock:r=next((r for r in s.core.state['reports'] if r['id']==rid),None)
                if r is None:raise ValueError('unknown state snapshot')
                return self._send(200,r)
            return self._send(404,{'error':'not found'})
        except (ValueError,KeyError,TypeError) as e:return self._send(400,{'error':str(e)})

    def do_POST(self):
        port=self.server.server_port
        if not self._host() or not self._token() or self.headers.get('Origin') not in (f'http://localhost:{port}',f'http://127.0.0.1:{port}'):
            return self._reject(403,{'error':'same-origin request and session token required'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self._reject(415,{'error':'application/json required'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            limit=16*1024*1024 if urlsplit(self.path).path=='/api/import' else 128000
            if not 1<=n<=limit:raise ValueError('request byte budget exceeded')
            data=parse_json(self.rfile.read(n).decode('utf-8'), max_chars=limit if urlsplit(self.path).path=='/api/import' else 50000);s=self.server.service;path=urlsplit(self.path).path;r={'ok':True}
            if path=='/api/import':r=s.import_checkpoint(data.get('checkpoint',{}),data.get('archive_current',False))
            elif path=='/api/chat':s.submit(data.get('text'))
            elif path=='/api/command':s.command(data.get('kind'),data.get('payload',{}))
            elif path=='/api/advance':s.request_step()
            elif path=='/api/auto':s.start_auto(data.get('steps',8))
            elif path=='/api/pause':s.pause()
            elif path=='/api/options':r=s.set_options(data)
            elif path=='/api/config':r=s.configure(data.get('config',{}),data.get('key'),data.get('clear_key',False))
            elif path=='/api/check':r=s.check_connection()
            elif path=='/api/protocol-check':r=s.check_protocol()
            elif path=='/api/manual':s.accept_manual(data.get('request_id'),data.get('text'))
            elif path=='/api/new':s.new_life()
            else:return self._send(404,{'error':'unknown endpoint'})
            return self._send(200,r)
        except (ValueError,KeyError,TypeError,UnicodeDecodeError,OSError) as e:return self._send(400,{'error':str(e)})

class SharedServer(ThreadingHTTPServer):
    allow_reuse_address=True;daemon_threads=True
    def __init__(self,service,port):
        super().__init__(('127.0.0.1',port),Handler);self.service=service;self.token=secrets.token_urlsafe(32)

def create_server(service,port=8773):
    if type(port) is not int or not 0<=port<=65535:raise ValueError('invalid port')
    return SharedServer(service,port)

def serve(directory,port=8773,open_browser=True):
    from .service import SharedService
    s=SharedService(directory)
    try:server=create_server(s,port)
    except Exception:s.close();raise
    s.start_worker();url='http://127.0.0.1:'+str(server.server_port)
    print('Shared Field v0.5: '+url,flush=True)
    print('State autosaves; restored paused. Built-in environment only, no real computer control. Ctrl+C stops.',flush=True)
    if open_browser:webbrowser.open(url)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:print('\nStopped; state preserved.',flush=True)
    finally:server.server_close();s.close()
