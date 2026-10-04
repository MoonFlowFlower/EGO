"""Regressions for current-state authority and the real serialized input entry."""
import copy
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from .harness import Harness
from .memory import Memory
from .server import KernelServer
from .test_harness import Body, Model, decision, goal, place, delayed_result
from .test_kernel import Audit
from .test_turns import route
from .work import create_work, save_work


class ContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'state.sqlite'
        self.body, self.audit = Body(), Audit()
        self.threads = []
        self.release = threading.Event()

    def tearDown(self):
        self.release.set()
        for thread in self.threads:
            thread.join(4)
            self.assertFalse(thread.is_alive())
        self.tmp.cleanup()

    def saved(self):
        m = Memory(self.path)
        try:
            return m.goal()
        finally:
            m.close()

    def start(self, e, identity, text, channel='minecraft'):
        result = []
        thread = threading.Thread(target=lambda: result.append(e.run(identity, channel, text)), daemon=True)
        self.threads.append(thread)
        thread.start()
        return thread, result

    def queue(self, e, identity, text, count=1):
        thread, result = self.start(e, identity, text, 'airi')
        deadline = time.monotonic() + 2
        while e._waiting < count and time.monotonic() < deadline:
            time.sleep(.005)
        self.assertEqual(e._waiting, count)
        return thread, result

    def hold_first_action(self):
        entered = threading.Event()
        original = self.body.start_action
        def held(action, **kw):
            result = original(action, **kw)
            if len(self.body.actions) == 1:
                return delayed_result(result, entered, self.release)
            return result
        self.body.start_action = held
        return entered

    def seed_old_state(self):
        m = Memory(self.path)
        source, _ = m.begin('old', 'minecraft', '我喜欢一起做事。先放两块木板。')
        work = create_work(goal(), self.body.snapshot(), source)
        work['status'], work['last_problem'] = 'blocked', 'crafting_grid_or_cursor_not_clear'
        save_work(m, work, [source])
        m.append('experience', {'type': 'action_receipt', 'action': {'name': 'craft', 'args': {}},
                 'receipt': {'verified': False, 'status': 'crafting_grid_or_cursor_not_clear',
                             'observed': {'crafting_grid': {'oak_log': 17}, 'cursor': {'name': 'oak_log', 'count': 17}}}}, [source])
        m.finish('old', '历史错误断言：合成格和光标现在还卡着17根原木。', [source])
        original = m.goal()
        m.close()
        return original

    def test_chat_projection_removes_stale_assertions_without_erasing_history(self):
        original = self.seed_old_state()
        model = Model(route('status'), {'reply': '现在合成格和光标都是空的。'})
        Harness(self.path, model, self.body, self.audit).run('now', 'airi', '合成格和光标现在怎么样？')
        context = model.contexts[-1]
        encoded = json.dumps(context, ensure_ascii=False)
        self.assertTrue(all(r['authority']=='past_utterance_not_current_world_fact' for r in context['dialogue']))
        self.assertNotIn('历史错误断言', json.dumps(context['current_body'], ensure_ascii=False))
        self.assertNotIn('"observed"', encoded)
        self.assertNotIn('"baseline"', encoded)
        self.assertEqual(context['current_body']['state']['crafting_grid'], {})
        self.assertIsNone(context['current_body']['state']['cursor'])
        self.assertIn('我喜欢一起做事', encoded)
        self.assertEqual(self.saved(), original)
        m = Memory(self.path)
        try:
            self.assertIn('历史错误断言', m.cached('old'))
        finally:
            m.close()

    def test_offline_projection_does_not_advertise_old_values_as_current(self):
        self.body.state.update(offline=True, inventory={'diamond': 17})
        model = Model(route('status'), {'reply': '目前离线，无法确认库存。'})
        Harness(self.path, model, self.body, self.audit).run('off', 'airi', '现在有多少材料？')
        current = model.contexts[-1]['current_body']
        self.assertFalse(current['available'])
        self.assertNotIn('diamond', json.dumps(current))

    def test_actual_residue_and_missing_fields_are_not_replaced_by_defaults(self):
        self.body.state['crafting_grid'] = {'acacia_log': 1}
        self.body.state['cursor'] = {'name': 'acacia_planks', 'count': 2}
        del self.body.state['window']
        model = Model(route('status'), {'reply': '合成格和光标确实还有东西。'})
        Harness(self.path, model, self.body, self.audit).run('residue', 'airi', '整理好了吗？')
        current = model.contexts[-1]['current_body']
        self.assertEqual(current['state']['crafting_grid'], {'acacia_log': 1})
        self.assertEqual(current['state']['cursor']['count'], 2)
        self.assertNotIn('window', current['state'])

    def test_chat_returns_then_same_turn_continues_with_new_observation(self):
        entered = self.hold_first_action()
        def chat(_):
            self.body.state['position']['x'] = 9
            return {'reply': '我在，已经放了一块。'}
        model = Model(route('task', quote='放两块'), place(goal()), route('status'), chat, place())
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块')
        self.assertTrue(entered.wait(2))
        task = self.saved()['work']
        conversation, replies = self.queue(e, 'chat', '进展怎么样？')
        self.release.set()
        conversation.join(3); original.join(3)
        self.assertEqual(replies, ['我在，已经放了一块。'])
        saved = self.saved()['work']
        self.assertEqual(saved['status'], 'completed')
        for key in ('task_id', 'source_id', 'done_when'):
            self.assertEqual(saved[key], task[key])
        self.assertEqual(len(self.body.blocks), 2)
        self.assertEqual(model.contexts[-1]['body']['position']['x'], 9)
        self.assertEqual(model.contexts[-1]['current']['user'], '放两块')
        self.assertEqual(model.contexts[-1]['remaining_decisions'], 63)
        actions = [row for _, row in self.audit.rows if row.get('event_id') == 'chat' and 'action' in row]
        self.assertEqual(actions, [])
        calls = model.calls
        e.run('chat', 'airi', '进展怎么样？'); e.run('task', 'minecraft', '放两块')
        self.assertEqual(model.calls, calls)
        self.assertEqual(len(self.body.blocks), 2)

    def test_multiple_chats_drain_before_resume(self):
        entered = self.hold_first_action()
        model = Model(route('task', quote='放两块'), place(goal()),
                      route('chat'), {'reply': '嗯。'}, route('status'), {'reply': '还有一块。'}, place())
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'a', '嗨'); self.queue(e, 'b', '还有多少？', 2)
        self.release.set(); original.join(4)
        self.assertEqual(self.saved()['goal_status'], 'completed')
        self.assertEqual(model.contexts[-1]['work']['actions'], 1)
        self.assertEqual(model.calls, 7)

    def test_stop_during_chat_revokes_continuation(self):
        entered = self.hold_first_action()
        def chat(_):
            e.stop()
            return {'reply': '我在。'}
        model = Model(route('task', quote='放两块'), place(goal()), route('chat'), chat, place())
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertEqual(self.saved()['goal_status'], 'paused_by_owner')
        self.assertEqual(model.calls, 4)

    def test_reconnect_during_chat_revokes_continuation(self):
        entered = self.hold_first_action()
        def chat(_):
            e.invalidate('body_reconnect')
            return {'reply': '我在。'}
        model = Model(route('task', quote='放两块'), place(goal()), route('chat'), chat, place())
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertEqual(self.saved()['goal_status'], 'interrupted')

    def test_failed_chat_requires_explicit_resume(self):
        entered = self.hold_first_action()
        model = Model(route('task', quote='放两块'), place(goal()), route('chat'), {'reply': '嗨', 'action': {}}, place())
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertEqual(self.saved()['goal_status'], 'interrupted')
        self.assertEqual(self.body.stops, 0)

    def test_new_task_takes_over_without_old_task_overwriting_it(self):
        entered = self.hold_first_action()
        new_goal = goal(1); new_goal['title'] = '改放一块'
        model = Model(route('task', quote='放两块'), place(goal()), route('task', quote='改放一块'), place(new_goal))
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'new', '改放一块'); self.release.set()
        for t in self.threads: t.join(4)
        self.assertEqual(self.saved()['title'], '改放一块')
        self.assertEqual(self.saved()['goal_status'], 'completed')
        self.assertEqual(len(self.body.blocks), 2)
        self.assertEqual(model.calls, 4)

    def test_chat_does_not_reset_decision_limit(self):
        entered = self.hold_first_action()
        model = Model(route('task', quote='放三块'), place(goal(3)), route('chat'), {'reply': '嗨。'}, place(), place())
        e = Harness(self.path, model, self.body, self.audit, max_decisions=2)
        original, _ = self.start(e, 'task', '放三块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.blocks), 2)
        self.assertEqual(self.saved()['work']['last_problem'], 'task_decision_cap')
        self.assertEqual(model.calls, 5)

    def test_chat_time_counts_toward_original_deadline(self):
        entered = self.hold_first_action()
        now = [100.0]
        def chat(_):
            now[0] = 116.0
            return {'reply': '嗨。'}
        model = Model(route('task', quote='放两块'), place(goal()), route('chat'), chat, place())
        e = Harness(self.path, model, self.body, self.audit, max_seconds=15)
        # A task-specific clock avoids changing thread/test timeout clocks.
        with patch('companion.harness.time', type('Clock', (), {'monotonic': lambda: now[0]})):
            original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
            self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertEqual(self.saved()['work']['last_problem'], 'task_deadline')

    def test_input_arriving_during_decision_discards_that_action(self):
        entered = threading.Event()
        def delayed(_):
            entered.set(); self.release.wait(4)
            return place(goal(1))
        model = Model(route('task', quote='放一块'), delayed, route('chat'), {'reply': '嗨。'}, place(goal(1)))
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放一块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(model.calls, 5)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertEqual(model.contexts[-1]['remaining_decisions'], 63)
        self.assertTrue(any(r.get('event') == 'decision_deferred_for_input' for _, r in self.audit.rows))

    def test_cached_display_and_chat_return_before_resumed_task_finishes(self):
        entered = self.hold_first_action()
        resumed, finish = threading.Event(), threading.Event()
        def later(_):
            resumed.set(); finish.wait(4)
            return place()
        model = Model(route('task', quote='放两块'), place(goal()), route('chat'), {'reply': '嗨。'}, later)
        e = Harness(self.path, model, self.body, self.audit)
        server = KernelServer(e, self.audit, port=0)
        try:
            original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
            chat, replies = self.queue(e, 'chat', '嗨'); self.release.set()
            self.assertTrue(resumed.wait(2)); chat.join(1)
            self.assertEqual(replies, ['嗨。']); self.assertTrue(original.is_alive())
            rendered = []
            def display():
                mirror = server.mirror('chat', '嗨')
                rendered.append(server.respond({'model': 'ego-companion', 'messages': [{'role': 'user', 'content': mirror}]}, lambda _: None))
            viewer = threading.Thread(target=display, daemon=True); self.threads.append(viewer); viewer.start(); viewer.join(1)
            self.assertEqual(rendered, ['嗨。'])
            self.assertEqual(model.calls, 5)
        finally:
            finish.set(); server.close()

    def test_repeated_failure_guard_survives_chat(self):
        entered = self.hold_first_action(); self.body.always_fail = True
        craft = {'name': 'craft', 'args': {'item': 'oak_planks', 'count': 1}}
        model = Model(route('task', quote='放两块'), decision(goal=goal(), action=craft),
                      route('chat'), {'reply': '嗨。'}, decision(action=craft), decision(action=craft))
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'chat', '嗨'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.actions), 1)
        self.assertEqual(self.saved()['goal_status'], 'blocked')
        self.assertEqual(model.contexts[-1]['harness_notice']['attempts_without_success'], 2)

    def test_memory_request_revokes_suspended_turn(self):
        entered = self.hold_first_action()
        model = Model(route('task', quote='放两块'), place(goal()), route('memory', quote='记住蓝灯'),
                      decision(convention={'trigger': '蓝灯', 'meaning': '走到我身边', 'replaces': None}),
                      decision(status='chat', reply='记住了。'))
        e = Harness(self.path, model, self.body, self.audit)
        original, _ = self.start(e, 'task', '放两块'); self.assertTrue(entered.wait(2))
        self.queue(e, 'memory', '记住蓝灯代表走到我身边'); self.release.set(); original.join(4)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertEqual(self.saved()['goal_status'], 'interrupted')

    def test_restart_or_inactive_goal_cannot_be_woken_by_chat(self):
        for status in ('yielded', 'blocked', 'paused_by_owner', 'paused_limit', 'interrupted', 'completed'):
            with self.subTest(status=status):
                m = Memory(self.path)
                source, _ = m.begin('seed-' + status, 'verification', '放两块')
                w = create_work(goal(), self.body.snapshot(), source); w['status'] = status
                save_work(m, w, [source]); m.finish('seed-' + status, '保留', [source]); m.close()
                model = Model(route('chat'), {'reply': '我在。'})
                e = Harness(self.path, model, self.body, self.audit)
                before = self.saved()
                e.run('chat-' + status, 'airi', '嗨')
                self.assertEqual(self.saved(), before)
                self.assertEqual(before['goal_status'], 'interrupted' if status == 'yielded' else status)
                self.assertEqual(self.body.actions, [])

    def test_forget_during_yield_does_not_restore_deleted_task_text(self):
        m = Memory(self.path)
        source = m.library.utterance('蓝灯代表 PRIVATE_TARGET_927。', session_id='teach')
        card = m.propose({'trigger': '蓝灯', 'meaning': 'PRIVATE_TARGET_927', 'replaces': None}, source)
        m.close()
        entered = self.hold_first_action()
        private_goal = goal(); private_goal['title'] = 'PRIVATE_TARGET_927'
        model = Model(route('task', quote='蓝灯'), place(private_goal), route('memory', quote='忘掉蓝灯'),
                      decision(forget_card=card))
        e = Harness(self.path, model, self.body, self.audit)
        original, replies = self.start(e, 'task', '蓝灯'); self.assertTrue(entered.wait(2))
        self.queue(e, 'forget', '忘掉蓝灯'); self.release.set()
        for t in self.threads: t.join(4)
        self.assertEqual(len(self.body.blocks), 1)
        self.assertIsNone(self.saved())
        self.assertNotIn('PRIVATE_TARGET_927', replies[0])
        self.assertNotIn(b'PRIVATE_TARGET_927', self.path.read_bytes())

    def test_resume_takes_over_same_task_and_can_itself_yield(self):
        first = self.hold_first_action()
        second, finish_second = threading.Event(), threading.Event()
        underlying = self.body.start_action
        def twice(action, **kw):
            result = underlying(action, **kw)
            if len(self.body.actions) == 2:
                return delayed_result(result, second, finish_second)
            return result
        self.body.start_action = twice
        model = Model(route('task', quote='放三块'), place(goal(3)), route('resume', quote='继续'), place(),
                      route('chat'), {'reply': '嗨。'}, place())
        e = Harness(self.path, model, self.body, self.audit)
        try:
            original, _ = self.start(e, 'task', '放三块'); self.assertTrue(first.wait(2))
            task_id = self.saved()['work']['task_id']
            self.queue(e, 'resume', '继续'); self.release.set(); self.assertTrue(second.wait(2))
            self.queue(e, 'chat', '嗨'); finish_second.set()
            for t in self.threads: t.join(4)
            self.assertEqual(self.saved()['goal_status'], 'completed')
            self.assertEqual(self.saved()['work']['task_id'], task_id)
            self.assertEqual(len(self.body.blocks), 3)
            self.assertEqual(model.calls, 7)
        finally:
            finish_second.set()


if __name__ == '__main__':
    unittest.main(verbosity=2)
