"""Loopback-only UI and action API; no external application access."""
from __future__ import annotations
import argparse
import json
import mimetypes
from pathlib import Path
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlparse,unquote,parse_qs
from .life import Life
from .dialogue import respond,compose_letter

ROOT=Path(__file__).resolve().parent


def serve(data,port,letter_writer=compose_letter,enable_life_sharing=True):
    life=Life(data,enable_life_sharing=enable_life_sharing);token=secrets.token_urlsafe(32);chat_lock=threading.Lock()
    lease={'seen':0.,'tick':time.monotonic()};lease_lock=threading.Lock()
    completed={}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def send(self,value,status=200,content_type='application/json; charset=utf-8'):
            body=value if isinstance(value,bytes) else json.dumps(value,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff');self.end_headers()
            try:self.wfile.write(body)
            except (BrokenPipeError,ConnectionResetError):pass
        def trusted_host(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def do_GET(self):
            if not self.trusted_host():return self.send({'error':'Local host required'},403)
            route=unquote(urlparse(self.path).path)
            if route=='/api/state':return self.send(life.snapshot())
            if route=='/api/health':return self.send({'app':'ego-desktop-pet','version':4})
            if route=='/api/note':
                try:return self.send(life.read_note(parse_qs(urlparse(self.path).query).get('name',['给悠小喵的便签.txt'])[0]))
                except (ValueError,UnicodeError) as exc:return self.send({'error':str(exc)},400)
            if route=='/api/export':return self.send(life.snapshot())
            if route=='/':
                html=(ROOT/'web/index.html').read_text(encoding='utf-8').replace('__TOKEN__',token)
                return self.send(html.encode(),content_type='text/html; charset=utf-8')
            if route=='/assets/atlas.png':path=ROOT.parent/'desktop_pet_assets/v1/original_companion_atlas.png'
            else:
                base=ROOT/'local_assets' if route.startswith('/model/') else ROOT/'web'
                relative=route.removeprefix('/model/') if route.startswith('/model/') else route.lstrip('/')
                path=(base/relative).resolve()
                if not path.is_relative_to(base.resolve()):return self.send({'error':'Not found'},404)
            if not path.is_file():return self.send({'error':'Not found'},404)
            return self.send(path.read_bytes(),content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
        def do_POST(self):
            if not self.trusted_host() or self.headers.get('X-Pet-Token')!=token:return self.send({'error':'Local session required'},403)
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):return self.send({'error':'Same origin required'},403)
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<0 or length>32768:raise ValueError('请求太长啦')
                body=json.loads(self.rfile.read(length) or b'{}')
                route=urlparse(self.path).path
                if route=='/api/note':return self.send(life.save_note(body['name'],body['text'],body.get('version')))
                if route=='/api/heartbeat':
                    with lease_lock:lease['seen']=time.monotonic()
                    return self.send({'ok':True})
                if route=='/api/pause':
                    with lease_lock:lease['seen']=0
                    return self.send({'ok':True})
                if route=='/api/action':return self.send(life.command(body['action'],body.get('data'),body.get('id')))
                if route=='/api/forget':life.forget(body['source']);return self.send(life.snapshot())
                if route=='/api/chat':
                    text=body.get('text','').strip();rid=body.get('id','')
                    if not text or len(text)>2000 or not rid or len(rid)>100:raise ValueError('请输入1到2000字')
                    if not chat_lock.acquire(blocking=False):return self.send({'error':'上一句话还在回复，稍等一下'},409)
                    try:
                        if rid in completed:return self.send(completed[rid])
                        existing=[m for m in life.snapshot()['messages'] if m['id']==rid+'-reply']
                        if existing:return self.send({'reply':existing[0]['text'],'mode':'model'})
                        # A prior dispatch without a saved reply is ambiguous. Never replay it.
                        if any(m['id']==rid for m in life.snapshot()['messages']):return self.send({'error':'这句话已提交过，未自动重复发送'},409)
                        completed[rid]=respond(life,text,rid)
                        return self.send(completed[rid])
                    finally:chat_lock.release()
                return self.send({'error':'Not found'},404)
            except (ValueError,KeyError,RuntimeError) as exc:return self.send({'error':str(exc)},400)
            except Exception as exc:return self.send({'error':'暂时没能完成这一步（'+type(exc).__name__+'），存档仍在。'},500)

    def tick():
        while True:
            time.sleep(1)
            with lease_lock:
                now=time.monotonic();elapsed=now-lease['tick'];lease['tick']=now
                live=now-lease['seen']<8 and elapsed<3
            if live:life.advance(elapsed)
    def letters():
        while True:
            time.sleep(1)
            with lease_lock:live=time.monotonic()-lease['seen']<8
            if not live or not chat_lock.acquire(blocking=False):continue
            try:
                job=life.claim_letter_job()
                if not job:continue
                try:life.finish_letter_job(job['id'],text=letter_writer(life,job))
                except Exception as exc:life.finish_letter_job(job['id'],error=str(exc) if isinstance(exc,RuntimeError) else '这次回信中断了，没有自动重发。')
            finally:chat_lock.release()
    httpd=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    threading.Thread(target=tick,daemon=True).start()
    threading.Thread(target=letters,daemon=True).start()
    print(f'EGO desktop pet: http://127.0.0.1:{port}',flush=True)
    httpd.serve_forever()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=18180)
    parser.add_argument('--data',default=str(ROOT/'data'))
    parser.add_argument('--experimental-life-sharing',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--no-life-sharing',action='store_true',help='关闭生活创作信，仅保留便签回信')
    args=parser.parse_args()
    if args.experimental_life_sharing and Path(args.data).resolve()==(ROOT/'data').resolve():parser.error('实验生活分享只能使用 --data 指定隔离目录')
    serve(args.data,args.port,enable_life_sharing=not args.no_life_sharing)
