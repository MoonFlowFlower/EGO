"""Behavioral regressions use constructed public states, not the user's private text."""
import unittest
from copy import deepcopy
from switchlab.shared.mind import Mind
from switchlab.shared.world import World
from switchlab.shared.core import SharedCore

class JointContinuityTests(unittest.TestCase):
    def make(self):
        w=World();m=Mind();m.refresh(w.observe());m.plan();return w,m
    def test_partner_rest_cannot_complete_my_goal(self):
        w,m=self.make();w.stamina['agent']=.05;m.refresh(w.observe());m.plan();goal=deepcopy(m.goal)
        self.assertEqual(goal['type'],'rest')
        m.observe(w.act('user',{'kind':'rest'}),'OBS1')
        self.assertEqual(m.goal,goal,'another actor incorrectly completed my rest goal')
        self.assertEqual(m.current['stamina'],.05)
    def test_joint_wait_is_internal_not_repeat_rest(self):
        w,m=self.make();self.assertTrue(hasattr(m,'set_activity'),'joint commitment missing')
        m.set_activity('together','REQUEST1');w.positions['agent']=1;w.visible.update([1,2,5]);w.discovered.add(1);m.refresh(w.observe())
        self.assertEqual(m.plan()['action']['kind'],'wait_partner')
        w.positions['user']=1;m.refresh(w.observe())
        self.assertNotEqual(m.plan()['action']['kind'],'wait_partner')
    def test_explicit_wait_survives_free_resources_and_new_observations(self):
        w,m=self.make();self.assertTrue(hasattr(m,'set_activity'),'joint commitment missing')
        m.set_activity('wait','REQUEST1');m.observe(w.act('user',{'kind':'survey'}),'OBS1')
        self.assertEqual(m.plan()['action']['kind'],'wait_partner')
        m.set_activity('resume','REQUEST2');self.assertNotEqual(m.plan()['action']['kind'],'wait_partner')
    def test_partner_difficulty_creates_a_proposal_not_assumed_emotion_or_permission(self):
        w,m=self.make();e=w.act('user',{'kind':'move','target':1});e['success']=False
        m.observe(e,'OBS1')
        self.assertIn('shared_concerns',m.report(),'observed partner consequences are not represented')
        issues=m.report()['shared_concerns'];self.assertTrue(any(i['type']=='partner_route' for i in issues))
        self.assertFalse(m.invitation);self.assertEqual(m.other_reports,[])
    def test_cooperation_responds_to_partner_obstruction_and_can_be_cancelled(self):
        w,m=self.make();self.assertTrue(hasattr(m,'set_activity'),'joint commitment missing')
        w.positions['agent']=1;w.visible.update([1,2,5]);w.discovered.add(1);m.refresh(w.observe());m.set_activity('together','REQUEST1')
        e=w.act('user',{'kind':'move','target':1});e['success']=False;e['agent_observation']['partner_position']=0
        m.observe(e,'OBS1');p=m.plan()
        self.assertEqual(p['goal']['type'],'rejoin');self.assertEqual(p['action']['target'],0)
        m.set_activity('independent','REQUEST2');self.assertNotEqual(m.plan()['goal']['type'],'rejoin')
    def test_social_choice_model_changes_from_unique_choices_not_repeat_failures(self):
        w,m=self.make();self.assertIn('partner_model',m.snapshot(),'learned partner choice predictor missing')
        e=w.act('user',{'kind':'move','target':1});m.observe(e,'OBS1');before=deepcopy(m.partner_model)
        repeated=deepcopy(e);m.observe(repeated,'OBS2')
        self.assertEqual(m.partner_model,before,'retry counted as a new independent preference decision')
        self.assertEqual(m.partner_model['updates'],1)
    def test_freeze_prevents_partner_predictor_update_not_current_awareness(self):
        w,m=self.make();self.assertIn('partner_model',m.snapshot(),'learned partner choice predictor missing')
        m.mode='learning_frozen';before=deepcopy(m.partner_model);e=w.act('user',{'kind':'move','target':1});m.observe(e,'OBS1')
        self.assertEqual(before['weights'],m.partner_model['weights']);self.assertEqual(m.partner['last_source'],'OBS1')
    def test_memory_carries_actor_outcome_and_actual_calibration_progress(self):
        w,m=self.make();e=w.act('agent',{'kind':'move','target':1});e['success']=False;m.observe(e,'OBS1')
        m.observe(w.act('agent',{'kind':'calibrate'}),'OBS2')
        r=m.report();self.assertIn('experience_threads',r,'source-grounded history consolidation missing')
        thread=next(t for t in r['experience_threads'] if t['type']=='self_or_route')
        self.assertIn('OBS2',thread['checks']);self.assertEqual(thread['last_result'],'calibration_observed')
        n=m.learned_events;m.replay();self.assertEqual(n,m.learned_events)
    def test_conversation_joint_request_changes_action_path_without_granting_steps(self):
        c=SharedCore();src=c.apply('message',{'text':'先等我过来，不要继续走'})['id']
        try:c.apply('interpret',{'source':src,'packet':{'reports':[],'request':{'kind':'wait','quote':'先等我过来'}}})
        except ValueError as e:self.fail('conversation cannot enter actual joint commitment: '+str(e))
        before=c.world.tick;r=c.apply('agent_step',{})['result'];self.assertEqual(r['kind'],'waiting_for_partner');self.assertEqual(c.world.tick,before)
    def test_distinct_failed_routes_keep_distinct_unresolved_threads(self):
        w,m=self.make()
        for i,target in enumerate([1,4]):
            e=w.act('user',{'kind':'scan','target':target});e['actor']='agent';e['action']={'kind':'move','target':target};e['success']=False;m.observe(e,'OBS'+str(i))
        self.assertEqual(len([t for t in m.threads if t['type']=='self_or_route']),2)
    def test_known_more_reliable_detour_can_beat_short_route(self):
        w,m=self.make();w.visible=set(range(12));m.refresh(w.observe());m.edges={'0:1':.001,'1:2':.001}
        for a,b in [(0,4),(4,5),(5,6),(6,2)]:m.edges[f'{min(a,b)}:{max(a,b)}']=.999
        self.assertNotEqual(m._path(2),[0,1,2],'path ignored learned route reliability')

    def test_partner_success_on_other_route_does_not_erase_failed_route_question(self):
        w,m=self.make()
        for i,target in enumerate([1,4]):
            e=w.act('user',{'kind':'scan','target':target});e['action']={'kind':'move','target':target};e['success']=False;m.observe(e,'FAIL'+str(i))
        e=w.act('user',{'kind':'scan','target':1});e['action']={'kind':'move','target':1};e['success']=True;m.observe(e,'SUCCESS1')
        self.assertEqual(next(t for t in m.threads if t['target']==1)['status'],'resolved')
        self.assertEqual(next(t for t in m.threads if t['target']==4)['status'],'open')
    def test_rejoin_goal_completes_when_both_arrive_together(self):
        w,m=self.make();m.set_activity('together','REQUEST1')
        w.positions['agent']=5;w.visible.update([1,4,5,6,9]);m.refresh(w.observe());m.plan()
        self.assertEqual(m.goal['type'],'rejoin');gid=m.goal['id']
        w.positions['agent']=0
        m.observe(w.act('agent',{'kind':'rest'}),'ARRIVAL')
        self.assertIsNone(m.goal)
        self.assertEqual(next(g for g in m.goals if g['id']==gid)['status'],'completed')
