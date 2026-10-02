"""Real two-hop HTTP; model side is an explicitly identified deterministic fixture."""
import unittest,json,threading,tempfile,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from switchlab.shared.service import SharedService
from switchlab.shared.http import create_server
from switchlab.studio.provider import Provider,DEFAULT

class SharedModelHTTPFixture(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        d=json.loads(body['messages'][-1]['content']);self.server.received.append({'path':self.path,'phase':d['phase']})
        if d['phase']=='interpret':packet={'reports':[],'request':{'kind':'none'}}
        else:packet={'state_id':d['state_id'],'speech':'【HTTP TEST FIXTURE · 非真实模型】从指定状态快照返回的测试文本。'}
        payload=json.dumps({'model':'SHARED_HTTP_TEST_FIXTURE','choices':[{'finish_reason':'stop','message':{'content':json.dumps(packet,ensure_ascii=False)}}],
            'usage':{'prompt_tokens':12,'completion_tokens':8}}).encode()
        self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(payload)));self.end_headers();self.wfile.write(payload)

class SharedPipelineTests(unittest.TestCase):
    def test_browser_client_to_app_to_provider_back_to_persistent_state(self):
        endpoint=ThreadingHTTPServer(('127.0.0.1',0),SharedModelHTTPFixture);endpoint.received=[]
        t=threading.Thread(target=endpoint.serve_forever,daemon=True);t.start()
        try:
            with tempfile.TemporaryDirectory() as d:
                p=Provider({**DEFAULT,'mode':'api','model':'SHARED_HTTP_TEST_FIXTURE','base_url':f'http://127.0.0.1:{endpoint.server_port}/v1'})
                s=SharedService(d,provider=p);app=create_server(s,0);a=threading.Thread(target=app.serve_forever,daemon=True);a.start()
                base=f'http://127.0.0.1:{app.server_port}'
                def request(path,data=None):
                    h={'X-SwitchLab-Token':app.token}
                    if data is not None:h.update(Origin=base,**{'Content-Type':'application/json'});data=json.dumps(data).encode()
                    with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers=h),timeout=5) as r:return json.load(r)
                try:
                    request('/api/options',{'language_mode':'api'})
                    request('/api/command',{'kind':'player_action','payload':{'action':{'kind':'survey'}}})
                    request('/api/chat',{'text':'我们刚才发现了什么，你现在有什么感觉？'})
                    s.run_once();s.run_once();v=request('/api/state');cp=request('/api/export')
                    self.assertEqual(endpoint.received,[{'path':'/v1/chat/completions','phase':'interpret'},{'path':'/v1/chat/completions','phase':'express'}])
                    self.assertEqual(v['world']['tick'],1);self.assertIn('HTTP TEST FIXTURE',v['messages'][-1]['text'])
                    self.assertEqual(cp['state']['calls'],2)
                    from switchlab.shared.core import SharedCore
                    self.assertEqual(cp,SharedCore.restore(cp).checkpoint())
                finally:app.shutdown();app.server_close();s.close();a.join(2)
        finally:endpoint.shutdown();endpoint.server_close();t.join(2)
