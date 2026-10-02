import copy
import math
import unittest

from switchlab.world import World, Config
from switchlab.model import BeliefModel, physical_projection, likelihood, STATES


class WorldTests(unittest.TestCase):
    def test_public_observation_has_no_hidden_state(self):
        w = World(Config(seed=7))
        o = w.observe()
        self.assertEqual(set(o), {'tick', 'energy', 'coolant', 'progress', 'deadline',
                                 'contract_id', 'pending', 'completed', 'missed'})
        o['energy'] = -100
        self.assertGreater(w.observe()['energy'], 0)

    def test_determinism(self):
        a, b = World(Config(seed=17)), World(Config(seed=17))
        for action in ['e0', 'calibrate', 'repair', 'c1', 'work', 'noise'] * 5:
            self.assertEqual(a.step(action), b.step(action))
            self.assertEqual(a.snapshot(), b.snapshot())

    def test_invalid_action_has_no_effect(self):
        w = World(Config(seed=1)); before = w.snapshot()
        with self.assertRaises(ValueError): w.step('delete_file')
        self.assertEqual(before, w.snapshot())

    def test_physical_model_matches_world_public_transition(self):
        for seed in range(4):
            w = World(Config(seed=seed))
            for action in ['e0','c1','calibrate','probe_e','probe_c','repair',
                           'hand_energy','hand_coolant','work','noise','wait'] * 3:
                before = w.observe(); tr = w.step(action)
                predicted, reward = physical_projection(before, action, tr['outcome'])
                self.assertEqual(predicted, tr['after'])
                self.assertAlmostEqual(reward, tr['reward'])

    def test_resume_world_is_exact(self):
        w = World(Config(seed=81))
        for _ in range(7): w.step('e0')
        restored = World.from_snapshot(w.snapshot())
        for action in ['c0','probe_c','work','repair'] * 4:
            self.assertEqual(w.step(action), restored.step(action))

    def test_intervention_not_announced_to_agent(self):
        w = World(Config(seed=2)); o = w.observe()
        w.intervene('damage_tool')
        self.assertEqual(o, w.observe())
        self.assertEqual(w.snapshot()['hidden'][2], 0)

    def test_keyed_world_modes_not_action_rng_consumption(self):
        a,b=World(Config(seed=81)), World(Config(seed=81))
        for _ in range(60):
            a.step('noise'); b.step('wait')
            self.assertEqual(a.snapshot()['hidden'], b.snapshot()['hidden'])


class BeliefTests(unittest.TestCase):
    def test_probability_simplex(self):
        m=BeliefModel(); w=World(Config(seed=22))
        for a in ['e0','e1','c0','calibrate','probe_e','probe_c','noise']*4:
            tr=w.step(a); m.update(a,tr['outcome'])
            self.assertAlmostEqual(sum(m.belief),1)
            self.assertTrue(all(math.isfinite(x) and x>=0 for x in m.belief))

    def test_informative_probe_reduces_entropy(self):
        m=BeliefModel(); before=m.entropy()
        posterior=m.condition('probe_e','1',advance=False)
        self.assertLess(posterior.entropy(), before)
        self.assertGreater(posterior.marginals()['energy_mode_1'], .85)

    def test_noise_has_zero_evidence(self):
        m=BeliefModel()
        for outcome in ['0','1']:
            post=m.condition('noise',outcome,advance=False)
            self.assertEqual(m.belief,post.belief)

    def test_diagnostics_separate_self_and_world(self):
        m=BeliefModel()
        post=m.condition('calibrate','0',advance=False)
        self.assertLess(post.marginals()['tool_healthy'],m.marginals()['tool_healthy'])
        self.assertAlmostEqual(post.marginals()['energy_mode_1'],.5)

    def test_predictions_normalized(self):
        m=BeliefModel()
        for a in ['e0','e1','c0','c1','calibrate','probe_e','probe_c','noise','repair','work','wait']:
            self.assertAlmostEqual(sum(p for _,p in m.predict(a)),1)

    def test_frozen_evidence_does_not_learn(self):
        m=BeliefModel(freeze=True); before=list(m.belief)
        m.update('probe_e','1')
        self.assertEqual(before,m.belief)

    def test_likelihood_family_has_no_state_truth_input(self):
        self.assertEqual(len(STATES),8)
        self.assertEqual(likelihood('noise','1',STATES[0]),.5)
        self.assertEqual(likelihood('noise','1',STATES[-1]),.5)

    def test_snapshot_is_json_roundtrippable(self):
        import json
        m=BeliefModel();m.update('e1','yield')
        restored=BeliefModel.from_snapshot(json.loads(json.dumps(m.snapshot())))
        self.assertEqual(m.snapshot(),restored.snapshot())

    def test_invalid_beliefs_rejected(self):
        with self.assertRaises(ValueError): BeliefModel(belief=[float('nan')]*8)
        with self.assertRaises(ValueError): BeliefModel(belief=[1.0])
