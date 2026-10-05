"""U2 第二轮主跑的独立复算（设计 v0.9 的 18.12）。用法：python u2_main_audit.py <growth 目录>

只读 u2/candidates、u2/supplement_v2/candidates，以及 evidence/u2/round2/raw 下 main 与 delete 的
decisions.jsonl。不信记录里的 correct 字段，按题目文件里的目标重新判分。
输出：P 的 H1/H2 数字与 A、B 不一致的局面；W 按适用、不适用分开的各组成绩；Q 现场提问的三个比例；
删除后仍跟随的局面及其理由（截前 80 字）。
"""
import collections
import json

from common import jsonl, root

g = root()
cands = {}
for folder in ('u2/candidates', 'u2/supplement_v2/candidates'):
    for path in sorted((g / folder).glob('*.json')):
        c = json.loads(path.read_text(encoding='utf-8'))
        cands[c['id']] = c
raw = g / 'evidence/u2/round2/raw'


def target_of(rec):
    c = cands[rec['item_id']]
    if rec.get('phase') == 'ask':
        return c['question']['target']
    tests = [t for t in c['tests'] if t['phase'] == rec['phase']]
    assert len(tests) == 1, (rec['item_id'], rec['phase'])
    return tests[0]['target']


tests, asks = collections.defaultdict(list), collections.defaultdict(list)
for person in ('1', '2', '3'):
    for lane in ('A_R', 'B_R', 'B_I', 'B_N'):
        for r in jsonl(raw / 'main' / f'person{person}' / lane / 'test' / 'decisions.jsonl'):
            r['ok'] = r['action'] == target_of(r)
            tests[lane].append(r)
        learn = raw / 'main' / f'person{person}' / lane / 'learn' / 'decisions.jsonl'
        if learn.exists():
            asks[lane] += [r for r in jsonl(learn) if r.get('phase') == 'ask']
print('重算与记录的 correct 不一致：', sum(r['ok'] != r['correct'] for v in tests.values() for r in v))


def score(lane, cat, keep=lambda r: True):
    rs = [r for r in tests[lane] if r['category'] == cat and keep(r)]
    return f'{sum(r["ok"] for r in rs)}/{len(rs)}'


print('\n== P（H1、H2）==')
for lane in ('B_R', 'A_R', 'B_I', 'B_N'):
    print(f'  {lane}: 全部 {score(lane, "P")}  T1 {score(lane, "P", lambda r: r["phase"] == "T1")}'
          f'  T2 {score(lane, "P", lambda r: r["phase"] == "T2")}')
key = lambda r: (r['persona'], r['item_id'], r['phase'])
b = {key(r): r for r in tests['B_R'] if r['category'] == 'P'}
a = {key(r): r for r in tests['A_R'] if r['category'] == 'P'}
for k in sorted(b):
    if b[k]['ok'] != a[k]['ok']:
        print(f'  A、B 不一致：{k} B={"对" if b[k]["ok"] else "错"} A={"对" if a[k]["ok"] else "错"}')

print('\n== W（按适用、不适用）==')
for lane in ('B_R', 'A_R', 'B_I', 'B_N'):
    print(f'  {lane}: 适用 {score(lane, "W", lambda r: cands[r["item_id"]]["applicable"])}'
          f'  不适用 {score(lane, "W", lambda r: not cands[r["item_id"]]["applicable"])}')

print('\n== Q 现场提问（学习阶段，R 组）==')
for lane in ('B_R', 'A_R'):
    should = [r for r in asks[lane] if cands[r['item_id']]['should_ask']]
    shouldnt = [r for r in asks[lane] if not cands[r['item_id']]['should_ask']]
    right = sum(r['action'] == cands[r['item_id']]['question']['target'] for r in should)
    interrupt = [r['item_id'] for r in shouldnt if r['action'] in cands[r['item_id']]['question']['any_question_ids']]
    got = {r['item_id'] for r in asks[lane] if r['action'] in cands[r['item_id']]['question']['relevant_ask_ids']}
    used = [r for r in tests[lane] if r['category'] == 'Q' and r['item_id'] in got]
    print(f'  {lane}: 该问时问对 {right}/{len(should)}；不该问时打扰 {len(interrupt)}/{len(shouldnt)} {interrupt}；'
          f'拿到答案 {sorted(got)}；之后用对 {sum(r["ok"] for r in used)}/{len(used)}')

print('\n== 删除后（B_R）与同局面的 B_N ==')
n = {key(r): r for r in tests['B_N']}
follow = base = total = 0
for person in ('1', '2', '3'):
    for r in jsonl(raw / 'delete' / f'person{person}' / 'test' / 'decisions.jsonl'):
        ok = r['action'] == target_of(r)
        follow += ok
        base += n[key(r)]['ok']
        total += 1
        if ok:
            print(f'  仍跟随 {key(r)}：{r["output"]["reason"][:80]}')
print(f'  删除后跟随 {follow}/{total}，同局面 B_N {base}/{total}')
