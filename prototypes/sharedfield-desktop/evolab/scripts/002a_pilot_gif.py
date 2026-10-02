"""Illustrative predeclared L0 B/drift/seed0; reuse development draws, no selection."""
import sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from evolab.config import setup
from evolab.render import render
from evolab.v002.config import Config
from evolab.v002.rollout import rollout
from evolab.v002.records import write_json, verify_protected

setup(); verify_protected()
data = json.loads(Path('evidence/002A/f2_learnability.json').read_text())
c = Config(**data['levels'][0]['config'])
directory = Path('runs/002A/F2/L0_gru_mb_plastic_drift_seed0')
final = torch.load(directory/'final_mean.pt', weights_only=True)
assert final['generation'] == 400
start = time.perf_counter()
scores, result = rollout(c, 'drift', 'gru_mb_plastic', 512, 0, 'pilot_dev', 1,
                         final['mean'].cuda()[None], trace=True)
saved = torch.load(directory/'development.pt', weights_only=True)
assert torch.equal(scores.cpu(), saved['scores'])
path = Path('evidence/002A/pilot_L0_B_drift_seed0.gif')
render(result['frames'], path)
write_json('evidence/002A/pilot_gif.json', dict(source=str(directory), generation=400,
    domain='pilot_dev', domain_id=430000, episode_index=0, episodes=512,
    selection='First full-scale probe, fixed before results; no best selection',
    replay_bitwise_equal=True, episode_survival=float(scores[0, 0]),
    example_good_food=int(saved['good'][0]), example_bad_food=int(saved['bad'][0]),
    example_drift_switches=int((saved['start'][0] >= 0).sum()),
    example_survived_first=bool(saved['survived_first'][0]),
    seconds=time.perf_counter()-start, frames=len(result['frames']),
    timing_note='Rendered concurrently with pilot; auxiliary GPU work included within F2 wall budget',
    human_visual_acceptance='未验证'))
print(path, 'scores bitwise match, seconds', time.perf_counter()-start)
