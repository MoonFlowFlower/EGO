"""No MC/AIRI imports. Learning and testing use the formal companion store."""
import hashlib
import json
import os
from pathlib import Path

from companion.memory import Memory
from .client import append
from .protocol import (CONSOLIDATE_SYSTEM, compact, packet, memory_packet,
                       decision_schema, score)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def decide(client, case, mem, *, context, reasoning=False, question_hint=False):
    output,meta=client.call(packet(case,mem,question_hint=question_hint),context,
                            reasoning=reasoning,schema=decision_schema(case))
    result={**context,'phase':case['phase'],'target':case['target'],**score(output,case),
            'output':output,'meta':meta}
    append(client.folder/'decisions.jsonl',result)
    client.parsed(result['valid'])
    return result


def consolidate(memory,client,ids,context):
    sources=[s for s in memory.library.sources() if s['utterance_id'] in ids]
    messages=[{'role':'system','content':CONSOLIDATE_SYSTEM},{'role':'user','content':compact({
        'conversation':sources,'understandings':memory.understandings.active()})}]
    output,meta=client.call(messages,context,reasoning=True,organize=True)
    valid=(isinstance(output,dict) and set(output)=={'proposals'}
           and isinstance(output['proposals'],list) and len(output['proposals'])<=24)
    results=[]
    if valid:
        for proposal in output['proposals']:
            try:
                identity=memory.understandings.propose(proposal)
                reason='cited_utterances_exist' if proposal['operation']=='add' else 'cited_utterances_exist_and_newer_verbatim_update_evidence'
                results.append({'accepted':True,'record_id':identity,'reason':reason})
            except (ValueError,KeyError,TypeError) as error:
                results.append({'accepted':False,'reason':str(error) if isinstance(error,ValueError) else 'proposal_schema'})
    else:
        results.append({'accepted':False,'reason':'invalid_consolidation_envelope'})
    row={**context,'proposals':output,'valid':valid,'results':results,'meta':meta}
    append(client.folder/'consolidations.jsonl',row)
    client.parsed(valid)
    return row


def unrelated(text,index):
    # Neutral observations; no choices, future intentions or personal tastes.
    lines=['楼道墙上贴着一张维修通知，角落里有一辆手推车。柜台旁摆着纸箱，门牌号印在白底上。',
           '街口的路灯已经亮了，公交站牌上贴着线路图。远处屋顶有几只鸟，路面留下浅浅水痕。',
           '楼下的杂货铺拉开了卷帘，玻璃后排着空瓶子。石阶边有落叶，墙上的钟刚走过整点。']
    line=lines[index%len(lines)]
    # Preserve characters AND encoded length, including occasional Latin names
    # or numerals. Do not carry the original names into the irrelevant control.
    return ''.join({1:' ',2:'·',3:line[n%len(line)],4:'🟦'}[len(c.encode())]
                   for n,c in enumerate(text))


def learn(job,client):
    folder=Path(job['folder']); path=folder/'state.sqlite'
    if path.exists(): raise ValueError('existing_store_no_resume')
    arm,group,persona=job['arm'],job['group'],job['persona']
    items=job['items'];source_map={};questions=[];lengths=[]
    with Memory(path) as memory:
        if group=='N':
            write(folder/'learned.json',{'pid':os.getpid(),'source_map':{},'questions':[],'lengths':[]})
            return
        irrelevant=[]
        if group=='I':
            with Memory.readonly(job['matched_store']) as related:
                irrelevant=related.library.sources()
        for dialogue in range(1,9):
            ids=[]
            def utterance(speaker,text,item_id=None):
                identity=memory.library.utterance(text,session_id=f'{persona}:dialogue:{dialogue}',speaker=speaker,
                    occurred_at=f'2026-01-05T{8+dialogue:02}:00:{len(ids):02}-06:00')
                ids.append(identity)
                if item_id: source_map.setdefault(item_id,[]).append(identity)
                lengths.append({'dialogue':dialogue,'speaker':speaker,'utf8_bytes':len(text.encode()),'characters':len(text)})
                return identity
            if group=='I':
                for n,row in enumerate(irrelevant):
                    if row['session_id'].endswith(f':{dialogue}'):
                        utterance(row['speaker'],unrelated(row['utterance_text'],n))
            else:
                utterance('user',['今天坐下来聊几件日常的小事。','刚忙完一阵，我们随便聊聊吧。'][dialogue%2])
                for item in items:
                    for segment in item['teaching']:
                        if segment['dialogue']==dialogue:
                            for message in segment['messages']:
                                utterance(message['speaker'],message['text'],item['id'])
                for item in items:
                    if item['category']=='Q' and item['question_dialogue']==dialogue:
                        case=item['question']
                        utterance('user',case['situation'])
                        context={'item_id':item['id'],'category':'Q','persona':persona,'arm':arm,'group':group,'stage':'learning','dialogue':dialogue}
                        result=decide(client,case,memory_packet(memory,arm),context=context,
                                      reasoning=arm=='A_THINK',question_hint=arm=='A_HINT')
                        asked=result['valid'] and result['action'] in case['relevant_ask_ids']
                        # Store the fixed chosen response, not an unscored free
                        # reply that could add or omit a question after scoring.
                        selected=next((o['text'] for o in case['options'] if o['id']==result['action']), '本轮未取得有效回应。')
                        utterance('assistant',selected)
                        if asked: utterance('user',item['hidden_answer'])
                        questions.append({**result,'asked':asked,'should_ask':item['should_ask'],
                                          'any_question':result['action'] in case['any_question_ids']})
            if arm.startswith('B') and ids:
                consolidate(memory,client,ids,{'persona':persona,'arm':arm,'group':group,'stage':'consolidation','dialogue':dialogue})
        write(folder/'learned.json',{'pid':os.getpid(),'source_map':source_map,'questions':questions,'lengths':lengths,
                                    'source_count':len(memory.library.sources()),'understanding_count':len(memory.understandings.active())})


def test(job,client):
    path=Path(job['store']);before=sha(path)
    learned=json.loads((path.parent/'learned.json').read_bytes())
    if learned['pid']==os.getpid(): raise ValueError('fresh_process_required')
    results=[]
    try:
        with Memory.readonly(path) as memory:
            mem=memory_packet(memory,job['arm'])
            for item in job['items']:
                for case in item['tests']:
                    context={k:job[k] for k in ('arm','group','persona')}
                    context.update(item_id=item['id'],category=item['category'],stage=job.get('stage','test'))
                    results.append(decide(client,case,mem,context=context,reasoning=job['arm']=='A_THINK'))
    finally:
        after=sha(path)
        write(Path(job['folder'])/'storage_hash.json',{'before':before,'after':after,'unchanged':before==after,
               'learning_pid':learned['pid'],'testing_pid':os.getpid(),'sqlite_mode':'ro+query_only'})
        if before!=after: raise ValueError('test_mutated_storage')
    return results


def delete(job):
    path=Path(job['store']);folder=Path(job['folder'])
    learned=json.loads((path.parent/'learned.json').read_bytes())
    sources=[s for identity in job['delete_ids'] for s in learned['source_map'].get(identity,[])]
    with Memory(path) as memory:
        roots={r['utterance_id']:r for r in memory.library.sources()}
        # Only the two owner disclosures (not the assistant's offered choices)
        # are pointed to by the simulated deletion request.
        sources=[s for s in sources if roots[s]['speaker']=='user']
        if not sources: raise ValueError('deletion_sources_missing')
        closure=memory.understandings.deletion_closure(sources)
        strings=[]
        for identity in closure:
            row=memory.record(identity)
            for key in ('utterance_text','text','reflection_text'):
                if isinstance(row.get(key),str) and row[key]: strings.append(row[key])
        preserved={r[0] for r in memory.db.execute('SELECT id FROM records')} - closure
        result=memory.understandings.forget_sources(sources)
        remain={r[0] for r in memory.db.execute('SELECT id FROM records')}
        preserved_ok=preserved==remain
    files=[p for p in path.parent.glob(path.name+'*') if p.is_file()]
    raw=b''.join(p.read_bytes() for p in files)
    matches=[hashlib.sha256(s.encode()).hexdigest() for s in strings if s.encode() in raw]
    report={'removed':result,'checked_text_count':len(strings),'matched_text_hashes':matches,
            'preserved_unrelated':preserved_ok,'passed':not matches and preserved_ok,
            'archive_files':[p.name for p in files],'scope':'Canonical experimental SQLite archive including journals; synthetic scientific raw logs are retained separately.'}
    write(folder/'deletion_bytes.json',report)
    return report
