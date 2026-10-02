"""Real app HTTP and real provider HTTP; generated language is a named fixture."""
import json
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from switchlab.studio.adaptive_service import AdaptiveService
from switchlab.studio.http import create_server
from tests.adaptive_fixtures import proposal

class AdaptivePipelineTests(unittest.TestCase):
    def test_two_hop_http_selection_artifact_feedback_revision_and_replay(self):
        requests=[]
        class Model(BaseHTTPRequestHandler):
            def log_message(self,*a):pass
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                prompt=json.loads(data['messages'][-1]['content']);requests.append(prompt)
                if prompt['phase']=='analyse':packet=proposal(prompt['source_event'],True)
                elif prompt['phase']=='express':packet={'decision_id':prompt['local_decision']['id'],'speech':'HTTP_TEST_FIXTURE：这是明确标注的集成测试。'}
                else:packet={'content':'# 测试产出\nHTTP_TEST_FIXTURE；保留原始约束与反馈。'}
                raw=json.dumps({'model':'HTTP_TEST_FIXTURE','choices':[{'finish_reason':'stop','message':{'content':json.dumps(packet,ensure_ascii=False)}}],
                    'usage':{'prompt_tokens':10,'completion_tokens':10}},ensure_ascii=False).encode()
                self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        model=ThreadingHTTPServer(('127.0.0.1',0),Model);mt=threading.Thread(target=model.serve_forever,daemon=True);mt.start()
        self.addCleanup(model.server_close);self.addCleanup(model.shutdown)
        with tempfile.TemporaryDirectory() as d:
            service=AdaptiveService(d);service.start_worker();server=create_server(service,0)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
            def call(path,body=None):
                data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
                h={'X-SwitchLab-Token':server.token,'Origin':base,'Content-Type':'application/json'}
                with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers=h),timeout=6) as r:return json.load(r)
            def wait_for(predicate):
                end=time.monotonic()+8
                while time.monotonic()<end:
                    state=call('/api/state')
                    if state['runtime']['error']:self.fail(state['runtime']['error'])
                    if predicate(state):return state
                    time.sleep(.03)
                self.fail('async pipeline timed out')
            try:
                call('/api/config',{'config':{'mode':'api','base_url':f'http://127.0.0.1:{model.server_port}/v1','model':'HTTP_TEST_FIXTURE'}})
                call('/api/chat',{'text':'请比较方案，不要遗漏资源约束'})
                state=wait_for(lambda s:len(s['goals'])==1 and not s['runtime']['busy'])
                self.assertEqual([r['phase'] for r in requests],['analyse','express'])
                self.assertEqual(state['cognition']['observations'],1);self.assertEqual(state['lab']['observation']['tick'],0)
                call('/api/auto',{'steps':6});state=wait_for(lambda s:len(s['artifacts'])==1 and not s['runtime']['busy'])
                call('/api/command',{'kind':'feedback','payload':{'artifact_id':state['artifacts'][0]['id'],'kind':'criteria_failed','text':'需要保留新的约束XYZ'}})
                state=wait_for(lambda s:len(s['artifacts'])==2 and not s['runtime']['busy'])
                self.assertIn('需要保留新的约束XYZ',json.dumps(requests[-1],ensure_ascii=False))
                self.assertGreater(state['cognition']['learner']['updates'],0)
                call('/api/pause',{});n=len(requests);time.sleep(.2);self.assertEqual(n,len(requests))
                cp=call('/api/export')
                from switchlab.studio.adaptive_core import AdaptiveCore
                restored=AdaptiveCore.restore(cp)
                self.assertEqual(len(restored.state['artifacts']),2)
            finally:server.shutdown();server.server_close();service.close();thread.join(2)
