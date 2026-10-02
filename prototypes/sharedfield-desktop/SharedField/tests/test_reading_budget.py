import json
import tempfile
import unittest
from pathlib import Path
from tools.start_reading import BudgetProvider, load_codex_key


class ReadingBudgetTests(unittest.TestCase):
    def test_only_named_codex_key_and_no_ambiguous_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'keys.txt'
            p.write_text('other key\nsk-or-v1-other\ncodex key\nsk-or-v1-designated\n',encoding='utf-8')
            self.assertEqual(load_codex_key(p),'sk-or-v1-designated')
            p.write_text('other key\nsk-or-v1-other',encoding='utf-8')
            with self.assertRaises(ValueError):load_codex_key(p)

    def test_reservation_survives_restart_and_error(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'budget.json'
            provider=BudgetProvider(p,'',max_usd='0.08')
            provider._request=lambda *args: (_ for _ in ()).throw(ValueError('test failure'))
            with self.assertRaises(ValueError):provider.complete([{'role':'user','content':'x'}])
            ledger=json.loads(p.read_text())
            self.assertEqual(ledger['calls'],1)
            self.assertGreater(float(ledger['reserved_usd']),0)
            restored=BudgetProvider(p,'',max_usd='0.08')
            with self.assertRaisesRegex(ValueError,'预算'):restored.complete([{'role':'user','content':'x'}])
            self.assertEqual(json.loads(p.read_text())['calls'],1)

    def test_changed_price_or_configuration_cannot_bypass_budget(self):
        with tempfile.TemporaryDirectory() as d:
            p=BudgetProvider(Path(d)/'budget.json','')
            p.config['model']='another-model'
            with self.assertRaisesRegex(ValueError,'固定'):p.complete([])
