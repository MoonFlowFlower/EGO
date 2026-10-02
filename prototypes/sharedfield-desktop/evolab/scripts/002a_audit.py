"""Read-only integrity audit of 002A evidence and protected legacy bytes."""
import sys, json, subprocess, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from evolab.v002.records import verify_protected, write_json
from evolab.v002.gates import learnability

verify_protected()
prefix = 'prototypes/sharedfield-desktop/'
old = subprocess.check_output(['git', 'show', f'cf3666c:{prefix}evolab/PROGRESS.md'])
assert Path('PROGRESS.md').read_bytes().endswith(old[old.index(b'## '):])
before = subprocess.check_output(['git', 'show', f'cf3666c:{prefix}TASK_BOARD.md'])
after = Path('../TASK_BOARD.md').read_bytes()
def protected_lines(data):
    return [line for line in data.splitlines(keepends=True)
            if not line.startswith('最新研究推进（2026-10-02）：EVOLAB-'.encode())]
assert protected_lines(before) == protected_lines(after)
f1 = json.loads(Path('evidence/002A/f1_world_gate.json').read_text())
assert [l['poison_cost'] for l in f1['levels']] == [.05, .1, .15]
assert [l['passed'] for l in f1['levels']] == [False, False, True]
checked = []
path = Path('evidence/002A/f2_learnability.json')
if path.exists():
    f2 = json.loads(path.read_text())
    for level in f2['levels']:
        if level['gate']:
            assert learnability(level['runs'], 3) == level['gate']
        for run in level['runs']:
            directory = Path('runs/002A/F2')/run['label']
            config_bytes = Path(f'configs/002a_pilot_L{level["level"]}.yaml').read_bytes()
            assert hashlib.sha256(config_bytes).hexdigest() == run['config_sha256']
            records = [json.loads(line) for line in (directory/'generations.jsonl').read_text().splitlines()]
            assert [r['generation'] for r in records] == list(range(1, run['generation']+1))
            final = torch.load(directory/'final_mean.pt', map_location='cpu', weights_only=True)
            assert final['generation'] == run['generation']
            assert final['config_sha256'] == run['config_sha256']
            if run['generation'] == 400:
                checkpoint = torch.load(directory/'generation_0400.pt', map_location='cpu', weights_only=True)
                assert torch.equal(final['mean'], checkpoint['mean'])
            else:
                assert run['generation'] == run['collapsed_at']
                assert all(r['population_std'] == 0 for r in records[-20:])
            dev = torch.load(directory/'development.pt', map_location='cpu', weights_only=True)
            m = run['development']
            # Scores already divided by horizon; tolerate only reduction rounding.
            assert abs(dev['scores'].mean().item()-m['survival']) < 1e-7
            assert (dev['good'] > 0).float().mean().item() == m['ate_good_fraction']
            assert dev['survived_first'].float().mean().item() == m['survived_first_fraction']
            assert dev['good'].double().mean().item() == m['good_food_mean']
            assert dev['bad'].double().mean().item() == m['bad_food_mean']
            assert dev['scores'].numel() == 512
            assert torch.isfinite(dev['scores']).all()
            actual_switches = dev['start'] >= 0
            assert actual_switches.sum().item() == m['switches']
            assert (actual_switches & ~dev['observed']).sum().item() == m['censored']
            assert (dev['duration'][actual_switches] >= 0).all()
            checked.append(run['label'])
assert not list(Path('runs/002A').glob('**/*holdout*'))
write_json('evidence/002A/integrity_audit.json', dict(status='PASS', protected_001a=True,
    original_progress_preserved=True, task_board_other_lines_unchanged=True,
    pilot_runs_checked=checked, holdout_002a_artifacts_absent=True,
    limitation='Absence of files alone is not proof of non-access; rollout also rejects all holdout domains/regimes.'))
print('PASS', len(checked), 'pilot runs checked')
