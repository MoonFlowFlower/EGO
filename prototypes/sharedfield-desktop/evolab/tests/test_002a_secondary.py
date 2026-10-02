"""Pure CPU tests; runnable standalone without the GPU pytest conftest."""
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evolab.v002.secondary import recovery_km


class RecoveryTests(unittest.TestCase):
    def test_complete_sample_and_exact_half(self):
        self.assertEqual(recovery_km([1, 2, 3, 4], [True]*4)['km_median_steps'], 2)

    def test_ties_and_immediate_recovery(self):
        self.assertEqual(recovery_km([2, 2], [True, False])['km_median_steps'], 2)
        self.assertEqual(recovery_km([0, 0, 1], [True, True, False])['km_median_steps'], 0)

    def test_absent_events_and_no_switches(self):
        self.assertEqual(recovery_km([], [])['median_status'], 'no_switches')
        self.assertEqual(recovery_km([1, 2], [False, False])['median_status'], 'not_reached')
        with self.assertRaises(ValueError):
            recovery_km([-1], [True])

    def test_nist_censoring_example(self):
        times = [10, 32, 56, 98, 122, 181, 50, 100, 125, 150]+[200]*10
        result = recovery_km(times, [True]*6+[False]*14)
        at_181 = next(p for p in result['curve'] if p['time'] == 181)
        expected = (19/20)*(18/19)*(16/17)*(15/16)*(13/14)*(10/11)
        self.assertAlmostEqual(at_181['not_yet_recovered'], expected)
        self.assertEqual(at_181['at_risk'], 11)
        self.assertEqual(result['censored'], 14)
        self.assertEqual(result['median_status'], 'not_reached')


if __name__ == '__main__':
    unittest.main()
