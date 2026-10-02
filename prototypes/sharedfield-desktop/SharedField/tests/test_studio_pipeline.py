"""Real HTTP across both app and provider seams; language remains a labeled fixture."""
import json
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from switchlab.studio.http import StudioServer
from switchlab.studio.service import Service
from tests.test_studio_core import packet

class PipelineTests(unittest.TestCase):
    def test_chat_http_to_provider_http_to_saved_artifact_feedback_revision(self):
        requests=[]
        class ModelFixture(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                prompt=json.loads(data['messages'][-1]['content']);requests.append(prompt)
                result=packet(prompt['source_event']) if prompt['phase']=='turn' else {'content':'# HTTP 集成夹具\n输入已接通，非真实语言模型。'}
                payload={'model':'HTTP_FIXTURE_ONLY','choices':[{'finish_reason':'stop','message':{'content':json.dumps(result,ensure_ascii=False)}}],
                         'usage':{'prompt_tokens':12,'completion_tokens':8}}
                raw=json.dumps(payload,ensure_ascii=False).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        model=ThreadingHTTPServer(('127.0.0.1',0),ModelFixture)
        mt=threading.Thread(target=model.serve_forever,daemon=True);mt.start()
        with tempfile.TemporaryDirectory() as d:
            service=Service(d);service.start_worker();server=StudioServer(service,0)
            t=threading.Thread(target=server.serve_forever,daemon=True);t.start();base=f'http://127.0.0.1:{server.server_port}'
            def call(path,body=None):
                data=json.dumps(body,ensure_ascii=False).encode() if body is not None else None
                headers={'X-SwitchLab-Token':server.token,'Origin':base,'Content-Type':'application/json'}
                with urllib.request.urlopen(urllib.request.Request(base+path,data=data,headers=headers),timeout=8) as r:return json.load(r)
            def wait_for(predicate):
                end=time.monotonic()+6
                while time.monotonic()<end:
                    state=call('/api/state')
                    if predicate(state):return state
                    time.sleep(.04)
                self.fail('async pipeline did not reach required state; '+str(state['runtime']))
            try:
                call('/api/config',{'config':{'mode':'api','base_url':f'http://127.0.0.1:{model.server_port}/v1','model':'HTTP_FIXTURE_ONLY'}})
                call('/api/chat',{'text':'集成测试：比较两个可行方案'})
                wait_for(lambda s:len(s['goals'])==1 and not s['runtime']['busy'])
                call('/api/auto',{'steps':6})
                state=wait_for(lambda s:len(s['artifacts'])==1 and not s['runtime']['busy'])
                call('/api/command',{'kind':'feedback','payload':{'artifact_id':state['artifacts'][0]['id'],'kind':'criteria_failed','text':'保留新的测试约束'}})
                state=wait_for(lambda s:len(s['artifacts'])==2 and not s['runtime']['busy'])
                self.assertIn('保留新的测试约束',json.dumps(requests[-1],ensure_ascii=False))
                self.assertEqual(state['calls'],3);self.assertEqual(state['usage']['output_tokens'],24)
                self.assertEqual(state['runtime']['last_model'],'HTTP_FIXTURE_ONLY')
                count=len(requests);time.sleep(.3);self.assertEqual(len(requests),count)
                call('/api/pause',{});checkpoint=call('/api/export')
                from switchlab.studio.core import Core
                self.assertEqual(len(Core.restore(checkpoint).state['artifacts']),2)
            finally:server.shutdown();server.server_close();service.close()
        model.shutdown();model.server_close()

if __name__=='__main__':unittest.main()
