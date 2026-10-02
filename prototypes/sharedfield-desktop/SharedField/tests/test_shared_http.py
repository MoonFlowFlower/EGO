import json,threading,tempfile,unittest,urllib.request,urllib.error,subprocess,sys,re
from pathlib import Path
from tests.test_shared_service import SharedFixture
try:
    from switchlab.shared.http import create_server
    from switchlab.shared.service import SharedService
except ImportError:create_server=None

class SharedHTTPTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(create_server,'shared HTTP integration absent')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=SharedService(self.tmp.name,provider=SharedFixture());self.addCleanup(self.s.close)
        self.server=create_server(self.s,0);self.t=threading.Thread(target=self.server.serve_forever,daemon=True);self.t.start()
        self.addCleanup(self.cleanup_server);self.base='http://127.0.0.1:'+str(self.server.server_port)
    def cleanup_server(self):self.server.shutdown();self.server.server_close();self.t.join(2)
    def req(self,path,body=None,token=True,origin=None,host=None):
        h={'X-SwitchLab-Token':self.server.token} if token else {};data=None
        if host:h['Host']=host
        if body is not None:h.update({'Origin':origin or self.base,'Content-Type':'application/json'});data=json.dumps(body).encode()
        with urllib.request.urlopen(urllib.request.Request(self.base+path,data=data,headers=h),timeout=5) as r:
            b=r.read();return json.loads(b) if r.headers.get_content_type()=='application/json' else b.decode()
    def test_shared_default_page_and_assets(self):
        body=self.req('/')
        for ident in ('worldMap','messageInput','affectBars','focusText','askFeeling'):self.assertIn('id="'+ident+'"',body)
        for path in ('/app.js','/style.css'):self.assertTrue(self.req(path))
    def test_actual_http_world_and_chat_read_same_kernel(self):
        self.req('/api/command',{'kind':'player_action','payload':{'action':{'kind':'survey'}}})
        self.req('/api/chat',{'text':'你现在有什么感觉？'});self.s.run_once()
        v=self.req('/api/state');self.assertEqual(v['world']['tick'],1);self.assertEqual(v['cognition']['learned_events'],1)
        cp=self.req('/api/export');self.assertEqual(cp['schema'],'switchlab.shared.v5')
    def test_reports_have_readonly_endpoint(self):
        self.req('/api/chat',{'text':'你在想什么'});self.s.run_once();r=self.req('/api/state')['messages'][-1]['state_id']
        a=self.req('/api/report?id='+r);b=self.req('/api/report?id='+r);self.assertEqual(a,b)
    def test_csrf_and_host_and_unauthorized_action(self):
        for opts in ({'token':False},{'origin':'https://evil.invalid'},{'host':'evil.invalid'}):
            with self.assertRaises(urllib.error.HTTPError) as c:self.req('/api/chat',{'text':'hi'},**opts)
            self.assertEqual(c.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/command',{'kind':'shell','payload':{}})
    def test_no_arbitrary_files_or_legacy_artifacts(self):
        for p in ('/../../README.md','/api/artifact?id=A01'):
            with self.assertRaises(urllib.error.HTTPError) as c:self.req(p)
            self.assertEqual(c.exception.code,404)
    def test_options_are_validated_and_do_not_grant_steps(self):
        self.req('/api/options',{'language_mode':'manual','narrate':True})
        self.assertEqual(self.s.auto_remaining,0)
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/options',{'interval':0})
