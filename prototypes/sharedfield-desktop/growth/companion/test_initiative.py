"""Mechanism tests with scripted decisions; these do not establish model learning."""
import copy
import tempfile
import threading
import time
import unittest
from pathlib import Path

from .behavior import validate_tree, next_action, accept_result
from .harness import Harness
from .memory import Memory
from .test_harness import Body, Model, delayed_result
from .test_kernel import Audit
from .initiative import projects, records, scope_problem

TEXT = '我忙一会儿，你可以用背包里的材料自己安排事情，只做合成和整理。'
CRAFT = {'name': 'craft', 'args': {'item': 'oak_planks', 'count': 1}}
RECOVER = {'name': 'recover_inventory', 'args': {}}


def leaf(identity, action):
    return {'id': identity, 'type': 'action', 'action': action}


def contract():
    return {'title': '准备可用材料', 'steps': ['准备材料', '核对变化'],
            'done_when': [{'kind': 'gained', 'item': 'oak_planks', 'count': 4}]}


def grant(context):
    return {'request_quote': context['current_user'], 'focus': '自己安排背包材料',
            'actions': ['craft', 'recover_inventory'], 'placement_radius': 0,
            'reply': '我会自己安排背包里的材料。'}


def proposal(context, tree=None):
    return {'candidates': ['试着准备以后可用的材料', '暂时安静'], 'choice': 0,
            'project_id': context['current_work']['initiative']['project_id'] if context.get('current_work') else None,
            'concern': '以后使用材料是否方便', 'goal': contract(),
            'tree': tree or leaf('craft', CRAFT),
            'based_on_policy': context['policies'][-1]['record_id'] if context['policies'] else None,
            'evidence_ids': [context['evidence_ids'][0]], 'reply': ''}


def repair(context):
    return proposal(context, {'id': 'recover_then_craft', 'type': 'sequence',
                             'children': [leaf('recover', RECOVER), leaf('craft', CRAFT)]})


def route(text, *args):
    return {'mode': 'autonomy' if text == TEXT else 'chat', 'task_kind': 'ordinary',
            'information_need': {'sources': ['goal'], 'memory_queries': [], 'question': '了解当前工作'}}


class InitiativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'state.sqlite'
        self.body, self.audit = Body(), Audit()
    def tearDown(self): self.temp.cleanup()
    def engine(self, model, **kw):
        return Harness(self.path, model, self.body, self.audit, input_router=route, **kw)
    def start(self, model):
        engine = self.engine(model)
        engine.run('grant', 'minecraft', TEXT)
        return engine
    def saved(self):
        with Memory(self.path) as memory: return memory.goal()['work']

    def test_delegation_drives_real_harness_effect_without_second_input(self):
        model = Model(grant, proposal)
        engine = self.start(model)
        self.assertTrue(engine.initiative.drain_one())
        self.assertEqual([a['name'] for a in self.body.actions], ['craft', 'inspect'])
        self.assertEqual(self.saved()['status'], 'completed')
        with Memory(self.path) as memory:
            self.assertEqual(len(projects(memory)), 1)
            row = memory.db.execute("SELECT channel,user_id FROM kernel_turns WHERE channel='initiative'").fetchone()
            self.assertEqual(row, ('initiative', None))
            self.assertEqual(len([r for r in memory.context() if r['role'] == 'user']), 1)
        self.assertEqual(model.calls, 2)

    def test_current_router_accepts_quoted_standing_delegation(self):
        routed = {'mode': 'autonomy', 'request_quote': TEXT, 'task_kind': 'ordinary',
                  'information_need': {'question': '选择自己的项目', 'sources': ['current_body'], 'memory_queries': []}}
        model = Model(routed, grant, proposal)
        engine = Harness(self.path, model, self.body, self.audit)
        engine.run('grant', 'minecraft', TEXT)
        engine.initiative.drain_one()
        self.assertEqual(self.saved()['status'], 'completed')

    def test_failure_changes_tree_and_retains_failure_and_policy_versions(self):
        self.body.state['crafting_grid'] = {'oak_log': 1}
        model = Model(grant, proposal, repair)
        engine = self.start(model)
        engine.initiative.drain_one()
        self.assertEqual([a['name'] for a in self.body.actions], ['craft', 'recover_inventory', 'craft', 'inspect'])
        self.assertEqual(self.saved()['initiative']['policy']['revision'], 2)
        self.assertEqual(self.saved()['status'], 'completed')
        with Memory(self.path) as memory:
            self.assertEqual(len(records(memory, 'skill', 'initiative_policy')), 2)
            self.assertTrue(any(r['body'].get('receipt', {}).get('verified') is False
                                for r in memory.library.rows('experience')))

    def test_completion_event_deduplicates_and_no_grant_means_no_calls(self):
        engine = self.engine(Model())
        engine.initiative.enqueue('same', 'task_completed', [])
        self.assertFalse(engine.initiative.drain_one())
        engine = self.start(Model(grant, proposal))
        engine.initiative.drain_one()
        with Memory(self.path) as memory: identity = memory.goal()['work']['task_id']
        size = len(engine.initiative.queue)
        engine.initiative.enqueue('completed:' + identity, 'task_completed', [])
        self.assertEqual(len(engine.initiative.queue), size)

    def test_idle_is_valid_and_no_effect_or_recursive_event(self):
        def idle(context):
            value = proposal(context)
            value.update(choice=None, goal=None, tree=None)
            return value
        engine = self.start(Model(grant, idle))
        engine.initiative.drain_one()
        self.assertEqual(self.body.actions, [])
        self.assertEqual(engine.initiative.queue, [])

    def test_stop_discards_late_plan_and_clears_events(self):
        entered, release = threading.Event(), threading.Event()
        def slow(context):
            entered.set(); release.wait(4)
            return proposal(context)
        engine = self.start(Model(grant, slow))
        worker = threading.Thread(target=engine.initiative.drain_one)
        worker.start(); self.assertTrue(entered.wait(2))
        engine.stop(); release.set(); worker.join(4)
        self.assertFalse(worker.is_alive())
        self.assertEqual(self.body.actions, [])
        self.assertEqual(engine.initiative.queue, [])
        self.assertEqual(len(self.body.speech), 1)
        with Memory(self.path) as memory:
            self.assertEqual(records(memory, 'skill', 'initiative_policy'), [])

    def test_restart_preserves_project_and_policy_but_never_replays(self):
        engine = self.start(Model(grant, proposal))
        engine.initiative.drain_one()
        old_project = self.saved()['initiative']['project_id']
        count = len(self.body.actions)
        restarted = self.engine(Model())
        restarted.initiative.pulse()
        self.assertFalse(restarted.initiative.drain_one())
        self.assertEqual(len(self.body.actions), count)
        with Memory(self.path) as memory:
            self.assertEqual(projects(memory)[0]['project_id'], old_project)
            self.assertEqual(len(records(memory, 'skill', 'initiative_policy')), 1)

    def test_deleted_authority_cannot_drive_an_event(self):
        engine = self.start(Model(grant))
        with Memory(self.path) as memory:
            memory.store.delete_private(memory.record(engine.initiative.grant_id)['source_id'])
        self.assertFalse(engine.initiative.drain_one())
        self.assertEqual(self.body.actions, [])
        self.assertIsNone(engine.initiative.grant_id)

    def test_tree_outside_delegation_rejected_before_effect(self):
        def outside(context): return proposal(context, leaf('mine', {'name': 'collect', 'args': {'block': 'oak_log', 'count': 1}}))
        engine = self.start(Model(grant, outside))
        engine.initiative.drain_one()
        self.assertEqual(self.body.actions, [])
        self.assertTrue(any(r.get('error_code') == 'initiative_action_outside_delegation' for _, r in self.audit.rows))

    def test_model_call_cap_does_not_bypass_shared_budget(self):
        engine = self.start(Model(grant))
        engine.initiative.MAX_MODEL_CALLS = 0
        engine.initiative.drain_one()
        self.assertEqual(engine.model.calls, 1)
        self.assertEqual(self.body.actions, [])

    def test_fallback_conditions_have_executable_semantics(self):
        tree = validate_tree({'id': 'root', 'type': 'fallback', 'children': [
            {'id': 'ready', 'type': 'condition', 'condition': {'kind': 'inventory_clear'}}, leaf('recover', RECOVER)]})
        policy = {'tree': tree}
        state = self.body.snapshot(); state['crafting_grid'] = {'oak_log': 1}
        self.assertEqual(next_action(policy, state), RECOVER)
        accept_result(policy, RECOVER, {'verified': True})
        self.assertIsNone(next_action(policy, state))
        self.assertEqual(policy['status'], 'success')
        with self.assertRaises(ValueError): validate_tree({'id': 'code', 'type': 'exec', 'code': 'anything'})

    def test_spatial_scope_and_no_demolition(self):
        bounded = {'actions': ['place_at'], 'anchor': {'x': 0, 'y': 64, 'z': 0}, 'placement_radius': 2}
        action = {'name': 'place_at', 'args': {'block': 'oak_planks', 'position': {'x': 3, 'y': 64, 'z': 0}}}
        self.assertEqual(scope_problem(bounded, action), 'initiative_placement_outside_area')
        action['args']['position']['x'] = 1
        self.assertIsNone(scope_problem(bounded, action))
        action['args']['block'] = 'air'
        self.assertIsNotNone(scope_problem(bounded, action))

    def test_chat_during_autonomous_action_resumes_same_goal(self):
        entered, release = threading.Event(), threading.Event()
        original = self.body.start_action
        def delayed(action, **kw):
            result = original(action, **kw)
            return delayed_result(result, entered, release) if action['name'] == 'craft' else result
        self.body.start_action = delayed
        engine = self.start(Model(grant, proposal, {'reply': '我正在准备材料。'}))
        worker = threading.Thread(target=engine.initiative.drain_one)
        worker.start(); self.assertTrue(entered.wait(2))
        chat = threading.Thread(target=lambda: engine.run('chat', 'minecraft', '你在做什么'))
        chat.start()
        deadline = time.monotonic() + 2
        while not engine._waiting and time.monotonic() < deadline: time.sleep(.005)
        self.assertTrue(engine._waiting)
        release.set(); worker.join(4); chat.join(4)
        self.assertFalse(worker.is_alive() or chat.is_alive())
        self.assertEqual(self.saved()['status'], 'completed')
        self.assertEqual([a['name'] for a in self.body.actions], ['craft', 'inspect'])
        self.assertEqual(engine.model.calls, 3)
        self.assertTrue(any(r.get('event') == 'task_resumed_after_conversation' for _, r in self.audit.rows))

    def test_result_contract_cannot_be_lowered_during_revision(self):
        self.body.always_fail = True
        def weaken(context):
            value = proposal(context)
            value['goal']['done_when'] = [{'kind': 'inventory', 'item': 'oak_planks', 'count': 1}]
            return value
        engine = self.start(Model(grant, proposal, weaken))
        engine.initiative.drain_one()
        self.assertEqual(self.saved()['done_when'], contract()['done_when'])
        self.assertEqual(self.saved()['status'], 'blocked')
        self.assertEqual(len(self.body.actions), 1)
        with Memory(self.path) as memory:
            self.assertEqual(len(records(memory, 'skill', 'initiative_policy')), 1)

    def test_finite_event_and_effect_bounds(self):
        engine = self.start(Model(grant, proposal))
        engine.initiative.MAX_EFFECT_ACTIONS = 0
        engine.initiative.drain_one()
        self.assertEqual(self.body.actions, [])
        self.assertEqual(self.saved()['last_problem'], 'initiative_action_cap')
        engine.initiative.MAX_EVENTS = 1
        engine.initiative.enqueue('more', 'body_changed', [])
        self.assertEqual(engine.initiative.queue, [])

    def test_placement_uses_world_verifier(self):
        text = '在你现在位置2格内自己安排放木板。'
        def spatial_grant(context):
            return {**grant(context), 'actions': ['place_at'], 'placement_radius': 2}
        position = {'x': 1, 'y': 64, 'z': 0}
        def spatial_plan(context):
            value = proposal(context, leaf('place', {'name': 'place_at', 'args': {'block': 'oak_planks', 'position': position}}))
            value['goal'] = {'title': '试一种摆法', 'steps': ['放置并观察'],
                             'done_when': [{'kind': 'blocks', 'block': 'oak_planks', 'positions': [position]}]}
            return value
        engine = Harness(self.path, Model(spatial_grant, spatial_plan), self.body, self.audit,
                         input_router=lambda *args: {'mode': 'autonomy', 'task_kind': 'ordinary'})
        engine.run('spatial', 'minecraft', text)
        engine.initiative.drain_one()
        self.assertEqual(self.saved()['status'], 'completed')
        self.assertTrue(self.saved()['completion']['world_verified'])
        self.assertEqual([a['name'] for a in self.body.actions], ['verify_blocks', 'place_at', 'verify_blocks'])

    def test_redelegation_loads_same_project_and_policy_without_reteaching(self):
        engine = self.start(Model(grant, proposal))
        engine.initiative.drain_one()
        old_project = self.saved()['initiative']['project_id']
        def reuse(context):
            self.assertEqual(context['projects'][0]['project_id'], old_project)
            self.assertTrue(context['policies'])
            value = proposal(context)
            value['project_id'] = old_project
            return value
        restarted = self.engine(Model(grant, reuse))
        restarted.run('regrant', 'minecraft', TEXT)
        restarted.initiative.drain_one()
        self.assertEqual(self.saved()['status'], 'completed')
        self.assertEqual(self.saved()['initiative']['project_id'], old_project)

    def test_pulse_dispatches_without_blocking_its_caller(self):
        engine = self.start(Model(grant, proposal))
        started = time.monotonic()
        engine.initiative.pulse()
        self.assertLess(time.monotonic() - started, 1)
        engine.initiative.worker.join(3)
        self.assertFalse(engine.initiative.worker.is_alive())
        self.assertEqual(self.saved()['status'], 'completed')

    def test_already_satisfied_goal_does_not_create_a_fake_achievement(self):
        def trivial(context):
            value = proposal(context)
            value['goal']['done_when'] = [{'kind': 'inventory', 'item': 'oak_planks', 'count': 1}]
            return value
        engine = self.start(Model(grant, trivial))
        engine.initiative.drain_one()
        self.assertEqual(self.body.actions, [])
        with Memory(self.path) as memory:
            self.assertIsNone(memory.goal())


if __name__ == '__main__': unittest.main()
