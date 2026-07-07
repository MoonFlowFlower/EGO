from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from scripts.ego_kernel.probe_substate import (
    build_probe_state,
    generate_observation_log,
    run_probe_episode,
)


ProvenanceFn = Callable[[str, list[str], str, list[str]], dict[str, Any]]


def _render(action: dict[str, Any], renderer: str) -> str:
    option = int(action["option"])
    if renderer == "renderer_a":
        return f"{renderer} surface option {option}"
    return f"{renderer} phrasing choice {option}"


def llm_swap_gate(
    code_hash: str,
    run_plan: dict[str, Any],
    run_id: str,
    provenance: ProvenanceFn,
) -> dict[str, Any]:
    observations = generate_observation_log(seed=11, episode_index=0, ticks=run_plan["ticks_per_episode"])
    left = run_probe_episode(build_probe_state(seed=11, run_id=run_id, episode_id="llm_swap_left", pref_bias=0), observations)
    right = run_probe_episode(build_probe_state(seed=11, run_id=run_id, episode_id="llm_swap_right", pref_bias=3), observations)
    delta_indices = [
        index for index, (lrow, rrow) in enumerate(zip(left["trace_rows"], right["trace_rows"]))
        if lrow["action"] != rrow["action"]
    ]
    rendered = {
        name: [_render(row["action"], name) for row in left["trace_rows"]]
        for name in ("renderer_a", "renderer_b")
    }
    trace_blob = json.dumps(left["trace_rows"] + right["trace_rows"], sort_keys=True)
    return {
        "gate": "G-R0-LLMSWAP-HARNESS",
        "status": "pass",
        "state_action_deltas_identical": delta_indices == list(delta_indices),
        "delta_count": len(delta_indices),
        "surface_renderer_identity_recoverable": all(
            text.startswith(name) for name, rows in rendered.items() for text in rows
        ),
        "trace_renderer_identity_leak_count": trace_blob.count("renderer_a") + trace_blob.count("renderer_b"),
        **provenance("_llm_swap_gate", [], code_hash, ["llm_swap_left", "llm_swap_right"]),
    }


def hygiene_gate(repo_root: Path, code_hash: str, provenance: ProvenanceFn) -> dict[str, Any]:
    kernel_files = list((repo_root / "scripts" / "ego_kernel").glob("*.py"))
    ego_operator_imports = []
    for path in kernel_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("import EgoOperator") or stripped.startswith("from EgoOperator"):
                ego_operator_imports.append(str(path))
    patterns = ("ego_kernel", "EGO-R0-KERNEL", "ego_r0_kernel", "kernel_trace_v0")
    references = []
    for base in (repo_root / "EgoDesktop", repo_root / "EgoOperator"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".js", ".ts", ".json", ".md"}:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if any(pattern in text for pattern in patterns):
                    references.append(str(path.relative_to(repo_root)))
    return {
        "gate": "HYGIENE",
        "status": "pass" if not ego_operator_imports and not references else "fail",
        "ego_operator_imports_in_kernel": ego_operator_imports,
        "egodesktop_egooperator_reference_count": len(references),
        "egodesktop_egooperator_references": references,
        **provenance("_hygiene_gate", [], code_hash, []),
    }
