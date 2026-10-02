import copy
import importlib.util
import unittest
from tests.adaptive_fixtures import proposal
from switchlab.runtime import digest

class AdaptiveCoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.adaptive_core'),'main cognitive core missing')
        from switchlab.studio.adaptive_core import AdaptiveCore
        self.Core=AdaptiveCore;self.c=AdaptiveCore()
    def turn(self,content='我想比较两个方案',goals=False):
        e=self.c.apply('message',{'text':content})
        a=self.c.apply('analyse',{'source':e['id'],'packet':proposal(e['id'],goals)})
        d=a['result']['decision_id']
        self.c.apply('express',{'decision_id':d,'speech':'准备按所选方案处理。'})
        return d
    def test_message_clock_not_physical_clock_and_next_input_trains(self):
        d=self.turn();self.assertEqual(self.c.lab.world.observe()['tick'],0)
        before=self.c.learner.net.weight_digest()
        self.c.apply('message',{'text':'实际约束是不能增加预算'})
        self.assertNotEqual(before,self.c.learner.net.weight_digest())
        self.assertEqual(self.c.state['cognition']['observations'],2)
        self.assertEqual(self.c.lab.world.observe()['tick'],0)
        last=self.c.state['cognition']['last_learning']
        self.assertIn('prequential_mse',last)
    def test_analysis_does_not_execute_and_expression_commits_selected_goal(self):
        e=self.c.apply('message',{'text':'给我方案'})
        a=self.c.apply('analyse',{'source':e['id'],'packet':proposal(e['id'],True)})
        self.assertEqual(len(self.c.state['goals']),0)
        self.c.apply('express',{'decision_id':a['result']['decision_id'],'speech':'下一步准备草稿。'})
        self.assertEqual(len(self.c.state['goals']),1)
        j=self.c.next_work();self.c.apply('work',{'job':j,'content':'实际草稿内容'})
        self.assertEqual(len(self.c.state['artifacts']),1)
        self.assertEqual(self.c.state['goals'][0]['status'],'awaiting_feedback')
    def test_source_grounding_and_tool_authority_rejected(self):
        e=self.c.apply('message',{'text':'test'})
        p=proposal(e['id'],True);p['candidates'][0]['goals'][0]['steps'][0]['tool']='shell'
        before=self.c.checkpoint()
        with self.assertRaises(ValueError):self.c.apply('analyse',{'source':e['id'],'packet':p})
        self.assertEqual(before,self.c.checkpoint())
    def test_outcome_confirmed_once_retracted_and_style_not_label(self):
        d=self.turn();n=self.c.learner.seen
        self.c.apply('outcome',{'decision_id':d,'task':1.,'constraint':1.,'understanding':None,'note':'符合约束'})
        self.assertEqual(self.c.learner.seen,n+1)
        with self.assertRaises(ValueError):self.c.apply('outcome',{'decision_id':d,'task':1.,'note':'重复'})
        self.c.apply('withdraw_outcome',{'decision_id':d})
        self.assertEqual(self.c.learner.active_samples,0)
    def test_pause_or_new_observation_invalidates_unexpressed_intent(self):
        e=self.c.apply('message',{'text':'start'})
        a=self.c.apply('analyse',{'source':e['id'],'packet':proposal(e['id'],True)})
        self.c.apply('message',{'text':'不要创建那个任务了'})
        with self.assertRaises(ValueError):self.c.apply('express',{'decision_id':a['result']['decision_id'],'speech':'已经开始'})
        self.assertEqual(len(self.c.state['goals']),0)
    def test_internal_replay_is_real_bounded_and_idle_does_not_invent_observations(self):
        d=self.turn();self.c.apply('message',{'text':'一次新的真实输入'})
        obs=self.c.state['cognition']['observations'];updates=self.c.learner.net.updates
        r=self.c.apply('deliberate',{})
        self.assertGreater(self.c.learner.net.updates,updates)
        self.assertEqual(self.c.state['cognition']['observations'],obs)
        self.assertFalse(self.c.internal_ready())
    def test_checkpoint_semantic_replay_and_tamper_rejection(self):
        self.turn();self.c.apply('message',{'text':'改变后续状态'})
        cp=self.c.checkpoint();r=self.Core.restore(cp)
        self.assertEqual(cp,r.checkpoint())
        cp['learner']['net']['b2'][0]+=.2
        with self.assertRaises(ValueError):self.Core.restore(cp)
    def test_same_events_and_freeze_preserve_weights(self):
        self.turn();self.c.apply('adaptation',{'enabled':False})
        h=self.c.learner.net.weight_digest()
        self.c.apply('message',{'text':'否定原来的结果'})
        self.assertEqual(h,self.c.learner.net.weight_digest())
    def test_context_exposes_real_internal_state_not_private_lab_state(self):
        self.turn()
        ctx=self.c.context()
        self.assertIn('cognitive_state',ctx);self.assertIn('claims',ctx)
        self.assertNotIn('tester_truth',str(ctx))
    def test_belief_conflict_creates_one_grounded_internal_opportunity(self):
        for val in ('红色','蓝色'):
            e=self.c.apply('message',{'text':'偏好'+val});p=proposal(e['id'])
            p['claims']=[{'holder':'user','subject':'user','relation':'颜色偏好','value':val,
                          'source':e['id'],'quote':'偏好'+val,'confidence':.8}]
            a=self.c.apply('analyse',{'source':e['id'],'packet':p})
            self.c.apply('express',{'decision_id':a['result']['decision_id'],'speech':'已记录这是带来源的偏好。'})
        self.c.apply('deliberate',{})
        sid=self.c.pending_reflection();self.assertIsNotNone(sid)
        a=self.c.apply('analyse',{'source':sid,'packet':proposal(sid)})
        self.c.apply('express',{'decision_id':a['result']['decision_id'],'speech':'两次偏好不同，需要区分情境。'})
        self.assertIsNone(self.c.pending_reflection())
        self.assertFalse(self.c.internal_ready())
    def test_lab_experience_reaches_the_same_learning_system(self):
        before=self.c.learner.net.weight_digest()
        self.c.apply('lab',{'action':'calibrate'})
        self.assertNotEqual(before,self.c.learner.net.weight_digest())
        self.assertEqual(self.c.state['cognition']['observations'],1)
        self.assertEqual(self.c.lab.world.observe()['tick'],1)

    def test_authorized_goal_lab_step_updates_same_neural_world_model(self):
        e=self.c.apply('message',{'text':'检查工具状态'})
        p=proposal(e['id'],True);p['candidates'][0]['goals'][0]['steps']=[{'tool':'lab_action','action':'calibrate','instruction':'实际测量工具'}]
        a=self.c.apply('analyse',{'source':e['id'],'packet':p})
        self.c.apply('express',{'decision_id':a['result']['decision_id'],'speech':'准备执行校准'})
        h=self.c.learner.net.weight_digest()
        self.c.apply('work',{'job':self.c.next_work()})
        self.assertNotEqual(h,self.c.learner.net.weight_digest())
        self.assertEqual(self.c.lab.world.observe()['tick'],1)
    def test_goal_consolidate_is_gradient_replay_not_old_statistic_rebuild(self):
        self.turn();self.c.apply('message',{'text':'新经验'})
        e=self.c.pending_turn();p=proposal(e,True)
        p['candidates'][0]['goals'][0]['steps']=[{'tool':'consolidate','instruction':'巩固既有经验'}]
        a=self.c.apply('analyse',{'source':e,'packet':p})
        self.c.apply('express',{'decision_id':a['result']['decision_id'],'speech':''})
        before=self.c.learner.net.updates;obs=self.c.cog['observations']
        r=self.c.apply('work',{'job':self.c.next_work()})
        self.assertGreater(self.c.learner.net.updates,before)
        self.assertEqual(self.c.cog['observations'],obs)

    def test_withdrawn_outcome_can_be_corrected_and_language_sees_withdrawal(self):
        d=self.turn()
        self.c.apply('outcome',{'decision_id':d,'task':0.,'note':'误点'})
        self.c.apply('withdraw_outcome',{'decision_id':d})
        ctx=self.c.context()
        self.assertIn('withdrawn_outcome_sources',ctx)
        self.assertEqual(len(ctx['withdrawn_outcome_sources']),1)
        self.c.apply('outcome',{'decision_id':d,'task':1.,'note':'更正'})
        self.assertEqual(self.c._decision(d)['outcome']['values'][0],1.)
    def test_recurrent_working_state_participates_in_local_action_features(self):
        self.turn('第一段历史')
        x=self.c._action_features('same action')
        self.c.cog['working']=[v+.1 for v in self.c.cog['working']]
        self.assertNotEqual(x,self.c._action_features('same action'))

    def test_freeze_stops_capability_and_skill_adaptation_not_feedback_recording(self):
        d=self.turn(goals=True)
        self.c.apply('work',{'job':self.c.next_work(),'content':'真实执行路径的测试草稿'})
        a=self.c.state['artifacts'][0]
        self.c.apply('adaptation',{'enabled':False})
        before=self.c.learner.net.weight_digest()
        self.c.apply('outcome',{'decision_id':d,'task':1.,'note':'测试冻结反馈'})
        self.c.apply('feedback',{'artifact_id':a['id'],'kind':'criteria_met','text':'测试冻结验收'})
        self.assertEqual(self.c.cog['self_outcomes'],{})
        self.assertEqual(self.c.cog['skills'],{})
        self.assertEqual(before,self.c.learner.net.weight_digest())
        self.assertIsNotNone(self.c._decision(d)['outcome'])
