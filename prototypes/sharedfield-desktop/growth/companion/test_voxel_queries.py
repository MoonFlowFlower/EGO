import unittest
from .engine import completed_negative_search
from .verify_blocked_v12 import ConsistentSealedScene, search_view
from .voxel_scene import VoxelScene, xyz


class QueryTests(unittest.TestCase):
    def test_procedural_air_and_bedrock_search_agree_with_observation(self):
        scene=ConsistentSealedScene()
        for name in ('air','bedrock'):
            r=scene.start_action({'name':'search','args':{'block':name,'range':8}}).result()
            self.assertTrue(r['verified']);self.assertEqual(r['status'],'block_located')
            self.assertEqual(scene.block(xyz(r['block_position'])),name)
            self.assertEqual(r['query']['scope'],'loaded_chunks_only')
        self.assertEqual(search_view(scene,'air',8)['distance'],0)
        self.assertFalse(scene.changes)

    def test_complete_negative_is_bounded_and_uses_production_protocol(self):
        scene=ConsistentSealedScene();action={'name':'search','args':{'block':'wood','range':32}}
        r=scene.start_action(action).result()
        self.assertTrue(completed_negative_search(action,r));self.assertFalse(r['verified'])
        self.assertEqual(r['query']['range'],32);self.assertEqual(len(r['query']['block_types']),8)
        self.assertIsNone(r['block_position'])

    def test_search_sees_virtual_floor_and_excludes_unloaded_cells(self):
        scene=VoxelScene();r=search_view(scene,'stone',8)
        self.assertEqual(r['distance'],1);self.assertEqual(scene.block(xyz(r['block_position'])),'stone')
        scene.blocks[(scene.origin[0]+30,scene.origin[1],scene.origin[2])]='oak_log'
        self.assertFalse(search_view(scene,'wood',32)['found'])
        scene.loaded=False;self.assertFalse(search_view(scene,'stone',8)['found'])


if __name__=='__main__':unittest.main()
