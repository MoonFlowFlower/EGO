"""Render retained F2 evidence without selecting by between-arm differences."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evolab.v002.records import verify_protected


def main():
    verify_protected()
    data = json.loads(Path('evidence/002A/f2_learnability.json').read_text())
    lines = ['# EVOLAB-002A F2 可学性闸门 L', '',
             f"状态：{data['status']}；选定级：{data['selected_level']}。", '',
             f"累计GPU任务墙钟 {data.get('seconds', 0):.3f} 秒（含CPU调度、CUDA同步、检查点、评估和重测W）。预算21600秒。", '',
             f"完整400代预跑：{data.get('full_probe_seconds', '未完成')} 秒；四级规模规划估计：{data.get('projected_all_four_levels_seconds', '未验证')} 秒。", '',
             '固定毒性0.15。L0移动额外耗能0；L1累加7×7视野；L2累加σ=0.05、种群512；L3累加初始能量1.0。每级2臂×2世界×3种子，最终512个pilot开发回合。', '',
             '域pilot_train=420000、pilot_dev=430000，master_seed=20261002。两臂配对种子0–2，初始化与突变也含pilot域。每20代128固定开发回合仅用于日志；最终512回合generation标签1，与中途标签0隔离。没有保留集访问。', '',
             '首轮B/drift/seed0预先指定跑满400代实测；其他试跑在连续20代零标准差时允许提前结束并取该时刻均值。collapsed_at为第20代检测时刻。未用最佳检查点。标准差以float64计算，避免常数float32向量因归约舍入出现伪非零。适应度、OpenES秩和Adam均沿用001A。', '']
    thermal = []
    for level in data['levels']:
        lines += [f"## L{level['level']}", '',
                  f"配置：`configs/002a_pilot_L{level['level']}.yaml`。", '',
                  '| arm | world | seed | generations | collapsed_at | S | ate good ≥1 | survived first | good/bad mean | seconds |',
                  '|---|---|---:|---:|---:|---:|---:|---:|---|---:|']
        for row in level['runs']:
            m = row['development']
            lines.append(f"| {row['arm']} | {row['regime']} | {row['seed']} | {row['generation']} | {row['collapsed_at']} | {m['survival']:.9f} | {m['ate_good_fraction']:.9f} | {m['survived_first_fraction']:.9f} | {m['good_food_mean']:.6f}/{m['bad_food_mean']:.6f} | {row['seconds']:.3f} |")
            thermal.extend(row['thermal'])
        gate = level.get('gate')
        if gate:
            lines += ['', '| arm | world | seed-average S | ate good ≥1 | survived first | absolute gate |',
                      '|---|---|---:|---:|---:|---|']
            for group in gate['groups']:
                m = group['mean']
                lines.append(f"| {group['arm']} | {group['regime']} | {m['survival']:.9f} | {m['ate_good_fraction']:.9f} | {m['survived_first_fraction']:.9f} | {group['checks']} |")
            lines += ['', f"L{level['level']}通过：{gate['passed']}。"]
        else:
            lines += ['', '此级未完成，闸门未验证。']
        recheck = level.get('world_recheck')
        if isinstance(recheck, dict):
            lines += ['', f"W重测通过：{recheck['passed']}；各条件：" + str([(r['regime'], r['arm'], r['survival']) for r in recheck['rows']])]
            thermal.extend(r['thermal'] for r in recheck['rows'])
        else:
            lines += ['', 'W沿用F1：L0世界一致，L1视野和L2 ES改动不影响拥有全坐标的脚本基线，轨迹不变。']
        lines.append('')
    if thermal:
        temps = [t['temperature_c'] for t in thermal]
        clocks = [t['graphics_mhz'] for t in thermal]
        lines += [f'逐20代及运行首尾采样温度{min(temps):.0f}–{max(temps):.0f}°C，图形时钟{min(clocks):.0f}–{max(clocks):.0f}MHz；非连续峰值。', '']
    failures = []
    for path in sorted(Path('evidence/002A/pilot_summaries').glob('*.json')):
        record = json.loads(path.read_text())
        if record['status'] != 'COMPLETE':
            failures.append(record)
    lines += ['## 失败、预算与偏离', '']
    if data.get('error'):
        lines += ['阶段错误/停止记录：', '```text', data['error'], '```', '']
    for failure in failures:
        lines += [f"运行 `{failure['label']}`：{failure['status']}，{failure['seconds']:.3f}秒。",
                  '```text', failure['error'], '```', '']
    if not failures and not data.get('error'):
        lines += ['截至该报告，没有运行NaN、崩溃或失败重跑。', '']
    lines += ['逐代原始日志、检查点与逐回合指标保留在 `runs/002A/F2/`；提交的 `pilot_summaries/` 只含固定每20代摘要及最后指标。完整阶段索引 `f2_learnability.json`。', '',
              '只按上述绝对指标选择阶梯，没有查看B−A差值，没有增加阶梯之外的训练手段。正式矩阵、V、保留集、消融和H1–H3均未验证。', '']
    Path('evidence/002A/F2_LEARNABILITY.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    print(data['status'], data.get('seconds'), 'seconds')


if __name__ == '__main__':
    main()
