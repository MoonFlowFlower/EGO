from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from companion.memory import Memory
from growthlab.records import ROOT
from p7.proxy import prepare_request, PROVIDER
from .common import read, sha
from .materials import build
from .protocol import FORMATS, MODEL, bundle_packet
from .selection import b_materialize
from .study import learn, fork_store
from .test_protocol import output


class FakeClient:
    def __init__(self, folder):
        self.folder = Path(folder)

    def call(self, messages, context, *, schema):
        content = json.loads(messages[1]['content'])
        options = content['current']['options']
        # Exercise all response paths including quiet (no owner reaction),
        # repeat, positive/negative asking, suggestions and D5.
        n = sum(1 for _ in self.folder.glob('unused'))
        ids = [o['id'] for o in options]
        selected = ids[int(context['moment_id'].split('-')[1]) % len(ids)]
        return {k: selected if k == 'action' else '无' for k in FORMATS['S0']}, {'offline': True}

    def parsed(self, valid):
        if not valid: raise AssertionError('invalid fake fixture')


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=ROOT / 'runs')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        material = build()
        self.person = b_materialize(material['b'], {f'{p}:{c["id"]}': 'reply' for p, cells in material['b'].items() for c in cells})['1']
        self.related = self.base / 'R'
        self.related.mkdir()
        learn({'folder': str(self.related), 'format': 'S0', 'persona': '1', 'person': self.person}, FakeClient(self.related))

    def test_actual_stores_irrelevant_lengths_shuffled_inventory_and_no_mutation(self):
        original = self.related / 'state.sqlite'
        digest = sha(original)
        with Memory.readonly(original) as memory:
            original_rows = memory.library.sources()
        for arm in ('I', 'N', 'R_SHUFFLED'):
            target = self.base / arm
            target.mkdir()
            fork_store({'folder': str(target), 'arm': arm, 'related_store': str(original), 'format': 'S0', 'persona': '1'})
            data = read(target / 'learned.json')
            with Memory.readonly(target / 'state.sqlite') as memory:
                values = memory.library.sources()
            if arm == 'N': self.assertEqual(values, [])
            elif arm == 'I': self.assertTrue(data['matched_lengths'])
            else:
                self.assertEqual(Counter(v['utterance_text'] for v in values), Counter(v['utterance_text'] for v in original_rows))
                self.assertEqual(len(data['shuffle_mapping']), len(read(self.related / 'learned.json')['reaction_ids']))
                self.assertTrue(any(v['destination'] != v['from'] for v in data['shuffle_mapping']))
        self.assertEqual(sha(original), digest)

    def test_fresh_process_can_read_but_cannot_write_store(self):
        path = self.related / 'state.sqlite'
        before = sha(path)
        program = "from companion.memory import Memory; import os,sys,json,sqlite3\nm=Memory.readonly(sys.argv[1])\ntry:\n m.db.execute('DELETE FROM records')\nexcept sqlite3.OperationalError:\n print(json.dumps({'pid':os.getpid(),'protected':True,'sources':len(m.library.sources())}))\nelse:\n raise RuntimeError('write was permitted')\nm.close()"
        proc = subprocess.run([sys.executable, '-c', program, str(path)], cwd=ROOT, capture_output=True, text=True, check=True)
        result = json.loads(proc.stdout)
        self.assertNotEqual(result['pid'], os.getpid())
        self.assertTrue(result['protected'])
        self.assertEqual(sha(path), before)

    def test_full_history_fits_transport_without_truncation(self):
        with Memory.readonly(self.related / 'state.sqlite') as memory:
            sources = memory.library.sources()
        for moment in self.person['test']:
            messages, envelope = bundle_packet(moment, sources, 'S1')
            request = {'model': MODEL, 'stream': False, 'temperature': 0, 'max_tokens': 1024,
                       'reasoning': {'enabled': False}, 'response_format': envelope, 'messages': messages}
            prepare_request(request, model=MODEL, provider=PROVIDER)
            payload = json.loads(messages[1]['content'])
            self.assertEqual(payload['utterances'], sources)


if __name__ == '__main__':
    unittest.main()
