import copy
import importlib.util
import math
import unittest

from switchlab.studio.neural import TinyNet

class NeuralRegression(unittest.TestCase):
    def test_backward_gradient_matches_numerical_difference(self):
        net=TinyNet(inputs=4,hidden=3,outputs=3,utility_heads=1)
        x=[.2,-.4,.1,.8];y=[1.,.2,-.5];mask=[1.,1.,1.]
        net.train(x,y,mask)
        grads=net.gradients(x,y,mask)
        for name,i,j in [('w1',1,2),('w2',0,1)]:
            w=getattr(net,name);old=w[i][j];eps=1e-5
            w[i][j]=old+eps;plus=net.loss(x,y,mask)
            w[i][j]=old-eps;minus=net.loss(x,y,mask);w[i][j]=old
            self.assertAlmostEqual(grads[name][i][j],(plus-minus)/(2*eps),places=7)
    def test_parameters_really_learn_and_serialize(self):
        net=TinyNet();x=[.2]*80;y=[1.,0.,1.]+[.2]*24;m=[1.]*27
        old=net.weight_digest();loss=net.loss(x,y,m)
        for _ in range(30):net.train(x,y,m)
        self.assertNotEqual(old,net.weight_digest());self.assertLess(net.loss(x,y,m),loss)
        self.assertEqual(net.snapshot(),TinyNet.restore(net.snapshot()).snapshot())
        self.assertEqual(net.parameter_count,2619)
    def test_mask_cannot_train_unobserved_targets(self):
        a=TinyNet();b=TinyNet();x=[.1]*80
        a.train(x,[1.]*27,[0.]*27)
        self.assertEqual(a.weight_digest(),b.weight_digest())
        with self.assertRaises(ValueError):a.predict([math.nan]*80)

class AdaptiveLearningTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('switchlab.studio.learning'), 'online learning implementation is missing')
        from switchlab.studio.learning import OutcomeLearner, features
        self.Learner=OutcomeLearner;self.features=features
    def test_unique_events_frozen_weights_and_replay_not_evidence(self):
        l=self.Learner();x=self.features('question about a plan','compare options',{})
        self.assertEqual(len(x),80)
        before=l.net.weight_digest()
        l.learn('one',x,[1.,1.,0.]+[0.]*24,[1.]*3+[0.]*24)
        self.assertNotEqual(before,l.net.weight_digest());n=l.seen
        with self.assertRaises(ValueError):l.learn('one',x,[1.]*27,[1.]*27)
        l.replay(8);self.assertEqual(l.seen,n)
        before=l.net.weight_digest();l.enabled=False
        l.learn('two',x,[0.]*27,[1.]*27);l.replay(8)
        self.assertEqual(l.net.weight_digest(),before)
    def test_different_histories_reverse_same_candidate_order(self):
        a=self.Learner();b=self.Learner()
        xs=[self.features('choose how to solve this','compare options',{}),self.features('choose how to solve this','act directly',{})]
        for i in range(12):
            for j in range(2):
                a.learn(f'{i}-{j}',xs[j],[float(j==0)]*3+[0.]*24,[1.]*3+[0.]*24)
                b.learn(f'{i}-{j}',xs[j],[float(j==1)]*3+[0.]*24,[1.]*3+[0.]*24)
        self.assertGreater(a.predict(xs[0])['utility'],a.predict(xs[1])['utility'])
        self.assertLess(b.predict(xs[0])['utility'],b.predict(xs[1])['utility'])
    def test_retraction_rebuild_removes_gradient_influence(self):
        l=self.Learner();x=self.features('one','two',{});prior=l.net.weight_digest()
        l.learn('x',x,[1.]*27,[1.]*27);l.replay(4);l.retract('x')
        self.assertEqual(l.net.weight_digest(),prior)
        self.assertEqual(l.active_samples,0)
    def test_freeze_also_freezes_similarity_and_predictor_arbitration(self):
        l=self.Learner();x=self.features('context','act',{})
        for i in range(10):l.learn(str(i),x,[1.]*3+[0.]*24,[1.]*3+[0.]*24)
        l.enabled=False;before=l.predict(x);samples=l.active_samples
        for i in range(10,20):l.learn(str(i),x,[0.]*27,[1.]*27)
        self.assertEqual(before,l.predict(x));self.assertEqual(samples,l.active_samples)

    def test_roundtrip_and_bounded_reservoir(self):
        l=self.Learner(capacity=8)
        for i in range(30):
            l.learn(str(i),self.features(str(i),'act',{}),[0.]*27,[1.]*27)
        self.assertEqual(len(l.samples),8)
        restored=self.Learner.restore(l.snapshot())
        self.assertEqual(restored.snapshot(),l.snapshot())
        x=self.features('new','act',{});self.assertEqual(l.predict(x),restored.predict(x))
    def test_utility_uses_only_confirmed_labels(self):
        l=self.Learner();x=self.features('next message','reply',{})
        for i in range(12):l.learn(str(i),x,[0.]*27,[0.]*3+[1.]*24)
        p=l.predict(x)
        self.assertEqual(p['utility_labels'],0)
        self.assertEqual(p['outcomes'],[.5,.5,.5])
