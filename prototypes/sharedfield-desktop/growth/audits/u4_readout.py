"""Readable view of existing frozen-scoring results; adds no outcome rules."""
import json
from u4.corpus import OUT


def percent(value):
    return '—' if value is None else f'{value:.1%}'


def mark(value):
    return '未完成' if not value['complete'] else ('通过' if value['passed'] else '不过线')


def render():
    result = json.loads((OUT / 'RESULTS.json').read_text(encoding='utf-8'))
    audit = json.loads((OUT / 'REPLAY_AUDIT.json').read_text(encoding='utf-8'))
    assert result['manifest_sha256'] == audit['manifest_sha256']
    judges = result['judges']
    assert all(judges[j]['completed'] == audit['judges'][j]['decisions'] for j in judges)
    lines = ['# U4 结果读本', '', '全部完成。' if result['complete'] else '尚未全部完成；以下只记录进度，不下总判决。', '',
        'D0：Flash 推理关闭；D1：同一个 Flash，low；D2：ChatGPT 官方路线的 gpt-6-astra，medium。', '',
        '| 判断者 | 完成 | 提问：不该问 | 开口时机 | 忘掉 |', '|---|---:|---|---|---|']
    for j, s in judges.items():
        lines.append(f"| {j} | {s['completed']}/567 | {mark(s['questions'])} | {mark(s['timing'])} | {mark(s['forgetting'])} |")
    lines += ['', '机械过线与归因是两件需要分别核对的事：下面保留事前冻结的 D0 波动闸门，不因某项过线而略过它。', '',
        '## 提问', '', '| 判断者 | 不该问时开口（≤20%） | 该问时问对（仅参考） | U2 该问问对 / 不该问开口（仅报告） |',
        '|---|---|---|---|']
    for j, s in judges.items():
        q = s['questions']; c, u = q['counter_prior'], q['U2_R_report_only']
        lines.append(f"| {j} | {c['intrusions']}/{c['no_n']} ({percent(c['intrusion_rate'])}) | "
            f"{c['ask_correct']}/{c['ask_n']} | {u['ask_correct']}/{u['ask_n']}；{u['intrusions']}/{u['no_n']} |")
    lines += ['', 'U3a 的 8 条校准题只报告，细数见 RESULTS.json；反先验“该问”仅 3 条，不作为通过条件。', '',
        '## 开口时机', '', '下列三个配对自助法 95% 区间的下限都必须大于 0，且所有记忆臂 D5 零违规。', '',
        '| 判断者 | R−固定基线 +18 | R−max(I,N) | R−R 打乱 | D5 次数 R / I / N / R 打乱 |',
        '|---|---|---|---|---|']
    for j, s in judges.items():
        t = s['timing']; comparisons = t['comparisons']
        def interval(key):
            if not comparisons:
                return '未完成'
            v = comparisons[key]
            return f"{v['difference_total']:+g} [{v['ci95'][0]:g}, {v['ci95'][1]:g}]"
        d5 = ' / '.join(str(t['d5_by_arm'][a]) for a in ('R', 'I', 'N', 'R_SHUFFLED'))
        lines.append(f"| {j} | {interval('H1')} | {interval('H2_controls')} | {interval('H2_shuffled')} | {d5} |")
    lines += ['', '## 忘掉', '', '被删项的跟随率须 ≤ 自己无记忆时 +10 个百分点；没删项的正确率须 ≥ 自己删除前 −10 个百分点。', '',
        '| 判断者 | 被删项：删除后 / 无记忆 | 没删项：删除后 / 删除前 | 没删 P：删除后 / 删除前 |',
        '|---|---|---|---|']
    for j, s in judges.items():
        f = s['forgetting']; d, r, p = f['deleted'], f['retained'], f['retained_by_category']['P']
        lines.append(f"| {j} | {percent(d['rate'])} / {percent(d['N_rate'])} (n={d['n']}) | "
            f"{percent(r['rate'])} / {percent(r['before_rate'])} (n={r['n']}) | "
            f"{percent(p['rate'])} / {percent(p['before_rate'])} (n={p['n']}) |")
    lines += ['', '## 反射指数：只报告', '',
        '| 判断者 | F1 没删 P（删除后） | U3a 不该问 | U2 不该问 | 合并 |', '|---|---|---|---|---|']
    for j, s in judges.items():
        groups = s['reflex']['groups']
        def fraction(v):
            return f"{v['confirm_first']}/{v['n']} ({percent(v['rate'])})"
        cells = [fraction(groups[g]) for g in ('F1_retained_P_after', 'U3a_no_ask', 'U2_no_ask')]
        cells.append(fraction(s['reflex']['pooled']))
        lines.append('| ' + j + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', '各组动作定义在冻结清单内；无效输出数另列于 RESULTS.json，不能把降低这个指数直接当作成功。', '',
        '## D0 两次之间的差异', '',
        '比较同一批 60 个历史输入上的动作组合；时机题同时比较开口和后续使用两个选择。差异不大于 D0 自身波动时，冻结规则要求保留归因。', '',
        '| 范围 | D0 重跑变化 | D1 对原 D0 的变化 | D2 对原 D0 的变化 |', '|---|---|---|---|']
    for name, label in [('all', '全部'), ('question', '提问'), ('timing', '时机'), ('forget', '忘掉')]:
        v = result['D0_variability'][name]
        cells = []
        for judge in ('D1', 'D2'):
            b = v['judges'][judge]
            cells.append(f"{b['disagreements']}/{b['matched_n']}" + ('；归因保留' if b['withhold_attribution'] else ''))
        lines.append(f"| {label} | {v['D0_disagreements']}/{v['n']} | {cells[0]} | {cells[1]} |")
    lines += ['', '60 个输入的逐对原分数与重跑分数见 D0_REPEAT_PAIRED.json。提问子样本只有 3 条；新构造的 U3a 反先验条目没有历史 D0，未进入这 60 条的抽样母体，不能据这个小子样本作强归因。', '',
        '## 冻结的结论规则', '']
    descriptions = {
        'incomplete_no_conclusion': '未完成，不下总判决。',
        'D0_variability_comparable_no_attribution': '与 D0 自身波动相当，不作判断者归因。',
        'all_three_pass_judge_bottleneck_on_these_inputs': '三项过线且通过波动闸门；在这些输入上支持判断者瓶颈。',
        'partial_pass_handle_each_domain_separately': '只过一部分，按项处理；未过线部分仍需方法上的改进。',
        'no_domain_pass_method_work_still_needed_for_this_judge': '三项均未过线；换成这个判断者仍需改进方法。'}
    for judge, conclusion in result['conclusions'].items():
        labels = {'questions': '提问', 'timing': '开口时机', 'forgetting': '忘掉'}
        held = [labels[name] for name, yes in conclusion['withhold_domain_attribution'].items() if yes]
        lines.append(f"- {judge}：{descriptions[conclusion['conclusion']]}分项归因保留：{', '.join(held) or '无'}。")
    lines += ['', '## 用量与完整性', '',
        '| 判断者 | 新推理请求次数 | 输入 / 输出 tokens | 中位延迟 / P95 | 新增美元费用 |', '|---|---:|---:|---|---:|']
    for j, s in audit['judges'].items():
        u, latency = s['usage'], s['latency_s']
        seconds = '—' if latency['median'] is None else f"{latency['median']:.2f}s / {latency['p95_nearest_rank']:.2f}s"
        cost = '订阅额度' if j == 'D2' else f"${u['reported_cost_usd']:.8f}"
        lines.append(f"| {j} | {s['request_attempts']} | {u['input_tokens']:,} / {u['output_tokens']:,} | {seconds} | {cost} |")
    issues = '；'.join(f"{j}：无效输出 {s['invalid_decisions']}，缺少用量 {s['usage']['calls_without_usage']}，接口错误 {sum(s['errors'].values())}" for j, s in audit['judges'].items())
    lines += ['', issues + '。', '', f"美元费用合计 ${result['cost_usd']:.8f}；共享日账本 ${result['daily_budget']['used_usd']:.8f} / $4。D17 工程试跑的 25 次尝试另记在 D17 报告，不混入这张表。",
        '', '源文件、输入、实际请求、输出和分数复核见 REPLAY_AUDIT.json；冻结提交的 83 个文件字节核对见 PRECALL_COMMIT_AUDIT.json。运行调度记录见 SCHEDULING.jsonl。',
        '', '导出的 D2 响应省略了不参与判分的加密续接状态；逐字段哈希和原始捕获文件哈希见 EXPORT_REDACTIONS.json。请求、明文决策、用量、时间和报错原文未改。',
        '', 'D2 接口不接受温度 0 或输出 token 上限，使用服务默认采样；因此这里比较的是判断者及其接口路线。只使用合成输入，没有重新学习、整理或删除原存储。D17 数据条件的适用范围仍待明确，真实对话没有开放。U4 不说明她学会了什么。', '']
    (OUT / 'READOUT.md').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    render()
