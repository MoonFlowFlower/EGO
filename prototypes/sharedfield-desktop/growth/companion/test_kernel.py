"""Deterministic engineering checks; no model/network/game calls."""
import concurrent.futures
import http.client
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest

from p7.proxy import BudgetLedger, ProxyError
from .engine import Engine, validate_action
from .memory import Memory
from .server import KernelServer, PUBLIC_MODEL, last_input


def decision(reply='',**fields):
    return {'reply':reply,'goal':None,'convention':None,'forget_card':None,'action':None,**fields}


class Audit:
    def __init__(self):self.rows=[]
    def write(self,name,row):self.rows.append((name,row))


class Body:
    def __init__(self):self.actions=[];self.speech=[];self.stops=0;self.verified=True
    def snapshot(self):return {'offline':False,'inventory':{'oak_log':2},'owner':{'distance':2,'height_difference':0}}
    def say(self,text):self.speech.append(text)
    def stop(self):self.stops+=1;return {'verified':True,'status':'stopped'}
    def start_action(self,action,**kwargs):
        self.actions.append(action)
        future=concurrent.futures.Future()
        future.set_result({'verified':self.verified,'status':'checked' if self.verified else 'failed','observed':self.snapshot()})
        return future


class Model:
    def __init__(self,*steps):self.steps=list(steps);self.contexts=[];self.calls=0
    def decide(self,prompt,context):
        self.calls+=1;self.contexts.append(context)
        step=self.steps.pop(0)
        return step(context) if callable(step) else step


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite'
        self.body=Body();self.audit=Audit()
    def tearDown(self):self.tmp.cleanup()
    def engine(self,model,**kwargs):return Engine(self.path,model,self.body,self.audit,**kwargs)

    def test_desktop_teach_full_restart_mc_action_and_receipt(self):
        teach=Model(decision(convention={'trigger':'蓝灯','meaning':'走到我身边','replaces':None}),decision('约定已记下。'))
        first=self.engine(teach)
        first.run('teach','airi','这是工程测试约定：蓝灯代表走到我身边。')
        second_model=Model(decision(goal={'title':'走到 Moonlight 身边'},action={'name':'approach','args':{}}),decision('距离已经确认。'))
        second=self.engine(second_model)
        reply=second.run('trigger','minecraft','蓝灯')
        self.assertEqual(reply,'距离已经确认。')
        self.assertEqual([a['name'] for a in self.body.actions],['approach'])
        ctx=second_model.contexts[0]
        self.assertTrue(ctx['annotations']);self.assertEqual(ctx['conventions'][0]['meaning'],'走到我身边')
        self.assertEqual({r['channel'] for r in ctx['history']},{'airi','minecraft'})
        self.assertTrue(second_model.contexts[1]['receipts'][0]['verified'])
        memory=Memory(self.path)
        self.assertEqual(memory.goal()['goal_status'],'awaiting_next_input');memory.close()
        third_model=Model(decision('刚才靠近了你。'))
        self.engine(third_model).run('recall','airi','刚才做了什么')
        self.assertTrue(third_model.contexts[0]['recent_actions'][0]['receipt']['verified'])
        self.assertEqual(third_model.contexts[0]['recent_actions'][0]['action']['name'],'approach')

    def test_idempotent_input_never_repeats_model_action_or_speech(self):
        model=Model(decision(action={'name':'inspect','args':{}}),decision('看到了。'))
        engine=self.engine(model)
        answer=engine.run('one','minecraft','观察')
        self.assertEqual(engine.run('one','minecraft','观察'),answer)
        self.assertEqual(model.calls,2);self.assertEqual(len(self.body.actions),1);self.assertEqual(len(self.body.speech),1)

    def test_interrupted_turn_is_not_replayed_after_restart(self):
        m=Memory(self.path);m.begin('crash','minecraft','做一个动作');m.close()
        model=Model();engine=self.engine(model)
        self.assertIn('不会自动重放',engine.run('crash','minecraft','做一个动作'))
        self.assertEqual(model.calls,0);self.assertEqual(self.body.actions,[])

    def test_correction_deletion_remove_quotes_and_derived_records(self):
        m=Memory(self.path)
        source=m.library.utterance('蓝灯代表 PRIVATE_OLD_927。',session_id='teach')
        card=m.propose({'trigger':'蓝灯','meaning':'PRIVATE_OLD_927','replaces':None},source)
        update=m.library.utterance('蓝灯不再是 PRIVATE_OLD_927，现在改成 PRIVATE_NEW_927。',session_id='correct')
        revised=m.propose({'trigger':'蓝灯','meaning':'PRIVATE_NEW_927','replaces':card},update)
        m.append('reflection',{'text':'PRIVATE_OLD_927 and PRIVATE_NEW_927'},[card,revised])
        self.assertEqual(len(m.library.cards()),1)
        self.assertEqual(m.library.cards()[0]['meaning'],'PRIVATE_NEW_927')
        m.forget(revised);self.assertEqual(m.library.cards(),[]);m.close()
        raw=self.path.read_bytes()
        self.assertNotIn(b'PRIVATE_OLD_927',raw);self.assertNotIn(b'PRIVATE_NEW_927',raw)

    def test_unquoted_memory_rejected_and_saturday_computed(self):
        m=Memory(self.path);source=m.library.utterance('周六20:00以后上线代表先聊一会。',session_id='t')
        with self.assertRaises(ValueError):m.propose({'trigger':'周六20:00以后上线','meaning':'去采矿','replaces':None},source)
        m.propose({'trigger':'周六20:00以后上线','meaning':'先聊一会','replaces':None},source)
        self.assertEqual(m.library.cards()[0]['trigger']['weekday'],5)
        self.assertTrue(m.library.annotate('上线了','2026-10-03T20:01:00-05:00',('login',)))
        self.assertFalse(m.library.annotate('上线了','2026-10-04T20:01:00-05:00',('login',)))
        m.close()

    def test_stop_cancels_late_model_and_queued_inputs(self):
        entered=threading.Event();release=threading.Event()
        def late(_):entered.set();release.wait(4);return decision(action={'name':'approach','args':{}})
        model=Model(late);engine=self.engine(model)
        a=threading.Thread(target=engine.run,args=('a','airi','过来'));a.start();self.assertTrue(entered.wait(2))
        b=threading.Thread(target=engine.run,args=('b','minecraft','跟我'));b.start();time.sleep(.05)
        engine.stop();release.set();a.join(3);b.join(3)
        self.assertFalse(a.is_alive() or b.is_alive());self.assertEqual(self.body.actions,[]);self.assertEqual(model.calls,1)

    def test_failed_action_has_no_retry_or_second_action(self):
        self.body.verified=False
        model=Model(decision(goal={'title':'盖房'},action={'name':'craft','args':{'item':'oak_planks','count':1}}),
                    decision('还要继续',action={'name':'craft','args':{'item':'oak_planks','count':1}}))
        answer=self.engine(model).run('fail','minecraft','盖房')
        self.assertIn('没有得到成功确认',answer);self.assertEqual(len(self.body.actions),1)
        m=Memory(self.path);self.assertEqual(m.goal()['title'],'盖房');m.close()

    def test_static_actions_and_decision_cap(self):
        for action in ({'name':'newAction','args':{}},{'name':'craft','args':{'item':'oak_planks','count':True}},
                       {'name':'give','args':{'item':'/op Moonlight','count':1}},{'name':'approach','args':{'code':'shell'}}):
            with self.assertRaises(ValueError):validate_action(action)
        model=Model(decision(action={'name':'inspect','args':{}}))
        answer=self.engine(model,max_decisions=1).run('cap','minecraft','看看')
        self.assertEqual(model.calls,1);self.assertIn('已用完',answer)

    def test_budget_refusal_keeps_unknown_reservation(self):
        ledger=BudgetLedger(Path(self.tmp.name)/'budget.sqlite',.10)
        charge=ledger.reserve(.08);ledger.settle(charge,{})
        with self.assertRaises(ProxyError):ledger.reserve(.05)
        self.assertAlmostEqual(ledger.total(),.08)

    def test_official_airi_timestamp_does_not_hide_stop_or_forget(self):
        for text in ('停止','忘掉蓝灯'):
            request={'model':PUBLIC_MODEL,'messages':[{'role':'user','content':'[2026-10-03 12:50] '+text}]}
            self.assertEqual(last_input(request)[0],text)

    def test_http_sse_shared_authority_and_native_mirror_cached_after_restart(self):
        model=Model(decision('同一个内核的回复。'))
        server=KernelServer(self.engine(model),self.audit,port=0);server.start()
        port=server.httpd.server_address[1]
        def request(path,data=None,token=True,origin='null'):
            conn=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
            headers={'Content-Type':'application/json','Origin':origin}
            if token:headers['Authorization']='Bearer '+server.token
            conn.request('POST' if data else 'GET',path,body=json.dumps(data) if data else None,headers=headers)
            response=conn.getresponse();result=response.status,response.read().decode();conn.close();return result
        try:
            self.assertEqual(request('/v1/models',token=False)[0],401)
            self.assertEqual(request('/v1/models',origin='https://untrusted.example')[0],403)
            self.assertEqual(request('/v1/models')[0],200)
            data={'model':PUBLIC_MODEL,'stream':True,'messages':[{'role':'system','content':'REIMPORT_PRIVATE_FAKE'},
                {'role':'user','content':'OLD_UI_PRIVATE_FAKE'},{'role':'assistant','content':'IGNORE_FAKE'},
                {'role':'user','content':'你好'}]}
            status,body=request('/v1/chat/completions',data)
            self.assertEqual(status,200);self.assertIn('[DONE]',body);self.assertIn('同一个内核的回复',body)
            self.assertNotIn('FAKE',json.dumps(model.contexts,ensure_ascii=False))
            server.engine.model=Model(decision('MC 已经回答。'))
            server.engine.run('mc:done','minecraft','原始游戏输入')
            rendered=server.mirror('mc:done','原始游戏输入')
            # New engine object with the same DB proves native UI replay after restart.
            restarted=Model();server.engine=self.engine(restarted)
            replay={'model':PUBLIC_MODEL,'messages':[{'role':'user','content':'[2026-10-03 12:50] '+rendered}]}
            for _ in range(2):
                status,body=request('/v1/chat/completions',replay)
                self.assertEqual(status,200);self.assertIn('MC 已经回答',body)
            self.assertEqual(restarted.calls,0)
            self.assertEqual(len(self.body.speech),2)
        finally:server.close()


if __name__=='__main__':unittest.main(verbosity=2)
