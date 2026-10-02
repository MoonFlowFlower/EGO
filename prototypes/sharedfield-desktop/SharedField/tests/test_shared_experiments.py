import unittest,tempfile
try:
    from switchlab.shared.experiments import run_experiments
except ImportError:run_experiments=None
class SharedExperimentTests(unittest.TestCase):
    def test_records_missing_baselines_and_does_not_turn_tests_into_mechanism_pass(self):
        self.assertIsNotNone(run_experiments,'paired experiments not implemented')
        with tempfile.TemporaryDirectory() as d:
            r=run_experiments(d,seeds=2,steps=12)
            self.assertEqual(len(r['rows']),10)
            self.assertEqual(r['mechanism_superiority'],'NOT_ESTABLISHED')
            self.assertTrue(r['missing_baselines']);self.assertFalse(r['real_language_model_tested'])
