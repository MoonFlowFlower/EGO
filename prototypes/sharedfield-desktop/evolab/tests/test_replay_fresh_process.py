import json,subprocess,sys
from pathlib import Path
import pytest

@pytest.mark.parametrize('arm',['gru_fixed','gru_mb_plastic'])
def test_replay_fresh_process(arm,tmp_path):
    outputs=[]
    root=Path(__file__).resolve().parents[1]
    for i in range(2):
        out=tmp_path/f'{arm}_{i}.json'
        subprocess.run([sys.executable,str(root/'scripts/replay_probe.py'),arm,str(out)],check=True,cwd=root)
        outputs.append(json.loads(out.read_text()))
    assert outputs[0]==outputs[1]
