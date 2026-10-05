"""Explain a generic observation boundary; this function cannot execute tools."""
from pathlib import Path
PROMPT=Path(__file__).with_name('stall_prompt.txt').read_text(encoding='utf-8')


def question(model,text,work,state,records,reason):
    latest_by_tool={r['action']['name']:i for i,r in enumerate(records)}
    selected=sorted(set(latest_by_tool.values())|set(range(max(0,len(records)-6),len(records))))
    value=model.decide(PROMPT,{'current_user':text,'work':work,'current_body':state,
        'tool_evidence':[records[i] for i in selected],
        'execution_boundary':{'reason':reason,'further_actions_allowed':False},
        'purpose':'explain the observed gap and ask one answerable question; do not invent permission or completion'})
    if not isinstance(value,dict) or set(value)!={'reply'} or not isinstance(value['reply'],str) or not 0<len(value['reply'])<=1800:
        raise ValueError('stall_reply_schema')
    return value['reply']
