"""Close a pre-formal stop using retained evidence; never evaluate new episodes."""
import json
import hashlib
from pathlib import Path


def nested_report(path):
    source = Path(path).read_text(encoding='utf-8').splitlines()
    if source and source[0].startswith('# '):
        source = source[2:]
    return '\n'.join('#'+line if line.startswith('#') else line
                     for line in source)


def main():
    folder = Path('evidence/002A')
    f2 = json.loads((folder/'f2_learnability.json').read_text())
    reasons = {
        'STOP_L_EXHAUSTED': '本卡无效：四级固定阶梯均未通过可学性闸门 L。在此预算内 ES 学不会 Room-v0（具体指两臂都达到本卡规定的觅食门槛）；停止，不进入正式实验。V 尚未测量。',
        'STOP_W_RECHECK_FAILED': 'L3 改变初始能量后的闸门 W 重测不通过；停止，不进入正式实验。',
        'STOP_PROJECTED_BUDGET': '完整预跑后的预计总耗时超过 F2 六小时预算；停止，等待用户决定。',
        'FAILED_OR_BUDGET_STOP': 'F2 遇到执行停止，具体原因见下方保留的错误记录。未完成的阶梯没有判为失败或通过；等待用户决定。',
    }
    if f2['status'] not in reasons:
        raise RuntimeError('Only a terminal pre-formal stop can produce this report')
    completed = [r for level in f2['levels'] for r in level['runs']]
    audit = json.loads((folder/'integrity_audit.json').read_text())
    assert audit['status'] == 'PASS'
    assert len(audit['pilot_runs_checked']) == len(completed)
    for name in ('F2_LEARNABILITY.md', 'PILOT_SECONDARY.md', 'pilot_survival_curves.png'):
        assert (folder/name).exists(), name
    hashes = {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
              for name in ('PREREG_002A.md', 'PREREG_E2.md', 'configs/e2_frozen.yaml')}
    early = [r for r in completed if r['generation'] < 400]
    projection_error = f2['seconds'] / f2['projected_all_four_levels_seconds'] - 1
    lines = ['# EVOLAB-002A 报告', '',
             f"执行状态：**{f2['status']}**。{reasons[f2['status']]}", '',
             '**没有形成可塑性正、部分或负结果。** 正式矩阵 F3、正式有效性 V、保留集、B0 消融及 H1–H3 均未验证。当前证据不足以支持或反驳终生可塑性的存活优势，也不能记为 X1 的科学负证据。', '',
             f"F0 已通过；F1 的 W 首次在 poison_cost=0.15 通过；F2 已完成 {len(completed)} 次试跑。F2 累计 GPU 任务墙钟 {f2.get('seconds', 0):.3f} 秒（{f2.get('seconds', 0)/3600:.4f} 小时），上限 21600 秒。此墙钟包含调度、同步、检查点和评估，并非纯 CUDA kernel 时间。", '',
             f"其中 {len(completed)-len(early)} 次跑满400代，{len(early)}次按坍缩规则提前结束，共 {sum(r['generation'] for r in completed)} 代。完整关闭摘要见 [closure_summary.json](closure_summary.json)。", '',
             '## 工程与可复现性', '',
             'Windows 原生，沿用 .venv、PyTorch 2.11.0+cu128 / CUDA 12.8、sm_120。001A 的回归完整测试集 33/33 通过（42.09秒）；新增闸门测试2项、恢复时间 CPU 单测4项分别通过。详见 [F0](F0_TESTS.md)、[次要分析测试](secondary_tests.json) 和 runs/002A 中对应日志。', '',
             '新实现位于 evolab/v002/；原世界步进与 OpenES 保持复用。001A 两臂的新进程五代重放逐位一致；两臂各抽取 drift/seed0 第400代均值在原开发集1024回合的结果逐位一致。001A 文件哈希、原 PROGRESS 后缀与任务板非 EVOLAB 行通过保护审计。002A 的整批400代跨进程重复运行未验证。', '',
             '首轮 F0 曾因共享 checkout 外部快进至 cf3666c、README 新增002A入口导致哈希测试失败；核对外部提交后只更新该保护基准，保留失败记录。未修改001A原代码、冻结配置、预注册或证据。', '',
             '| protected file | SHA-256 |', '|---|---|']
    lines += [f'| `{name}` | `{digest}` |' for name, digest in hashes.items()]
    lines += ['', '## 配置与选择规则', '',
              '没有通过 L 的最终采用配置，因此未生成正式冻结配置。开发配置逐级保存为 configs/002a_pilot_L*.yaml；每次运行摘要记录其SHA-256。F1选定毒性0.15（001A为0.05）；L0移动额外耗能0（原0.002）；L1视野7×7（原5×5）；L2 σ=0.05 / population=512（原0.02 / 256）；L3初始能量1.0（原0.6）。仅执行已启动的级，未跳级、未额外改适应度或增加训练手段。', '',
              '5×5视野时参数 A=18246、B=18254；7×7时 A=25926、B=25934。两种尺寸均通过参数预算匹配测试。所有试跑使用 master_seed=20261002 和独立 pilot 域，正式 master_seed=20261003 尚未使用。保留集入口仍被代码拒绝。', '',
              '每个完整运行只取第400代均值；允许的连续20代零方差坍缩试跑取检测时刻均值。没有按中途最高分选择，未用 B−A 差值决定阶梯。完整运行记录、坍缩和错误见下文。', '',
              '## 计时、热状态与偏离', '',
              f'完整预算探针为预先指定的 L0 B/drift/seed0：285.397秒。按各级种群倍数外推四级约5.708小时；实际总耗时比该粗估高 {projection_error:.2%}。该模型没有单独建模视野、存活长度和热状态；各次实测耗时见完整表格。', '',
              'F2中一次 nvidia-smi 明确记录 SW Thermal Slowdown Active；插电状态已只读核实。温度/时钟范围见下文，均为采样值，不代表连续峰值；驱动累计降频计数不能全部归因于本实验。未改变功耗或系统设置。', '',
              '固定示例 GIF 的512回合重放耗时91.215秒，与 L0 B/static/seed2 末段并行，占用已纳入F2墙钟；该训练运行耗时不作为独立吞吐基准。以后未再并行启动GPU辅助工作。GIF重放逐回合分数与原保存结果逐位一致。', '',
              '## 世界闸门完整数值', '',
              '以下保留F1完成时的阶段记录；其中后续计划反映当时状态。已实施的F2结果见下一节。', '',
              nested_report(folder/'F1_WORLD_GATE.md'), '',
              '## 可学性闸门完整数值', '', nested_report(folder/'F2_LEARNABILITY.md'), '',
              '## 次要分析', '', nested_report(folder/'PILOT_SECONDARY.md'), '',
              '## 可视证据', '',
              '![Pilot survival curves](pilot_survival_curves.png)', '',
              '曲线为固定128开发回合的每20代记录，最终点为512独立标签开发回合。显示各自的绝对存活比例；闸门同时检查进食和第一次漂移暴露，曲线本身不能替代闸门。', '',
              '![Fixed pilot B example](pilot_L0_B_drift_seed0.gif)', '',
              'GIF固定取 L0 B/drift/seed0 最终均值、开发回合0，没有按表现挑选。该回合存活300步、吃到2次好食物、0次坏食物，死亡前未经历漂移，因此不展示漂移后的适应。代理已检查画面和标注；用户人工目检未验证。', '',
              '## 本结果不能证明什么', '',
              'W只说明特权手写H与本卡规定的N/F对照满足数值要求，不能排除所有其他不适应策略。试跑失败只限制本卡世界、网络、OpenES及预算组合，不能推出演化策略普遍不可行，也不能推出可塑性无效。', '',
              '没有正式开发V结果、保留集效应量或置信区间，没有B0消融。不得把个别static成功种子、进食或GIF作为科学假设的证据；不得外推到桌宠或用户，不作生命、意识、情感或能动性声明。', '',
              '原始逐代日志、均值、优化器检查点和逐回合张量保留于 runs/002A/（不提交）；提交摘要JSON、报告与图像。证据一致性见 [integrity_audit.json](integrity_audit.json)。停止后的进一步训练或新方法须由用户决定。', '']
    (folder/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    print('Wrote pre-formal stop report:', f2['status'], len(completed), 'completed pilots')


if __name__ == '__main__':
    main()
