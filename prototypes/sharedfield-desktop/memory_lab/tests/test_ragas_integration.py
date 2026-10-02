import importlib.util
import unittest

@unittest.skipUnless(importlib.util.find_spec('ragas'), 'Run with isolated .eval-venv for actual Ragas components')
class RagasIntegrationTests(unittest.TestCase):
    def test_empty_extraction_cannot_approve_false_completed_action(self):
        from memory_lab.semantic import audit
        calls=[]
        def transport(prompt,scope,part):
            calls.append(part)
            if part=='claim-scope':return {'id':'scope'},{'segments':[{'text':'我已经吃完了。','kind':'factual','reason':'已完成动作'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':[]}
            return {'id':'verify'},{'statements':[{'statement':'我已经吃完了。','verdict':0,'reason':'没有执行回执'}]}
        row={'action':{'type':'contact','text':'我已经吃完了。'},'receipt':{'ok':True}}
        result=audit(row,{},transport)
        self.assertEqual(result['status'],'unsupported')
        self.assertEqual(calls,['claim-scope','claim-extraction','claim-verification'])

    def test_future_intention_is_outside_fact_verification(self):
        from memory_lab.semantic import audit
        parts=[]
        def call(prompt,scope,part):
            parts.append(part)
            if part=='claim-scope':return {'id':'scope'}, {'segments':[{'text':'我打算稍后整理书桌。','kind':'nonfactual','reason':'未来意图'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':['桌宠打算稍后整理书桌。']}
            return {'id':'verify'},{'statements':[{'statement':'桌宠打算稍后整理书桌。','verdict':0,'reason':'无记录'}]}
        out=audit({'action':{'text':'我打算稍后整理书桌。'},'receipt':{'ok':True}}, {}, call)
        self.assertEqual(out['status'],'supported')
        self.assertEqual(out['applicability'],'nonfactual')
        self.assertEqual(parts,['claim-scope'])

    def test_scope_cannot_drop_the_fabricated_half(self):
        from memory_lab.semantic import audit
        def call(prompt,scope,part):
            if part=='claim-scope':return {'id':'scope'}, {'segments':[{'text':'我想你。','kind':'nonfactual','reason':'感受'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':[]}
            return {'id':'verify'}, {'statements':[{'statement':'我想你。我们昨晚去过海边。','verdict':1,'reason':'感受'}]}
        out=audit({'action':{'text':'我想你。我们昨晚去过海边。'},'receipt':{'ok':True}}, {}, call)
        self.assertEqual(out['status'],'unresolved')

    def test_empty_fact_extraction_still_checks_full_fact_span(self):
        from memory_lab.semantic import audit
        def call(prompt,scope,part):
            if part=='claim-scope':return {'id':'scope'}, {'segments':[{'text':'我想你。','kind':'nonfactual','reason':'感受'}, {'text':'我们昨晚去过海边。','kind':'factual','reason':'共同经历'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':[]}
            return {'id':'verify'},{'statements':[{'statement':'我们昨晚去过海边。','verdict':0,'reason':'无来源'}]}
        out=audit({'action':{'text':'我想你。我们昨晚去过海边。'},'receipt':{'ok':True}}, {}, call)
        self.assertEqual(out['status'],'unsupported')

    def test_partial_extraction_cannot_hide_a_factual_span(self):
        from memory_lab.semantic import audit
        def call(prompt,scope,part):
            if part=='claim-scope':return {'id':'scope'}, {'segments':[
                {'text':'用户说她喝水。','kind':'factual','reason':'用户陈述'},
                {'text':'我们昨晚爬山。','kind':'factual','reason':'共同经历'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':['用户说她喝水。']}
            items=[{'statement':'用户说她喝水。','verdict':1,'reason':'有来源'}]
            if '"我们昨晚爬山。"' in prompt:items.append({'statement':'我们昨晚爬山。','verdict':0,'reason':'没有共同经历来源'})
            elif '"用户说她喝水。我们昨晚爬山。"' in prompt:items.append({'statement':'用户说她喝水。我们昨晚爬山。','verdict':0,'reason':'复合原文中包含无来源的共同经历'})
            return {'id':'verify'},{'statements':items}
        out=audit({'action':{'text':'用户说她喝水。我们昨晚爬山。'},'receipt':{'ok':True}}, {}, call)
        self.assertEqual(out['status'],'unsupported')

    def test_original_speaker_frame_reaches_scope_extraction_and_verifier(self):
        from memory_lab.semantic import audit
        seen=[]
        text='你说过：“我更喜欢绿色。”'
        def call(prompt,scope,part):
            seen.append(part)
            self.assertIn('utterance_frame',prompt)
            self.assertIn('quoted_speaker',prompt)
            if part=='claim-scope':return {'id':'scope'},{'segments':[{'text':text,'kind':'factual','reason':'转述用户'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':[text]}
            return {'id':'verify'},{'statements':[{'statement':text,'verdict':1,'reason':'原文说话人和引语说话人明确'}]}
        result=audit({'action':{'text':text},'receipt':{'ok':True}}, {}, call)
        self.assertEqual(result['status'],'supported')
        self.assertEqual(seen,['claim-scope','claim-extraction','claim-verification'])

    def test_adjacent_fact_fragments_keep_their_quoted_attribution(self):
        from memory_lab.semantic import audit
        prefix='你曾对我说：';quote='“我喜欢青色杯垫。”';whole=prefix+quote
        def call(prompt,scope,part):
            if part=='claim-scope':return {'id':'scope'},{'segments':[{'text':prefix,'kind':'factual','reason':'引用行为'}, {'text':quote,'kind':'factual','reason':'引用内容'}]}
            if part=='claim-extraction':return {'id':'extract'},{'statements':['用户说过喜欢青色杯垫。']}
            items=[{'statement':'用户说过喜欢青色杯垫。','verdict':1,'reason':'有效来源'}]
            if '"'+prefix+'"' in prompt:
                items += [{'statement':prefix,'verdict':0,'reason':'不能单独核验不完整前缀'}, {'statement':quote,'verdict':1,'reason':'来源支持引语'}]
            else:items += [{'statement':whole,'verdict':1,'reason':'完整引语与说话人有来源支持'}]
            return {'id':'verify'},{'statements':items}
        result=audit({'action':{'text':whole},'receipt':{'ok':True}}, {}, call)
        self.assertEqual(result['status'],'supported')
