"""One shared model, separate conversational intent from execution permission."""
from pathlib import Path
from .attention import validate_need

ROUTE_PROMPT=Path(__file__).with_name('intent_prompt.txt').read_text(encoding='utf-8')
CHAT_PROMPT=Path(__file__).with_name('chat_prompt.txt').read_text(encoding='utf-8')


def route_input(model, text, pending, annotations, *, situation=None):
    result=model.decide(ROUTE_PROMPT,{'current_user':text,'matched_conventions':annotations,'situation':situation})
    # A non-executing conversation has no task category to validate. This hint
    # must never prevent a reply or grant execution; other fields stay strict.
    if isinstance(result,dict) and result.get('mode') in ('chat','status'):
        result={**result,'task_kind':'ordinary'}
    if not isinstance(result,dict) or set(result)!={'mode','request_quote','task_kind','information_need'}:
        raise ValueError('intent_schema')
    validate_need(result['information_need'])
    if result['mode'] not in ('chat','status','task','resume','steer','memory','autonomy') or result['task_kind'] not in ('ordinary','structure','pickup','approach','follow'):
        raise ValueError('intent_value')
    quote=result['request_quote']
    if not isinstance(quote,str) or (result['mode'] in ('task','resume','steer','memory','autonomy') and (not quote or quote not in text)):
        raise ValueError('intent_must_quote_current_input')
    if result['mode']=='steer' and (not pending or pending.get('goal_status')=='completed'):
        return {**result,'mode':'task'}
    if result['mode']=='resume' and (not pending or pending.get('goal_status') == 'completed'):
        return {**result,'mode':'status'}
    return result


def chat_reply(model, context):
    result=model.decide(CHAT_PROMPT,context)
    if not isinstance(result,dict) or set(result)!={'reply'} or not isinstance(result['reply'],str) or not 0<len(result['reply'])<=1800:
        raise ValueError('chat_response_schema')
    return result['reply']
