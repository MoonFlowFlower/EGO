#!/usr/bin/env python3
"""Codex session bootstrap and closeout guard for the EGO repo."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONTRACT_PATH = ROOT / ".codex" / "project_contract.yaml"
DEFAULT_PROGRAM_STATE_PATH = ROOT / "docs" / "PROGRAM_STATE_UNIFIED.yaml"
DEFAULT_CODEX_MEMORY_PATH = ROOT / "CODEX_MEMORY.md"
DEFAULT_TASK_BOARD_PATH = ROOT / "Tasks" / "TASK_BOARD.yaml"
DEFAULT_OUTBOX_PATH = ROOT / "artifacts" / "task_board" / "outbox.jsonl"
ITL_ROOT = ROOT.parent / "intelligence-theory-lab"

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import codex_project_autopilot  # noqa: E402

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - only exercised when PyYAML is absent.
    yaml = None


class GuardError(Exception):
    def __init__(self, code: str, message: str, **details: Any) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True)
class CommandResult:
    args: list[str]
    returncode: int
    stdout: str
    stderr: str


class GuardRunner:
    def run(self, args: list[str]) -> CommandResult:
        try:
            completed = subprocess.run(
                args,
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            return CommandResult(args=args, returncode=127, stdout="", stderr=str(exc))
        return CommandResult(
            args=args,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def which(self, name: str) -> str | None:
        return shutil.which(name)


def _load_yaml(path: Path, *, code: str) -> dict[str, Any]:
    if yaml is None:
        raise GuardError("yaml_unavailable", "PyYAML is required")
    if not path.exists():
        raise GuardError(code, f"Required file not found: {path}", path=str(path))
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise GuardError(f"invalid_{code}", f"YAML file must contain an object: {path}", path=str(path))
    return payload


def _json_or_none(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _run_text(runner: GuardRunner, args: list[str]) -> dict[str, Any]:
    result = runner.run(args)
    return {
        "args": args,
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def _path_allowed(path: str, prefixes: list[str]) -> bool:
    return codex_project_autopilot._path_allowed(path, prefixes)  # noqa: SLF001


def _as_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _load_mutation_scope(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "status": "not_configured",
            "path": None,
            "allowed_mutation_paths": [],
            "expected_mutation_surface": [],
            "raw": {},
        }
    payload = _load_yaml(path, code="missing_mutation_scope")
    allowed_paths = _as_str_list(payload.get("allowed_mutation_paths"))
    if not allowed_paths:
        raise GuardError(
            "invalid_mutation_scope",
            "Mutation scope must declare at least one allowed_mutation_paths entry",
            path=str(path),
        )
    return {
        "status": "loaded",
        "path": str(path),
        "task": payload.get("task"),
        "task_id": payload.get("task_id"),
        "task_kind": payload.get("task_kind"),
        "requested_action_id": payload.get("requested_action_id"),
        "source_route_revision_id": payload.get("source_route_revision_id"),
        "source_route_fingerprint": payload.get("source_route_fingerprint"),
        "expected_target_route_revision_id": payload.get("expected_target_route_revision_id"),
        "independent_red_review_required": payload.get("independent_red_review_required"),
        "red_review_ref": payload.get("red_review_ref"),
        "allowed_mutation_paths": allowed_paths,
        "forbidden_mutation_paths": _as_str_list(payload.get("forbidden_mutation_paths")),
        "expected_mutation_surface": _as_str_list(payload.get("expected_mutation_surface")),
        "claim_ceiling": payload.get("claim_ceiling"),
        "auto_remote_anchor": payload.get("auto_remote_anchor"),
        "migration_exception": payload.get("migration_exception") or {},
        "raw": payload,
    }


def _is_staged(status: str) -> bool:
    return bool(status) and status[0] not in {" ", "?"}


def _candidate_scope_prefix(path: str) -> str:
    normalized = path.strip().strip('"').replace("\\", "/").strip("/")
    if not normalized:
        return "(root)"
    parts = [part for part in normalized.split("/") if part]
    if len(parts) >= 4 and parts[:3] == ["docs", "codex", "tasks"]:
        return "/".join(parts[:4]) + "/"
    if len(parts) >= 4 and parts[0] == "legacy":
        return "/".join(parts[:4]) + "/"
    if len(parts) >= 2 and parts[0] == "legacy":
        return "/".join(parts[:2]) + "/"
    if len(parts) >= 3 and parts[0] in {"artifacts", ".agents"}:
        return "/".join(parts[:3]) + "/"
    if len(parts) >= 2 and parts[0] in {"scripts", "docs", "tests", "EgoOperator", "EgoDesktop"}:
        return "/".join(parts[:2]) + "/"
    if len(parts) >= 2 and parts[0].startswith("."):
        return "/".join(parts[:2]) + "/"
    if len(parts) >= 2:
        return parts[0] + "/"
    return parts[0]


def _common_component_count(path: str, prefix: str) -> int:
    path_parts = [part for part in path.strip("/").replace("\\", "/").split("/") if part]
    prefix_parts = [part for part in prefix.strip("/").replace("\\", "/").split("/") if part]
    count = 0
    for left, right in zip(path_parts, prefix_parts):
        if left != right:
            break
        count += 1
    return count


def _nearest_allowed_prefix(path: str, prefixes: list[str]) -> str | None:
    scored = [(_common_component_count(path, prefix), len(prefix), prefix) for prefix in prefixes]
    scored = [item for item in scored if item[0] > 0]
    if not scored:
        return None
    return max(scored)[2]


def _unsafe_analysis(
    entries: list[dict[str, Any]],
    *,
    allowed_prefixes: list[str],
    local_only_prefixes: list[str],
) -> dict[str, Any]:
    groups_by_prefix: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        prefix = _candidate_scope_prefix(str(entry.get("path") or ""))
        groups_by_prefix.setdefault(prefix, []).append(entry)

    groups: list[dict[str, Any]] = []
    nearest_candidates = allowed_prefixes + local_only_prefixes
    for prefix, values in sorted(groups_by_prefix.items()):
        groups.append(
            {
                "path_prefix": prefix,
                "count": len(values),
                "staged_count": sum(1 for item in values if _is_staged(str(item.get("status") or ""))),
                "local_only_count": sum(1 for item in values if _path_allowed(str(item.get("path") or ""), local_only_prefixes)),
                "nearest_allowed_prefix": _nearest_allowed_prefix(prefix, nearest_candidates),
                "candidate_scoped_path": prefix,
                "reason": "not covered by allowed_mutation_paths or task-scoped mutation scope",
                "sample": values[:5],
            }
        )
    return {
        "groups": groups,
        "candidate_scoped_paths": sorted({group["candidate_scoped_path"] for group in groups}),
    }


def _repo_from_origin(remote: str) -> str | None:
    remote = remote.strip()
    patterns = [
        r"^git@github\.com:(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        r"^https://github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?/?$",
    ]
    for pattern in patterns:
        match = re.match(pattern, remote)
        if match:
            return match.group("repo")
    return None


def read_program_state(path: Path) -> dict[str, Any]:
    payload = _load_yaml(path, code="missing_program_state")
    program = payload.get("program")
    if not isinstance(program, dict):
        raise GuardError("invalid_program_state", "PROGRAM_STATE_UNIFIED.yaml is missing program section")
    keys = [
        "current_phase",
        "current_layer",
        "highest_evidence_level",
        "verification_level",
        "next_minimal_action",
        "status_owner",
    ]
    return {key: program.get(key) for key in keys}


def compute_route_fingerprint(program_state: dict[str, Any]) -> str:
    program = program_state.get("program") or {}
    route_guard = dict(program_state.get("route_guard") or {})
    route_guard.pop("route_fingerprint", None)
    canonical_subset = {
        "program": {
            "current_phase": program.get("current_phase"),
            "next_minimal_action": program.get("next_minimal_action"),
        },
        "route_guard": route_guard,
    }
    encoded = json.dumps(
        canonical_subset,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def science_authority_pin_status(program_state: dict[str, Any], runner: GuardRunner) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    if not route_guard:
        return {"status": "unavailable", "expected_head": None, "actual_head": None, "failed_pins": ["route_guard"]}
    science_axis = (route_guard.get("authority_axes") or {}).get("science_attribution") or {}
    expected_head = str(science_axis.get("pinned_head") or "")
    head = runner.run(["git", "-C", str(ITL_ROOT), "rev-parse", "HEAD"])
    failures: list[str] = []
    if head.returncode != 0 or head.stdout.strip() != expected_head:
        failures.append("head")
    for name, pin in (route_guard.get("science_source_pins") or {}).items():
        if not isinstance(pin, dict):
            failures.append(str(name))
            continue
        path = str(pin.get("path") or "")
        oid = runner.run(["git", "-C", str(ITL_ROOT), "rev-parse", f"HEAD:{path}"])
        if oid.returncode != 0 or oid.stdout.strip() != str(pin.get("git_blob_oid") or ""):
            failures.append(str(name))
    return {
        "status": "pass" if not failures else "fail",
        "expected_head": expected_head,
        "actual_head": head.stdout.strip() if head.returncode == 0 else None,
        "failed_pins": failures,
    }


def build_route_guard_readback(program_state: dict[str, Any], runner: GuardRunner) -> dict[str, Any]:
    program = program_state.get("program") or {}
    route_guard = program_state.get("route_guard") or {}
    binding = route_guard.get("allowed_action_binding") or {}
    authorizations = route_guard.get("authorizations") or {}
    lineage = route_guard.get("lineage_inventory") or {}
    red_review = route_guard.get("red_review") or {}
    computed = compute_route_fingerprint(program_state)
    stored = route_guard.get("route_fingerprint")
    pin_status = science_authority_pin_status(program_state, runner)
    return {
        "route_revision_id": route_guard.get("route_revision_id"),
        "route_fingerprint": computed if stored == computed else f"MISMATCH:{computed}",
        "current_phase": program.get("current_phase"),
        "current_layer": program.get("current_layer"),
        "allowed_next_action_ids": binding.get("allowed_next_action_ids") or [],
        "forbidden_action_classes": binding.get("forbidden_action_classes") or [],
        "authorized_implementation_targets": authorizations.get("authorized_implementation_targets") or [],
        "undisposed_lineage_count": lineage.get("undisposed_count"),
        "unresolved_review_blockers": red_review.get("unresolved_review_blockers") or [],
        "science_authority_pin_status": pin_status.get("status"),
    }


def classify_red_review_triggers(
    *,
    changed_paths: list[str],
    diff_added_lines: dict[str, list[str]],
    policy: dict[str, Any],
    generated_view_matches: set[str] | None = None,
) -> list[dict[str, Any]]:
    generated_view_matches = generated_view_matches or set()
    authority_patterns = [str(item) for item in policy.get("authority_path_patterns") or []]
    claim_terms = [str(item).casefold() for item in policy.get("diff_added_claim_terms") or []]
    generated_views = {str(item) for item in policy.get("generated_view_paths") or []}
    triggers: list[dict[str, Any]] = []
    for path in sorted(set(changed_paths)):
        if path in generated_views and path in generated_view_matches:
            continue
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in authority_patterns):
            triggers.append({"type": "authority_path", "path": path})
        added = "\n".join(diff_added_lines.get(path) or []).casefold()
        matched = sorted(term for term in claim_terms if term and term in added)
        if matched:
            triggers.append({"type": "diff_added_claim", "path": path, "terms": matched})
    return triggers


def validate_route_mutation_scope(
    *,
    scope: dict[str, Any],
    program_state: dict[str, Any],
    changed_paths: list[str],
    added_task_dirs: list[str],
    red_triggers: list[dict[str, Any]],
    execution_requested: bool = False,
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    route_guard = program_state.get("route_guard") or {}
    binding = route_guard.get("allowed_action_binding") or {}
    required_scope_fields = (
        "task_id",
        "task_kind",
        "requested_action_id",
        "source_route_revision_id",
        "source_route_fingerprint",
        "expected_target_route_revision_id",
        "independent_red_review_required",
        "red_review_ref",
    )
    missing_fields = [key for key in required_scope_fields if key not in scope]
    if missing_fields:
        blockers.append({"reason": "route_mutation_scope_fields_missing", "fields": missing_fields})
    task_id = scope.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        blockers.append({"reason": "mutation_scope_single_task_id_required"})
    requested_action = scope.get("requested_action_id")
    current_fingerprint = compute_route_fingerprint(program_state)
    current_revision = route_guard.get("route_revision_id")
    exact_migration_id = "EGO-ROUTE-8692-SUPERSESSION-AND-EGODESKTOP-AUTHORITY-ARCHIVE-001A"
    migration = scope.get("migration_exception") or {}
    migration_completion = (
        task_id == exact_migration_id
        and requested_action == exact_migration_id
        and scope.get("source_route_fingerprint") == "026535337949d5ea2857805e5d9e0d2b6bfae016154fbf58587eafcea6411aa3"
        and scope.get("expected_target_route_revision_id") == current_revision
        and "docs/PROGRAM_STATE_UNIFIED.yaml" in changed_paths
        and migration.get("exact_task_id") == exact_migration_id
        and migration.get("enabled") is False
        and migration.get("consumed") is True
        and migration.get("wildcard_allowed") is False
        and migration.get("operator_override_allowed") is False
    )
    if scope.get("source_route_fingerprint") != current_fingerprint and not migration_completion:
        blockers.append(
            {
                "reason": "stale_route_fingerprint",
                "source": scope.get("source_route_fingerprint"),
                "current": current_fingerprint,
            }
        )
    expected_source_revision = "PRE_ROUTE_GUARD_MIGRATION" if migration_completion else current_revision
    if scope.get("source_route_revision_id") != expected_source_revision:
        blockers.append(
            {
                "reason": "source_route_revision_mismatch",
                "source": scope.get("source_route_revision_id"),
                "expected": expected_source_revision,
            }
        )
    allowed_actions = binding.get("allowed_next_action_ids") or []
    if requested_action not in allowed_actions and not migration_completion:
        blockers.append({"reason": "ROUTE_ACTION_NOT_BOUND", "requested_action_id": requested_action})
    if len(set(added_task_dirs)) > 1:
        blockers.append({"reason": "multiple_task_directories", "task_dirs": sorted(set(added_task_dirs))})
    allowed_paths = [str(item) for item in scope.get("allowed_mutation_paths") or []]
    out_of_scope = [path for path in changed_paths if not _path_allowed(path, allowed_paths)]
    if out_of_scope:
        blockers.append({"reason": "scope_outside_authority_or_route_file", "paths": out_of_scope})
    if scope.get("expected_target_route_revision_id") != current_revision:
        blockers.append(
            {
                "reason": "target_route_revision_mismatch",
                "expected": scope.get("expected_target_route_revision_id"),
                "actual": current_revision,
            }
        )
    if red_triggers and scope.get("independent_red_review_required") is not True:
        blockers.append({"reason": "independent_red_review_not_required_by_scope"})
    if red_triggers and not str(scope.get("red_review_ref") or "").strip():
        blockers.append({"reason": "authority_change_without_red_review_ref", "triggers": red_triggers})
    task_kind = str(scope.get("task_kind") or "")
    if current_revision == "EGO_ROUTE_8692_SUPERSESSION_001A" and "governance" in task_kind and not migration_completion:
        blockers.append({"reason": "governance_only_successor_forbidden"})
    if task_id == exact_migration_id and not migration_completion:
        blockers.append({"reason": "migration_exception_reused_or_invalid"})
    implementation_targets = binding.get("authorized_implementation_targets") or []
    if implementation_targets:
        blockers.append({"reason": "unauthorized_implementation_targets_nonempty"})
    if execution_requested or bool((scope.get("raw") or {}).get("execution_requested")):
        if binding.get("execution_authorized") is not True:
            blockers.append({"reason": "card_execution_not_authorized"})
    if requested_action == "bank_EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A":
        if task_kind != "executable_candidate_independent_headroom":
            blockers.append({"reason": "card2_task_kind_mismatch"})
    return blockers


def read_codex_memory(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise GuardError("missing_codex_memory", f"CODEX_MEMORY.md not found: {path}", path=str(path))
    text = path.read_text(encoding="utf-8")
    preference_ids = re.findall(r"\|\s*(pref-[A-Za-z0-9_-]+)\s*\|", text)
    truth_ids = re.findall(r"\|\s*(project-[A-Za-z0-9_-]+)\s*\|", text)
    bootstrap_commands = re.findall(
        r"python(?:3)?\s+scripts/(?:codex_memory|codex_session_guard)\.py\s+[A-Za-z-]+(?:\s+--[A-Za-z-]+(?:\s+\w+)?)?",
        text,
    )
    return {
        "path": str(path),
        "source_of_truth_declared": ".codex/memory/project_truth.jsonl" in text,
        "preference_ids": preference_ids,
        "truth_ids": truth_ids,
        "bootstrap_commands": bootstrap_commands,
        "has_auto_push_preference": "pref-auto-push-remote" in preference_ids,
        "has_session_discipline_preference": "pref-session-discipline" in preference_ids,
    }


def read_git_state(runner: GuardRunner) -> dict[str, Any]:
    remote = _run_text(runner, ["git", "remote", "get-url", "origin"])
    branch = _run_text(runner, ["git", "branch", "--show-current"])
    head = _run_text(runner, ["git", "rev-parse", "--short", "HEAD"])
    upstream = _run_text(runner, ["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"])
    ahead = behind = None
    if upstream["returncode"] == 0:
        parts = upstream["stdout"].split()
        if len(parts) == 2 and all(part.isdigit() for part in parts):
            behind = int(parts[0])
            ahead = int(parts[1])
    return {
        "origin_url": remote["stdout"] if remote["returncode"] == 0 else None,
        "origin_repo": _repo_from_origin(remote["stdout"]) if remote["returncode"] == 0 else None,
        "branch": branch["stdout"] if branch["returncode"] == 0 else None,
        "head": head["stdout"] if head["returncode"] == 0 else None,
        "upstream": {
            "returncode": upstream["returncode"],
            "ahead": ahead,
            "behind": behind,
            "raw": upstream["stdout"],
            "stderr": upstream["stderr"],
        },
    }


def contract_remote_check(contract: codex_project_autopilot.ProjectContract, git_state: dict[str, Any]) -> dict[str, Any]:
    origin_repo = git_state.get("origin_repo")
    if not origin_repo:
        return {"status": "origin_unavailable", "contract_repo": contract.repo, "origin_repo": None}
    if str(contract.repo).casefold() != str(origin_repo).casefold():
        return {
            "status": "remote_contract_mismatch",
            "contract_repo": contract.repo,
            "origin_repo": origin_repo,
        }
    return {"status": "ok", "contract_repo": contract.repo, "origin_repo": origin_repo}


def dirty_state(
    contract: codex_project_autopilot.ProjectContract,
    runner: GuardRunner,
    *,
    mutation_scope: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local_only = [
        str(item)
        for item in (contract_summary_extra(contract).get("closeout_gate", {}).get("local_only_path_prefixes") or [])
    ]
    task_scoped_allowed = _as_str_list((mutation_scope or {}).get("allowed_mutation_paths"))
    entries = codex_project_autopilot.dirty_entries(runner)
    buckets: dict[str, list[dict[str, Any]]] = {
        "scoped": [],
        "task_scoped": [],
        "local_only": [],
        "unsafe": [],
        "staged": [],
    }
    local_only_staged: list[dict[str, Any]] = []
    for entry in entries:
        data = entry.to_dict()
        if _is_staged(entry.status):
            buckets["staged"].append(data)
        if _path_allowed(entry.path, local_only):
            buckets["local_only"].append(data)
            if _is_staged(entry.status):
                local_only_staged.append(data)
        elif _path_allowed(entry.path, contract.allowed_mutation_paths):
            buckets["scoped"].append(data)
        elif _path_allowed(entry.path, task_scoped_allowed):
            buckets["task_scoped"].append(data)
        else:
            buckets["unsafe"].append(data)
    return {
        "total_dirty": len(entries),
        "counts": {name: len(values) for name, values in buckets.items()},
        "samples": {name: values[:20] for name, values in buckets.items()},
        "local_only_staged": {
            "count": len(local_only_staged),
            "sample": local_only_staged[:20],
        },
        "unsafe_analysis": _unsafe_analysis(
            buckets["unsafe"],
            allowed_prefixes=contract.allowed_mutation_paths + task_scoped_allowed,
            local_only_prefixes=local_only,
        ),
        "allowance": {
            "contract_allowed_count": len(contract.allowed_mutation_paths),
            "task_scoped_allowed_count": len(task_scoped_allowed),
            "task_scope_source": (mutation_scope or {}).get("path"),
        },
        "has_task_board_change": any(entry.path == "Tasks/TASK_BOARD.yaml" for entry in entries),
    }


def contract_summary_extra(contract: codex_project_autopilot.ProjectContract) -> dict[str, Any]:
    if yaml is None or not contract.path.exists():
        return {}
    payload = yaml.safe_load(contract.path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def task_board_snapshot(contract: codex_project_autopilot.ProjectContract, board_path: Path) -> dict[str, Any]:
    report = codex_project_autopilot.command_local_report(contract, board_path)
    plan_next = codex_project_autopilot.command_local_plan_next(contract, board_path)
    return {
        "board_path": str(board_path),
        "counts": report.get("counts") or {},
        "plan_next": {
            "status": plan_next.get("status"),
            "stop_reason": plan_next.get("stop_reason"),
            "next_task": plan_next.get("next_task"),
            "valid_stop": plan_next.get("stop_reason") in {"no_ready_task", "no_ready_issue"},
        },
    }


def github_availability(
    contract: codex_project_autopilot.ProjectContract,
    runner: GuardRunner,
) -> dict[str, Any]:
    if runner.which("gh") is None:
        return {
            "status": "unavailable",
            "reason": "gh_not_found",
            "repo": contract.repo,
            "project_owner": contract.owner,
            "project_number": contract.project_number,
        }
    result = runner.run([sys.executable, str(SCRIPT_DIR / "codex_project_autopilot.py"), "doctor"])
    parsed = _json_or_none(result.stdout)
    if result.returncode != 0:
        return {
            "status": "unavailable",
            "reason": (parsed or {}).get("error") or "doctor_failed",
            "returncode": result.returncode,
            "doctor": parsed,
            "stderr": result.stderr.strip(),
        }
    return {
        "status": "ok",
        "reason": None,
        "doctor": parsed,
        "repo": contract.repo,
        "project_owner": contract.owner,
        "project_number": contract.project_number,
    }


def _dirty_paths(runner: GuardRunner) -> list[str]:
    return sorted({entry.path for entry in codex_project_autopilot.dirty_entries(runner)})


def _added_task_directories(runner: GuardRunner) -> list[str]:
    directories: set[str] = set()
    for entry in codex_project_autopilot.dirty_entries(runner):
        path = entry.path.replace("\\", "/")
        if not path.startswith("docs/codex/tasks/"):
            continue
        parts = path.split("/")
        if len(parts) < 4 or parts[3] == "TASK_LANE_INDEX.md":
            continue
        status = entry.status
        if status == "??" or "A" in status[:2]:
            directories.add("/".join(parts[:4]))
    return sorted(directories)


def _diff_added_lines(runner: GuardRunner, changed_paths: list[str]) -> dict[str, list[str]]:
    output: dict[str, list[str]] = {}
    for path in changed_paths:
        proc = runner.run(["git", "diff", "--unified=0", "HEAD", "--", path])
        lines = [
            line[1:]
            for line in proc.stdout.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        ]
        if not lines:
            absolute = ROOT / path
            status = next(
                (entry.status for entry in codex_project_autopilot.dirty_entries(runner) if entry.path == path),
                "",
            )
            if status == "??" and absolute.is_file():
                lines = absolute.read_text(encoding="utf-8", errors="replace").splitlines()
        output[path] = lines
    return output


def _generated_view_matches(program_state: dict[str, Any]) -> set[str]:
    codex_dir = SCRIPT_DIR / "codex"
    if str(codex_dir) not in sys.path:
        sys.path.insert(0, str(codex_dir))
    try:
        from program_state_common import (  # type: ignore
            EVIDENCE_LEDGER_INDEX_PATH,
            load_yaml as load_program_yaml,
            render_status_markdown,
            render_summary_markdown,
        )
        from route_convergence_common import (  # type: ignore
            render_repo_surface_map,
            render_task_lane_index,
        )
    except Exception:
        return set()
    try:
        evidence_index = load_program_yaml(EVIDENCE_LEDGER_INDEX_PATH)
        expected = {
            "docs/STATUS.md": render_status_markdown(program_state, evidence_index),
            "artifacts/reports/program_state_summary.md": render_summary_markdown(program_state, evidence_index),
            "docs/codex/tasks/TASK_LANE_INDEX.md": render_task_lane_index(program_state),
            "docs/REPO_SURFACE_MAP.md": render_repo_surface_map(program_state),
        }
    except Exception:
        return set()
    matches: set[str] = set()
    for relative, rendered in expected.items():
        path = ROOT / relative
        if path.is_file() and path.read_text(encoding="utf-8") == rendered:
            matches.add(relative)
    return matches


def build_bootstrap_snapshot(
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    program_state_path: Path = DEFAULT_PROGRAM_STATE_PATH,
    codex_memory_path: Path = DEFAULT_CODEX_MEMORY_PATH,
    task_board_path: Path | None = None,
    mutation_scope_path: Path | None = None,
    runner: GuardRunner | None = None,
) -> dict[str, Any]:
    runner = runner or GuardRunner()
    contract = codex_project_autopilot.load_contract(contract_path)
    board_path = task_board_path or codex_project_autopilot.task_board_path(contract)
    git_state = read_git_state(runner)
    mutation_scope = _load_mutation_scope(mutation_scope_path)
    full_program_state = _load_yaml(program_state_path, code="missing_program_state")
    return {
        "status": "ok",
        "schema_version": "codex.session_bootstrap.v1",
        "program_state": read_program_state(program_state_path),
        "route_guard_readback": build_route_guard_readback(full_program_state, runner),
        "codex_memory": read_codex_memory(codex_memory_path),
        "project_contract": codex_project_autopilot.contract_summary(contract),
        "session_bootstrap": contract_summary_extra(contract).get("session_bootstrap") or {},
        "task_mutation_scope": mutation_scope,
        "git": git_state,
        "remote_contract_check": contract_remote_check(contract, git_state),
        "dirty_state": dirty_state(contract, runner, mutation_scope=mutation_scope),
        "task_board": task_board_snapshot(contract, board_path),
        "github_sync": github_availability(contract, runner),
        "claim_ceiling": (
            "Codex session bootstrap local workflow candidate pass; does not prove EgoOperator runtime efficacy, "
            "stable user benefit, live autonomy, durable memory efficacy, proactive messaging, or consciousness."
        ),
    }


def build_closeout_check(
    *,
    contract_path: Path = DEFAULT_CONTRACT_PATH,
    program_state_path: Path = DEFAULT_PROGRAM_STATE_PATH,
    codex_memory_path: Path = DEFAULT_CODEX_MEMORY_PATH,
    task_board_path: Path | None = None,
    mutation_scope_path: Path | None = None,
    runner: GuardRunner | None = None,
) -> dict[str, Any]:
    snapshot = build_bootstrap_snapshot(
        contract_path=contract_path,
        program_state_path=program_state_path,
        codex_memory_path=codex_memory_path,
        task_board_path=task_board_path,
        mutation_scope_path=mutation_scope_path,
        runner=runner,
    )
    contract = codex_project_autopilot.load_contract(contract_path)
    extra = contract_summary_extra(contract)
    gate = extra.get("closeout_gate") if isinstance(extra.get("closeout_gate"), dict) else {}
    dirty = snapshot["dirty_state"]
    git_state = snapshot["git"]
    blockers: list[dict[str, Any]] = []
    publication_pending: dict[str, Any] | None = None

    if snapshot["remote_contract_check"]["status"] != "ok":
        blockers.append({"reason": "remote_contract_mismatch", **snapshot["remote_contract_check"]})
    if git_state.get("branch") != contract.default_branch:
        blockers.append(
            {
                "reason": "wrong_branch",
                "branch": git_state.get("branch"),
                "expected": contract.default_branch,
            }
        )
    upstream = git_state.get("upstream") or {}
    if upstream.get("returncode") == 0 and int(upstream.get("ahead") or 0) > 0:
        if (snapshot.get("task_mutation_scope") or {}).get("auto_remote_anchor") == "forbidden":
            publication_pending = {"reason": "push_pending", "ahead": upstream.get("ahead"), "blocking": False}
        else:
            blockers.append({"reason": "push_pending", "ahead": upstream.get("ahead")})
    elif upstream.get("returncode") != 0:
        blockers.append({"reason": "upstream_unavailable", "stderr": upstream.get("stderr")})

    if dirty["counts"]["unsafe"]:
        blockers.append(
            {
                "reason": "unsafe_dirty_paths",
                "sample": dirty["samples"]["unsafe"],
                "groups": dirty.get("unsafe_analysis", {}).get("groups") or [],
                "candidate_scoped_paths": dirty.get("unsafe_analysis", {}).get("candidate_scoped_paths") or [],
            }
        )

    if dirty.get("local_only_staged", {}).get("count"):
        blockers.append({"reason": "local_only_paths_staged", **dirty["local_only_staged"]})

    if bool(contract.commit_policy.get("require_scoped_staging")) and dirty["counts"]["staged"] == 0:
        blockers.append({"reason": "no_staged_changes", "required": True})

    github = snapshot["github_sync"]
    if dirty.get("has_task_board_change") and github.get("status") != "ok":
        blockers.append(
            {
                "reason": "remote_sync_unavailable",
                "github_status": github,
                "outbox_required": True,
                "outbox_path": str(Path(str(contract.task_state.get("outbox_path") or DEFAULT_OUTBOX_PATH))),
            }
        )

    full_program_state = _load_yaml(program_state_path, code="missing_program_state")
    changed_paths = _dirty_paths(runner)
    policy = extra.get("route_guard_policy") if isinstance(extra.get("route_guard_policy"), dict) else {}
    generated_matches = _generated_view_matches(full_program_state) if policy else set()
    red_triggers = (
        classify_red_review_triggers(
            changed_paths=changed_paths,
            diff_added_lines=_diff_added_lines(runner, changed_paths),
            policy=policy,
            generated_view_matches=generated_matches,
        )
        if policy
        else []
    )
    scope = snapshot.get("task_mutation_scope") or {}
    route_scope_present = all(
        scope.get(key) is not None
        for key in (
            "task_id",
            "task_kind",
            "requested_action_id",
            "source_route_fingerprint",
            "expected_target_route_revision_id",
        )
    )
    route_scope_blockers: list[dict[str, Any]] = []
    if route_scope_present:
        route_scope_blockers = validate_route_mutation_scope(
            scope=scope,
            program_state=full_program_state,
            changed_paths=changed_paths,
            added_task_dirs=_added_task_directories(runner),
            red_triggers=red_triggers,
        )
        blockers.extend(route_scope_blockers)

    return {
        "status": "ok",
        "schema_version": "codex.closeout_gate.v1",
        "eligible": not blockers,
        "blocked_reasons": blockers,
        "required_closeout": {
            "scoped_staging": bool(contract.commit_policy.get("require_scoped_staging")),
            "push": bool(contract.commit_policy.get("push")),
            "task_board_github_mirror": bool(gate.get("require_task_board_github_sync", True)),
            "verification_commands": gate.get("verification_commands") or [],
        },
        "task_mutation_scope": snapshot.get("task_mutation_scope") or {},
        "route_guard_readback": snapshot.get("route_guard_readback") or {},
        "route_scope_blockers": route_scope_blockers,
        "red_review_triggers": red_triggers,
        "generated_view_matches": sorted(generated_matches),
        "publication_pending": publication_pending,
        "dirty_state": dirty,
        "remote_contract_check": snapshot["remote_contract_check"],
        "github_sync": github,
        "task_board": snapshot["task_board"],
        "claim_ceiling": "Codex closeout gate local workflow candidate pass only.",
    }


def render_markdown(payload: dict[str, Any]) -> str:
    if payload.get("schema_version") == "codex.closeout_gate.v1":
        blockers = payload.get("blocked_reasons") or []
        dirty = payload.get("dirty_state") or {}
        counts = dirty.get("counts") or {}
        scope = payload.get("task_mutation_scope") or {}
        lines = [
            "# Codex Closeout Gate",
            "",
            f"- eligible: `{str(payload.get('eligible')).lower()}`",
            f"- blockers: `{len(blockers)}`",
            f"- remote_contract: `{payload.get('remote_contract_check', {}).get('status')}`",
            f"- github_sync: `{payload.get('github_sync', {}).get('status')}`",
            f"- task_board_plan_next: `{payload.get('task_board', {}).get('plan_next', {}).get('stop_reason')}`",
            f"- dirty_scoped/task_scoped/local_only/unsafe: `{counts.get('scoped')}` / `{counts.get('task_scoped')}` / `{counts.get('local_only')}` / `{counts.get('unsafe')}`",
            f"- mutation_scope: `{scope.get('status')}` `{scope.get('path')}`",
            f"- route_revision_id: `{payload.get('route_guard_readback', {}).get('route_revision_id')}`",
            f"- route_fingerprint: `{payload.get('route_guard_readback', {}).get('route_fingerprint')}`",
            f"- red_review_triggers: `{len(payload.get('red_review_triggers') or [])}`",
            f"- publication_pending: `{payload.get('publication_pending')}`",
            "",
            "## Blocked Reasons",
        ]
        if blockers:
            for blocker in blockers:
                lines.append(f"- `{blocker.get('reason')}`")
        else:
            lines.append("- none")
        unsafe_groups = []
        for blocker in blockers:
            if blocker.get("reason") == "unsafe_dirty_paths":
                unsafe_groups = blocker.get("groups") or []
                break
        if unsafe_groups:
            lines.extend(["", "## Unsafe Dirty Path Groups"])
            for group in unsafe_groups[:20]:
                lines.append(
                    "- "
                    f"`{group.get('path_prefix')}` "
                    f"count=`{group.get('count')}` staged=`{group.get('staged_count')}` "
                    f"nearest_allowed=`{group.get('nearest_allowed_prefix')}` "
                    f"candidate_scope=`{group.get('candidate_scoped_path')}`"
                )
        return "\n".join(lines) + "\n"

    program = payload.get("program_state") or {}
    task_board = payload.get("task_board") or {}
    dirty = payload.get("dirty_state") or {}
    route = payload.get("route_guard_readback") or {}
    lines = [
        "# Codex Boot Snapshot",
        "",
        f"- current_phase: `{program.get('current_phase')}`",
        f"- current_layer: `{program.get('current_layer')}`",
        f"- highest_evidence_level: `{program.get('highest_evidence_level')}`",
        f"- next_minimal_action: {program.get('next_minimal_action')}",
        f"- origin_repo: `{payload.get('git', {}).get('origin_repo')}`",
        f"- branch: `{payload.get('git', {}).get('branch')}`",
        f"- remote_contract: `{payload.get('remote_contract_check', {}).get('status')}`",
        f"- dirty_total: `{dirty.get('total_dirty')}`",
        f"- dirty_scoped/task_scoped/local_only/unsafe: `{dirty.get('counts', {}).get('scoped')}` / `{dirty.get('counts', {}).get('task_scoped')}` / `{dirty.get('counts', {}).get('local_only')}` / `{dirty.get('counts', {}).get('unsafe')}`",
        f"- task_board_counts: `{task_board.get('counts')}`",
        f"- autopilot_plan_next: `{task_board.get('plan_next', {}).get('status')}` / `{task_board.get('plan_next', {}).get('stop_reason')}`",
        f"- github_sync: `{payload.get('github_sync', {}).get('status')}` / `{payload.get('github_sync', {}).get('reason')}`",
        "",
        "## route_guard_readback",
        "",
        f"- route_revision_id: `{route.get('route_revision_id')}`",
        f"- route_fingerprint: `{route.get('route_fingerprint')}`",
        f"- current_phase: `{route.get('current_phase')}`",
        f"- current_layer: `{route.get('current_layer')}`",
        f"- allowed_next_action_ids: `{route.get('allowed_next_action_ids')}`",
        f"- forbidden_action_classes: `{route.get('forbidden_action_classes')}`",
        f"- authorized_implementation_targets: `{route.get('authorized_implementation_targets')}`",
        f"- undisposed_lineage_count: `{route.get('undisposed_lineage_count')}`",
        f"- unresolved_review_blockers: `{route.get('unresolved_review_blockers')}`",
        f"- science_authority_pin_status: `{route.get('science_authority_pin_status')}`",
        "",
        "## Claim Ceiling",
        payload.get("claim_ceiling", ""),
    ]
    return "\n".join(lines) + "\n"


def write_payload(payload: dict[str, Any], *, fmt: str, out_path: str | None, stream: TextIO) -> None:
    text = render_markdown(payload) if fmt == "markdown" else json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if out_path:
        path = Path(out_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    stream.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="EGO Codex session bootstrap and closeout guard")
    parser.add_argument("--contract", default=str(DEFAULT_CONTRACT_PATH))
    parser.add_argument("--program-state", default=str(DEFAULT_PROGRAM_STATE_PATH))
    parser.add_argument("--codex-memory", default=str(DEFAULT_CODEX_MEMORY_PATH))
    parser.add_argument("--task-board", default=None)
    parser.add_argument("--mutation-scope", default=None, help="Optional task-scoped mutation allowance YAML")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("bootstrap", "closeout-check"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--format", choices=["json", "markdown"], default="json")
        sub.add_argument("--out")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    runner: GuardRunner | None = None,
    stdout: TextIO | None = None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    out = stdout or sys.stdout
    runner = runner or GuardRunner()
    try:
        kwargs = {
            "contract_path": Path(args.contract),
            "program_state_path": Path(args.program_state),
            "codex_memory_path": Path(args.codex_memory),
            "task_board_path": Path(args.task_board) if args.task_board else None,
            "mutation_scope_path": Path(args.mutation_scope) if args.mutation_scope else None,
            "runner": runner,
        }
        if args.command == "bootstrap":
            payload = build_bootstrap_snapshot(**kwargs)
        elif args.command == "closeout-check":
            payload = build_closeout_check(**kwargs)
        else:  # pragma: no cover - argparse enforces command choices.
            raise GuardError("unknown_command", f"Unknown command: {args.command}")
        write_payload(payload, fmt=args.format, out_path=args.out, stream=out)
        return 0
    except (GuardError, codex_project_autopilot.AutopilotError) as exc:
        code = getattr(exc, "code", "guard_error")
        message = getattr(exc, "message", str(exc))
        details = getattr(exc, "details", {})
        write_payload({"status": "error", "error": code, "message": message, **details}, fmt="json", out_path=None, stream=out)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
