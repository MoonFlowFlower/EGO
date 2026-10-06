"""The only component allowed to call a model; fixed route and shared ledger."""
import json
import time
from contextlib import nullcontext
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
    if not isinstance(current, str) or not current:
        # Endogenous events have no current utterance. Keep source-bearing
        # history and tool feedback as evidence, not fabricated new dialogue.
        if transcript: evidence_context['historical_dialogue'] = transcript
        if feedback is not None: evidence_context['execution_feedback'] = feedback
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
    interpretation='situation' in context and 'matched_conventions' in context
    notice=context.get('harness_notice') or (context.get('execution_feedback') or {}).get('harness_notice')
    repair=isinstance(notice,dict) and notice.get('kind')=='invalid_model_output'
    thinking=(execution or interpretation or 'initiative_stage' in context) and not repair
    return {'model':model,'stream':False,'temperature':0,
            'max_tokens':(8192 if execution or context.get('initiative_stage') in ('choose','revise') else 2048) if thinking else 1600,
            'reasoning':{'enabled':True,'effort':'low','exclude':True} if thinking else {'enabled':False},
            'response_format':{'type':'json_object'},'messages':request_messages(system,context)}


class DecisionError(ValueError):
    def __init__(self,code):super().__init__(code);self.code=code


class Model:
    def __init__(self, transport, audit, *, route='deepseek'):
        if route not in ('deepseek', 'chatgpt'):
            raise ValueError('unknown_model_route')
        if (getattr(transport, 'route', None) == 'chatgpt') != (route == 'chatgpt'):
            raise ValueError('explicit_chatgpt_route_required')
        self.transport, self.audit = transport, audit
        self.route = route
        self.calls = 0

    def decide(self, system, context):
        request = request_payload(self.transport.model,system,context)
        output, _ = self.complete(request)
        return output

    def complete(self, request, *, observer=None, allow_invalid=False):
        """Shared production/experiment entry. The observer never receives headers."""
        if self.route == 'chatgpt':
            self.calls += 1
            return self.transport.complete(request, observer=observer, allow_invalid=allow_invalid)
        lock = getattr(self.transport.ledger, 'call_lock', nullcontext)
        with lock():
            return self._complete(request, observer=observer, allow_invalid=allow_invalid)

    def _complete(self, request, *, observer=None, allow_invalid=False):
        started = time.monotonic()
        call = None
        usage = {}
        finish_reason=None
        data = None
        error_code = None
        failed_charge = None
        if observer:
            observer('request', {'request':request})
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
            finish_reason=choice.get('finish_reason')
            if finish_reason != 'stop':
                raise DecisionError('model_output_truncated' if finish_reason=='length' else 'model_output_incomplete')
            try:
                output = json.loads(choice['message']['content'])
            except (json.JSONDecodeError,TypeError) as error:raise DecisionError('model_decision_json') from error
        except DecisionError as error:
            error_code=error.code
            if not allow_invalid: raise
            output=None
        except Exception as error:
            error_code = getattr(error,'code',type(error).__name__)
            failed_charge = getattr(error,'charge_id',None)
            raise
        finally:
            cost = None
            if call:
                cost = self.transport.ledger.settle(call.charge_id, usage)
                # Content has provenance in canonical SQLite, not a second raw log.
                self.audit.write('model.jsonl', {'unix_s': time.time(), 'charge_id': call.charge_id,
                    'model': call.payload['model'], 'providers': call.payload['provider']['only'],
                    'latency_s': time.monotonic()-started, 'cost_usd': cost,
                    'reasoning_requested':request['reasoning'],'max_tokens':request['max_tokens'],
                    'finish_reason':finish_reason,
                    'request_bytes':len(json.dumps(call.payload,ensure_ascii=False,separators=(',',':')).encode()),
                    'reasoning_tokens':usage.get('completion_tokens_details',{}).get('reasoning_tokens'),
                    'input_tokens': usage.get('prompt_tokens'), 'output_tokens': usage.get('completion_tokens')})
            meta = {'latency_s':time.monotonic()-started, 'charge_id':call.charge_id if call else failed_charge,
                    'cost_usd':cost, 'usage':usage, 'finish_reason':finish_reason,
                    'error':error_code, 'reasoning_requested':request.get('reasoning')}
            if error_code:
                self.audit.write('model.jsonl', {'event':'model_error','error_code':error_code})
            if observer:
                observer('response', {'response':data,'meta':meta})
        return output, meta
