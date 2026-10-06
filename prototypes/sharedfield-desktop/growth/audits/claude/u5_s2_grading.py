"""探索线 S2 对 U5 的 20 条预测，照判分键判分（设计 v0.9 的 25.9）。用法：python u5_s2_grading.py <growth 目录>

判分键：仓库外的 explore/rounds/2026-10-06-S2-U5判分键.md，SHA-256
20946332c47896bb4d7379a85330245d8405bafc9f8638b1086422dd06a88747（PROGRESS 2026-10-06 存证）。
数字来自 u5_audit.compute()（独立复算，与 RESULTS.json 逐项一致）；区间按键的规定取读数 RESULTS.json 给的。
口径照键：主动 = 问、问已知、建议；忙时开口 = 可见标记"在忙"为真时的主动（不是读数里含普通回应的那个口径）；
该建议时建议 = 隐藏标签为"该建议"时选了建议。P5 不补算区间。
"""
import json

from common import root
from u5_audit import compute

HIT, MISS, NA = '命中', '落空', '不可判'


def combine(parts):
    verdicts = [v for v, _ in parts]
    if all(v == HIT for v in verdicts):
        return HIT
    if any(v == MISS for v in verdicts):
        return MISS
    return NA


def main():
    g = root()
    res = compute(g)
    codex = json.load(open(g / 'evidence/u5/RESULTS.json', encoding='utf-8'))
    T = {j: res['timing'][j]['arms'] for j in ('D0', 'D1')}
    CI = {j: codex['judges'][j]['timing']['comparisons'] for j in ('D0', 'D1')}
    F = res['f1b']
    d5 = {j: sum(T[j][a].get('d5', 0) for a in T[j]) for j in ('D0', 'D1')}
    phen = {j: CI[j]['phenomenon']['ci95'][0] > 0 for j in ('D0', 'D1')}
    not_affected = {j: CI[j]['phenomenon']['ci95'][0] <= 0 <= CI[j]['phenomenon']['ci95'][1] for j in ('D0', 'D1')}
    holds = lambda j, k: CI[j][k]['ci95'][0] > 0
    A = lambda j, arm: T[j][arm].get('active', 0)
    U = lambda j, arm: T[j][arm].get('utility', 0)
    cnt = lambda j, arm, act: T[j][arm].get(act, 0)
    busy = lambda j, arm: T[j][arm].get('busy_active', 0)
    sug_at = lambda j, arm: T[j][arm].get('suggest_at_suggest', 0)
    fmt = lambda j, k: f'{CI[j][k]["difference_total"]:+d} [{CI[j][k]["ci95"][0]:.0f}, {CI[j][k]["ci95"][1]:.0f}]'

    print('== 判分前核对 ==')
    print(f'  D0 的 S0 N：主动 {A("D0", "N")}（问 {cnt("D0", "N", "ask")}、问已知 {cnt("D0", "N", "repeat")}、建议 '
          f'{cnt("D0", "N", "suggest")}），忙时开口 {busy("D0", "N")}，该建议时建议 {sug_at("D0", "N")}，总效用 {U("D0", "N")}'
          '（键：42、10/21/11、14、5、−28）')
    print(f'  固定基线 {res["fixed_total"]}，按人物 {res["fixed_by_person"]}（键：18；9、3、6）')
    print(f'  U4 对照：没删 删除前 D0 {F["D0"]["retained_correct"]["before"]}、D1 {F["D1"]["retained_correct"]["before"]}；'
          f'删除后 {F["D0"]["retained_correct"]["after"]}、{F["D1"]["retained_correct"]["after"]}；无记忆 '
          f'{F["D0"]["retained_correct"]["none"]}、{F["D1"]["retained_correct"]["none"]}；被删无记忆跟随 '
          f'{F["D0"]["deleted_follow"]["none"]}/18、{F["D1"]["deleted_follow"]["none"]}/18；D0、D1 没删不同 '
          f'{F["D0_vs_D1_retained_diff"]}（键：62/62、49/55、34/36、1/18、2/18、4/12/7）')
    for j in ('D0', 'D1'):
        print(f'  {j}：D5 {d5[j]}；现象 {fmt(j, "phenomenon")}，成立 {phen[j]}，不受记忆影响 {not_affected[j]}')

    rows = []

    def add(code, parts, note=''):
        rows.append((code, combine(parts) if isinstance(parts, list) else parts, parts, note))

    # ---- Claude 3.1
    parts = []
    for j in ('D0', 'D1'):
        diff = U(j, 'scope') - U(j, 'scope_shuffled')
        floor = A(j, 'scope') <= 2 and A(j, 'scope_shuffled') <= 2
        if d5[j]:
            parts.append((NA, f'{j} D5'))
        elif floor or not_affected[j]:
            parts.append((NA, f'{j} 两臂主动 {A(j, "scope")}、{A(j, "scope_shuffled")}，都在地板上（≤2）'
                              if floor else f'{j} 不受记忆影响'))
        else:
            ok = abs(diff) <= 3 and CI[j]['C3']['ci95'][0] <= 0
            parts.append((HIT if ok else MISS, f'{j} 差 {diff:+d}，C3 {fmt(j, "C3")}'))
    add('U5-0a', parts, '若不计本键加的地板条件，两项本会命中（差 0、0）')
    parts = [((HIT if F[j]['retained_correct']['F1b'] >= 58 else MISS), f'{j} 没删 {F[j]["retained_correct"]["F1b"]}/64')
             for j in ('D0', 'D1')]
    add('U5-0b', parts)

    # ---- Claude 3.2（现象检查为前提）
    def gated(j):
        return d5[j] or not phen[j]

    add('乙1', [((NA if gated(j) else (HIT if holds(j, 'C5') else MISS)), f'{j} C5 {fmt(j, "C5")}') for j in ('D0', 'D1')])
    parts = []
    for j in ('D0', 'D1'):
        rn = cnt(j, 'N', 'repeat')
        cap = 0.3 * rn + 2
        rp = cnt(j, 'precedent', 'repeat')
        if gated(j):
            parts.append((NA, f'{j} 门槛'))
        elif rn < 6:
            parts.append((NA, f'{j} N 问已知 {rn} < 6，前提不成立'))
        elif A(j, 'precedent') <= cap:
            parts.append((NA, f'{j} 换先例整体主动 {A(j, "precedent")} 不超过上限 {cap:.1f}'))
        else:
            parts.append((HIT if rp <= cap else MISS, f'{j} 换先例问已知 {rp}，上限 {cap:.1f}（N 问已知 {rn}）'))
    add('乙2', parts)
    parts = []
    for j in ('D0', 'D1'):
        bn, bp = busy(j, 'N'), busy(j, 'precedent')
        c5_zero = CI[j]['C5']['ci95'][0] <= 0 <= CI[j]['C5']['ci95'][1]
        if gated(j):
            parts.append((NA, f'{j} 门槛'))
        elif bn < 3:
            parts.append((NA, f'{j} N 忙时开口 {bn} < 3，前提不成立（读数含普通回应的口径是 {T[j]["N"]["busy_nonquiet"]}，不用）'))
        elif c5_zero:
            parts.append((NA, f'{j} C5 区间含 0'))
        else:
            parts.append((HIT if bp >= bn else MISS, f'{j} 换先例忙时开口 {bp} ≥ N 的 {bn}？'))
    add('乙3', parts)
    parts = []
    for j in ('D0', 'D1'):
        sn, sf = cnt(j, 'N', 'suggest'), cnt(j, 'feedback', 'suggest')
        if gated(j):
            parts.append((NA, f'{j} 门槛'))
        elif sn < 6:
            parts.append((NA, f'{j} N 建议 {sn} < 6'))
        else:
            parts.append((HIT if sf <= 3 else MISS, f'{j} 全反馈建议 {sf}（N 建议 {sn}）'))
    add('乙4', parts)
    if gated('D0') or gated('D1'):
        add('甲1', NA)
    else:
        i = U('D1', 'feedback') - U('D0', 'feedback')
        add('甲1', [(HIT if i >= 6 else MISS, f'(i) 全反馈效用 D1 {U("D1", "feedback"):+d} − D0 {U("D0", "feedback"):+d} = {i:+d}'),
                   (HIT if holds('D1', 'C1') else MISS, f'(ii) D1 C1 {fmt("D1", "C1")}'),
                   (HIT if not holds('D0', 'C1') else MISS, f'(iii) D0 C1 {fmt("D0", "C1")}')])
    both_floor = (F['D0']['retained_correct']['F1b'] <= F['D0']['retained_correct']['none'] and
                  F['D1']['retained_correct']['F1b'] <= F['D1']['retained_correct']['none'])
    dd = F['D0_vs_D1_retained_diff']['F1b']
    add('甲2', [(NA, '两个判断者都不读记忆')] if both_floor else
        [(HIT if dd <= 7 else MISS, f'F1b 没删 64 个局面 D0、D1 选得不同 {dd}（门槛 7；没删答对 D0 '
          f'{F["D0"]["retained_correct"]["F1b"]} > 34、D1 {F["D1"]["retained_correct"]["F1b"]} > 36）')])
    add('丁1', [(HIT if A('D1', 'N') < 42 else MISS, f'D1 的 N 主动 {A("D1", "N")} < 42')])
    add('丁2', [((HIT if phen[j] else MISS), f'{j} 现象 {fmt(j, "phenomenon")}') for j in ('D0', 'D1')])
    add('戊1', [((NA if gated(j) else (HIT if holds(j, 'C1') else MISS)), f'{j} C1 {fmt(j, "C1")}') for j in ('D0', 'D1')])
    parts = []
    for j in ('D0', 'D1'):
        sf, sa = cnt(j, 'feedback', 'suggest'), sug_at(j, 'feedback')
        ok = sf >= 6 and sa / sf >= .6 if sf else False
        parts.append((NA if gated(j) else (HIT if ok else MISS), f'{j} 全反馈建议 {sf}，落在该建议时 {sa}（{sa / sf:.2f}）'
                      if sf else f'{j} 全反馈建议 0'))
    add('戊2', parts)
    pre = all(A(j, 'feedback') - A(j, 'feedback_control') >= 5 for j in ('D0', 'D1'))
    if not pre or gated('D0') or gated('D1'):
        add('戊3', [(NA, '前提不成立')])
    else:
        gap = abs(U('D0', 'feedback') - U('D1', 'feedback'))
        add('戊3', [(HIT if gap < 6 else MISS, f'|{U("D0", "feedback"):+d} − {U("D1", "feedback"):+d}| = {gap}（前提：多开口 D0 '
                     f'{A("D0", "feedback") - A("D0", "feedback_control")}、D1 {A("D1", "feedback") - A("D1", "feedback_control")}）')])

    # ---- Codex 第 3 节
    for code, j in (('P1a', 'D0'), ('P1b', 'D1')):
        f = F[j]
        p1 = f['deleted_follow']['F1b'] / 18 <= f['deleted_follow']['none'] / 18 + .10 + 1e-12
        p2 = f['retained_correct']['F1b'] / 64 >= f['retained_correct']['before'] / 64 - .10 - 1e-12
        add(code, [(HIT if p1 else MISS, f'被删跟随 {f["deleted_follow"]["F1b"]}/18（自己无记忆 {f["deleted_follow"]["none"]}/18）'),
                   (HIT if p2 else MISS, f'没删答对 {f["retained_correct"]["F1b"]}/64（自己删除前 {f["retained_correct"]["before"]}/64）')])
    add('P2', [(NA if gated('D1') else (HIT if holds('D1', 'C1') else MISS), f'D1 C1 {fmt("D1", "C1")}')])
    add('P3', [(NA if gated('D1') else (HIT if holds('D1', 'C3') else MISS), f'D1 C3 {fmt("D1", "C3")}')])
    add('P4', [(NA if gated('D0') else (HIT if not holds('D0', 'C5') else MISS), f'D0 C5 {fmt("D0", "C5")}')])
    for code, j in (('P5a', 'D0'), ('P5b', 'D1')):
        pts = '，'.join(f'{a} {U(j, a) - res["fixed_total"]:+d}' for a in ('precedent', 'feedback', 'feedback_control',
                                                                         'scope', 'scope_shuffled'))
        add(code, [(NA, f'读数只给点值（{pts}），没有区间；键规定不补算')])

    print('\n== 逐条 ==')
    tally = {}
    for code, verdict, parts, note in rows:
        tally[verdict] = tally.get(verdict, 0) + 1
        detail = '；'.join(f'{d}：{v}' for v, d in parts) if isinstance(parts, list) else ''
        print(f'  {code:6s} {verdict}  {detail}{"（" + note + "）" if note else ""}')
    print(f'\n  合计 {len(rows)} 条：' + '，'.join(f'{k} {v}' for k, v in tally.items()))
    by_author = {}
    for code, verdict, _, _ in rows:
        who = 'Codex' if code.startswith('P') else 'Claude'
        by_author.setdefault(who, {}).setdefault(verdict, 0)
        by_author[who][verdict] += 1
    print('  分作者：' + '；'.join(f'{w} ' + '，'.join(f'{k} {v}' for k, v in d.items()) for w, d in by_author.items()))

    # ---- Claude 3.3 的概率押注
    events = [('现象 D0', .97, phen['D0']), ('现象 D1', .85, phen['D1']),
              ('C5 D0', .75, holds('D0', 'C5')), ('C5 D1', .65, holds('D1', 'C5')),
              ('C1 D0', .30, holds('D0', 'C1')), ('C1 D1', .45, holds('D1', 'C1')),
              ('C3 D0', .05, holds('D0', 'C3')), ('C3 D1', .05, holds('D1', 'C3')),
              ('F1b D0', .75, F['D0']['pass_deleted'] and F['D0']['pass_retained']),
              ('F1b D1', .80, F['D1']['pass_deleted'] and F['D1']['pass_retained']),
              ('噪声 ≤3', .80, res['noise']['different_from_U4_D0'] <= 3)]
    brier = sum((p - int(o)) ** 2 for _, p, o in events) / len(events)
    print('\n== Claude 3.3 概率押注（不计命中）==')
    print('  ' + '；'.join(f'{n} {p} → {"发生" if o else "没发生"}' for n, p, o in events))
    print(f'  Brier 分 {brier:.4f}（{len(events)} 个事件；全押 0.5 的参照是 0.25）')
    conf = {'U5-0a': .9, 'U5-0b': .9, '乙1': .7, '乙2': .7, '乙3': .55, '乙4': .4, '甲1': .3, '甲2': .75, '丁1': .7,
            '丁2': .85, '戊1': .25, '戊2': .25, '戊3': .5}
    judged = [(c, conf[c], v == HIT) for c, v, _, _ in rows if c in conf and v != NA]
    b2 = sum((p - int(o)) ** 2 for _, p, o in judged) / len(judged)
    print(f'  第 3.1、3.2 节的把握对判出的 {len(judged)} 条：Brier 分 {b2:.4f}')


if __name__ == '__main__':
    main()
