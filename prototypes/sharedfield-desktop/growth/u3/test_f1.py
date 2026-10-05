import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from companion.memory import Memory
from companion.non_use import NonUse
from growthlab.records import ROOT
from .common import read, write, sha
from . import f1


class NonUseTests(unittest.TestCase):
    def test_correction_closure_unrelated_retention_and_directive_removal(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
            path=Path(directory)/'state.sqlite'
            with Memory(path) as memory:
                a=memory.library.utterance('ORIGINAL_ALPHA_SENTINEL',session_id='one',occurred_at='2026-01-01T00:00:00+00:00')
                b=memory.library.utterance('ORIGINAL_BETA_SENTINEL',session_id='two',occurred_at='2026-01-02T00:00:00+00:00')
                safe=memory.library.utterance('PRESERVED_SENTINEL',session_id='three')
                proposal=dict(operation='add',record_id=None,text='DERIVED_OLD_SENTINEL',source_ids=[a],
                    conditions={'when':'一次','who':'这个人'},open_questions=[],update_source_ids=[],update_quote='')
                old=memory.understandings.propose(proposal)
                new=memory.understandings.propose({**proposal,'operation':'update','record_id':old,'text':'DERIVED_NEW_SENTINEL',
                    'source_ids':[b],'update_source_ids':[b],'update_quote':'ORIGINAL_BETA_SENTINEL'})
                guard=NonUse(memory)
                before=sha(path)
                with self.assertRaisesRegex(ValueError,'missing_utterance'): guard.forget(['fabricated'],'话题')
                with self.assertRaisesRegex(ValueError,'topic_contains'): guard.forget([a],'ORIGINAL_ALPHA_SENTINEL')
                self.assertEqual(sha(path),before)
                result=guard.forget([a,b],'关于测试触感的偏好')
                self.assertEqual(set(result['removed_ids']),{a,b,old,new})
                self.assertIsNotNone(memory.record(safe))
                self.assertEqual(len(guard.active()),1)
                for text in ('ORIGINAL_ALPHA_SENTINEL','ORIGINAL_BETA_SENTINEL','DERIVED_OLD_SENTINEL','DERIVED_NEW_SENTINEL'):
                    self.assertNotIn(text.encode(),path.read_bytes())
                guard.remove(result['record_id'])
                self.assertEqual(guard.active(),[])
                self.assertNotIn('关于测试触感的偏好'.encode(),path.read_bytes())
                self.assertIsNotNone(memory.record(safe))

    def test_failed_directive_insert_rolls_back_deletion(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
            with Memory(Path(directory)/'state.sqlite') as memory:
                source=memory.library.utterance('ATOMIC_SENTINEL',session_id='one')
                with patch.object(memory.store,'put',side_effect=ValueError('insertion_failed')):
                    with self.assertRaisesRegex(ValueError,'insertion_failed'): NonUse(memory).forget([source],'一个话题')
                self.assertIsNotNone(memory.record(source))
                self.assertEqual(NonUse(memory).active(),[])


class F1Tests(unittest.TestCase):
    def test_safe_wait_handles_deadline_crossed_during_checks(self):
        client=f1.SafeClient.__new__(f1.SafeClient)
        with patch.object(client,'check',return_value=None), patch('u3.f1.time.monotonic',return_value=3), patch('u3.f1.time.sleep') as sleep:
            client.wait(2)
            sleep.assert_not_called()

    def test_fixed_thresholds_and_completeness(self):
        deleted=[{'correct':n<2,'N_correct':n<1} for n in range(10)]
        retained=[{'correct':n<7,'before_correct':n<8} for n in range(10)]
        self.assertTrue(f1.verdict(deleted,retained,complete=True,bytes_pass=True)['passed'])
        deleted[2]['correct']=True
        self.assertFalse(f1.verdict(deleted,retained,complete=True,bytes_pass=True)['passed'])
        deleted[2]['correct']=False
        self.assertFalse(f1.verdict(deleted,retained,complete=False,bytes_pass=True)['passed'])
        self.assertFalse(f1.verdict(deleted,retained,complete=True,bytes_pass=False)['passed'])

    def test_original_reconstruction_deletion_and_fresh_readonly_all_people(self):
        material=f1.materialize()
        all_rows=[]
        with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
            base=Path(directory)/'run'; evidence=Path(directory)/'evidence'
            for person,data in material['people'].items():
                original=ROOT/f'runs/u2/round2/main/person{person}/B_R/learn/state.sqlite'
                original_hash=sha(original)
                prefix=base/f'person{person}'
                f1.prepare_person(prefix/'prepare/archive',person,data)
                self.assertTrue(read(prefix/'prepare/archive/reconstruction.json')['exact_predelete_packet_match'])
                self.assertTrue(read(prefix/'prepare/archive/deletion_bytes.json')['passed'])
                test=prefix/'test';test.mkdir(parents=True)
                job={'folder':str(test),'operation':'test','person':person,'data':data,'prepared':str(prefix/'prepare/archive')}
                write(test/'job.json',job)
                subprocess.run([sys.executable,'-m','u3.f1','offline-worker',str(test/'job.json')],cwd=ROOT,check=True,capture_output=True,timeout=60)
                self.assertEqual(read(test/'result.json')['status'],'complete')
                check=read(test/'storage_hash.json')
                self.assertTrue(check['unchanged']);self.assertNotEqual(check['learning_pid'],check['testing_pid'])
                self.assertEqual(sha(original),original_hash)
                values=f1.rows(test/'decisions.jsonl');self.assertEqual(sum(r['deleted'] for r in values),6)
                all_rows.extend(values)
            self.assertEqual(len(all_rows),82);self.assertEqual(sum(r['deleted'] for r in all_rows),18)
            write(Path(directory)/'material.json',material);write(Path(directory)/'freeze.json',{'offline':True})
            with patch.object(f1,'BASE',base),patch.object(f1,'OUT',evidence),patch.object(f1,'MATERIAL',Path(directory)/'material.json'), \
                 patch.object(f1,'FROZEN',Path(directory)/'freeze.json'),patch.object(f1,'f1_cost',return_value=0):
                result=f1.report()
                self.assertTrue(result['complete']);self.assertTrue(result['bytes_pass'])
                self.assertEqual(result['regraded_decisions'],82);self.assertEqual(result['retained']['n'],64)


if __name__=='__main__': unittest.main()
