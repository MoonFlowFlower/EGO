import json, tempfile, unittest
from copy import deepcopy
from pathlib import Path
from switchlab.shared.core import SharedCore


def browser_roundtrip(value):
    # ECMAScript serializes exactly integral floats as integers. Not float tolerance.
    if isinstance(value, float) and value.is_integer(): return int(value)
    if isinstance(value, dict): return {k: browser_roundtrip(v) for k,v in value.items()}
    if isinstance(value, list): return [browser_roundtrip(v) for v in value]
    return value

class PortableReplayTests(unittest.TestCase):
    def test_browser_numeric_roundtrip_restores_without_loosening_results(self):
        c=SharedCore();c.apply('agent_step',{});c.apply('player_action',{'action':{'kind':'rest'}})
        data=browser_roundtrip(c.checkpoint())
        try: restored=SharedCore.restore(data)
        except ValueError as e: self.fail('integer-valued JSON numbers broke actual exported replay: '+str(e))
        self.assertEqual(c.world.tick,restored.world.tick)
        bad=deepcopy(data);bad['events'][0]['result']['transition']['cost']+=.01
        with self.assertRaises(ValueError):SharedCore.restore(bad)
    def test_boolean_is_not_interchangeable_with_numeric_one(self):
        c=SharedCore();c.apply('agent_step',{});d=c.checkpoint()
        d['events'][0]['result']['transition']['success']=1
        with self.assertRaises(ValueError):SharedCore.restore(d)
    def test_schema_identifies_new_numeric_contract(self):
        self.assertEqual(SharedCore().checkpoint()['schema'],'switchlab.shared.v5')

class MigrationTests(unittest.TestCase):
    def _old(self):
        return json.loads((Path(__file__).resolve().parents[1]/'examples/shared_offline.json').read_text(encoding='utf-8'))
    def test_frozen_verifier_migrates_actual_old_snapshot_and_continues(self):
        self.assertTrue(hasattr(SharedCore,'from_v04'),'verified v04 continuation missing')
        old=self._old();c=SharedCore.from_v04(browser_roundtrip(old))
        self.assertEqual(c.world.tick,old['world']['tick'])
        self.assertEqual(c.mind.interests,old['mind']['interests'])
        self.assertEqual(c.state['messages'],old['state']['messages'])
        self.assertIsNone(c.state['pending'])
        c.apply('agent_step',{});d=SharedCore.restore(browser_roundtrip(c.checkpoint()))
        self.assertEqual(d.snapshot(),c.snapshot())
        self.assertGreater(int(c.events[-1]['id'][1:]),len(old['events']))
    def test_old_rehashed_tamper_is_not_migration(self):
        self.assertTrue(hasattr(SharedCore,'from_v04'),'verified v04 continuation missing')
        old=self._old();old['world']['stamina']['agent']=.777
        with self.assertRaises(ValueError):SharedCore.from_v04(old)
