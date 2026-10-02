"""Loopback UI. Only selected local operations; no arbitrary paths, SQL or shell."""
from __future__ import annotations
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import json,secrets,sqlite3,webbrowser
from ..studio.http import Handler as BaseHandler
from ..studio.protocol import parse_json
ASSETS=Path(__file__).resolve().parent/'web'
class Handler(BaseHandler):
    def do_GET(self):
        if not self._host():return self._send(403,{'error':'loopback Host required'})
        parts=urlsplit(self.path);path=parts.path
        if path=='/':return self._send(200,(ASSETS/'index.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token),'text/html; charset=utf-8')
        if path=='/reading':return self._send(200,(ASSETS/'reading.html').read_text(encoding='utf-8').replace('__TOKEN__',self.server.token),'text/html; charset=utf-8')
        if path in ('/app.js','/style.css','/reading.js','/reading.css'):
            return self._send(200,(ASSETS/path[1:]).read_bytes(),'text/javascript; charset=utf-8' if path.endswith('.js') else 'text/css; charset=utf-8')
        if not self._token():return self._send(403,{'error':'session token required'})
        s=self.server.service;q=parse_qs(parts.query)
        def one(key,default=''):return q.get(key,[default])[0]
        try:
            with s.lock:
                if path=='/api/state':r=s.view()
                elif path=='/api/reading':r=s.reading_view()
                elif path=='/api/export':return self._send(200,s.store.export(),filename='SharedField_v06_checkpoint.json')
                elif path=='/api/source':r=s.store.observation(one('id'))
                elif path=='/api/search':r=s.store.search(one('q'),limit=int(one('limit','12')),offset=int(one('offset','0')))
                elif path=='/api/history':r=s.store.recent(limit=int(one('limit','40')),offset=int(one('offset','0')))
                elif path=='/api/commitments':r=s.store.commitments(limit=int(one('limit','30')),offset=int(one('offset','0')),include_closed=one('closed')=='1')
                elif path=='/api/versions':r={'items':s.store.versions(one('id'))}
                elif path=='/api/claims':r=s.store.claims(scope=one('scope','personal'),limit=int(one('limit','30')),offset=int(one('offset','0')))
                elif path=='/api/context':r=s.last_context or {'note':'尚未构建语言上下文'}
                else:return self._send(404,{'error':'not found'})
            return self._send(200,r)
        except (ValueError,KeyError,TypeError,sqlite3.Error) as e:return self._send(400,{'error':str(e)})
    def do_POST(self):
        port=self.server.server_port
        if not self._host() or not self._token() or self.headers.get('Origin') not in (f'http://localhost:{port}',f'http://127.0.0.1:{port}'):
            return self._reject(403,{'error':'same-origin request and session token required'})
        if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self._reject(415,{'error':'application/json required'})
        try:
            path=urlsplit(self.path).path;limit=128*1024*1024 if path=='/api/import' else 180000
            n=int(self.headers.get('Content-Length','0'))
            if not 1<=n<=limit:raise ValueError('request byte limit exceeded')
            data=parse_json(self.rfile.read(n).decode('utf-8'),max_chars=limit);s=self.server.service;r={'ok':True}
            if path=='/api/chat':r={'ok':True,'source':s.submit(data.get('text'))['id']}
            elif path=='/api/reading':r=s.reading_command(data)
            elif path=='/api/background':s.start_background()
            elif path=='/api/pause':s.pause()
            elif path=='/api/advance':s.request_step()
            elif path=='/api/auto':s.start_auto(data.get('steps',8))
            elif path=='/api/world':s.world_command(data.get('kind'),data.get('payload',{}))
            elif path=='/api/options':r=s.set_options(data)
            elif path=='/api/memory-settings':r=s.set_memory_settings(data)
            elif path=='/api/config':r=s.configure(data.get('config',{}),data.get('key'),data.get('clear_key',False))
            elif path=='/api/check':r=s.check_connection()
            elif path=='/api/grant':r=s.grant_calls(data.get('count'))
            elif path=='/api/manual':s.accept_manual(data.get('request_id'),data.get('text'))
            elif path=='/api/resume-turn':s.resume_turn(data.get('source'))
            elif path=='/api/commitment':r=s.edit_commitment(data)
            elif path=='/api/feedback':r=s.give_feedback(data.get('contact'),data.get('outcome'),data.get('explanation'))
            elif path=='/api/backup':r=s.backup()
            elif path=='/api/import':r=s.import_checkpoint(data.get('checkpoint'),data.get('archive_current',False))
            elif path=='/api/forget':r=s.forget(data.get('source_ids'),data.get('confirmed',False))
            elif path=='/api/replay':
                with s.lock:r=s._commit('replay',{})['result']
            elif path=='/api/reindex':
                with s.lock:s.store.reindex()
            else:return self._send(404,{'error':'unknown local endpoint'})
            return self._send(200,r)
        except (ValueError,KeyError,TypeError,UnicodeDecodeError,OSError,sqlite3.Error) as e:return self._send(400,{'error':str(e)})
class MemoryServer(ThreadingHTTPServer):
    allow_reuse_address=True;daemon_threads=True
    def __init__(self,service,port):
        super().__init__(('127.0.0.1',port),Handler);self.service=service;self.token=secrets.token_urlsafe(32)
def create_server(service,port=8774):
    if type(port) is not int or not 0<=port<=65535:raise ValueError('invalid port')
    return MemoryServer(service,port)
def serve(directory,port=8774,open_browser=True):
    from .service import MemoryService
    service=MemoryService(directory)
    try:server=create_server(service,port)
    except BaseException:service.close();raise
    service.start_worker();url=f'http://127.0.0.1:{server.server_port}'
    print('SharedField Memory v0.7: '+url,flush=True)
    print('Local memory: '+str(service.session_path.resolve()),flush=True)
    print('Starts paused. No paid background until enabled. Ctrl+C stops. Keep backups.',flush=True)
    if open_browser:webbrowser.open(url)
    try:server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:print('\nStopped; memory retained.',flush=True)
    finally:server.server_close();service.close()
