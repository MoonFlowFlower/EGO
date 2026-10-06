from copy import deepcopy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from companion.chatgpt import adapt_request, consume, Transport, UsageLedger, QUOTA
from companion.chatgpt_oauth import ChatGPTError
from companion.model import Model
from u2.protocol import decision_schema


def response(*events):
    stream = io.BytesIO(b''.join(b'data: ' + json.dumps(e).encode() + b'\n\n' for e in events))
    stream.headers, stream.status = {}, 200
    return stream


class TransportTests(unittest.TestCase):
    def test_adapter_preserves_every_content_byte_and_schema(self):
        request = {'model': 'test', 'messages': [{'role': 'system', 'content': '系统\n逐字'},
            {'role': 'user', 'content': '{"记忆": "  原文\\n "}'}], 'reasoning': {'enabled': True, 'effort': 'medium'},
            'response_format': decision_schema({'options': [{'id': 'a'}]}), 'temperature': 0, 'max_tokens': 1024}
        before = deepcopy(request)
        adapted = adapt_request(request)
        self.assertEqual(request, before)
        self.assertEqual(adapted['instructions'], request['messages'][0]['content'])
        self.assertEqual(adapted['input'], request['messages'][1:])
        self.assertEqual(adapted['text']['format']['schema'], request['response_format']['json_schema']['schema'])
        self.assertNotIn('temperature', adapted)
        self.assertNotIn('max_output_tokens', adapted)
        self.assertFalse(adapted['store'])
        self.assertTrue(adapted['stream'])

    def test_empty_terminal_uses_completed_output_items(self):
        item = {'type': 'message', 'content': [{'type': 'output_text', 'text': '{"answer":1}'}]}
        result = consume(response({'type': 'response.output_item.done', 'output_index': 0, 'item': item},
            {'type': 'response.completed', 'response': {'status': 'completed', 'output': [], 'usage': {'output_tokens': 4}}}))
        self.assertEqual(result['output'], [item])

    def test_partial_output_never_counts_as_success_and_quota_is_terminal(self):
        for event in ({'type': 'response.output_text.delta', 'delta': '{"answer":1}'},
                      {'type': 'response.failed', 'response': {'error': {'code': QUOTA}}}):
            with self.assertRaises(ChatGPTError) as caught:
                consume(response(event))
            self.assertEqual(caught.exception.code, QUOTA if event['type'] == 'response.failed' else 'chatgpt_interrupted_stream')

    def test_route_is_explicit_and_synthetic_only(self):
        with self.assertRaises(ChatGPTError):
            Transport('model')
        transport = type('T', (), {'route': 'chatgpt'})()
        with self.assertRaises(ValueError):
            Model(transport, None)
        self.assertEqual(Model(transport, None, route='chatgpt').route, 'chatgpt')

    def test_subscription_tokens_do_not_become_dollars(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = UsageLedger(Path(directory) / 'subscription.sqlite')
            identity = ledger.start('model')
            ledger.finish(identity, {'input_tokens': 10, 'output_tokens': 4}, .2)
            another = ledger.start('model')
            ledger.finish(another, {}, .1, {'code': QUOTA})
            snapshot = ledger.snapshot()
            self.assertEqual((snapshot['calls'], snapshot['input_tokens'], snapshot['output_tokens']), (2, 10, 4))
            self.assertEqual(snapshot['errors'], 1)
            self.assertEqual(snapshot['calls_without_usage'], 1)
            with ledger.connect() as db:
                self.assertNotIn('charges', [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")])


if __name__ == '__main__':
    unittest.main()
