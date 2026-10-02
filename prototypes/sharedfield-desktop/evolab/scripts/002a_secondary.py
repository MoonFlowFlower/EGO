"""CPU-only secondary description of already saved pilot evaluation tensors."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from evolab.v002.secondary import recovery_km
from evolab.v002.records import write_json

torch.set_num_threads(4)
data = json.loads(Path('evidence/002A/f2_learnability.json').read_text())
rows = []
for level in data['levels']:
    for run in level['runs']:
        raw = torch.load(Path('runs/002A/F2')/run['label']/'development.pt',
                         map_location='cpu', weights_only=True)
        valid = raw['start'] >= 0
        estimate = recovery_km(raw['duration'][valid].tolist(), raw['observed'][valid].tolist())
        estimate.pop('curve')  # event-level arrays remain in runs, not committed
        assert estimate['switches'] == run['development']['switches']
        assert estimate['censored'] == run['development']['censored']
        rows.append(dict(level=level['level'], arm=run['arm'], regime=run['regime'], seed=run['seed'],
                         good_food_mean=raw['good'].double().mean().item(),
                         bad_food_mean=raw['bad'].double().mean().item(),
                         collapsed_at=run['collapsed_at'], **estimate))
write_json('evidence/002A/pilot_secondary.json', dict(
    scope='Pilot development only; no holdout or ablation',
    method='Within each seed, Kaplan-Meier median over actual drift switches; right censored at death, horizon or superseding switch',
    caution='Censoring may be informative; descriptive only, not counterfactual post-mortem recovery or a decision criterion',
    reference='https://itl.nist.gov/div898/handbook/apr/section2/apr215.htm', rows=rows))
lines = ['# EVOLAB-002A 试跑次要指标', '',
         '只描述已有pilot开发回合，不是保留集或消融分析。每个种子独立统计；从未经历切换记为no_switches，中位数未降到50%记为not_reached。死亡、时限或下一次切换使未恢复事件右截尾。同一步切换并吃到好食物记0步；同一时刻的恢复先于截尾移出风险集。', '',
         '采用 [NIST所述的Kaplan–Meier乘积极限估计](https://itl.nist.gov/div898/handbook/apr/section2/apr215.htm)。死亡/下一次切换可能构成信息性截尾，因此只作描述，不推断死亡后的反事实恢复，不参与任何闸门或H1–H3判定。', '',
         '| level | arm | world | seed | good mean | bad mean | switches | censored | censor fraction | KM median steps | status | collapsed_at |',
         '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
for r in rows:
    frac = 'N/A' if r['censored_fraction'] is None else f"{r['censored_fraction']:.6f}"
    med = 'N/A' if r['km_median_steps'] is None else str(r['km_median_steps'])
    lines.append(f"| L{r['level']} | {r['arm']} | {r['regime']} | {r['seed']} | {r['good_food_mean']:.6f} | {r['bad_food_mean']:.6f} | {r['switches']} | {r['censored']} | {frac} | {med} | {r['median_status']} | {r['collapsed_at']} |")
Path('evidence/002A/PILOT_SECONDARY.md').write_text('\n'.join(lines)+'\n', encoding='utf-8', newline='\n')
print('Described', len(rows), 'saved pilot runs; no new episodes')
