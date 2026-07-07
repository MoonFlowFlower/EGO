from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.ego_kernel.validation import run_validation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="artifacts/ego_r0_kernel_state_substrate_001a")
    args = parser.parse_args()
    result = run_validation(repo_root=ROOT, out_dir=Path(args.out_dir))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["verdict"] == "r0_substrate_pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
