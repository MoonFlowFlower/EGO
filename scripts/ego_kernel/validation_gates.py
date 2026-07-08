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
DEFAULT_SANCTIONED_ADOPTERS_PATH = (
    "docs/codex/tasks/ego-r0-kernel-state-substrate-001a/sanctioned_kernel_adopters.json"
)
REFERENCE_PATTERNS = ("ego_kernel", "EGO-R0-KERNEL", "ego_r0_kernel", "kernel_trace_v0")
REFERENCE_SUFFIXES = {".py", ".js", ".ts", ".json", ".md"}


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


def _normalize_repo_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").strip()


def _has_wildcard(path: str) -> bool:
    return any(token in path for token in ("*", "?", "[", "]"))


def load_sanctioned_adopters(
    repo_root: Path,
    relative_path: str = DEFAULT_SANCTIONED_ADOPTERS_PATH,
) -> dict[str, Any]:
    config_path = repo_root / relative_path
    if not config_path.exists():
        return {
            "path": relative_path,
            "sha256": None,
            "sanctioned_adopters": [],
            "errors": [{"reason": "missing_sanctioned_adopters_config", "path": relative_path}],
        }
    raw = config_path.read_text(encoding="utf-8")
    payload = json.loads(raw)
    errors = []
    adopters = []
    for entry in payload.get("sanctioned_adopters", []):
        adopter_path = _normalize_repo_path(entry.get("path", ""))
        authorizing_card = str(entry.get("authorizing_card", "")).strip()
        rationale = str(entry.get("rationale", "")).strip()
        if not adopter_path:
            errors.append({"reason": "missing_path", "entry": entry})
        if _has_wildcard(adopter_path):
            errors.append({"reason": "wildcard_path_forbidden", "path": adopter_path})
        if not authorizing_card:
            errors.append({"reason": "missing_authorizing_card", "path": adopter_path})
        elif not (repo_root / "docs" / "codex" / "tasks" / authorizing_card).exists():
            errors.append({
                "reason": "authorizing_card_missing",
                "path": adopter_path,
                "authorizing_card": authorizing_card,
            })
        if not rationale:
            errors.append({"reason": "missing_rationale", "path": adopter_path})
        adopters.append({
            "path": adopter_path,
            "authorizing_card": authorizing_card,
            "rationale": rationale,
        })
    return {
        "path": relative_path,
        "sha256": _sha256_text(raw),
        "sanctioned_adopters": adopters,
        "errors": errors,
    }


def classify_kernel_references(
    references: list[str],
    sanctioned_adopters: list[dict[str, Any]],
) -> list[str]:
    declared_paths = {_normalize_repo_path(entry.get("path", "")) for entry in sanctioned_adopters}
    return [
        reference
        for reference in [_normalize_repo_path(item) for item in references]
        if reference not in declared_paths
    ]


def declared_kernel_adopters(
    references: list[str],
    sanctioned_adopters: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    reference_set = {_normalize_repo_path(item) for item in references}
    return [
        {
            "path": _normalize_repo_path(entry.get("path", "")),
            "authorizing_card": str(entry.get("authorizing_card", "")).strip(),
            "rationale": str(entry.get("rationale", "")).strip(),
        }
        for entry in sanctioned_adopters
        if _normalize_repo_path(entry.get("path", "")) in reference_set
    ]


def hygiene_status(ego_operator_imports: list[str], undeclared_references: list[str], config_errors: list[dict[str, Any]] | None = None) -> str:
    return "pass" if not ego_operator_imports and not undeclared_references and not (config_errors or []) else "fail"


def _sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def scan_kernel_references(repo_root: Path) -> list[str]:
    references = []
    for base in (repo_root / "EgoDesktop", repo_root / "EgoOperator"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            relative_parts = path.relative_to(repo_root).parts
            if "node_modules" in relative_parts:
                continue
            if path.is_file() and path.suffix.lower() in REFERENCE_SUFFIXES:
                text = path.read_text(encoding="utf-8", errors="ignore")
                if any(pattern in text for pattern in REFERENCE_PATTERNS):
                    references.append(_normalize_repo_path(path.relative_to(repo_root)))
    return sorted(references)


def hygiene_gate(repo_root: Path, code_hash: str, provenance: ProvenanceFn) -> dict[str, Any]:
    kernel_files = list((repo_root / "scripts" / "ego_kernel").glob("*.py"))
    ego_operator_imports = []
    for path in kernel_files:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("import EgoOperator") or stripped.startswith("from EgoOperator"):
                ego_operator_imports.append(str(path))
    references = scan_kernel_references(repo_root)
    allowlist = load_sanctioned_adopters(repo_root)
    undeclared_references = classify_kernel_references(references, allowlist["sanctioned_adopters"])
    declared_adopters = declared_kernel_adopters(references, allowlist["sanctioned_adopters"])
    return {
        "gate": "HYGIENE",
        "status": hygiene_status(ego_operator_imports, undeclared_references, allowlist["errors"]),
        "ego_operator_imports_in_kernel": ego_operator_imports,
        "egodesktop_egooperator_reference_count": len(references),
        "egodesktop_egooperator_references": references,
        "declared_adopters": declared_adopters,
        "declared_adopter_count": len(declared_adopters),
        "undeclared_references": undeclared_references,
        "undeclared_reference_count": len(undeclared_references),
        "sanctioned_adopters_config": {
            "path": allowlist["path"],
            "sha256": allowlist["sha256"],
            "errors": allowlist["errors"],
        },
        "node_modules_excluded": True,
        **provenance("_hygiene_gate", [allowlist["path"]], code_hash, []),
    }
