"""One shared model, separate conversational intent from execution permission."""
from pathlib import Path

ROUTE_PROMPT=Path(__file__).with_name('intent_prompt.txt').read_text(encoding='utf-8')
CHAT_PROMPT=Path(__file__).with_name('chat_prompt.txt').read_text(encoding='utf-8')


def route_input(model, text, pending, annotations):
    result=model.decide(ROUTE_PROMPT,{'current_user':text,'pending_title':pending.get('title') if pending else None,
                                    'matched_conventions':annotations})
    if not isinstance(result,dict) or set(result)!={'mode','request_quote','task_kind'}:
        raise ValueError('intent_schema')
    if result['mode'] not in ('chat','status','task','resume','memory') or result['task_kind'] not in ('ordinary','structure'):
        raise ValueError('intent_value')
    quote=result['request_quote']
    if not isinstance(quote,str) or (result['mode'] in ('task','resume','memory') and (not quote or quote not in text)):
        raise ValueError('intent_must_quote_current_input')
    if result['mode']=='resume' and not pending:
        return {**result,'mode':'status'}
    return result


def chat_reply(model, context):
    result=model.decide(CHAT_PROMPT,context)
    if not isinstance(result,dict) or set(result)!={'reply'} or not isinstance(result['reply'],str) or not 0<len(result['reply'])<=1800:
        raise ValueError('chat_response_schema')
    return result['reply']
