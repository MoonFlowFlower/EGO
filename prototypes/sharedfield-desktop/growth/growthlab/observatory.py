"""Observer process: copied snapshots + bounded control messages, no live Env."""
import copy,json,queue,secrets,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from .records import ROOT

class Mailbox:
    def __init__(self,output):self.output=output;self.latest=None;self.lock=threading.Lock()
    def read(self):
        with self.lock:
            while True:
                try:self.latest=self.output.get_nowait()
                except queue.Empty:break
            return copy.deepcopy(self.latest)

def make_server(mailbox,controls,formal=False,port=8766):
    token=secrets.token_urlsafe(24);origin=f'http://127.0.0.1:{port}'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def reply(self,data,status=200,kind='application/json'):
            body=data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode()
            self.send_response(status);self.send_header('Content-Type',kind+'; charset=utf-8')
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Security-Policy',"frame-ancestors 'none'");self.end_headers();self.wfile.write(body)
        def local(self):
            return self.client_address[0]=='127.0.0.1' and self.headers.get('Host')==f'127.0.0.1:{port}' and self.headers.get('Origin',origin)==origin and self.headers.get('Sec-Fetch-Site')!='cross-site'
        def do_GET(self):
            if not self.local():return self.reply({'error':'source_denied'},403)
            if self.path=='/':return self.reply((ROOT/'web/index.html').read_text(encoding='utf-8').replace('__TOKEN__',token).encode(),kind='text/html')
            if self.headers.get('X-Control')!=token:return self.reply({'error':'session_denied'},403)
            if self.path=='/api/state':return self.reply(mailbox.read())
            return self.reply({'error':'not_found'},404)
        def do_POST(self):
            if formal:return self.reply({'error':'formal_read_only'},403)
            if not self.local() or self.headers.get('Origin')!=origin or self.headers.get('X-Control')!=token:return self.reply({'error':'control_denied'},403)
            if self.path!='/api/control':return self.reply({'error':'not_found'},404)
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0<size<=256:raise ValueError('body_size')
                command=json.loads(self.rfile.read(size))
                if not isinstance(command,dict) or len(command)!=1 or set(command)-{'mode','action'}:raise ValueError('schema')
                if 'mode' in command and command['mode'] not in ('agent','human'):raise ValueError('mode')
                if 'action' in command:
                    actions=(mailbox.read() or {}).get('observation',{}).get('actions',[])
                    if command['action'] not in actions:raise ValueError('action')
                controls.put_nowait(command)
            except (ValueError,TypeError,KeyError,queue.Full):return self.reply({'error':'command_denied'},400)
            self.reply({'queued':True})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler);server.session_token=token
    return server
