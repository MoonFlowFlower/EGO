"""Freeze E1-approved settings. Refuse to overwrite any existing frozen config."""
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
from evolab.config import Config, config_dict

expected = 'B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082'
assert hashlib.sha256(Path('PREREG_E2.md').read_bytes()).hexdigest().upper() == expected
c = config_dict(Config())
c['semantics'] = {
    'movement_cost': 'directional command, including wall attempts',
    'survival_steps': 'count step begun alive, including lethal step',
    'food_refractory': '20 subsequent steps ineligible; available on 21st',
    'drift_switch': 'step start when age >= next_switch',
    'plastic_action_trace': 'selected command; observation contains executed command',
    'initial_previous_action': 'all zeros',
    'random_draws': 'stable SHA256-derived separate CUDA generators; full horizon pre-generated',
    'validation': 'fixed 128 dev episodes every 20 generations; final 1024 different dev episodes',
    'training_validity': 'aggregate five seeds per arm/world; hierarchical CI must not overlap R',
    'budget_probe': 'B/drift/seed0 counts among the 20 runs',
    'holdout_gate': 'all 20 runs complete and engineering validity before accessing holdout',
}
raw = yaml.safe_dump(c, allow_unicode=True, sort_keys=True).encode()
target = Path('configs/e2_frozen.yaml')
with target.open('xb') as f:
    f.write(raw)
Path('configs/e1_dev.yaml').write_bytes(raw)
digest = hashlib.sha256(raw).hexdigest()
Path('configs/e2_frozen.sha256').write_bytes((digest + '\n').encode())
print(digest)
