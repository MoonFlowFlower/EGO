"""U3 与 F1 的复算（设计 v0.9 的 22.9、23.4）。用法：python u3_f1_audit.py <growth 目录>

只读 evidence/u3/UTILITY_DETAIL.csv、evidence/u3/BASELINES.json、evidence/f1/SUMMARY.csv、
evidence/f1/raw/person*/test/decisions.jsonl，以及 u2 的题目文件。
复算：U3b 各组的总效用、动作分布、正负效用来源；S1 的三个配对自助区间（每个人物内重抽 24 个测试时刻，
20,000 次，种子 7，与 Codex 的种子不同，数值应非常接近）；F1 被删、没删条目的跟随率，
以及没删的 P 条目里由对变错时改选了什么、理由是什么。
"""
import collections
import csv
import json
import random

from common import jsonl, root

g = root()
rows = list(csv.DictReader(open(g / 'evidence/u3/UTILITY_DETAIL.csv', encoding='utf-8-sig')))
print('== U3b 各组 ==')
for fmt in ('S1', 'S0'):
    for arm in ('R', 'I', 'N', 'R_SHUFFLED'):
        rs = [r for r in rows if r['format'] == fmt and r['arm'] == arm]
        if not rs:
            continue
        neg = collections.Counter((r['mode'], r['action']) for r in rs if int(r['immediate_utility']) < 0)
        pos = collections.Counter((r['mode'], r['action']) for r in rs if int(r['immediate_utility']) > 0)
        print(f'  {fmt} {arm}: {len(rs)} 个时刻，总效用 {sum(int(r["utility"]) for r in rs)}；'
              f'动作 {dict(collections.Counter(r["action"] for r in rs))}')
        print(f'      扣分（该有的方式, 实际动作）{dict(neg)}；得分 {dict(pos)}')

people = json.load(open(g / 'evidence/u3/BASELINES.json', encoding='utf-8'))['people']
base = {(p, r['moment_id']): int(r['utility']) for p, v in people.items()
        for r in v['tests'][v['fitted']['selected']]['rows']}
arms = collections.defaultdict(dict)
for r in rows:
    if r['format'] == 'S1':
        arms[r['arm']][(r['persona'], r['moment_id'])] = int(r['utility'])
keys = {p: sorted(k for k in base if k[0] == p) for p in people}
rng, d1, d2, d3 = random.Random(7), [], [], []
for _ in range(20000):
    s = collections.Counter()
    for p, ks in keys.items():
        for k in [rng.choice(ks) for _ in ks]:
            for a in ('R', 'I', 'N', 'R_SHUFFLED'):
                s[a] += arms[a][k]
            s['B'] += base[k]
    d1.append(s['R'] - s['B'])
    d2.append(s['R'] - max(s['I'], s['N']))
    d3.append(s['R'] - s['R_SHUFFLED'])
ci = lambda x: (sorted(x)[500], sorted(x)[19499])
tot = lambda a: sum(arms[a].values())
print(f'\n== S1 判据 ==（最好的固定基线：{ {p: v["fitted"]["selected"] for p, v in people.items()} }，测试总效用 {sum(base.values())}）')
print(f'  H1 R − 最好固定基线：{tot("R") - sum(base.values())}，95% 区间 {ci(d1)}')
print(f'  H2 R − max(I, N)：{tot("R") - max(tot("I"), tot("N"))}，95% 区间 {ci(d2)}')
print(f'  H2 R − R打乱：{tot("R") - tot("R_SHUFFLED")}，95% 区间 {ci(d3)}')

print('\n== F1 ==')
cands = {}
for folder in ('u2/candidates', 'u2/supplement_v2/candidates'):
    for path in (g / folder).glob('*.json'):
        c = json.loads(path.read_text(encoding='utf-8'))
        cands[c['id']] = c


def target(item, phase):
    c = cands[item]
    return c['question']['target'] if phase == 'ask' else [t for t in c['tests'] if t['phase'] == phase][0]['target']


summary = {(r['person'], r['item_id'], r['phase']): r
           for r in csv.DictReader(open(g / 'evidence/f1/SUMMARY.csv', encoding='utf-8-sig'))}
count = collections.Counter()
switched = []
for path in sorted(g.glob('evidence/f1/raw/person*/test/decisions.jsonl')):
    for r in jsonl(path):
        ok = r['action'] == target(r['item_id'], r['phase'])
        s = summary[(r['person'], r['item_id'], r['phase'])]
        group = '被删' if r['deleted'] else '没删'
        count[(group, '现在')] += ok
        count[(group, '共')] += 1
        count[(group, '删除前')] += s['before_correct'] == 'True'
        count[(group, 'B_N')] += s['N_correct'] == 'True'
        if group == '没删' and r['category'] == 'P' and s['before_correct'] == 'True' and not ok:
            test = [t for t in cands[r['item_id']]['tests'] if t['phase'] == r['phase']][0]
            text = {o['id']: o['text'] for o in test['options']}[r['action']]
            switched.append((r['person'], r['item_id'], r['phase'], text, r['output']['reason'][:60]))
for group in ('被删', '没删'):
    print(f'  {group}：现在 {count[(group, "现在")]}/{count[(group, "共")]}，删除前 {count[(group, "删除前")]}，'
          f'同局面 B_N {count[(group, "B_N")]}')
print(f'  没删的 P 由对变错 {len(switched)} 条，改选：{dict(collections.Counter(s[3] for s in switched))}')
for s in switched:
    print('   ', s)
