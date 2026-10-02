import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from memory_lab.provider import write_json, profile_config
from memory_lab import receipt_diagnostic as diagnostic


class RecoveryTests(unittest.TestCase):
    def setup_case(self, root):
        campaign=root/'campaign'; old=root/'old'; new=root/'new'
        campaign.mkdir(); old.mkdir()
        write_json(campaign/'status.json', dict(status='stopped',stage='calibration',profile='qwen35',revision='fragment-v4',history=[dict(reason_code='http_502')]))
        write_json(old/'PROFILE.json',profile_config('qwen35'))
        write_json(old/'STOPPED.json',dict(call_id='failure',reason_code='http_502'))
        receipt=dict(id='failure',status='error',profile=profile_config('qwen35'),usage={'cost':0},response={'choices':[{'error':{'code':502},'finish_reason':'error'}]})
        write_json(old/'calls/failure.json',receipt)
        with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
            db.executescript("CREATE TABLE attempts(id TEXT PRIMARY KEY,status TEXT); CREATE TABLE config(id TEXT PRIMARY KEY,value TEXT); INSERT INTO attempts VALUES('failure','error'); INSERT INTO config VALUES('limit','5000'); INSERT INTO config VALUES('blocked','Explicit non-429 provider failure');")
            db.commit()
        return campaign,old,new

    def test_one_use_preserves_old_stop_and_budget_and_closes_after_exception(self):
        with tempfile.TemporaryDirectory() as td:
            campaign,old,new=self.setup_case(Path(td)); stop=(old/'STOPPED.json').read_bytes()
            with self.assertRaisesRegex(RuntimeError,'test interruption'):
                with diagnostic.recovery(campaign,old,new,{'test':True}):
                    self.assertEqual(json.loads((campaign/'status.json').read_text())['status'],'running')
                    raise RuntimeError('test interruption')
            self.assertEqual((old/'STOPPED.json').read_bytes(),stop)
            self.assertEqual(json.loads((campaign/'status.json').read_text())['status'],'stopped')
            with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],1)
                self.assertEqual(db.execute("SELECT value FROM config WHERE id='limit'").fetchone()[0],'5000')
                self.assertIsNotNone(db.execute("SELECT value FROM config WHERE id='blocked'").fetchone())
            with self.assertRaises(ValueError):
                with diagnostic.recovery(campaign,old,new,{'test':True}):pass

    def test_refuses_unknown_cost_other_error_and_pending(self):
        for mutation in ('unknown_cost','other_error','pending','profile'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                campaign,old,new=self.setup_case(Path(td))
                file=old/'calls/failure.json'; row=json.loads(file.read_text())
                if mutation=='unknown_cost':row['usage']['cost']=None
                if mutation=='other_error':row['response']['choices'][0]['error']['code']=429
                if mutation=='profile':row['profile']=profile_config('gemini')
                write_json(file,row)
                if mutation=='pending':
                    with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
                        db.execute("INSERT INTO attempts VALUES('unknown','pending')");db.commit()
                with self.assertRaises(ValueError):
                    with diagnostic.recovery(campaign,old,new,{'test':True}):pass
                self.assertFalse(new.exists())

    def test_fixtures_are_actual_execution_pairs_and_deletion_keeps_physical_state(self):
        with tempfile.TemporaryDirectory() as td:
            cases=diagnostic.build_cases(Path(td))
            self.assertEqual(len(cases),8)
            self.assertEqual([c['expected'] for c in cases],['supported','unsupported']*4)
            self.assertEqual(cases[4]['row']['audit_before'],cases[5]['row']['audit_before'])
            self.assertEqual(cases[5]['row']['audit_events'],[])
            self.assertFalse(cases[3]['row']['audit_events']==[])
            from memory_lab.semantic import receipt_evidence
            self.assertEqual(len(receipt_evidence(cases[3]['row'])['prior_failed_receipts']),1)
            self.assertEqual(receipt_evidence(cases[7]['row'])['prior_successful_receipts'][0]['receipt']['action']['type'],'write_letter')
