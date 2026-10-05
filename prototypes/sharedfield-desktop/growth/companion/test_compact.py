import copy
import json
import random
import unittest
from .compact import regions,project,compact_context
from .model import request_payload
from .work import validate_goal
from .harness import PROMPT
from p7.proxy import prepare_request


def expand(rs):
    return [(x,y,z,r.get('block')) for r in rs
        for x in range(r['min']['x'],r['max']['x']+1)
        for y in range(r['min']['y'],r['max']['y']+1)
        for z in range(r['min']['z'],r['max']['z']+1)]


class CompactTests(unittest.TestCase):
    def test_readability_counts_do_not_confuse_query_success_with_known_cells(self):
        unknown=project({'verified':True,'cells':[[x,70,0,None] for x in range(3)]})
        self.assertEqual(unknown['observation_counts'],{'known':0,'unknown':3,'by_block':{}})
        mixed=project({'cells':[[0,70,0,'air'],[1,70,0,'stone'],[2,70,0,None]]})
        self.assertEqual(mixed['observation_counts'],{'known':2,'unknown':1,'by_block':{'air':1,'stone':1}})

    def test_sparse_unknown_air_solid_roundtrip_does_not_fill_holes(self):
        random.seed(41)
        cells=[[x,y,z,random.choice(['stone','air',None])] for x in range(-3,5) for y in range(4) for z in range(3) if random.random()>.2]
        restored=expand(regions(cells));self.assertEqual(len(restored),len(cells));self.assertEqual(set(restored),set(map(tuple,cells)))

    def test_criterion_keeps_exact_coordinates_and_contract(self):
        g={'title':'保留形状和空位','steps':['观察','构造','核对'],'done_when':[
            {'kind':'blocks','block':b,'positions':[{'x':x,'y':y,'z':z} for x in range(8) for z in range(8)]}
            for b,y in [('oak_planks',70),('air',71)]]}
        restored=validate_goal(project(g))
        for a,b in zip(g['done_when'],restored['done_when']):
            self.assertEqual(a['block'],b['block']);self.assertEqual({tuple(sorted(p.items())) for p in a['positions']},{tuple(sorted(p.items())) for p in b['positions']})

    def test_failed_world_readback_retains_every_unknown_and_mismatch(self):
        targets=[{'block':'oak_planks','position':{'x':i,'y':70,'z':0},'observed_block':b,'matches':b=='oak_planks'}
                 for i,b in enumerate(['oak_planks','air',None,'stone'])]
        compressed=project({'status':'goal_blocks_checked','verified':False,'blocks':targets})
        restored=[{'block':c['expected'],'position':{'x':x,'y':y,'z':z},'observed_block':c['observed'],'matches':c['matches']}
            for c in compressed['block_checks'] for x,y,z,_ in expand(c['regions'])]
        self.assertFalse(compressed['verified']);self.assertEqual(sorted(restored,key=lambda b:b['position']['x']),targets)

    def test_aliases_only_replace_exact_equal_state_and_preserve_input(self):
        ctx={'body':{'inventory':{}},'work':{'task_id':'t'},'execution_feedback':{'current_body':{'inventory':{'oak_log':1}},'work':{'task_id':'t'}}}
        original=copy.deepcopy(ctx);wire=compact_context(ctx)
        self.assertEqual(ctx,original);self.assertIn('current_body',wire['execution_feedback']);self.assertEqual(wire['execution_feedback']['work_ref'],'context.work')

    def test_full_128_target_feedback_fits_existing_transport_boundary(self):
        conditions=[{'kind':'blocks','block':b,'positions':[{'x':x,'y':y,'z':z} for x in range(8) for z in range(8)]}
            for b,y in [('oak_planks',70),('air',71)]]
        g={'title':'完整空间契约','steps':['观察','执行','核对'],'done_when':conditions}
        w={**g,'task_id':'t','request':{'user':'完成约定布局'},'placed':[]}
        receipt={'verified':False,'status':'goal_blocks_checked','blocks':[
            {'block':c['block'],'position':p,'observed_block':'air','matches':c['block']=='air'} for c in conditions for p in c['positions']]}
        ctx={'current':{'user':'完成约定布局'},'original_request':w['request'],'work':w,'goal':{'work':w,'record_id':'g'},
            'body':{'offline':False},'receipts':[receipt]*6,'remaining_decisions':30,
            'execution_feedback':{'work':w,'current_body':{'offline':False},'previous_decision':{'goal':g},'receipts':[receipt]*6}}
        self.assertGreater(len(json.dumps(ctx).encode()),60000)
        payload=request_payload('deepseek/deepseek-v4.1-flash',PROMPT,ctx)
        _,raw,_=prepare_request(payload,model=payload['model'])
        self.assertLess(len(raw),60000);self.assertIn('"matches":false',payload['messages'][-1]['content'])


if __name__=='__main__':unittest.main()
