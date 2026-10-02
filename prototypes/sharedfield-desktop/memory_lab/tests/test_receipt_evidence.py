import json
import tempfile
import unittest
from pathlib import Path

from memory_lab.core import Store,World,canonical
from memory_lab.semantic import audit_context


class ReceiptEvidenceTests(unittest.TestCase):
    def test_real_commit_path_exposes_completed_meal_without_external_citations(self):
        with tempfile.TemporaryDirectory() as td:
            store=Store(Path(td)/'raw.sqlite')
            try:
                World(store,dict(now=1,places={},inventory=['餐点'],hunger=70,energy=50))
                eat={'type':'eat','target':'餐点','evidence_ids':[]}
                meal=store.commit_step(eat,'eat','meal',{'action':eat},{'id':'one'}, {})
                say={'type':'contact','text':'我吃完餐点了。','evidence_ids':[]}
                spoken=store.commit_step(say,'say','speech',{'action':say},{'id':'two'}, {})
                context=json.loads(audit_context(spoken))
                self.assertEqual(len(context['prior_successful_receipts']),1)
                evidence=context['prior_successful_receipts'][0]
                self.assertEqual(evidence['source_id'],'meal')
                self.assertEqual(evidence['receipt'],meal['receipt'])
                self.assertEqual(evidence['receipt']['state_changes']['hunger'],0)
                self.assertNotEqual(evidence['source_id'],spoken['event_id'])
                store.forget(['meal'])
                say2=dict(say,text='刚才那顿饭还记得吗？')
                after=store.commit_step(say2,'later','later-speech',{'action':say2},{'id':'three'}, {})
                later=json.loads(audit_context(after))
                self.assertFalse(any(x['source_id']=='meal' for x in later['prior_successful_receipts']))
            finally:store.close()

    def test_failed_receipt_is_not_labeled_successful(self):
        failed={'ok':False,'action':{'type':'eat','target':'面包'},'state_changes':{}}
        context=json.loads(audit_context({'action':{'text':'我吃完了'},'prior_receipts':[failed]}))
        self.assertEqual(context['prior_successful_receipts'],[])
        self.assertEqual(context['prior_failed_receipts'][0]['receipt'],failed)

    def test_story_user_claim_future_or_current_event_cannot_become_receipt(self):
        action={'type':'eat','target':'面包'};receipt={'ok':True,'action':action,'state_changes':{'hunger':0}}
        rows=[]
        for key,kind,at in [('story','simulation',1),('user','user_statement',1),('future','action_result',8),('current','action_result',2)]:
            rows.append(dict(id=key,kind=kind,actor='生活执行器',at=at,text=canonical({'action':action,'receipt':receipt})))
        row={'event_id':'current','action':{'text':'我吃了'},'audit_before':{'now':2},'audit_events':rows}
        self.assertEqual(json.loads(audit_context(row))['prior_successful_receipts'],[])

    def test_mismatched_action_cannot_become_verified_receipt(self):
        event=dict(id='bad',kind='action_result',actor='生活执行器',at=1,
                   text=canonical({'action':{'type':'eat'},'receipt':{'ok':True,'action':{'type':'wait'},'state_changes':{}}}))
        context=json.loads(audit_context({'action':{'text':'吃完了'},'audit_events':[event]}))
        self.assertEqual(context['prior_successful_receipts'],[])
        self.assertEqual(context['unparsed_receipt_sources'],['bad'])
