"""Failure-oriented checks, with explicit controllable language transport doubles."""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.test_studio_service import ScriptedTransport
from tests.test_studio_core import packet
from switchlab.studio.service import Service
from switchlab.studio.core import Core
from switchlab.runtime import digest

class EdgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.p=ScriptedTransport();self.s=Service(self.tmp.name,provider=self.p)
    def tearDown(self):
        self.s.close();self.tmp.cleanup()
    def test_rehashed_result_tamper_rejected_by_computation(self):
        self.s.submit('test');self.s.run_once(force=True)
        c=self.s.core.checkpoint();c['events'][0]['result']['evidence_id']='E999999'
        # Repair hash chain to show that computation, not only a checksum, detects it.
        previous=digest(c['metadata'])
        for e in c['events']:
            e['previous']=previous;e.pop('hash');e['hash']=digest(e);previous=e['hash']
        c['head']=previous
        with self.assertRaises(ValueError):Core.restore(c)
    def test_malformed_json_fence_is_a_user_error(self):
        from switchlab.studio.protocol import parse_json
        with self.assertRaises(ValueError):parse_json('```')
    def test_actual_tool_anomaly_can_trigger_language_without_user_message(self):
        for _ in range(10):
            self.s.command('lab',{'action':'calibrate'})
            if self.s.core.pending_reflection():break
        self.assertIsNotNone(self.s.core.pending_reflection())
        self.s.start_auto(1);self.s.run_once()
        context=json.loads(self.p.requests[-1][-1]['content'])
        self.assertEqual(context['selected_input']['kind'],'tool_result')
        self.assertFalse([x for x in self.s.core.state['messages'] if x['role']=='user'])
        self.assertTrue(self.s.core.state['goals'])
        self.assertEqual(self.s.auto_remaining,0)
    def test_failed_disk_commit_rolls_back_memory_state(self):
        before=self.s.core.checkpoint()
        with patch('switchlab.studio.service.save_json',side_effect=OSError('disk full')):
            with self.assertRaises(ValueError):self.s.submit('cannot persist')
        self.assertEqual(before,self.s.core.checkpoint());self.assertTrue(self.s.error)
    def test_new_life_archives_old_complete_state(self):
        self.s.submit('preserve this');old=self.s.core.checkpoint();self.s.new_life()
        archive=list((Path(self.tmp.name)/'archive').glob('*.json'))
        self.assertEqual(len(archive),1);self.assertEqual(json.loads(archive[0].read_text()),old)
        self.assertEqual(self.s.core.state['messages'],[]);self.assertEqual(self.s.auto_remaining,0)
    def test_new_constraint_invalidates_inflight_draft(self):
        self.s.submit('first task');self.s.run_once(force=True)
        self.p.entered.clear();self.p.block=threading.Event()
        t=threading.Thread(target=lambda:self.s.run_once(force=True));t.start();self.assertTrue(self.p.entered.wait(2))
        self.s.submit('new constraint');self.p.block.set();t.join(4)
        self.assertEqual(self.s.core.state['artifacts'],[]);self.assertIsNotNone(self.s.core.pending_turn())
    def test_configuration_never_moves_secret_to_another_endpoint(self):
        from switchlab.studio.provider import DEFAULT
        self.s.configure({**DEFAULT,'mode':'api','model':'test','base_url':'https://example.org/v1','network_consent':True})
        self.assertEqual(self.s.provider.key,'')
    def test_connection_check_cannot_write_after_close(self):
        ready=threading.Event();release=threading.Event();errors=[]
        def complete(messages):
            ready.set();release.wait(4)
            return {'packet':{'speech':'connection ok'},'model':'fixture','usage':{'input_tokens':1,'output_tokens':1}}
        self.p.complete=complete
        def run():
            try:self.s.check_connection()
            except ValueError as e:errors.append(str(e))
        t=threading.Thread(target=run);t.start();self.assertTrue(ready.wait(2))
        self.s.close();saved=(Path(self.tmp.name)/'session.json').read_bytes();release.set();t.join(4)
        self.assertEqual((Path(self.tmp.name)/'session.json').read_bytes(),saved)
        self.assertTrue(errors)
    def test_aborted_provider_usage_is_counted_without_committing_model_proposals(self):
        # Budget is reserved even if a request gets cancelled; token counts can remain unknown.
        self.s.submit('test');self.p.block=threading.Event()
        t=threading.Thread(target=lambda:self.s.run_once(force=True));t.start();self.p.entered.wait(2)
        self.s.pause();self.p.block.set();t.join(4)
        self.assertEqual(self.s.core.state['calls'],1);self.assertFalse(self.s.core.state['goals'])

if __name__=='__main__':unittest.main()
