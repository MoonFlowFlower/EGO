import importlib.util
import unittest
class ExperimentContractTests(unittest.TestCase):
    def test_reproducible_offline_tournament_includes_simple_controls(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.experiments'),'callable experiment missing')
        from switchlab.studio.experiments import run_prediction_probe
        a=run_prediction_probe(seed=1,training=24,testing=12)
        b=run_prediction_probe(seed=1,training=24,testing=12)
        self.assertEqual(a,b)
        self.assertEqual(set(a['methods']),{'neural','similarity','adaptive','frozen_prior','oracle'})
        self.assertEqual(a['label_source'],'synthetic_generator')
        self.assertFalse(a['real_language_test'])
        self.assertEqual(a['methods']['oracle']['regret'],0.)

    def test_retention_has_equal_compute_current_only_control(self):
        from switchlab.studio.experiments import run_retention_probe
        r=run_retention_probe()
        self.assertIn('matched_current_only',r)
        self.assertEqual(r['matched_current_only']['gradient_updates'],r['replay']['gradient_updates'])
        self.assertEqual(r['matched_current_only']['new_external_samples'],r['replay']['new_external_samples'])
