"""Exercise the real action loop; model fixtures deliberately keep done=false."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from memory_lab.adapters import Baseline
from memory_lab.runner import setup_base, run_episode


class WaitingTests(unittest.TestCase):
    def run_case(self, phases, actions, *, crash=False, initial=None):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/'run';seen=[];iterator=iter(actions)
            case=dict(id='waiting',split='development',family=1,user='u',history=[],commitments=[],
                initial=initial or dict(now=1,user='u',places={},inventory=[],hunger=80,energy=80),phases=phases)
            def adapter(arm,store,path):return Baseline(store,path,embed=lambda ts:[[1.,0.] for _ in ts])
            def model(messages,**kw):
                seen.append(json.loads(messages[-1]['content']))
                # Extra calls expose the bug through call count/state rather than StopIteration.
                action=next(iterator,{'type':'wait'})
                return dict(id='offline',choices=[{'message':{'content':json.dumps(dict(action=action,done=False))}}])
            original=Baseline.retain;interrupted=[False]
            def indexing(self,events):
                if not interrupted[0] and any(e['kind']=='action_result' for e in events):
                    interrupted[0]=True;raise RuntimeError('after action commit')
                return original(self,events)
            with patch('memory_lab.runner.scope'),patch('memory_lab.runner.check_gateway'),patch('memory_lab.runner.create_adapter',side_effect=adapter):
                base=setup_base(case,'baseline',root)
                if crash:
                    with patch.object(Baseline,'retain',indexing),self.assertRaises(RuntimeError):
                        run_episode(case,'baseline',1,root,base,model_call=model)
                result=run_episode(case,'baseline',1,root,base,model_call=model)
                # Reopening the completed same event must be a no-op too.
                run_episode(case,'baseline',1,root,base,model_call=model)
            folder=next((root/'episodes').iterdir());trace=json.loads((folder/'trace.json').read_text());saved=json.loads((folder/'final-store.json').read_text())
            return seen,trace,saved,result

    def phase(self, **kw):
        p=dict(now=1,notice='等下一条消息',trigger='user_message',max_steps=6,expect={});p.update(kw);return p

    def test_successful_wait_yields_even_when_model_says_not_done(self):
        seen,trace,saved,_=self.run_case([self.phase()],[dict(type='wait')])
        self.assertEqual(len(seen),1)
        self.assertEqual(len(trace),1)
        end=json.loads(dict(saved['checkpoints'])['phase_done-0'])
        self.assertEqual(end['reason'],'awaiting_event')
        self.assertTrue(end['ok'])

    def test_successful_help_does_not_send_followup_contact_in_same_event(self):
        seen,trace,_,_=self.run_case([self.phase()],[dict(type='ask_help',text='需要食物'),dict(type='contact',text='再催一次')])
        self.assertEqual(len(seen),1)
        self.assertEqual(len(trace[-1]['final_state']['help']),1)
        self.assertEqual(trace[-1]['final_state']['contacts'],[])

    def test_failed_help_can_recover_before_yielding(self):
        seen,trace,_,_=self.run_case([self.phase()],[dict(type='ask_help',text=''),dict(type='ask_help',text='食物没了')])
        self.assertEqual(len(seen),2)
        self.assertFalse(trace[0]['receipt']['ok'])
        self.assertTrue(trace[1]['receipt']['ok'])
        self.assertEqual(len(trace[-1]['final_state']['help']),1)

    def test_yield_survives_crash_after_committing_request_before_indexing(self):
        seen,trace,_,_=self.run_case([self.phase()],[dict(type='ask_help',text='帮忙')],crash=True)
        self.assertEqual(len(seen),1)
        self.assertEqual(len(trace),1)
        self.assertEqual(len(trace[-1]['final_state']['help']),1)

    def test_new_environment_and_clock_events_allow_life_to_continue(self):
        phases=[self.phase(),self.phase(now=2,trigger='environment_change',notice='食物到手',max_steps=1,
                                     state={'inventory':['饭'],'edible':['饭']},expect={'hunger':0}),
                self.phase(now=3,trigger='clock',notice='后来困了',max_steps=1,state={'energy':5},expect={'rested':True})]
        seen,trace,_,_=self.run_case(phases,[dict(type='ask_help',text='食物没了'),dict(type='eat',target='饭'),dict(type='sleep')])
        self.assertEqual(len(seen),3)
        self.assertEqual([r['action']['type'] for r in trace],['ask_help','eat','sleep'])
        self.assertEqual(trace[-1]['final_state']['hunger'],0)
        self.assertTrue(trace[-1]['final_state']['rested'])
