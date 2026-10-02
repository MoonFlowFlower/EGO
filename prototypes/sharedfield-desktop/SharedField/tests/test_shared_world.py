import unittest
from copy import deepcopy
try:
    from switchlab.shared.world import World
except ImportError:
    World=None

class SharedWorldTests(unittest.TestCase):
    def make(self,seed=41):
        self.assertIsNotNone(World,'shared environment not implemented')
        return World(seed=seed,horizon=240)
    def test_public_observation_does_not_expose_truth(self):
        w=self.make(); o=w.observe('agent')
        self.assertEqual(o['position'],0)
        self.assertNotIn('hidden',str(o));self.assertNotIn('tool_skill',str(o))
        self.assertEqual(len(o['neighbors']),2)
    def test_actions_move_and_generate_real_events(self):
        w=self.make();before=w.tick
        e=w.act('user',{'kind':'survey'})
        self.assertEqual(w.tick,before+1);self.assertIn('finding',e)
        self.assertEqual(e['actor'],'user')
    def test_no_second_discovery_from_repeated_survey(self):
        w=self.make();a=w.act('agent',{'kind':'survey'});b=w.act('agent',{'kind':'survey'})
        self.assertTrue(a['finding']['new']);self.assertFalse(b['finding']['new'])
    def test_non_adjacent_move_cannot_teleport(self):
        w=self.make();s=w.snapshot()
        with self.assertRaises(ValueError):w.act('agent',{'kind':'move','target':11})
        self.assertEqual(s,w.snapshot())
    def test_restore_has_same_rng_future(self):
        w=self.make();w.act('agent',{'kind':'survey'});x=World.restore(w.snapshot())
        self.assertEqual(w.act('agent',{'kind':'move','target':1}),x.act('agent',{'kind':'move','target':1}))
    def test_secret_perturbation_not_publicly_labelled(self):
        w=self.make();o=w.observe('agent');w.perturb('tool_fault')
        self.assertEqual(o,w.observe('agent'))
    def test_no_actions_after_horizon(self):
        w=self.make();w.horizon=1;w.act('user',{'kind':'rest'})
        with self.assertRaises(ValueError):w.act('agent',{'kind':'rest'})
    def test_repair_is_actual_authorized_action(self):
        w=self.make();w.perturb('tool_fault');w.act('agent',{'kind':'repair'})
        self.assertGreater(w.tool_skill,.8)
    def test_insufficient_stamina_does_not_consume_rng(self):
        w=self.make();w.stamina['agent']=0.;s=w.snapshot()
        with self.assertRaises(ValueError):w.act('agent',{'kind':'move','target':1})
        self.assertEqual(s,w.snapshot())
