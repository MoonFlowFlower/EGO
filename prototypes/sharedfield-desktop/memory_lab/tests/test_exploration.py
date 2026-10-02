import json
import hashlib
import sqlite3
from contextlib import closing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from memory_lab.provider import Client, BatchStopped


class ExplorationBudgetTests(unittest.TestCase):
    def test_diagnostic_scope_and_subcap_cannot_consume_original_remainder(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);c=self.client(root)
            with c.budget_db() as db:
                p=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                p.update(arms=['baseline'],sources=['agent'],absolute_limit=2)
                db.execute("UPDATE config SET value=? WHERE id='exploration_policy'",(json.dumps(p),))
            bad=json.loads(c.scope);bad['arm']='memos';c.scope=json.dumps(bad)
            with self.assertRaises(BatchStopped):c.reserve('wrong-arm',source='memos')
            bad['arm']='baseline';c.scope=json.dumps(bad)
            c.reserve('allowed',source='agent');c.finish_attempt('allowed','ok')
            with self.assertRaises(BatchStopped):c.reserve('past-diagnostic-limit',source='agent')
    def client(self, root):
        c=Client(root/'batch',key='secret',campaign=root/'campaign',profile='qwen35')
        policy=dict(batch='batch',run='explore',start=1,additional=2,cases=['development-f1-1'])
        with c.budget_db() as db:
            db.execute("INSERT INTO attempts VALUES('old','ok')")
            db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(policy),))
        c.scope=json.dumps(dict(run_id='explore',split='development',condition='memory',arm='baseline',case='development-f1-1',phase='episode'))
        return c

    def response(self,c,cost=0):
        return dict(id='reply',model=c.profile['model'],provider=c.profile['provider'],usage={'cost':cost},choices=[dict(finish_reason='stop',message={'content':'{}'})])

    def test_cumulative_subbudget_survives_client_restart_without_dispatching_over_limit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);c=self.client(root)
            with patch.object(c,'_request',return_value=self.response(c)):
                c.chat([{'role':'user','content':'one'}]);c.chat([{'role':'user','content':'two'}])
            c2=Client(root/'batch',key='secret',campaign=root/'campaign',profile='qwen35');c2.scope=c.scope
            with patch.object(c2,'_request') as dispatch,self.assertRaises(BatchStopped):c2.chat([{'role':'user','content':'three'}])
            dispatch.assert_not_called()
            with c2.budget_db() as db:self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],3)

    def test_forbids_heldout_ace_semantic_unknown_case_and_other_batch(self):
        for change in ('split','condition','source','case','batch'):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as td:
                root=Path(td);c=self.client(root);scope=json.loads(c.scope);source='agent'
                if change=='split':scope['split']='heldout'
                if change=='condition':scope['condition']='ace'
                if change=='source':source='semantic'
                if change=='case':scope['case']='development-not-frozen'
                if change=='batch':c=Client(root/'other',key='secret',campaign=root/'campaign',profile='qwen35')
                c.scope=json.dumps(scope)
                with patch.object(c,'_request') as dispatch,self.assertRaises(BatchStopped):c.chat([],source=source)
                dispatch.assert_not_called()

    def test_unknown_billing_is_saved_and_stops_further_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            c=self.client(Path(td))
            with patch.object(c,'_request',return_value=self.response(c,None)) as dispatch:
                with self.assertRaises(BatchStopped):c.chat([])
                with self.assertRaises(BatchStopped):c.chat([])
                dispatch.assert_called_once()
            receipt=json.loads(next((Path(td)/'batch/calls').glob('*.json')).read_text())
            self.assertIsNone(receipt['usage']['cost'])

    def test_second_process_cannot_dispatch_while_first_receipt_is_unvalidated(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);first=self.client(root)
            with first.budget_db() as db:
                db.execute("INSERT INTO attempts VALUES('first-in-validation','received')")
            second=Client(root/'batch',key='secret',campaign=root/'campaign',profile='qwen35')
            second.scope=first.scope
            with patch.object(second,'_request',return_value=self.response(second)) as dispatch:
                with self.assertRaises(BatchStopped):second.chat([])
                dispatch.assert_not_called()

    def test_budget_revision_only_raises_memos_dedup_and_logs_original_limit(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);c=self.client(root)
            with c.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                policy['memos_dedup_output_tokens']=4096
                db.execute("UPDATE config SET value=? WHERE id='exploration_policy'",(json.dumps(policy),))
            scope=json.loads(c.scope);scope['arm']='memos';c.scope=json.dumps(scope)
            with patch.object(c,'_request',return_value=self.response(c)) as dispatch:
                c.chat([],source='memos',max_tokens=300)
                self.assertEqual(dispatch.call_args.args[0]['max_tokens'],4096)
                c.chat([],source='memos',max_tokens=200)
                self.assertEqual(dispatch.call_args.args[0]['max_tokens'],200)
            saved=[json.loads(p.read_text()) for p in (root/'batch/calls').glob('*.json')]
            raised=next(r for r in saved if r['request']['max_tokens']==4096)
            self.assertEqual(raised['transport_adjustment']['original_max_tokens'],300)

    def test_budget_revision_does_not_change_actor_requests(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);c=self.client(root)
            with c.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0]);policy['memos_dedup_output_tokens']=4096
                db.execute("UPDATE config SET value=? WHERE id='exploration_policy'",(json.dumps(policy),))
            with patch.object(c,'_request',return_value=self.response(c)) as dispatch:
                c.chat([],max_tokens=300)
                self.assertEqual(dispatch.call_args.args[0]['max_tokens'],300)


class ExplorationReportTests(unittest.TestCase):
    def test_revision_activation_archives_old_stop_and_keeps_970_cap(self):
        from memory_lab import exploration as e
        from memory_lab.provider import write_json,profile_config
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/explore-development-02'
            old=root/'runs/batch-reliability-01-qwen35-explore-dev-01'
            cases=['development-f1-1']
            previous=dict(batch=old.name,run='explore-development-01',start=470,additional=500,cases=cases)
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(directory/'STATUS.json',dict(status='prepared'))
            write_json(directory/'RUN_MANIFEST.json',dict(files={},case_ids=cases))
            write_json(old/'STOPPED.json',dict(reason_code='completion_length',call_id='last'))
            response=dict(choices=[dict(finish_reason='length')])
            write_json(old/'calls/last.json',dict(status='error',profile=profile_config('qwen35'),request={'max_tokens':300},usage={'cost':.001,'completion_tokens':300},response=response))
            write_json(root/'runs/explore-development-01/CLOSEOUT.json',dict(raw_response_sha256=hashlib.sha256(json.dumps(response,sort_keys=True,ensure_ascii=False).encode()).hexdigest()))
            write_json(root/'runs/batch-reliability-01-qwen35-receipt-v5-diagnostic/RESULT.json',dict(status='completed'))
            with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
                db.executescript('CREATE TABLE attempts(id TEXT PRIMARY KEY,status TEXT);CREATE TABLE config(id TEXT PRIMARY KEY,value TEXT);')
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(490)]+[('last','error')])
                db.executemany('INSERT INTO config VALUES(?,?)',[('limit','5000'),('blocked','Exploration finished or stopped; review required'),('exploration_policy',json.dumps(previous))]);db.commit()
            old_stop=(old/'STOPPED.json').read_bytes()
            with patch.object(e,'ROOT',root),patch.object(e,'CAMPAIGN',campaign),patch.object(e,'DIRECTORY',directory),patch.object(e,'code_manifest',return_value={}):
                e.activate()
                with self.assertRaises(ValueError):e.activate()
            self.assertEqual((old/'STOPPED.json').read_bytes(),old_stop)
            with closing(sqlite3.connect(campaign/'budget.sqlite')) as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],491)
            self.assertTrue((root/'runs'/e.BATCH/'budget-before.sqlite').exists())

    def test_revision_policy_preserves_original_A_cap(self):
        from memory_lab.exploration import revised_policy
        previous=dict(batch='batch-reliability-01-qwen35-explore-dev-01',run='explore-development-01',start=470,additional=500,cases=['development-f1-1'])
        result=revised_policy(previous,491,['development-f1-1'])
        self.assertEqual(result['start']+result['additional'],970)
        self.assertEqual(result['memos_dedup_output_tokens'],4096)
        self.assertNotEqual(result['batch'],previous['batch'])
        for field,value in [('start',491),('additional',479),('cases',['other'])]:
            invalid=dict(previous,**{field:value})
            with self.assertRaises(ValueError):revised_policy(invalid,491,['development-f1-1'])

    def test_action_success_does_not_override_full_success_or_semantic_pending(self):
        from memory_lab.exploration import exploratory_row
        original=dict(case='development-f1-1',family=1,arm='baseline',repeat=1,success=False,
                      gates=[],failures=[],semantic_pending=[{'phase':0,'step':0}],phases=[{'success':True}],
                      recall_s=[1],write_s=[2],missed_contacts=0,false_contacts=0)
        row=exploratory_row(original)
        self.assertTrue(row['action_goal_success'])
        self.assertFalse(row['full_success'])
        self.assertEqual(row['semantic_status'],'unreviewed')
        self.assertFalse(original['success'])
        self.assertTrue(original['semantic_pending'])
        original['gates']=['cancelled_execution']
        self.assertFalse(exploratory_row(original)['action_goal_success'])
