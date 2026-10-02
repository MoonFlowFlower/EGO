from contextlib import ExitStack
import json,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from switchlab.shared.core import SharedCore
from switchlab.shared.service import SharedService

class ContinuationIOTests(unittest.TestCase):
    def test_import_requires_empty_life_or_explicit_archive(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as cleanup:
            s=SharedService(d);cleanup.callback(s.close);s.submit('正在使用的个体')
            self.assertTrue(hasattr(s,'import_checkpoint'),'mainline checkpoint import missing')
            c=SharedCore();c.apply('agent_step',{})
            with self.assertRaises(ValueError):s.import_checkpoint(c.checkpoint())
            self.assertEqual(s.core.state['messages'][0]['text'],'正在使用的个体')
            s.import_checkpoint(c.checkpoint(),archive_current=True)
            self.assertEqual(s.core.world.tick,1);self.assertEqual(s.auto_remaining,0)
            self.assertTrue(list((Path(d)/'archive').glob('*.json')))
    def test_memory_reconstruction_does_not_relearn_physical_evidence(self):
        old=json.loads((Path(__file__).resolve().parents[1]/'examples/shared_offline.json').read_text())
        c=SharedCore.from_v04(old)
        self.assertEqual(c.mind.self_stats,old['mind']['self_stats']);self.assertEqual(c.mind.learned_events,old['mind']['learned_events'])
        self.assertGreater(len(c.mind.memory_cards),0,'migration discarded actual autobiographical evidence')
        self.assertEqual(c.mind.partner_model['updates'],0,'new predictor pretended to have old online training')
    def test_hidden_original_state_is_not_model_context(self):
        old=json.loads((Path(__file__).resolve().parents[1]/'examples/shared_offline.json').read_text())
        c=SharedCore.from_v04(old);ctx=json.dumps(c.context())
        self.assertNotIn('edge_stable',ctx);self.assertNotIn('tool_skill',ctx);self.assertNotIn('origin_digest',ctx)
