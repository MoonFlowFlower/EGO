"""Recompute every score from the saved model output, without model judging."""
import json
from .corpus import OUT, rows
from .run import verify, FROZEN
from .scoring import grade, questions, timing, forgetting, reflex
from u3.common import write, sha, utc, budget_snapshot, cost
from .corpus import BASE


def noise_comparison(inputs, decisions, repeats):
    result = {}
    for domain in ('all', 'question', 'timing', 'forget'):
        ids = [i for i in repeats if i in decisions.get('D0_repeat', {}) and
               (domain == 'all' or inputs[i]['domain'] == domain)]
        within = [decisions['D0_repeat'][i]['score']['signature'] !=
                  grade(inputs[i], inputs[i]['historical']['output'])['signature'] for i in ids]
        entry = {'n': len(ids), 'D0_disagreements': sum(within),
                 'D0_rate': sum(within)/len(ids) if ids else None, 'judges': {}}
        for judge in ('D1', 'D2'):
            matched = [i for i in ids if i in decisions.get(judge, {})]
            disagreement = sum(decisions[judge][i]['score']['signature'] !=
                grade(inputs[i], inputs[i]['historical']['output'])['signature'] for i in matched)
            equivalent_noise = sum(decisions['D0_repeat'][i]['score']['signature'] !=
                grade(inputs[i], inputs[i]['historical']['output'])['signature'] for i in matched)
            entry['judges'][judge] = {'matched_n': len(matched), 'disagreements': disagreement,
                'rate': disagreement/len(matched) if matched else None,
                'D0_disagreements_same_subset': equivalent_noise,
                'withhold_attribution': not matched or len(matched) != len(ids) or disagreement <= equivalent_noise}
        result[domain] = entry
    return result


def report():
    manifest = verify()
    inputs = {i['id']: i for i in rows(OUT / 'INPUTS.jsonl')}
    decisions, summaries = {}, {}
    for judge in manifest['judges']:
        records = rows(OUT / 'raw' / judge / 'decisions.jsonl')
        if len(records) != len({r['id'] for r in records}):
            raise ValueError('duplicate_decision')
        for row in records:
            recomputed = grade(inputs[row['id']], row['output'])
            if row['score'] != recomputed:
                raise ValueError('score_mismatch:' + judge + ':' + row['id'])
        decisions[judge] = {r['id']: r for r in records}
        if judge == 'D0_repeat':
            continue
        data = [{'input': inputs[r['id']], 'score': r['score']} for r in records]
        summaries[judge] = {'completed': len(records), 'planned': 567,
            'questions': questions([r for r in data if r['input']['domain'] == 'question']),
            'timing': timing([r for r in data if r['input']['domain'] == 'timing']),
            'forgetting': forgetting([r for r in data if r['input']['domain'] == 'forget']),
            'reflex': reflex(data)}
    noise = noise_comparison(inputs, decisions, manifest['D0_repeat_ids'])
    complete = all(s['completed'] == 567 for s in summaries.values()) and len(decisions['D0_repeat']) == 60
    conclusions = {}
    for judge in ('D1', 'D2'):
        summary = summaries[judge]
        passed = {name: summary[name]['passed'] for name in ('questions', 'timing', 'forgetting')}
        withheld = {name: noise[domain]['judges'][judge]['withhold_attribution']
                    for name, domain in [('questions', 'question'), ('timing', 'timing'), ('forgetting', 'forget')]}
        if summary['completed'] != 567 or len(decisions['D0_repeat']) != 60:
            conclusion = 'incomplete_no_conclusion'
        elif noise['all']['judges'][judge]['withhold_attribution']:
            conclusion = 'D0_variability_comparable_no_attribution'
        elif all(passed.values()) and not any(withheld.values()):
            conclusion = 'all_three_pass_judge_bottleneck_on_these_inputs'
        elif any(passed.values()):
            conclusion = 'partial_pass_handle_each_domain_separately'
        else:
            conclusion = 'no_domain_pass_method_work_still_needed_for_this_judge'
        conclusions[judge] = {'mechanical_passes': passed, 'withhold_domain_attribution': withheld,
                              'conclusion': conclusion}
    result = {'at_utc': utc(), 'manifest_sha256': sha(FROZEN), 'complete': complete,
        'judges': summaries, 'D0_variability': noise, 'conclusions': conclusions,
        'cost_usd': cost(BASE / 'charge_ids.jsonl'), 'daily_budget': budget_snapshot(),
        'claim_ceiling': manifest['claim_ceiling'],
        'transport_limit': 'D2 uses service sampling defaults because SIWC rejects temperature. This is a route+judge comparison.'}
    write(OUT / 'RESULTS.json', result)
    lines = ['# U4 换判断者', '', '完整结束。' if complete else '尚未完整结束，不下总判决。', '',
             '| 判断者 | 完成输入 | 提问（不该问） | 开口时机 | 忘掉 |', '|---|---:|---|---|---|']
    for judge, summary in summaries.items():
        mark = lambda k: '未完成' if not summary[k]['complete'] else ('通过' if summary[k]['passed'] else '不过线')
        lines.append(f"| {judge} | {summary['completed']}/567 | {mark('questions')} | {mark('timing')} | {mark('forgetting')} |")
    lines += ['', f"D0 重跑完成 {len(decisions['D0_repeat'])}/60；分项差异、原始计数和结论保留条件见 RESULTS.json。",
              '', '反先验该问只有 3 条，只作参考；校准层和反射指数只报告。D5 任一测试臂出现违规都不能通过。',
              '', 'D2 保留全部消息文字与 JSON schema，但接口不支持温度 0 与输出 token 上限；服务默认采样构成解释限制。',
              '', '未重新学习、整理或删除原存储。只能评价这批合成输入上的判断者与方法，不能说明她学会了什么。',
              '', f"新增美元费用：${result['cost_usd']:.8f}；当日本地共享账本：${result['daily_budget']['used_usd']:.8f}。"]
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    result = report()
    print(json.dumps({'complete': result['complete'], 'judges': {k: v['completed'] for k, v in result['judges'].items()},
                      'cost_usd': result['cost_usd']}, ensure_ascii=False))
