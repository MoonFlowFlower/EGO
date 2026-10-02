"""Actual app HTTP -> actual compatible HTTP server; language server is TEST FIXTURE."""
import json,threading,tempfile,unittest,urllib.request
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from switchlab.memory.http import create_server
from switchlab.memory.service import MemoryService
from switchlab.memory.store import MemoryStore
from tests.test_memory_service import Fixture
from tests.test_memory_store import NOW

class ProviderHTTPFixture(BaseHTTPRequestHandler):
    def log_message(self,*a):pass
    def do_POST(self):
        data=json.loads(self.rfile.read(int(self.headers['Content-Length'])));self.server.requests.append(data)
        if self.path!='/v1/chat/completions':self.send_error(404);return
        try:r=self.server.fixture.complete(data['messages'])
        except (KeyError,json.JSONDecodeError):r={'packet':{'speech':'TEST FIXTURE connection'},'model':'TEST_FIXTURE','usage':{'input_tokens':1,'output_tokens':1}}
        body=json.dumps({'model':r['model'],'choices':[{'message':{'content':json.dumps(r['packet'],ensure_ascii=False)},'finish_reason':'stop'}],
             'usage':{'prompt_tokens':r['usage']['input_tokens'],'completion_tokens':r['usage']['output_tokens']}},ensure_ascii=False).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)

def provider_server():
    server=ThreadingHTTPServer(('127.0.0.1',0),ProviderHTTPFixture);server.fixture=Fixture();server.requests=[]
    t=threading.Thread(target=server.serve_forever,daemon=True);t.start();return server,t

class PipelineTests(unittest.TestCase):
    def test_two_http_hops_commit_recall_contact_and_replay(self):
        with tempfile.TemporaryDirectory() as t:
            clock=[NOW];s=MemoryService(t,clock=lambda:clock[0]);provider,pt=provider_server();app=create_server(s,0)
            at=threading.Thread(target=app.serve_forever,daemon=True);at.start();base=f'http://127.0.0.1:{app.server_port}'
            def request(path,body=None):
                headers={'X-SwitchLab-Token':app.token};raw=None
                if body is not None:raw=json.dumps(body).encode();headers.update(Origin=base);headers['Content-Type']='application/json'
                with urllib.request.urlopen(urllib.request.Request(base+path,raw,headers),timeout=10) as r:return json.load(r)
            try:
                request('/api/config',{'config':{'mode':'api','base_url':f'http://127.0.0.1:{provider.server_port}/v1','model':'TEST_FIXTURE'},'key':'TEST_NOT_A_REAL_SECRET'})
                request('/api/options',{'language_mode':'api'});request('/api/chat',{'text':'测试夹具：1分钟后一起看星空'});s.run_once();s.run_once()
                v=request('/api/state');self.assertEqual(v['commitments']['total'],1);self.assertEqual(len(provider.requests),2)
                clock[0]+=65;request('/api/background',{});s.run_once();self.assertEqual(len(provider.requests),3)
                self.assertIn('现在方便开始吗',request('/api/state')['messages'][-1]['text'])
                cp=request('/api/export');self.assertNotIn('TEST_NOT_A_REAL_SECRET',json.dumps(cp))
                replay=MemoryStore.from_export(Path(t)/'replay.db',cp)
                try:self.assertEqual(replay.projection_digest(),s.store.projection_digest())
                finally:replay.close()
            finally:app.shutdown();app.server_close();provider.shutdown();provider.server_close();s.close();at.join(2);pt.join(2)
