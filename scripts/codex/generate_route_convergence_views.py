#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from route_convergence_common import (
    REPO_HYGIENE_POLICY_PATH,
    REPO_SURFACE_MAP_PATH,
    TASK_LANE_INDEX_PATH,
    load_program_state,
    render_repo_hygiene_policy,
    render_repo_surface_map,
    render_task_lane_index,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    program_state = load_program_state()
    _write(TASK_LANE_INDEX_PATH, render_task_lane_index(program_state))
    _write(REPO_HYGIENE_POLICY_PATH, render_repo_hygiene_policy())
    _write(REPO_SURFACE_MAP_PATH, render_repo_surface_map())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
