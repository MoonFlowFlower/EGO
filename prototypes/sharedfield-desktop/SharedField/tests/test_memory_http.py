import unittest,tempfile,threading,json,urllib.request,urllib.error
from pathlib import Path
from tests.test_memory_service import Fixture
from tests.test_memory_store import NOW
from switchlab.memory.service import MemoryService
try:
    from switchlab.memory.http import create_server
except ImportError:create_server=None

class MemoryHTTPTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(create_server,'memory is not the served application')
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=MemoryService(self.tmp.name,provider=Fixture(),clock=lambda:NOW);self.addCleanup(self.s.close)
        self.server=create_server(self.s,0);self.t=threading.Thread(target=self.server.serve_forever,daemon=True);self.t.start();self.addCleanup(self.stop)
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def stop(self):self.server.shutdown();self.server.server_close();self.t.join(2)
    def req(self,path,body=None,token=True,origin=None,host=None):
        h={'X-SwitchLab-Token':self.server.token} if token else {};raw=None
        if host:h['Host']=host
        if body is not None:h.update(Origin=origin or self.base);h['Content-Type']='application/json';raw=json.dumps(body).encode()
        with urllib.request.urlopen(urllib.request.Request(self.base+path,data=raw,headers=h),timeout=10) as r:
            b=r.read();return json.loads(b) if r.headers.get_content_type()=='application/json' else b.decode()
    def test_actual_chat_http_uses_longterm_memory(self):
        self.req('/api/options',{'language_mode':'api'});self.req('/api/chat',{'text':'测试夹具：1分钟后一起看星空'})
        self.s.run_once();self.s.run_once();v=self.req('/api/state')
        self.assertEqual(v['commitments']['total'],1);self.assertIn('已经记下',v['messages'][-1]['text'])
        self.assertEqual(self.req('/api/export')['schema'],'sharedfield.memory.v6')
    def test_source_query_and_full_read(self):
        mid=self.req('/api/chat',{'text':'蓝色读书约定'})['source']
        self.assertEqual(self.req('/api/source?id='+mid)['text'],'蓝色读书约定')
        self.assertTrue(self.req('/api/search?q=%E8%93%9D%E8%89%B2')['items'])
    def test_security_host_origin_token_unknown_capability(self):
        for opts in ({'token':False},{'host':'evil.invalid'},{'origin':'https://evil.invalid'}):
            with self.assertRaises(urllib.error.HTTPError) as c:self.req('/api/chat',{'text':'bad'},**opts)
            self.assertEqual(c.exception.code,403)
        for p in ('/../../README.md','/api/shell'):
            with self.assertRaises(urllib.error.HTTPError):self.req(p,{} if p=='/api/shell' else None)
    def test_page_assets_and_no_background_by_default(self):
        html=self.req('/')
        for ident in ('messageInput','commitments','memoryDialog','configDialog','backgroundButton'):self.assertIn('id="'+ident+'"',html)
        for p in ('/app.js','/style.css'):self.assertTrue(self.req(p))
        self.assertFalse(self.req('/api/state')['runtime']['background'])
    def test_edit_cancel_backup_delete_same_kernel(self):
        r=self.req('/api/commitment',{'op':'create','title':'一起读书','quote':'以后一起读书','accept':True});cid=r['commitments'][0]
        self.req('/api/commitment',{'op':'cancel','id':cid,'expected_revision':1,'quote':'取消一起读书'})
        self.assertEqual(self.req('/api/commitments?closed=1')['items'][0]['status'],'cancelled')
        self.assertTrue(self.req('/api/backup',{})['ok'])
        mid=self.req('/api/chat',{'text':'请删除这条专用测试'})['source']
        self.req('/api/forget',{'source_ids':[mid],'confirmed':True})
        with self.assertRaises(urllib.error.HTTPError):self.req('/api/source?id='+mid)
    def test_timezone_and_background_and_limits_explicit(self):
        self.req('/api/memory-settings',{'timezone':'UTC+08:00'});self.assertIn('+08:00',self.req('/api/state')['time'])
        self.req('/api/background',{});self.assertTrue(self.req('/api/state')['runtime']['background'])
        self.req('/api/pause',{});self.assertFalse(self.req('/api/state')['runtime']['background'])
        self.assertIn('ceiling',self.req('/api/grant',{'count':5}))
