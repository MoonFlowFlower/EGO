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

    def test_negative_search_continues_to_different_query_and_collection(self):
        original=self.body.start_action
        def start(action,**kwargs):
            if action['name']=='search' and action['args']['block']=='oak_log':
                self.body.actions.append(action)
                future=concurrent.futures.Future()
                future.set_result({'verified':False,'status':'block_not_found','observation_complete':True,
                                   'found':False,'query':{'scope':'loaded_chunks_only','range':32}})
                return future
            return original(action,**kwargs)
        self.body.start_action=start
        model=Model(decision(action={'name':'search','args':{'block':'oak_log','range':32}}),
                    decision(action={'name':'search','args':{'block':'wood','range':128}}),
                    decision(action={'name':'collect','args':{'block':'spruce_log','count':3}}),decision('已采到。'))
        answer=self.engine(model).run('wood','minecraft','采木头')
        self.assertEqual(answer,'已采到。')
        self.assertEqual([a['name'] for a in self.body.actions],['search','search','collect'])
        self.assertFalse(model.contexts[1]['receipts'][0]['verified'])
        self.assertNotIn('execution_blocked',model.contexts[1])

    def test_repeated_negative_search_does_not_loop(self):
        def start(action,**kwargs):
            self.body.actions.append(action);future=concurrent.futures.Future()
            future.set_result({'verified':False,'status':'block_not_found','observation_complete':True,
                               'found':False,'query':{'scope':'loaded_chunks_only'}});return future
        self.body.start_action=start
        d=decision(action={'name':'search','args':{'block':'wood','range':128}})
        model=Model(d,d)
        answer=self.engine(model).run('repeat','minecraft','采木头')
        self.assertEqual(len(self.body.actions),1);self.assertEqual(model.calls,2)
        self.assertIn('已经尝试过',answer)

    def placement_body(self, *, proof=True, fail_at=None):
        def start(action, **kwargs):
            self.body.actions.append(action)
            n=len(self.body.actions)
            receipt={'verified':n!=fail_at, 'status':'placed_block_checked', 'position':{'x':n,'y':64,'z':0}}
            if proof:
                receipt['placement']={'before_block':'air','after_block':'oak_planks',
                                      'inventory_before':20-n,'inventory_after':19-n,'consumed':1}
            future=concurrent.futures.Future();future.set_result(receipt);return future
        self.body.start_action=start

    def test_repeated_placement_with_world_and_inventory_progress_continues(self):
        self.placement_body()
        d=decision(action={'name':'place','args':{'block':'oak_planks'}})
        model=Model(d,d,decision('两块已确认。'))
        engine=self.engine(model)
        self.assertEqual(engine.run('two-places','minecraft','继续铺两块'),'两块已确认。')
        self.assertEqual(len(self.body.actions),2)
        self.assertNotEqual(model.contexts[2]['receipts'][0]['position'],model.contexts[2]['receipts'][1]['position'])
        engine.run('two-places','minecraft','继续铺两块')
        self.assertEqual(len(self.body.actions),2);self.assertEqual(model.calls,3)

    def test_success_flag_without_placement_progress_is_blocked_and_recorded(self):
        self.placement_body(proof=False)
        d=decision(action={'name':'place','args':{'block':'oak_planks'}})
        answer=self.engine(Model(d,d)).run('no-progress','minecraft','继续铺')
        self.assertIn('没有确认新的进展',answer);self.assertEqual(len(self.body.actions),1)
        m=Memory(self.path);guard=m.recent_actions()[-1]['receipt'];m.close()
        self.assertFalse(guard['executed']);self.assertTrue(guard['previous_verified'])
        self.assertEqual(guard['previous_status'],'placed_block_checked')
        self.assertTrue(any(row.get('event')=='action_repeat_blocked' for _,row in self.audit.rows))

    def test_repeat_permissions_do_not_survive_failed_placement(self):
        self.placement_body(fail_at=2)
        d=decision(action={'name':'place','args':{'block':'oak_planks'}})
        answer=self.engine(Model(d,d,d)).run('failed-second','minecraft','连续铺')
        self.assertEqual(len(self.body.actions),2);self.assertIn('没有得到成功确认',answer)

    def test_inventory_work_can_repeat_after_confirmed_gain_or_delivery(self):
        for name,args,receipt in (
            ('collect',{'block':'oak_log','count':1},{'status':'collection_inventory_checked','gained':1}),
            ('craft',{'item':'oak_planks','count':1},{'status':'craft_inventory_checked','gained':4}),
            ('give',{'item':'oak_planks','count':1},{'status':'give_entity_and_inventory_checked','lost':1,'matching_collected':1}),
        ):
            with self.subTest(name=name):
                self.body.actions=[]
                def start(action,**kwargs):
                    self.body.actions.append(action);future=concurrent.futures.Future()
                    future.set_result({'verified':True,**receipt});return future
                self.body.start_action=start
                d=decision(action={'name':name,'args':args})
                self.assertEqual(self.engine(Model(d,d,decision('完成两次。'))).run(name,'minecraft','继续'),'完成两次。')
                self.assertEqual(len(self.body.actions),2)

    def test_repeated_placement_still_obeys_eight_decision_cap(self):
        self.placement_body()
        d=decision(action={'name':'place','args':{'block':'oak_planks'}})
        model=Model(*[d for _ in range(8)])
        answer=self.engine(model).run('repeat-cap','minecraft','继续铺')
        self.assertEqual(len(self.body.actions),8);self.assertEqual(model.calls,8)
        self.assertIn('八次决定已用完',answer)

    def test_progress_requires_concrete_matching_effect(self):
        from .engine import confirmed_progress
        action={'name':'place','args':{'block':'oak_planks'}}
        receipt={'verified':True,'status':'placed_block_checked','position':{'x':1,'y':64,'z':0},
                 'placement':{'before_block':'air','after_block':'oak_planks','inventory_before':4,'inventory_after':3,'consumed':1}}
        self.assertTrue(confirmed_progress(action,receipt))
        for change in ({'before_block':'oak_planks'},{'after_block':'dirt'},{'inventory_after':4},{'consumed':0}):
            self.assertFalse(confirmed_progress(action,{**receipt,'placement':{**receipt['placement'],**change}}))
        self.assertFalse(confirmed_progress({'name':'inspect','args':{}},{'verified':True,'status':'observed'}))
        self.assertFalse(confirmed_progress({'name':'craft','args':{'item':'oak_planks','count':1}},
                                          {'verified':True,'status':'craft_inventory_checked','gained':0}))

    def test_failed_queries_and_navigation_still_block_and_record_explanation(self):
        from .engine import completed_negative_search
        self.assertFalse(completed_negative_search({'name':'search'}, {'status':'unknown_block','verified':False}))
        self.assertFalse(completed_negative_search({'name':'go_to_block'},
            {'status':'block_not_found','observation_complete':True,'found':False,'query':{'scope':'loaded_chunks_only'}}))
        self.body.verified=False
        model=Model(decision(action={'name':'search','args':{'block':'unknown','range':32}}),decision('没有有效查询。'))
        self.engine(model).run('bad','minecraft','查找')
        self.assertTrue(model.contexts[1]['execution_blocked']);self.assertEqual(len(self.body.actions),1)
        m=Memory(self.path)
        saved=[r['body'] for r in m.library.rows('reflection') if r['body'].get('execution_blocked')]
        m.close();self.assertEqual(saved[0]['decision']['reply'],'没有有效查询。')
        for name in ('search','go_to_block'):
            validate_action({'name':name,'args':{'block':'wood','range':128}})
            with self.assertRaises(ValueError):validate_action({'name':name,'args':{'block':'wood','range':129}})

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
