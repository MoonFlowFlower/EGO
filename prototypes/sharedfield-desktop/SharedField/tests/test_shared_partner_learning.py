"""Toy intervention, not a real user's preference or a social-emotion benchmark."""
import unittest
from copy import deepcopy
from switchlab.shared.mind import Mind
from switchlab.shared.world import World
from switchlab.shared import continuity


def trained_mind(target, freeze=False):
    # Both actions are available on each trial. Context identifiers change so
    # retries of one route are never credited as independent choices.
    m=Mind();m.mode='learning_frozen' if freeze else 'full'
    base=World().act('user',{'kind':'move','target':1})
    base['before']['neighbors']=[{'id':1,'kind':'flora'},{'id':4,'kind':'ruins'}]
    base['action']['target']=target
    for episode in range(1,61):
        m.expedition=episode
        continuity.observe(m,deepcopy(base),'TRAIN'+str(episode))
    # Same public evaluation world and own physical experience in both arms.
    w=World();w.discovered.add(0)
    m.refresh(w.observe());m.known['1']['kind']='flora';m.known['4']['kind']='ruins'
    m.partner.update(position=0,stamina=1.,failure_streak=0,last_source=None,last_action=None)
    m.set_activity('together','TEST_CONSENT')
    return m

class PartnerLearningTests(unittest.TestCase):
    def test_different_choice_histories_change_same_available_destination(self):
        left=trained_mind(1);right=trained_mind(4)
        self.assertEqual(left.current,right.current)
        self.assertEqual(left.interests,right.interests)
        self.assertEqual(left.candidates()[0]['action']['target'],1)
        self.assertEqual(right.candidates()[0]['action']['target'],4)
    def test_freezing_learning_destroys_this_difference(self):
        a=trained_mind(1,True);b=trained_mind(4,True)
        self.assertEqual(a.partner_model['updates'],0)
        self.assertEqual(a.candidates()[0]['action'],b.candidates()[0]['action'])
    def test_explicit_independence_disables_partner_ranking_path(self):
        a=trained_mind(1);b=trained_mind(4)
        a.set_activity('independent','TEST_CANCEL');b.set_activity('independent','TEST_CANCEL')
        self.assertEqual(a.candidates()[0]['action'],b.candidates()[0]['action'])
