import json
import unittest
from switchlab.world import World, Config
from switchlab.model import BeliefModel
from switchlab.agent import Agent, AgentConfig
from switchlab.planner import plan, terminal_value, binary_diagnostic_value

class PlannerTests(unittest.TestCase):
    def test_independent_diagnostic_fixture(self):
        uniform=binary_diagnostic_value(.5,.9,1.)
        sure=binary_diagnostic_value(.98,.9,1.)
        noisy=binary_diagnostic_value(.5,.5,1.)
        self.assertAlmostEqual(uniform['without'],2.)
        self.assertAlmostEqual(uniform['with'],5.4)
        self.assertAlmostEqual(sure['without'],7.68)
        self.assertAlmostEqual(sure['with'],6.68)
        self.assertAlmostEqual(noisy['with'],1.)

    def test_noise_not_rewarded(self):
        o=World(Config()).observe(); result=plan(o,BeliefModel(),depth=2)
        self.assertLess(result['scores']['noise'],result['scores']['wait'])
        self.assertNotEqual(result['action'],'noise')

    def test_history_changes_same_observation_action(self):
        o=World(Config()).observe();o.update(energy=1.,coolant=8.,deadline=None)
        a,b=BeliefModel(),BeliefModel()
        for _ in range(4):
            a.update('probe_e','0'); b.update('probe_e','1')
            a.update('calibrate','1'); b.update('calibrate','1')
        pa,pb=plan(o,a),plan(o,b)
        self.assertEqual(pa['action'],'e0')
        self.assertEqual(pb['action'],'e1')

    def test_needs_not_idle_timer_select_goal(self):
        m=BeliefModel(); e=World(Config()).observe();c=dict(e)
        e.update(energy=1.,coolant=8.,deadline=None)
        c.update(energy=10.,coolant=0.,deadline=None)
        self.assertIn(plan(e,m)['action'],('e0','e1','hand_energy'))
        self.assertIn(plan(c,m)['action'],('c0','c1','hand_coolant'))

    def test_world_observation_is_not_mutated_by_imagination(self):
        w=World(Config());o=w.observe();before=json.dumps(o,sort_keys=True)
        result=plan(o,BeliefModel())
        self.assertEqual(before,json.dumps(o,sort_keys=True))
        self.assertTrue(result['branches'])
        self.assertGreater(result['nodes'],0)

    def test_disabled_viability_changes_objective(self):
        o=World(Config()).observe();low=dict(o,energy=0.)
        self.assertGreater(terminal_value(o),terminal_value(low))
        self.assertEqual(terminal_value(o,viability=False),terminal_value(low,viability=False))

class AgentTests(unittest.TestCase):
    def test_closed_loop_writes_memory_and_changes_belief(self):
        a=Agent(AgentConfig());w=World(Config(seed=3))
        before=a.model.snapshot()
        for _ in range(8):
            d=a.decide(w.observe());a.learn(w.step(d['action']))
        self.assertNotEqual(before,a.model.snapshot())
        self.assertEqual(len(a.memory),8)
        self.assertGreater(a.goal_counter,0)

    def test_replay_cannot_count_evidence_twice(self):
        a=Agent(AgentConfig());w=World(Config(seed=15))
        for _ in range(12):
            d=a.decide(w.observe());a.learn(w.step(d['action']))
        before=a.model.belief[:]
        for _ in range(3): a.replay()
        for x,y in zip(before,a.model.belief): self.assertAlmostEqual(x,y,places=13)

    def test_internal_compute_not_new_observation(self):
        a=Agent(AgentConfig());w=World(Config());before=a.model.snapshot()
        d=a.think(w.observe())
        self.assertEqual(before,a.model.snapshot())
        self.assertEqual(len(a.memory),0)
        self.assertEqual(w.observe()['tick'],0)
        self.assertGreater(d['nodes'],0)

    def test_no_replay_same_actions_exact_filter(self):
        a=Agent(AgentConfig());b=Agent(AgentConfig(ablation='no_replay'))
        wa,wb=World(Config(seed=32)),World(Config(seed=32))
        for _ in range(22):
            da,db=a.decide(wa.observe()),b.decide(wb.observe())
            self.assertEqual(da['action'],db['action'])
            a.learn(wa.step(da['action']));b.learn(wb.step(db['action']))
        self.assertGreater(a.replay_count,b.replay_count)

    def test_flat_baseline_has_equal_information(self):
        a=Agent(AgentConfig(ablation='no_goal_commitment'));b=Agent(AgentConfig(policy='flat_bayes'))
        wa,wb=World(Config(seed=8)),World(Config(seed=8))
        for _ in range(12):
            da,db=a.decide(wa.observe()),b.decide(wb.observe())
            self.assertEqual(da['action'],db['action'])
            a.learn(wa.step(da['action']));b.learn(wb.step(db['action']))
            self.assertEqual(a.model.belief,b.model.belief)

    def test_snapshot_round_trip(self):
        a=Agent(AgentConfig());w=World(Config(seed=42))
        for _ in range(7):
            d=a.decide(w.observe());a.learn(w.step(d['action']))
        b=Agent.from_snapshot(json.loads(json.dumps(a.snapshot())))
        self.assertEqual(a.snapshot(),b.snapshot())
        self.assertEqual(a.decide(w.observe()),b.decide(w.observe()))

    def test_unsupported_modes_rejected(self):
        with self.assertRaises(ValueError): AgentConfig(policy='pretend_neural')
        with self.assertRaises(ValueError): AgentConfig(ablation='silent_fake')

    def test_internal_computation_consumed_by_next_decision(self):
        a=Agent(AgentConfig());o=World(Config()).observe()
        a.think(o);n=a.total_nodes
        d=a.decide(o)
        self.assertTrue(d['used_cached_computation'])
        self.assertEqual(n,a.total_nodes)

    def test_missed_goal_is_abandoned_not_marked_completed(self):
        a=Agent(AgentConfig(planner='two_step'));o=World(Config()).observe()
        a.current_goal={'id':1,'domain':'delivery','target':1,'contract_id':0,
                        'remaining':3,'adopted_tick':0,'source':'predicted_outcome_value'}
        o.update(contract_id=1,completed=0)
        d=a.decide(o)
        self.assertEqual(d['previous_goal_outcome'],'abandoned')
        self.assertEqual(d['goal_event'],'abandoned_then_adopted')

    def test_goal_budget_expiry_is_not_success(self):
        a=Agent(AgentConfig(planner='two_step'));o=World(Config()).observe()
        a.current_goal={'id':1,'domain':'energy','target':11.,'contract_id':0,
                        'remaining':0,'adopted_tick':0,'source':'predicted_outcome_value'}
        d=a.decide(o)
        self.assertEqual(d['previous_goal_outcome'],'budget_exhausted')

    def test_hidden_oracle_interface_cannot_be_called_on_candidate(self):
        a=Agent(AgentConfig())
        with self.assertRaises(PermissionError):a.set_oracle_state([0,0,1])
