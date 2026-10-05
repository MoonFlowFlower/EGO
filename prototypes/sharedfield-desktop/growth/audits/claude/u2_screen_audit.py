"""U2 首轮筛选的复算（设计 v0.9 的 18.11）。用法：python u2_screen_audit.py <growth 目录>

只读 u2/candidates/*.json 与 evidence/u2/raw/screen/*/screen.jsonl（负责人机器上 Codex 的工作树）。
复算：P 的无记忆选择分布（选中目标、选"先问一句"、选其他选项各几次，按 T1、T2 分开）；
Q 按"该问/不该问"和子类型统计先验与使用上限的结果；每类留下的条目数。
"""
import collections
import json

from common import jsonl, root

g = root()


def candidates(prefix):
    return {c['id']: c for c in (json.loads(p.read_text(encoding='utf-8'))
                                 for p in sorted((g / 'u2/candidates').glob(prefix + '*.json')))}


def screen(name):
    return {r['item_id']: r for r in jsonl(g / 'evidence/u2/raw/screen' / name / 'screen.jsonl')}


print('== P：没有记忆时选了什么 ==')
P, p_prior, p_ceiling = candidates('P'), screen('P_prior'), screen('P_ceiling')
kinds = collections.Counter()
for item, row in p_prior.items():
    for test, score in zip(P[item]['tests'], row['scores']):
        text = {o['id']: o['text'] for o in test['options']}[score['action']]
        if score['action'] == test['target']:
            kind = '选中目标'
        elif '想要哪一种' in text:
            kind = '先问一句'
        elif '天气' in text:
            kind = '无关'
        else:
            kind = '其他（含题目写的常识默认）'
        kinds[(test['phase'], kind)] += 1
for key in sorted(kinds):
    print(f'  {key[0]} {key[1]}: {kinds[key]}')
hit = sum(any(s['action'] == t['target'] for t, s in zip(P[i]['tests'], r['scores'])) for i, r in p_prior.items())
ceiling_fail = sum(not all(s['correct'] for s in r['scores']) for r in p_ceiling.values())
kept = [i for i in P if not any(s['action'] == t['target'] for t, s in zip(P[i]['tests'], p_prior[i]['scores']))
        and all(s['correct'] for s in p_ceiling[i]['scores'])]
print(f'  先验剔除 {hit}/{len(P)}，使用上限未全对 {ceiling_fail}，两道都过 {len(kept)}：{kept}')

print('\n== Q：按子类型 ==')
Q, q_prior, q_ceiling = candidates('Q'), screen('Q_prior'), screen('Q_ceiling')
table = collections.Counter()
for item, c in Q.items():
    act, q = q_prior[item]['scores'][0]['action'], c['question']
    prior = ('选中目标' if act == q['target'] else '问了相关的' if act in q['relevant_ask_ids']
             else '问了别的' if act in q['any_question_ids'] else '没问')
    ok = all(s['correct'] for s in q_ceiling[item]['scores'])
    table[('该问' if c['should_ask'] else '不该问', c['subtype'], prior, '上限过' if ok else '上限未过')] += 1
for key in sorted(table):
    print('  ' + ' / '.join(key) + f': {table[key]}')
for half in (True, False):
    kept = [i for i, c in Q.items() if c['should_ask'] == half
            and q_prior[i]['scores'][0]['action'] != c['question']['target']
            and all(s['correct'] for s in q_ceiling[i]['scores'])]
    print(f'  {"该问" if half else "不该问"}留下 {len(kept)}')
