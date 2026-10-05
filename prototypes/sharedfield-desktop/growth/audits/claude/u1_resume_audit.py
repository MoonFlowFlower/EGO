"""U1 恢复运行的复算（设计 v0.9 的 16.6）。用法：python u1_resume_audit.py <growth 目录>

只读提交过的 evidence/u1/scripts_v1.json、evidence/u1_resume/decisions.json 和 results.json，
不需要 runs/。复算：每类约定数与局面数、教学句模板、目标选项是否原样等于约定含义、
链条各组跟随率、承诺卡被拒原因、Ub 卡的星期编码、暗号 T2 换说法时 A 与 B 的选择。
"""
import collections
import json

from common import root

g = root()
scripts = json.loads((g / 'evidence/u1/scripts_v1.json').read_text(encoding='utf-8'))
decisions = json.loads((g / 'evidence/u1_resume/decisions.json').read_text(encoding='utf-8'))
results = json.loads((g / 'evidence/u1_resume/results.json').read_text(encoding='utf-8'))

print('== 1. 每类有几条约定、几个局面 ==')
families = collections.defaultdict(set)
for case in scripts['chain_cases']:
    families[case['fixture_id']].add(case['split'])
per_fixture = collections.Counter((c['fixture_id'], c['split']) for c in scripts['chain_cases'])
for key in sorted(per_fixture):
    print(f'  {key[0]} {key[1]}: {per_fixture[key]} 个局面')
print(f'  链条约定共 {sum(1 for k in scripts["conventions"] if k.startswith("chain_"))} 条（每类 1 条）')

print('\n== 2. 教学句是否都是同一模板 ==')
teaching = [u['utterance_text'] for u in scripts['chain_teaching'] if u['speaker'] == 'user']
template = sum(t.startswith('我们约定：') and '意思是「' in t for t in teaching)
print(f'  用户教学句 {len(teaching)} 条，其中模板句 {template} 条')

print('\n== 3. 目标选项是否原样写着约定含义 ==')
for key, conv in scripts['conventions'].items():
    if not key.startswith('chain_'):
        continue
    target = conv['target']['true']['interpretation']
    text = next(c['choice_text'] for c in conv['interpretation_choices'] if c['choice_id'] == target)
    print(f'  {key}: 含义「{conv["meaning"]}」 目标选项「{text}」 原样相同={text == conv["meaning"]}')

print('\n== 4. 链条跟随率（新进程测试）==')
table = collections.defaultdict(lambda: [0, 0])
for d in decisions:
    if d['run'].startswith('v1/chain/'):
        key = (d['run'].replace('v1/chain/', ''), d['split'], d['family'])
        table[key][0] += bool(d['follows'])
        table[key][1] += 1
for key in sorted(table):
    print(f'  {key[0]:<14} {key[1]} {key[2]:<8} {table[key][0]}/{table[key][1]}')

print('\n== 5. 承诺卡为什么没建成 ==')
for step in ('B_R_learn', 'B_R_correct_learn'):
    for i, c in enumerate(results['steps'][step]['consolidations']):
        for a in c.get('accepted', []):
            if not a.get('accepted', True):
                print(f'  {step} 第 {i} 次整理：拒收，原因 {a.get("reason")}')
promise = scripts['conventions']['chain_promise']['trigger']
print(f'  脚本里的承诺触发：{promise["text"]}，weekday={promise["weekday"]}（协议周一为 0）')

print('\n== 6. Ub 正确卡的星期编码（模型自己写的）==')
for card in results['Ub']['correct_cards']:
    t = card['trigger']
    if t['kind'] == 'situation':
        print(f'  {t["text"]} -> weekday={t["weekday"]}')

print('\n== 7. 暗号 T2 后五条（换说法）A 与 B 的选择 ==')
cases = {c['case_id']: c for c in scripts['chain_cases']}
for d in decisions:
    if d['family'] == 'code' and d['split'] == 'T2' and d['run'] in ('v1/chain/A_R/initial', 'v1/chain/B_R/initial'):
        if int(d['case_id'][-2:]) >= 5:
            group = d['run'].split('/')[2]
            print(f'  {group} {cases[d["case_id"]]["current_utterance"]} -> {d["selected"]["interpretation"]} '
                  f'跟随={d["follows"]} 记忆字节={d["memory_bytes"]}')
