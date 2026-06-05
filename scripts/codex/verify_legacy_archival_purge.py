#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import yaml

from archive_verifier_common import (
    ArchivalManifest,
    check_archive_core,
    check_forbidden_snippets,
    check_historical_safety_notes,
    check_required_snippets,
    load_archival_manifest,
)
from route_convergence_common import build_route_entries, load_program_state


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "artifacts" / "archive" / "legacy_pre_operator_mainline_manifest.json"


ACTIVE_DOCS = (
    "AGENTS.md",
    "README.md",
    "docs/AGENT_DEVELOPMENT_PLAYBOOK.md",
    "docs/MAINLINE_QUICKSTART.md",
    "docs/CAPABILITY_REGISTRY.md",
    "docs/REPO_SURFACE_MAP.md",
    "docs/REPO_HYGIENE_POLICY.md",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
    ".codex/project_contract.yaml",
)

HISTORICAL_DOCS_WITH_SAFETY_NOTE = (
    "docs/CURRENT_PROJECT_LOGIC_FLOW.md",
)

ACTIVE_SCRIPT_FILES = (
    "scripts/codex/audit_worktree_noise.py",
    "scripts/codex/build_capability_registry.py",
    "scripts/codex/check_program_state_integrity.py",
    "scripts/codex/generate_program_state_views.py",
    "scripts/codex/generate_route_convergence_views.py",
    "scripts/codex/lint_repo.py",
    "scripts/codex/program_state_common.py",
    "scripts/codex/route_convergence_common.py",
    "scripts/codex/verify_mainline_clarity.py",
    "scripts/codex/verify_repo.py",
    "scripts/codex/verify_route_convergence.py",
)

LEGACY_IMPORT_MODULES = (
    "EgoCore",
    "OpenEmotion",
    "ego_desktop_lab",
    "openemotion",
    "emotiond",
)


def _load_manifest(errors: list[str]) -> ArchivalManifest | None:
    try:
        return load_archival_manifest(MANIFEST_PATH)
    except Exception as exc:
        errors.append(f"missing or invalid archive manifest: {MANIFEST_PATH.relative_to(ROOT).as_posix()} ({exc})")
        return None


def _required_pointers(manifest: ArchivalManifest) -> dict[str, list[str]]:
    return {
        "legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md": [
            manifest.archive_tag,
            "docs/PROGRAM_STATE_UNIFIED.yaml",
            "no runtime authority",
            "new Stage Card and evidence gate",
        ],
        "docs/archive/LEGACY_ALGORITHM_INVENTORY.md": [
            "Reference only",
            "No runtime authority",
            "No default path",
            "Reuse requires a new Stage Card and evidence gate",
        ],
        "artifacts/archive/legacy_pre_operator_mainline_manifest.json": [
            manifest.archive_tag,
            manifest.archive_commit,
        ],
    }


def _forbidden_active_snippets(manifest: ArchivalManifest) -> tuple[str, ...]:
    removed = []
    for rel_path in manifest.removed_dirs:
        removed.append(f"{rel_path}/")
        removed.append(rel_path)
    return (
        *removed,
        "EgoCore/app/",
        "EgoCore/docs/PROGRAM_STATE_UNIFIED.yaml",
        "OpenEmotion/docs/PROGRAM_STATE_UNIFIED.yaml",
        "OpenEmotion/openemotion/",
        "ego_desktop_lab/main.py",
    )


def _check_archive_pointers(errors: list[str], manifest: ArchivalManifest) -> None:
    check_archive_core(root=ROOT, manifest=manifest, errors=errors)
    check_required_snippets(ROOT, _required_pointers(manifest), errors)


def _check_program_state(errors: list[str]) -> None:
    state = load_program_state()
    integrity = state.get("integrity") or {}
    if integrity.get("legacy_archive_pointer") != "legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md":
        errors.append("program state integrity.legacy_archive_pointer mismatch")
    if integrity.get("compatibility_mirrors") not in (None, []):
        errors.append("program state still declares compatibility mirrors")
    if "shim_register" in integrity:
        errors.append("program state still declares legacy shim_register")
    generated = set(integrity.get("generated_views") or [])
    if generated != {"docs/STATUS.md", "artifacts/reports/program_state_summary.md"}:
        errors.append("program state generated_views still include legacy mirrors or missing current generated views")

    for workstream in state.get("workstreams") or []:
        text = " ".join(str(workstream.get(key, "")) for key in ("id", "owner", "status", "summary"))
        if not any(name in text for name in ("EgoCore", "OpenEmotion", "ego_desktop_lab")):
            continue
        if workstream.get("mainline_connected") is True or workstream.get("enabled") is True:
            errors.append(
                f"legacy-named workstream is still active-looking: {workstream.get('id')} "
                f"mainline_connected={workstream.get('mainline_connected')} enabled={workstream.get('enabled')}"
            )


def _check_route_entries(errors: list[str]) -> None:
    entries = build_route_entries(load_program_state())
    active_or_supporting = [entry for entry in entries if entry.lane in {"active_default", "supporting_active"}]
    for entry in active_or_supporting:
        text = " ".join([entry.key, entry.label, entry.why, *(entry.paths)])
        if any(name in text for name in ("EgoCore", "OpenEmotion", "ego_desktop_lab")):
            errors.append(f"active/supporting route references archived legacy: {entry.key}")


def _check_active_docs_and_scripts(errors: list[str], manifest: ArchivalManifest) -> None:
    check_forbidden_snippets(ROOT, ACTIVE_DOCS + ACTIVE_SCRIPT_FILES, _forbidden_active_snippets(manifest), errors)
    check_historical_safety_notes(
        ROOT,
        {
            rel_path: [
                "pre-EgoOperator historical logic-flow record",
                "legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md",
                manifest.archive_tag,
            ]
            for rel_path in HISTORICAL_DOCS_WITH_SAFETY_NOTE
        },
        errors,
    )


def _check_ego_operator_imports(errors: list[str]) -> None:
    for path in sorted((ROOT / "EgoOperator").rglob("*.py")):
        rel_path = path.relative_to(ROOT).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel_path)
        except SyntaxError as exc:
            errors.append(f"{rel_path} syntax error while scanning imports: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in LEGACY_IMPORT_MODULES or alias.name.startswith(tuple(f"{item}." for item in LEGACY_IMPORT_MODULES)):
                        errors.append(f"{rel_path} imports archived legacy module: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module in LEGACY_IMPORT_MODULES or module.startswith(tuple(f"{item}." for item in LEGACY_IMPORT_MODULES)):
                    errors.append(f"{rel_path} imports archived legacy module: {module}")


def _check_project_contract(errors: list[str]) -> None:
    path = ROOT / ".codex" / "project_contract.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    for field in ("protected_paths", "allowed_mutation_paths"):
        for item in data.get(field) or []:
            if any(item.startswith(f"{removed}/") or item == removed for removed in _forbidden_contract_removed_dirs()):
                errors.append(f"project_contract.{field} still references removed legacy path: {item}")
    for prefix in data.get("task_classification", {}).get("ready_title_prefixes") or []:
        if prefix.startswith(("EgoCore", "OpenEmotion", "ego_desktop_lab")):
            errors.append(f"project contract task default uses archived legacy title prefix: {prefix}")


def _forbidden_contract_removed_dirs() -> tuple[str, ...]:
    manifest = load_archival_manifest(MANIFEST_PATH)
    return manifest.removed_dirs


def main() -> int:
    errors: list[str] = []
    manifest = _load_manifest(errors)
    if manifest is None:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    _check_archive_pointers(errors, manifest)
    _check_program_state(errors)
    _check_route_entries(errors)
    _check_active_docs_and_scripts(errors, manifest)
    _check_ego_operator_imports(errors)
    _check_project_contract(errors)

    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "archive_tag": manifest.archive_tag,
                "archive_commit": manifest.archive_commit,
                "removed_dirs_absent": list(manifest.removed_dirs),
                "runtime_owner": "EgoOperator",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
