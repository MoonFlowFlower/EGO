import copy
import tempfile
import threading
import time
import unittest
from pathlib import Path
from .harness import Harness
from .interaction import action_problem, bind_request, input_event, reconcile_pickups
from .interaction_scene import InteractionScene
from .memory import Memory
from .recall import recall
from .test_harness import Model, decision, goal, place
from .test_kernel import Audit
from .work import create_work, save_work, incorporate, preliminary_completion, fingerprint


def pickup_goal():
    return {'title': '捡起指定原木', 'steps': ['观察物品', '拾取并核对'],
            'done_when': [{'kind': 'picked_up', 'item': 'wood', 'count': 8}]}


def task(kind='ordinary'):
    return lambda *args: {'mode': 'task', 'task_kind': kind}


class InteractionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.path = Path(self.tmp.name) / 'state.sqlite'
        self.body = InteractionScene(); self.audit = Audit()

    def tearDown(self):
        self.body.release(); self.tmp.cleanup()

    def saved(self):
        m = Memory(self.path)
        try: return m.goal()['work']
        finally: m.close()

    def seed(self):
        m = Memory(self.path); source, _ = m.begin('old', 'verification', '铺8块木板')
        w = create_work(goal(8), self.body.snapshot(), source); w['status'] = 'blocked'
        save_work(m, w, [source]); m.finish('old', '没铺完', [source]); m.close(); return w

    def test_new_request_cannot_act_under_old_goal(self):
        old = self.seed()
        model = Model(decision(action={'name': 'approach', 'args': {}}), place())
        Harness(self.path, model, self.body, self.audit, input_router=task('approach'), max_decisions=2).run('new', 'verification', '过来一下')
        self.assertEqual(self.body.actions, [])
        self.assertEqual(self.saved()['task_id'], old['task_id'])

    def test_come_has_own_goal_finishes_and_preserves_suspended_task(self):
        old = self.seed()
        near = {'title': '走到玩家身边', 'steps': ['走近'], 'done_when': [{'kind': 'near_owner'}]}
        model = Model(decision(goal=near, action={'name': 'approach', 'args': {}}))
        Harness(self.path, model, self.body, self.audit, input_router=task('approach')).run('new', 'verification', '过来一下')
        self.assertNotEqual(self.saved()['task_id'], old['task_id']); self.assertEqual(self.saved()['status'], 'completed')
        self.assertEqual([a['name'] for a in self.body.actions], ['approach', 'inspect'])
        m = Memory(self.path)
        try: self.assertTrue(any(r['body'].get('type') == 'suspended_task' for r in m.library.rows('project')))
        finally: m.close()

    def test_incompatible_primitive_steering_establishes_new_goal(self):
        old=self.seed()
        near={'title':'走近玩家','steps':['走近'],'done_when':[{'kind':'near_owner'}]}
        model=Model(decision(goal=near,action={'name':'approach','args':{}}))
        Harness(self.path,model,self.body,self.audit,input_router=lambda *a:{'mode':'steer','task_kind':'approach'}).run('come','verification','过来一下')
        self.assertEqual(self.saved()['status'],'completed');self.assertNotEqual(self.saved()['task_id'],old['task_id'])

    def test_pickup_contract_cannot_be_inventory_gain(self):
        bad = pickup_goal(); bad['done_when'] = [{'kind': 'gained', 'item': 'oak_log', 'count': 8}]
        model = Model(decision(goal=bad, action={'name': 'collect', 'args': {'block': 'oak_log', 'count': 8}}), decision(goal=bad))
        Harness(self.path, model, self.body, self.audit, input_router=task('pickup')).run('pick', 'verification', '捡起8个原木')
        self.assertEqual(self.body.actions, [])

    def test_legacy_inventory_only_pickup_cannot_complete_on_resume(self):
        m=Memory(self.path);source,_=m.begin('old','verification','捡8个原木')
        legacy=pickup_goal();legacy['done_when']=[{'kind':'gained','item':'oak_log','count':8}]
        w=create_work(legacy,self.body.snapshot(),source);w['status']='blocked';save_work(m,w,[source]);m.close()
        self.body.state['inventory']['oak_log']=10
        engine=Harness(self.path,Model(),self.body,self.audit,input_router=lambda *a:{'mode':'resume','task_kind':'pickup'})
        engine.run('resume','verification','继续')
        self.assertEqual(self.saved()['status'],'waiting_user');self.assertEqual(self.body.actions,[])

    def test_bound_pickup_requires_events_and_inventory(self):
        a = {'name': 'pickup_items', 'args': {'entity_ids': [41], 'item': 'wood', 'count': 8}}
        w = create_work(pickup_goal(), self.body.snapshot(), 'source')
        self.body.state['inventory']['oak_log'] = 8
        self.assertFalse(preliminary_completion(w, self.body.snapshot())['satisfied'])
        self.body.state['inventory'].pop('oak_log')
        receipt = self.body.start_action(a).result(); incorporate(w, a, receipt)
        self.assertTrue(preliminary_completion(w, self.body.snapshot())['satisfied'])
        incorporate(w, a, receipt); self.assertEqual(w['picked_up'], {'oak_log': 8})

    def test_pickup_cannot_search_or_collect_tree(self):
        w = create_work(pickup_goal(), self.body.snapshot(), 'source')
        self.assertEqual(action_problem(w, {'name': 'collect', 'args': {}}, self.body.snapshot()), 'action_outside_current_request')

    def test_passive_pickup_after_request_is_verified_and_old_events_are_ignored(self):
        event = input_event('new', 'verification', '捡原木', self.body.snapshot())
        w = create_work(pickup_goal(), self.body.snapshot(), 'source');bind_request(w,event,'pickup')
        s = self.body.snapshot();s['inventory']['oak_log']=8
        s['recent_pickups']=[{'entity_key':'body:41','entity_id':41,'item':'oak_log','count':8,
            'position':{'x':4,'y':64,'z':0},'collected_at':event['received_at']*1000-1}]
        reconcile_pickups(w,s);self.assertEqual(w['picked_up'],{})
        s['recent_pickups'][0]['collected_at']+=2
        reconcile_pickups(w,s);reconcile_pickups(w,s)
        self.assertEqual(w['picked_up'],{'oak_log':8});self.assertTrue(preliminary_completion(w,s)['satisfied'])

    def test_steering_changes_revision_and_latest_input_without_new_task(self):
        self.body.hold = 'observe_items'
        pick = {'name': 'pickup_items', 'args': {'entity_ids': [42], 'item': 'wood', 'count': 8}}
        model = Model(decision(goal=pickup_goal(), action={'name': 'observe_items', 'args': {'range': 16}}), decision(action=pick))
        router = lambda text,*a: {'mode': 'steer' if text == '这儿' else 'task', 'task_kind': 'pickup'}
        engine = Harness(self.path, model, self.body, self.audit, input_router=router)
        first = threading.Thread(target=lambda: engine.run('pick', 'verification', '捡一下8个原木'))
        first.start(); self.assertTrue(self.body.entered.wait(3)); before = self.saved()
        self.body.state['owner']['position']['x'] = 8
        self.body.state['dropped_items']['items'] = [self.body.item(42, 8)]
        second = threading.Thread(target=lambda: engine.run('steer', 'verification', '这儿'))
        second.start()
        end = time.monotonic()+3
        while not engine._waiting and time.monotonic()<end: time.sleep(.005)
        self.body.release(); first.join(4); second.join(4)
        self.assertFalse(first.is_alive() or second.is_alive())
        after = self.saved(); self.assertEqual(after['task_id'], before['task_id']); self.assertEqual(after['revision'], 2)
        self.assertEqual(after['status'], 'completed'); self.assertEqual(model.contexts[-1]['current']['user'], '这儿')
        self.assertEqual(model.contexts[-1]['current']['body_at_input']['owner']['position']['x'], 8)

    def test_question_is_sent_and_actions_wait(self):
        model = Model(decision(goal=pickup_goal(), status='waiting_user', reply='你指的是哪一堆？',
                               action={'name': 'collect', 'args': {'block': 'oak_log', 'count': 8}}))
        Harness(self.path, model, self.body, self.audit, input_router=task('pickup')).run('pick', 'verification', '捡原木')
        self.assertIn('你指的是哪一堆？', self.body.speech); self.assertEqual(self.saved()['status'], 'waiting_user')
        self.assertEqual(self.body.actions, [])

    def test_structure_cannot_promise_execution(self):
        model = Model()
        reply = Harness(self.path, model, self.body, self.audit, input_router=task('structure')).run('house', 'verification', '建房')
        self.assertIn('不能承诺', reply); self.assertEqual(model.calls, 0); self.assertEqual(self.body.actions, [])

    def test_fresh_observation_allowed_and_repetition_bounded(self):
        inspect = {'name': 'inspect', 'args': {}}
        model = Model(decision(goal=goal(8), action=inspect), *[decision(action=inspect) for _ in range(5)])
        Harness(self.path, model, self.body, self.audit, input_router=task()).run('observe', 'verification', '观察后放8块')
        self.assertGreater(len(self.body.actions), 1); self.assertEqual(self.saved()['status'], 'waiting_user')
        self.assertLessEqual(len(self.body.actions), 5)
        a = self.body.snapshot(); b = copy.deepcopy(a); b['owner']['position']['x'] = 100
        self.assertNotEqual(fingerprint(a), fingerprint(b))

    def test_recall_active_quoted_candidates_and_forget(self):
        m = Memory(self.path)
        try:
            source, _ = m.begin('teach', 'verification', '蓝灯碰头表示走到我身边')
            card = m.propose({'trigger': '蓝灯碰头', 'meaning': '走到我身边', 'replaces': None}, source)
            for n in range(520):
                m.append('experience', {'type': 'action_receipt', 'task_title': '无关采矿',
                    'action': {'name': 'collect', 'args': {'block': 'stone'}}, 'receipt': {'status': 'observed'}}, [])
            result = recall(m, '碰头之前的约定')
            self.assertEqual(result['candidates'][0]['record_id'], card)
            self.assertEqual(result['candidates'][0]['source_ids'], [source])
            self.assertEqual(recall(m, 'unrelated_zebra')['candidates'], [])
            m.forget(card); self.assertEqual(recall(m, '蓝灯碰头')['candidates'], [])
        finally: m.close()

    def test_recall_is_not_body_observation_or_permission(self):
        m = Memory(self.path)
        try:
            source, _ = m.begin('past', 'verification', '拾取原木')
            m.append('experience', {'type': 'action_receipt', 'event_id': 'past', 'task_title': '拾取原木',
                'action': {'name': 'pickup_items', 'args': {}}, 'receipt': {'verified': False, 'status': 'pickup_partial',
                'observed': {'inventory': {'diamond': 100}}}}, [source])
            result = recall(m, '拾取原木')
            self.assertNotIn('diamond', str(result)); self.assertIn('historical_result', str(result))
        finally: m.close()


if __name__ == '__main__': unittest.main()
