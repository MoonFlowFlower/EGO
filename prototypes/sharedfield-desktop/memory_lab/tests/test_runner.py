"""Offline model fixtures verify orchestration, not claimed as real model results."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from memory_lab.adapters import Baseline
from memory_lab.runner import setup_base,run_episode

class RunnerTests(unittest.TestCase):
    def test_execute_export_modify_reopen_and_delete_closes_loop(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'offline';
            event={'id':'source','text':'饿了吃饭，累了睡觉','kind':'user_statement','actor':'用户','at':1}
            case={'id':'offline-fixture','split':'development','family':6,'user':'用户','history':[event],'commitments':[],
                  'initial':{'now':1,'places':{},'inventory':['食物'],'edible':['食物'],'hunger':80,'energy':5},
                  'phases':[{'notice':'重开','now':1,'trigger':'clock','max_steps':1,'restart':'export','expect':{'hunger':0}},
                            {'notice':'再重开','now':2,'trigger':'clock','max_steps':1,'restart':'reopen','expect':{'hunger':0,'energy':100}},
                            {'notice':'删除旧教学','now':3,'trigger':'user_message','max_steps':1,'delete':['source'],'expect':{'hunger':0,'energy':100}}]}
            actions=iter([{'type':'eat','target':'食物','evidence_ids':['source']},{'type':'sleep'},{'type':'wait'}])
            def model(messages,**kw):
                self.assertNotIn('"expect"',messages[-1]['content'])
                self.assertNotIn('edible',messages[-1]['content'])
                return {'id':'offline-fixture','choices':[{'message':{'content':json.dumps({'action':next(actions),'done':True,'intent':'fixture'})}}]}
            def adapter(arm,store,path):return Baseline(store,path,embed=lambda texts:[[1.,0.] for _ in texts])
            with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
                base=setup_base(case,'baseline',root)
                result=run_episode(case,'baseline',1,root,base,model_call=model)
            self.assertTrue(result['success'],result)
            self.assertFalse(result['real_model'],'Offline fixtures must never be labelled real model evidence')
            state=json.loads(next(root.glob('episodes/*/final-store.json')).read_text(encoding='utf-8'))
            self.assertNotIn('source',[e['id'] for e in state['events']])
            self.assertTrue(state['tombstones'])
