import json
from pathlib import Path
import tempfile
import unittest

from companion.memory import Memory


def proposal(ids, text='你在独处时倾向留出安静的空隙。', **changes):
    return {'operation': 'add', 'record_id': None, 'text': text,
            'source_ids': ids, 'conditions': {'when': '独处时', 'who': '你'},
            'open_questions': [], 'update_source_ids': [], 'update_quote': '',
            **changes}


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'state.sqlite'
        self.m = Memory(self.path)
        self.addCleanup(self.m.close)

    def say(self, text, n=1):
        return self.m.library.utterance(text, session_id=f'dialogue-{n}',
                                        occurred_at=f'2026-10-0{n}T18:00:00-05:00')

    def test_fabricated_citation_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing_utterance'):
            self.m.understandings.propose(proposal(['invented']))

    def test_update_requires_new_quoted_evidence(self):
        source = self.say('把收音机关上吧，翻书的声音就够了。')
        old = self.m.understandings.propose(proposal([source]))
        with self.assertRaisesRegex(ValueError, 'update_evidence'):
            self.m.understandings.propose(proposal([source], operation='update', record_id=old))
        new_source = self.say('搬家后我一个人待着反而想听点背景音乐。', 2)
        new = self.m.understandings.propose(proposal([source,new_source],
            text='搬家后你独处时想听背景音乐。', operation='update', record_id=old,
            update_source_ids=[new_source], update_quote='搬家后我一个人待着反而想听点背景音乐。'))
        self.assertEqual([r['record_id'] for r in self.m.understandings.active()], [new])

    def test_deletion_covers_versions_derivatives_and_preserves_unrelated(self):
        a = self.say('松墨壶先放回去，晚饭用缺口碗。')
        b = self.say('橙色伞留在玄关。')
        first = self.m.understandings.propose(proposal([a], '你用餐偏向有缺痕的器物。',
            conditions={'when':'PRIVATE_CONDITION_379','who':'PRIVATE_PERSON_379'},open_questions=['PRIVATE_QUESTION_379']))
        update = self.say('现在餐具都换成完整的了。',2)
        last = self.m.understandings.propose(proposal([update], '你如今用无瑕的器皿。',
            operation='update', record_id=first, update_source_ids=[update], update_quote='现在餐具都换成完整的了。'))
        self.m.append('summary', {'text':'由旧餐具经历派生的特别摘要。'}, [first])
        self.m.understandings.propose(proposal([b], '你把雨具留在门旁。'))
        report = self.m.understandings.forget_sources([update])
        self.assertGreaterEqual(report['removed_records'], 4)
        rows = self.m.understandings.active()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['text'], '你把雨具留在门旁。')
        data = self.path.read_bytes()
        for text in ('现在餐具都换成完整的了。','你用餐偏向有缺痕的器物。','你如今用无瑕的器皿。','由旧餐具经历派生的特别摘要。',
                     'PRIVATE_CONDITION_379','PRIVATE_PERSON_379','PRIVATE_QUESTION_379'):
            self.assertNotIn(text.encode(), data)
        self.assertIsNotNone(self.m.record(b))

    def test_update_chronology_parses_offsets_in_program(self):
        old_source=self.m.library.utterance('旧的选择。',session_id='a',occurred_at='2026-10-05T09:00:00-05:00')
        old=self.m.understandings.propose(proposal([old_source]))
        earlier=self.m.library.utterance('这句实际上更早。',session_id='b',occurred_at='2026-10-05T13:00:00+00:00')
        with self.assertRaisesRegex(ValueError,'not_later'):
            self.m.understandings.propose(proposal([earlier],operation='update',record_id=old,
                update_source_ids=[earlier],update_quote='这句实际上更早。'))


if __name__ == '__main__':
    unittest.main()
