"""Publish compact summaries after evaluation; keep raw generations/episodes in runs."""
import json
from pathlib import Path

if not Path('evidence/e2_decision.json').exists():
    raise RuntimeError('Wait until evaluation has consumed training episode records')
for path in Path('runs').glob('*_attempt*/status.json'):
    record = json.loads(path.read_text())
    if record['status'] == 'RUNNING':
        raise RuntimeError('Cannot finalize summaries while a run is active')
    record['raw_status'] = path.as_posix()
    record['raw_generations'] = (path.parent / 'generations.jsonl').as_posix()
    record.pop('training_survival', None)
    record.pop('random_survival', None)
    if 'curve' in record:
        record['curve'] = [r for r in record['curve'] if 'development_mean' in r]
        record['curve_sampling'] = 'fixed every 20 generations; full raw curve retained in runs'
    destination = Path('evidence/summaries') / (record['label'] + '.json')
    destination.write_text(json.dumps(record, indent=2), encoding='utf-8', newline='\n')
