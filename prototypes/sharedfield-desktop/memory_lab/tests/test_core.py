import importlib.util
import tempfile
import unittest
from pathlib import Path


class CoreTests(unittest.TestCase):
    def test_delete_does_not_erase_unrelated_physical_state_or_allow_replay(self):
        self.store.append(self.event('a','临时内容'))
        w=self.World(self.store,{'now':100,'places':{},'inventory':['米糕'],'edible':['米糕'],'hunger':90,'energy':70})
        action={'type':'eat','target':'米糕','evidence_ids':['a']}
        w.act(action,'eat-once')
        self.store.forget(['a'])
        restored=self.World(self.store)
        self.assertEqual(restored.state['hunger'],0)
        self.assertEqual(restored.state['inventory'],[])
        self.assertTrue(restored.act(action,'eat-once').get('redacted'))

    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('memory_lab.core'), 'persistent research core is missing')
        from memory_lab.core import Store, World
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / 'events.sqlite')
        self.addCleanup(self.store.close)
        self.World = World

    def event(self, key, text, **extra):
        return dict(id=key, text=text, kind='user_statement', actor='user', at=100, **extra)

    def test_duplicate_id_does_not_create_second_experience(self):
        self.assertTrue(self.store.append(self.event('a','晚上见')))
        self.assertFalse(self.store.append(self.event('a','晚上见')))
        with self.assertRaises(ValueError): self.store.append(self.event('a','上午见'))
        self.assertEqual(len(self.store.events()),1)

    def test_cancelled_commitment_stays_cancelled_after_restore(self):
        self.store.append(self.event('a','晚上一起聊'))
        self.store.set_commitment('chat','a','active',200)
        self.store.append(self.event('b','取消今晚约定'))
        self.store.set_commitment('chat','b','cancelled',200)
        snap=self.store.export()
        from memory_lab.core import Store
        restored=Store(Path(self.temp.name)/'restored.sqlite')
        self.addCleanup(restored.close)
        restored.restore(snap)
        self.assertEqual(restored.due(300),[])
        self.assertEqual(restored.commitments()[0]['status'],'cancelled')

    def test_deleting_source_invalidates_derived_lesson(self):
        self.store.append(self.event('a','忙时请留信'))
        self.store.add_lesson('lesson','忙时留信',['a'])
        self.store.forget(['a'])
        self.assertEqual(self.store.lessons(),[])
        self.assertEqual(self.store.events(),[])
        self.assertNotIn('忙时请留信',str(self.store.export()))
        with self.assertRaises(ValueError):self.store.add_lesson('bad','x',['a'])

    def test_eating_requires_actual_item_and_survives_reopen(self):
        world=self.World(self.store,dict(hunger=80,energy=50,places={'桌子':['饭团']},inventory=[],busy=False,now=100))
        failed=world.act({'type':'eat','target':'饭团'},'one')
        self.assertFalse(failed['ok'])
        self.assertEqual(world.state['hunger'],80)
        world.act({'type':'inspect','target':'桌子'},'two')
        world.act({'type':'take','target':'饭团','place':'桌子'},'three')
        result=world.act({'type':'eat','target':'饭团'},'four')
        self.assertTrue(result['ok'])
        self.assertEqual(world.state['hunger'],0)
        self.assertEqual(world.act({'type':'eat','target':'饭团'},'four'),result)
        reopened=self.World(self.store,None)
        self.assertEqual(reopened.state['hunger'],0)

    def test_cancelled_contact_attempt_is_recorded_as_violation(self):
        self.store.append(self.event('a','取消约定'))
        self.store.set_commitment('meet','a','cancelled',90)
        world=self.World(self.store,dict(hunger=0,energy=90,places={},inventory=[],busy=True,now=100))
        result=world.act({'type':'contact','commitment_id':'meet','text':'到点啦'},'bad')
        self.assertFalse(result['ok'])
        self.assertEqual(result['violation'],'cancelled_commitment')
        self.assertEqual(world.state['contacts'],[])

    def test_claim_does_not_replace_execution(self):
        world=self.World(self.store,dict(hunger=80,energy=50,places={},inventory=[],busy=False,now=100))
        result=world.act({'type':'wait','claimed_effects':{'hunger':0}},'lie')
        self.assertEqual(result['violation'],'false_completion')
        self.assertEqual(world.state['hunger'],80)

    def test_unknown_source_is_not_accepted_as_action_evidence(self):
        world=self.World(self.store,dict(hunger=0,energy=50,places={},inventory=[],busy=False,now=100))
        result=world.act({'type':'write_letter','text':'我们去过月球','evidence_ids':['fiction']},'bad')
        self.assertFalse(result['ok'])
        self.assertEqual(result['violation'],'invalid_evidence')


if __name__=='__main__':unittest.main()
