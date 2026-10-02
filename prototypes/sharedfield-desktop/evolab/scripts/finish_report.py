"""Add audited context to the generated report, using saved evidence only."""
import json
from pathlib import Path

decision = json.loads(Path('evidence/e2_decision.json').read_text())
diagnostics = json.loads(Path('evidence/e2_training_diagnostics.json').read_text())
audit = json.loads(Path('evidence/final_audit.json').read_text())
assert audit['status'] == 'PASS'
report_path = Path('evidence/E2_REPORT.md')
original = report_path.read_bytes()
Path('runs/E2_REPORT_generated.md').write_bytes(original)
addition = '\n\n## 执行核查与解释边界\n\n'
addition += '20/20次均完成400代，无训练NaN、崩溃、丢失或失败重跑。最终均值逐个与generation_0400.pt逐位比对通过；原始逐代日志各有400条连续代号。原E0失败记录和TASK_BOARD受保护段落逐字节核对通过。独立审计见 `final_audit.json`，置信区间与判定从保存的保留集结果重新计算一致（工程无效时不访问保留集）。\n\n'
addition += 'E0、E1证据分别见 `E0_ENV.md`、`E1_WORLD.md`；E1最终22测试通过。唯一一次实现测试修补为稳定排序参数错误，另修正了H的意外进食归因并加入测试；此前检查/自动审批失败均保留在PROGRESS。世界参数未调整，预注册未改，冻结后无救援调参。\n\n'
if decision['status'] == 'VALID':
    addition += '|训练世界|臂|保留集条件|S（5种子等权均值）|\n|---|---|---|---|\n'
    groups = sorted({(r['trained_regime'], r['arm'], r['condition']) for r in decision['rows']})
    for group in groups:
        rows = [r for r in decision['rows'] if (r['trained_regime'], r['arm'], r['condition']) == group]
        assert len(rows) == 5
        addition += f'|{group[0]}|{group[1]}|{group[2]}|{sum(r["mean"] for r in rows)/5:.9f}|\n'
    addition += f'\n主假设相对收益门槛δ={decision["delta"]:.9f}；静态门槛δ_static={decision["delta_static"]:.9f}。两种漂移条件始终等权，未按子条件挑结果。\n\n'

for arm in ('gru_fixed', 'gru_mb_plastic'):
    rows = [r for r in diagnostics['rows'] if r['arm'] == arm and r['regime'] == 'drift']
    fraction = sum(r['fraction_below_200_steps'] for r in rows)/5
    mean_life = sum(r['mean_lifetime_steps'] for r in rows)/5
    addition += f'- 漂移训练后的{arm}在独立开发回合中，平均寿命{mean_life:.3f}步，**{fraction:.3%}在200步前死亡**。\n'
addition += '\n训练漂移首次发生在200–400步。上述200步前死亡的回合没有经历训练式漂移，这限制了本实验对持续适应的覆盖。约150步与低耗能停留策略相符，但全体策略的行为机制未单独验证。按预注册给出的负结果不能扩展成“终生可塑性一般无效”，也不能证明GRU确实学会了上下文适应。H的高存活只证明特权手写控制能在该世界存活；不证明当前ES设置足以演化出同等技能。未追加救援实验。\n\n'
budget = json.loads(Path('evidence/e2_budget.json').read_text())
train_hours = sum(r['wall_seconds'] for r in diagnostics['rows'])/3600
eval_hours = decision.get('evaluation_wall_hours', 0)
addition += f'完整预跑{budget["pilot_seconds"]:.3f}秒，20次外推{budget["twenty_run_hours"]:.4f}小时；实际训练{train_hours:.4f}小时，为外推的{train_hours/budget["twenty_run_hours"]:.3f}倍。评估{eval_hours:.4f}小时，合计{train_hours+eval_hours:.4f}小时，未超24小时。这里计的是GPU任务墙钟，含CPU调度、同步、记录与统计，非GPU kernel独占时间。\n\n'
addition += f'长负载逐20代采样温度范围{diagnostics["temperature_C_range"]}°C，核心时钟范围{diagnostics["graphics_clock_MHz_range"]}MHz；驱动曾明确报告SW Thermal Slowdown Active，见 `e2_thermal.json`。软件为Python3.12.13、torch2.11.0+cu128/CUDA12.8，TF32关闭；完整依赖见requirements-evolab.txt。\n\n'
addition += '统计种子在查看保留集之前以 `configs/statistics_seeds.json`（提交61c1e38）披露；它记录既有固定规则，未修改分析。主配置SHA-256 `134d90c1d7e935be720d73445784b488818c16744c8d29f98f177c97493e14a8`；预注册SHA-256 `B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082`。\n\n'
addition += '![预先选定seed0的两臂训练曲线](e2_training_curves.png)\n\n'
if decision['status'] == 'VALID':
    addition += '![预先选定B/drift/seed0/episode0，drift_fast评估示例](e2_plastic_drift.gif)\n\n调质信号m仅作该个体的内部量显示，不作情感或主观状态解释。\n'
report_path.write_bytes(original + addition.encode())
