import copy
import unittest
from .model import request_messages
from .interaction import action_problem, goal_problem


class RepresentationTests(unittest.TestCase):
    def test_latest_utterance_remains_an_actual_message_after_evidence(self):
        for context in ({'current_user':'现在呢？','goal':{'title':'旧任务'}},
                        {'current':{'user':'这边','body_at_input':{'position':{'x':2}}},'body':{'position':{'x':3}}}):
            original=copy.deepcopy(context)
            messages=request_messages('schema instructions',context)
            self.assertEqual(messages[-1]['content'],context.get('current_user') or context['current']['user'])
            self.assertEqual(messages[-1]['role'],'user')
            self.assertEqual(messages[0],{'role':'system','content':'schema instructions'})
            self.assertEqual(context,original)
            self.assertEqual(len(messages),3)

    def test_composition_is_not_rejected_by_first_primitive_label(self):
        composite={'task_kind':'approach','done_when':[{'kind':'near_owner'}, {'kind':'picked_up','item':'wood','count':8}]}
        self.assertIsNone(goal_problem('approach',composite))
        self.assertIsNone(goal_problem('pickup',composite))
        self.assertIsNone(action_problem(composite,{'name':'approach','args':{}},{}))
        self.assertEqual(action_problem(composite,{'name':'collect','args':{'block':'oak_log','count':8}},{}),
                         'action_outside_current_request')
        placement={'task_kind':'approach','done_when':[{'kind':'near_owner'},{'kind':'placed','block':'oak_planks','count':1}]}
        self.assertIsNone(action_problem(placement,{'name':'place','args':{'block':'oak_planks'}},{}))
        self.assertEqual(goal_problem('pickup',{'done_when':[{'kind':'gained','item':'oak_log','count':8}]}),
                         'task_requires_picked_up_criterion')


if __name__=='__main__':unittest.main()
