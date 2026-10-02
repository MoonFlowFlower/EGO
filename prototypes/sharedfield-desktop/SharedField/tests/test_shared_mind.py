import unittest
from copy import deepcopy
from switchlab.shared.world import World
try:
    from switchlab.shared.mind import Mind
except ImportError:Mind=None

class SharedMindTests(unittest.TestCase):
    def make(self):
        self.assertIsNotNone(Mind,'appraisal / planning kernel not implemented')
        w=World();m=Mind();m.refresh(w.observe('agent'));return w,m
    def test_plan_requires_only_public_observation(self):
        w,m=self.make();p=m.plan()
        self.assertIn(p['action']['kind'],('survey','move','scan','rest','calibrate','sleep'))
        self.assertIn('prediction',p);self.assertIn('goal',p)
    def test_report_is_read_only_and_exists_before_question(self):
        w,m=self.make();m.plan();s=m.snapshot();a=m.report();b=m.report()
        self.assertEqual(a,b);self.assertEqual(s,m.snapshot())
        self.assertIn('focus',a);self.assertIn('affect',a)
    def test_unique_observation_updates_map_interest_once(self):
        w,m=self.make();e=w.act('agent',{'kind':'survey'});m.observe(e,'E1')
        n=m.snapshot()['learned_events'];s=m.snapshot();m.observe(e,'E1')
        self.assertEqual(s,m.snapshot());self.assertEqual(n,1)
    def test_learning_freeze_does_not_hide_current_observation(self):
        w,m=self.make();m.mode='learning_frozen';prior=deepcopy(m.interests)
        e=w.act('agent',{'kind':'survey'});m.observe(e,'E1')
        self.assertEqual(prior,m.interests);self.assertTrue(m.current['surveyed'])
    def test_failure_changes_appraisal_not_just_caption(self):
        w,m=self.make();m.plan();e=w.act('agent',{'kind':'move','target':1})
        e['success']=False;e['after']['position']=0;e['agent_observation']['position']=0
        m.observe(e,'E1')
        self.assertGreater(m.affect()['frustration'],0)
        self.assertGreater(m.report()['attention']['prediction_error'],0)
    def test_capability_is_learned_from_calibration_not_user_belief(self):
        w,m=self.make();before=m.capability()
        for i in range(12):
            e=w.act('agent',{'kind':'calibrate'});e['success']=False
            m.observe(e,'E'+str(i))
        self.assertLess(m.capability(),before-.3)
    def test_self_ablation_changes_success_forecast(self):
        w,m=self.make();m.self_stats={'a':1.,'b':15.,'n':15}
        action={'kind':'move','target':1};a=m.predict(action)['success']
        m.mode='self_off';b=m.predict(action)['success'];self.assertLess(a,b)
    def test_affect_ablation_changes_risk_coefficients(self):
        w,m=self.make();m.appraisals.append({'source':'test','delta':{'valence':-.4,'arousal':.8,'frustration':.9},'why':'controlled intervention'})
        a=m.coefficients();m.mode='affect_off';b=m.coefficients()
        self.assertGreater(a['risk'],b['risk']);self.assertNotEqual(a,b)
    def test_replay_not_new_evidence_and_counts_are_stable(self):
        w,m=self.make();m.observe(w.act('agent',{'kind':'survey'}),'E1')
        before=m.learned_events;stats=deepcopy(m.interests);m.replay()
        self.assertEqual(before,m.learned_events);self.assertEqual(stats,m.interests)
    def test_new_expedition_keeps_knowledge_not_old_room_map(self):
        w,m=self.make();m.observe(w.act('agent',{'kind':'survey'}),'E1');stats=deepcopy(m.interests)
        m.new_expedition(World(seed=43).observe('agent'))
        self.assertEqual(stats,m.interests);self.assertEqual(m.surveyed,[])
    def test_exhaustion_proposes_rest_and_no_more_info_can_sleep(self):
        w,m=self.make();w.stamina['agent']=.01;m.refresh(w.observe('agent'))
        self.assertEqual(m.plan()['action']['kind'],'rest')
        w.stamina['agent']=1.;w.discovered=set(range(12));w.visible=set(range(12));m.refresh(w.observe('agent'))
        self.assertEqual(m.plan()['action']['kind'],'sleep')
    def test_other_person_preference_does_not_become_users_preference(self):
        w,m=self.make();baseline=m.candidates()
        k=m.current['room']['kind']
        m.add_report({'domain':'interest','holder':'other:路人','value':k,'confidence':.9,'kind':'explicit','quote':'路人喜欢这个'},'E1')
        self.assertEqual(baseline,m.candidates())
