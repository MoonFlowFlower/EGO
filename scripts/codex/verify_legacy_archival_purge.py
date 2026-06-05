#!/usr/bin/env python3
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable

import yaml

from route_convergence_common import build_route_entries, load_program_state


ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_TAG = "legacy-pre-operator-mainline-before-purge"
ARCHIVE_COMMIT = "67347a759b5911f14e151748f294938fe53058ae"

REMOVED_DIRS = (
    "legacy/ego-pre-handmade-mainline/EgoCore",
    "legacy/ego-pre-handmade-mainline/OpenEmotion",
    "legacy/ego-pre-handmade-mainline/ego_desktop_lab",
)

REQUIRED_POINTERS = {
    "legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md": [
        ARCHIVE_TAG,
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
        ARCHIVE_TAG,
        ARCHIVE_COMMIT,
    ],
}

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

FORBIDDEN_ACTIVE_SNIPPETS = (
    "legacy/ego-pre-handmade-mainline/EgoCore/",
    "legacy/ego-pre-handmade-mainline/OpenEmotion/",
    "legacy/ego-pre-handmade-mainline/ego_desktop_lab/",
    "legacy/ego-pre-handmade-mainline/EgoCore",
    "legacy/ego-pre-handmade-mainline/OpenEmotion",
    "legacy/ego-pre-handmade-mainline/ego_desktop_lab",
    "EgoCore/app/",
    "EgoCore/docs/PROGRAM_STATE_UNIFIED.yaml",
    "OpenEmotion/docs/PROGRAM_STATE_UNIFIED.yaml",
    "OpenEmotion/openemotion/",
    "ego_desktop_lab/main.py",
)

LEGACY_IMPORT_MODULES = (
    "EgoCore",
    "OpenEmotion",
    "ego_desktop_lab",
    "openemotion",
    "emotiond",
)


def _git_stdout(args: list[str]) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _contains_any(text: str, snippets: Iterable[str]) -> list[str]:
    return [snippet for snippet in snippets if snippet in text]


def _check_removed_dirs(errors: list[str]) -> None:
    for rel_path in REMOVED_DIRS:
        if (ROOT / rel_path).exists():
            errors.append(f"removed legacy directory still exists: {rel_path}")


def _check_archive_pointers(errors: list[str]) -> None:
    resolved = _git_stdout(["rev-parse", "--verify", ARCHIVE_TAG])
    if resolved != ARCHIVE_COMMIT:
        errors.append(f"archive tag {ARCHIVE_TAG} resolves to {resolved or 'unavailable'}, expected {ARCHIVE_COMMIT}")

    for rel_path, snippets in REQUIRED_POINTERS.items():
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"missing archive pointer surface: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        for snippet in snippets:
            if snippet not in text:
                errors.append(f"{rel_path} missing required archive snippet: {snippet}")

    manifest_path = ROOT / "artifacts/archive/legacy_pre_operator_mainline_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("created_from_commit") != ARCHIVE_COMMIT:
            errors.append("manifest created_from_commit does not match archive commit")
        if manifest.get("archive_pointer", {}).get("name") != ARCHIVE_TAG:
            errors.append("manifest archive pointer name mismatch")
        if sorted(manifest.get("removed_paths") or []) != sorted(f"{item}/" for item in REMOVED_DIRS):
            errors.append("manifest removed_paths mismatch")


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


def _check_active_docs_and_scripts(errors: list[str]) -> None:
    for rel_path in ACTIVE_DOCS + ACTIVE_SCRIPT_FILES:
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"missing active surface: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        matches = _contains_any(text, FORBIDDEN_ACTIVE_SNIPPETS)
        if matches:
            errors.append(f"{rel_path} contains forbidden active legacy path snippets: {', '.join(matches[:5])}")

    for rel_path in HISTORICAL_DOCS_WITH_SAFETY_NOTE:
        path = ROOT / rel_path
        if not path.exists():
            errors.append(f"missing historical surface with safety note: {rel_path}")
            continue
        text = path.read_text(encoding="utf-8")
        required = [
            "pre-EgoOperator historical logic-flow record",
            "legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md",
            ARCHIVE_TAG,
        ]
        for snippet in required:
            if snippet not in text:
                errors.append(f"{rel_path} missing historical safety snippet: {snippet}")


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
            if any(item.startswith(f"{removed}/") or item == removed for removed in REMOVED_DIRS):
                errors.append(f"project_contract.{field} still references removed legacy path: {item}")
    for prefix in data.get("task_classification", {}).get("ready_title_prefixes") or []:
        if prefix.startswith(("EgoCore", "OpenEmotion", "ego_desktop_lab")):
            errors.append(f"project contract task default uses archived legacy title prefix: {prefix}")


def main() -> int:
    errors: list[str] = []
    _check_removed_dirs(errors)
    _check_archive_pointers(errors)
    _check_program_state(errors)
    _check_route_entries(errors)
    _check_active_docs_and_scripts(errors)
    _check_ego_operator_imports(errors)
    _check_project_contract(errors)

    if errors:
        print(json.dumps({"status": "fail", "errors": errors}, ensure_ascii=False, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "pass",
                "archive_tag": ARCHIVE_TAG,
                "archive_commit": ARCHIVE_COMMIT,
                "removed_dirs_absent": list(REMOVED_DIRS),
                "runtime_owner": "EgoOperator",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
