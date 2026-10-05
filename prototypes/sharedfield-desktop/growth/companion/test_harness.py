import concurrent.futures
import copy
import tempfile
import threading
import time
import unittest
from pathlib import Path

from .harness import Harness
from .memory import Memory
from .test_kernel import Audit
from .work import validate_goal, validate_action


def decision(**kw):
    return dict(reply='', goal=None, convention=None, forget_card=None, action=None, status='continue', **kw) if not kw else {
        **dict(reply='', goal=None, convention=None, forget_card=None, action=None, status='continue'), **kw}


def goal(n=2):
    return {'title': f'放置{n}块木板', 'steps': ['准备木板', '连续放置', '核对方块'],
            'done_when': [{'kind': 'placed', 'block': 'oak_planks', 'count': n}]}


def place(g=None):
    return decision(goal=g, action={'name': 'place', 'args': {'block': 'oak_planks'}})


def delayed_result(result, entered, release):
    """Match Body.start_action: dispatch returns a future without blocking."""
    future = concurrent.futures.Future()
    def finish():
        if release.wait(4): future.set_result(result.result())
        else: future.set_exception(TimeoutError('test_release'))
    threading.Thread(target=finish, daemon=True).start()
    entered.set()
    return future


class Model:
    def __init__(self, *steps): self.steps=list(steps); self.calls=0; self.contexts=[]
    def decide(self, prompt, context):
        self.calls+=1; self.contexts.append(copy.deepcopy(context))
        step=self.steps.pop(0)
        return step(context) if callable(step) else copy.deepcopy(step)


class Body:
    def __init__(self):
        self.actions=[]; self.speech=[]; self.stops=0; self.blocks={}; self.always_fail=False
        self.state={'offline':False,'position':{'x':0,'y':64,'z':0},'inventory':{'oak_planks':30,'oak_log':2},
                    'crafting_grid':{},'cursor':None,'window':None,'owner':{'distance':2,'height_difference':0}}
    def snapshot(self):return copy.deepcopy(self.state)
    def say(self,text):self.speech.append(text)
    def stop(self):self.stops+=1;return {'verified':True,'status':'stopped'}
    def start_action(self,a,**kwargs):
        self.actions.append(a)
        name=a['name']; r={'verified':True,'status':'observed'}
        if name in ('place','place_at'):
            before=self.state['inventory']['oak_planks'];self.state['inventory']['oak_planks']-=1
            p=a['args'].get('position', {'x':len(self.blocks)+1,'y':64,'z':0})
            self.blocks[tuple(p.values())]='oak_planks'
            r={'verified':True,'status':'placed_block_checked','position':p,
               'placement':{'before_block':'air','after_block':'oak_planks','inventory_before':before,'inventory_after':before-1,'consumed':1}}
        elif name=='recover_inventory':
            self.state['crafting_grid']={};self.state['cursor']=None
            r={'verified':True,'status':'inventory_recovered','conserved':True}
        elif name=='craft':
            if self.state['crafting_grid'] or self.always_fail:
                r={'verified':False,'status':'crafting_grid_or_cursor_not_clear'}
            else:
                self.state['inventory']['oak_planks']+=4
                r={'verified':True,'status':'craft_inventory_checked','gained':4}
        elif name=='verify_blocks':
            r={'verified':all(self.blocks.get(tuple(t['position'].values()))==t['block'] for t in a['args']['targets']), 'status':'goal_blocks_checked'}
        r['observed']=self.snapshot()
        f=concurrent.futures.Future();f.set_result(r);return f


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite';self.body=Body();self.audit=Audit()
    def tearDown(self):self.tmp.cleanup()
    def engine(self,model,**kw):
        # Actor-loop fixtures have already-classified task inputs; production routing is tested separately.
        return Harness(self.path,model,self.body,self.audit,input_router=lambda text,*args:{'mode':'resume' if text.startswith('继续') else 'task','task_kind':'ordinary'},**kw)
    def saved(self):
        m=Memory(self.path)
        try:return m.goal()['work']
        finally:m.close()
    def test_one_input_continues_beyond_eight_then_verifies_goal(self):
        model=Model(place(goal(10)),*[place() for _ in range(9)])
        e=self.engine(model);e.run('ten','minecraft','连续放10块')
        self.assertEqual(len(self.body.blocks),10);self.assertEqual(model.calls,10)
        self.assertEqual(self.saved()['status'],'completed');self.assertEqual(self.saved()['checkpoints'],1)
        self.assertTrue(any(r.get('event')=='task_checkpoint' and r['continues'] for _,r in self.audit.rows))
        e.run('ten','minecraft','连续放10块');self.assertEqual(model.calls,10)
    def test_recover_then_craft_and_place_without_another_input(self):
        self.body.state['crafting_grid']={'oak_log':1}
        craft={'name':'craft','args':{'item':'oak_planks','count':1}}
        model=Model(decision(goal=goal(),action=craft), decision(action={'name':'recover_inventory','args':{}}),
                    decision(action=craft),place(),place())
        self.engine(model).run('recover','minecraft','整理后放两块')
        self.assertEqual(self.saved()['status'],'completed');self.assertEqual(model.calls,5)
        self.assertEqual([a['name'] for a in self.body.actions],['craft','recover_inventory','craft','place','place','verify_blocks'])
        self.assertEqual(model.contexts[1]['harness_notice']['kind'],'recover_or_replan')
    def test_same_failed_action_same_state_is_not_executed_again(self):
        self.body.always_fail=True
        craft={'name':'craft','args':{'item':'oak_planks','count':1}}
        model=Model(decision(goal=goal(),action=craft),decision(action=craft),decision(action=craft))
        self.engine(model).run('fail','minecraft','放两块')
        self.assertEqual(len(self.body.actions),1);self.assertEqual(self.saved()['status'],'blocked')
    def test_prose_completion_without_world_proof_rejected(self):
        model=Model(decision(goal=goal(),status='done',reply='我完成了'),decision(status='done',reply='完成了'))
        answer=self.engine(model).run('false','minecraft','放两块')
        self.assertEqual(self.saved()['status'],'blocked');self.assertNotIn('我完成了',answer)
        self.assertEqual(self.body.actions,[])
    def test_model_cannot_lower_active_contract(self):
        changed=goal(3);changed['done_when'][0]['count']=1
        model=Model(place(goal(3)),decision(goal=changed,status='done'),decision(goal=changed,status='done'))
        self.engine(model).run('change','minecraft','放3块')
        self.assertEqual(self.saved()['done_when'][0]['count'],3);self.assertEqual(self.saved()['status'],'blocked')
    def test_restart_keeps_progress_but_never_replays_old_input(self):
        self.engine(Model(place(goal(3))),max_decisions=1).run('first','minecraft','放3块')
        self.assertEqual(self.saved()['status'],'paused_limit')
        model=Model(place(),place()); e=self.engine(model)
        e.run('first','minecraft','放3块');self.assertEqual(model.calls,0)
        e.run('second','minecraft','继续');self.assertEqual(len(self.body.blocks),3)
        self.assertEqual(self.saved()['status'],'completed')
    def test_late_decision_discarded_on_stop(self):
        entered=threading.Event();release=threading.Event()
        def wait(_):entered.set();release.wait(3);return place(goal())
        e=self.engine(Model(wait));t=threading.Thread(target=e.run,args=('late','minecraft','放两块'));t.start()
        self.assertTrue(entered.wait(2));e.stop();release.set();t.join(3)
        self.assertFalse(t.is_alive());self.assertEqual(self.body.actions,[])
    def test_new_input_yields_at_boundary_and_keeps_same_task(self):
        entered=threading.Event();release=threading.Event();original=self.body.start_action
        def first(a,**kw):
            first_call=not self.body.actions
            result=original(a,**kw)
            return delayed_result(result,entered,release) if first_call else result
        self.body.start_action=first
        model=Model(place(goal(3)),place(),place());e=self.engine(model)
        one=threading.Thread(target=e.run,args=('a','minecraft','放3块'));one.start();self.assertTrue(entered.wait(2))
        two=threading.Thread(target=e.run,args=('b','airi','继续，保持原目标'));two.start()
        limit=time.monotonic()+2
        while not e._waiting and time.monotonic()<limit:time.sleep(.01)
        self.assertEqual(e._waiting,1);release.set();one.join(3);two.join(3)
        self.assertFalse(one.is_alive() or two.is_alive());self.assertEqual(self.saved()['status'],'completed')
        self.assertEqual(model.contexts[1]['current']['user'],'继续，保持原目标')
        self.assertEqual(len(self.body.blocks),3)
    def test_readback_rejects_destroyed_block(self):
        original=self.body.start_action
        def remove(a,**kw):
            if a['name']=='verify_blocks':self.body.blocks.clear()
            return original(a,**kw)
        self.body.start_action=remove
        e=self.engine(Model(place(goal(1)),decision(status='blocked',reply='方块已不在原处。')))
        e.run('destroyed','minecraft','放1块');self.assertEqual(self.saved()['status'],'blocked')
    def test_chat_works_without_mc(self):
        self.body.state={'offline':True}
        # Exercise the real no-action conversation path, not the task-only fixture router.
        from .test_turns import route
        engine=Harness(self.path,Model(route('chat'),{'reply':'我在。'}),self.body,self.audit)
        self.assertEqual(engine.run('chat','airi','在吗'),'我在。')
        self.assertEqual(self.body.actions,[])
    def test_convention_can_be_saved_and_used_by_harness(self):
        model=Model(decision(convention={'trigger':'蓝灯','meaning':'走到我身边','replaces':None}),decision(status='chat',reply='记住了。'))
        self.engine(model).run('teach','airi','蓝灯代表走到我身边。')
        m=Memory(self.path)
        try:self.assertEqual(m.library.cards()[0]['meaning'],'走到我身边')
        finally:m.close()
    def test_spatial_contract_and_action_validation(self):
        validate_action({'name':'place_at','args':{'block':'oak_planks','position':{'x':1,'y':64,'z':0}}})
        for a in ({'name':'recover_inventory','args':{'drop':True}}, {'name':'inspect_area','args':{'radius':9}},
                  {'name':'place_at','args':{'block':'oak_planks','position':{'x':True,'y':64,'z':0}}}):
            with self.assertRaises(ValueError):validate_action(a)
        for c in ({'kind':'any_success'}, {'kind':'placed','block':'oak_planks','count':0}):
            with self.assertRaises(ValueError):validate_goal({**goal(),'done_when':[c]})


if __name__=='__main__':unittest.main(verbosity=2)
