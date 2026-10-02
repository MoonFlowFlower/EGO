import unittest
from switchlab.world import World,Config
from switchlab.model import BeliefModel
from switchlab.rollout import rollout_plan

class RolloutTests(unittest.TestCase):
    def test_deterministic_bounded_imagination(self):
        w=World(Config());o=w.observe();m=BeliefModel();before=m.snapshot()
        a=rollout_plan(o,m);b=rollout_plan(o,m)
        self.assertEqual(a,b)
        self.assertEqual(before,m.snapshot())
        self.assertEqual(w.observe(),o)
        self.assertEqual(a['planning_horizon'],10)
        self.assertLessEqual(a['nodes'],13*8*10)

    def test_random_sensor_cannot_manufacture_value(self):
        o=World(Config()).observe();m=BeliefModel()
        d=rollout_plan(o,m)
        self.assertAlmostEqual(d['scores']['wait']-d['scores']['noise'],.15,places=8)

    def test_continuations_are_present(self):
        d=rollout_plan(World(Config()).observe(),BeliefModel())
        self.assertTrue(d['branches'])
        self.assertTrue(all('next_action' in x for x in d['branches']))
        self.assertEqual(d['method'],'particle_rollout_mpc')

    def test_controller_can_select_preserved_short_horizon(self):
        from switchlab.agent import AgentConfig
        self.assertEqual(AgentConfig(planner='two_step').planner,'two_step')
        self.assertEqual(AgentConfig().planner,'rollout')
