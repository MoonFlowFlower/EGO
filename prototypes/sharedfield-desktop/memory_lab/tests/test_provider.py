import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ProviderTests(unittest.TestCase):
    def test_only_labelled_credential_is_selected(self):
        from memory_lab.provider import read_key
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'keys.txt'
            p.write_text('other key: sk-or-other\ncodex key:\nsk-or-correct\n', encoding='utf-8')
            self.assertEqual(read_key(p), 'sk-or-correct')
            p.write_text('other key: sk-or-other', encoding='utf-8')
            with self.assertRaises(ValueError): read_key(p)

    def test_route_cannot_be_overridden(self):
        from memory_lab.provider import payload, MODEL
        p = payload({'model':'other', 'provider':{'allow_fallbacks':True},
                     'messages':[{'role':'user','content':'hello'}], 'temperature':1})
        self.assertEqual(p['model'], MODEL)
        self.assertEqual(p['temperature'], 0)
        self.assertFalse(p['provider']['allow_fallbacks'])
        self.assertEqual(p['provider']['only'], ['deepinfra/fp8'])

    def test_wrong_model_latches_batch_and_records_receipt(self):
        from memory_lab.provider import Client, BatchStopped
        with tempfile.TemporaryDirectory() as td:
            c = Client(Path(td), key='sk-or-test', max_calls=2)
            with patch.object(c, '_request', return_value={'id':'r','provider':'DeepInfra','model':'wrong','choices':[]}):
                with self.assertRaises(BatchStopped): c.chat([{'role':'user','content':'test'}])
            self.assertTrue((Path(td)/'STOPPED.json').exists())
            with patch.object(c, '_request') as request:
                with self.assertRaises(BatchStopped): c.chat([{'role':'user','content':'test'}])
                request.assert_not_called()
            self.assertEqual(len(list((Path(td)/'calls').glob('*.json'))),1)

    def test_timeout_never_retries_or_writes_key(self):
        from memory_lab.provider import Client, BatchStopped
        with tempfile.TemporaryDirectory() as td:
            c = Client(Path(td), key='sk-or-secret', max_calls=2)
            with patch.object(c, '_request', side_effect=TimeoutError('sk-or-secret')) as request:
                with self.assertRaises(BatchStopped): c.chat([{'role':'user','content':'test'}])
                self.assertEqual(request.call_count, 1)
            self.assertNotIn('sk-or-secret', ''.join(p.read_text() for p in Path(td).rglob('*.json')))
