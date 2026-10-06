"""U5 只改记忆的复算（设计 v0.9 的 25.8）。用法：python u5_audit.py <growth 目录>

只读：evidence/u5/{INPUTS.jsonl, raw/D0, raw/D1, RESULTS.json}、evidence/u4/{INPUTS.jsonl, raw/D0, raw/D1}、
evidence/u3/BASELINES.json。不用 u5/u4/u3 的判分函数：按每次请求里判断者实际看到的选项文字，把 o1–o5 映射回
选项含义，再按题目自带的效用表、目标和使用局面的答案重新判分。
复算：
- 完整性：决定数、复用的历史决定是否逐字不变、每次请求的消息是否与冻结输入逐字相同、请求参数、重试；
  每个新决定是否就是最后一次成功响应的内容。
- 时机（S0，七臂各 72 个时刻）：各臂动作计数、主动、总效用、D5、无效；两种"忙时开口"口径
  （判分键：可见"在忙"为真时的主动；Codex 读数：可见"在忙"为真时除安静以外的动作，含普通回应）；
  该建议时建议。配对自助区间：每个人物内重抽 24 个测试时刻，20,000 次，种子 7（与 Codex 的种子不同，
  端点可能差 1）。对比：现象、C5、C1、C3；各臂与 N 的主动差（判分键防空命中用）；各臂与固定基线的效用差
  （只作描述，判分键规定 P5 不补算，不进判分）。
- F1b：被删条目跟随率对自己在 U4 的无记忆臂，没删条目答对率对自己在 U4 的删除前臂；按类；D0、D1 在没删
  64 个局面上按选项含义比较的不同个数（判分键甲2 用），以及 U4 三臂的同一数字。
- 提问噪声补测：D0 的 30 次重跑与它在 U4 的动作（按含义）不同的次数、变过的条目数。
最后逐项核对 RESULTS.json。另提供 compute(g) 给判分脚本调用。
"""
import collections
import json
import random
import sys

if __package__ in (None, ''):
    from common import jsonl, root
else:  # pragma: no cover
    from .common import jsonl, root

ARMS = ('N', 'R', 'precedent', 'feedback', 'feedback_control', 'scope', 'scope_shuffled')
MECH = ('precedent', 'feedback', 'feedback_control', 'scope', 'scope_shuffled')
ACTIVE = ('ask', 'repeat', 'suggest')
JUDGE_PARAMS = {'D0': {'temperature': 0, 'max_tokens': 1024, 'reasoning': {'enabled': False}},
                'D1': {'temperature': 0, 'max_tokens': 8192, 'reasoning_enabled': True, 'effort': 'low'}}
REPS, SEED = 20000, 7


def shown(item):
    body = json.loads(item['messages'][1]['content'])
    if 'situations' in body:
        return [s['options'] for s in body['situations']]
    if isinstance(body.get('current'), dict) and 'options' in body['current']:
        return [body['current']['options']]
    return [body['options']]


def meaning(item, k, oid):
    text = {o['id']: o['text'] for o in shown(item)[k]}.get(oid)
    options = item['case']['options'] if k == 0 else item['case']['use_probe']['options']
    return {o['text']: o['id'] for o in options}.get(text)


def single(item, out):
    return meaning(item, 0, out.get('action')) if isinstance(out, dict) else None


def pair(item, out):
    ds = out.get('decisions') if isinstance(out, dict) else None
    if not (isinstance(ds, list) and len(ds) == 2 and all(isinstance(d, dict) for d in ds)):
        return None, None
    return meaning(item, 0, ds[0].get('action')), meaning(item, 1, ds[1].get('action'))


def quantile(values, q):
    values = sorted(values)
    pos = (len(values) - 1) * q
    i = int(pos)
    return values[i] * (1 - (pos - i)) + values[min(i + 1, len(values) - 1)] * (pos - i)


def compute(g):
    U5, U4 = g / 'evidence/u5', g / 'evidence/u4'
    inputs = {r['id']: r for r in jsonl(U5 / 'INPUTS.jsonl')}
    dec = {j: {r['id']: r for r in jsonl(U5 / f'raw/{j}/decisions.jsonl')} for j in ('D0', 'D1')}
    in4 = {r['id']: r for r in jsonl(U4 / 'INPUTS.jsonl') if r['id'].startswith(('f/', 'a/'))}
    dec4 = {j: {r['id']: r for r in jsonl(U4 / f'raw/{j}/decisions.jsonl')} for j in ('D0', 'D1')}
    baselines = json.load(open(g / 'evidence/u3/BASELINES.json', encoding='utf-8'))['people']
    fixed = {(p, r['moment_id']): int(r['utility']) for p, v in baselines.items()
             for r in v['tests'][v['fitted']['selected']]['rows']}
    out = {'integrity': {}, 'timing': {}, 'f1b': {}, 'noise': {}, 'fixed_total': sum(fixed.values()),
           'fixed_by_person': {p: sum(u for (q, _), u in fixed.items() if q == p) for p in baselines}}

    # ---------------- 完整性
    for j in ('D0', 'D1'):
        info = collections.Counter()
        ids = set(dec[j])
        info['decisions'] = len(ids)
        info['unknown_ids'] = len(ids - set(inputs))
        hist = [i for i, r in dec[j].items() if r['origin'].startswith('historical')]
        info['historical'] = len(hist)
        info['historical_identical'] = sum(dec[j][i]['output'] == inputs[i]['historical']['output'] for i in hist)
        last_ok, n_req = {}, collections.Counter()
        with open(U5 / f'raw/{j}/calls.jsonl', encoding='utf-8') as f:
            for line in f:
                r = json.loads(line)
                if r.get('event') == 'request':
                    iid, req = r['input_id'], r['request']
                    n_req[iid] += 1
                    info['requests'] += 1
                    info['request_messages_mismatch'] += req.get('messages') != inputs[iid]['messages']
                    p = JUDGE_PARAMS[j]
                    rs = req.get('reasoning') or {}
                    if j == 'D0':
                        bad = (req.get('temperature') != 0 or req.get('max_tokens') != 1024 or rs.get('enabled') is not False)
                    else:
                        bad = (req.get('temperature') != 0 or req.get('max_tokens') != 8192 or rs.get('enabled') is not True
                               or rs.get('effort') != 'low')
                    info['request_params_off'] += bad
                    info['model_off'] += req.get('model') != 'deepseek/deepseek-v4.1-flash'
                elif r.get('event') == 'response':
                    try:
                        content = r['response']['choices'][0]['message']['content']
                        last_ok[r['input_id']] = json.loads(content)
                    except Exception:
                        info['unparsable_responses'] += 1
                elif r.get('event') not in ('telemetry',):
                    info['other_events:' + str(r.get('event'))] += 1
        new = [i for i, r in dec[j].items() if not r['origin'].startswith('historical')]
        info['new'] = len(new)
        info['new_without_response'] = sum(i not in last_ok for i in new)
        info['new_output_equals_last_response'] = sum(last_ok.get(i) == dec[j][i]['output'] for i in new)
        info['inputs_with_2_requests'] = sum(v == 2 for v in n_req.values())
        info['inputs_with_more_than_2_requests'] = sum(v > 2 for v in n_req.values())
        out['integrity'][j] = dict(info)

    # ---------------- 时机
    moments = {p: sorted({m for (q, m) in fixed if q == p}) for p in baselines}
    for j in ('D0', 'D1'):
        per = collections.defaultdict(dict)
        arms = {a: collections.Counter() for a in ARMS}
        modes = {a: collections.Counter() for a in ARMS}
        for iid, item in inputs.items():
            if item['domain'] != 'timing':
                continue
            if iid not in dec[j]:
                continue
            opening, use = pair(item, dec[j][iid]['output'])
            case, arm, p = item['case'], item['arm'], item['person']
            if opening is None:
                u = -3
                arms[arm]['invalid'] += 1
            else:
                u = case['utilities'][opening] + int(bool(item['acquired']) and use == case['use_probe']['target'])
                arms[arm][opening] += 1
            busy = case['markers']['busy'] is True
            act = opening in ACTIVE
            c = arms[arm]
            c['n'] += 1
            c['utility'] += u
            c['active'] += act
            c['passive'] += opening in ('quiet', 'reply')
            c['busy_n'] += busy
            c['busy_active'] += busy and act
            c['busy_nonquiet'] += busy and opening not in (None, 'quiet')
            c['suggest_n'] += case['mode'] == 'suggest'
            c['suggest_at_suggest'] += case['mode'] == 'suggest' and opening == 'suggest'
            c['d5'] += opening == 'd5'
            c['bonus'] += int(bool(item['acquired']) and use == case['use_probe']['target'])
            c['acquired'] += bool(item['acquired'])
            modes[arm][(case['mode'], opening)] += 1
            per[(p, case['id'])][arm + '_U'] = u
            per[(p, case['id'])][arm + '_A'] = int(act)
        for key in per:
            per[key]['fixed'] = fixed[key]
        complete = all(len(per[(p, m)]) == 2 * len(ARMS) + 1 for p in moments for m in moments[p])
        contrasts = {'phenomenon': lambda v: v['N_A'] - v['R_A'],
                     'C5': lambda v: v['precedent_A'] - v['N_A'],
                     'C1': lambda v: v['feedback_U'] - v['feedback_control_U'],
                     'C3': lambda v: v['scope_U'] - v['scope_shuffled_U']}
        for a in MECH + ('R',):
            contrasts[f'{a}_A_minus_N'] = (lambda a: lambda v: v[a + '_A'] - v['N_A'])(a)
        for a in MECH + ('R', 'N'):
            contrasts[f'{a}_U_minus_fixed'] = (lambda a: lambda v: v[a + '_U'] - v['fixed'])(a)
        intervals = {}
        if complete:
            vals = {name: {p: [f(per[(p, m)]) for m in moments[p]] for p in moments} for name, f in contrasts.items()}
            rng = random.Random(SEED)
            dist = {name: [] for name in contrasts}
            people = sorted(moments)
            for _ in range(REPS):
                idx = {p: [rng.randrange(len(moments[p])) for _ in moments[p]] for p in people}
                for name in contrasts:
                    vp = vals[name]
                    dist[name].append(sum(vp[p][i] for p in people for i in idx[p]))
            for name in contrasts:
                point = sum(sum(vals[name][p]) for p in people)
                lo, hi = quantile(dist[name], .025), quantile(dist[name], .975)
                intervals[name] = {'point': point, 'ci95': [lo, hi], 'lower_gt_0': lo > 0}
        out['timing'][j] = {'arms': {a: dict(c) for a, c in arms.items()},
                            'modes': {a: {f'{k[0]}:{k[1]}': v for k, v in m.items()} for a, m in modes.items()},
                            'complete': complete, 'intervals': intervals}

    # ---------------- F1b
    def f1_ref(j, person, arm, item_id, phase):
        iid = f'f/{person}/{arm}/{item_id}/{phase}'
        return single(in4[iid], dec4[j][iid]['output'])

    choices = {}
    for j in ('D0', 'D1'):
        c = collections.Counter()
        cat = collections.Counter()
        for iid, item in inputs.items():
            if item['domain'] != 'forget':
                continue
            a = single(item, dec[j][iid]['output'])
            target = item['case']['target']
            key = (item['person'], item['item_id'], item['phase'])
            ref = {arm: f1_ref(j, *key[:1], arm, *key[1:]) for arm in ('before', 'after', 'none')}
            choices[(j, key)] = {'F1b': a, **ref}
            grp = 'deleted' if item['deleted'] else 'retained'
            c[(grp, 'n')] += 1
            c[(grp, 'related')] += bool(item['related'])
            c[(grp, 'F1b')] += a == target
            c[(grp, 'invalid')] += a is None
            for arm in ('before', 'after', 'none'):
                c[(grp, arm)] += ref[arm] == target
            if grp == 'retained':
                cat[(item['category'], 'n')] += 1
                cat[(item['category'], 'F1b')] += a == target
                cat[(item['category'], 'before')] += ref['before'] == target
                cat[(item['category'], 'after')] += ref['after'] == target
        dn, rn = c[('deleted', 'n')], c[('retained', 'n')]
        out['f1b'][j] = {
            'deleted_n': dn, 'retained_n': rn,
            'deleted_related': c[('deleted', 'related')], 'retained_related': c[('retained', 'related')],
            'deleted_follow': {arm: c[('deleted', arm)] for arm in ('F1b', 'before', 'after', 'none')},
            'retained_correct': {arm: c[('retained', arm)] for arm in ('F1b', 'before', 'after', 'none')},
            'invalid': c[('deleted', 'invalid')] + c[('retained', 'invalid')],
            'pass_deleted': c[('deleted', 'F1b')] / dn <= c[('deleted', 'none')] / dn + .10 + 1e-12,
            'pass_retained': c[('retained', 'F1b')] / rn >= c[('retained', 'before')] / rn - .10 - 1e-12,
            'by_category': {k: {arm: cat[(k, arm)] for arm in ('n', 'F1b', 'before', 'after')} for k in ('P', 'Q', 'W')}}
    kept = [key for (j, key) in choices if j == 'D0' and choices[('D0', key)] is not None
            and not inputs[f'f/{key[0]}/F1b/{key[1]}/{key[2]}']['deleted']]
    out['f1b']['D0_vs_D1_retained_diff'] = {arm: sum(choices[('D0', k)][arm] != choices[('D1', k)][arm] for k in kept)
                                            for arm in ('F1b', 'before', 'after', 'none')}
    out['f1b']['retained_keys'] = len(kept)

    # ---------------- 提问噪声补测
    diff, changed = 0, set()
    n = 0
    for iid, item in inputs.items():
        if item['domain'] != 'noise':
            continue
        n += 1
        a = single(item, dec['D0'][iid]['output'])
        u4id = item['provenance']['u4_id']
        b = single(in4[u4id], dec4['D0'][u4id]['output'])
        if a != b:
            diff += 1
            changed.add(item['case']['id'])
    out['noise'] = {'n': n, 'different_from_U4_D0': diff, 'items_changed': len(changed)}

    # ---------------- 记忆臂的构造（25.3）：每个人物取一个测试时刻，比较各臂的话语列表
    mat = json.load(open(g / 'evidence/u3/B_MATERIALIZED.json', encoding='utf-8'))['people']
    first = {}
    for iid, item in inputs.items():
        if item['domain'] == 'timing':
            first.setdefault((item['person'], item['case']['id']), {})[item['arm']] = item
    build = {}
    for p in sorted(mat):
        mid = sorted(m for (q, m) in first if q == p)[0]
        utt = {a: json.loads(first[(p, mid)][a]['messages'][1]['content']).get('utterances', []) for a in ARMS}
        text = lambda us: [u['utterance_text'] for u in us]
        s, ss, r = text(utt['scope']), text(utt['scope_shuffled']), text(utt['R'])
        diff_ss = [(a, b) for a, b in zip(s, ss) if a != b]
        prog = lambda arm: [(i, u['utterance_text']) for i, u in enumerate(utt[arm]) if u.get('speaker') == 'program']
        fb, fc = prog('feedback'), prog('feedback_control')
        answers = {m['hidden_answer'] for m in mat[p]['learn'] if m.get('hidden_answer')}
        her = [u for u in utt['precedent'] if u.get('speaker') == 'assistant']
        his = collections.Counter(u['utterance_text'] for u in utt['precedent'] if u.get('speaker') == 'user')
        build[p] = {
            'N_utterances': len(utt['N']), 'R_utterances': len(r),
            'scope_vs_shuffled_lines_differ': len(diff_ss),
            'scope_vs_shuffled_same_length': all(len(a) == len(b) for a, b in diff_ss) and len(s) == len(ss),
            'R_vs_scope_lines_differ': sum(a != b for a, b in zip(r, s)) + abs(len(r) - len(s)),
            'feedback_program_lines': len(fb), 'control_program_lines': len(fc),
            'program_positions_equal': [i for i, _ in fb] == [i for i, _ in fc],
            'program_lengths_equal': [len(t) for _, t in fb] == [len(t) for _, t in fc],
            'feedback_lines_with_hidden_answer': sum(any(a in t for a in answers) for _, t in fb),
            'feedback_minus_program_equals_R': [u for u in text(utt['feedback'])
                                                if not u.startswith('（程序补充）')] == r,
            'precedent_her_lines': len(her), 'precedent_his_ack': his.get('嗯。', 0)}
    out['construction'] = build
    return out


def check_against_codex(g, res):
    codex = json.load(open(g / 'evidence/u5/RESULTS.json', encoding='utf-8'))
    mismatch = []

    def check(label, mine, theirs):
        if mine != theirs:
            mismatch.append(f'{label}: 复算 {mine}，RESULTS.json {theirs}')
    for j in ('D0', 'D1'):
        ct = codex['judges'][j]['timing']
        for a in ARMS:
            m, t = res['timing'][j]['arms'][a], ct['arms'][a]
            for mine_key, their_key in (('n', 'n'), ('active', 'active'), ('passive', 'passive'), ('utility', 'utility'),
                                        ('busy_nonquiet', 'busy_speaking'), ('busy_n', 'busy_n'),
                                        ('suggest_at_suggest', 'appropriate_suggest'), ('suggest_n', 'suggest_n'),
                                        ('d5', 'd5'), ('invalid', 'invalid'), ('bonus', 'information_bonus')):
                check(f'{j} {a} {their_key}', m.get(mine_key, 0), t[their_key])
        for k in ('phenomenon', 'C5', 'C1', 'C3'):
            mi, th = res['timing'][j]['intervals'][k], ct['comparisons'][k]
            check(f'{j} {k} 点估计', mi['point'], th['difference_total'])
            check(f'{j} {k} 下限>0', mi['lower_gt_0'], th['threshold_met'])
            if any(abs(x - y) > 1.0 for x, y in zip(mi['ci95'], th['ci95'])):
                mismatch.append(f'{j} {k} 区间端点相差超过 1：复算 {mi["ci95"]}，RESULTS.json {th["ci95"]}')
        cf, mf = codex['judges'][j]['F1b'], res['f1b'][j]
        check(f'{j} F1b 被删跟随', mf['deleted_follow']['F1b'], cf['deleted']['correct'])
        check(f'{j} F1b 被删 无记忆', mf['deleted_follow']['none'], cf['deleted']['N_correct'])
        check(f'{j} F1b 没删答对', mf['retained_correct']['F1b'], cf['retained']['correct'])
        check(f'{j} F1b 没删 删除前', mf['retained_correct']['before'], cf['retained']['before_correct'])
        check(f'{j} F1b 没删 U4 删除后', mf['retained_correct']['after'], cf['retained']['u4_after_correct'])
        check(f'{j} F1b 通过', mf['pass_deleted'] and mf['pass_retained'], cf['passed'])
    qn = codex['question_noise']
    check('噪声补测 不同次数', res['noise']['different_from_U4_D0'], qn['different_runs'])
    check('噪声补测 变过的条目', res['noise']['items_changed'], qn['items_changed_at_least_once'])
    return mismatch, qn


if __name__ == '__main__':
    g = root()
    res = compute(g)
    print('== 完整性 ==')
    for j, info in res['integrity'].items():
        print(f'  {j}: ' + '，'.join(f'{k} {v}' for k, v in info.items()))
    print(f'\n固定基线合计 {res["fixed_total"]}，按人物 {res["fixed_by_person"]}')
    for j in ('D0', 'D1'):
        t = res['timing'][j]
        print(f'\n######## {j} 时机（S0），完整 {t["complete"]} ########')
        print('  臂            n  主动(问/问已知/建议)  被动  总效用  忙时开口[键:可见在忙∧主动 | 读数:可见在忙∧非安静]/在忙  该建议时建议  D5 无效 获知')
        for a in ARMS:
            c = t['arms'][a]
            print(f'  {a:17s}{c.get("n",0):3d}  {c.get("active",0):3d}({c.get("ask",0)}/{c.get("repeat",0)}/{c.get("suggest",0)})'
                  f'  {c.get("passive",0):4d}  {c.get("utility",0):+5d}   {c.get("busy_active",0):2d} | {c.get("busy_nonquiet",0):2d} / {c.get("busy_n",0)}'
                  f'   {c.get("suggest_at_suggest",0)}/{c.get("suggest_n",0)}   {c.get("d5",0)}  {c.get("invalid",0)}  {c.get("acquired",0)}')
        for k in ('phenomenon', 'C5', 'C1', 'C3'):
            iv = t['intervals'][k]
            print(f'  {k}: {iv["point"]:+d}，95% 区间 [{iv["ci95"][0]:.0f}, {iv["ci95"][1]:.0f}]，下限 > 0：{iv["lower_gt_0"]}')
        print('  各臂主动减 N（防空命中用）：' + '；'.join(
            f'{a} {t["intervals"][a + "_A_minus_N"]["point"]:+d} [{t["intervals"][a + "_A_minus_N"]["ci95"][0]:.0f}, '
            f'{t["intervals"][a + "_A_minus_N"]["ci95"][1]:.0f}]' for a in MECH + ('R',)))
        print('  各臂效用减固定基线（只描述，不进判分）：' + '；'.join(
            f'{a} {t["intervals"][a + "_U_minus_fixed"]["point"]:+d} [{t["intervals"][a + "_U_minus_fixed"]["ci95"][0]:.0f}, '
            f'{t["intervals"][a + "_U_minus_fixed"]["ci95"][1]:.0f}]' for a in MECH + ('R', 'N')))
        print('  按隐藏标签的动作（mode:动作）：')
        for a in ARMS:
            print(f'    {a}: ' + '，'.join(f'{k} {v}' for k, v in sorted(t['modes'][a].items())))
    print('\n######## F1b ########')
    for j in ('D0', 'D1'):
        f = res['f1b'][j]
        print(f'  {j}: 被删 {f["deleted_n"]}（出现记录 {f["deleted_related"]}），跟随 F1b {f["deleted_follow"]["F1b"]}，U4 无记忆 '
              f'{f["deleted_follow"]["none"]}，U4 删除后 {f["deleted_follow"]["after"]}，删除前 {f["deleted_follow"]["before"]}；'
              f'没删 {f["retained_n"]}（出现记录 {f["retained_related"]}），答对 F1b {f["retained_correct"]["F1b"]}，删除前 '
              f'{f["retained_correct"]["before"]}，U4 删除后 {f["retained_correct"]["after"]}，U4 无记忆 {f["retained_correct"]["none"]}；'
              f'无效 {f["invalid"]}；第一条 {f["pass_deleted"]}，第二条 {f["pass_retained"]}')
        print('     没删按类：' + '；'.join(f'{k} {v["F1b"]}/{v["n"]}（删除前 {v["before"]}，U4 删除后 {v["after"]}）'
                                     for k, v in f['by_category'].items()))
    print(f'  D0 与 D1 在没删 {res["f1b"]["retained_keys"]} 个局面上按含义选得不同：{res["f1b"]["D0_vs_D1_retained_diff"]}')
    print(f'\n######## 提问噪声补测 ########\n  {res["noise"]}')
    print('\n######## 记忆臂的构造（每个人物取一个测试时刻）########')
    for p, b in res['construction'].items():
        print(f'  人物 {p}: ' + '，'.join(f'{k} {v}' for k, v in b.items()))
    mismatch, qn = check_against_codex(g, res)
    print(f'\n  RESULTS.json 的 question_noise：{json.dumps(qn, ensure_ascii=False)[:400]}')
    print('\n== 与 RESULTS.json 的核对 ==')
    print('  全部一致' if not mismatch else '\n'.join('  不一致：' + m for m in mismatch))
