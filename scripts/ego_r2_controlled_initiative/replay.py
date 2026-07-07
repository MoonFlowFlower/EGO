from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def digest_payload(payload: object) -> str:
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def fresh_process_smoke_replay(tmp_path: Path, *, master_seed: int, n_episodes: int) -> dict:
    cmd = [
        sys.executable,
        "-m",
        "scripts.ego_r2_controlled_initiative.runner",
        "--phase",
        "smoke-digest",
        "--master-seed",
        str(master_seed),
        "--n-ep",
        str(n_episodes),
    ]
    env = dict(os.environ)
    env["PYTHONHASHSEED"] = "0"
    outputs = []
    for idx in range(2):
        proc = subprocess.run(cmd, cwd=Path.cwd(), env=env, text=True, capture_output=True, timeout=60)
        (tmp_path / f"replay_{idx}.stdout").write_text(proc.stdout, encoding="utf-8")
        (tmp_path / f"replay_{idx}.stderr").write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            return {
                "status": "fail",
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "episodes": n_episodes,
            }
        outputs.append(json.loads(proc.stdout))
    return {
        "producer_function": "fresh_process_smoke_replay",
        "status": "pass" if outputs[0]["digest"] == outputs[1]["digest"] else "fail",
        "digest_1": outputs[0]["digest"],
        "digest_2": outputs[1]["digest"],
        "episodes": n_episodes,
    }
