import tempfile
import unittest
from unittest.mock import patch
from desktop_pet.life import Life
from desktop_pet.dialogue import compose_letter


class LifeSharingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.life=Life(self.tmp.name,enable_life_sharing=True)

    def finish_current(self):
        with self.life.lock,self.life.db() as db:
            self.life._finish(db,self.life.state['activity']);self.life._save(db)

    def autonomous_meal(self):
        self.life.command('teach')
        self.life.advance(1)
        self.assertEqual(self.life.state['activity']['kind'],'eat')
        self.finish_current()

    def job_after_writing(self):
        self.life.command('write');self.finish_current()
        return self.life.claim_letter_job()

    def test_actual_autonomous_meal_becomes_quiet_share_once(self):
        self.life.command('busy',{'minutes':60})
        self.life.command('teach');self.life.advance(1)
        self.assertEqual(self.life.snapshot()['letter_work'],[])
        before=self.life.state['food'];self.finish_current()
        self.assertEqual(self.life.state['food'],before-1)
        job=self.job_after_writing()
        self.assertEqual(job['kind'],'life')
        self.assertEqual(job['moment']['initiator'],'autonomous')
        self.assertEqual(job['moment']['changes']['food']['after'],before-1)
        self.life.finish_letter_job(job['id'],text={'format':'life-v3','imagination':'吃完了。这次记得自己去找吃的，想把这件小事告诉你。'})
        s=self.life.snapshot()
        self.assertEqual(len(s['letters']),1)
        self.assertIn('source_moment',s['letters'][0])
        self.assertFalse(any(e['kind']=='contact' for e in s['events']))
        self.life=Life(self.tmp.name,enable_life_sharing=True)
        self.life.state['hunger']=80;self.life.state['activity']=None
        self.life.advance(1);self.finish_current()
        self.assertEqual(len(self.life.snapshot()['letter_work']),1)

    def test_invited_action_is_not_claimed_as_autonomous(self):
        self.life.command('teach');self.life.command('eat');self.finish_current()
        self.assertEqual(self.life.snapshot()['letter_work'],[])
        job=self.job_after_writing()
        self.assertEqual(job['moment']['initiator'],'user')
        self.assertEqual(job['moment']['actor'],'pet')
        self.assertNotIn('teaching',job['moment'])
        with patch('desktop_pet.dialogue.generate',return_value={'reply':'吃好啦'}) as generate:
            compose_letter(self.life,job)
        self.assertEqual(generate.call_args.args[2],'life_imagination')
        self.assertIn('你叫我',generate.call_args.args[1][-1]['content'])
        self.assertIn('悠小喵',generate.call_args.args[1][-1]['content'])

    def test_no_material_write_does_not_start_empty_animation(self):
        with self.assertRaisesRegex(ValueError,'分享'):self.life.command('write')
        self.assertIsNone(self.life.state['activity'])

    def test_forgetting_source_cancels_inflight_and_cannot_revive(self):
        self.autonomous_meal();job=self.job_after_writing()
        source=job['moment']['teaching']['id']
        self.life.forget(source)
        self.life.finish_letter_job(job['id'],text='迟到的模型输出')
        other=Life(self.tmp.name,enable_life_sharing=True)
        self.assertEqual(other.snapshot()['letters'],[])
        self.assertIsNone(other.claim_letter_job())
        self.assertEqual(other.snapshot()['letter_work'][-1]['status'],'cancelled')

    def test_cancel_teaching_stops_autonomous_action_before_completion(self):
        self.life.command('teach');self.life.advance(1)
        before=self.life.state['food']
        self.life.command('unlearn')
        for _ in range(15):self.life.advance(2)
        self.assertEqual(self.life.state['food'],before)
        self.assertEqual(self.life.snapshot()['letter_work'],[])

    def test_deleted_source_withdraws_sent_derivative(self):
        self.autonomous_meal();job=self.job_after_writing()
        self.life.finish_letter_job(job['id'],text={'format':'life-v3','imagination':'从教学衍生的回信'})
        self.life.forget(job['moment']['teaching']['id'])
        self.assertTrue(self.life.snapshot()['letters'][0]['withdrawn'])

    def test_rest_uses_real_energy_change_and_second_milestone(self):
        self.autonomous_meal()
        self.life.state['energy']=20
        self.life.advance(1)
        self.assertEqual(self.life.state['activity']['kind'],'rest')
        self.finish_current()
        self.assertEqual(self.life.state['energy'],98)
        self.assertEqual(len(self.life.snapshot()['letter_work']),2)
        moments=self.life.state['share_moments']
        self.assertEqual(moments[-1]['changes']['energy']['after'],98)
        self.life.command('teach')
        self.life.state['hunger']=80;self.life.advance(1);self.finish_current()
        self.assertEqual(len(self.life.snapshot()['letter_work']),2)

    def test_busy_preserves_in_progress_action(self):
        self.life.command('teach');self.life.advance(1)
        activity=self.life.snapshot()['activity']
        self.life.command('busy',{'minutes':5})
        self.assertEqual(self.life.snapshot()['activity'],activity)

    def test_old_note_jobs_mix_with_new_life_jobs(self):
        self.life.command('read');self.finish_current()
        self.autonomous_meal()
        note=self.job_after_writing();self.assertIn('note',note)
        self.life.finish_letter_job(note['id'],text='便签回信')
        living=self.job_after_writing();self.assertEqual(living['kind'],'life')
        self.life.finish_letter_job(living['id'],text={'format':'life-v3','imagination':'生活分享'})
        self.assertEqual(len(Life(self.tmp.name,enable_life_sharing=True).snapshot()['letters']),2)

    def test_reteaching_then_cancelling_also_cancels_older_pending_share(self):
        self.autonomous_meal();job=self.job_after_writing()
        self.life.command('teach');self.life.command('unlearn')
        self.life.finish_letter_job(job['id'],text='不应再发出的旧教学分享')
        self.assertEqual(self.life.snapshot()['letters'],[])

    def test_disabled_runtime_does_not_dispatch_or_generate_life_jobs(self):
        self.autonomous_meal()
        self.life.command('write');self.finish_current()
        default=Life(self.tmp.name,enable_life_sharing=False)
        self.assertIsNone(default.claim_letter_job())
        before=len(default.state['share_moments'])
        default.command('eat')
        for _ in range(8):default.advance(2)
        self.assertEqual(len(default.state['share_moments']),before)
