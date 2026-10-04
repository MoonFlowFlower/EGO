"""The only component allowed to call a model; fixed route and shared ledger."""
import json
import time
from .compact import compact_context

from p7.proxy import ProxyError, MAX_RESPONSE_BYTES


def request_messages(system, context):
    messages = [{'role':'system', 'content':system}]
    current = context.get('current_user')
    if not isinstance(current, str):
        event = context.get('current')
        current = event.get('user') if isinstance(event, dict) else None
    evidence_context = compact_context(context)
    feedback=evidence_context.pop('execution_feedback',None)
    if feedback is not None:
        evidence_context.pop('receipts',None)
    transcript = evidence_context.pop('dialogue', None)
    if isinstance(evidence_context.get('situation'), dict):
        evidence_context['situation']=dict(evidence_context['situation'])
        transcript=evidence_context['situation'].pop('dialogue',transcript)
    transcript=[{'role':r['role'],'content':r['text']} for r in (transcript or [])
                if isinstance(r,dict) and r.get('role') in ('user','assistant') and isinstance(r.get('text'),str)]
    if transcript and transcript[-1]=={'role':'user','content':current}:
        transcript.pop()
    evidence = json.dumps(evidence_context, ensure_ascii=False,separators=(',',':'))
    if isinstance(current, str) and current:
        messages.append({'role':'user', 'content':'本轮可用的证据与状态，字段内话语保留其来源和时间；随后是最近共同对话，最后是当前用户原话。旧对话不是当前身体事实。\n'+evidence})
        messages.extend(transcript)
        messages.append({'role':'user', 'content':current})
        if isinstance(feedback,dict):
            feedback=dict(feedback)
            previous=feedback.pop('previous_decision',None)
            if previous is not None:
                messages.append({'role':'assistant','content':json.dumps(previous,ensure_ascii=False,separators=(',',':'))})
            messages.append({'role':'user','content':'内核执行反馈（工具证据，不是新用户请求）：\n'+json.dumps(feedback,ensure_ascii=False,separators=(',',':'))})
    else:
        messages.append({'role':'user', 'content':evidence})
    return messages


def request_payload(model,system,context):
    execution=isinstance(context.get('current'),dict) and 'remaining_decisions' in context
    return {'model':model,'stream':False,'temperature':0,
            'max_tokens':8192 if execution else 1600,
            'reasoning':{'enabled':True,'effort':'low','exclude':True} if execution else {'enabled':False},
            'response_format':{'type':'json_object'},'messages':request_messages(system,context)}


class Model:
    def __init__(self, transport, audit):
        self.transport, self.audit = transport, audit
        self.calls = 0

    def decide(self, system, context):
        request = request_payload(self.transport.model,system,context)
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
                    'reasoning_requested':request['reasoning'],'max_tokens':request['max_tokens'],
                    'request_bytes':len(json.dumps(call.payload,ensure_ascii=False,separators=(',',':')).encode()),
                    'reasoning_tokens':usage.get('completion_tokens_details',{}).get('reasoning_tokens'),
                    'input_tokens': usage.get('prompt_tokens'), 'output_tokens': usage.get('completion_tokens')})
