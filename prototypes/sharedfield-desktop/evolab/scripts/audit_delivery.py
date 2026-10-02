"""Read-only final audit. No training or environment/holdout episodes are run."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from evolab.statistics import decide
torch.set_num_threads(4)

expected_prereg = 'B0B8E3939A3CF22B1FB7071E576CAE8AA9EC71D93CC25D33635D131FCC15E082'
assert hashlib.sha256(Path('PREREG_E2.md').read_bytes()).hexdigest().upper() == expected_prereg
sha = hashlib.sha256(Path('configs/e2_frozen.yaml').read_bytes()).hexdigest()
assert sha == '134d90c1d7e935be720d73445784b488818c16744c8d29f98f177c97493e14a8'
records = [json.loads(p.read_text()) for p in Path('runs').glob('*_attempt*/status.json')]
assert len(records) == 20 and all(r['status'] == 'COMPLETE' for r in records)
assert len({(r['arm'], r['regime'], r['seed']) for r in records}) == 20
assert all(r['generation'] == 400 and r['config_sha256'] == sha for r in records)
for r in records:
    directory = Path('runs') / r['label']
    lines = [json.loads(line) for line in (directory / 'generations.jsonl').read_text().splitlines()]
    assert [line['generation'] for line in lines] == list(range(1, 401))
    final = torch.load(directory / 'final_mean.pt', weights_only=True)
    last = torch.load(directory / 'generation_0400.pt', weights_only=True)
    assert final['generation'] == last['generation'] == 400
    assert torch.equal(final['mean'], last['mean']) and torch.isfinite(final['mean']).all()

original_e0 = subprocess.check_output(['git', 'show', 'bf48b4a:prototypes/sharedfield-desktop/evolab/evidence/E0_ENV.md'])
assert Path('evidence/E0_ENV.md').read_bytes().startswith(original_e0)
original_board = subprocess.check_output(['git', 'show', 'ac8d3cf:prototypes/sharedfield-desktop/TASK_BOARD.md'])
prefix = '最新研究推进（2026-10-02）：EVOLAB-001A'.encode()
def protected_lines(data):
    return b''.join(line for line in data.splitlines(keepends=True) if not line.startswith(prefix))
assert protected_lines(original_board) == protected_lines(Path('../TASK_BOARD.md').read_bytes())

decision = json.loads(Path('evidence/e2_decision.json').read_text())
if decision['status'] == 'VALID':
    def tensor(regime, arm, conditions):
        return torch.stack([torch.stack([torch.load(Path('runs') / f'holdout_{regime}_{arm}_{s}_{cond}.pt',
                                                   weights_only=True) for cond in conditions]) for s in range(5)])
    recomputed = decide(tensor('drift', 'gru_fixed', ['drift_fast', 'drift_slow']),
                        tensor('drift', 'gru_mb_plastic', ['drift_fast', 'drift_slow']),
                        tensor('drift', 'gru_mb_frozen', ['drift_fast', 'drift_slow']),
                        tensor('static', 'gru_fixed', ['static_holdout']),
                        tensor('static', 'gru_mb_plastic', ['static_holdout']))
    assert all(decision[k] == v for k, v in recomputed.items())
    assert len(decision['rows']) == 120
    assert all(row['episodes'] == 1024 for row in decision['rows'])
else:
    assert decision['status'] == 'ENGINEERING_INVALID'
    assert not Path('runs/holdout_started.json').exists()
print(json.dumps({'status': 'PASS', 'runs': 20, 'generations_each': 400,
                  'final_mean_matches_generation_400': True,
                  'original_E0_bytes_preserved': True, 'protected_TASK_BOARD_bytes_preserved': True,
                  'config_sha256': sha, 'prereg_sha256': expected_prereg,
                  'decision_recomputed_from_saved_outcomes': decision['status'] == 'VALID'}, indent=2))
