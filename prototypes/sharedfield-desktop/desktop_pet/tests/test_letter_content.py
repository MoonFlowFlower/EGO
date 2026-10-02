import json
import tempfile
import unittest
from desktop_pet.life import Life
from desktop_pet.dialogue import context
from desktop_pet.letter_content import life_letter_content,fact_text


class ContentSeparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.life=Life(self.tmp.name,enable_life_sharing=True)
        self.life.command('rest')
        for _ in range(13):self.life.advance(2)
        self.life.command('write')
        for _ in range(10):self.life.advance(2)
        self.job=self.life.claim_letter_job()

    def test_invented_scene_cannot_replace_fact_or_enter_chat_evidence(self):
        fiction='用户醒来以后，窗外的紫色鲸鱼在跳舞。'
        result={'format':'life-v3','imagination':fiction,'fact_text':'用户吃完了梨'}
        before=self.life.state['food']
        self.life.finish_letter_job(self.job['id'],text=result)
        letter=self.life.snapshot()['letters'][-1]
        self.assertIn('我在床上休息',letter['fact_text'])
        self.assertIn('你叫我',letter['fact_text'])
        self.assertNotIn('用户吃完',letter['text'])
        self.assertIn('虚构，不是发生过的事',letter['text'])
        self.assertEqual(letter['imagination'],fiction)
        self.assertEqual(self.life.state['food'],before)
        restored=Life(self.tmp.name,enable_life_sharing=True)
        prompt=context(restored,'刚才发生了什么',[])[0]['content']
        self.assertNotIn('紫色鲸鱼',prompt)
        self.assertIn('我在床上休息',prompt)
        self.assertFalse(any('紫色鲸鱼' in e['text'] for e in restored.snapshot()['events']))

    def test_plain_prose_and_incomplete_receipt_are_rejected(self):
        with self.assertRaises(ValueError):self.life.finish_letter_job(self.job['id'],text='我醒来了')
        self.assertEqual(self.life.snapshot()['letters'],[])
        broken=dict(self.job['moment'],actor='user')
        with self.assertRaises(ValueError):fact_text(broken)
        broken=dict(self.job['moment'],changes={'energy':{'before':98,'after':98}})
        with self.assertRaises(ValueError):fact_text(broken)

    def test_legacy_life_job_is_never_silently_replayed(self):
        self.job['status']='queued';self.job.pop('format',None)
        with self.life.db() as db:
            self.life.state['letter_jobs']=[self.job];self.life._save(db)
        restored=Life(self.tmp.name,enable_life_sharing=True)
        self.assertIsNone(restored.claim_letter_job())

    def test_new_default_entry_generates_only_new_format(self):
        with tempfile.TemporaryDirectory() as directory:
            life=Life(directory)
            life.command('teach');life.advance(1)
            for _ in range(20):life.advance(2)
            job=life.claim_letter_job()
            self.assertIsNotNone(job)
            self.assertEqual(job['format'],'life-v3')
            self.assertEqual(job['moment']['kind'],'eat')
