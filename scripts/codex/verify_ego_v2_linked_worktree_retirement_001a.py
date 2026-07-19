#!/usr/bin/env python3
"""Callable evidence producer for controlled linked-worktree retirement."""

from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Iterable, Mapping

import yaml


TASK_ID = "EGO-V2-LINKED-WORKTREE-RETIREMENT-001A-R2"
CARD_SHA256 = "0fef18a8a25483f2ff703dcf7a4a35841449ca4b11cf0ac3c087fdafbc63c043"
MAIN_BASE = "ac11d4baec78fb4acc0e9f13f391f16a6a76c644"
MAIN_BASE_TREE = "60a8e260029845e2eeaa1e401dc3c9f029d651fd"
V2_BRANCH = "codex/ego-v2-product-first-001a"
V2_HEAD = "722a9cd11b5f6349242bcf8a7cf2e48f67122b3c"
V2_TREE = "8da84639fa9c849f64a59506dbbccfb554d38cfd"
ITL_HEAD = "d338bc522d4be6e1f6f4733466b0688c0a494acf"
CHECKPOINT_BRANCH = "codex/non-live-negative-anti-zeno-checkpoint-20260718"
CHECKPOINT_HEAD = "35db7ab27ce1815f96fe53ffd64b89aab5101c49"
CHECKPOINT_PARENT = "089ab5ef27431eb5ace4ff4795f57f08fd052779"
OLD_ROUTE_FINGERPRINT = "324609c8afcb444c65e5995845318286e1dfc26882cc2b8e860d224add4aa501"
V2_WORKTREE = Path("D:/Project/AIProject/MyProject/Ego-v2-product-first-001a")
BUNDLE_NAME = "EGO-V2-ROLLBACK-722a9cd1.bundle"
RETENTION_MODE = "BRANCH_REF_PLUS_VERIFIED_EXTERNAL_BUNDLE"
CLAIM_CEILING = (
    "The redundant clean linked checkout was retired while its exact rollback "
    "branch, commit, tree, and verified external bundle remained reconstructable; "
    "Ego main remained the sole product-development worktree."
)
FORBIDDEN_CLAIMS = (
    "This does not prove runtime integration, product readiness, learning, memory "
    "causality, initiative, agency, subjectivity, consciousness, or electronic life."
)
EXPECTED_PATHS = [
    "README.md",
    "docs/ACTIVE_CONTEXT_PACK.md",
    "docs/MAINLINE_QUICKSTART.md",
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
    "scripts/codex_session_guard.py",
    "scripts/codex/verify_route_convergence.py",
    "scripts/tests/test_route_governance_supersession.py",
    "scripts/tests/test_codex_session_guard.py",
    "scripts/codex/verify_ego_v2_linked_worktree_retirement_001a.py",
    "scripts/tests/test_verify_ego_v2_linked_worktree_retirement_001a.py",
    "docs/codex/tasks/ego-v2-linked-worktree-retirement-001a/STAGE_CARD.md",
    "docs/codex/tasks/ego-v2-linked-worktree-retirement-001a/MUTATION_SCOPE.yaml",
    "docs/codex/tasks/ego-v2-linked-worktree-retirement-001a/COLLISION_RECORD.md",
    "docs/codex/tasks/ego-v2-linked-worktree-retirement-001a/PHASE_RED_REVIEW.json",
    "artifacts/EGO-V2-LINKED-WORKTREE-RETIREMENT-001A/retirement_receipt.json",
    "artifacts/EGO-V2-LINKED-WORKTREE-RETIREMENT-001A/validation_report.json",
    "artifacts/EGO-V2-LINKED-WORKTREE-RETIREMENT-001A/failure_manifest.json",
    "artifacts/EGO-V2-LINKED-WORKTREE-RETIREMENT-001A/claim_ceiling.txt",
]
ARTIFACT_NAMES = {
    "retirement_receipt.json",
    "validation_report.json",
    "failure_manifest.json",
    "claim_ceiling.txt",
}
CLOSED_SWITCHES = {
    "enabled": False,
    "default_enabled": False,
    "mainline_connected": False,
    "runtime_mainline_connected": False,
    "runtime_authority": "none",
    "science_weight": 0,
    "remote_anchor": False,
    "auto_remote_anchor": "forbidden",
    "proactive_action_enabled": False,
    "initiative_executor_authorized": False,
    "background_dispatch": False,
    "external_side_effects": False,
    "llm": "forbidden",
    "network": "forbidden",
}
PINNED_INPUTS = {
    "scripts/codex_session_guard.py": "9e10af881b1d89718bd2a2ee8a48bf1ab331a812817288dfa5e4128912a46c9c",
    "docs/PROGRAM_STATE_UNIFIED.yaml": "9d6b2a1f1dd7dfa2d198a074caf7dbbfc1054ee86590ef001864f7e02e57f6d0",
    "scripts/tests/test_route_governance_supersession.py": "83b28fd121496c2d500dcd10d24d2df79cc29874e87397b983aefd6a61164fb8",
    "scripts/tests/test_codex_session_guard.py": "52582ad22f388ae04b89e638c3934965560b2db4bea16f4ffa99118d90b771aa",
    "README.md": "ac5223b6bb3367676cd90def9804a5fe1e8299d0a4d8ead55e219a07d8422d00",
    "docs/ACTIVE_CONTEXT_PACK.md": "70728366f9d7f3921b6a2e8d888cc3c329c8bafc641a14993ea73c5497b1e287",
    "docs/MAINLINE_QUICKSTART.md": "eb343b886b5ae72bb09fce272c99b599f901edba1d9edcf5b90630caa7fbe862",
    "docs/codex/tasks/TASK_LANE_INDEX.md": "74a7d12b3fb0e63472ae25bc910859a54c9afc49e5a95cc4d955e52cd7521b2f",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _file_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": _sha256(raw)}


def _code_path_hash() -> str:
    return _file_record(Path(__file__))["sha256"]


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _run(command: list[str], *, cwd: Path | None = None) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return {
        "command": command,
        "cwd": str(cwd) if cwd else None,
        "exit_code": completed.returncode,
        "stdout": completed.stdout.splitlines(),
        "stderr": completed.stderr.splitlines(),
    }


def _git(repo: Path, *args: str) -> dict[str, Any]:
    return _run(["git", "-c", "core.longpaths=true", "-C", str(repo), *args])


def _stdout_one(record: Mapping[str, Any]) -> str | None:
    lines = record.get("stdout") or []
    return str(lines[0]).strip() if record.get("exit_code") == 0 and len(lines) == 1 else None


def _utc_run_id(phase: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"ego-v2-linked-worktree-retirement-001a-{phase}-{now}"


def aggregate_checks(checks: Mapping[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    for name, value in checks.items():
        if type(value) is not bool:
            raise ValueError(f"boolean computed check required: {name}")
        if value is not True:
            failed.append(str(name))
    return {"verdict": "pass" if not failed else "fail", "failed_checks": sorted(failed)}


def parse_worktree_porcelain(lines: Iterable[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    for raw in [*lines, ""]:
        line = raw.rstrip("\n")
        if not line:
            if current:
                result.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value if value else True
    return result


def _status_paths(repo: Path) -> tuple[list[str], dict[str, Any]]:
    record = _git(
        repo,
        "-c",
        "core.longpaths=true",
        "--no-optional-locks",
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    paths: list[str] = []
    for line in record["stdout"]:
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return sorted(set(paths)), record


def collect_changed_paths(
    repo: Path, expected_paths: list[str]
) -> tuple[list[str], dict[str, Any], list[str]]:
    """Collect Git-visible paths plus exact required evidence hidden by ignore rules."""
    paths, status = _status_paths(repo)
    collected = set(paths)
    ignored_required: list[str] = []
    for relative in expected_paths:
        if relative in collected or not (repo / relative).is_file():
            continue
        ignored = _git(repo, "check-ignore", "--", relative)
        if ignored["exit_code"] == 0:
            collected.add(relative)
            ignored_required.append(relative)
    return sorted(collected), status, sorted(ignored_required)


def find_path_matches(value: Any, target: str, path: str = "$") -> list[dict[str, str]]:
    wanted = target.replace("\\", "/").casefold()
    matches: list[dict[str, str]] = []
    if isinstance(value, str):
        if wanted in value.replace("\\", "/").casefold():
            matches.append({"path": path, "value": value})
    elif isinstance(value, Mapping):
        for key, nested in value.items():
            matches.extend(find_path_matches(str(key), target, f"{path}/<key>"))
            matches.extend(find_path_matches(nested, target, f"{path}/{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            matches.extend(find_path_matches(nested, target, f"{path}/{index}"))
    return matches


def scan_itl_route_objects(itl_repo: Path) -> dict[str, Any]:
    root = itl_repo / "artifacts" / "ROUTE-STATE-MACHINE-001A"
    parsed = 0
    errors: list[dict[str, str]] = []
    matches: list[dict[str, str]] = []
    for candidate in sorted([*root.rglob("*.json"), *root.rglob("*.jsonl")]):
        try:
            if candidate.suffix == ".jsonl":
                payload = [
                    json.loads(line)
                    for line in candidate.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            else:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            parsed += 1
            for match in find_path_matches(payload, str(V2_WORKTREE)):
                match["file"] = str(candidate.relative_to(root)).replace("\\", "/")
                matches.append(match)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append({"file": str(candidate), "error": repr(exc)})
    return {
        "producer_function": "scan_itl_route_objects",
        "parsed_files": parsed,
        "parse_errors": errors,
        "matches": matches,
    }


def _text_scan_itl(itl_repo: Path) -> dict[str, Any]:
    root = itl_repo / "artifacts" / "ROUTE-STATE-MACHINE-001A"
    records = []
    for spelling in (str(V2_WORKTREE).replace("\\", "/"), str(V2_WORKTREE).replace("/", "\\")):
        record = _run(["rg", "-n", "--hidden", "--fixed-strings", spelling, str(root)])
        records.append(record)
    return {"producer_function": "rg fixed-string dual-separator scan", "records": records}


def _load_state(repo: Path) -> dict[str, Any]:
    return yaml.safe_load((repo / "docs" / "PROGRAM_STATE_UNIFIED.yaml").read_text(encoding="utf-8"))


def expected_authority(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "worktree": None,
        "worktree_registered": False,
        "former_worktree": str(V2_WORKTREE).replace("\\", "/"),
        "former_worktree_disposition": "RETIRED_BY_ORDINARY_GIT_WORKTREE_REMOVE",
        "branch": V2_BRANCH,
        "head": V2_HEAD,
        "tree": V2_TREE,
        "active_development_authority": False,
        "frozen": True,
        "retention_mode": RETENTION_MODE,
        "external_bundle": {
            "path": bundle.get("path"),
            "bytes": bundle.get("bytes"),
            "sha256": bundle.get("sha256"),
        },
        "retirement_task_id": TASK_ID,
        "retirement_receipt": "artifacts/EGO-V2-LINKED-WORKTREE-RETIREMENT-001A/retirement_receipt.json",
    }


def validate_authority_shape(authority: Any, bundle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if authority != expected_authority(bundle):
        errors.append("linked_v2_rollback_reference_mismatch")
    return errors


def validate_bundle_binding(
    receipt: Mapping[str, Any], *, actual_sha256: str, actual_bytes: int
) -> list[str]:
    errors: list[str] = []
    bundle = receipt.get("bundle") or {}
    if bundle.get("sha256") != actual_sha256:
        errors.append("bundle_sha256_mismatch")
    if bundle.get("bytes") != actual_bytes:
        errors.append("bundle_bytes_mismatch")
    if receipt.get("reconstructed_head") != V2_HEAD:
        errors.append("reconstructed_head_mismatch")
    if receipt.get("reconstructed_tree") != V2_TREE:
        errors.append("reconstructed_tree_mismatch")
    if receipt.get("verdict") != "pass":
        errors.append("bundle_receipt_not_pass")
    return sorted(errors)


def validate_card_binding(actual_sha256: str) -> list[str]:
    return [] if actual_sha256 == CARD_SHA256 else ["retirement_card_sha256_mismatch"]


def _base_record(phase: str, inputs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "run_id": _utc_run_id(phase),
        "producer_function": f"verify_ego_v2_linked_worktree_retirement_001a.{phase}",
        "input_artifacts": inputs,
        "aggregation_rule": "pass iff every named callable Git, route, bundle, and boundary check is true",
        "code_path_hash": _code_path_hash(),
    }


def capture_preflight(repo: Path, itl_repo: Path, external_dir: Path, card: Path) -> dict[str, Any]:
    worktrees_record = _git(repo, "worktree", "list", "--porcelain")
    worktrees = parse_worktree_porcelain(worktrees_record["stdout"])
    repo_paths, repo_status = _status_paths(repo)
    v2_paths, v2_status = _status_paths(V2_WORKTREE)
    itl_paths, itl_status = _status_paths(itl_repo)
    state = _load_state(repo)
    authority = state["route_guard"]["v2_authority"]
    parsed_scan = scan_itl_route_objects(itl_repo)
    text_scan = _text_scan_itl(itl_repo)
    input_pins = {path: _file_record(repo / path) for path in PINNED_INPUTS}
    refs = {
        "main_head": _stdout_one(_git(repo, "rev-parse", "HEAD")),
        "main_tree": _stdout_one(_git(repo, "rev-parse", "HEAD^{tree}")),
        "v2_head": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{V2_BRANCH}")),
        "v2_tree": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{V2_BRANCH}^{{tree}}")),
        "checkpoint_head": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{CHECKPOINT_BRANCH}")),
        "checkpoint_parent": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{CHECKPOINT_BRANCH}^")),
        "itl_head": _stdout_one(_git(itl_repo, "rev-parse", "HEAD")),
    }
    checks = {
        "card_hash_matches": _file_record(card)["sha256"] == CARD_SHA256,
        "main_head_matches": refs["main_head"] == MAIN_BASE,
        "main_tree_matches": refs["main_tree"] == MAIN_BASE_TREE,
        "main_clean": repo_status["exit_code"] == 0 and repo_paths == [],
        "v2_directory_exists": V2_WORKTREE.is_dir(),
        "v2_head_matches": refs["v2_head"] == V2_HEAD,
        "v2_tree_matches": refs["v2_tree"] == V2_TREE,
        "v2_clean": v2_status["exit_code"] == 0 and v2_paths == [],
        "itl_head_matches": refs["itl_head"] == ITL_HEAD,
        "itl_clean": itl_status["exit_code"] == 0 and itl_paths == [],
        "checkpoint_head_matches": refs["checkpoint_head"] == CHECKPOINT_HEAD,
        "checkpoint_parent_matches": refs["checkpoint_parent"] == CHECKPOINT_PARENT,
        "linked_worktree_registered": any(
            str(item.get("worktree", "")).replace("\\", "/").casefold()
            == str(V2_WORKTREE).replace("\\", "/").casefold()
            and item.get("HEAD") == V2_HEAD
            and item.get("branch") == f"refs/heads/{V2_BRANCH}"
            for item in worktrees
        ),
        "pinned_input_bytes_match": all(
            input_pins[path]["sha256"] == expected for path, expected in PINNED_INPUTS.items()
        ),
        "stored_route_fingerprint_matches": state["route_guard"].get("route_fingerprint") == OLD_ROUTE_FINGERPRINT,
        "only_validation_action_live": authority.get("allowed_next_actions") == ["run_route_state_machine_validation"],
        "v2_switches_closed": all(authority.get(key) == value for key, value in CLOSED_SWITCHES.items()),
        "parsed_itl_path_scan_clean": parsed_scan["parse_errors"] == [] and parsed_scan["matches"] == [],
        "text_itl_path_scan_clean": all(
            record["exit_code"] == 1 and record["stdout"] == [] for record in text_scan["records"]
        ),
    }
    aggregation = aggregate_checks(checks)
    result = {
        **_base_record("capture_preflight", [_file_record(card), *input_pins.values()]),
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "checks": checks,
        "refs": refs,
        "worktrees": worktrees,
        "status_commands": {"main": repo_status, "v2": v2_status, "itl": itl_status},
        "input_pins": input_pins,
        "parsed_itl_path_scan": parsed_scan,
        "text_itl_path_scan": text_scan,
        "route_fingerprint": state["route_guard"].get("route_fingerprint"),
        "allowed_next_actions": authority.get("allowed_next_actions"),
        "closed_switches": {key: authority.get(key) for key in CLOSED_SWITCHES},
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(external_dir / "preflight.json", result)
    return result


def verify_bundle(
    repo: Path, external_dir: Path, reconstruction_dir: Path, *, create_clone: bool
) -> dict[str, Any]:
    preflight_path = external_dir / "preflight.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    bundle = external_dir / BUNDLE_NAME
    bundle_record = _file_record(bundle)
    verify_record = _git(repo, "bundle", "verify", str(bundle))
    heads_record = _git(repo, "bundle", "list-heads", str(bundle))
    clone_record: dict[str, Any] | None = None
    if create_clone:
        if reconstruction_dir.exists():
            raise RuntimeError(f"reconstruction target already exists: {reconstruction_dir}")
        reconstruction_dir.parent.mkdir(parents=True, exist_ok=True)
        clone_record = _run(
            [
                "git", "-c", "core.longpaths=true", "clone", "--no-local", "--branch",
                V2_BRANCH, str(bundle), str(reconstruction_dir),
            ]
        )
    head = _stdout_one(_git(reconstruction_dir, "rev-parse", "HEAD"))
    tree = _stdout_one(_git(reconstruction_dir, "rev-parse", "HEAD^{tree}"))
    clean_paths, long_status = _status_paths(reconstruction_dir)
    short_status = _run(
        ["git", "-C", str(reconstruction_dir), "--no-optional-locks", "status", "--porcelain=v1", "--untracked-files=all"]
    )
    origin = _stdout_one(_git(reconstruction_dir, "remote", "get-url", "origin"))
    expected_head_line = f"{V2_HEAD} refs/heads/{V2_BRANCH}"
    checks = {
        "preflight_pass": preflight.get("verdict") == "pass",
        "bundle_verify_pass": verify_record["exit_code"] == 0,
        "bundle_exact_ref_present": expected_head_line in heads_record["stdout"],
        "clone_command_pass": clone_record is None or clone_record["exit_code"] == 0,
        "reconstructed_head_matches": head == V2_HEAD,
        "reconstructed_tree_matches": tree == V2_TREE,
        "reconstructed_status_clean_with_longpaths": long_status["exit_code"] == 0 and clean_paths == [],
        "reconstruction_origin_is_bundle": origin is not None
        and Path(origin).resolve() == bundle.resolve(),
    }
    aggregation = aggregate_checks(checks)
    result = {
        **_base_record("verify_bundle", [_file_record(preflight_path), bundle_record]),
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "checks": checks,
        "bundle": bundle_record,
        "bundle_verify": verify_record,
        "bundle_heads": heads_record,
        "clone_command": clone_record,
        "reconstruction_dir": str(reconstruction_dir),
        "reconstruction_origin": origin,
        "reconstructed_head": head,
        "reconstructed_tree": tree,
        "longpaths_status": long_status,
        "hostile_instrument_control": {
            "producer_function": "git status without core.longpaths",
            "classification": (
                "INSTRUMENT_INVALID_FILENAME_LENGTH_WITHOUT_CORE_LONGPATHS"
                if short_status["stderr"] or short_status["stdout"]
                else "NO_FILENAME_LENGTH_EFFECT_OBSERVED"
            ),
            "result": short_status,
            "corrected_longpaths_status_is_clean": clean_paths == [],
        },
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(external_dir / "bundle_verification.json", result)
    return result


def _collect_final(
    repo: Path,
    itl_repo: Path,
    external_dir: Path,
    card: Path,
    expected_paths: list[str],
) -> dict[str, Any]:
    bundle_path = external_dir / BUNDLE_NAME
    bundle_record = _file_record(bundle_path)
    card_record = _file_record(card)
    card_binding_errors = validate_card_binding(card_record["sha256"])
    bundle_receipt_path = external_dir / "bundle_verification.json"
    bundle_receipt = json.loads(bundle_receipt_path.read_text(encoding="utf-8"))
    binding_errors = validate_bundle_binding(
        bundle_receipt,
        actual_sha256=bundle_record["sha256"],
        actual_bytes=bundle_record["bytes"],
    )
    reconstruction = Path(bundle_receipt["reconstruction_dir"])
    reconstruction_paths, reconstruction_status = _status_paths(reconstruction)
    worktrees_record = _git(repo, "worktree", "list", "--porcelain")
    worktrees = parse_worktree_porcelain(worktrees_record["stdout"])
    changed_paths, status_record, ignored_required_paths = collect_changed_paths(
        repo, expected_paths
    )
    state = _load_state(repo)
    authority = state["route_guard"]["v2_authority"]
    linked = authority["worktree_authority"]["linked_v2_rollback_reference"]
    refs = {
        "main_head": _stdout_one(_git(repo, "rev-parse", "HEAD")),
        "v2_head": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{V2_BRANCH}")),
        "v2_tree": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{V2_BRANCH}^{{tree}}")),
        "checkpoint_head": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{CHECKPOINT_BRANCH}")),
        "checkpoint_parent": _stdout_one(_git(repo, "rev-parse", f"refs/heads/{CHECKPOINT_BRANCH}^")),
        "itl_head": _stdout_one(_git(itl_repo, "rev-parse", "HEAD")),
        "reconstructed_head": _stdout_one(_git(reconstruction, "rev-parse", "HEAD")),
        "reconstructed_tree": _stdout_one(_git(reconstruction, "rev-parse", "HEAD^{tree}")),
    }
    parsed_scan = scan_itl_route_objects(itl_repo)
    text_scan = _text_scan_itl(itl_repo)
    expected_bundle_projection = {
        "path": str(bundle_path).replace("\\", "/"),
        "bytes": bundle_record["bytes"],
        "sha256": bundle_record["sha256"],
    }
    checks = {
        "main_remains_base_before_commit": refs["main_head"] == MAIN_BASE,
        "r2_card_binding_pass": card_binding_errors == [],
        "retired_directory_absent": not V2_WORKTREE.exists(),
        "worktree_registry_only_main": len(worktrees) == 1
        and str(worktrees[0].get("worktree", "")).replace("\\", "/").casefold()
        == str(repo).replace("\\", "/").casefold(),
        "rollback_branch_preserved": refs["v2_head"] == V2_HEAD,
        "rollback_tree_preserved": refs["v2_tree"] == V2_TREE,
        "checkpoint_preserved": refs["checkpoint_head"] == CHECKPOINT_HEAD
        and refs["checkpoint_parent"] == CHECKPOINT_PARENT,
        "itl_head_preserved": refs["itl_head"] == ITL_HEAD,
        "bundle_binding_pass": binding_errors == [],
        "fresh_reconstruction_preserved": refs["reconstructed_head"] == V2_HEAD
        and refs["reconstructed_tree"] == V2_TREE
        and reconstruction_status["exit_code"] == 0
        and reconstruction_paths == [],
        "authority_shape_exact": validate_authority_shape(linked, expected_bundle_projection) == [],
        "only_validation_action_live": authority.get("allowed_next_actions") == ["run_route_state_machine_validation"],
        "runtime_switches_unchanged_closed": all(
            authority.get(key) == value for key, value in CLOSED_SWITCHES.items()
        ),
        "exact_changed_path_set": changed_paths == sorted(expected_paths),
        "parsed_itl_path_scan_still_clean": parsed_scan["parse_errors"] == [] and parsed_scan["matches"] == [],
        "text_itl_path_scan_still_clean": all(
            record["exit_code"] == 1 and record["stdout"] == [] for record in text_scan["records"]
        ),
    }
    aggregation = aggregate_checks(checks)
    return {
        "checks": checks,
        "verdict": aggregation["verdict"],
        "failed_checks": aggregation["failed_checks"],
        "refs": refs,
        "worktrees": worktrees,
        "changed_paths": changed_paths,
        "ignored_required_paths": ignored_required_paths,
        "status_command": status_record,
        "bundle": bundle_record,
        "card": card_record,
        "card_binding_errors": card_binding_errors,
        "bundle_binding_errors": binding_errors,
        "authority_projection": linked,
        "closed_switches": {key: authority.get(key) for key in CLOSED_SWITCHES},
        "allowed_next_actions": authority.get("allowed_next_actions"),
        "parsed_itl_path_scan": parsed_scan,
        "text_itl_path_scan": text_scan,
    }


def finalize(
    repo: Path,
    itl_repo: Path,
    external_dir: Path,
    card: Path,
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ARTIFACT_NAMES:
        path = output_dir / name
        if not path.exists():
            path.write_text("{}\n" if name.endswith(".json") else "pending\n", encoding="utf-8", newline="\n")
    final = _collect_final(repo, itl_repo, external_dir, card, EXPECTED_PATHS)
    preflight_path = external_dir / "preflight.json"
    bundle_path = external_dir / "bundle_verification.json"
    base = _base_record(
        "finalize",
        [_file_record(card), _file_record(preflight_path), _file_record(bundle_path)],
    )
    post = {
        **base,
        **final,
        "claim_ceiling": CLAIM_CEILING,
        "what_this_does_not_prove": FORBIDDEN_CLAIMS,
    }
    _write_json(external_dir / "post_removal.json", post)
    post_record = _file_record(external_dir / "post_removal.json")
    initial_instrument_failure_path = (
        external_dir / "post_removal_initial_ignored_txt_instrument_fail.json"
    )
    initial_instrument_failure_record = (
        _file_record(initial_instrument_failure_path)
        if initial_instrument_failure_path.is_file()
        else None
    )
    initial_instrument_failure = (
        json.loads(initial_instrument_failure_path.read_text(encoding="utf-8-sig"))
        if initial_instrument_failure_record is not None
        else None
    )
    validation = {
        **base,
        "input_artifacts": [
            *base["input_artifacts"],
            post_record,
            *([initial_instrument_failure_record] if initial_instrument_failure_record else []),
        ],
        **final,
        "claim_ceiling": CLAIM_CEILING,
        "what_this_does_not_prove": FORBIDDEN_CLAIMS,
    }
    receipt = {
        **base,
        "input_artifacts": [*base["input_artifacts"], post_record],
        "verdict": final["verdict"],
        "failed_checks": final["failed_checks"],
        "retired_worktree": str(V2_WORKTREE).replace("\\", "/"),
        "retirement_method": "git worktree remove without --force",
        "rollback_branch": V2_BRANCH,
        "rollback_head": V2_HEAD,
        "rollback_tree": V2_TREE,
        "bundle": final["bundle"],
        "worktrees_after": final["worktrees"],
        "claim_ceiling": CLAIM_CEILING,
    }
    bundle_receipt = json.loads(bundle_path.read_text(encoding="utf-8"))
    failure_manifest = {
        **base,
        "input_artifacts": [
            *base["input_artifacts"],
            post_record,
            *([initial_instrument_failure_record] if initial_instrument_failure_record else []),
        ],
        "scoped_failed_checks": final["failed_checks"],
        "preserved_negative_evidence": {
            "raw_filesystem_deletion": "rejected because it cannot clear Git registry or prove recovery",
            "filename_length_instrument_control": bundle_receipt.get("hostile_instrument_control"),
            "ignored_required_evidence_control": {
                "paths": final["ignored_required_paths"],
                "reason": (
                    "the repository-wide *.txt ignore rule hides the required claim-ceiling file "
                    "from ordinary status; the callable collector requires the exact on-disk path "
                    "and a positive git check-ignore result"
                ),
            },
            "initial_finalize_instrument_failure": {
                "artifact": initial_instrument_failure_record,
                "verdict": (
                    initial_instrument_failure.get("verdict")
                    if initial_instrument_failure is not None
                    else None
                ),
                "failed_checks": (
                    initial_instrument_failure.get("failed_checks")
                    if initial_instrument_failure is not None
                    else []
                ),
            },
        },
        "full_repository_suite": "not_claimed_by_this_scoped_retirement_verifier",
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "retirement_receipt.json", receipt)
    _write_json(output_dir / "validation_report.json", validation)
    _write_json(output_dir / "failure_manifest.json", failure_manifest)
    (output_dir / "claim_ceiling.txt").write_text(
        CLAIM_CEILING + "\n" + FORBIDDEN_CLAIMS + "\n", encoding="utf-8", newline="\n"
    )
    actual = {path.name for path in output_dir.iterdir() if path.is_file()}
    if actual != ARTIFACT_NAMES:
        raise RuntimeError(f"artifact output set mismatch: {sorted(actual)}")
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("capture-preflight", "verify-bundle", "finalize"))
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--itl-root", type=Path, required=True)
    parser.add_argument("--external-dir", type=Path, required=True)
    parser.add_argument("--card", type=Path)
    parser.add_argument("--reconstruction-dir", type=Path)
    parser.add_argument("--create-clone", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    if args.phase == "capture-preflight":
        if args.card is None:
            parser.error("--card is required")
        result = capture_preflight(args.repo_root, args.itl_root, args.external_dir, args.card)
    elif args.phase == "verify-bundle":
        if args.reconstruction_dir is None:
            parser.error("--reconstruction-dir is required")
        result = verify_bundle(
            args.repo_root, args.external_dir, args.reconstruction_dir, create_clone=args.create_clone
        )
    else:
        if args.output_dir is None:
            parser.error("--output-dir is required")
        if args.card is None:
            parser.error("--card is required")
        result = finalize(
            args.repo_root,
            args.itl_root,
            args.external_dir,
            args.card,
            args.output_dir,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["verdict"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
