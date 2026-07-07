from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from scripts.ego_kernel.state import KernelState


KERNEL_TRACE_SCHEMA_VERSION = "kernel_trace_v0"
TRACE_FIELDS = (
    "task_id",
    "run_id",
    "episode_id",
    "step_id",
    "state_before_hash",
    "observation",
    "prediction",
    "action",
    "feedback",
    "prediction_error",
    "state_after_hash",
    "component_attribution",
    "seed_context",
)


def build_trace_row(
    *,
    state_before: KernelState,
    observation: dict[str, Any],
    action: dict[str, Any],
    state_after: KernelState,
    component_attribution: dict[str, Any],
) -> dict[str, Any]:
    return {
        "task_id": state_before.task_id,
        "run_id": state_before.run_id,
        "episode_id": state_before.episode_id,
        "step_id": state_after.step_id,
        "state_before_hash": state_before.state_hash(),
        "observation": observation,
        "prediction": None,
        "action": action,
        "feedback": None,
        "prediction_error": None,
        "state_after_hash": state_after.state_hash(),
        "component_attribution": component_attribution,
        "seed_context": state_after.seed_context(),
    }


def validate_trace_row(row: dict[str, Any]) -> None:
    if tuple(row.keys()) != TRACE_FIELDS:
        raise ValueError("kernel trace row fields are not in kernel_trace_v0 order")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            validate_trace_row(row)
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                validate_trace_row(payload)
                rows.append(payload)
    return rows
