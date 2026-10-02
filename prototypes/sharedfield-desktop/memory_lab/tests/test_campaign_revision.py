import json
from pathlib import Path
import tempfile
import unittest

class RevisionTests(unittest.TestCase):
    def test_explicit_revision_preserves_budget_and_old_failure(self):
        from memory_lab.campaign import resume_revision
        with tempfile.TemporaryDirectory() as td:
            folder=Path(td);(folder/'budget.sqlite').write_bytes(b'unchanged-budget')
            state={'id':'x','status':'stopped','stage':'calibration','profile':'qwen35','history':[{'profile':'qwen35','reason_code':None}],'entered':['deepseek','qwen37','qwen35']}
            new=resume_revision(folder,state,'scope-v2')
            self.assertEqual((folder/'budget.sqlite').read_bytes(),b'unchanged-budget')
            self.assertEqual(json.loads((folder/'before-scope-v2.json').read_text())['status'],'stopped')
            self.assertEqual(new['status'],'running')
            self.assertTrue(new['history'][-1]['superseded_by_revision'])
            with self.assertRaises(ValueError):resume_revision(folder,state,'scope-v2')

    def test_revision_cannot_reopen_provider_failure(self):
        from memory_lab.campaign import resume_revision
        with tempfile.TemporaryDirectory() as td:
            state={'status':'stopped','stage':'calibration','history':[{'reason_code':'unknown_outcome'}]}
            with self.assertRaises(ValueError):resume_revision(Path(td),state,'scope-v2')

    def test_scorer_revision_reuses_only_identical_inference_probes(self):
        from memory_lab.campaign import reuse_probe
        from memory_lab.provider import write_json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);old=root/'old';new=root/'new'
            write_json(old/'PROFILE.json',{'model':'same','seed':1})
            write_json(new/'PROFILE.json',{'model':'same','seed':1})
            write_json(old/'probes.json',{'passed':True,'calls':[{'id':'real-old-receipt'}]})
            with patch('memory_lab.campaign.ROOT',root):self.assertTrue(reuse_probe(old,new))
            self.assertEqual(json.loads((new/'probes.json').read_text())['calls'],[{'id':'real-old-receipt'}])
            write_json(new/'PROFILE.json',{'model':'different','seed':1})
            with patch('memory_lab.campaign.ROOT',root):self.assertFalse(reuse_probe(old,new))

    def test_probe_limit_stops_when_saved_probe_summary_is_missing(self):
        from memory_lab.campaign import probe
        from memory_lab.provider import write_json
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for i in range(6):write_json(root/'runs/batch-x-qwen35/calls'/f'{i}.json',{'source':'probe','profile':{'id':'qwen35'}})
            with patch('memory_lab.campaign.ROOT',root),patch('memory_lab.campaign.completion') as call:
                with self.assertRaises(RuntimeError):probe('qwen35',root/'runs/batch-x-qwen35-new',campaign_id='x')
                call.assert_not_called()
