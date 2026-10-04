import copy
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import secrets
import urllib.request
import urllib.error

from .harness import Harness
from .intent import route_input
from .memory import Memory
from .reconnect import ReconnectSchedule
from .runtime import Runtime
from .server import KernelServer
from .test_harness import Model, Body, goal, place, decision
from .test_kernel import Audit
from .work import create_work, save_work


def route(mode='status', kind='ordinary', quote=''):
    return {'mode':mode,'task_kind':kind,'request_quote':quote,
            'information_need': {'question':'测试替身请求证据',
                'sources':['current_body','goal','dialogue','user_history','historical_actions'], 'memory_queries':[]}}


class TurnTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite'
        self.body=Body();self.audit=Audit()
        m=Memory(self.path)
        source,_=m.begin('old','minecraft','建一座房子')
        g=goal(8);g['title']='在 Moonlight 这边建一座房子'
        w=create_work(g,self.body.snapshot(),source);w['status']='blocked';w['last_problem']='action_timeout'
        save_work(m,w,[source]);m.finish('old','待办保留',[source]);self.original=m.goal();m.close()
    def tearDown(self):self.tmp.cleanup()
    def saved(self):
        m=Memory(self.path)
        try:return m.goal()
        finally:m.close()
    def engine(self,model):return Harness(self.path,model,self.body,self.audit)
    def test_three_reported_inputs_never_enter_actor_or_modify_goal(self):
        for i,(text,mode) in enumerate([('(｡･∀･)ﾉﾞ嗨','chat'),('你怎么不动了','status'),('你现在在想做什么','status')]):
            model=Model(route(mode),{'reply':'我在。任务还保留着。'})
            e=self.engine(model);e.run(str(i),'minecraft',text)
            self.assertEqual(model.calls,2);self.assertEqual(self.body.actions,[]);self.assertEqual(self.body.stops,0)
            self.assertEqual(self.saved(),self.original)
            self.assertNotIn('history',model.contexts[0]);self.assertNotIn('recent_actions',model.contexts[0])
            e.run(str(i),'minecraft',text);self.assertEqual(model.calls,2)
    def test_chat_cannot_smuggle_action_even_with_schema_error(self):
        e=self.engine(Model(route('chat'),{'reply':'继续','action':{'name':'place','args':{'block':'oak_planks'}}}))
        e.run('smuggle','airi','嗨')
        self.assertEqual(self.body.actions,[]);self.assertEqual(self.body.stops,0);self.assertEqual(self.saved(),self.original)
    def test_router_malformed_or_old_quote_fails_closed(self):
        for i,response in enumerate([{},route('task',quote='继续施工')]):
            self.engine(Model(response)).run('bad'+str(i),'minecraft','嗨')
            self.assertEqual(self.saved(),self.original);self.assertEqual(self.body.stops,0)
        self.assertEqual(self.body.actions,[])
    def test_full_house_does_not_become_eight_blocks(self):
        model=Model(route('task','structure','建一座房子'),{'reply':'完整房屋还缺少可靠的布局验收，原待办保留。'})
        self.engine(model).run('house','minecraft','建一座房子')
        self.assertEqual(self.saved(),self.original);self.assertEqual(self.body.actions,[])
    def test_memory_output_cannot_rewrite_goal_or_act(self):
        model=Model(route('memory',quote='记住蓝灯'),decision(goal=goal(1)))
        self.engine(model).run('memory','airi','记住蓝灯')
        self.assertEqual(self.saved(),self.original);self.assertEqual(self.body.stops,0)
    def test_explicit_new_task_keeps_ten_action_continuity_and_replay_guard(self):
        model=Model(route('task',quote='连续放10块'),place(goal(10)),*[place() for _ in range(9)])
        e=self.engine(model);e.run('ten','minecraft','连续放10块')
        self.assertEqual(self.saved()['goal_status'],'completed');self.assertEqual(len(self.body.blocks),10)
        self.assertEqual(model.calls,11);e.run('ten','minecraft','连续放10块');self.assertEqual(model.calls,11)
    def test_explicit_resume_uses_existing_work(self):
        m=Memory(self.path)
        w=self.original['work'];w['title']='放置8块木板';save_work(m,w,[w['source_id']]);self.original=m.goal();m.close()
        model=Model(route('resume',quote='继续'),*[place() for _ in range(8)])
        e=self.engine(model);e.run('resume','minecraft','继续')
        self.assertEqual(self.saved()['work']['task_id'],self.original['work']['task_id'])
        self.assertEqual(len(self.body.blocks),8)
    def test_resume_full_house_is_kept_without_actor(self):
        self.engine(Model(route('resume','structure','继续'),{'reply':'房屋还缺布局验收，原待办保留。'})).run('resume-house','minecraft','继续')
        self.assertEqual(self.saved(),self.original);self.assertEqual(self.body.actions,[])
    def test_reconnect_invalidates_late_model_action(self):
        entered=threading.Event();release=threading.Event()
        def late(_):entered.set();release.wait(3);return place(goal(1))
        model=Model(route('task',quote='放1块'),late);e=self.engine(model)
        t=threading.Thread(target=e.run,args=('late','minecraft','放1块'));t.start();self.assertTrue(entered.wait(2))
        e.invalidate('body_reconnect');release.set();t.join(3)
        self.assertFalse(t.is_alive());self.assertEqual(self.body.actions,[]);self.assertEqual(self.saved()['goal_status'],'suspended')


class ReconnectTests(unittest.TestCase):
    def test_in_memory_local_token_handoff_and_authentication(self):
        token=secrets.token_urlsafe(32);server=KernelServer(None,Audit(),port=0,local_token=token)
        try:
            server.start()
            req=urllib.request.Request(server.base_url+'/models',headers={'Authorization':'Bearer '+token})
            with urllib.request.urlopen(req,timeout=3) as response:self.assertEqual(response.status,200)
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(server.base_url+'/models',timeout=3)
        finally:server.close()
        for value in ('bad','sk-not-a-local-token',False):
            with self.assertRaises(ValueError):KernelServer(None,Audit(),port=0,local_token=value)
    def test_backoff_cap_and_original_deadline(self):
        s=ReconnectSchedule()
        for now,expected in [(0,False),(1,False),(2,True),(3,False),(12,False),(13,True),(14,False),(43,False),(44,True),(100,False)]:
            self.assertEqual(s.due(now,exited=True,deadline=1000),expected)
        self.assertEqual(s.attempts,3)
        s=ReconnectSchedule();self.assertFalse(s.due(0,exited=True,deadline=1));self.assertFalse(s.due(2,exited=True,deadline=1))
    def test_success_does_not_reset_attempt_budget(self):
        s=ReconnectSchedule();s.due(0,exited=True,deadline=100);s.due(2,exited=True,deadline=100)
        s.due(3,exited=False,deadline=100);self.assertFalse(s.due(4,exited=True,deadline=100));self.assertTrue(s.due(14,exited=True,deadline=100))
    def test_runtime_reconnect_only_replaces_body_without_running_model(self):
        rt=Runtime.__new__(Runtime);rt._closed=threading.Event();rt._body_lock=threading.RLock();rt.deadline=time.monotonic()+20
        rt.audit=Audit();rt._reconnect=ReconnectSchedule();rt._reconnect_notice=False
        calls=[]
        class Stub:
            def __init__(self,*args):self.process=SimpleNamespace(poll=lambda:None)
            def start(self):calls.append('start')
            def close(self,reason):calls.append('close')
        rt.body=Stub();rt.body.process=SimpleNamespace(poll=lambda:0)
        rt.engine=SimpleNamespace(invalidate=lambda why:calls.append('invalidate'),body=rt.body)
        with patch('companion.runtime.Body',Stub):
            rt.reconnect_body(automatic=True);rt.reconnect_body(automatic=True)
        self.assertEqual(calls,['invalidate','close','start']);self.assertIs(rt.engine.body,rt.body)


if __name__=='__main__':unittest.main(verbosity=2)
