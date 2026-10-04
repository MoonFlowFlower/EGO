import tempfile
import unittest
from pathlib import Path

from .context import conversation_context
from .memory import Memory
from .test_harness import Body
from .verification_body import SceneBody


class ContextAndSceneTests(unittest.TestCase):
    def test_evidence_projection_follows_need_independently_of_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            m = Memory(Path(tmp) / 'state.sqlite')
            try:
                for identity, text, mode in [('build', '建房用橡木板', 'task'), ('social', '我喜欢猫', 'chat')]:
                    source, _ = m.begin(identity, 'airi', text)
                    m.append('reflection', {'type': 'input_route', 'event_id': identity, 'route': {'mode': mode}}, [source])
                    m.finish(identity, '之前生成的身体断言', [source])
                need = {'question':'刚才的社交话题', 'sources':['chat_history'], 'memory_queries':[]}
                context = conversation_context(m, '嗨', 'chat', Body().snapshot(), information_need=need)
                for key in ('current_body', 'goal', 'dialogue', 'user_history', 'historical_actions'):
                    self.assertNotIn(key, context)
                self.assertNotIn('memory_candidates', context)
                self.assertNotIn('action', context)
                self.assertEqual([r['text'] for r in context['chat_history']], ['我喜欢猫'])
                self.assertIn('之前生成', m.cached('build'))
                need = {'question':'当前材料', 'sources':['current_body','user_history'], 'memory_queries':[]}
                status = conversation_context(m, '材料够吗', 'status', Body().snapshot(), information_need=need)
                self.assertIn('current_body', status)
                self.assertEqual(len(status['user_history']), 2)
                social = conversation_context(m, '看看现在的材料', 'chat', Body().snapshot(), information_need=need)
                self.assertEqual(social['current_body']['state'], status['current_body']['state'])
                self.assertNotIn('goal', social)
                empty = conversation_context(m, '嗯', 'status', Body().snapshot(),
                    information_need={'question':'确认收到', 'sources':[], 'memory_queries':[]})
                self.assertNotIn('current_body', empty)
            finally:
                m.close()

    def test_area_placement_and_readback_share_actual_scene(self):
        body = SceneBody()
        area = body.start_action({'name': 'inspect_area', 'args': {'radius': 2}}).result()
        self.assertEqual(area['status'], 'local_area_observed')
        self.assertEqual(area['center'], {'x': 0, 'y': 64, 'z': 0})
        self.assertEqual(len(area['cells']), 100)
        self.assertIn([1, 63, 0, 'stone'], area['cells'])
        self.assertIn([1, 64, 0, 'air'], area['cells'])
        p = {'z': 0, 'y': 64, 'x': 1}
        placed = body.start_action({'name': 'place_at', 'args': {'block': 'oak_planks', 'position': p}})
        self.assertTrue(body.first_placement.is_set()); self.assertFalse(placed.done())
        self.assertEqual(body.block(p), 'oak_planks'); body.release()
        self.assertTrue(placed.result()['verified'])
        proof = body.start_action({'name': 'verify_blocks', 'args': {'targets': [{'block': 'oak_planks', 'position': p}]}}).result()
        self.assertTrue(proof['verified'])
        body.blocks.clear()
        proof = body.start_action({'name': 'verify_blocks', 'args': {'targets': [{'block': 'oak_planks', 'position': p}]}}).result()
        self.assertFalse(proof['verified'])

    def test_occupied_unsupported_or_missing_material_is_not_success(self):
        body = SceneBody()
        for position in ({'x': 1, 'y': 63, 'z': 0}, {'x': 1, 'y': 66, 'z': 0}):
            with self.assertRaises(RuntimeError):
                body.start_action({'name': 'place_at', 'args': {'block': 'oak_planks', 'position': position}})
        body.state['inventory']['oak_planks'] = 0
        with self.assertRaises(RuntimeError):
            body.start_action({'name': 'place', 'args': {'block': 'oak_planks'}})


if __name__ == '__main__':
    unittest.main(verbosity=2)
