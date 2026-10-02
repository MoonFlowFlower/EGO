import tempfile
import unittest
from pathlib import Path
import json
import re
from unittest.mock import patch

class GrowthTests(unittest.TestCase):
    def test_invalid_experience_cannot_be_laundered_through_uncited_intent(self):
        from memory_lab.growth import safe_learning_trace
        entry={'id':'A','source_ids':['deleted'],'text':'DELETED_SECRET'}
        row={'action':{'type':'wait','evidence_ids':[]},'experience_supplied':'[A] DELETED_SECRET',
             'decision':{'intent':'DELETED_SECRET','experience_ids':['A']}}
        self.assertEqual(safe_learning_trace([row],[{'id':'valid'}],[entry]),[])
        row['experience_supplied']='';row['input_source_ids']=['deleted']
        self.assertEqual(safe_learning_trace([row],[{'id':'valid'}],[]),[])
    def test_official_ace_updates_counts_only_for_experience_used_in_real_trace(self):
        from memory_lab.growth import Learner
        def reply(value):return {'id':'offline-fixture','model':'offline-fixture','choices':[{'message':{'content':json.dumps(value)}}]}
        case={'id':'dev-fixture','split':'development','phases':[]}
        event={'id':'teaching','text':'累了睡觉','kind':'user_statement','actor':'user','at':1}
        with tempfile.TemporaryDirectory() as td, patch('memory_lab.growth.scope'):
            learner=Learner(Path(td))
            row={'action':{'type':'sleep'},'receipt':{'ok':True,'state_changes':{'energy':100}},
                 'observation_after':{'energy':100},'experience_supplied':'','decision':{'intent':'休息','experience_ids':[]}}
            with patch('memory_lab.growth.completion',side_effect=[
                reply({'bullet_tags':[]}),reply({'reasoning':'fixture','operations':[{'type':'ADD','section':'life','content':'体力低时执行sleep；来源teaching'}]})]):
                learner.learn(case,[row],[event])
            self.assertIn('体力低',learner.playbook)
            self.assertEqual(len(learner.entries),1)
            self.assertEqual(learner.entries[0]['source_ids'],['teaching'])
            bullet=re.search(r'\[([^\]]+)\]',learner.playbook).group(1)
            row['experience_supplied']=learner.playbook;row['decision']['experience_ids']=[bullet]
            with patch('memory_lab.growth.completion',side_effect=[
                reply({'bullet_tags':[{'id':bullet,'tag':'helpful'}]}),reply({'reasoning':'fixture','operations':[]})]):
                learner.learn(case,[row],[event])
            self.assertIn('helpful=1',learner.playbook)
            self.assertFalse(list(Path(td).rglob('curator_failures.txt')),'Official curation must not silently fail')
            with patch('memory_lab.growth.completion') as call:
                with self.assertRaises(ValueError):learner.learn(case,[dict(row,experience_supplied='wrong')],[event])
                call.assert_not_called()
            learner.invalidate(['teaching'])
            self.assertEqual(learner.entries,[])
            self.assertEqual(learner.playbook,'')

    def test_holdout_cannot_update_experience(self):
        from memory_lab.growth import Learner
        with tempfile.TemporaryDirectory() as td:
            learner=Learner(Path(td),load_components=False)
            with self.assertRaises(ValueError):learner.learn({'split':'heldout'},[],[])

    def test_learning_feedback_contains_results_not_private_scores(self):
        from memory_lab.growth import learning_input
        case={'id':'c','split':'development','family':3,'history':[],
              'phases':[{'notice':'体力低','expect':{'rested':True},'forbid':['wait']} ]}
        trace=[{'action':{'type':'wait'},'receipt':{'ok':True,'state_changes':{}},'final_state':{'energy':5}}]
        text=learning_input(case,trace,[])
        self.assertIn('state_changes',text)
        self.assertNotIn('expect',text)
        self.assertNotIn('forbid',text)
        self.assertNotIn('success',text)
