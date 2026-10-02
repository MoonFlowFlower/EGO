"""Descriptive absolute survival curves, never a checkpoint/level selector."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

data = json.loads(Path('evidence/002A/f2_learnability.json').read_text())
levels = data['levels']
groups = [(a, w) for a in ('gru_fixed', 'gru_mb_plastic') for w in ('static', 'drift')]
colors = ['#1c6da8', '#d57425', '#24965a']
fig, axes = plt.subplots(len(levels), 4, figsize=(15, 3.1*len(levels)), squeeze=False,
                         sharex=True, sharey=True)
for i, level in enumerate(levels):
    for j, (arm, world) in enumerate(groups):
        ax = axes[i, j]
        for row in level['runs']:
            if (row['arm'], row['regime']) != (arm, world):
                continue
            c = colors[row['seed']]
            points = [p for p in row['curve'] if 'development_mean' in p]
            ax.plot([p['generation'] for p in points], [p['development_mean'] for p in points],
                    color=c, linewidth=1.3, alpha=.85)
            ax.scatter([row['generation']], [row['development']['survival']], color=c,
                       marker='D' if row['collapsed_at'] is not None and row['generation'] < 400 else 'o',
                       edgecolor='white', linewidth=.6, s=40, zorder=5)
        if world == 'static':
            ax.axhline(.5, color='#555555', linestyle=':', linewidth=.8)
        ax.set_ylim(0, 1.02); ax.set_xlim(0, 410)
        ax.grid(alpha=.18)
        ax.set_title(f"L{level['level']} | {'A' if arm == 'gru_fixed' else 'B'} | {world}")
        if j == 0:
            ax.set_ylabel('Survival fraction')
        if i == len(levels)-1:
            ax.set_xlabel('Generation')
        if not any((r['arm'], r['regime']) == (arm, world) for r in level['runs']):
            ax.text(.5, .5, 'Not completed', transform=ax.transAxes, ha='center')
fig.suptitle('EVOLAB-002A pilot: absolute development survival (no between-arm contrast)', fontsize=14)
handles = [Line2D([0], [0], color=c, label=f'Seed {s}') for s, c in enumerate(colors)]
handles += [Line2D([0], [0], color='black', marker='o', linestyle='', label='Final 512 episodes'),
            Line2D([0], [0], color='black', marker='D', linestyle='', label='Allowed collapse endpoint')]
fig.legend(handles=handles, loc='lower center', ncol=5, frameon=False)
fig.text(.5, .035, 'Lines: fixed 128 development episodes every 20 generations. Static dotted line: S=0.50.\n'
         'Drift gate uses feeding and first-drift survival, not a threshold on this survival curve.',
         ha='center', fontsize=9)
fig.tight_layout(rect=(0, .07, 1, .96))
fig.savefig('evidence/002A/pilot_survival_curves.png', dpi=150)
print('Saved descriptive pilot survival curves')
