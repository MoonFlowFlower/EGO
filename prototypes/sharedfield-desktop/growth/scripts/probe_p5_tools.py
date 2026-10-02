import json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crafter
from growthlab.demonstration import recording_env,convert
from growthlab.records import RUNS,EVIDENCE,write_json,telemetry
start=time.perf_counter();samples=[telemetry()];folder=RUNS/f'p5_smoke_{uuid.uuid4().hex}'
env=recording_env(folder,source='synthetic_tool_smoke')(seed=11,length=5)
rec=crafter.Recorder(env,folder,video_size=(128,128));rec.reset()
for _ in range(5):rec.step(0)
summary=convert(next(folder.glob('*.npz')),env.sidecar_path,folder/'filtered.json')
filtered=json.loads((folder/'filtered.json').read_text(encoding='utf-8'))
checks={'privileged_keys_removed':all(x not in json.dumps(filtered) for x in ('semantic','player_pos','achievements','reward')),
        'synthetic_not_human':filtered['source']=='synthetic_tool_smoke','aligned_complete_5_steps':summary['steps']==5}
env.sidecar['complete']=False;write_json(folder/'incomplete.json',env.sidecar)
try:convert(next(folder.glob('*.npz')),folder/'incomplete.json',folder/'should_not_exist.json')
except ValueError:checks['incomplete_rejected']=True
samples.append(telemetry())
write_json(EVIDENCE/'p5_tools.json',{'seconds':time.perf_counter()-start,'checks':checks,'conversion':summary,
    'owner_demonstration':'未验证; pending owner play','telemetry':samples})
assert all(checks.values()),checks
print(checks)
