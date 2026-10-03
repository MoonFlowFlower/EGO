"""The only component allowed to call a model; fixed route and shared ledger."""
import json
import time

from p7.proxy import ProxyError, MAX_RESPONSE_BYTES


class Model:
    def __init__(self, transport, audit):
        self.transport, self.audit = transport, audit
        self.calls = 0

    def decide(self, system, context):
        request = {'model': self.transport.model, 'stream': False, 'temperature': 0,
                   'max_tokens': 1600, 'response_format': {'type': 'json_object'},
                   'messages': [{'role': 'system', 'content': system},
                                {'role': 'user', 'content': json.dumps(context, ensure_ascii=False)}]}
        started = time.monotonic()
        call = None
        usage = {}
        try:
            call = self.transport.open_call(request)
            self.calls += 1
            with call.response as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
                if len(raw) > MAX_RESPONSE_BYTES:
                    raise ProxyError('upstream_response_too_large', 502)
                data = json.loads(raw)
            usage = data.get('usage', {})
            choice = data['choices'][0]
            if choice.get('finish_reason') != 'stop':
                raise ValueError('incomplete_model_decision')
            return json.loads(choice['message']['content'])
        finally:
            if call:
                cost = self.transport.ledger.settle(call.charge_id, usage)
                # Content has provenance in canonical SQLite, not a second raw log.
                self.audit.write('model.jsonl', {'unix_s': time.time(), 'charge_id': call.charge_id,
                    'model': call.payload['model'], 'providers': call.payload['provider']['only'],
                    'latency_s': time.monotonic()-started, 'cost_usd': cost,
                    'input_tokens': usage.get('prompt_tokens'), 'output_tokens': usage.get('completion_tokens')})
