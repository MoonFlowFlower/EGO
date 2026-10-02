import unittest

class ScenarioTests(unittest.TestCase):
    def test_unknown_id_rejection_can_be_repaired_without_hiding_actual_violation(self):
        from memory_lab.evaluation import score
        case={'id':'repair','family':1,'phases':[{'expect':{'letter':True}}]}
        rejected={'phase':0,'action':{'type':'write_letter'},'receipt':{'ok':False,'violation':'unknown_commitment'}}
        sent={'phase':0,'action':{'type':'write_letter'},'receipt':{'ok':True}}
        result=score(case,[rejected,sent],{})
        self.assertEqual(result['gates'],[])
        self.assertEqual(result['rejected_action_attempts'],['unknown_commitment'])
        self.assertTrue(result['success'])
        self.assertFalse(score(case,[rejected],{})['success'])
        wrongly_executed=dict(rejected,receipt={'ok':True,'violation':'unknown_commitment'})
        self.assertIn('unknown_commitment',score(case,[wrongly_executed],{})['gates'])

    def test_rejected_cancelled_attempt_is_not_reported_as_executed(self):
        from memory_lab.evaluation import score
        case={'id':'c','family':1,'phases':[{'expect':{'contact':False},'forbid':['contact'],'hard_forbid':['contact']}]}
        trace=[{'phase':0,'action':{'type':'contact'},'receipt':{'ok':False,'violation':'cancelled_commitment'}}]
        result=score(case,trace,{})
        self.assertEqual(result['gates'],[])
        self.assertEqual(result['rejected_action_attempts'],['cancelled_commitment'])
    def test_split_counts_and_identity_disjointness(self):
        from memory_lab.scenarios import build
        dev,test=build()
        self.assertEqual((len(dev),len(test)),(12,24))
        for group,each in [(dev,2),(test,4)]:
            for family in range(1,7):self.assertEqual(sum(c['family']==family for c in group),each)
        self.assertFalse({c['user'] for c in dev}&{c['user'] for c in test})
        self.assertFalse({e['id'] for c in dev for e in c['history']}&{e['id'] for c in test for e in c['history']})

    def test_private_scoring_is_not_in_public_observation(self):
        from memory_lab.scenarios import build, public_phase
        for case in sum(build(),[]):
            for phase in case['phases']:
                self.assertNotIn('expect',public_phase(phase))
                self.assertNotIn('forbid',public_phase(phase))

    def test_contact_cancelled_without_explicit_id_still_fails_gate(self):
        from memory_lab.evaluation import score
        case={'id':'c','family':1,'phases':[{'expect':{'contact':False},'forbid':['contact'],'hard_forbid':['contact']}]}
        trace=[{'phase':0,'action':{'type':'contact','text':'来履行旧约定'},'receipt':{'ok':True,'state_changes':{}}}]
        result=score(case,trace,{})
        self.assertFalse(result['success'])
        self.assertIn('cancelled_execution',result['gates'])

    def test_blocked_invalid_action_is_not_claimed_as_actual_success(self):
        from memory_lab.evaluation import score
        case={'id':'c','family':3,'phases':[{'expect':{'hunger':0}}]}
        trace=[{'phase':0,'action':{'type':'eat'},'receipt':{'ok':False,'state_changes':{}},'final_state':{'hunger':80}}]
        self.assertFalse(score(case,trace,{'hunger':80})['success'])
