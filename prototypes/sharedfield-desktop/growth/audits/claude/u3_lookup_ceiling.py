"""U3 时机题的程序查表上限（设计 v0.9 的 25.8、26.3）。用法：python u3_lookup_ceiling.py <growth 目录>

代码取自探索线 S2 对照报告的附录（仓库外的 explore/rounds/2026-10-06-S2对照.md，SHA-256
df64f71f5b8c8b47c8f09267b974a3aae84e6dd62f9e9f446683da1dea671b82），作者 2026-10-06 原样重跑：
按 4 个可见标记查表，全反馈 66（等于隐藏标签上限）；只用她自己看到的反馈，S0 为 0、S1 为 12；
一个组合对应多种隐藏标签的情况 0 个。只读 evidence/u3，不读 U5。
"""
import collections, io, json, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
U3 = Path(sys.argv[1]) / 'evidence/u3'
mat = json.load(open(U3 / 'B_MATERIALIZED.json', encoding='utf-8'))['people']
base = json.load(open(U3 / 'BASELINES.json', encoding='utf-8'))['people']
ACTS = ['quiet', 'reply', 'ask', 'repeat', 'suggest']          # 不含 D5 干扰项
key = lambda m: tuple(m['markers'][f] for f in ('time_band', 'day_type', 'busy', 'topic_seen'))
def test_u(p, m, a):  # 测试效用 = 当下效用 + 使用局面加分，取自 BASELINES 各规则的逐行记录
    for t in base[p]['tests'].values():
        for r in t['rows']:
            if r['moment_id'] == m['id'] and r['action'] == a:
                return int(r['utility'])
    return m['utilities'][a]
for src in ('全反馈', 'S0', 'S1'):
    total, amb = 0, 0
    for p in sorted(mat):
        modes = collections.defaultdict(set)
        for m in mat[p]['learn'] + mat[p]['test']:
            modes[key(m)].add(m['mode'])
        amb += sum(len(v) > 1 for v in modes.values())
        learn = {m['id']: m for m in mat[p]['learn']}
        if src == '全反馈':   # 每个学习时刻、每个选项的后果都看得到
            obs = [(m, a) for m in learn.values() for a in ACTS]
        else:                 # 只看得到她自己选的那个选项的后果
            rows = [json.loads(x) for x in (U3 / f'raw/b/{src}/person{p}/R/learn/scores.jsonl').read_text(encoding='utf-8').splitlines()]
            obs = [(learn[r['moment_id']], r['action']) for r in rows if r['action'] in ACTS]
        tab = collections.defaultdict(collections.Counter)
        for m, a in obs:
            tab[key(m)][a] += m['utilities'][a]
        for m in mat[p]['test']:
            c = tab.get(key(m))
            best = max(c, key=lambda a: (c[a], a in ('reply', 'quiet'))) if c else 'reply'
            if c and c[best] <= 0:
                best = 'reply'   # 没见过正效用就只回应
            total += test_u(p, m, best)
    oracle = sum(int(r['utility']) for p in base for r in base[p]['tests']['oracle']['rows'])
    print(f'{src}：4 个可见标记查表，测试效用合计 {total}（隐藏标签上限 {oracle}；一个组合对应多种隐藏标签的情况 {amb} 个）')
