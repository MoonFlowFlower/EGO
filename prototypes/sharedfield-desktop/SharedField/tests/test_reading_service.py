import json
import tempfile
import threading
import unittest
import urllib.request
from switchlab.memory.service import MemoryService
from switchlab.memory.http import create_server
from switchlab.studio.provider import DEFAULT

PACKET={'summary':'甲方案需要十分钟。','findings':[{'text':'甲的时间','paragraph':'p1','quote':'甲方案需要十分钟。'}],'question':'是否还有其他限制？'}

class ReadingServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.s=MemoryService(self.temp.name);self.addCleanup(lambda:self.s.close())

    def command(self,**kw):
        self.assertTrue(hasattr(self.s,'reading_command'),'actual MemoryService must expose the reading loop')
        return self.s.reading_command(kw)

    def begin(self):
        mid=self.command(op='material',title='小段落',text='甲方案需要十分钟。')['id']
        return self.command(op='start',material_id=mid,question='需要多久？',goal='比较方案')['id']

    def test_main_worker_reads_manual_packet_and_chat_sees_actual_artifact(self):
        self.s.set_options({'language_mode':'manual'});self.begin();self.s.run_once()
        r=self.s.manual_request;self.assertEqual(r['phase'],'reading')
        self.s.accept_manual(r['id'],json.dumps(PACKET));v=self.s.reading_view()
        self.assertEqual(v['activities'][0]['reading']['summary'],'甲方案需要十分钟。')
        self.s.submit('刚才一起读了什么？');self.s.run_once()
        context=json.loads(self.s.manual_request['messages'][-1]['content'])['context']
        self.assertEqual(context['reading']['activities'][0]['actual_reading'],'甲方案需要十分钟。')

    def test_pause_and_restart_leave_job_pending_without_automatic_request(self):
        self.s.set_options({'language_mode':'manual'});self.begin();self.s.run_once();old=self.s.manual_request['id']
        self.s.pause()
        with self.assertRaises(ValueError):self.s.accept_manual(old,json.dumps(PACKET))
        self.s.close();self.s=MemoryService(self.temp.name)
        self.assertFalse(self.s.run_once());self.assertEqual(self.s.reading_view()['pending_jobs'],1)
        self.command(op='resume');self.s.run_once();self.assertIsNotNone(self.s.manual_request)

    def test_local_mode_never_fakes_reading(self):
        self.begin();self.s.run_once()
        self.assertIsNone(self.s.reading_view()['activities'][0]['reading'])
        self.assertIn('模型',self.s.error)

    def test_http_reading_page_and_transaction_use_real_entry(self):
        server=create_server(self.s,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            with urllib.request.urlopen(base+'/reading') as r:self.assertIn('一起读',r.read().decode())
            request=urllib.request.Request(base+'/api/reading',json.dumps({'op':'material','title':'小段落','text':'真实文本'}).encode(),
                {'Content-Type':'application/json','Origin':base,'X-SwitchLab-Token':server.token})
            with urllib.request.urlopen(request) as r:mid=json.load(r)['id']
            self.assertEqual(self.s.reading_view()['materials'][0]['id'],mid)
        finally:server.shutdown();server.server_close();thread.join(2)

    def test_late_paid_reading_after_pause_is_not_saved_or_retried(self):
        entered=threading.Event();release=threading.Event()
        class Fixture:
            config={**DEFAULT,'mode':'api','model':'READING_TEST_FIXTURE'}
            def complete(self,messages):
                entered.set();release.wait(3)
                return {'packet':PACKET,'model':'READING_TEST_FIXTURE','usage':{}}
            def public(self):return {**self.config,'key_present':False,'local_endpoint':True}
        self.s.provider=Fixture();self.s.set_options({'language_mode':'api'});self.begin()
        t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(2));self.s.pause();release.set();t.join(4)
        self.assertIsNone(self.s.reading_view()['activities'][0]['reading']);self.assertFalse(self.s.run_once())

    def test_reading_provenance_reaches_chat_expression_deletion(self):
        self.s.set_options({'language_mode':'manual'});self.begin();self.s.run_once()
        self.s.accept_manual(self.s.manual_request['id'],json.dumps(PACKET))
        source=self.s.reading_view()['materials'][0]['source']
        self.s.submit('zzzzzzz');self.s.run_once();self.s.accept_manual(self.s.manual_request['id'],json.dumps({'claims':[],'commitments':[]}))
        self.s.run_once();r=self.s.manual_request
        self.s.accept_manual(r['id'],json.dumps({'speech':'从共同阅读得知：甲方案需要十分钟。','evidence_ids':[]}))
        self.s.forget([source],True)
        self.assertNotIn('甲方案需要十分钟',json.dumps(self.s.store.export(),ensure_ascii=False))

    def test_setting_change_during_paid_reading_requires_explicit_resume(self):
        entered=threading.Event();release=threading.Event()
        class Fixture:
            config={**DEFAULT,'mode':'api','model':'READING_TEST_FIXTURE'}
            def complete(self,messages):
                entered.set();release.wait(3)
                return {'packet':PACKET,'model':'READING_TEST_FIXTURE','usage':{}}
        self.s.provider=Fixture();self.s.set_options({'language_mode':'api'});self.begin()
        t=threading.Thread(target=self.s.run_once);t.start();self.assertTrue(entered.wait(2));self.s.set_memory_settings({'learning':False});release.set();t.join(4)
        self.assertFalse(self.s.run_once());self.assertIsNone(self.s.reading_view()['activities'][0]['reading'])
