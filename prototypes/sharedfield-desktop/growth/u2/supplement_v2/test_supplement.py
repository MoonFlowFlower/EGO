import copy
import json
import unittest
from u2.run import screen_packet
from .check import candidates, check


class SupplementTests(unittest.TestCase):
    def test_new_counts_and_all_case_checks(self):
        self.assertTrue(check(candidates())['passed'])

    def test_missing_specific_unknown_is_rejected_before_any_call(self):
        items=candidates()
        for item in items:
            if item['category']=='Q' and item['should_ask']:
                messages,_,_=screen_packet(item,'ceiling')
                actual=json.loads(messages[1]['content'])['situations'][0]['memory']
                self.assertEqual(actual,item['ceiling_question'])
        changed=copy.deepcopy(items)
        item=next(i for i in changed if i['category']=='Q' and i['should_ask'])
        item['ceiling_question']='你还不知道这件个人条件，后续安排会用得上。'
        result=check(changed)
        self.assertFalse(result['passed'])
        self.assertIn((item['id'],'ceiling_missing_specific_unknown'),result['format_errors'])


if __name__=='__main__':unittest.main()
