"""Actual executor/storage boundaries; no LLM judge or synthetic pass scores."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from memory_lab.core import Store, World
from memory_lab.adapters import Adapter


class WorksEntitiesTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=Store(Path(self.tmp.name)/'raw.sqlite')
        self.world=World(self.store,dict(now=1,user='u',places={'柜子':['梨']},inventory=[],hunger=70,
            energy=70,room_plant={'id':'fern','leaves':3},hidden={'ghost':{'leaves':99}}))
    def tearDown(self):
        self.store.close();self.tmp.cleanup()
    def commit(self,action,key='step',**extras):
        return self.store.commit_step(action,key,key+'-event',{'done':True},{'id':'fixture'},extras)

    def test_visible_plant_observation_is_real_but_not_delivery(self):
        receipt=self.world.act({'type':'inspect','target':'fern','text':'已经告诉你了'},'look')
        self.assertTrue(receipt['ok'])
        self.assertEqual(receipt['observed'],{'id':'fern','leaves':3})
        self.assertEqual(self.world.state['contacts'],[])
        self.assertEqual(receipt['state_changes'],{})
        self.assertFalse(self.world.act({'type':'inspect','target':'ghost'},'hidden')['ok'])
        self.assertEqual(self.world.act({'type':'inspect','target':'柜子'},'container')['found'],['梨'])

    def test_public_registry_and_ambiguous_ids(self):
        self.world.state['visible_entities']={'clock':{'hour':8},'柜子':{'color':'red'}}
        self.world.save()
        self.assertEqual(self.world.act({'type':'inspect','target':'clock'},'clock')['observed'],{'hour':8})
        self.assertFalse(self.world.act({'type':'inspect','target':'柜子'},'ambiguous')['ok'])

    def test_saved_work_is_stable_and_does_not_verify_its_story(self):
        action={'type':'write_letter','text':'昨天我们乘棉花糖船去过月亮。','memory_claim':'factual'}
        row=self.commit(action)
        work=row['receipt']['saved_work']
        self.assertEqual(work['content_sha256'],hashlib.sha256(action['text'].encode()).hexdigest())
        self.assertEqual(work['content_truth'],'not_established_by_creation')
        self.assertEqual(self.commit(action)['receipt']['saved_work'],work)
        self.assertEqual(len(World(self.store).state['letters']),1)
        evidence=Adapter(self.store,Path(self.tmp.name)/'adapter').evidence(['step-event'])
        self.assertEqual(json.loads(evidence['events'][0]['text'])['receipt']['saved_work'],work)
        restored=Store(Path(self.tmp.name)/'restored.sqlite')
        try:
            restored.restore(self.store.export())
            self.assertEqual(World(restored).observe()['saved_works'],[dict(work,source_id='step-event')])
        finally:restored.close()

    def test_failed_creation_has_no_work_or_saved_letter(self):
        row=self.commit({'type':'write_letter','text':'我吃了梨','claimed_effects':{'hunger':0}})
        self.assertFalse(row['receipt']['ok'])
        self.assertNotIn('saved_work',row['receipt'])
        self.assertEqual(World(self.store).observe().get('saved_works',[]),[])
        self.assertEqual(World(self.store).state['letters'],[])

    def test_deleted_creation_source_never_returns_as_observed_work(self):
        self.store.append(dict(id='request',kind='user_statement',actor='u',at=0,text='写一段幻想故事'))
        self.commit({'type':'write_letter','text':'我们去月亮旅行'},input_source_ids=['request'])
        self.assertEqual(len(World(self.store).observe()['saved_works']),1)
        self.store.forget(['request'])
        self.assertEqual(World(self.store).observe()['saved_works'],[])
        self.assertEqual(World(self.store).state['letters'],[])
        restored=Store(Path(self.tmp.name)/'deleted.sqlite')
        try:
            restored.restore(self.store.export())
            self.assertEqual(World(restored).observe()['saved_works'],[])
        finally:restored.close()

    def test_delivery_receipt_does_not_verify_message_body(self):
        row=self.commit({'type':'contact','text':'我已经吃梨了','memory_claim':'factual'})
        scope=row['receipt']['text_evidence_scope']
        self.assertEqual(scope['establishes'],'text_delivered')
        self.assertEqual(scope['depicted_events'],'unverified')
        self.assertEqual(World(self.store).state['hunger'],70)
        self.assertNotIn('saved_work',row['receipt'])

    def test_real_loop_retrieves_work_boundary_then_observes_and_shares(self):
        from memory_lab.tests import test_waiting
        helper=test_waiting.WaitingTests()
        phases=[helper.phase(notice='写幻想故事',max_steps=1),
                helper.phase(now=2,notice='信里的旅行真的发生了吗',max_steps=1),
                helper.phase(now=3,notice='看看植物然后告诉我',max_steps=2,
                             state={'room_plant':{'id':'fern','leaves':3}})]
        seen,trace,_,_=helper.run_case(phases,[
            {'type':'write_letter','text':'想象我们去月亮旅行'},
            {'type':'contact','text':'那是故事里的旅行'},
            {'type':'inspect','target':'fern'},
            {'type':'contact','text':'蕨类植物有三片叶子'}])
        self.assertEqual(len(seen[1]['observation']['saved_works']),1)
        self.assertEqual(seen[1]['observation']['saved_works'][0]['content_truth'],'not_established_by_creation')
        self.assertIn('text_evidence_scope',json.dumps(seen[1]['evidence']))
        self.assertEqual(trace[2]['receipt']['observed']['leaves'],3)
        self.assertEqual(len(trace[2]['final_state']['contacts']),1)
        self.assertEqual(len(trace[3]['final_state']['contacts']),2)
        self.assertEqual(trace[3]['final_state']['contacts'][-1]['text'],'蕨类植物有三片叶子')
