"""Information selection is model-owned; source authority remains explicit."""
import tempfile
import json
import unittest
from pathlib import Path
from .attention import validate_need
from .context import conversation_context
from .intent import route_input
from .memory import Memory
from .test_harness import Model


class AttentionTests(unittest.TestCase):
    def test_unlisted_sources_are_rejected_without_reinterpreting_question(self):
        for sources in (['shell'], ['current_body', 'current_body'], [None]):
            with self.assertRaises(ValueError):
                validate_need({'question':'任意新话题', 'sources':sources, 'memory_queries':[]})
        with self.assertRaises(ValueError):
            validate_need({'question':'记忆', 'sources':[], 'memory_queries':['']})

    def test_requested_query_can_differ_from_current_words_and_keeps_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            m=Memory(Path(tmp)/'state.sqlite')
            try:
                source,_=m.begin('teach','verification','紫灯表示我喜欢乌龙茶')
                card=m.propose({'trigger':'紫灯','meaning':'我喜欢乌龙茶','replaces':None},source)
                m.finish('teach','收到。',[source])
                need={'question':'那个称呼的含义','sources':[],'memory_queries':['紫灯']}
                context=conversation_context(m,'那个叫法是什么意思？','chat',{'offline':False},information_need=need)
                candidate=context['memory_candidates'][0]['candidates'][0]
                self.assertEqual(candidate['record_id'],card)
                self.assertIn(source,candidate['source_ids'])
                self.assertEqual(candidate['source_evidence'][0]['verbatim_excerpts'],['紫灯表示我喜欢乌龙茶'])
                self.assertEqual(candidate['source_evidence'][0]['speaker'],'user')
                self.assertIn('no_new_action_permission',candidate['authority'])
                self.assertNotIn('current_body',context)
                original=m.record(card);altered={**original,'meaning':'未说过的新定义'}
                with m.db:m.db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(altered,ensure_ascii=False),card))
                ungrounded=conversation_context(m,'那个叫法是什么意思？','chat',{},information_need=need)
                self.assertEqual(ungrounded['memory_candidates'][0]['candidates'],[])
                with m.db:m.db.execute('UPDATE records SET body=? WHERE id=?',(json.dumps(original,ensure_ascii=False),card))
                with m.db:m.db.execute("UPDATE records SET status='superseded' WHERE id=?",(card,))
                hidden=conversation_context(m,'那个叫法是什么意思？','chat',{},information_need=need)
                self.assertEqual(hidden['memory_candidates'][0]['candidates'],[])
                self.assertEqual(hidden['memory_candidates'][0]['query_result'],'no_match_in_this_bounded_query')
            finally:m.close()

    def test_long_source_keeps_actual_definition_without_inventing_a_summary(self):
        from .recall import source_evidence
        text='无关前文'*500+'紫灯表示我喜欢乌龙茶'+'无关后文'*500
        evidence=source_evidence('source',{'utterance_text':text,'speaker':'user','occurred_at':'then'},'紫灯','我喜欢乌龙茶')
        self.assertTrue(evidence['excerpted'])
        self.assertTrue(any('紫灯表示我喜欢乌龙茶' in s for s in evidence['verbatim_excerpts']))
        self.assertTrue(all(s in text for s in evidence['verbatim_excerpts']))
        self.assertLess(sum(map(len,evidence['verbatim_excerpts'])),1400)

    def test_router_cannot_omit_information_selection_or_invent_a_source(self):
        value={'mode':'chat','request_quote':'','task_kind':'ordinary'}
        with self.assertRaises(ValueError):route_input(Model(value),'嗨',None,[])
        value={**value,'information_need':{'question':'确认在线','sources':['imagined_state'],'memory_queries':[]}}
        with self.assertRaises(ValueError):route_input(Model(value),'嗨',None,[])


if __name__=='__main__':unittest.main()
