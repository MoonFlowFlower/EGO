import tempfile
import unittest
from pathlib import Path
from desktop_pet.life import Life


class LifeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.life=Life(Path(self.temp.name))

    def test_meal_finishes_once_and_survives_reopen(self):
        before=self.life.snapshot()['food']
        self.life.command('eat',{},'meal-1')
        self.life.command('eat',{},'meal-1')
        for _ in range(25):self.life.advance(2)
        state=self.life.snapshot()
        self.assertEqual(state['food'],before-1)
        self.assertLess(state['hunger'],20)
        restored=Life(Path(self.temp.name)).snapshot()
        self.assertEqual(restored['food'],state['food'])
        self.assertEqual(restored['hunger'],state['hunger'])

    def test_teaching_changes_next_choice_and_is_persistent(self):
        self.life.command('teach',{},'teach-1')
        other=Life(Path(self.temp.name))
        self.assertTrue(other.snapshot()['selfcare'])
        other.advance(1)
        self.assertEqual(other.snapshot()['activity']['kind'],'eat')

    def test_busy_does_not_generate_filler_without_new_material(self):
        self.life.command('busy',{'minutes':5},'busy-1')
        for _ in range(95):self.life.advance(2)
        state=self.life.snapshot()
        self.assertFalse(state['letters'])
        self.assertFalse(any(x['kind']=='contact' for x in state['events']))

    def test_reopening_does_not_add_offline_activity(self):
        before=self.life.snapshot()
        after=Life(Path(self.temp.name)).snapshot()
        self.assertEqual(before['active_seconds'],after['active_seconds'])
        self.assertEqual(before['events'],after['events'])

    def test_workspace_escape_is_rejected(self):
        with self.assertRaises(ValueError):self.life.read_note('../secret.txt')

    def test_return_cancels_busy_commitment(self):
        self.life.command('busy',{'minutes':5},'b')
        self.life.command('return',{},'r')
        self.assertIsNone(self.life.snapshot()['busy_until'])

    def test_forgetting_teaching_disables_future_rule(self):
        self.life.command('teach',{},'t')
        memory=self.life.snapshot()['memories'][0]
        self.life.forget(memory['source'])
        self.assertFalse(Life(Path(self.temp.name)).snapshot()['selfcare'])

    def test_chat_teaching_and_preference_change_real_state(self):
        from desktop_pet.dialogue import apply_teaching
        source=self.life.message('user','以后饿了自己吃饭。我喜欢画画。')
        apply_teaching(self.life,'以后饿了自己吃饭。我喜欢画画。',source)
        s=self.life.snapshot()
        self.assertTrue(s['selfcare'])
        self.assertTrue(any('画画' in m['text'] for m in s['memories']))
        apply_teaching(self.life,'不要自己吃饭了。','correction')
        self.assertFalse(self.life.snapshot()['selfcare'])

    def test_missing_food_asks_for_help_without_inventing_meal(self):
        self.life.command('teach',{},'t')
        with self.life.lock,self.life.db() as db:
            self.life.state['food']=0;self.life._save(db)
        self.life.advance(1)
        state=self.life.snapshot()
        self.assertTrue(any(x['kind']=='help' for x in state['events']))
        self.assertFalse(any(x['kind']=='eat' for x in state['events']))

    def test_incomplete_model_reply_is_logged_and_not_claimed_as_success(self):
        import io,json
        from unittest.mock import patch
        from desktop_pet.dialogue import respond
        reply={'model':'qwen/qwen3.5-flash-02-23','provider':'Alibaba','usage':{'cost':0},'choices':[{'finish_reason':'length','message':{'content':'partial'}}]}
        with patch('desktop_pet.dialogue.read_key',return_value='test-only'),patch('urllib.request.urlopen',return_value=io.BytesIO(json.dumps(reply).encode())) as request:
            with self.assertRaises(RuntimeError):respond(self.life,'你好','test-turn')
            request.assert_called_once()
        self.assertFalse(any(m['role']=='assistant' for m in self.life.snapshot()['messages']))
        with self.life.db() as db:
            records=[json.loads(r[0]) for r in db.execute('SELECT value FROM calls')]
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['status'],'error')

if __name__=='__main__':unittest.main()
