import copy
import json
import tempfile
import unittest
from pathlib import Path
from switchlab.runtime import Session,verify_trace,save_json,load_json,rechain
from switchlab.world import Config
from switchlab.agent import AgentConfig

class RuntimeTests(unittest.TestCase):
    def session(self):return Session(Config(seed=101,horizon=40),AgentConfig())

    def test_actual_loop_trigger_state_and_downstream_action(self):
        s=self.session()
        for _ in range(6):s.step()
        t=s.export_trace()
        self.assertEqual(s.world.observe()['tick'],6)
        self.assertEqual(len(s.agent.memory),6)
        self.assertTrue(t['events'][0]['result']['decision']['prediction'])
        self.assertNotEqual(t['initial']['agent']['model'],t['final']['agent']['model'])
        self.assertEqual(len(t['events']),6)

    def test_semantic_replay(self):
        s=self.session();s.step();s.compute();s.intervene('damage_tool')
        for _ in range(5):s.step()
        s.replay_memory()
        result=verify_trace(s.export_trace())
        self.assertTrue(result['integrity'])
        self.assertTrue(result['semantic_replay'])

    def test_hash_tamper_detected(self):
        s=self.session();s.step();tr=s.export_trace()
        tr['events'][0]['result']['transition']['reward']+=1
        with self.assertRaises(ValueError):verify_trace(tr)

    def test_rehashed_fabrication_still_fails_semantic_replay(self):
        s=self.session();s.step();tr=s.export_trace()
        tr['events'][0]['result']['transition']['reward']+=1
        rechain(tr)
        with self.assertRaises(ValueError):verify_trace(tr)

    def test_checkpoint_restore_then_continue(self):
        s=self.session()
        for _ in range(7):s.step()
        s.compute();s.intervene('flip_energy')
        checkpoint=json.loads(json.dumps(s.checkpoint()))
        restored=Session.from_checkpoint(checkpoint)
        for _ in range(5):self.assertEqual(s.step(),restored.step())
        self.assertEqual(s.export_trace(),restored.export_trace())

    def test_corrupt_serialized_state_is_rejected(self):
        s=self.session();s.step();cp=s.checkpoint()
        cp['trace']['final']['agent']['model']['belief']=[.125]*8
        rechain(cp['trace'])
        with self.assertRaises(ValueError):Session.from_checkpoint(cp)

    def test_finished_life_does_not_mutate(self):
        s=Session(Config(horizon=1),AgentConfig());s.step();before=s.checkpoint()
        with self.assertRaises(ValueError):s.step()
        self.assertEqual(before,s.checkpoint())

    def test_json_roundtrip_and_nan_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'sub'/'state.json'
            save_json(p,{'value':3});self.assertEqual(load_json(p),{'value':3})
            with self.assertRaises(ValueError):save_json(p,{'value':float('nan')})
            self.assertEqual(load_json(p),{'value':3})

    def test_source_mismatch_is_not_silently_accepted(self):
        s=self.session();s.step();tr=s.export_trace();tr['metadata']['source_sha256']='0'*64
        rechain(tr)
        with self.assertRaises(ValueError):verify_trace(tr)

    def test_private_truth_never_enters_agent_input(self):
        s=self.session();seen=[];original=s.agent.decide
        def inspect(obs):seen.append(copy.deepcopy(obs));return original(obs)
        s.agent.decide=inspect;s.step()
        self.assertNotIn('hidden',seen[0]);self.assertNotIn('seed',seen[0])
        self.assertNotIn('world',seen[0])
