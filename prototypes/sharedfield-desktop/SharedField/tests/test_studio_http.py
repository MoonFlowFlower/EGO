import importlib.util
import json
import re
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path

class StudioHttpTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.http'),'Studio HTTP/UI required')
        from switchlab.studio.service import Service
        from switchlab.studio.http import create_server
        self.tmp=tempfile.TemporaryDirectory();self.s=Service(Path(self.tmp.name))
        self.server=create_server(self.s,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f'http://127.0.0.1:{self.server.server_port}'
    def tearDown(self):
        if hasattr(self,'server'):self.server.shutdown();self.server.server_close();self.thread.join();self.s.close()
        if hasattr(self,'tmp'):self.tmp.cleanup()
    def request(self,path,body=None,token=True,origin=None,host=None):
        headers={}
        if token:headers['X-SwitchLab-Token']=self.server.token
        if host:headers['Host']=host
        data=None
        if body is not None:
            data=json.dumps(body,ensure_ascii=False).encode();headers['Content-Type']='application/json';headers['Origin']=origin or self.base
        return urllib.request.urlopen(urllib.request.Request(self.base+path,data=data,headers=headers),timeout=8)
    def test_real_static_ui_and_csp(self):
        with self.request('/') as r:
            s=r.read().decode();self.assertIn('持续认知工作台',s);self.assertNotIn('__TOKEN__',s)
            self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy'])
        for path in ('/app.js','/style.css'):
            with self.request(path) as r:self.assertEqual(r.status,200)
    def test_real_chat_http_mutates_persistent_state(self):
        with self.request('/api/chat',{'text':'你好，请不要把每句聊天都创建成任务'}) as r:self.assertEqual(r.status,200)
        with self.request('/api/state') as r:s=json.load(r)
        self.assertEqual(s['messages'][0]['role'],'user');self.assertIn('你好',s['messages'][0]['text'])
        self.assertTrue((Path(self.tmp.name)/'session.json').exists())
    def test_no_token_or_foreign_origin_rejected(self):
        for path,body,kwargs in [('/api/state',None,{'token':False}),('/api/chat',{'text':'x'},{'origin':'https://attacker.invalid'}),
                                  ('/api/state',None,{'host':'attacker.invalid'})]:
            with self.assertRaises(urllib.error.HTTPError) as c:self.request(path,body,**kwargs)
            self.assertEqual(c.exception.code,403)
    def test_no_arbitrary_path_or_shell(self):
        with self.assertRaises(urllib.error.HTTPError):self.request('/../../session.json')
        with self.assertRaises(urllib.error.HTTPError):self.request('/api/command',{'kind':'shell','payload':{'command':'ls'}})
    def test_loopback_experiment_steps_real_world(self):
        with self.request('/api/command',{'kind':'lab','payload':{'action':'calibrate'}}) as r:self.assertEqual(r.status,200)
        with self.request('/api/state') as r:d=json.load(r)
        self.assertEqual(d['lab']['observation']['tick'],1)
        self.assertNotIn('evaluator_truth',str(d))
    def test_export_and_pause(self):
        with self.request('/api/pause',{}) as r:self.assertEqual(r.status,200)
        with self.request('/api/export') as r:
            d=json.load(r);self.assertEqual(d['schema'],'switchlab.studio.v2')
            self.assertIn('attachment',r.headers['Content-Disposition'])
    def test_invalid_large_or_null_message(self):
        for s in (None,'x'*6001):
            with self.assertRaises(urllib.error.HTTPError):self.request('/api/chat',{'text':s})
