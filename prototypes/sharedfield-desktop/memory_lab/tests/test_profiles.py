import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

class ProfileTests(unittest.TestCase):
    def test_nested_provider_errors_are_durable_and_never_retried(self):
        from memory_lab.provider import Client,BatchStopped
        for code in (502,429):
            with self.subTest(code=code),tempfile.TemporaryDirectory() as td:
                c=Client(Path(td),key='secret')
                reply={'model':c.profile['model'],'provider':c.profile['provider'],
                       'usage':{'cost':0},'choices':[{'finish_reason':'error',
                       'error':{'code':code,'message':'provider failed'},'message':{'content':'partial'}}]}
                with patch.object(c,'_request',return_value=reply) as request:
                    with self.assertRaises(BatchStopped):c.chat([])
                    with self.assertRaises(BatchStopped):c.chat([])
                    request.assert_called_once()
                saved=json.loads(next(Path(td).glob('calls/*.json')).read_text())
                self.assertEqual(saved['status'],'error')
                self.assertEqual(saved['provider_error']['code'],code)
                self.assertEqual(saved['response']['usage']['cost'],0)
                with c.budget_db() as db:
                    self.assertEqual(db.execute('SELECT status FROM attempts').fetchone()[0],'error')
                    self.assertEqual(bool(db.execute("SELECT 1 FROM config WHERE id='blocked'").fetchone()),code!=429)
                self.assertEqual(json.loads((Path(td)/'STOPPED.json').read_text())['reason_code'],f'http_{code}')

    def test_received_nested_error_recovery_records_failure_without_dispatch(self):
        from memory_lab.provider import Client,BatchStopped
        with tempfile.TemporaryDirectory() as td:
            c=Client(Path(td),key='secret')
            reply={'model':c.profile['model'],'provider':c.profile['provider'],
                   'choices':[{'finish_reason':'error','error':{'code':502}}]}
            original=c.finish_attempt
            def crash(call_id,status,block=None):
                original(call_id,status,block)
                if status=='received':raise KeyboardInterrupt()
            with patch.object(c,'_request',return_value=reply),patch.object(c,'finish_attempt',side_effect=crash),self.assertRaises(KeyboardInterrupt):c.chat([])
            recovered=Client(Path(td),key='secret')
            with patch.object(recovered,'_request') as request,self.assertRaises(BatchStopped):recovered.chat([])
            request.assert_not_called()
            self.assertEqual(json.loads(next(Path(td).glob('calls/*.json')).read_text())['status'],'error')
            self.assertEqual(json.loads((Path(td)/'STOPPED.json').read_text())['reason_code'],'http_502')

    def test_closed_campaign_cannot_dispatch_another_paid_request(self):
        from memory_lab.provider import Client,BatchStopped,write_json
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);c=Client(root/'batch',key='secret',campaign=root/'campaign')
            write_json(root/'campaign/status.json',{'status':'stopped'})
            with patch.object(c,'_request') as request,self.assertRaises(BatchStopped):c.chat([])
            request.assert_not_called()

    def test_explicit_429_body_is_rotation_eligible(self):
        from memory_lab.provider import Client,BatchStopped
        with tempfile.TemporaryDirectory() as td:
            c=Client(Path(td),key='secret')
            with patch.object(c,'_request',return_value={'error':{'code':429}}),self.assertRaises(BatchStopped):c.chat([])
            self.assertEqual(json.loads((Path(td)/'STOPPED.json').read_text())['reason_code'],'http_429')

    def test_received_receipt_is_reconciled_without_second_paid_dispatch(self):
        from memory_lab.provider import Client
        with tempfile.TemporaryDirectory() as td:
            c=Client(Path(td),key='secret')
            reply={'id':'r','model':'deepseek/deepseek-v4-flash-0731','provider':'DeepInfra',
                   'choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}
            original=c.finish_attempt
            def crash(call_id,status,block=None):
                original(call_id,status,block)
                if status=='received':raise KeyboardInterrupt()
            with patch.object(c,'_request',return_value=reply),patch.object(c,'finish_attempt',side_effect=crash),self.assertRaises(KeyboardInterrupt):c.chat([])
            recovered=Client(Path(td),key='secret')
            with patch.object(recovered,'_request') as request:
                self.assertEqual(recovered.chat([])['id'],'r')
                request.assert_not_called()

    def test_429_closes_batch_and_budget_is_shared_across_profiles(self):
        from memory_lab.provider import Client,BatchStopped
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);budget=root/'campaign'
            a=Client(root/'a',key='secret',max_calls=1,campaign=budget,profile='deepseek')
            error=urllib.error.HTTPError('https://test',429,'limited',{},io.BytesIO(b'{"error":{"code":429}}'))
            with patch.object(a,'_request',side_effect=error),self.assertRaises(BatchStopped):a.chat([])
            self.assertEqual(json.loads((root/'a/STOPPED.json').read_text())['reason_code'],'http_429')
            b=Client(root/'b',key='secret',max_calls=1,campaign=budget,profile='qwen35')
            with patch.object(b,'_request') as request,self.assertRaises(BatchStopped):b.chat([])
            request.assert_not_called()

    def test_successful_identical_request_is_reused_without_charge(self):
        from memory_lab.provider import Client
        with tempfile.TemporaryDirectory() as td:
            c=Client(Path(td),key='secret',profile='qwen35')
            reply={'id':'one','model':'qwen/qwen3.5-flash-02-23','provider':'Alibaba','choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}
            with patch.object(c,'_request',return_value=reply) as request:
                first=c.chat([]);second=c.chat([])
            self.assertEqual(request.call_count,1)
            self.assertEqual(first,second)
            self.assertEqual(first['lab_profile']['id'],'qwen35')
            self.assertEqual(len(list(Path(td).glob('calls/*.json'))),1)

    def test_unknown_timeout_blocks_other_profile(self):
        from memory_lab.provider import Client,BatchStopped
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            a=Client(root/'a',key='secret',campaign=root/'campaign')
            with patch.object(a,'_request',side_effect=TimeoutError()),self.assertRaises(BatchStopped):a.chat([])
            b=Client(root/'b',key='secret',campaign=root/'campaign',profile='qwen35')
            with patch.object(b,'_request') as request,self.assertRaises(BatchStopped):b.chat([])
            request.assert_not_called()

    def test_batch_profile_cannot_change(self):
        from memory_lab.provider import Client
        with tempfile.TemporaryDirectory() as td:
            Client(Path(td),key='secret',profile='deepseek')
            with self.assertRaises(ValueError):Client(Path(td),key='secret',profile='qwen35')
