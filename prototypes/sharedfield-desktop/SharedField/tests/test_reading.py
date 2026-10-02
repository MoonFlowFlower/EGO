import json
import tempfile
import unittest
from pathlib import Path
from switchlab.memory.store import MemoryStore


class ReadingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = MemoryStore(Path(self.temp.name) / 'memory.db')
        self.addCleanup(self.store.close)

    def op(self, op, **kw):
        return self.store.apply('reading', {'op': op, **kw}, at=1790000000)['result']

    def material(self, text='甲方案需要十分钟。\n\n乙方案需要二十分钟。'):
        return self.op('material', title='实际文本', text=text)['id']

    def start(self, material=None):
        return self.op('start', material_id=material or self.material(), question='两种方案有什么差异？', goal='比较方案')['id']

    def result(self, job, **extra):
        packet={'summary':'两种方案所需时间不同。', 'findings':[{'text':'甲需要十分钟。','paragraph':'p1','quote':'甲方案需要十分钟。'}], 'question':'还需要比较质量吗？'}
        packet.update(extra)
        return self.op('result', job_id=job['id'], packet=packet, receipt={'model':'EXPLICIT_TEST_FIXTURE','transport':'fixture','input_bytes':400,'usage':{}})

    def job(self):
        from switchlab.memory.reading import next_job
        return next_job(self.store)

    def state(self):
        from switchlab.memory.reading import view
        return view(self.store)

    def taught(self):
        aid=self.start();self.result(self.job())
        self.op('feedback', activity_id=aid, text='不能只比较时间，还要列出原文没有给出的质量信息。')
        self.result(self.job(), method={'instruction':'比较时区分已有证据和缺失信息。','scope':'比较方案','limits':'没有证据时不能推断质量高低。'})
        self.op('adopt', activity_id=aid)
        return aid

    def test_real_reading_feedback_method_and_restore(self):
        aid=self.taught();state=self.state()
        self.assertEqual(state['activities'][0]['status'],'learned')
        self.assertEqual(state['methods'][0]['instruction'],'比较时区分已有证据和缺失信息。')
        self.assertIn(state['activities'][0]['feedback']['source'],state['methods'][0]['sources'])
        self.assertIn(state['methods'][0]['id'],state['methods'][0]['sources'])
        exported=self.store.export();copy=MemoryStore.from_export(Path(self.temp.name)/'copy.db',exported)
        self.addCleanup(copy.close)
        from switchlab.memory.reading import view
        self.assertEqual(view(copy),state)

    def test_fabricated_citation_and_duplicate_result_rejected(self):
        self.start();job=self.job()
        with self.assertRaises(ValueError):self.result(job,findings=[{'text':'不实','paragraph':'p1','quote':'文本没有这句话'}])
        self.assertEqual(self.state()['activities'][0]['status'],'queued')
        self.result(job)
        with self.assertRaises(ValueError):self.result(job)

    def test_forgetting_adoption_removes_method_and_dependent_uses(self):
        aid=self.taught();method=self.state()['methods'][0]
        mid=self.material('丙方案需要十分钟。')
        self.op('compare',activity_id=aid,material_id=mid,question='需要多久？')
        self.store.forget([method['id']],at=1790000001)
        state=self.state()
        self.assertEqual(state['methods'],[])
        self.assertEqual(state['comparisons'],[])
        self.assertEqual(state['pending_jobs'],0)
        self.assertTrue(state['materials'])

    def test_cancel_invalidates_inflight_result(self):
        aid=self.start();job=self.job();self.op('cancel',activity_id=aid)
        with self.assertRaises(ValueError):self.result(job)
        self.assertIsNone(self.job())

    def test_transfer_same_history_and_no_target_feedback_leak(self):
        aid=self.taught();material=self.material('丙方案需要十分钟。\n\n丁方案需要二十分钟。')
        cid=self.op('compare',activity_id=aid,material_id=material,question='比较丙和丁。')['id']
        from switchlab.memory.reading import build_request, jobs
        pair=[j for j in jobs(self.store) if j.get('comparison_id')==cid]
        self.assertEqual(len(pair),2)
        prompts=[json.loads(build_request(self.store,j)[-1]['content']) for j in pair]
        self.assertEqual(prompts[0]['history'],prompts[1]['history'])
        self.assertEqual(prompts[0]['material'],prompts[1]['material'])
        self.assertEqual(sorted(bool(p['method']) for p in prompts),[False,True])
        for j in pair:self.result(j,findings=[{'text':'丙十分钟','paragraph':'p1','quote':'丙方案需要十分钟。'}])
        self.op('score',comparison_id=cid,scores={'A':[1,1,1],'B':[2,2,2]},notes='用户评价测试夹具，不是真实语义验证')
        comparison=self.state()['comparisons'][0]
        self.assertEqual(comparison['status'],'evaluated')
        self.assertIn(comparison['delta'],(-3,3))
        with self.assertRaises(ValueError):self.op('score',comparison_id=cid,scores={'A':[2,2,2],'B':[2,2,2]},notes='重复')

    def test_identical_material_not_transfer_and_freeze_blocks_adoption(self):
        aid=self.taught();material=self.state()['activities'][0]['material_id']
        with self.assertRaises(ValueError):self.op('compare',activity_id=aid,material_id=material,question='再次问')
        self.store.apply('setting',{'learning':False})
        aid2=self.start();self.result(self.job());self.op('feedback',activity_id=aid2,text='请说明条件')
        self.result(self.job(),method={'instruction':'说明适用条件','scope':'比较方案','limits':'不编造'})
        with self.assertRaises(ValueError):self.op('adopt',activity_id=aid2)

    def test_forget_removes_material_and_derived_methods(self):
        self.taught();material=self.state()['materials'][0]
        self.store.forget([material['source']])
        state=self.state()
        self.assertFalse(state['materials']);self.assertFalse(state['methods']);self.assertFalse(state['activities'])
        self.assertNotIn('甲方案需要十分钟',json.dumps(self.store.export(),ensure_ascii=False))

    def test_context_keeps_whole_material_or_fails_explicitly(self):
        aid=self.start(self.material('前文。'+'详细材料。'*3000+'结尾证据。'))
        from switchlab.memory.reading import build_request
        wire=json.loads(build_request(self.store,self.job())[-1]['content'])
        self.assertTrue(''.join(p['text'] for p in wire['material']['paragraphs']).endswith('结尾证据。'))

    def test_reimported_content_and_queued_comparison_not_novel(self):
        aid=self.taught();text='丙方案是新的实际材料。';mid=self.material(text)
        self.op('compare',activity_id=aid,material_id=mid,question='比较')
        duplicate=self.material(text)
        with self.assertRaises(ValueError):self.op('compare',activity_id=aid,material_id=duplicate,question='仍然同样内容')

    def test_withdrawn_and_frozen_method_not_in_chat_context(self):
        self.taught()
        from switchlab.memory.reading import chat_context
        self.assertTrue(chat_context(self.store)['activities'][0]['method'])
        self.store.apply('setting',{'learning':False})
        self.assertIsNone(chat_context(self.store)['activities'][0]['method'])
        self.store.apply('setting',{'learning':True});self.op('withdraw',method_id=self.state()['methods'][0]['id'])
        self.assertIsNone(chat_context(self.store)['activities'][0]['method'])

    def test_withdrawn_queued_method_is_not_used(self):
        self.taught();aid=self.start();job=self.job()
        self.op('withdraw',method_id=self.state()['methods'][0]['id'])
        from switchlab.memory.reading import build_request
        with self.assertRaises(ValueError):build_request(self.store,job)

    def test_unrelated_source_deletion_preserves_reading(self):
        self.taught();before=self.state()
        source=self.store.apply('message',{'text':'可删除的无关消息'})['id']
        self.store.forget([source])
        self.assertEqual(self.state(),before)

    def test_manual_pair_does_not_certify_same_model(self):
        aid=self.taught();mid=self.material('新材料的可核查句子。')
        cid=self.op('compare',activity_id=aid,material_id=mid,question='这句话说了什么？')['id']
        for _ in range(2):
            j=self.job();self.op('result',job_id=j['id'],packet={'summary':'新材料','question':'还有吗？','findings':[{'text':'这句话','paragraph':'p1','quote':'新材料的可核查句子。'}]},receipt={'model':'manual-external','transport':'manual-external','input_bytes':500,'usage':{}})
        self.op('score',comparison_id=cid,scores={'A':[1,1,1],'B':[1,1,1]},notes='人工评分')
        self.assertFalse(self.state()['comparisons'][0]['same_model'])
