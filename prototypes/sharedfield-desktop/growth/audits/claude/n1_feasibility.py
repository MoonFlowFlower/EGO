"""N1 可行性粗算（设计 v0.9 的 26.3）。用法：python n1_feasibility.py <growth 目录>

只读 evidence/u3/B_MATERIALIZED.json 的学习时刻；测试时刻只读可见标记，用来核对覆盖，不读隐藏标签和效用（留给 N1）。
问题：一个只看得到自己动作后果的显式学习器，在每个人物 32 个学习时刻里，
按"没试过就试一次、试过就照结果做"的最简规则，要打扰几次、能把几种可见情境学对。"""
import collections, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
g = sys.argv[1]
mat = json.load(open(g + '/evidence/u3/B_MATERIALIZED.json', encoding='utf-8'))['people']
key = lambda m: tuple(m['markers'][f] for f in ('time_band', 'day_type', 'busy', 'topic_seen'))
APPROACH = ('ask', 'suggest')          # 来问一个以后用得上的问题 / 带着自己做的事来分享
for p in sorted(mat):
    learn = mat[p]['learn']
    combos = collections.Counter(key(m) for m in learn)
    tried = collections.defaultdict(dict)       # combo -> action -> 最近一次的效用
    welcome = annoy = 0
    for m in learn:
        k = key(m)
        known_good = [a for a, u in tried[k].items() if u > 0]
        untried = [a for a in APPROACH if a not in tried[k]]
        if known_good:
            a = known_good[0]
        elif untried:
            a = untried[0]
        else:
            a = 'quiet'
        u = m['utilities'][a]
        if a != 'quiet':
            tried[k][a] = u
            welcome += u > 0
            annoy += u < 0
    oracle = {}
    for m in learn:
        oracle[key(m)] = m['mode']
    learned_right = sum(1 for k, mode in oracle.items()
                        if (mode == 'hold' and not any(u > 0 for u in tried[k].values()))
                        or (mode in APPROACH and tried[k].get(mode, 0) > 0))
    test_combos = collections.Counter(key(m) for m in mat[p]['test'])
    print(f'人物 {p}: 学习时刻 {len(learn)}，可见组合 {len(combos)} 种（测试里 {len(test_combos)} 种，都在学习里出现：'
          f'{set(test_combos) <= set(combos)}），每种组合出现次数 {sorted(combos.values())}；'
          f'学习期 欢迎 {welcome}、打扰 {annoy}；学对的组合 {learned_right}/{len(oracle)}；隐藏标签分布 '
          f'{dict(collections.Counter(m["mode"] for m in learn))}')
