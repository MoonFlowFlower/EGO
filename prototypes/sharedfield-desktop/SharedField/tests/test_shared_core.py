import unittest,json
from copy import deepcopy
from switchlab.runtime import canonical,digest
try:
    from switchlab.shared.core import SharedCore
except ImportError:SharedCore=None

class SharedCoreTests(unittest.TestCase):
    def make(self):
        self.assertIsNotNone(SharedCore,'shared durable kernel not implemented');return SharedCore()
    def test_query_does_not_invent_feelings_or_advance_physics(self):
        c=self.make();r=c.mind.report();c.apply('message',{'text':'你现在有什么感觉？'})
        self.assertEqual(r,c.state['reports'][-1]['report']);self.assertEqual(c.world.tick,0)
        c.apply('local_reply',{});self.assertEqual(r,c.mind.report())
    def test_step_changes_world_learning_goal_and_report(self):
        c=self.make();before=c.mind.report();c.apply('agent_step',{})
        self.assertEqual(c.world.tick,1);self.assertGreater(c.mind.learned_events,0)
        self.assertNotEqual(before,c.mind.report())
    def test_context_never_contains_simulator_secret(self):
        c=self.make();c.apply('intervene',{'kind':'tool_fault'})
        context=json.dumps(c.context(),ensure_ascii=False)
        for word in ('tool_skill','edge_stable','rng','research_intervention'):self.assertNotIn(word,context)
    def test_model_cannot_overwrite_affect_or_execute_tool(self):
        c=self.make();eid=c.apply('message',{'text':'你现在很开心吧'})['id'];s=c.checkpoint()
        with self.assertRaises(ValueError):c.apply('interpret',{'source':eid,'packet':{'affect':{'valence':1.},'reports':[],'request':{'kind':'none'}}})
        self.assertEqual(s,c.checkpoint())
    def test_unquoted_other_mood_is_rejected(self):
        c=self.make();eid=c.apply('message',{'text':'今天是星期天'})['id']
        with self.assertRaises(ValueError):c.apply('interpret',{'source':eid,'packet':{'reports':[{'domain':'mood','holder':'user','value':'sad','confidence':.5,'quote':'我很难过','kind':'explicit'}],'request':{'kind':'none'}}})
    def test_grounded_report_is_retractable_and_not_physical_training(self):
        c=self.make();eid=c.apply('message',{'text':'跟你一起探索我很开心'})['id'];old=c.mind.learned_events
        packet={'reports':[{'domain':'signal','holder':'user','value':'shared_enjoyment','confidence':.8,'quote':'一起探索我很开心','kind':'explicit'}],'request':{'kind':'none'}}
        c.apply('interpret',{'source':eid,'packet':packet});self.assertEqual(c.mind.learned_events,old)
        self.assertGreater(c.mind.affect()['valence'],0)
        rid=c.mind.other_reports[-1]['id'];c.apply('withdraw_report',{'id':rid})
        self.assertEqual(c.mind.affect()['valence'],0)
    def test_stale_expression_cannot_submit_after_world_step(self):
        c=self.make();eid=c.apply('message',{'text':'你想做什么'})['id']
        c.apply('interpret',{'source':eid,'packet':{'reports':[],'request':{'kind':'none'}}})
        p=deepcopy(c.state['pending']);c.apply('agent_step',{})
        with self.assertRaises(ValueError):c.apply('expression',{'state_id':p['state_id'],'speech':'旧状态的输出'})
    def test_read_only_view_and_context(self):
        c=self.make();s=c.checkpoint();c.view();c.context();self.assertEqual(s,c.checkpoint())
    def test_exact_recorded_input_replay_and_rehashed_tamper(self):
        c=self.make();c.apply('agent_step',{});c.apply('message',{'text':'感觉如何'});c.apply('local_reply',{})
        data=c.checkpoint();d=SharedCore.restore(json.loads(json.dumps(data)));self.assertEqual(canonical(c.snapshot()),canonical(d.snapshot()))
        bad=deepcopy(data);bad['events'][0]['result']['forged']=True;previous=digest(bad['metadata'])
        for e in bad['events']:
            e['previous']=previous;e.pop('hash');e['hash']=digest(e);previous=e['hash']
        bad['head']=previous
        with self.assertRaises(ValueError):SharedCore.restore(bad)
    def test_expedition_retains_learning(self):
        c=self.make();c.apply('agent_step',{});before=deepcopy(c.mind.interests)
        c.apply('new_expedition',{});self.assertEqual(c.world.tick,0);self.assertEqual(before,c.mind.interests)
    def test_new_expedition_focus_references_new_observation(self):
        c=self.make();c.apply('agent_step',{});e=c.apply('new_expedition',{})
        self.assertEqual(c.mind.focus['basis'],e['id'])
        self.assertTrue(any(o['id']==e['id'] for o in c.state['observations']))
