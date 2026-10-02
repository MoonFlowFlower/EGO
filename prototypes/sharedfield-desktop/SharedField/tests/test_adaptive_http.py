import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path
from switchlab.studio.adaptive_service import AdaptiveService
from switchlab.studio.http import create_server
from tests.test_adaptive_service import FixtureProvider

ROOT=Path(__file__).resolve().parents[1]
class AdaptiveHTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.s=AdaptiveService(self.tmp.name,provider=FixtureProvider());self.addCleanup(self.s.close)
        self.server=create_server(self.s,0);self.t=threading.Thread(target=self.server.serve_forever,daemon=True);self.t.start()
        self.addCleanup(self.cleanup_server);self.base=f'http://127.0.0.1:{self.server.server_port}'
    def cleanup_server(self):self.server.shutdown();self.server.server_close();self.t.join(2)
    def req(self,path,body=None):
        h={'X-SwitchLab-Token':self.server.token}
        data=None
        if body is not None:h.update({'Origin':self.base,'Content-Type':'application/json'});data=json.dumps(body).encode()
        with urllib.request.urlopen(urllib.request.Request(self.base+path,data=data,headers=h),timeout=5) as r:
            raw=r.read();return json.loads(raw) if r.headers.get_content_type()=='application/json' else raw.decode()
    def test_default_html_exposes_cognitive_loop_not_toy_metrics(self):
        body=self.req('/')
        for ident in ('cognitionPanel','learningToggle','selectionMode','outcomeDialog','claimsList'):
            self.assertIn('id="'+ident+'"',body)
        self.assertIn('v0.3',body)
    def test_actual_http_chat_learn_feedback_export(self):
        self.req('/api/chat',{'text':'测试真实 HTTP 路径'})
        self.s.run_once();self.s.run_once()
        v=self.req('/api/state');self.assertEqual(v['cognition']['observations'],1)
        d=v['cognition']['decisions'][-1]['id']
        self.req('/api/command',{'kind':'outcome','payload':{'decision_id':d,'task':1.,'note':'合成测试结果'}})
        v=self.req('/api/state');self.assertGreater(v['cognition']['learner']['updates'],0)
        cp=self.req('/api/export');self.assertEqual(cp['schema'],'switchlab.studio.v3')
        from switchlab.studio.adaptive_core import AdaptiveCore
        self.assertEqual(cp,AdaptiveCore.restore(cp).checkpoint())
    def test_cli_default_actually_instantiates_adaptive_controller(self):
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.Popen([sys.executable,str(ROOT/'run.py'),'studio','--port','0','--no-browser','--data-dir',d],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                line=p.stdout.readline();match=re.search(r'http://127\.0\.0\.1:\d+',line)
                self.assertIsNotNone(match,line)
                base=match.group()
                with urllib.request.urlopen(base,timeout=3) as r:html=r.read().decode()
                token=re.search(r'name="studio-token" content="([^"]+)"',html).group(1)
                with urllib.request.urlopen(urllib.request.Request(base+'/api/state',headers={'X-SwitchLab-Token':token}),timeout=3) as r:v=json.load(r)
                self.assertEqual(v['version'],'0.3.0');self.assertIn('cognition',v)
            finally:
                p.terminate();p.communicate(timeout=5)

class ImportVersionTests(unittest.TestCase):
    def test_default_import_rejects_v2_not_startable_by_v3_core(self):
        from switchlab.studio.core import Core
        from switchlab.runtime import save_json
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'v2.json';save_json(source,Core().checkpoint())
            target=Path(d)/'new'
            r=subprocess.run([sys.executable,str(ROOT/'run.py'),'studio-import',str(source),'--data-dir',str(target)],capture_output=True,text=True,timeout=10)
            self.assertNotEqual(r.returncode,0,'v2 state must not be installed into a v3-only default runtime')
            self.assertIn('studio-migrate-v02',r.stderr+r.stdout)
            self.assertFalse((target/'session.json').exists())
