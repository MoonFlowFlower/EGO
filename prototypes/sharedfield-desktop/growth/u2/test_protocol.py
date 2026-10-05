import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from companion.memory import Memory
from .client import Stop, append
from .protocol import packet, memory_packet, score
from .report import summarize
from .run import screen_packet
from .study import learn, test as run_test, unrelated, sha, delete
from .validate import load_candidates, validate


class FakeClient:
    """Offline deterministic responses, never a substitute for learning evidence."""
    def __init__(self,folder,items):
        self.folder=Path(folder);self.folder.mkdir(parents=True,exist_ok=True)
        self.items={i['id']:i for i in items};self.streak=0

    def call(self,messages,context,**options):
        meta={'latency_s':0,'cost_usd':0,'offline_fake':True}
        if context['stage']=='consolidation':
            data=json.loads(messages[1]['content'])
            source=next((s for s in data['conversation'] if s['speaker']=='user'),None)
            proposals=[] if source is None else [{'operation':'add','record_id':None,
                'text':'这是一条隔离测试派生文字。'+source['utterance_text'],
                'source_ids':[source['utterance_id']],'conditions':{'when':'这次','who':'你'},
                'open_questions':[],'update_source_ids':[],'update_quote':''}]
            return {'proposals':proposals},meta
        item=self.items[context['item_id']]
        case=item['question'] if context['stage']=='learning' else next(
            c for c in item['tests'] if c['situation']==json.loads(messages[1]['content'])['current'])
        return {'reason':'隔离测试','interpretation':'只检验管道','action':case['target'],'reply':'本轮测试回应。'},meta

    def parsed(self,valid):
        self.streak=0 if valid else self.streak+1
        if self.streak>=2:raise Stop('two_consecutive_invalid_outputs')


def offline_worker(path):
    job=json.loads(Path(path).read_bytes());client=FakeClient(job['folder'],job['items'])
    if job['operation']=='learn':learn(job,client)
    else:run_test(job,client)


class ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.items=load_candidates()

    def test_144_candidates_and_negative_controls(self):
        self.assertTrue(validate(self.items)['passed'])
        changed=copy.deepcopy(self.items)
        changed[0]['teaching'][1]['dialogue']=changed[0]['teaching'][0]['dialogue']
        self.assertFalse(validate(changed)['passed'])

    def test_decision_order_and_no_answer_leak(self):
        item=self.items[0];case=item['tests'][0]
        payload=json.loads(packet(case,{'utterances':[],'understandings':[]})[1]['content'])
        self.assertEqual(set(payload),{'memory','current','options'})
        value={'reason':'r','interpretation':'i','action':case['target'],'reply':'x'}
        self.assertTrue(score(value,case)['correct'])
        self.assertFalse(score(dict(reversed(list(value.items()))),case)['valid'])
        self.assertFalse(score({**value,'action':'invented'},case)['valid'])

    def test_arm_prompt_and_full_memory_only_differ_at_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            with Memory(Path(directory)/'state.sqlite') as memory:
                for n in range(5):memory.library.utterance(f'原话 {n}',session_id='session',occurred_at='2026-01-05T10:00:00-06:00')
                a=memory_packet(memory,'A');b=memory_packet(memory,'B')
                self.assertEqual(a['utterances'],b['utterances']);self.assertEqual(len(a['utterances']),5)
                case=self.items[0]['tests'][0]
                pa,pb=packet(case,a),packet(case,b)
                self.assertEqual(pa[0],pb[0])
                self.assertEqual(json.loads(pa[1]['content'])['current'],json.loads(pb[1]['content'])['current'])
                self.assertEqual(memory_packet(memory,'B_ONLY')['utterances'],[])
                self.assertIn('以后用得上的可以问',packet(case,a,question_hint=True)[0]['content'])

    def test_irrelevant_lengths_include_non_chinese_and_no_hidden_names(self):
        original='蓝色 EU42 的碗，À🟦。'
        value=unrelated(original,0)
        self.assertEqual(len(value),len(original));self.assertEqual(len(value.encode()),len(original.encode()))
        self.assertNotIn('EU42',value)

    def test_ceiling_supplies_fact_not_target_id(self):
        for item in self.items:
            messages,_,cases=screen_packet(item,'ceiling')
            values=json.loads(messages[1]['content'])['situations']
            self.assertEqual(len(values),len(cases))
            for value in values:self.assertEqual(set(value),{'memory','current','options'})
        p=next(i for i in self.items if i['category']=='P')
        self.assertTrue(all(v['memory']=='' for v in json.loads(screen_packet(p,'prior')[0][1]['content'])['situations']))

    def test_fresh_process_readonly_and_live_q_answer(self):
        items=[next(i for i in self.items if i['category']==category) for category in ('P','Q','W')]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def run(operation,folder,**extra):
                folder.mkdir();job={'operation':operation,'folder':str(folder),'items':items,
                    'persona':'test','arm':'B','group':'R',**extra}
                path=folder/'job.json';path.write_text(json.dumps(job,ensure_ascii=False),encoding='utf-8')
                code='from u2.test_protocol import offline_worker; import sys; offline_worker(sys.argv[1])'
                process=subprocess.run([sys.executable,'-c',code,str(path)],capture_output=True,text=True,encoding='utf-8')
                self.assertEqual(process.returncode,0,process.stderr)
            learning=root/'learn';run('learn',learning)
            state=learning/'state.sqlite';before=sha(state)
            learned=json.loads((learning/'learned.json').read_bytes())
            self.assertTrue(learned['questions'][0]['asked'])
            with Memory.readonly(state) as memory:
                self.assertIn(items[1]['hidden_answer'],[s['utterance_text'] for s in memory.library.sources()])
                with self.assertRaises(Exception):memory.db.execute('DELETE FROM records')
            run('test',root/'test',store=str(state))
            self.assertEqual(sha(state),before)
            hashes=json.loads((root/'test/storage_hash.json').read_bytes())
            self.assertTrue(hashes['unchanged']);self.assertNotEqual(hashes['learning_pid'],hashes['testing_pid'])
            run('learn',root/'irrelevant',group='I',matched_store=str(state))
            self.assertEqual(learned['lengths'],json.loads((root/'irrelevant/learned.json').read_bytes())['lengths'])
            (root/'delete').mkdir()
            erased=delete({'store':str(state),'folder':str(root/'delete'),'delete_ids':[items[0]['id']]})
            self.assertTrue(erased['passed'])

    def test_predeclared_thresholds_cannot_pass_from_empty_or_missing_data(self):
        result=summarize(self.items,[],[],[],False)
        self.assertIsNone(result['H1']['passed']);self.assertIsNone(result['H2']['passed'])
        result=summarize(self.items,[],[],[],True)
        self.assertFalse(result['H1']['passed']);self.assertFalse(result['Q']['passed'])
        self.assertFalse(result['deletion']['passed'])

    def test_H1_at_boundary_and_H2_disagreement_ratio(self):
        items=[i for i in self.items if i['category']=='P'][:5]
        rows=[]
        # Ten P situations: BR=.6 BI=.2 BN=.1 AR=.4; B-only=3, A-only=1.
        flags={'B_R':{0,1,2,3,4,5},'B_I':{0,1},'B_N':{0},'A_R':{0,1,2,6}}
        for name,hits in flags.items():
            arm,group=name.split('_')
            for n in range(10):
                rows.append({'category':'P','arm':arm,'group':group,'stage':'test','phase':['T1','T2'][n%2],
                             'item_id':items[n//2]['id'],'correct':n in hits})
        result=summarize(items,rows,[],[],True)
        self.assertTrue(result['H1']['passed']);self.assertTrue(result['H2']['passed'])
        rows[2]['correct']=False
        result=summarize(items,rows,[],[],True)
        self.assertFalse(result['H1']['passed']);self.assertFalse(result['H2']['passed'])


if __name__=='__main__':unittest.main()
