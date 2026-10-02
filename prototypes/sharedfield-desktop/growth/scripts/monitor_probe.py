import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from growthlab.records import EVIDENCE,RUNS,telemetry,write_json
label=sys.argv[1];start=time.perf_counter();rows=[]
while time.perf_counter()-start<7200:
    rows.append(telemetry());write_json(RUNS/f'{label}_thermal.json',rows)
    if (EVIDENCE/f'{label}.json').exists():break
    time.sleep(1)
write_json(EVIDENCE/f'{label}_thermal.json',rows)
