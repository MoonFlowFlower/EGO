"""U4 换判断者的复算（设计 v0.9 的 24.8）。用法：python u4_audit.py <growth 目录>

只读 evidence/u4/INPUTS.jsonl、evidence/u4/raw/{D0,D0_repeat,D1,D2}/decisions.jsonl、evidence/u4/RESULTS.json、
evidence/u3/BASELINES.json。不用 u4/scoring.py 和 u2/u3 的判分函数：先按每次请求里判断者实际看到的选项文字，
把 o1–o5 映射回选项含义，再按题目自带的目标、效用表和使用局面的答案重新判分。
复算：提问（反先验"不该问"时开口、"该问"时问对、校准层、U2 现场提问）；时机（四臂总效用、D5、主动与被动的次数、
三个配对自助区间，每个人物内重抽 24 个时刻，20,000 次，种子 7，与 Codex 的种子不同，数值应非常接近）；
忘掉（被删跟随率对自己无记忆时，没删正确率对自己删除前）；反射指数；D0 重跑噪声与各判断者对原 D0 的差异；
D2 的 R 与 N 被动率之差的配对区间（判分键 K5 用）。最后逐项核对 RESULTS.json。
"""
import collections
import json
import random

from common import jsonl, root

g = root()
U4 = g / 'evidence/u4'
inputs = {r['id']: r for r in jsonl(U4 / 'INPUTS.jsonl')}
JUDGES = ('D0', 'D0_repeat', 'D1', 'D2')
dec = {j: {r['id']: r for r in jsonl(U4 / f'raw/{j}/decisions.jsonl')} for j in JUDGES}
codex = json.load(open(U4 / 'RESULTS.json', encoding='utf-8'))
ARMS = ('R', 'I', 'N', 'R_SHUFFLED')
CONFIRM = '先确认你此刻想要哪一种。'
mismatch = []


def check(label, mine, theirs):
    if mine != theirs:
        mismatch.append(f'{label}: 复算 {mine}，RESULTS.json {theirs}')


def shown(item):
    body = json.loads(item['messages'][1]['content'])
    if 'situations' in body:
        return [s['options'] for s in body['situations']]
    if isinstance(body.get('current'), dict):
        return [body['current']['options']]
    return [body['options']]


def meaning(item, k, oid):
    text = {o['id']: o['text'] for o in shown(item)[k]}.get(oid)
    options = item['case']['options'] if k == 0 else item['case']['use_probe']['options']
    return {o['text']: o['id'] for o in options}.get(text)


def signature(j, iid):
    item, out = inputs[iid], dec[j][iid]['output']
    if item['domain'] == 'timing':
        pair = out.get('decisions') if isinstance(out, dict) else None
        if not (isinstance(pair, list) and len(pair) == 2):
            return (None, None)
        return tuple(meaning(item, k, d.get('action')) for k, d in enumerate(pair))
    return (meaning(item, 0, out.get('action')) if isinstance(out, dict) else None,)


sig = {j: {iid: signature(j, iid) for iid in dec[j]} for j in JUDGES}
print('== 完整性 ==')
for j in JUDGES:
    bad = sum(None in s for s in sig[j].values())
    print(f'  {j}: {len(sig[j])} 个决定，无效或映射不上 {bad}')
reused = [iid for iid, r in dec['D0'].items() if r['origin'] == 'historical']
same = sum(dec['D0'][iid]['output'] == inputs[iid]['historical']['output'] for iid in reused)
print(f'  D0 复用历史决定 {len(reused)} 个，与原始调用记录的输出逐字相同 {same} 个')

baselines = json.load(open(g / 'evidence/u3/BASELINES.json', encoding='utf-8'))['people']
fixed = {(p, r['moment_id']): int(r['utility']) for p, v in baselines.items()
         for r in v['tests'][v['fitted']['selected']]['rows']}
moments = {p: sorted(m for q, m in fixed if q == p) for p in baselines}
rng_seed = 7
ci = lambda xs: (sorted(xs)[500], sorted(xs)[19499])


def boot(per_moment, contrasts):
    rng, dist = random.Random(rng_seed), collections.defaultdict(list)
    for _ in range(20000):
        s = collections.Counter()
        for p, ms in moments.items():
            for m in [rng.choice(ms) for _ in ms]:
                for key, value in per_moment[(p, m)].items():
                    s[key] += value
        for name, f in contrasts.items():
            dist[name].append(f(s))
    return {name: ci(v) for name, v in dist.items()}


summary = {}
for j in ('D0', 'D1', 'D2'):
    print(f'\n######## {j} ########')
    S = sig[j]
    # ---- 提问
    rows = collections.defaultdict(lambda: collections.Counter())
    reflex = collections.Counter()
    for iid, item in inputs.items():
        if item['domain'] != 'question':
            continue
        a = S[iid][0]
        if item['kind'] == 'u3a':
            layer = '校准' if item['prior_aligned'] else '反先验'
            if item['case']['kind'] == 'ask':
                rows[layer]['该问'] += 1
                rows[layer]['问对'] += a == 'ask'
            else:
                rows[layer]['不该问'] += 1
                rows[layer]['开口'] += a is None or a in ('ask', 'repeat')
                reflex['U3a 不该问'] += a in ('ask', 'repeat')
                reflex['U3a 不该问 n'] += 1
        else:
            if item['should_ask']:
                rows['U2']['该问'] += 1
                rows['U2']['问对'] += a in item['case']['relevant_ask_ids']
            else:
                rows['U2']['不该问'] += 1
                rows['U2']['开口'] += a is None or a in item['case']['any_question_ids']
                reflex['U2 不该问'] += a in item['case']['relevant_ask_ids']
                reflex['U2 不该问 n'] += 1
    cp = rows['反先验']
    q_pass = cp['不该问'] == 10 and cp['开口'] / cp['不该问'] <= .2
    print(f'  提问：反先验不该问开口 {cp["开口"]}/{cp["不该问"]}（≤20% 过线：{q_pass}）；该问问对 {cp["问对"]}/{cp["该问"]}（只参考）；'
          f'校准 {rows["校准"]["问对"]}/{rows["校准"]["该问"]}；U2 该问问对 {rows["U2"]["问对"]}/{rows["U2"]["该问"]}，'
          f'不该问开口 {rows["U2"]["开口"]}/{rows["U2"]["不该问"]}')
    cq = codex['judges'][j]['questions']
    check(f'{j} 提问 反先验开口', cp['开口'], cq['counter_prior']['intrusions'])
    check(f'{j} 提问 过线', q_pass, cq['passed'])
    check(f'{j} 提问 U2 不该问开口', rows['U2']['开口'], cq['U2_R_report_only']['intrusions'])
    check(f'{j} 提问 U2 该问问对', rows['U2']['问对'], cq['U2_R_report_only']['ask_correct'])

    # ---- 时机
    per = collections.defaultdict(dict)
    acts = {arm: collections.Counter() for arm in ARMS}
    loss = {arm: collections.Counter() for arm in ARMS}
    d5 = collections.Counter()
    for iid, item in inputs.items():
        if item['domain'] != 'timing':
            continue
        opening, use = S[iid]
        case, arm, p = item['case'], item['arm'], item['person']
        u = case['utilities'][opening] + int(item['acquired'] and use == case['use_probe']['target'])
        per[(p, case['id'])][arm] = u
        per[(p, case['id'])][arm + '_passive'] = int(opening in ('quiet', 'reply'))
        acts[arm][opening] += 1
        if case['utilities'][opening] < 0:
            loss[arm][(case['mode'], opening)] += 1
        d5[arm] += opening == 'd5'
    for key in per:
        per[key]['fixed'] = fixed[key]
    tot = {arm: sum(v[arm] for v in per.values()) for arm in ARMS}
    base = sum(fixed.values())
    cis = boot(per, {'H1': lambda s: s['R'] - s['fixed'], 'H2a': lambda s: s['R'] - max(s['I'], s['N']),
                     'H2b': lambda s: s['R'] - s['R_SHUFFLED'],
                     'R−N 被动': lambda s: s['R_passive'] - s['N_passive']})
    point = {'H1': tot['R'] - base, 'H2a': tot['R'] - max(tot['I'], tot['N']), 'H2b': tot['R'] - tot['R_SHUFFLED']}
    t_pass = not any(d5.values()) and all(cis[k][0] > 0 for k in ('H1', 'H2a', 'H2b'))
    print(f'  时机：总效用 {tot}，固定基线 {base}；D5 {dict(d5)}')
    for k, label in (('H1', 'R − 固定基线'), ('H2a', 'R − max(I,N)'), ('H2b', 'R − R打乱')):
        print(f'    {label}：{point[k]}，95% 区间 {cis[k]}')
    print(f'    三项全过且 D5 为零：{t_pass}')
    for arm in ARMS:
        passive = acts[arm]['quiet'] + acts[arm]['reply']
        active = acts[arm]['ask'] + acts[arm]['repeat'] + acts[arm]['suggest']
        print(f'    {arm}: 被动 {passive}，主动 {active}（问 {acts[arm]["ask"]}、问已知 {acts[arm]["repeat"]}、'
              f'建议 {acts[arm]["suggest"]}），扣分来源（该有的方式, 动作）{dict(loss[arm])}')
    print(f'    R 与 N 的被动率之差（R {sum(v["R_passive"] for v in per.values())}，N {sum(v["N_passive"] for v in per.values())}）'
          f'的 95% 区间 {cis["R−N 被动"]}')
    ct = codex['judges'][j]['timing']
    check(f'{j} 时机 总效用', tot, ct['utility_by_arm'])
    check(f'{j} 时机 D5', dict(d5) if any(d5.values()) else {a: 0 for a in ARMS}, ct['d5_by_arm'])
    check(f'{j} 时机 过线', t_pass, ct['passed'])
    for k, ck in (('H1', 'H1'), ('H2a', 'H2_controls'), ('H2b', 'H2_shuffled')):
        check(f'{j} 时机 {k} 点估计', point[k], ct['comparisons'][ck]['difference_total'])
        check(f'{j} 时机 {k} 过线', cis[k][0] > 0, ct['comparisons'][ck]['passed'])

    # ---- 忘掉
    grid = collections.defaultdict(dict)
    for iid, item in inputs.items():
        if item['domain'] == 'forget':
            a = S[iid][0]
            grid[(item['person'], item['item_id'], item['phase'])][item['arm']] = (
                a == item['case']['target'], item['deleted'], item['category'],
                {o['id']: o['text'] for o in item['case']['options']}.get(a) == CONFIRM)
    c = collections.Counter()
    for key, arms in grid.items():
        group = '被删' if arms['after'][1] else '没删'
        cat = arms['after'][2]
        for arm in ('before', 'after', 'none'):
            c[(group, arm)] += arms[arm][0]
            if group == '没删':
                c[(cat, arm)] += arms[arm][0]
        c[(group, 'n')] += 1
        if group == '没删':
            c[(cat, 'n')] += 1
            if cat == 'P':
                reflex['F1 没删 P'] += arms['after'][3]
                reflex['F1 没删 P n'] += 1
    dn, rn = c[('被删', 'n')], c[('没删', 'n')]
    del_pass = c[('被删', 'after')] / dn <= c[('被删', 'none')] / dn + .10
    ret_pass = c[('没删', 'after')] / rn >= c[('没删', 'before')] / rn - .10
    print(f'  忘掉：被删跟随 {c[("被删", "after")]}/{dn}，自己无记忆 {c[("被删", "none")]}/{dn}（过线 {del_pass}）；'
          f'没删 {c[("没删", "after")]}/{rn}，自己删除前 {c[("没删", "before")]}/{rn}，'
          f'下降 {100 * (c[("没删", "before")] - c[("没删", "after")]) / rn:.1f} 个百分点（过线 {ret_pass}）')
    print('    没删按类：' + '；'.join(f'{k} {c[(k, "after")]}/{c[(k, "n")]}（删除前 {c[(k, "before")]}）'
                               for k in ('P', 'Q', 'W')))
    cf = codex['judges'][j]['forgetting']
    check(f'{j} 忘掉 被删', (c[('被删', 'after')], round(c[('被删', 'none')] / dn, 6)),
          (cf['deleted']['correct'], round(cf['deleted']['N_rate'], 6)))
    check(f'{j} 忘掉 没删', (c[('没删', 'after')], round(c[('没删', 'before')] / rn, 6)),
          (cf['retained']['correct'], round(cf['retained']['before_rate'], 6)))
    check(f'{j} 忘掉 过线', del_pass and ret_pass, cf['passed'])

    # ---- 反射指数
    pooled = reflex['F1 没删 P'] + reflex['U3a 不该问'] + reflex['U2 不该问']
    pooled_n = reflex['F1 没删 P n'] + reflex['U3a 不该问 n'] + reflex['U2 不该问 n']
    print(f'  反射指数：F1 没删 P {reflex["F1 没删 P"]}/{reflex["F1 没删 P n"]}，U3a 不该问 {reflex["U3a 不该问"]}/'
          f'{reflex["U3a 不该问 n"]}，U2 不该问 {reflex["U2 不该问"]}/{reflex["U2 不该问 n"]}，合并 {pooled}/{pooled_n}')
    check(f'{j} 反射 合并', pooled, codex['judges'][j]['reflex']['pooled']['confirm_first'])
    summary[j] = {'questions': q_pass, 'timing': t_pass, 'forgetting': del_pass and ret_pass}

print('\n== D0 重跑噪声与判断者差异（同一批 60 个历史输入，比较动作；时机比较开口和使用两个动作）==')
rep = list(dec['D0_repeat'])
withhold = {}
for dom in ('all', 'question', 'timing', 'forget'):
    ids = [i for i in rep if dom == 'all' or inputs[i]['domain'] == dom]
    noise = sum(sig['D0_repeat'][i] != sig['D0'][i] for i in ids)
    diffs = {j: sum(sig[j][i] != sig['D0'][i] for i in ids) for j in ('D1', 'D2')}
    for j in ('D1', 'D2'):
        withhold[(j, dom)] = diffs[j] <= noise
        name = {'all': 'all', 'question': 'question', 'timing': 'timing', 'forget': 'forget'}[dom]
        check(f'噪声 {dom} {j}', (diffs[j], noise), (codex['D0_variability'][name]['judges'][j]['disagreements'],
                                                     codex['D0_variability'][name]['D0_disagreements']))
    print(f'  {dom}: n={len(ids)}，D0 重跑变化 {noise}，D1 对原 D0 {diffs["D1"]}，D2 对原 D0 {diffs["D2"]}；'
          f'保留归因（不大于噪声）D1 {withhold[("D1", dom)]}，D2 {withhold[("D2", dom)]}')

print('\n== 结论（24.5，按冻结的噪声规则）==')
for j in ('D1', 'D2'):
    domains = {'questions': 'question', 'timing': 'timing', 'forgetting': 'forget'}
    passes = summary[j]
    held = {k: withhold[(j, v)] for k, v in domains.items()}
    print(f'  {j}：过线 {passes}；归因保留 {held}')
    check(f'{j} 结论 过线', passes, codex['conclusions'][j]['mechanical_passes'])
    check(f'{j} 结论 归因保留', held, codex['conclusions'][j]['withhold_domain_attribution'])
print(f'  D0：过线 {summary["D0"]}')

print('\n== 与 RESULTS.json 的核对 ==')
print('  全部一致' if not mismatch else '\n'.join('  不一致：' + m for m in mismatch))
