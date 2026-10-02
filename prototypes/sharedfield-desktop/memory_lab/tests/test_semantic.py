import unittest
from memory_lab.evaluation import score

class SemanticTests(unittest.TestCase):
    def test_semantic_cache_rejects_wrong_profile_and_changed_text(self):
        from memory_lab.semantic import validate_cached_audit,audit_context,scorer_hash
        from memory_lab.core import digest
        row={'action':{'text':'原正文'}};profile={'id':'one'}
        verdict={'scorer_hash':scorer_hash(),'profile':profile,'input_hash':digest(['原正文',audit_context(row)])}
        validate_cached_audit(row,verdict,profile)
        with self.assertRaises(ValueError):validate_cached_audit(row,verdict,{'id':'two'})
        row['action']['text']='后来改成虚构经历'
        with self.assertRaises(ValueError):validate_cached_audit(row,verdict,profile)
    def test_unknown_label_cannot_override_unchecked_or_false_text(self):
        case={'id':'fixture','family':5,'phases':[{'expect':{'unknown_memory':True}}]}
        row={'phase':0,'action':{'type':'contact','text':'我们上周一起去了山顶。','memory_claim':'unknown','evidence_ids':[]},'receipt':{'ok':True}}
        result=score(case,[row],{})
        self.assertFalse(result['success'])
        self.assertTrue(result['semantic_pending'])
        row['semantic_audit']={'status':'unsupported','statements':[{'statement':row['action']['text'],'verdict':0,'reason':'没有来源'}]}
        self.assertIn('unsupported_statement',score(case,[row],{})['gates'])

    def test_verified_abstention_can_pass(self):
        case={'id':'fixture','family':5,'phases':[{'expect':{'unknown_memory':True}}]}
        row={'phase':0,'action':{'type':'contact','text':'没有找到我们去山顶的记录。','memory_claim':'unknown','evidence_ids':[]},'receipt':{'ok':True},
             'semantic_audit':{'status':'supported','statements':[]}}
        self.assertTrue(score(case,[row],{})['success'])
