import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer

class ProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.requests=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers();self.wfile.write(b'{"data":[{"id":"fixture-only"}]}')
            def do_POST(self):
                n=int(self.headers['Content-Length']);data=json.loads(self.rfile.read(n));cls.requests.append((self.path,dict(self.headers),data))
                if data['model']=='redirect':
                    self.send_response(302);self.send_header('Location','https://example.invalid/steal');self.end_headers();return
                if data['model']=='failure':
                    self.send_response(401);self.end_headers();self.wfile.write(b'Bearer super-secret echoed here');return
                if data['model']=='invalid':result={'choices':[{'message':{'content':'not JSON'}}]}
                else:result={'model':'fixture-only','choices':[{'finish_reason':'stop','message':{'content':'{"speech":"测试传输，不是实际模型。"}'}}],
                             'usage':{'prompt_tokens':8,'completion_tokens':6}}
                self.send_response(200);self.end_headers();self.wfile.write(json.dumps(result).encode())
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}/v1'
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join()
    def provider(self,model='fixture-only',**kwargs):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.provider'),'real HTTP provider required')
        from switchlab.studio.provider import Provider
        return Provider({'mode':'api','base_url':self.base,'model':model,**kwargs},'super-secret')
    def test_real_http_adapter_uses_configured_url_and_json(self):
        p=self.provider();result=p.complete([{'role':'system','content':'JSON'},{'role':'user','content':'你好'}])
        self.assertEqual(result['packet']['speech'],'测试传输，不是实际模型。')
        self.assertEqual(self.requests[-1][0],'/v1/chat/completions')
        self.assertEqual(self.requests[-1][2]['response_format']['type'],'json_object')
        self.assertEqual(result['usage']['input_tokens'],8)
    def test_key_absent_from_public_settings(self):
        self.assertNotIn('super-secret',json.dumps(self.provider().public()))
    def test_no_redirect_following(self):
        with self.assertRaises(ValueError):self.provider('redirect').complete([{'role':'user','content':'JSON'}])
    def test_error_does_not_echo_credential(self):
        with self.assertRaises(ValueError) as c:self.provider('failure').complete([{'role':'user','content':'JSON'}])
        self.assertNotIn('super-secret',str(c.exception))
    def test_invalid_model_output_is_error_not_scripted_fallback(self):
        with self.assertRaises(ValueError):self.provider('invalid').complete([{'role':'user','content':'JSON'}])
    def test_plain_http_remote_and_userinfo_rejected(self):
        from switchlab.studio.provider import Provider
        for url in ('http://example.com/v1','https://user:pass@example.com/v1','https://a.com/v1?key=abc'):
            with self.assertRaises(ValueError):Provider({'mode':'api','base_url':url,'model':'x','network_consent':True})
    def test_remote_needs_explicit_consent(self):
        from switchlab.studio.provider import Provider
        with self.assertRaises(ValueError):Provider({'mode':'api','base_url':'https://openrouter.ai/api/v1','model':'x'})
    def test_model_list(self):self.assertIn('fixture-only',self.provider().models())
    def test_prompt_only_mode_omits_response_format(self):
        self.provider(json_mode=False).complete([{'role':'user','content':'JSON'}])
        self.assertNotIn('response_format',self.requests[-1][2])
    def test_manual_mode_never_fabricates_answer(self):
        from switchlab.studio.provider import Provider
        with self.assertRaises(ValueError):Provider({'mode':'manual'}).complete([{'role':'user','content':'hello'}])
