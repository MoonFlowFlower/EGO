"""Read-only regrading and per-judge reporting; no evaluator model."""
import json
from .corpus import OUT, BASE, ARMS, ARM_NAMES, NOISE_IDS, rows
from .run import verify, FROZEN
from .scoring import grade, timing, forgetting
from .client import projection
from u3.common import ROOT, read, write, sha, utc, cost, budget_snapshot
from u4.scoring import grade as u4_grade


def report():
    manifest = verify()
    inputs = {i['id']: i for i in rows(OUT/'INPUTS.jsonl')}
    previous_inputs = {i['id']: i for i in rows(ROOT/'evidence/u4/INPUTS.jsonl')}
    previous = {j: {r['id']: r for r in rows(ROOT/f'evidence/u4/raw/{j}/decisions.jsonl')} for j in ('D0', 'D1', 'D2')}
    for judge, rs in previous.items():
        for identity, record in rs.items():
            assert record['score'] == u4_grade(previous_inputs[identity], record['output'])
    decisions, summaries = {}, {}
    for judge in ('D0', 'D1'):
        rs = rows(OUT/f'raw/{judge}/decisions.jsonl')
        assert len(rs) == len({r['id'] for r in rs})
        for r in rs:
            assert r['score'] == grade(inputs[r['id']], r['output'])
        decisions[judge] = {r['id']: r for r in rs}
        data = [{'input': inputs[r['id']], 'score': r['score']} for r in rs]
        t = timing([r for r in data if r['input']['domain'] == 'timing'])
        f = forgetting([r for r in data if r['input']['domain'] == 'forget'], previous[judge])
        summaries[judge] = {'completed': len(rs), 'planned': len(manifest['order'][judge]),
            'new_decisions': sum(r['origin'] == 'new' for r in rs),
            'reused_decisions': sum(r['origin'] != 'new' for r in rs), 'timing': t, 'F1b': f,
            'interpretation_stopped': not t['d5_zero_hard_gate']}
        write(OUT/f'RESULTS_{judge}.json', summaries[judge])
    noise = []
    for name in NOISE_IDS:
        original = previous['D0']['a/'+name]['score']['signature']
        reruns = [decisions['D0'].get(f'noise/{name}/{n}') for n in (1, 2, 3)]
        completed = [r for r in reruns if r]
        noise.append({'item_id': name, 'U4_D0_signature': original, 'completed': len(completed),
            'different_runs': sum(r['score']['signature'] != original for r in completed),
            'signatures': [r['score']['signature'] for r in completed],
            'invalid': sum(not r['score']['valid_output'] for r in completed),
            'U4_D1_differs': previous['D1']['a/'+name]['score']['signature'] != original,
            'U4_D2_differs': previous['D2']['a/'+name]['score']['signature'] != original})
    supplement = {'report_only': True, 'completed': sum(r['completed'] for r in noise),
        'different_runs': sum(r['different_runs'] for r in noise), 'planned_runs': 30,
        'items_changed_at_least_once': sum(r['different_runs'] > 0 for r in noise), 'planned_items': 10,
        'U4_D1_vs_D0': sum(r['U4_D1_differs'] for r in noise),
        'U4_D2_vs_D0': sum(r['U4_D2_differs'] for r in noise), 'items': noise,
        'U4_conclusion_unchanged': True}
    assert (supplement['U4_D1_vs_D0'], supplement['U4_D2_vs_D0']) == (3, 5)
    write(OUT/'QUESTION_NOISE.json', supplement)
    actual = cost(BASE/'charge_ids.jsonl')
    result = {'at_utc': utc(), 'manifest_sha256': sha(FROZEN),
        'complete': all(s['completed'] == s['planned'] for s in summaries.values()),
        'judges': summaries, 'question_noise': supplement, 'cost_usd': actual,
        'projection': projection(manifest, inputs, decisions, actual), 'daily_budget': budget_snapshot(),
        'claim_ceiling': manifest['claim_ceiling']}
    write(OUT/'RESULTS.json', result)
    lines = ['# U5 只改记忆', '', '完整结束。' if result['complete'] else '运行未完整结束；缺项不作完整结论。', '',
        '固定 U3 S0 的系统提示、测试局面、选项、格式和效用表，只由程序改记忆；没有重新学习。', '',
        '## F1b', '', '| 判断者 | 被删项：F1b / 无记忆 | 未删项：删除前 → U4 删除后 → F1b | 两条判据 |', '|---|---|---|---|']
    for judge, s in summaries.items():
        f = s['F1b']; d, r = f['deleted'], f['retained']
        mark = '未完成' if not f['complete'] else '通过' if f['passed'] else '未通过'
        if s['interpretation_stopped']:
            mark += '；D5闸门关闭，停止解释'
        lines.append(f'| {judge} | {d["correct"]}/{d["n"]} / {d["N_correct"]}/{d["n"]} | {r["before_correct"]} → {r["u4_after_correct"]} → {r["correct"]} / {r["n"]} | {mark} |')
    lines += ['', '相关性按冻结题目的 teaching_domain 精确判断：18 个被删局面相关，64 个未删局面不相关。真实使用中的话题判断误差未测。']
    for judge, s in summaries.items():
        t = s['timing']
        lines += ['', f'## {judge}：S0 机制', '', f'解释状态：`{t["interpretation"]}`。', '',
            '| 记忆臂 | 完成 | 主动 | 忙时开口 | 该建议时建议 | 总效用 | 距固定基线 +18 | D5 | 无效 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for arm in ARMS:
            a = t['arms'][arm]
            lines.append(f'| {ARM_NAMES[arm]} | {a["n"]}/72 | {a["active"]} | {a["busy_speaking"]}/{a["busy_n"]} | {a["appropriate_suggest"]}/{a["suggest_n"]} | {a["utility"]:+d} | {a["difference_from_fixed_18"]} | {a["d5"]} | {a["invalid"]} |')
        if t['comparisons']:
            lines += ['', '| 判据 | 差值 | 配对 95% 区间 | 结果 |', '|---|---:|---|---|']
            for key, c in t['comparisons'].items():
                status = ('成立' if c['threshold_met'] else '不成立') if key == 'phenomenon' else ('只报告' if c['established'] is None else '成立' if c['established'] else '不成立')
                lines.append(f'| {key} | {c["difference_total"]:+d} | {c["ci95"]} | {status} |')
    lines += ['', '主动计问、问已知、建议；忙时开口计有效主动作中除安静之外的动作，包含普通回应。无效主决定按原 U3 记 −3，不计为被动。', '',
        '## 提问噪声补测（只报告）', '',
        f'D0 {supplement["completed"]}/30 次完成；与 U4 不同 {supplement["different_runs"]}/30 次，至少变化一次 {supplement["items_changed_at_least_once"]}/10 条。并列对照：U4 D1 与 D0 不同 3/10，D2 为 5/10。U4 结论不改。', '',
        '## 证据边界', '',
        '原 R 三个人物的学习获知标记全为零，各臂使用加分相同且全为零。作用域标签只涉及原学习中的 4 条负反应。检验只覆盖这批合成材料，机制不成立不能推广为机制不存在；不说明她学会了什么。', '',
        f'新增费用 ${actual:.8f}；共享日账本 ${result["daily_budget"]["used_usd"]:.8f} / $4，未知预留 ${result["daily_budget"]["unknown_included_usd"]:.8f}。', '',
        '冻结清单 FROZEN.json；逐条输入 INPUTS.jsonl；逐次输出及程序分数 raw/；按判断者结果 RESULTS_D0.json 与 RESULTS_D1.json；补测 QUESTION_NOISE.json。']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'complete': result['complete'], 'counts': {j:s['completed'] for j,s in summaries.items()}, 'cost_usd': actual}))
    return result


if __name__ == '__main__':
    report()
