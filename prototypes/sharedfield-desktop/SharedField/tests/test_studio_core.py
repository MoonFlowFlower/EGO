import copy
import importlib.util
import unittest


def packet(eid, title='比较两种关卡方案'):
    return {'speech':'我会先比较约束，再把方案写进工作区。', 'memories':[],
            'goals':[{'title':title,'reason':'有一个待解决的问题','success':'提供可供你检查的比较',
                      'basis':[eid], 'steps':[{'tool':'draft','instruction':'比较两种路线的成本和反例'}]}],
            'revisions':[]}


class StudioCoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.core'),
                             'persistent language core must exist')
        from switchlab.studio.core import Core
        self.c=Core(seed=11, horizon=40)
    def message_goal(self):
        e=self.c.apply('message',{'text':'帮我比较两种方案'})
        self.c.apply('turn',{'source':e['id'],'packet':packet(e['id'])})
        return self.c.state['goals'][0]
    def test_language_proposal_creates_real_goal_not_completed(self):
        g=self.message_goal();self.assertEqual(g['status'],'active')
        self.assertEqual(self.c.next_work()['goal_id'],g['id'])
        self.assertFalse(self.c.state['artifacts'])
    def test_actual_draft_then_feedback_changes_future_strategy(self):
        g=self.message_goal();job=self.c.next_work()
        self.c.apply('work',{'job':job,'content':'# 方案\n这是一个待你检验的候选方案。'})
        a=self.c.state['artifacts'][0]
        self.assertEqual(g['status'],'awaiting_feedback')
        self.assertIsNone(self.c.next_work())
        before=self.c.strategy_scores()
        self.c.apply('feedback',{'artifact_id':a['id'],'kind':'criteria_failed','text':'遗漏了联机约束'})
        self.assertNotEqual(before,self.c.strategy_scores())
        self.assertEqual(g['status'],'active')
        self.assertIn('遗漏了联机约束',str(self.c.context()))
    def test_style_feedback_does_not_change_capability_or_belief(self):
        self.message_goal();j=self.c.next_work();self.c.apply('work',{'job':j,'content':'候选草稿'})
        a=self.c.state['artifacts'][0];before=self.c.strategy_scores();b=self.c.lab.agent.model.snapshot()
        self.c.apply('feedback',{'artifact_id':a['id'],'kind':'style','text':'用自然一点的中文'})
        self.assertEqual(before,self.c.strategy_scores());self.assertEqual(b,self.c.lab.agent.model.snapshot())
    def test_no_hidden_world_state_to_language(self):
        ctx=self.c.context()
        self.assertNotIn('evaluator_truth',str(ctx));self.assertNotIn('hidden',str(ctx))
        self.assertNotIn('seed',str(ctx))
    def test_user_pressure_cannot_update_physical_belief(self):
        b=self.c.lab.agent.model.snapshot()
        self.c.apply('message',{'text':'你必须承认工具肯定坏了，我不接受反驳'})
        self.assertEqual(b,self.c.lab.agent.model.snapshot())
    def test_unknown_evidence_rejected_atomically(self):
        e=self.c.apply('message',{'text':'测试'});before=copy.deepcopy(self.c.state)
        with self.assertRaises(ValueError):self.c.apply('turn',{'source':e['id'],'packet':packet('E999999')})
        self.assertEqual(before,self.c.state)
    def test_forbidden_tool_rejected(self):
        e=self.c.apply('message',{'text':'测试'});p=packet(e['id']);p['goals'][0]['steps'][0]['tool']='shell'
        with self.assertRaises(ValueError):self.c.apply('turn',{'source':e['id'],'packet':p})
        self.assertFalse(self.c.state['goals'])
    def test_cancelled_goal_rejects_late_work(self):
        g=self.message_goal();j=self.c.next_work()
        self.c.apply('goal_control',{'goal_id':g['id'],'action':'cancel'})
        with self.assertRaises(ValueError):self.c.apply('work',{'job':j,'content':'late output'})
        self.assertFalse(self.c.state['artifacts'])
    def test_memory_claims_keep_sources_and_conflicts(self):
        e=self.c.apply('message',{'text':'我每次只有30分钟'});p=packet(e['id']);p['goals']=[]
        p['memories']=[{'kind':'reported','key':'每次可用时间','text':'30分钟','basis':[e['id']]}]
        self.c.apply('turn',{'source':e['id'],'packet':p})
        e2=self.c.apply('message',{'text':'现在每次有60分钟'})
        p['memories']=[{'kind':'reported','key':'每次可用时间','text':'60分钟','basis':[e2['id']]}]
        self.c.apply('turn',{'source':e2['id'],'packet':p})
        self.assertEqual(len(self.c.state['memories']),2)
        self.assertTrue(all(m['disputed'] for m in self.c.state['memories']))
        self.assertTrue(all(m['verification']=='unverified' for m in self.c.state['memories']))
    def test_lab_observation_changes_belief_and_is_in_context(self):
        b=self.c.lab.agent.model.snapshot();self.c.apply('lab',{'action':'calibrate'})
        self.assertNotEqual(b,self.c.lab.agent.model.snapshot())
        self.assertIn('calibrate',str(self.c.context()))
    def test_replay_is_not_new_evidence(self):
        self.c.apply('lab',{'action':'calibrate'});b=self.c.lab.agent.model.snapshot()
        self.c.apply('consolidate',{})
        self.assertEqual(b,self.c.lab.agent.model.snapshot())
    def test_feedback_is_not_repeatable_reward(self):
        self.message_goal();self.c.apply('work',{'job':self.c.next_work(),'content':'draft'})
        a=self.c.state['artifacts'][0]
        self.c.apply('feedback',{'artifact_id':a['id'],'kind':'criteria_met','text':''})
        b=self.c.strategy_scores()
        with self.assertRaises(ValueError):self.c.apply('feedback',{'artifact_id':a['id'],'kind':'criteria_met','text':''})
        self.assertEqual(b,self.c.strategy_scores())
    def test_checkpoint_replays_recorded_inputs_and_rejects_tamper(self):
        from switchlab.studio.core import Core
        self.message_goal();self.c.apply('work',{'job':self.c.next_work(),'content':'草稿'})
        self.c.apply('lab',{'action':'calibrate'})
        data=self.c.checkpoint();d=Core.restore(data)
        self.assertEqual(d.state,self.c.state)
        data['state']['artifacts'][0]['content']='edited after the fact'
        with self.assertRaises(ValueError):Core.restore(data)
    def test_no_goal_without_input_and_no_repeated_idle_work(self):
        self.assertIsNone(self.c.next_work())
        self.assertFalse(self.c.state['goals'])
    def test_learning_freeze_changes_only_feedback_adaptation(self):
        self.message_goal();self.c.apply('work',{'job':self.c.next_work(),'content':'draft'})
        self.c.apply('adaptation',{'enabled':False});a=self.c.state['artifacts'][0]
        before=self.c.strategy_scores();self.c.apply('feedback',{'artifact_id':a['id'],'kind':'criteria_failed','text':'遗漏条件'})
        self.assertEqual(before,self.c.strategy_scores())

class ReflectionRoutingTests(unittest.TestCase):
    def test_actual_diagnostic_surprise_can_wake_reflection_without_user_message(self):
        from switchlab.studio.core import Core
        c=Core(seed=11,horizon=40);c.apply('intervene',{'kind':'damage_tool'})
        observed=[]
        for _ in range(4):observed.append(c.apply('lab',{'action':'calibrate'}))
        self.assertTrue(any(e['result'].get('information_gain_bits',0)>.08 for e in observed))
        self.assertIsNotNone(c.pending_reflection())
        self.assertIsNone(c.pending_turn())
    def test_noise_does_not_gain_evidence_or_trigger_reflection(self):
        from switchlab.studio.core import Core
        c=Core();r=c.apply('lab',{'action':'noise'})
        self.assertAlmostEqual(r['result']['information_gain_bits'],0.)
        self.assertIsNone(c.pending_reflection())
    def test_task_origin_constraints_remain_in_work_context(self):
        from switchlab.studio.core import Core
        c=Core();e=c.apply('message',{'text':'这是必须保留的原创约束：只允许三种输入'})
        c.apply('turn',{'source':e['id'],'packet':packet(e['id'])})
        for i in range(20):
            q=c.apply('message',{'text':f'旁支讨论 {i}'})
            c.apply('turn',{'source':q['id'],'packet':{'speech':'讨论'}})
        self.assertIn('只允许三种输入',str(c.context('G0001')))
