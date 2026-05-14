#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from route_convergence_common import (
    HYGIENE_RULES,
    REPO_SURFACE_MAP_PATH,
    build_route_entries,
    load_program_state,
    render_repo_surface_map,
)


ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"
QUICKSTART_PATH = ROOT / "docs" / "MAINLINE_QUICKSTART.md"


REQUIRED_README_REFS = (
    "docs/MAINLINE_QUICKSTART.md",
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
    "docs/REPO_HYGIENE_POLICY.md",
)

REQUIRED_QUICKSTART_REFS = (
    "subject_system_v1_governed_proactivity",
    "EgoCore",
    "OpenEmotion",
    "ego_desktop_lab",
    "reference harness",
    "not a second runtime",
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
)


def _git_lines(args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _matches_prefix(path: str, prefix: str) -> bool:
    return path == prefix.rstrip("/") or path.startswith(prefix)


def _check_staged_operational_exhaust(errors: list[str]) -> None:
    staged_added = _git_lines(["diff", "--cached", "--name-only", "--diff-filter=A"])
    blocked: list[str] = []
    for path in staged_added:
        for rule in HYGIENE_RULES:
            if _matches_prefix(path, rule.path_prefix):
                blocked.append(f"{path} ({rule.class_name})")
                break
        if "__pycache__/" in path or path.endswith((".pyc", ".pyo")):
            blocked.append(f"{path} (python_cache_exhaust)")
    if blocked:
        errors.append("staged operational exhaust is not allowed: " + ", ".join(sorted(blocked)[:20]))


def _check_text_contains(path: Path, required: tuple[str, ...], errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"missing required mainline clarity file: {path.relative_to(ROOT)}")
        return
    text = path.read_text(encoding="utf-8")
    for item in required:
        if item not in text:
            errors.append(f"{path.relative_to(ROOT)} missing `{item}`")


def main() -> int:
    errors: list[str] = []
    state = load_program_state()
    entries = build_route_entries(state)
    active = [entry for entry in entries if entry.lane == "active_default"]
    if len(active) != 1:
        errors.append(f"expected exactly one active_default lane, found {len(active)}")
    elif active[0].key != "subject-system-v1-governed-proactivity":
        errors.append("active_default lane must stay `subject-system-v1-governed-proactivity`")

    _check_text_contains(README_PATH, REQUIRED_README_REFS, errors)
    _check_text_contains(QUICKSTART_PATH, REQUIRED_QUICKSTART_REFS, errors)

    if not REPO_SURFACE_MAP_PATH.exists():
        errors.append("missing generated docs/REPO_SURFACE_MAP.md")
    else:
        expected = render_repo_surface_map()
        actual = REPO_SURFACE_MAP_PATH.read_text(encoding="utf-8")
        if actual != expected:
            errors.append("generated file drift detected: docs/REPO_SURFACE_MAP.md")

    _check_staged_operational_exhaust(errors)

    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    print(
        json.dumps(
            {
                "status": "pass",
                "active_default": active[0].key if active else None,
                "quickstart": str(QUICKSTART_PATH.relative_to(ROOT)),
                "surface_map": str(REPO_SURFACE_MAP_PATH.relative_to(ROOT)),
                "staged_exhaust_blocked": True,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
