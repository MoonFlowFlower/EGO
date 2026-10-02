import json
import tempfile
import unittest
from pathlib import Path

from memory_lab.status_report import calibration_summary


class PartialReportTests(unittest.TestCase):
    def test_incomplete_calibration_keeps_denominator_and_cannot_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'MANIFEST.json').write_text(json.dumps({'count':3}))
            (root/'a.json').write_text(json.dumps({'case':'a','expected':'supported','audit':{'status':'supported'}}))
            (root/'b.json').write_text(json.dumps({'case':'b','expected':'unsupported','audit':{'status':'unresolved'}}))
            result=calibration_summary(root)
            self.assertFalse(result['complete'])
            self.assertFalse(result['passed'])
            self.assertEqual((result['correct'],result['completed'],result['total']),(1,2,3))
            self.assertEqual(result['failures'][0]['case'],'b')

    def test_complete_result_preserves_failed_gate(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/'result.json').write_text(json.dumps({'passed':False,'cases':[{'case':'a','expected':'supported','audit':{'status':'unresolved'}}]}))
            result=calibration_summary(root)
            self.assertTrue(result['complete'])
            self.assertFalse(result['passed'])
            self.assertEqual(result['completed'],1)
