"""Shared PSPC shadow-only contract helpers.

These helpers are intentionally script-side utilities. EgoOperator runtime
modules must not import them unless a future stage explicitly authorizes a
default-off runtime-adjacent shadow path.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterable


SIDE_EFFECTS_FALSE = {
    "runtime_registered": False,
    "user_response_mutated": False,
    "proposal_mutated": False,
    "plan_mutated": False,
    "memory_written": False,
    "gate_invoked": False,
    "approval_mutated": False,
    "transport_called": False,
    "proactive_trigger": False,
    "planner_called": False,
    "training_called": False,
    "model_executed": False,
    "claim_ceiling_raised": False,
}

RUNTIME_AUTHORITY_FIELDS = {
    "action",
    "tool_call",
    "command",
    "user_message",
    "memory_write",
    "gate_decision",
    "approval_id",
    "transport",
    "send",
    "schedule",
    "runtime_registration",
    "mainline_authority",
    "enable",
}


def sha256_text(value: str | None) -> str | None:
    if value is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def runtime_field_hits(payload: Any, *, prefix: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if str(key) in RUNTIME_AUTHORITY_FIELDS:
                hits.append(dotted)
            hits.extend(runtime_field_hits(value, prefix=dotted))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            hits.extend(runtime_field_hits(value, prefix=f"{prefix}[{index}]"))
    return sorted(set(hits))


def active_runtime_python_files(repo_root: Path, *, excluded_parts: Iterable[str] | None = None) -> list[Path]:
    runtime_root = Path(repo_root) / "EgoOperator"
    excluded = set(excluded_parts or {"adapters", "artifacts", "docs", "__pycache__"})
    files: list[Path] = []
    for path in runtime_root.rglob("*.py"):
        rel = path.relative_to(runtime_root)
        if any(part in excluded for part in rel.parts):
            continue
        if "test" in path.name.lower():
            continue
        files.append(path)
    return sorted(files)


def scan_active_runtime_sources(repo_root: Path, markers: Iterable[str]) -> dict[str, Any]:
    marker_list = list(markers)
    files = active_runtime_python_files(repo_root)
    offenders: list[dict[str, str]] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        for marker in marker_list:
            if marker in source:
                offenders.append(
                    {
                        "path": str(path.relative_to(repo_root)),
                        "marker": marker,
                    }
                )
    return {
        "scanned_file_count": len(files),
        "markers": marker_list,
        "offenders": offenders,
        "ok": not offenders,
    }
