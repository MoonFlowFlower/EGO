import tempfile
import unittest
from pathlib import Path

from p7.proxy import BudgetLedger, ProxyError
from .runtime import batch_limit


class RuntimeBudgetTests(unittest.TestCase):
    def test_existing_default_batch_keeps_its_limit(self):
        self.assertEqual(batch_limit({'start_total':1.25,'extra_cap':.5,'limit':1.75}),1.75)

    def test_authorized_increase_reaches_ledger_but_total_cap_still_applies(self):
        limit=batch_limit({'start_total':1.25029185959,'extra_cap':3.74970814041,'limit':5})
        self.assertEqual(limit,5)
        self.assertEqual(batch_limit({'start_total':1.25,'extra_cap':10,'limit':20}),5)
        with tempfile.TemporaryDirectory() as folder:
            ledger=BudgetLedger(Path(folder)/'budget.sqlite',limit)
            ledger.reserve(1.70168216959)  # preserve all previous reservations
            ledger.reserve(.05)
            self.assertAlmostEqual(ledger.total(),1.75168216959)
            with self.assertRaises(ProxyError):ledger.reserve(3.3)
            self.assertAlmostEqual(ledger.total(),1.75168216959)

    def test_all_configured_bounds_apply_and_invalid_numbers_fail(self):
        self.assertEqual(batch_limit({'start_total':1.25,'extra_cap':.5,'limit':4}),1.75)
        self.assertEqual(batch_limit({'start_total':1.25,'extra_cap':3.75,'limit':2}),2)
        for key in ('start_total','extra_cap','limit'):
            for value in (True,-1,float('nan'),float('inf'),'5'):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                    batch_limit({**{'start_total':1.25,'extra_cap':3.75,'limit':5},key:value})


if __name__=='__main__':unittest.main()
