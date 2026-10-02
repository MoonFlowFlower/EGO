import tempfile
import unittest
from pathlib import Path
from desktop_pet.life import Life


class NoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.life=Life(self.tmp.name)

    def finish(self,kind):
        self.life.command(kind)
        with self.life.lock,self.life.db() as db:
            self.life._finish(db,self.life.state['activity']);self.life._save(db)

    def test_edit_persists_and_stale_editor_cannot_overwrite(self):
        old=self.life.read_note('给悠小喵的便签.txt')
        saved=self.life.save_note(old['name'],'今天把薄荷搬到了窗台。',old['version'])
        self.assertEqual(Life(self.tmp.name).read_note(old['name'])['text'],saved['text'])
        with self.assertRaises(ValueError):self.life.save_note(old['name'],'旧编辑器覆盖',old['version'])
        with self.assertRaises(ValueError):self.life.save_note('../outside.txt','x',None)

    def test_no_empty_letters_and_one_job_per_completed_note_version(self):
        with self.assertRaises(ValueError):self.life.command('write')
        self.assertEqual(self.life.snapshot()['letters'],[])
        self.life.save_note('今天.txt','薄荷搬到了窗台，我担心下午阳光太强。',None)
        self.life.command('read',{'name':'今天.txt'})
        self.assertIsNone(self.life.claim_letter_job())
        with self.life.lock,self.life.db() as db:
            self.life._finish(db,self.life.state['activity']);self.life._save(db)
        self.finish('write');job=self.life.claim_letter_job()
        self.assertIn('薄荷',job['note']['text'])
        self.assertIsNone(self.life.claim_letter_job())
        self.life.finish_letter_job(job['id'],'你把薄荷搬到窗台啦。我也好奇那里下午的光会不会太强。')
        self.life.command('read',{'name':'今天.txt'})
        with self.life.lock,self.life.db() as db:
            self.life._finish(db,self.life.state['activity']);self.life._save(db)
        with self.assertRaises(ValueError):self.life.command('write')
        self.assertIsNone(self.life.claim_letter_job())
        self.assertEqual(len(self.life.snapshot()['letters']),1)
        self.assertEqual(self.life.snapshot()['letters'][0]['source_note']['text'],job['note']['text'])

    def test_dispatched_job_is_not_replayed_after_restart(self):
        self.life.command('read',{'name':'给悠小喵的便签.txt'})
        with self.life.lock,self.life.db() as db:
            self.life._finish(db,self.life.state['activity']);self.life._save(db)
        self.finish('write');self.assertIsNotNone(self.life.claim_letter_job())
        other=Life(self.tmp.name)
        self.assertIsNone(other.claim_letter_job())
        self.assertEqual(other.snapshot()['letter_work'][-1]['status'],'error')

    def test_reply_uses_completed_read_even_if_file_changes(self):
        from unittest.mock import patch
        from desktop_pet.dialogue import compose_letter
        old=self.life.read_note('给悠小喵的便签.txt')
        self.finish('read')
        self.life.save_note(old['name'],'后来改成了完全不同的内容',old['version'])
        self.finish('write');job=self.life.claim_letter_job()
        with patch('desktop_pet.dialogue.generate',return_value={'reply':'针对原文的回信'}) as generate:
            self.assertEqual(compose_letter(self.life,job),'针对原文的回信')
        messages=generate.call_args.args[1]
        self.assertIn('食物在餐桌旁',messages[-1]['content'])
        self.assertNotIn('后来改成',messages[-1]['content'])
        self.assertEqual(generate.call_args.args[2],'note_letter')
        self.life.finish_letter_job(job['id'],error='测试连接失败')
        with self.assertRaises(ValueError):self.life.command('write')
        self.assertIsNone(self.life.claim_letter_job())
        self.assertEqual(self.life.snapshot()['letters'],[])

    def test_second_read_does_not_lose_first_pending_reply(self):
        self.finish('read')
        self.life.command('write')
        self.life.save_note('第二张.txt','这是第二件小事。',None)
        self.life.command('read',{'name':'第二张.txt'})
        with self.life.lock,self.life.db() as db:
            self.life._finish(db,self.life.state['activity']);self.life._save(db)
        self.life=Life(self.tmp.name)
        self.finish('write');first=self.life.claim_letter_job()
        self.assertEqual(first['note']['name'],'给悠小喵的便签.txt')
        self.life.finish_letter_job(first['id'],text='第一封')
        self.finish('write');second=self.life.claim_letter_job()
        self.assertEqual(second['note']['name'],'第二张.txt')

    def test_saved_version_must_match_when_starting_read(self):
        note=self.life.read_note('给悠小喵的便签.txt')
        self.life.save_note(note['name'],'其他窗口的新版本',note['version'])
        with self.assertRaises(ValueError):self.life.command('read',{'name':note['name'],'version':note['version']})
        self.assertIsNone(self.life.state['last_note'])

