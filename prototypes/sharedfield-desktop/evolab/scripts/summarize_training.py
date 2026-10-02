"""Describe already recorded lifetimes and clocks; never run new episodes."""
import json
from pathlib import Path

rows, temperatures, clocks = [], [], []
for path in sorted(Path('runs').glob('*_attempt*/status.json')):
    r = json.loads(path.read_text())
    if r['status'] != 'COMPLETE':
        raise RuntimeError('Wait for all runs to finish')
    survival = r['training_survival']
    # Round float32 normalized scores back to their integer step counts.
    lifetimes = [round(x * 1500) for x in survival]
    rows.append({'arm': r['arm'], 'regime': r['regime'], 'seed': r['seed'],
                 'minimum_lifetime_steps': min(lifetimes), 'maximum_lifetime_steps': max(lifetimes),
                 'mean_lifetime_steps': sum(lifetimes) / len(lifetimes),
                 'fraction_below_200_steps': sum(t < 200 for t in lifetimes) / len(lifetimes),
                 'fraction_exactly_150_steps': sum(t == 150 for t in lifetimes) / len(lifetimes),
                 'wall_seconds': r['wall_seconds']})
    for point in r['curve']:
        if 'gpu_telemetry_csv' in point:
            values = [float(x.strip()) for x in point['gpu_telemetry_csv'].split(',')]
            temperatures.append(values[0]); clocks.append(values[1])
assert len(rows) == 20
out = {'scope': 'post-run descriptive audit of recorded development outcomes; no new experiments',
       'rows': rows, 'temperature_C_range': [min(temperatures), max(temperatures)],
       'graphics_clock_MHz_range': [min(clocks), max(clocks)],
       'warning': 'Training drift first switches at 200..400. A lifetime below 200 proves no drift exposure; >=200 alone does not prove exposure.'}
Path('evidence/e2_training_diagnostics.json').write_text(json.dumps(out, indent=2), encoding='utf-8', newline='\n')
