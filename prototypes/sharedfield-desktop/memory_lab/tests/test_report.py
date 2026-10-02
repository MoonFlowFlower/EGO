import unittest

class ReportTests(unittest.TestCase):
    def test_three_repeats_are_one_scenario_sample(self):
        from memory_lab.report import paired
        a=[{'case':f'c{i}','repeat':r,'family':1,'success':False} for i in range(4) for r in range(3)]
        b=[dict(row,success=True) for row in a]
        p=paired(a,b)
        self.assertEqual(p['scenario_n'],4)
        self.assertEqual(p['difference'],1)
        self.assertEqual(p['ci95'],[1,1])

    def test_incomplete_pair_is_rejected(self):
        from memory_lab.report import paired
        with self.assertRaises(ValueError):paired([{'case':'x','repeat':1,'family':1,'success':True}],[])

    def test_gate_blocks_selection_despite_high_score(self):
        from memory_lab.report import choose
        summaries={'baseline':{'rate':.8,'gates':0,'cost':1},'hindsight':{'rate':1,'gates':1,'cost':2},'memos':{'rate':.8,'gates':0,'cost':1.2}}
        result=choose(summaries,{'hindsight':{'difference':.2,'ci95':[.1,.3]},'memos':{'difference':0,'ci95':[-.1,.1]}})
        self.assertEqual(result['research_backend'],'baseline')
        self.assertIn('hindsight',result['blocked_by_gates'])
