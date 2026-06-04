"""Launch the local EgoDesktop Live2D viewer with a gated EgoOperator signal."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from EgoOperator.primitives.embodied_initiative import (  # noqa: E402
    build_embodied_initiative_contract,
    validate_embodied_initiative_contract,
)


def _node_executable() -> str:
    return shutil.which("node.exe") or shutil.which("node") or "node"


def _write_signal_file(user_text: str) -> Path:
    contract = build_embodied_initiative_contract(
        user_text=user_text,
        primitive_class="live2d_presence_state",
    )
    validation = validate_embodied_initiative_contract(contract)
    if validation.get("status") != "pass":
        raise SystemExit(f"embodied initiative contract failed validation: {validation}")
    signal_path = Path(tempfile.gettempdir()) / "ego_live2d_presence_signal.json"
    signal_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    return signal_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", required=True, help="Path to .model3.json or its containing directory.")
    parser.add_argument(
        "--user-text",
        default="Live2D presence state for EgoOperator desktop viewer v1.",
        help="Bounded text used only to build the local primitive contract.",
    )
    parser.add_argument("--smoke", action="store_true", help="Run Electron smoke and exit.")
    parser.add_argument("--out", help="Smoke output directory.")
    args = parser.parse_args()

    signal_path = _write_signal_file(args.user_text)
    desktop_root = REPO_ROOT / "EgoDesktop"
    script_name = "smoke.js" if args.smoke else "start.js"
    command = [_node_executable(), str(desktop_root / "scripts" / script_name)]
    command.extend(["--model-path", str(Path(args.model_path)), "--signal-file", str(signal_path)])
    if args.out:
        command.extend(["--out", str(Path(args.out))])
    return subprocess.call(command, cwd=desktop_root)


if __name__ == "__main__":
    raise SystemExit(main())
