import copy
import tempfile
import unittest
from pathlib import Path
from .harness import Harness
from .test_harness import Model, Body, decision, goal
from .test_kernel import Audit
from .work import validate_action, validate_goal, create_work, incorporate
from .voxel_scene import VoxelScene, grade_hut
from .model import request_messages
from .memory import Memory


def pos(x,y=64,z=0):return dict(x=x,y=y,z=z)
def spatial(conditions):return dict(title='按坐标构造并保留空间',steps=['观察','构造','核对'],done_when=conditions)


class CapabilityTests(unittest.TestCase):
    def test_tool_result_follows_previous_decision_instead_of_reissuing_request(self):
        prior=decision(action=dict(name='inspect',args={}))
        context={'current':{'user':'先看再搭'},'execution_feedback':{'previous_decision':prior,'receipts':[{'status':'observed'}]}}
        messages=request_messages('instruction',context)
        self.assertEqual(messages[-2]['role'],'assistant');self.assertIn('"inspect"',messages[-2]['content'])
        self.assertIn('observed',messages[-1]['content']);self.assertEqual(messages[-3]['content'],'先看再搭')

    def test_invalid_decision_is_repairable_and_cannot_execute(self):
        with tempfile.TemporaryDirectory() as folder:
            body=Body();path=Path(folder)/'state.sqlite'
            model=Model({'goal':{'action':{'name':'place','args':{'block':'oak_planks'}}}},
                decision(goal=goal(1),action=dict(name='place',args=dict(block='oak_planks'))))
            h=Harness(path,model,body,Audit(),input_router=lambda *args:dict(mode='task',task_kind='ordinary'))
            h.run('schema','verification','放一块')
            self.assertEqual(len(body.blocks),1);self.assertEqual(model.calls,2)
            self.assertEqual(model.contexts[1]['execution_feedback']['harness_notice']['code'],'harness_decision_schema')

    def test_invalid_decision_repair_is_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            body=Body();model=Model({}, {}, {}, decision(goal=goal(1)))
            h=Harness(Path(folder)/'state.sqlite',model,body,Audit(),input_router=lambda *args:dict(mode='task',task_kind='ordinary'))
            h.run('schema','verification','放一块');self.assertEqual(model.calls,3);self.assertFalse(body.actions)

    def test_dialogue_roles_and_adjacency_survive_state_serialization(self):
        context={'current_user':'对','situation':{'pending_work':{'title':'挖矿','status':'blocked'},'dialogue':[
            {'record_id':'u1','role':'user','text':'雨后挺安静'},
            {'record_id':'a1','role':'assistant','text':'是挺安静的。'},
            {'record_id':'u2','role':'user','text':'对'}]}}
        original=copy.deepcopy(context);messages=request_messages('instruction',context)
        self.assertEqual(messages[-2:], [{'role':'assistant','content':'是挺安静的。'},{'role':'user','content':'对'}])
        self.assertEqual(sum(m['content']=='对' for m in messages),1)
        self.assertNotIn('"dialogue"',messages[1]['content']);self.assertEqual(context,original)

    def test_observation_does_not_commit_placeholder_goal(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.sqlite';body=Body()
            placeholder=spatial([dict(kind='blocks',block='oak_planks',positions=[pos(0,0,0)])])
            model=Model(decision(goal=placeholder,action=dict(name='inspect',args={})),decision(status='waiting_user',reply='确认一下施工位置。'))
            h=Harness(path,model,body,Audit(),input_router=lambda *args:dict(mode='task',task_kind='structure'))
            h.run('plan','verification','先看场地')
            self.assertEqual([a['name'] for a in body.actions],['inspect']);self.assertIsNone(model.contexts[1]['work'])
            m=Memory(path)
            try:self.assertIsNone(m.goal())
            finally:m.close()

    def test_geometry_grader_rejects_missing_roof_wall_and_blocked_interior(self):
        scene=VoxelScene(origin=(0,64,0))
        for x in range(5):
            for z in range(5):
                scene.blocks[(x,66,z)]='oak_planks'
                if x in (0,4) or z in (0,4):
                    if (x,z)!=(2,0):
                        for y in (64,65):scene.blocks[(x,y,z)]='oak_planks'
        scene.changes=[dict(block=b,position=dict(zip(('x','y','z'),p))) for p,b in scene.blocks.items()]
        scene.state['inventory']['oak_planks']-=len(scene.changes)
        self.assertTrue(grade_hut(scene)['passed'])
        for missing,flag in [((2,66,2),'roof'),((0,64,2),'walls')]:
            block=scene.blocks.pop(missing)
            self.assertFalse(grade_hut(scene)[flag]);scene.blocks[missing]=block
        scene.blocks[(2,64,2)]='stone';self.assertFalse(grade_hut(scene)['interior_clear'])

    def test_regions_expand_union_without_changing_input(self):
        g=spatial([dict(kind='blocks',block='oak_planks',regions=[dict(min=pos(0),max=pos(2)),dict(min=pos(2),max=pos(3))])])
        original=copy.deepcopy(g);checked=validate_goal(g)
        self.assertEqual(g,original);self.assertEqual(checked['done_when'][0]['positions'],[pos(n) for n in range(4)])

    def test_regions_and_world_bounds(self):
        for a,b in [(pos(3),pos(2)),(pos(0),pos(64)),(pos(0,320),pos(0,320))]:
            with self.assertRaises(ValueError):validate_goal(spatial([dict(kind='blocks',block='stone',regions=[dict(min=a,max=b)])]))
        conditions=[dict(kind='blocks',block='stone',regions=[dict(min=pos(n*64),max=pos(n*64+63))]) for n in range(3)]
        self.assertEqual(len(validate_goal(spatial(conditions[:2]))['done_when']),2)
        with self.assertRaisesRegex(ValueError,'goal_world_check_limit'):validate_goal(spatial(conditions))

    def test_conflicting_solid_and_air_is_not_a_completable_contract(self):
        with self.assertRaisesRegex(ValueError,'goal_conflicting_blocks'):
            validate_goal(spatial([dict(kind='blocks',block=block,positions=[pos(1)]) for block in ('stone','air')]))

    def test_batch_bounds_and_partial_effects(self):
        targets=[dict(block='oak_planks',position=pos(n)) for n in range(8)]
        action=dict(name='place_many',args=dict(targets=targets));validate_action(action)
        for bad in [[],targets+[targets[0]],targets[:1]*2,[dict(block='air',position=pos(1))]]:
            with self.assertRaises(ValueError):validate_action(dict(name='place_many',args=dict(targets=bad)))
        w=create_work(goal(8),Body().snapshot(),'source')
        receipt=dict(verified=False,placements=[dict(target=targets[0],receipt=dict(verified=True,position=pos(0),placement=dict(consumed=1))),
            dict(target=targets[1],receipt=dict(verified=False,position=pos(1)))])
        incorporate(w,action,receipt);incorporate(w,action,receipt)
        self.assertEqual(w['placed'],targets[:1])

    def test_observation_can_precede_goal_but_mutation_cannot(self):
        with tempfile.TemporaryDirectory() as folder:
            body=Body();model=Model(decision(action=dict(name='inspect',args={})),
                decision(action=dict(name='place',args=dict(block='oak_planks'))),
                decision(action=dict(name='place',args=dict(block='oak_planks'))))
            h=Harness(Path(folder)/'state.sqlite',model,body,Audit(),input_router=lambda *args:dict(mode='task',task_kind='ordinary'))
            h.run('preplan','verification','看看现场再规划')
            self.assertEqual([a['name'] for a in body.actions],['inspect']);self.assertFalse(body.blocks)

    def test_invalid_coordinate_contract_returns_diagnostic_for_repair(self):
        with tempfile.TemporaryDirectory() as folder:
            body=Body();bad=spatial([dict(kind='blocks',block=block,positions=[pos(1)]) for block in ('stone','air')])
            model=Model(decision(goal=bad),decision(status='waiting_user',reply='这个位置已有障碍，请指定另外一处。'))
            h=Harness(Path(folder)/'state.sqlite',model,body,Audit(),input_router=lambda *args:dict(mode='task',task_kind='ordinary'))
            h.run('repair','verification','搭个东西')
            self.assertEqual(model.contexts[1]['harness_notice']['code'],'goal_conflicting_blocks');self.assertFalse(body.actions)


if __name__=='__main__':unittest.main()
