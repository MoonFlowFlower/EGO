"""D17: explicit, synthetic-only SIWC Responses transport and separate usage."""
from copy import deepcopy
from contextlib import contextmanager
import json
import sqlite3
import time
import uuid

from growthlab.records import ROOT
from p7.proxy import DEFAULT_BUDGET, MAX_RESPONSE_BYTES
from .chatgpt_oauth import (ChatGPTError, Credentials, RESOURCE, access_token,
                            file_lock, http)

USAGE = ROOT / 'runs/d17/usage.sqlite'
QUOTA = 'subscription_sharing_usage_limit_exceeded'


def adapt_request(request):
    """Change only the envelope. Message text and JSON schema are copied exactly."""
    messages = deepcopy(request['messages'])
    system = None
    if messages and messages[0]['role'] == 'system':
        system = messages.pop(0)['content']
    if any(m['role'] == 'system' for m in messages):
        raise ChatGPTError('d17_multiple_system_messages_unsupported')
    fmt = deepcopy(request['response_format'])
    if fmt['type'] == 'json_schema':
        fmt = {'type': 'json_schema', **fmt['json_schema']}
    result = {'model': request['model'], 'input': messages, 'store': False, 'stream': True,
              'text': {'format': fmt}, 'reasoning': {'effort':
                request['reasoning'].get('effort', 'low') if request['reasoning'].get('enabled') else 'none'}}
    if system is not None:
        result['instructions'] = system
    return result


def events(response):
    size, data = 0, []
    for raw in response:
        size += len(raw)
        if size > MAX_RESPONSE_BYTES:
            raise ChatGPTError('chatgpt_stream_too_large')
        line = raw.decode('utf-8').rstrip('\r\n')
        if not line:
            if data:
                value = '\n'.join(data)
                data = []
                if value != '[DONE]':
                    yield json.loads(value)
        elif line.startswith('data:'):
            data.append(line[5:].lstrip(' '))
    if data and '\n'.join(data) != '[DONE]':
        yield json.loads('\n'.join(data))


def consume(response):
    items = {}
    for event in events(response):
        kind = event.get('type')
        if kind == 'response.output_item.done':
            items[event['output_index']] = event['item']
        if kind == 'response.completed':
            result = event['response']
            if result.get('status') != 'completed':
                raise ChatGPTError('chatgpt_invalid_terminal_status', body=json.dumps(event, ensure_ascii=False))
            if not result.get('output'):
                result['output'] = [items[i] for i in sorted(items)]
            # Account metadata is not scientific evidence or synthetic text.
            result.pop('safety_identifier', None)
            result.pop('user', None)
            return result
        if kind in ('response.failed', 'error', 'response.incomplete'):
            result = event.get('response', event)
            error = result.get('error') or result
            code = error.get('code') or ('chatgpt_incomplete' if kind == 'response.incomplete' else 'chatgpt_stream_error')
            failure = ChatGPTError(code, status=getattr(response, 'status', 200),
                body=json.dumps(event, ensure_ascii=False), request_id=response.headers.get('x-request-id'))
            failure.usage = result.get('usage') or {}
            raise failure
    raise ChatGPTError('chatgpt_interrupted_stream', status=getattr(response, 'status', 200),
                       request_id=response.headers.get('x-request-id'))


class UsageLedger:
    def __init__(self, path=USAGE):
        from pathlib import Path
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS calls
                (id TEXT PRIMARY KEY, started REAL, model TEXT, status TEXT, input_tokens INTEGER,
                 output_tokens INTEGER, reasoning_tokens INTEGER, latency_s REAL, error TEXT)''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        try:
            with db:
                yield db
        finally:
            db.close()

    def start(self, model):
        identity = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO calls(id,started,model,status) VALUES(?,?,?,?)',
                       (identity, time.time(), model, 'unknown'))
        return identity

    def finish(self, identity, usage, latency, error=None):
        with self.connect() as db:
            db.execute('''UPDATE calls SET status=?,input_tokens=?,output_tokens=?,reasoning_tokens=?,
                latency_s=?,error=? WHERE id=?''', ('failed' if error else 'completed',
                usage.get('input_tokens'), usage.get('output_tokens'),
                (usage.get('output_tokens_details') or {}).get('reasoning_tokens'), latency,
                json.dumps(error, ensure_ascii=False) if error else None, identity))

    def snapshot(self):
        with self.connect() as db:
            row = db.execute('''SELECT COUNT(*), COALESCE(SUM(input_tokens),0),
                COALESCE(SUM(output_tokens),0), SUM(status='failed'), SUM(status='unknown'),
                SUM(input_tokens IS NULL OR output_tokens IS NULL) FROM calls''').fetchone()
            last = db.execute('SELECT error FROM calls WHERE error IS NOT NULL ORDER BY started DESC LIMIT 1').fetchone()
        return dict(zip(('calls', 'input_tokens', 'output_tokens', 'errors', 'unknown_calls', 'calls_without_usage'), row),
                    billing='subscription', last_error=json.loads(last[0]) if last else None)


class Transport:
    route = 'chatgpt'

    def __init__(self, model, *, synthetic=False, credentials=None, ledger=None):
        if synthetic is not True:
            raise ChatGPTError('d17_synthetic_only')
        self.model, self.synthetic = model, synthetic
        self.credentials = credentials or Credentials()
        self.ledger = ledger or UsageLedger()

    def catalog(self):
        return http(RESOURCE + '/models', bearer=access_token(self.credentials))

    def complete(self, request, *, observer=None, allow_invalid=False):
        from .model import DecisionError
        if request['model'] != self.model:
            raise ChatGPTError('d17_model_changed')
        payload = adapt_request(request)
        # This lock shares single concurrency with DeepSeek without using its dollar ledger.
        with file_lock(DEFAULT_BUDGET.with_suffix('.model-call.lock')):
            token = access_token(self.credentials)
            started = time.monotonic()
            identity = self.ledger.start(self.model)
            usage, result, error, output = {}, None, None, None
            if observer:
                observer('request', {'request': request, 'wire_request': payload, 'route': self.route})
            try:
                with http(RESOURCE + '/responses', bearer=token, payload=payload, stream=True) as response:
                    result = consume(response)
                usage = result.get('usage') or {}
                messages = [x for x in result.get('output', []) if x.get('type') == 'message']
                parts = [p for m in messages for p in m.get('content', [])]
                if any(p.get('type') == 'refusal' for p in parts):
                    raise DecisionError('model_refusal')
                content = ''.join(p['text'] for p in parts if p.get('type') == 'output_text')
                try:
                    output = json.loads(content)
                except (ValueError, TypeError):
                    raise DecisionError('model_decision_json') from None
            except DecisionError as failure:
                error = {'code': failure.code, 'body': '', 'http_status': 200}
                if not allow_invalid:
                    raise
            except ChatGPTError as failure:
                from .chatgpt_oauth import redact
                failure.body = redact(failure.body, (token,))
                usage = getattr(failure, 'usage', {})
                error = failure.evidence()
                raise
            except (OSError, TimeoutError, ValueError) as failure:
                error = {'code': 'chatgpt_interrupted_stream', 'body': '', 'http_status': None}
                raise ChatGPTError(error['code']) from None
            except BaseException:
                error = {'code': 'chatgpt_interrupted_call', 'body': '', 'http_status': None}
                raise
            finally:
                latency = time.monotonic() - started
                self.ledger.finish(identity, usage, latency, error)
                meta = {'route': self.route, 'subscription_call_id': identity, 'cost_usd': None,
                    'latency_s': latency, 'usage': usage, 'error': error,
                    'finish_reason': 'stop' if result and not error else None,
                    'returned_model': result.get('model') if result else None,
                    'reasoning_requested': request['reasoning']}
                if observer:
                    observer('response', {'response': result, 'meta': meta})
            return output, meta
