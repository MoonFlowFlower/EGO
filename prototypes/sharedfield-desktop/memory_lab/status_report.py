"""Summarize a finite campaign from its saved evidence; never call a model."""
import argparse
from collections import Counter
import json
import re
from .provider import ROOT, write_json


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def calibration_summary(directory):
    complete=(directory/'result.json').exists()
    if complete:
        result=read(directory/'result.json');cases=result['cases'];total=len(cases)
    else:
        result={};total=read(directory/'MANIFEST.json')['count']
        cases=[]
        for path in sorted(directory.glob('*.json')):
            value=read(path)
            if 'case' in value and 'expected' in value and 'audit' in value:cases.append(value)
    failures=[c for c in cases if c['expected']!=c['audit']['status']]
    return dict(complete=complete,passed=bool(complete and result.get('passed')),
                completed=len(cases),total=total,correct=len(cases)-len(failures),failures=failures,cases=cases)


def summarize(campaign):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', campaign):
        raise ValueError('Invalid campaign ID')
    state = read(ROOT / 'runs/campaigns' / campaign / 'status.json')
    profiles, smokes, calibrations, calls = [], [], [], []
    for batch in sorted((ROOT/'runs').glob(f'batch-{campaign}-*')):
        if not (batch/'PROFILE.json').exists():continue
        config=read(batch/'PROFILE.json');name=config['id']
        profiles.append({'id': name, 'batch':batch.name,'profile': config,
                         'probes': read(batch / 'probes.json') if (batch / 'probes.json').exists() else None})
        calls.extend(read(p) for p in sorted((batch / 'calls').glob('*.json')))
        for arm in ('baseline', 'memos', 'hindsight'):
            path = ROOT / 'runs' / ('smoke-'+arm+'-'+batch.name.removeprefix('batch-')) / 'result.json'
            if path.exists():
                result = read(path)
                smokes.append({'profile': name, 'batch':batch.name,'arm': arm, 'file': path.relative_to(ROOT).as_posix(),
                               'passed': bool(result.get('real_backend') and result.get('evidence')
                                              and result.get('restart_ok') and result.get('deleted_recall') == [])})
        for directory in sorted(batch.glob('calibration*')):
            if not directory.is_dir() or not any((directory/f).exists() for f in ('result.json','MANIFEST.json')):continue
            result=calibration_summary(directory)
            path=directory/('result.json' if result['complete'] else 'MANIFEST.json')
            calibrations.append(dict(profile=name,batch=batch.name,**result,
                                     file=path.relative_to(ROOT).as_posix()))
    heldout = {}
    for stage in ('memory', 'growth'):
        rows = [read(p) for p in (ROOT / 'runs').glob(f'{stage}-{campaign}-*/episodes/*/result.json')]
        heldout[stage] = sum(str(r.get('case', '')).startswith('heldout') for r in rows)
    return {'campaign': campaign, 'status': state['status'], 'stage': state['stage'],
            'real_model_simulated_life': True, 'usage': state['usage'],
            'saved_call_files': len(calls), 'saved_call_statuses': dict(Counter(c['status'] for c in calls)),
            'profiles': profiles, 'smokes': smokes, 'calibrations': calibrations,
            'heldout_completed': heldout, 'selection': None, 'ace_benefit': None,
            'history': state['history'],'revision':state.get('revision'),
            'memory_run':state.get('memory_run'),'growth_run':state.get('growth_run')}


def revision_report(report):
    usage=report['usage'];revision=report['revision']
    current=[c for c in report['calibrations'] if c['batch'].endswith('-'+revision)]
    lines=['# 桌宠记忆实验：评分范围修订结果', '',
        f"当前活动 **{report['campaign']} / {revision}**：**{report['status']}**，阶段 **{report['stage']}**。",
        '这是**真实模型调用下的模拟生活实验**；不代表真实长期陪伴或性格成长已经通过验收。','',
        '## 已交付', '',
        '- 先分类完整正文的事实/非事实/不确定片段，再复用Ragas拆解与NLI；分类片段必须逐字覆盖完整正文。纯意图和感受标记为非事实，不伪称已经验证内心状态。',
        '- 每个事实原文片段与拆解结果一起核验，防止非空拆解漏掉另一条虚构经历；空拆解也不能直接通过。分类仍依赖模型，不能因此保证永不漏检。',
        '- 校准冻结评分器与样本哈希；已暴露案例只作回归，另加独立新16例。答案不进模型，结果不回流行动或ACE。',
        '- 话语上下文修订将外层说话人、听话人、引语内人称与评测者视角作为明确输入元数据贯穿分类/拆解/核验；元数据不证明所述事件发生。',
        '- 显式修订归档旧失败，沿用同一Qwen3.5配置、新建批次与实验存档，复用原5000次累计账本；此前调用未清零。后续评分修订复用配置完全一致的兼容探针回执，未超过6次直接探针。',
        '- 独立代码复核发现并修复部分事实拆解遗漏；新样本由另一上下文独立编写，不是独立人工标注或真实用户样本。','',
        '## 实际证据', '', '| 项目 | 当前结果 |','|---|---|',
        f"| 全活动调用 | {usage['attempted_calls']}；状态 {usage['statuses']} |",
        f"| 已知回执费用 | USD {usage['known_cost_usd']:.8f}；另{usage['unknown_cost_calls']}次计费未知 |",
        f"| 后端冒烟 | {sum(c['passed'] for c in report['smokes'])}/{len(report['smokes'])}，含之前版本 |",
        f"| 正式记忆保留案例 | {report['heldout_completed']['memory']}/216 |",
        f"| 正式成长保留案例 | {report['heldout_completed']['growth']}/144 |", '',
        '离线验证见 `evidence/fragment-v4-final-tests.txt`（59通过、7隔离依赖跳过）与 `evidence/fragment-isolated-tests.txt`（14通过，含这7项）；审查记录与每版冻结清单在 `evidence/`。', '',
        '## 新版校准', '']
    if not current:lines+=['尚无完成的新版校准；不能宣称通过。']
    for c in current:
        lines += [f"- {c['profile']}：已完成 **{c['completed']}/{c['total']}**，其中 **{c['correct']}** 例匹配冻结标签。{'通过当前校准门槛' if c['passed'] else '未通过或未完成，正式比较不启动'}。原始证据：`{c['file']}`。"]
        data=c['cases']
        prefixes=['calibration-','blind-v2-','frame-v3-','fragment-v4-']
        active_prefix={'scope-v2':'blind-v2-','frame-v3':'frame-v3-','fragment-v4':'fragment-v4-'}.get(revision)
        for prefix in prefixes:
            group=[x for x in data if x['case'].startswith(prefix)]
            if not group:continue
            label='独立新例' if prefix==active_prefix else '已暴露回归 ('+prefix.rstrip('-')+')'
            lines += [f"  - {label}：{sum(x['expected']==x['audit']['status'] for x in group)}/{len(group)}。"]
        for failure in c['failures']:
            a=failure['audit']
            lines += [f"  - 失败 `{failure['case']}`：预期 {failure['expected']}，实际 {a['status']}。"]
            for statement in a.get('statements',[]):
                if statement.get('verdict')==0:lines += [f"    - {statement['statement']} —— {statement['reason']}"]
            if a.get('reason'):lines += [f"    - {a['reason']}"]
    post=ROOT/'evidence/frame-v3-outcome.json'
    if revision=='fragment-v4':
        lines += ['', '## 中断与标注复核', '',
            '第57例 fragment-v4-13 的事实核验收到 choices[0].error.code=502、finish_reason=error；供应商中止异常JSON输出。这是已收到的失败回执，不是429；没有自动重试或换模型。最后4例未完成。',
            '原始冻结标签精确匹配53/56；未解决的frame-v3-04为安全拒判（unresolved）。独立复核发现fragment-v4-09和11原正例无依据地把inventory等同背包，两条gold不适合作为无歧义正例。保留原标签与分数，另记勘误，不改为新的盲测通过。',
            'fragment-v4-11虽可因“背包”附加信息被拒绝，核验理由却忽略真实成功eat回执与hunger=0，仍是独立的核验理由错误。',
            '此前三处片段组装误拒在本轮均通过。此结果支持该局部修复，不支持整体语义底线已经通过。',
            '补充修复只涉及嵌套供应商失败的持久记账和部分结果展示；真实受测评分器未改。证据：`evidence/fragment-v4-outcome.json`、`evidence/fragment-v4-adjudication.md`、`evidence/fragment-v4-failure-reconciliation.json`。']
    if post.exists() and revision=='frame-v3':
        outcome=read(post)
        lines += ['', '## 真实测试后的离线修复', '',
            '三处误拒均涉及相邻事实片段被当作独立完整主张：例如“你说过：”与后面的引语分开核验。已用确定性组装保留相邻事实片段的上下文，并增加先失败后通过的组件回归。',
            '**此后续修复只有离线证据，没有追加真实模型校准；上面的41/44属于修复前冻结版本，不能宣称当前版本已通过44例。**',
            '证据：`evidence/fragment-isolated-tests.txt`、`evidence/fragment-main-tests.txt`。真实受测源码快照：`evidence/semantic-frame-v3-tested.py`；版本与分组结果：`evidence/frame-v3-outcome.json`。']
    lines += ['', '## 结论与边界', '']
    pending=ROOT/'evidence/receipt-v5-offline.json'
    live=ROOT/'runs/batch-reliability-01-qwen35-receipt-v5-diagnostic/RESULT.json'
    if live.exists() and revision=='fragment-v4':
        diagnostic=read(live)
        lines += [f"receipt-v5一次配对机制诊断已结束：{diagnostic.get('matched',0)}/{len(diagnostic['cases'])}符合预注册标签。新评分器源码与8个输入预冻结；这不是独立盲测或全校准。",
                  '4个真实成功动作被识别；缺失、失败、删除回执负例被拒绝。但仅写信声称吃梨被错判为吃过，理由还虚构库存减少。故成功条件失败，不能担任虚构动作的独立硬验收门槛。',
                  '新增24次请求均有回执；旧502批次保留，已恢复停止状态。停止自动提示修补和付费重跑。下一项仅做有界离线验收协议审查，未改变既有门槛。详见 `evidence/receipt-v5-adjudication.md`、`evidence/receipt-v5-live-outcome.json`。']
        review=ROOT/'evidence/acceptance-protocol-review.json'
        if review.exists():
            decision=read(review)
            lines += [f"最新离线协议审查已完成：`ACCEPTANCE_PROTOCOL_REVIEW.md`。自动化{decision['automation_status']}，状态{decision['status']}；本轮新增模型调用0。",
                      '建议仅开展12开发场景×3底座的有限行为探索，保留语义待验收、不触碰保留测试、不正式排名或运行ACE；备选全量独立人工正文复核需审阅资源。两者均待用户选择，未改变原验收协议。上述“下一项审查”为此前历史安排。']
    elif pending.exists() and revision=='fragment-v4':
        lines += ['新增离线修订 receipt-v5：正式执行链原先没有填充专门回执字段，而校准链有；现从有效action_result事件提取带来源的成功/失败回执。另修复ok:false样本被放入成功回执字段的接口错误。7项针对性测试与7项隔离Ragas组件测试通过。',
                  '**这些只有离线证据，当前评分器已变化，不能复用上方fragment-v4校准成绩。** 本轮新增付费调用0，累计仍446；旧502批次保持封存。详见 `RECEIPT_REVISION.md`、`evidence/receipt-v5-offline.json`。']
    if report['status']=='complete':
        for stage in ('memory','growth'):
            path=ROOT/'runs'/report[stage+'_run']/'report.json'
            lines += [f"{stage} 正式报告：`{path.relative_to(ROOT).as_posix()}`。完整选型以该配对报告为准。"]
    else:
        lines += ['**尚无正式记忆选型或ACE收益结论。** 不把校准分数当成记忆效果，也不把回归测试通过当成完整桌宠完成。']
        if report['status']=='stopped' and report['stage']=='calibration' and revision!='fragment-v4':
            lines += ['本轮按照预定门槛停止，没有为通过新例子继续调提示或换模型挑分数。具体失败应先判断来自核验范围、语义拆解、证据表示还是NLI判断，再决定修订范围；未解决前不接入产品。']
    lines += ['', '方法依据：[VeriScore](https://aclanthology.org/2024.findings-emnlp.552/)区分可核验与不可核验内容；本地共同经历仍须核验，不能照搬其网页证据场景中排除私人经历的做法。[Ragas](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)继续承担事实支持性核验。本项目分层集成须以自己的校准结果判断。', '',
        '无付费调用重建报告：`.\\memory_lab\\.venv\\Scripts\\python.exe -B -m memory_lab.status_report --campaign reliability-01`。',
        '旧版报告保留于 `evidence/report-before-scope-v2.md`；活动历史、逐次原始调用、冻结清单与失败均保留。原SharedField运行时和个人存档不在本次修改范围。']
    (ROOT/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', default='reliability-01')
    args = parser.parse_args()
    report = summarize(args.campaign)
    write_json(ROOT / 'evidence/reliability-status.json', report)
    if report.get('revision'):
        revision_report(report)
        print(json.dumps({'status':report['status'],'stage':report['stage'],'usage':report['usage']},ensure_ascii=False))
        return
    if report['status'] != 'stopped' or report['stage'] != 'calibration':
        raise ValueError('This report template requires a campaign stopped at calibration')
    usage = report['usage']
    smoke_count = sum(s['passed'] for s in report['smokes'])
    calibrations = '\n'.join(f"| {c['profile']} / {c['file'].split('/')[-2]} | {c['correct']}/{c['total']} | {'通过' if c['passed'] else '未通过'} |" for c in report['calibrations'])
    text = f'''# 可靠性修订与实验状态报告

**可靠性代码和回归验证已交付；中文语义校准未通过，正式记忆与成长对照没有启动。当前不能选出记忆底座，也不能判断 ACE 是否改善行为。**

本报告是**真实模型调用下的模拟生活实验**。原桌宠目标、SharedField 运行时和个人存档不在本次修改范围。历史 batch-01 的208次调用和14个诊断轮次保留在旧报告 `evidence/report-before-reliability.md`，不混入本轮统计。

## 本轮实际结果

| 项目 | 证据与状态 |
|---|---|
| 活动 | {report['campaign']}，{report['status']}，停止于 {report['stage']} |
| 直接兼容性探针 | DeepSeek、Qwen3.7、Qwen3.5 各3次通过，回执检查模型和固定供应商 |
| 真实后端冒烟 | {smoke_count}/{len(report['smokes'])} 通过；每个模型下的基线、MemOS、Hindsight 写入、来源召回、重开和删除 |
| 真实调用 | {usage['attempted_calls']} 次；成功 {usage['statuses'].get('ok', 0)}，失败 {usage['statuses'].get('error', 0)}；跨模型累计，不重置5000次上限 |
| 回执已知费用 | USD {usage['known_cost_usd']:.8f}；另 {usage['unknown_cost_calls']} 次失败计费未知，不能记为零 |
| 正式记忆保留测试 | {report['heldout_completed']['memory']}/216，未启动 |
| 正式成长保留测试 | {report['heldout_completed']['growth']}/144，未启动 |

DeepSeek 与 Qwen3.7 均在校准时遇到429，活动封存对应批次、重建下一模型的基础材料，原回执保留。Qwen3.5 校准失败不是429，因此没有根据分数继续换 Gemini。没有混合模型统计，没有让评测答案进入行动或 ACE。

## 校准失败与一次有界修复

| 模型 / 校准目录 | 符合预期 | 结果 |
|---|---|---|
{calibrations}

第一次 Qwen3.5 校准发现集成缺陷：核验指令混入事实拆解，四个虚构陈述被拆成空列表；本项目适配器把空列表当成通过。上游 Ragas 对空列表返回 NaN，并不支持这样处理。已把拆解与支持性判断分开，空列表改为一次正文整体核验，并补回归测试。

保留原失败后，只对同一模型、同一累计预算执行了一次修复复验。12个校准例有11个符合预期；6个反例全部被拒绝，但一个正例“我准备去吃碗里的粥”被错误视作缺少事实依据。未来意图不应被当作已经完成的行动。**这不是语义底线通过，也不代表总体准确率已经估计。**

停止原因是评分器仍不适配中文生活表达，不能据此断言三个记忆方案无效。后续最有价值的工作是用新的盲测样本，独立验证意图、过去事实、虚构故事和不确定表达的区分；不能持续针对这12例调提示后宣称泛化。当前不再发起付费调用。

## 已实现及验证边界

- SQLite 原子保存动作结果、世界状态、约定、经历、步骤和待索引记录；恢复复用已完成动作和已收到的模型回执。写入与删除均持久排队，无法确认原生索引完整性时从有效来源重建。
- ACE 保留固定上游反思与新增经验组件；本地公共层补充条目版本、来源和依赖失效。派生内容保守依赖全部输入，可能连带失效无关条目；不宣称精确到句子的来源识别。
- 推理配置、实际模型回执、路由、评分缓存输入和冻结产物一致性检查已加入；显式429整批切换、未知计费停止、关闭活动禁止自动重启。
- Ragas 0.4.3 和兼容依赖在隔离环境中锁定，复用官方拆解/NLI提示与类型；计费运输和来源核验集成由本项目实现。模型裁判不是独立真值。
- 主环境52项测试：51通过、1项隔离依赖测试跳过；该项在评测环境单独执行通过。证据：`evidence/reliability-all-tests.txt`、`evidence/ragas-component-tests.txt`。MemOS 独立 TypeScript 与桥接语法检查通过。
- 独立代码复核指出回执重放、失效经验重新学习、删除交付丢失、评分缓存串用和原生克隆重试冲突五项问题；均已修复并回归。复核不代替真实完整对照。

原 SharedField 的 memory-store 源码绑定指纹与原验证记录一致；650个实验文本文件未检出授权密钥，研究端口关闭。收尾证据见 `evidence/reliability-closeout.json`。

上述中断注入主要在离线可控环境验证，真实后端冒烟不等于每个真实数据库中断点都已验证。没有本轮完整候选费用/延迟/资源比较，没有真实换机、长期陪伴或人格成长验收。结构化约定已覆盖；自然聊天识别、改约与取消仍是后续桌宠端到端任务。

## 上游证据与采用边界

- [AWS 事务发件箱](https://docs.aws.amazon.com/en_en/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)：成熟模式仍要求消费者去重，本地实现有回归证据。
- [FActScore](https://aclanthology.org/2023.emnlp-main.741/) 与 [Ragas Faithfulness](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/)：支持事实拆解与核验方法；本项目中文校准尚未通过。
- [ACE 论文](https://arxiv.org/abs/2510.04618)报告任务收益；锁定代码只有新增操作实际执行，本地补失效管理；本项目尚无真实成长收益结论。
- [LongMemEval](https://arxiv.org/abs/2410.10813)提供更新、时间推理和拒绝虚构的测试参考；不直接证明主动履约或陪伴体验。

固定提交、中文检索模型、许可证与依赖见 `upstream-lock.json`、`model-revisions.json`、锁文件和 `licenses/`。采用状态分为上游报告、代码已有实现、本项目实测，互不替代。

## 复现与接续

- 原始请求、回执、失败与费用：`runs/batch-{args.campaign}-*/calls/`；活动总账：`runs/campaigns/{args.campaign}/status.json`。
- 校准逐例证据：上述校准目录的 `result.json`；机器可读汇总：`evidence/reliability-status.json`。
- 不调用模型重建本报告：`.\\memory_lab\\.venv\\Scripts\\python.exe -B -m memory_lab.status_report --campaign {args.campaign}`。
- 回归和部署入口见 `README.md`；实现任务状态见 `RELIABILITY_PLAN.md` 和根目录 `TASK_BOARD.md`。

**不作正式选型，不默认接入 ACE，不启动训练。** 研究服务已停止，持久数据与失败资料保留。新的有效比较需要先解决评分校准并重新冻结实现和评分版本；本次关闭活动不能自动重开，旧诊断和校准成绩不并入正式比较。
'''
    (ROOT / 'REPORT.md').write_text(text, encoding='utf-8')
    print(json.dumps({'status': report['status'], 'stage': report['stage'], 'usage': usage,
                      'smokes_passed': smoke_count, 'heldout_completed': report['heldout_completed']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
