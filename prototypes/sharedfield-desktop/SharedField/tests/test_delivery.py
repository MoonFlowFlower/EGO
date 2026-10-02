import json
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from switchlab.server import create_server
from switchlab.runtime import Session
from switchlab.world import Config
from switchlab.agent import AgentConfig
from switchlab.experiments import paired_summary,run_life,build_summary

ROOT=Path(__file__).resolve().parents[1]

class ExperimentTests(unittest.TestCase):
    def test_paired_zero_gap_is_not_positive_evidence(self):
        rows=[]
        for seed in (1,2,3):
            for label in ('candidate','flat_bayes'):
                rows.append({'seed':seed,'scenario':'standard','label':label,'return':5.,'completed':1,'nodes':10})
        s=paired_summary(rows,'standard','flat_bayes')
        self.assertEqual(s['mean_delta'],0.)
        self.assertEqual(s['lives'],3)
        summary=build_summary(rows)
        self.assertEqual(summary['mechanism_status'],'NOT_ESTABLISHED')
        self.assertIn('history-conditioned', ' '.join(summary['missing_baselines']))

    def test_single_life_row_and_actions_are_actual(self):
        row=run_life({'seed':11,'horizon':8,'scenario':'standard','label':'candidate',
                      'policy':'candidate','ablation':'none','planner':'two_step'})
        self.assertEqual(row['steps'],8)
        self.assertEqual(sum(row['action_counts'].values()),8)
        self.assertGreater(row['nodes'],0)

class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=create_server(Session(Config(horizon=20),AgentConfig(planner='two_step')),port=0)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base=f'http://127.0.0.1:{cls.server.server_port}'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=2)
    def request(self,path='/',data=None,token=True,origin=None,host=None):
        headers={}
        if data is not None:
            data=json.dumps(data).encode();headers['Content-Type']='application/json'
            headers['Origin']=self.base if origin is None else origin
            if token:headers['X-SwitchLab-Token']=self.server.token
        if host:headers['Host']=host
        return urllib.request.urlopen(urllib.request.Request(self.base+path,data=data,headers=headers),timeout=10)
    def test_dashboard_and_assets(self):
        with self.request() as r:
            body=r.read().decode();self.assertIn('SwitchLab',body)
            self.assertIn('Content-Security-Policy',r.headers)
        for path in ('/app.js','/style.css','/api/state'):
            with self.request(path) as r:self.assertEqual(r.status,200)
    def test_real_http_step(self):
        with self.request('/api/state') as r:before=json.load(r)['observation']['tick']
        with self.request('/api/command',{'command':'step','count':1}) as r:
            after=json.load(r)['observation']['tick']
        self.assertEqual(after,before+1)
    def test_no_csrf_token_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as c:
            self.request('/api/command',{'command':'step'},token=False)
        self.assertEqual(c.exception.code,403)
    def test_foreign_origin_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as c:
            self.request('/api/command',{'command':'step'},origin='https://attacker.invalid')
        self.assertEqual(c.exception.code,403)
    def test_dns_rebinding_host_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as c:
            self.request('/api/state',host='attacker.invalid')
        self.assertEqual(c.exception.code,403)
    def test_arbitrary_file_path_not_served(self):
        with self.assertRaises(urllib.error.HTTPError) as c:self.request('/../../README.md')
        self.assertEqual(c.exception.code,404)
    def test_invalid_command_and_step_budget_rejected(self):
        for data in ({'command':'shell','text':'ls'},{'command':'step','count':9999},
                     {'command':'step','count':True}):
            with self.assertRaises(urllib.error.HTTPError) as c:self.request('/api/command',data)
            self.assertEqual(c.exception.code,400)
    def test_export_is_checkpoint_not_server_files(self):
        with self.request('/api/export/checkpoint') as r:
            self.assertEqual(json.load(r)['schema'],'switchlab.checkpoint.v1')

class CliTests(unittest.TestCase):
    def test_help_and_actual_run_from_foreign_cwd(self):
        with tempfile.TemporaryDirectory(prefix='switchlab space ') as tmp:
            output=Path(tmp)/'result'
            p=subprocess.run([sys.executable,str(ROOT/'run.py'),'run','--steps','3','--seed','11',
                              '--planner','two_step','--out',str(output)],cwd=tmp,
                             capture_output=True,text=True,timeout=20)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertTrue((output/'trace.json').is_file())
            self.assertTrue((output/'checkpoint.json').is_file())
            self.assertTrue((output/'report.html').is_file())
            q=subprocess.run([sys.executable,str(ROOT/'run.py'),'verify',str(output/'trace.json')],
                             cwd=tmp,capture_output=True,text=True,timeout=20)
            self.assertEqual(q.returncode,0,q.stderr)
    def test_invalid_seed_nonzero_exit(self):
        p=subprocess.run([sys.executable,str(ROOT/'run.py'),'run','--seed','-1'],
                         capture_output=True,text=True,timeout=10)
        self.assertNotEqual(p.returncode,0)

class InterruptedExperimentTests(unittest.TestCase):
    def test_finished_rows_survive_a_later_failed_variant(self):
        from unittest.mock import patch
        from switchlab.experiments import run_benchmark
        variants=[{'label':'valid','policy':'obs_only'}, {'label':'invalid','policy':'not_a_policy'}]
        with tempfile.TemporaryDirectory() as tmp:
            with patch('switchlab.experiments.VARIANTS',variants):
                with self.assertRaises(ValueError):run_benchmark(tmp,seeds=1,stress_seeds=0,jobs=1,horizon=2)
            lines=(Path(tmp)/'rows.partial.jsonl').read_text().splitlines()
            self.assertEqual(len(lines),1)
            self.assertEqual(json.loads(lines[0])['label'],'valid')
            self.assertFalse((Path(tmp)/'summary.json').exists())
