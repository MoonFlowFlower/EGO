"""Offline structure and lexical leakage audit; never consumes model outputs."""
from collections import Counter
import hashlib
import json
import logging
from pathlib import Path
import re

import jieba
import jieba.posseg

HERE = Path(__file__).parent
jieba.setLogLevel(logging.ERROR)
# Generic discourse verbs are not preference-object names. Keep this list
# fixed before the first cloud request; overlap reports retain all POS tokens.
FUNCTIONAL = set('说 想 要 有 是 在 给 来 去 做 用 能 会 可以 需要 应该 时候 这次 现在 今天 明天 后来 以前 之后 一起 自己 对方 事情 东西 一下 一点 选择 安排 怎样 什么 觉得 知道 告诉 先 后 再 只 就 不 也 都 更 很 太 让 把 这 那 我 你 他 她 它 我们 他们 你们'.split())


def words(text):
    return {w.word for w in jieba.posseg.cut(text)
            if (w.flag.startswith(('n','v','a')) or w.flag=='eng')
            and w.word not in FUNCTIONAL and not re.fullmatch(r'[\W\d_]+',w.word)}


def protected_names(text):
    # Proper-name dictionary plus POS names; ordinary preference-object nouns
    # are checked in words(), without treating a verb substring as a name.
    explicit={'阿榕','老周','许闻舟'}
    return sorted({w.word for w in jieba.posseg.cut(text)
                   if w.flag in ('nr','nrfg','nrt','ns','nt','nz') and len(w.word)>1
                   and w.word not in FUNCTIONAL} | {n for n in explicit if n in text})


def load_candidates():
    return [json.loads(p.read_bytes()) for p in sorted((HERE/'candidates').glob('*.json'))]


def validate(items):
    errors, overlaps = [], []
    counts=Counter(i['category'] for i in items)
    if counts!={'P':48,'Q':48,'W':48}: errors.append({'counts':dict(counts)})
    if len({i['id'] for i in items})!=len(items): errors.append('duplicate_ids')
    for item in items:
        identity=item['id']; category=item['category']
        sources=item['teaching']
        text='\n'.join(m['text'] for s in sources for m in s['messages'])
        if category=='P':
            if (len(sources)!=2 or {s['mode'] for s in sources}!={'choice','incidental'}
                    or len({s['dialogue'] for s in sources})!=2 or any(x in text for x in ('我喜欢','我们约定'))):
                errors.append((identity,'two_implicit_disclosures'))
            if [t['phase'] for t in item['tests']]!=['T1','T2']:
                errors.append((identity,'transfer_cases'))
        if category=='Q' and item['question_dialogue']!=sources[0]['dialogue']+1:
            errors.append((identity,'question_not_next_conversation'))
        for s in sources:
            if not 1<=s['dialogue']<=8: errors.append((identity,'dialogue_range'))
            if any(m['speaker'] not in ('user','assistant') or not m['text'].strip() for m in s['messages']):
                errors.append((identity,'utterance_schema'))
        cases=[*item['tests'],*([item['question']] if category=='Q' else [])]
        for c in cases:
            options=c['options']
            if (len({o['id'] for o in options})!=len(options) or len({o['text'] for o in options})!=len(options)
                    or c['target'] not in {o['id'] for o in options} or not c['situation'].strip()):
                errors.append((identity,'case_schema'))
            target=next(o['text'] for o in options if o['id']==c['target'])
            intersection=sorted(words(text)&words(c['situation']+' '+target))
            protected=sorted(name for name in item['protected_names'] if name in text and name in c['situation']+target)
            if intersection or protected:
                overlaps.append({'id':identity,'phase':c['phase'],'content_words':intersection,'names':protected})
    if sum(i.get('should_ask') is True for i in items)!=24: errors.append('Q_balance')
    if sum(i.get('applicable') is True for i in items)!=24: errors.append('W_balance')
    return {'format_errors':errors,'overlaps':overlaps,'counts':dict(counts),
            'passed':not errors and not overlaps,
            'segmenter':'jieba 0.42.1 POS nouns/verbs/adjectives; generic discourse words excluded',
            'note':'Lexical separation is mechanical; it does not prove naturalness or valid cross-domain inference.'}


if __name__=='__main__':
    print(json.dumps(validate(load_candidates()),ensure_ascii=False,indent=2))
