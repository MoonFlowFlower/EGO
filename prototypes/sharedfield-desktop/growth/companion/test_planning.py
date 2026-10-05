"""Request continuity before the final result can be specified; no cloud calls."""
import json
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path

from p7.proxy import ProxyError
from .compact import project
from .harness import Harness
from .interaction_scene import InteractionScene
from .memory import Memory
from .test_harness import Model, decision, goal, place
from .test_kernel import Audit
from .test_turns import route
from .work import create_pending_work, preliminary_completion, validate_action


def inspect():return decision(action={'name':'inspect','args':{}})
def wait():return decision(status='waiting_user',reply='目前这个位置还需要确认范围，你指的是旁边这一块吗？')


class PlanningTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite'
        self.body=InteractionScene();self.audit=Audit();self.threads=[]
    def tearDown(self):
        self.body.release()
        for t in self.threads:
            t.join(3);self.assertFalse(t.is_alive())
        self.tmp.cleanup()
    def saved(self):
        m=Memory(self.path)
        try:return m.goal()['work']
        finally:m.close()
    def engine(self,model,**kw):
        return Harness(self.path,model,self.body,self.audit,
            input_router=kw.pop('input_router',lambda *a:route('task','structure')),**kw)
    def start(self,engine,identity,text):
        t=threading.Thread(target=lambda:engine.run(identity,'verification',text),daemon=True)
        self.threads.append(t);t.start();return t
    def queue(self,engine,text):
        t=self.start(engine,'interruption',text);deadline=time.monotonic()+2
        while not engine._waiting and time.monotonic()<deadline:time.sleep(.005)
        self.assertEqual(engine._waiting,1);return t

    def test_intent_is_durable_before_first_actor_call_and_approach_does_not_complete_it(self):
        seen=[]
        def approach(context):
            seen.append(self.saved())
            self.assertEqual(seen[0]['request']['user'],'先看现场，再建小木屋')
            self.assertEqual(seen[0]['done_when'],[])
            return decision(action={'name':'approach','args':{}})
        reply=self.engine(Model(approach,wait())).run('task','verification','先看现场，再建小木屋')
        saved=self.saved()
        self.assertEqual(saved['task_id'],seen[0]['task_id'])
        self.assertEqual(saved['status'],'waiting_user');self.assertIsNone(saved['completion'])
        self.assertEqual(saved['actions'],1)
        self.assertEqual([a['name'] for a in self.body.actions],['approach'])
        self.assertNotIn('目标已核对完成',reply)

    def test_empty_contract_and_model_done_cannot_complete(self):
        pending=create_pending_work('检查后再建',self.body.snapshot(),'source')
        self.assertFalse(preliminary_completion(pending,self.body.snapshot())['satisfied'])
        self.engine(Model(decision(status='done'),decision(status='done'))).run('task','verification','建小屋')
        self.assertIsNone(self.saved()['completion']);self.assertEqual(self.body.actions,[])

    def test_uncontracted_effects_and_distant_approach_do_not_execute(self):
        self.body.state['owner']['position']['x']=50
        model=Model(decision(action={'name':'approach','args':{}}),place(),wait())
        self.engine(model).run('task','verification','建小屋')
        self.assertEqual(self.body.actions,[])
        self.assertEqual(model.contexts[1]['receipts'][-1]['status'],'planning_approach_requires_nearby_owner')
        self.assertEqual(model.contexts[2]['receipts'][-1]['status'],'result_contract_required_before_effect')

    def test_contract_submission_preserves_identity_and_still_requires_world_proof(self):
        model=Model(inspect(),place(goal(1)))
        self.engine(model,input_router=lambda *a:route('task')).run('task','verification','看完再放一块')
        saved=self.saved()
        self.assertEqual(saved['task_id'],model.contexts[0]['work']['task_id'])
        self.assertEqual(saved['status'],'completed');self.assertTrue(saved['completion']['world_verified'])
        self.assertEqual([a['name'] for a in self.body.actions],['inspect','place','verify_blocks'])

    def test_budget_exception_preserves_unplanned_request_and_restart_needs_explicit_resume(self):
        def no_budget(_):raise ProxyError('budget_stop',402)
        self.engine(Model(no_budget)).run('task','verification','在这里建房')
        old=self.saved();self.assertEqual(old['last_problem'],'budget_stop')
        self.assertEqual(old['request']['user'],'在这里建房');self.assertEqual(old['done_when'],[])
        chat=self.engine(Model({'reply':'我在。'}),input_router=lambda *a:route('chat'))
        chat.run('chat','verification','在吗')
        self.assertEqual(self.saved(),old);self.assertEqual(self.body.actions,[])
        self.engine(Model(inspect(),wait()),input_router=lambda *a:route('resume','structure')).run('resume','verification','继续')
        self.assertEqual(self.saved()['task_id'],old['task_id'])
        self.assertEqual([a['name'] for a in self.body.actions],['inspect'])

    def test_budget_failure_keeps_already_spoken_reply_in_canonical_history(self):
        def no_budget(_):raise ProxyError('budget_stop',402)
        first=inspect();first['reply']='我先观察地面。'
        result=self.engine(Model(first,no_budget)).run('task','verification','在这里建房')
        self.assertIn(first['reply'],result);self.assertIn('预算',result)
        memory=Memory(self.path)
        try:self.assertEqual(memory.cached('task'),result)
        finally:memory.close()

    def test_chat_yields_and_resumes_same_planning_request_with_fresh_state_and_original_limit(self):
        self.body.hold='inspect'
        def answer(_):
            self.body.state['position']['y']=63
            return {'reply':'我在看地形。'}
        model=Model(inspect(),answer,inspect(),wait())
        router=lambda text,*a:route('status') if text=='在看什么' else route('task','structure')
        engine=self.engine(model,input_router=router,max_decisions=3)
        t=self.start(engine,'task','建小屋');self.assertTrue(self.body.entered.wait(2))
        old=self.saved();chat=self.queue(engine,'在看什么');self.body.release();chat.join(3);t.join(3)
        self.assertEqual(self.saved()['task_id'],old['task_id'])
        self.assertEqual(self.saved()['actions'],2)
        self.assertEqual(model.contexts[2]['body']['position']['y'],63)
        self.assertEqual(model.contexts[2]['remaining_decisions'],2)
        self.assertEqual(model.contexts[2]['current']['user'],'建小屋')
        self.assertEqual(self.saved()['status'],'waiting_user')

    def test_steering_updates_same_pending_request_and_cancels_stale_plan(self):
        self.body.hold='inspect';model=Model(inspect(),wait())
        router=lambda text,*a:route('steer','structure') if text=='地面在下面' else route('task','structure')
        engine=self.engine(model,input_router=router)
        t=self.start(engine,'task','建小屋');self.assertTrue(self.body.entered.wait(2))
        old=self.saved();steering=self.queue(engine,'地面在下面');self.body.release();steering.join(3);t.join(3)
        self.assertEqual(self.saved()['task_id'],old['task_id']);self.assertEqual(self.saved()['revision'],2)
        self.assertEqual(model.contexts[-1]['current']['user'],'地面在下面')
        self.assertEqual([a['name'] for a in self.body.actions],['inspect'])

    def test_stop_during_planning_discards_continuation(self):
        self.body.hold='inspect';model=Model(inspect(),place(goal(1)))
        engine=self.engine(model)
        t=self.start(engine,'task','建小屋');self.assertTrue(self.body.entered.wait(2))
        engine.stop();self.body.release();t.join(3)
        self.assertEqual(self.saved()['status'],'paused_by_owner');self.assertEqual(model.calls,1)
        self.assertEqual([a['name'] for a in self.body.actions],['inspect'])

    def test_observation_schema_and_lossless_model_projection(self):
        validate_action({'name':'inspect_area','args':{'radius':4,'center':{'x':12,'y':111,'z':-58},'below':8,'above':0}})
        for args in ({'radius':1,'below':True},{'radius':1,'below':17},{'radius':1,'above':-1},{'radius':1,'center':{'x':0.2,'y':10,'z':0}}):
            with self.assertRaises(ValueError):validate_action({'name':'inspect_area','args':args})
        raw=subprocess.check_output([r'C:\Program Files\nodejs\node.exe',str(Path(__file__).with_name('test_perception.mjs')),'--fixture'],text=True)
        receipt=json.loads(raw.splitlines()[-1]);compact=project(receipt);restored={}
        for region in compact['observed_regions']:
            a,b=region['min'],region['max']
            for x in range(a['x'],b['x']+1):
                for y in range(a['y'],b['y']+1):
                    for z in range(a['z'],b['z']+1):restored[x,y,z]=region['block']
        self.assertEqual(restored,{tuple(c[:3]):c[3] for c in receipt['cells']})
        self.assertEqual(compact['coverage'],receipt['coverage'])
        self.assertEqual(restored[12,108,-58],'grass_block');self.assertIsNone(restored[8,108,-58])


if __name__=='__main__':unittest.main()
