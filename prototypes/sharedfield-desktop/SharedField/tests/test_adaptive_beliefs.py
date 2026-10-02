import importlib.util
import unittest

class BeliefTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.beliefs'),'grounded beliefs missing')
        from switchlab.studio.beliefs import BeliefGraph
        self.G=BeliefGraph
    def test_exact_source_required_and_no_self_certifying_truth(self):
        g=self.G();s={'E1':'小明认为盒子在左边。'}
        item={'holder':'other:小明','subject':'盒子','relation':'位置','value':'左边','source':'E1','quote':'盒子在左边','confidence':.8}
        g.add([item],s)
        self.assertEqual(g.claims[0]['verification'],'unverified_extraction')
        item['quote']='盒子在右边'
        with self.assertRaises(ValueError):g.add([item],s)
    def test_other_belief_not_world_truth_and_conflicts_not_majority(self):
        g=self.G();s={'E1':'小明认为盒子在左边，实际上我把盒子移到右边了。','E2':'小明还是认为在左边。'}
        def q(h,v,source,quote):return {'holder':h,'subject':'盒子','relation':'位置','value':v,'source':source,'quote':quote,'confidence':.9}
        g.add([q('other:小明','左边','E1','盒子在左边'),q('world','右边','E1','盒子移到右边')],s)
        self.assertEqual(len(g.conflicts()),0)
        g.add([q('world','左边','E2','在左边')],s)
        self.assertEqual(len(g.conflicts()),1)
        g.add([q('world','左边','E2','在左边')],s)
        self.assertEqual(len(g.claims),3)
        self.assertNotIn('true',str(g.claims))
    def test_resolve_records_correction_without_deleting_history(self):
        g=self.G();s={'E1':'偏好红色','E2':'偏好蓝色'}
        for sid,val in [('E1','红色'),('E2','蓝色')]:
            g.add([{'holder':'user','subject':'user','relation':'颜色偏好','value':val,'source':sid,'quote':s[sid],'confidence':.8}],s)
        self.assertEqual(len(g.conflicts()),1)
        g.resolve(g.claims[0]['id'],'withdraw','E3')
        self.assertEqual(len(g.claims),2);self.assertEqual(len(g.conflicts()),0)
        self.assertEqual(g.snapshot(),self.G.restore(g.snapshot()).snapshot())
