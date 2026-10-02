"""Preselected representative seed-0 curves, no best-run selection."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10,3.7),sharey=True)
for ax,regime in zip(axes,('static','drift')):
    for arm,name in (('gru_fixed','A: fixed GRU'),('gru_mb_plastic','B: plastic GRU')):
        path=Path('evidence/summaries')/f'{arm}_{regime}_seed0_attempt0.json'
        if not path.exists():continue
        r=json.loads(path.read_text());curve=r['curve']
        val=[x for x in curve if 'development_mean' in x]
        ax.plot([x['generation'] for x in val],[x['development_mean'] for x in val],label=name)
    ax.set_title(f'{regime}, seed 0 (preselected)');ax.set_xlabel('Generation');ax.set_ylim(0,1);ax.grid(alpha=.2);ax.legend()
axes[0].set_ylabel('Development mean survival fraction')
fig.tight_layout();fig.savefig('evidence/e2_training_curves.png',dpi=180);plt.close(fig)
