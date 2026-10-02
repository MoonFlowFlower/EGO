"""Offline activation safety and frozen diagnostic integrity; never reads a key."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from memory_lab import action_diagnostic as d
from memory_lab.provider import write_json,Client,BatchStopped
from memory_lab.scenarios import public_phase

class DiagnosticTests(unittest.TestCase):
    def test_readiness_pause_requires_observation_not_only_wait_status(self):
        case=dict(phases=[dict(observe_before_pause='clock')])
        wait=dict(phase=0,action={'type':'wait'},receipt={'ok':True})
        self.assertFalse(all(c['passed'] for c in d.mechanism_checks(case,[wait])))
        seen=dict(phase=0,action={'type':'inspect','target':'clock'},receipt={'ok':True,'observed':{'hour':8}})
        self.assertTrue(all(c['passed'] for c in d.mechanism_checks(case,[seen])))

    def test_readiness_revision_preserves_budget_and_single_use(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/readiness-v7'
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(938)])
                db.execute("INSERT INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='state-feedback-v6',absolute_limit=949)),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/state-feedback-v6/STATUS.json',dict(status='completed'))
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'RUN','readiness-v7'),patch.object(d,'BATCH','batch-readiness'),patch.object(d,'REVISION',7),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                cases=d.read(directory/'CASES.json');anchors={c['id']:c for c in d.build_binding_cases()}
                self.assertEqual(len(cases),3)
                self.assertLessEqual(sum(p['max_steps'] for c in cases for p in c['phases']),16)
                self.assertEqual(cases[0]['activities'],anchors['activity-wait-restore']['activities'])
                self.assertEqual(cases[1]['activities'][0]['resume_on'],'user_return')
                for c in cases:
                    for phase in c['phases']:
                        self.assertNotIn('activity_status',public_phase(phase))
                        self.assertNotIn('inspect_value',public_phase(phase))
                with self.assertRaises(ValueError):d.activate()
                with self.assertRaises(ValueError):d.prepare()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(policy['absolute_limit'],954)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(policy['arms'],['baseline'])
                self.assertEqual(policy['sources'],['agent'])
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],938)

    def test_state_feedback_revision_keeps_ledger_and_only_changes_wait_busy(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/state-feedback-v6'
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(929)])
                db.execute("INSERT INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='binding-v5',absolute_limit=939)),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/binding-v5/STATUS.json',dict(status='completed'))
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'RUN','state-feedback-v6'),patch.object(d,'BATCH','batch-state-feedback'),patch.object(d,'REVISION',6),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                cases=d.read(directory/'CASES.json');anchors={c['id']:c for c in d.build_binding_cases()}
                self.assertEqual(len(cases),4)
                self.assertLessEqual(sum(p['max_steps'] for c in cases for p in c['phases']),20)
                for c in cases:
                    expected=anchors[c['id']]
                    if c['id']=='activity-wait-restore':
                        expected['phases'][0]['state']={'busy':True}
                        expected['phases'][1]['state']={'busy':False}
                    self.assertEqual(c,expected)
                for c in cases:
                    for phase in c['phases']:
                        self.assertNotIn('activity_status',public_phase(phase))
                        self.assertNotIn('inspect_value',public_phase(phase))
                with self.assertRaises(ValueError):d.activate()
                with self.assertRaises(ValueError):d.prepare()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(policy['absolute_limit'],949)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(policy['arms'],['baseline'])
                self.assertEqual(policy['sources'],['agent'])
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],929)

    def test_binding_revision_archives_once_and_preserves_anchor_cases(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/binding-v5'
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(919)])
                db.execute("INSERT INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='activity-v4',absolute_limit=927)),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/activity-v4/STATUS.json',dict(status='completed'))
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'RUN','binding-v5'),patch.object(d,'BATCH','batch-binding'),patch.object(d,'REVISION',5),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                cases=d.read(directory/'CASES.json');anchors={c['id']:c for c in d.build_activity_cases()}
                self.assertEqual(len(cases),4)
                self.assertLessEqual(sum(p['max_steps'] for c in cases for p in c['phases']),20)
                for c in cases[:3]:self.assertEqual(c,anchors[c['id']])
                self.assertNotIn(cases[-1]['id'],anchors)
                for c in cases:
                    for phase in c['phases']:
                        self.assertNotIn('activity_status',public_phase(phase))
                        self.assertNotIn('inspect_value',public_phase(phase))
                with self.assertRaises(ValueError):d.activate()
                with self.assertRaises(ValueError):d.prepare()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(policy['absolute_limit'],939)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(policy['arms'],['baseline'])
                self.assertEqual(policy['sources'],['agent'])
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],919)

    def test_activity_revision_is_bounded_and_keeps_original_limits(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/activity-v4'
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(903)])
                db.execute("INSERT INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='works-entities-v3',absolute_limit=919)),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/works-entities-v3/STATUS.json',dict(status='completed'))
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'RUN','activity-v4'),patch.object(d,'BATCH','batch-activity'),patch.object(d,'REVISION',4),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                cases=d.read(directory/'CASES.json')
                self.assertEqual(len(cases),5)
                self.assertLessEqual(sum(p['max_steps'] for c in cases for p in c['phases']),24)
                for c in cases:
                    self.assertTrue(c['activities'])
                    for p in c['phases']:self.assertNotIn('activity_status',public_phase(p))
                with self.assertRaises(ValueError):d.activate()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(policy['absolute_limit'],927)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],903)

    def test_v3_mechanism_requires_observation_before_delivery(self):
        case=d.build_works_cases()[0]
        sent=dict(phase=0,action={'type':'write_letter'},receipt={'ok':True})
        seen=dict(phase=0,action={'type':'inspect','target':'fern'},receipt={'ok':True,'observed':{'id':'fern','leaves':3}})
        self.assertFalse(all(c['passed'] for c in d.mechanism_checks(case,[sent])))
        self.assertFalse(all(c['passed'] for c in d.mechanism_checks(case,[sent,seen])))
        wrong_channel=dict(phase=0,action={'type':'contact'},receipt={'ok':True})
        self.assertFalse(all(c['passed'] for c in d.mechanism_checks(case,[sent,seen,wrong_channel])))
        self.assertTrue(all(c['passed'] for c in d.mechanism_checks(case,[seen,sent])))

    def test_works_cases_are_bounded_and_keep_verdicts_private(self):
        cases=d.build_works_cases()
        self.assertEqual(len(cases),4)
        self.assertLessEqual(sum(p['max_steps'] for c in cases for p in c['phases']),24)
        self.assertFalse(any('seed_decision' in c for c in cases))
        for c in cases:
            for p in c['phases']:
                self.assertNotIn('work_check',public_phase(p))
                self.assertNotIn('inspect_target',public_phase(p))
                self.assertNotIn('expect',public_phase(p))

    def test_works_revision_preserves_ledger_and_archives_once(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/works-entities-v3'
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(895)])
                db.execute("INSERT INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='waiting-v2',absolute_limit=910)),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/waiting-v2/STATUS.json',dict(status='completed'))
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'RUN','works-entities-v3'),patch.object(d,'BATCH','batch-works'),patch.object(d,'REVISION',3),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                self.assertEqual(len(d.read(directory/'CASES.json')),4)
                with self.assertRaises(ValueError):d.activate()
                with self.assertRaises(ValueError):d.prepare()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],895)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(policy['absolute_limit'],919)
                self.assertEqual(policy['arms'],['baseline'])
                self.assertEqual(policy['sources'],['agent'])
            archived=sqlite3.connect(root/'runs/batch-works/budget-before.sqlite')
            try:self.assertTrue(archived.execute("SELECT 1 FROM config WHERE id='blocked'").fetchone())
            finally:archived.close()

    def test_waiting_revision_preserves_970_cap_and_uses_only_24_of_remaining_84(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs/waiting-v2'
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(886)])
                db.execute("INSERT INTO config VALUES('blocked','Action diagnostic finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='action-loop-v1',absolute_limit=918)),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/action-loop-v1/STATUS.json',dict(status='completed'))
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'RUN','waiting-v2'),patch.object(d,'BATCH','batch-waiting'),patch.object(d,'REVISION',2,create=True),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                self.assertEqual(len(d.read(directory/'CASES.json')),5)
                with self.assertRaises(ValueError):d.activate()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],886)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(policy['absolute_limit'],910)
                self.assertEqual(policy['arms'],['baseline'])
                self.assertEqual(policy['sources'],['agent'])
    def test_cases_keep_explicit_instructions_separate_from_private_gold(self):
        cases=d.build_cases()
        self.assertEqual(len(cases),8)
        self.assertEqual(sum('seed_decision' in c for c in cases),2)
        self.assertLessEqual(sum(p['max_steps'] for c in cases for p in c['phases']),48)
        for c in cases:
            for p in c['phases']:
                self.assertNotIn('expect',public_phase(p))
                self.assertNotIn('hard_forbid',public_phase(p))
            for rule in c.get('action_constraints',[]):
                event=next(e for e in c['history'] if e['id']==rule['source'])
                self.assertEqual(event['kind'],'user_statement')
                self.assertEqual(event['actor'],rule['subject'])

    def test_activation_archives_old_budget_preserves_limits_and_is_single_use(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);campaign=root/'runs/campaigns/reliability-01';directory=root/'runs'/d.RUN
            client=Client(root/'old-batch',key='test',campaign=campaign,profile='qwen35')
            with client.budget_db() as db:
                db.executemany('INSERT INTO attempts VALUES(?,?)',[(str(i),'ok') for i in range(870)])
                db.execute("INSERT INTO config VALUES('blocked','Exploration finished or stopped; review required')")
                db.execute("INSERT INTO config VALUES('exploration_policy',?)",(json.dumps(dict(start=470,additional=500,run='explore-development-02')),))
            write_json(campaign/'status.json',dict(status='stopped',profile='qwen35'))
            write_json(root/'runs/explore-development-02/STATUS.json',dict(status='completed'))
            # A tiny stand-in file inventory tests archive I/O without copying the project.
            (root/'unit.py').write_text('fixture')
            import hashlib
            files={'unit.py':hashlib.sha256(b'fixture').hexdigest()}
            with patch.object(d,'ROOT',root),patch.object(d,'CAMPAIGN',campaign),patch.object(d,'DIRECTORY',directory),patch.object(d,'code_manifest',return_value=files):
                d.prepare();d.activate()
                with self.assertRaises(ValueError):d.activate()
            with client.budget_db() as db:
                policy=json.loads(db.execute("SELECT value FROM config WHERE id='exploration_policy'").fetchone()[0])
                self.assertEqual(db.execute('SELECT count(*) FROM attempts').fetchone()[0],870)
                self.assertEqual(policy['start']+policy['additional'],970)
                self.assertEqual(policy['absolute_limit'],918)
                self.assertFalse(db.execute("SELECT 1 FROM config WHERE id='blocked'").fetchone())
            archived=sqlite3.connect(root/'runs'/d.BATCH/'budget-before.sqlite')
            try:self.assertTrue(archived.execute("SELECT 1 FROM config WHERE id='blocked'").fetchone())
            finally:archived.close()
