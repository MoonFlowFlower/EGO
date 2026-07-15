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
import tempfile
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
CARD2_SYNC_TASK_ID = "EGO-PET-WORLD-V1-CARD2-ITL-AUTHORITY-SYNC-001A"
CARD2_SYNC_ACTION_ID = "sync_EGO_pet_world_v1_card2_bank_admission_under_separate_task"
CARD2_BANK_ACTION_ID = "bank_EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A"
CARD2_TASK_ID = "EGO-PET-WORLD-V1-CAPABILITY-HEADROOM-001A"
CARD2_TASK_PREFIX = "docs/codex/tasks/ego-pet-world-v1-capability-headroom-001a/"
CARD2_SYNC_ROUTE_REVISION = "EGO_PET_WORLD_V1_CARD2_ITL_AUTHORITY_SYNC_001A"
CARD2_SYNC_TASK_PREFIX = "docs/codex/tasks/ego-pet-world-v1-card2-itl-authority-sync-001a/"
CARD2_SYNC_TASK_DIR = ROOT / "docs" / "codex" / "tasks" / "ego-pet-world-v1-card2-itl-authority-sync-001a"
VISIBLE_LIFE_TASK_ID = "EGO-VISIBLE-LIFE-PROXY-V0-ROUTE-REPLACEMENT-001A"
VISIBLE_LIFE_ROUTE_REVISION = "EGO_VISIBLE_LIFE_PROXY_V0_ROUTE_REPLACEMENT_001A"
VISIBLE_LIFE_TRANSITION_ACTION_ID = "replace_defective_card2_admission_with_visible_life_proxy_v0"
VISIBLE_LIFE_IMPLEMENT_ACTION_ID = "implement_EGO-VISIBLE-LIFE-PROXY-V0-001A"
VISIBLE_LIFE_TASK_PREFIX = "docs/codex/tasks/ego-visible-life-proxy-v0-route-replacement-001a/"
VISIBLE_LIFE_PHASE_A_SCOPE_PATH = f"{VISIBLE_LIFE_TASK_PREFIX}MUTATION_SCOPE_PHASE_A.yaml"
VISIBLE_LIFE_PHASE_B_SCOPE_PATH = f"{VISIBLE_LIFE_TASK_PREFIX}MUTATION_SCOPE_PHASE_B.yaml"
VISIBLE_LIFE_CROSSWALK_PATH = f"{VISIBLE_LIFE_TASK_PREFIX}ITL_CLOSURE_CROSSWALK.json"
VISIBLE_LIFE_RED_REVIEW_PATH = f"{VISIBLE_LIFE_TASK_PREFIX}PHASE_A_RED_REVIEW.json"
VISIBLE_LIFE_CROSSWALK_PRODUCER_CODE_PATH_HASH = "35150699a116035d45ed61575ff55fd12577ca249b96a9dfc3e1fcc9885c3e48"
VISIBLE_LIFE_ITL_COMMIT = "55706c734a2bf25ba1d9d2aa273283ed4dc39802"
VISIBLE_LIFE_ITL_ROUTE_ID = "EGO-PET-WORLD-V1-CAPABILITY-CARD-BANK-ADMISSION-001A"
VISIBLE_LIFE_TARGETS = [
    "labs/ego_life_playground_v0/__init__.py",
    "labs/ego_life_playground_v0/engine.py",
    "labs/ego_life_playground_v0/store.py",
    "labs/ego_life_playground_v0/app.py",
    "scripts/run_ego_life_playground_v0.py",
    "tests/test_ego_life_playground_v0.py",
]
VISIBLE_LIFE_FORBIDDEN_PREFIXES = [
    "EgoDesktop/",
    "EgoOperator/",
    "packages/",
    "deployment/",
    "providers/",
]
VISIBLE_LIFE_FORBIDDEN_ACTIONS = [
    "modify_EgoDesktop_or_EgoOperator",
    "add_LLM_or_network_integration",
    "enable_runtime_or_mainline",
    "grant_runtime_authority",
    "register_or_satisfy_science_successor",
    "claim_mechanism_learning_agency_or_electronic_life",
    "repair_reopen_or_rerun_closed_card2_action",
    "push_tag_or_remote_anchor",
]
VISIBLE_LIFE_CORE_TASK_ID = "EGO-VISIBLE-LIFE-PROXY-V0-CORE-ADOPTION-001A"
VISIBLE_LIFE_CORE_ROUTE_REVISION = "EGO_VISIBLE_LIFE_PROXY_V0_CORE_ADOPTION_001A"
VISIBLE_LIFE_CORE_STALE_ADOPT_ACTION_ID = "adopt_EGO-VISIBLE-LIFE-PROXY-V0_as_product_development_core"
VISIBLE_LIFE_CORE_SYNC_ACTION_ID = "sync_EGO_visible_life_proxy_v0_product_core_authority_under_separate_task"
VISIBLE_LIFE_CORE_DRAFT_V1_ACTION_ID = (
    "draft_EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A_only_after_EGO_sync_validation"
)
VISIBLE_LIFE_CORE_TASK_PREFIX = "docs/codex/tasks/ego-visible-life-proxy-v0-core-adoption-001a/"
VISIBLE_LIFE_CORE_SCOPE_PATH = f"{VISIBLE_LIFE_CORE_TASK_PREFIX}MUTATION_SCOPE.yaml"
VISIBLE_LIFE_CORE_RED_REVIEW_PATH = f"{VISIBLE_LIFE_CORE_TASK_PREFIX}PHASE_A_RED_REVIEW.json"
VISIBLE_LIFE_CORE_CROSSWALK_PATH = f"{VISIBLE_LIFE_CORE_TASK_PREFIX}ITL_AUTHORITY_CROSSWALK.json"
VISIBLE_LIFE_CORE_ITL_COMMIT = "619bff5fd9400bba00002af26f65ce73894a9dce"
VISIBLE_LIFE_CORE_ITL_ROUTE_ID = "EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-001A"
VISIBLE_LIFE_CORE_ITL_OBJECTS = {
    "product_axis_state": {
        "path": "artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json",
        "git_blob_oid": "fe416f3f2a81b8bc3c7931700c2b100970c73cb6",
        "git_blob_payload_sha256": "4055052a8f4022b01d0f419cb2956f5d3e5acbe336bcaab0999f947b0b16065a",
    },
    "product_core_state": {
        "path": (
            "artifacts/ROUTE-STATE-MACHINE-001A/routes/"
            "EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-001A/state.json"
        ),
        "git_blob_oid": "6c285f5361583ea397e54a4951b886ee06c09df7",
        "git_blob_payload_sha256": "6b7e8fe55679ce6530e3fd9556cc55eb05bec1876d38d198c2e912fdd0eff36e",
    },
    "product_core_closure": {
        "path": (
            "artifacts/ROUTE-STATE-MACHINE-001A/routes/"
            "EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-001A/closure.json"
        ),
        "git_blob_oid": "5c48e69919dd374c3e7939eaeb1c29faf6bfb679",
        "git_blob_payload_sha256": "fc528cebae00b61cabc11056775e928eca8df407439833839addef00c0d4672c",
    },
    "product_core_events": {
        "path": (
            "artifacts/ROUTE-STATE-MACHINE-001A/routes/"
            "EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-001A/events.jsonl"
        ),
        "git_blob_oid": "2cec0ff395adacf95e8964b4adb55bd2f6be563f",
        "git_blob_payload_sha256": "7b050e777d63967d33a2aef01136d7259f929dd439f93f1507d7394430eab571",
    },
    "product_core_validation_report": {
        "path": (
            "artifacts/ROUTE-STATE-MACHINE-001A/routes/"
            "EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-001A/adoption_validation_report.json"
        ),
        "git_blob_oid": "b70d20265749f4051af0e8624e50e1620f2e68cd",
        "git_blob_payload_sha256": "2178d0a6af9ffe919eac599e7cf04168b17235002ef456a3383704f7e2b9d1a7",
    },
    "product_core_transition_card": {
        "path": "docs/codex/tasks/ITL-EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-TRANSITION-001A.md",
        "git_blob_oid": "54d877947e089bf88479c97a2f3f3b07a5ad6f6a",
        "git_blob_payload_sha256": "27abba96094f31c0b0c14471cee08a77029aafed7cfe90f6ebd61e799f75f997",
    },
    "product_core_red_receipt": {
        "path": (
            "artifacts/ITL-EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-TRANSITION-001A/"
            "red_precheck.json"
        ),
        "git_blob_oid": "b5eb5b5cb506939b5e10f95636330534407bea60",
        "git_blob_payload_sha256": "7d613f32f52277a7d4c97a1a86b186f0532409784bfda7859cf60225ce5cec32",
    },
}
VISIBLE_LIFE_CORE_BASELINE_COMMIT = "546e3639299d7b11b599df3d00645666a6953bac"
VISIBLE_LIFE_CORE_BASELINE_PARENT = "d5d98ac0783a7e67b6d003b460470bdf4350d4bd"
VISIBLE_LIFE_CORE_BASELINE_TREE = "fe79061dca2991c822cf2b0b5547a08d9b4682f9"
VISIBLE_LIFE_CORE_BASELINE_DIR = "artifacts/EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A"
VISIBLE_LIFE_CORE_BASELINE_REFS = {
    "manifest_path": f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_baseline_manifest.json",
    "trace_path": f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_trigger_trace.jsonl",
    "database_path": f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_trigger.sqlite3",
    "validation_report_path": f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_baseline_validation_report.json",
    "validator_path": "scripts/codex/verify_ego_life_core_v0_baseline.py",
}
VISIBLE_LIFE_CORE_SYNC_PATHS = [
    f"{VISIBLE_LIFE_CORE_TASK_PREFIX}STAGE_CARD.md",
    f"{VISIBLE_LIFE_CORE_TASK_PREFIX}COLLISION_RECORD.md",
    f"{VISIBLE_LIFE_CORE_TASK_PREFIX}MUTATION_SCOPE.yaml",
    VISIBLE_LIFE_CORE_CROSSWALK_PATH,
    VISIBLE_LIFE_CORE_RED_REVIEW_PATH,
    f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_baseline_manifest.json",
    f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_trigger.sqlite3",
    f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_trigger_trace.jsonl",
    f"{VISIBLE_LIFE_CORE_BASELINE_DIR}/core_baseline_validation_report.json",
    "docs/PROGRAM_STATE_UNIFIED.yaml",
    "artifacts/reports/program_state_summary.md",
    "docs/STATUS.md",
    "docs/codex/tasks/TASK_LANE_INDEX.md",
    "docs/REPO_SURFACE_MAP.md",
    "scripts/codex_session_guard.py",
    "scripts/codex/verify_route_convergence.py",
    "scripts/codex/verify_ego_life_core_v0_baseline.py",
    "scripts/tests/test_codex_session_guard.py",
    "scripts/tests/test_route_governance_supersession.py",
    "scripts/tests/test_verify_ego_life_core_v0_baseline.py",
]
VISIBLE_LIFE_CORE_FORBIDDEN_ACTIONS = [
    "reuse_implement_EGO-VISIBLE-LIFE-PROXY-V0-001A",
    "create_parallel_visible_life_product_core",
    "implement_EGO-LIFE-KERNEL-V1-CONTINUITY-PLAYGROUND-001A",
    "modify_EgoDesktop_or_EgoOperator",
    "add_LLM_or_network_integration",
    "enable_runtime_or_runtime_mainline",
    "grant_runtime_authority",
    "register_or_satisfy_science_successor",
    "claim_mechanism_learning_agency_or_electronic_life",
    "repair_reopen_or_rerun_closed_card2_action",
    "push_tag_or_remote_anchor",
]
_VISIBLE_LIFE_CORE_EVIDENCE_CACHE: dict[tuple[Any, ...], dict[str, Any]] = {}

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


def _git_repo(
    repo: Path,
    args: list[str],
    *,
    text: bool = True,
) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=text,
        check=False,
    )


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def flatten_json_leaves(value: Any, pointer: str = "") -> list[tuple[str, Any]]:
    if isinstance(value, dict) and value:
        leaves: list[tuple[str, Any]] = []
        for key in sorted(value):
            leaves.extend(flatten_json_leaves(value[key], f"{pointer}/{_json_pointer_escape(str(key))}"))
        return leaves
    if isinstance(value, list) and value:
        leaves = []
        for index, item in enumerate(value):
            leaves.extend(flatten_json_leaves(item, f"{pointer}/{index}"))
        return leaves
    return [(pointer or "/", value)]


def _source_pin_records(route_guard: dict[str, Any]) -> list[dict[str, Any]]:
    authority = route_guard.get("authority_source") or {}
    records: list[dict[str, Any]] = []
    for name, pin in sorted((authority.get("objects") or {}).items()):
        if isinstance(pin, dict):
            records.append({"name": str(name), **pin})
    return records


def read_itl_authority_objects(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    authority = route_guard.get("authority_source") or {}
    pinned_commit = str(authority.get("pinned_commit") or "")
    errors: list[str] = []
    if not pinned_commit:
        return {"status": "fail", "errors": ["missing_itl_authority_commit"], "payloads": {}}
    commit_probe = _git_repo(ITL_ROOT, ["cat-file", "-e", f"{pinned_commit}^{{commit}}"])
    if commit_probe.returncode != 0:
        return {"status": "fail", "errors": ["missing_itl_authority_commit"], "payloads": {}}
    payloads: dict[str, Any] = {}
    input_artifacts: list[dict[str, Any]] = []
    for pin in _source_pin_records(route_guard):
        name = str(pin.get("name") or "")
        path = str(pin.get("path") or "")
        expected_oid = str(pin.get("git_blob_oid") or "")
        expected_sha = str(pin.get("git_blob_payload_sha256") or "")
        oid_probe = _git_repo(ITL_ROOT, ["rev-parse", f"{pinned_commit}:{path}"])
        actual_oid = oid_probe.stdout.strip() if oid_probe.returncode == 0 else ""
        if actual_oid != expected_oid:
            errors.append(f"itl_object_oid_mismatch:{name}")
            continue
        blob_probe = _git_repo(ITL_ROOT, ["cat-file", "blob", expected_oid], text=False)
        raw = blob_probe.stdout if blob_probe.returncode == 0 else b""
        actual_sha = hashlib.sha256(raw).hexdigest()
        if actual_sha != expected_sha:
            errors.append(f"itl_object_payload_mismatch:{name}")
            continue
        if path.endswith(".json"):
            try:
                payloads[name] = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                errors.append(f"itl_object_json_invalid:{name}")
                continue
        else:
            payloads[name] = raw.decode("utf-8")
        input_artifacts.append(
            {
                "name": name,
                "repo": "intelligence-theory-lab",
                "commit": pinned_commit,
                "path": path,
                "git_blob_oid": expected_oid,
                "git_blob_payload_sha256": expected_sha,
            }
        )
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "pinned_commit": pinned_commit,
        "payloads": payloads,
        "input_artifacts": input_artifacts,
    }


def _script_code_path_hash() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def validate_crosswalk_entries(
    *,
    route_state: dict[str, Any],
    phase_b_review_receipt: dict[str, Any],
    entries: list[dict[str, Any]],
) -> list[str]:
    expected: dict[tuple[str, str], tuple[str, str]] = {}
    for source_name, payload, target_root in (
        ("route_state", route_state, "/route_guard/transcribed_itl/route_state"),
        (
            "phase_b_review_receipt",
            phase_b_review_receipt,
            "/route_guard/transcribed_itl/phase_b_review_receipt",
        ),
    ):
        for source_pointer, leaf_value in flatten_json_leaves(payload):
            expected[(source_name, source_pointer)] = (
                f"{target_root}{'' if source_pointer == '/' else source_pointer}",
                hashlib.sha256(_canonical_json_bytes(leaf_value)).hexdigest(),
            )
    observed: dict[tuple[str, str], tuple[str, str]] = {}
    errors: list[str] = []
    for row in entries:
        key = (str(row.get("source_name") or ""), str(row.get("source_pointer") or ""))
        if key in observed:
            errors.append("field_crosswalk_duplicate_leaf")
        observed[key] = (str(row.get("target_pointer") or ""), str(row.get("value_sha256") or ""))
        if row.get("transform") != "verbatim_json_value":
            errors.append("field_crosswalk_nonverbatim_transform")
    missing = set(expected) - set(observed)
    extra = set(observed) - set(expected)
    if missing:
        errors.append("field_crosswalk_leaf_omitted")
    if extra:
        errors.append("field_crosswalk_extra_leaf")
    if any(observed.get(key) != value for key, value in expected.items() if key in observed):
        errors.append("field_crosswalk_value_or_target_mismatch")
    return sorted(set(errors))


def build_field_crosswalk_payload(
    *,
    route_state: dict[str, Any],
    phase_b_review_receipt: dict[str, Any],
    input_artifacts: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    sources = {
        "route_state": (route_state, "/route_guard/transcribed_itl/route_state"),
        "phase_b_review_receipt": (
            phase_b_review_receipt,
            "/route_guard/transcribed_itl/phase_b_review_receipt",
        ),
    }
    entries: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for source_name, (payload, target_root) in sources.items():
        leaves = flatten_json_leaves(payload)
        source_counts[source_name] = len(leaves)
        for source_pointer, leaf_value in leaves:
            entries.append(
                {
                    "source_name": source_name,
                    "source_pointer": source_pointer,
                    "target_pointer": f"{target_root}{'' if source_pointer == '/' else source_pointer}",
                    "transform": "verbatim_json_value",
                    "value_sha256": hashlib.sha256(_canonical_json_bytes(leaf_value)).hexdigest(),
                }
            )
    omitted = entries[0]
    omission_errors = validate_crosswalk_entries(
        route_state=route_state,
        phase_b_review_receipt=phase_b_review_receipt,
        entries=entries[1:],
    )
    return {
        "schema_version": "ego.itl_authority_field_crosswalk.v1",
        "task_id": CARD2_SYNC_TASK_ID,
        "run_id": run_id,
        "producer_function": "scripts.codex_session_guard.build_field_crosswalk_payload",
        "producer_code_path_hash": _script_code_path_hash(),
        "input_artifacts": input_artifacts,
        "aggregation_rule": "flatten every dict/list leaf in sorted-key/index order; require one verbatim target leaf per source leaf",
        "source_leaf_counts": source_counts,
        "total_leaf_count": len(entries),
        "entries": entries,
        "omission_positive_control": {
            "omitted_source_name": omitted["source_name"],
            "omitted_source_pointer": omitted["source_pointer"],
            "expected_count": len(entries),
            "mutated_count": len(entries) - 1,
            "rejected": "field_crosswalk_leaf_omitted" in omission_errors,
            "rejection_code": "field_crosswalk_leaf_omitted",
            "observed_error_codes": omission_errors,
        },
        "claim_ceiling": "field-by-field authority transcription evidence only",
    }


def validate_visible_life_crosswalk_entries(
    *,
    route_state: dict[str, Any],
    closure: dict[str, Any],
    entries: list[dict[str, Any]],
) -> list[str]:
    expected: dict[tuple[str, str], tuple[str, str]] = {}
    for source_name, payload, target_root in (
        ("route_state", route_state, "/route_guard/transcribed_itl/route_state"),
        ("closure", closure, "/route_guard/transcribed_itl/closure"),
    ):
        for source_pointer, leaf_value in flatten_json_leaves(payload):
            expected[(source_name, source_pointer)] = (
                f"{target_root}{'' if source_pointer == '/' else source_pointer}",
                hashlib.sha256(_canonical_json_bytes(leaf_value)).hexdigest(),
            )
    observed: dict[tuple[str, str], tuple[str, str]] = {}
    errors: list[str] = []
    for row in entries:
        key = (str(row.get("source_name") or ""), str(row.get("source_pointer") or ""))
        if key in observed:
            errors.append("visible_life_crosswalk_duplicate_leaf")
        observed[key] = (str(row.get("target_pointer") or ""), str(row.get("value_sha256") or ""))
        if row.get("transform") != "verbatim_json_value":
            errors.append("visible_life_crosswalk_nonverbatim_transform")
    if set(expected) - set(observed):
        errors.append("visible_life_crosswalk_leaf_omitted")
    if set(observed) - set(expected):
        errors.append("visible_life_crosswalk_extra_leaf")
    if any(observed.get(key) != value for key, value in expected.items() if key in observed):
        errors.append("visible_life_crosswalk_value_or_target_mismatch")
    return sorted(set(errors))


def build_visible_life_closure_crosswalk_payload(
    *,
    route_state: dict[str, Any],
    closure: dict[str, Any],
    input_artifacts: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    sources = {
        "route_state": (route_state, "/route_guard/transcribed_itl/route_state"),
        "closure": (closure, "/route_guard/transcribed_itl/closure"),
    }
    entries: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for source_name, (payload, target_root) in sources.items():
        leaves = flatten_json_leaves(payload)
        source_counts[source_name] = len(leaves)
        for source_pointer, leaf_value in leaves:
            entries.append(
                {
                    "source_name": source_name,
                    "source_pointer": source_pointer,
                    "target_pointer": f"{target_root}{'' if source_pointer == '/' else source_pointer}",
                    "transform": "verbatim_json_value",
                    "value_sha256": hashlib.sha256(_canonical_json_bytes(leaf_value)).hexdigest(),
                }
            )
    omission_errors = validate_visible_life_crosswalk_entries(
        route_state=route_state,
        closure=closure,
        entries=entries[1:],
    )
    return {
        "schema_version": "ego.visible_life_proxy.itl_closure_crosswalk.v1",
        "task_id": VISIBLE_LIFE_TASK_ID,
        "run_id": run_id,
        "producer_function": "scripts.codex_session_guard.build_visible_life_closure_crosswalk_payload",
        "producer_code_path_hash": VISIBLE_LIFE_CROSSWALK_PRODUCER_CODE_PATH_HASH,
        "input_artifacts": input_artifacts,
        "aggregation_rule": "flatten every committed ITL state/closure leaf in sorted-key/index order and require one verbatim target leaf",
        "source_leaf_counts": source_counts,
        "total_leaf_count": len(entries),
        "entries": entries,
        "omission_positive_control": {
            "omitted_source_name": entries[0]["source_name"],
            "omitted_source_pointer": entries[0]["source_pointer"],
            "expected_count": len(entries),
            "mutated_count": len(entries) - 1,
            "rejected": "visible_life_crosswalk_leaf_omitted" in omission_errors,
            "rejection_code": "visible_life_crosswalk_leaf_omitted",
            "observed_error_codes": omission_errors,
        },
        "claim_ceiling": "committed ITL closure transcription evidence only",
    }


def validate_visible_life_closure_crosswalk(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    source = read_itl_authority_objects(program_state)
    errors = list(source.get("errors") or [])
    payloads = source.get("payloads") or {}
    route_state = payloads.get("route_state")
    closure = payloads.get("closure")
    transcribed = route_guard.get("transcribed_itl") or {}
    if not isinstance(route_state, dict) or transcribed.get("route_state") != route_state:
        errors.append("visible_life_route_state_transcription_mismatch")
    if not isinstance(closure, dict) or transcribed.get("closure") != closure:
        errors.append("visible_life_closure_transcription_mismatch")
    ref = route_guard.get("closure_crosswalk") or {}
    relative = str(ref.get("path") or "")
    artifact_path = ROOT / relative
    artifact, artifact_error = _read_json_file(artifact_path)
    if artifact_error or artifact is None:
        errors.append("visible_life_crosswalk_artifact_unavailable")
        return {"status": "fail", "errors": errors, "source": source}
    raw_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if raw_sha != ref.get("artifact_payload_sha256"):
        errors.append("visible_life_crosswalk_artifact_sha256_mismatch")
    if isinstance(route_state, dict) and isinstance(closure, dict):
        expected = build_visible_life_closure_crosswalk_payload(
            route_state=route_state,
            closure=closure,
            input_artifacts=[
                {
                    **row,
                    # The closure crosswalk is a frozen V0 artifact produced
                    # against the earlier ITL object boundary.  The same Git
                    # objects remain present at the later product-axis commit,
                    # but their provenance commit must not be rewritten during
                    # the additive authority sync.
                    "commit": VISIBLE_LIFE_ITL_COMMIT,
                }
                for row in list(source.get("input_artifacts") or [])
                if row.get("name")
                in {"route_state", "events", "closure", "closure_validation_report", "task_card", "itl_red_review"}
            ],
            run_id=str(artifact.get("run_id") or ""),
        )
        if artifact != expected:
            errors.append("visible_life_crosswalk_callable_recompute_mismatch")
        errors.extend(
            validate_visible_life_crosswalk_entries(
                route_state=route_state,
                closure=closure,
                entries=list(artifact.get("entries") or []),
            )
        )
        if expected.get("omission_positive_control", {}).get("rejected") is not True:
            errors.append("visible_life_crosswalk_omission_positive_control_did_not_fire")
    return {
        "status": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "source": source,
        "artifact_payload_sha256": raw_sha,
        "total_leaf_count": artifact.get("total_leaf_count"),
        "producer_function": artifact.get("producer_function"),
        "run_id": artifact.get("run_id"),
        "aggregation_rule": artifact.get("aggregation_rule"),
        "producer_code_path_hash": artifact.get("producer_code_path_hash"),
    }


def validate_visible_life_core_crosswalk_entries(
    *,
    product_axis_state: dict[str, Any],
    product_core_state: dict[str, Any],
    product_core_closure: dict[str, Any],
    entries: list[dict[str, Any]],
) -> list[str]:
    sources = {
        "product_axis_state": (product_axis_state, "/route_guard/transcribed_itl_product/product_axis_state"),
        "product_core_state": (product_core_state, "/route_guard/transcribed_itl_product/product_core_state"),
        "product_core_closure": (
            product_core_closure,
            "/route_guard/transcribed_itl_product/product_core_closure",
        ),
    }
    expected: dict[tuple[str, str], tuple[str, str]] = {}
    for source_name, (payload, target_root) in sources.items():
        for source_pointer, leaf_value in flatten_json_leaves(payload):
            expected[(source_name, source_pointer)] = (
                f"{target_root}{'' if source_pointer == '/' else source_pointer}",
                hashlib.sha256(_canonical_json_bytes(leaf_value)).hexdigest(),
            )
    observed: dict[tuple[str, str], tuple[str, str]] = {}
    errors: list[str] = []
    for row in entries:
        key = (str(row.get("source_name") or ""), str(row.get("source_pointer") or ""))
        if key in observed:
            errors.append("visible_life_core_crosswalk_duplicate_leaf")
        observed[key] = (str(row.get("target_pointer") or ""), str(row.get("value_sha256") or ""))
        if row.get("transform") != "verbatim_json_value":
            errors.append("visible_life_core_crosswalk_nonverbatim_transform")
    if set(expected) - set(observed):
        errors.append("visible_life_core_crosswalk_leaf_omitted")
    if set(observed) - set(expected):
        errors.append("visible_life_core_crosswalk_extra_leaf")
    if any(observed.get(key) != value for key, value in expected.items() if key in observed):
        errors.append("visible_life_core_crosswalk_value_or_target_mismatch")
    return sorted(set(errors))


def build_visible_life_core_authority_crosswalk_payload(
    *,
    product_axis_state: dict[str, Any],
    product_core_state: dict[str, Any],
    product_core_closure: dict[str, Any],
    input_artifacts: list[dict[str, Any]],
    run_id: str,
) -> dict[str, Any]:
    sources = {
        "product_axis_state": (product_axis_state, "/route_guard/transcribed_itl_product/product_axis_state"),
        "product_core_state": (product_core_state, "/route_guard/transcribed_itl_product/product_core_state"),
        "product_core_closure": (
            product_core_closure,
            "/route_guard/transcribed_itl_product/product_core_closure",
        ),
    }
    entries: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    for source_name, (payload, target_root) in sources.items():
        leaves = flatten_json_leaves(payload)
        source_counts[source_name] = len(leaves)
        for source_pointer, leaf_value in leaves:
            entries.append(
                {
                    "source_name": source_name,
                    "source_pointer": source_pointer,
                    "target_pointer": f"{target_root}{'' if source_pointer == '/' else source_pointer}",
                    "transform": "verbatim_json_value",
                    "value_sha256": hashlib.sha256(_canonical_json_bytes(leaf_value)).hexdigest(),
                }
            )
    omission_errors = validate_visible_life_core_crosswalk_entries(
        product_axis_state=product_axis_state,
        product_core_state=product_core_state,
        product_core_closure=product_core_closure,
        entries=entries[1:],
    )
    return {
        "schema_version": "ego.visible_life_proxy.itl_product_core_authority_crosswalk.v1",
        "task_id": VISIBLE_LIFE_CORE_TASK_ID,
        "requested_action_id": VISIBLE_LIFE_CORE_SYNC_ACTION_ID,
        "source_commit": VISIBLE_LIFE_CORE_ITL_COMMIT,
        "source_route_id": VISIBLE_LIFE_CORE_ITL_ROUTE_ID,
        "run_id": run_id,
        "producer_function": "scripts.codex_session_guard.build_visible_life_core_authority_crosswalk_payload",
        "producer_code_path_hash": _script_code_path_hash(),
        "input_artifacts": input_artifacts,
        "aggregation_rule": (
            "flatten every committed ITL product-axis/state/closure leaf in sorted-key/index order and require "
            "one verbatim Ego target leaf"
        ),
        "source_leaf_counts": source_counts,
        "total_leaf_count": len(entries),
        "entries": entries,
        "omission_positive_control": {
            "omitted_source_name": entries[0]["source_name"],
            "omitted_source_pointer": entries[0]["source_pointer"],
            "expected_count": len(entries),
            "mutated_count": len(entries) - 1,
            "rejected": "visible_life_core_crosswalk_leaf_omitted" in omission_errors,
            "rejection_code": "visible_life_core_crosswalk_leaf_omitted",
            "observed_error_codes": omission_errors,
        },
        "claim_ceiling": "committed ITL product-axis authority transcription evidence only",
    }


def validate_visible_life_core_authority_crosswalk(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    source = read_itl_authority_objects(program_state)
    errors = list(source.get("errors") or [])
    payloads = source.get("payloads") or {}
    axis = payloads.get("product_axis_state")
    state = payloads.get("product_core_state")
    closure = payloads.get("product_core_closure")
    transcribed = route_guard.get("transcribed_itl_product") or {}
    for name, payload in (
        ("product_axis_state", axis),
        ("product_core_state", state),
        ("product_core_closure", closure),
    ):
        if not isinstance(payload, dict) or transcribed.get(name) != payload:
            errors.append(f"visible_life_core_{name}_transcription_mismatch")
    ref = route_guard.get("product_authority_crosswalk") or {}
    relative = str(ref.get("path") or "")
    artifact_path = ROOT / relative
    artifact, artifact_error = _read_json_file(artifact_path)
    if artifact_error or artifact is None:
        errors.append("visible_life_core_crosswalk_artifact_unavailable")
        return {"status": "fail", "errors": sorted(set(errors)), "source": source}
    raw_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if raw_sha != ref.get("artifact_payload_sha256"):
        errors.append("visible_life_core_crosswalk_artifact_sha256_mismatch")
    if isinstance(axis, dict) and isinstance(state, dict) and isinstance(closure, dict):
        expected = build_visible_life_core_authority_crosswalk_payload(
            product_axis_state=axis,
            product_core_state=state,
            product_core_closure=closure,
            input_artifacts=list(source.get("input_artifacts") or []),
            run_id=str(artifact.get("run_id") or ""),
        )
        if artifact != expected:
            errors.append("visible_life_core_crosswalk_callable_recompute_mismatch")
        errors.extend(
            validate_visible_life_core_crosswalk_entries(
                product_axis_state=axis,
                product_core_state=state,
                product_core_closure=closure,
                entries=list(artifact.get("entries") or []),
            )
        )
        if expected.get("omission_positive_control", {}).get("rejected") is not True:
            errors.append("visible_life_core_crosswalk_omission_positive_control_did_not_fire")
    return {
        "status": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "source": source,
        "artifact_payload_sha256": raw_sha,
        "total_leaf_count": artifact.get("total_leaf_count"),
        "producer_function": artifact.get("producer_function"),
        "run_id": artifact.get("run_id"),
        "aggregation_rule": artifact.get("aggregation_rule"),
        "producer_code_path_hash": artifact.get("producer_code_path_hash"),
    }


def validate_lineage_records(expected_records: list[dict[str, Any]], candidate_records: list[dict[str, Any]]) -> list[str]:
    expected = {str(row.get("lineage_id") or ""): row for row in expected_records}
    candidate = {str(row.get("lineage_id") or ""): row for row in candidate_records}
    errors: list[str] = []
    if len(candidate) != len(candidate_records):
        errors.append("lineage_universe_duplicate_id")
    if set(expected) - set(candidate):
        errors.append("lineage_universe_omission")
    if set(candidate) - set(expected):
        errors.append("lineage_universe_extra_id")
    if any(candidate.get(key) != value for key, value in expected.items() if key in candidate):
        errors.append("lineage_universe_record_drift")
    return sorted(set(errors))


def discover_card2_lineage_universe(*, run_id: str) -> dict[str, Any]:
    rules = [
        ("old_route_8692", ["docs/codex/tasks/ego-canonical-mechanism-integration-001a/STAGE_CARD.md"]),
        ("egodesktop_virtualcat_m1_m3", ["docs/EGO_CANONICAL_MECHANISM_INTEGRATION_ROUTE_001A.md"]),
        ("pet_world_v0_p0", ["artifacts/egodesktop_pet_world_integration_001a/p0/audit_claude_full_hostile_001.json"]),
        ("pilot_1_initial", ["artifacts/ego-pet-capability-conformance-001a/result.json"]),
        ("pilot_1_repair", ["artifacts/ego-pet-capability-conformance-001a/repair_001/result.json"]),
        ("pilot_3", ["artifacts/ego-pet-capability-conformance-001a/pe_forage_003/result.json"]),
        ("learned_outcome_cards", ["docs/codex/tasks/ego-learned-outcome-kernel-capability-001a/P1R0_DESIGN_INVALID_AUDIT_RESULT.json"]),
        ("outcome_utility_closure", ["docs/codex/tasks/ego-engineering-only-outcome-utility-route-replacement-001a/TASK-CARD-EGO-OUTCOME-UTILITY-ADAPTER-CLOSURE-001A.md"]),
    ]
    records: list[dict[str, Any]] = []
    for lineage_id, paths in rules:
        evidence = []
        for relative in paths:
            path = ROOT / relative
            evidence.append(
                {
                    "repo": "Ego",
                    "path": relative,
                    "exists": path.is_file(),
                    "payload_sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None,
                }
            )
        records.append({"lineage_id": lineage_id, "discovery_evidence": evidence})
    old_k0_path = "artifacts/ROUTE-STATE-MACHINE-001A/routes/K0-DUAL-TRACK-SUPERSESSION-001A/closure.json"
    old_k0_probe = _git_repo(ITL_ROOT, ["rev-parse", f"cb6cd57b8405bbac378f2857766ddaf63e08e194:{old_k0_path}"])
    records.append(
        {
            "lineage_id": "old_k0_science_route",
            "discovery_evidence": [
                {
                    "repo": "intelligence-theory-lab",
                    "commit": "cb6cd57b8405bbac378f2857766ddaf63e08e194",
                    "path": old_k0_path,
                    "exists": old_k0_probe.returncode == 0,
                    "git_blob_oid": old_k0_probe.stdout.strip() if old_k0_probe.returncode == 0 else None,
                }
            ],
        }
    )
    records.sort(key=lambda item: str(item["lineage_id"]))
    discovered_ids = [str(record["lineage_id"]) for record in records]
    omitted_id = discovered_ids[0]
    omission_errors = validate_lineage_records(records, records[1:])
    return {
        "schema_version": "ego.card2_lineage_universe.v1",
        "task_id": CARD2_SYNC_TASK_ID,
        "run_id": run_id,
        "producer_function": "scripts.codex_session_guard.discover_card2_lineage_universe",
        "producer_code_path_hash": _script_code_path_hash(),
        "input_artifacts": [evidence for record in records for evidence in record["discovery_evidence"]],
        "aggregation_rule": "fixed callable discovery rules over committed or current immutable lineage marker paths; sorted unique lineage_id universe",
        "discovered_count": len(records),
        "records": records,
        "universe_sha256": hashlib.sha256(_canonical_json_bytes(discovered_ids)).hexdigest(),
        "omission_positive_control": {
            "omitted_lineage_id": omitted_id,
            "expected_count": len(records),
            "mutated_count": len(records) - 1,
            "rejected": "lineage_universe_omission" in omission_errors,
            "rejection_code": "lineage_universe_omission",
            "observed_error_codes": omission_errors,
        },
        "claim_ceiling": "callable lineage-universe completeness control only",
    }


def _read_json_file(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, str(exc)
    return (payload, None) if isinstance(payload, dict) else (None, "JSON root must be an object")


def validate_field_crosswalk(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    source = read_itl_authority_objects(program_state)
    errors = list(source.get("errors") or [])
    payloads = source.get("payloads") or {}
    route_state = payloads.get("route_state")
    phase_b_receipt = payloads.get("phase_b_review_receipt")
    transcribed = route_guard.get("transcribed_itl") or {}
    if not isinstance(route_state, dict) or transcribed.get("route_state") != route_state:
        errors.append("route_state_transcription_mismatch")
    if not isinstance(phase_b_receipt, dict) or transcribed.get("phase_b_review_receipt") != phase_b_receipt:
        errors.append("phase_b_review_receipt_transcription_mismatch")
    crosswalk_ref = route_guard.get("field_crosswalk") or {}
    relative = str(crosswalk_ref.get("path") or "")
    artifact_path = ROOT / relative
    artifact, artifact_error = _read_json_file(artifact_path)
    if artifact_error or artifact is None:
        errors.append("field_crosswalk_artifact_unavailable")
        return {"status": "fail", "errors": errors, "source": source}
    raw_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if raw_sha != crosswalk_ref.get("artifact_payload_sha256"):
        errors.append("field_crosswalk_artifact_sha256_mismatch")
    if isinstance(route_state, dict) and isinstance(phase_b_receipt, dict):
        expected = build_field_crosswalk_payload(
            route_state=route_state,
            phase_b_review_receipt=phase_b_receipt,
            input_artifacts=list(source.get("input_artifacts") or []),
            run_id=str(artifact.get("run_id") or ""),
        )
        if artifact != expected:
            errors.append("field_crosswalk_callable_recompute_mismatch")
        entry_errors = validate_crosswalk_entries(
            route_state=route_state,
            phase_b_review_receipt=phase_b_receipt,
            entries=list(artifact.get("entries") or []),
        )
        errors.extend(entry_errors)
        if expected.get("omission_positive_control", {}).get("rejected") is not True:
            errors.append("field_crosswalk_omission_positive_control_did_not_fire")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "source": source,
        "artifact_payload_sha256": raw_sha,
        "total_leaf_count": artifact.get("total_leaf_count"),
        "producer_function": artifact.get("producer_function"),
        "run_id": artifact.get("run_id"),
        "aggregation_rule": artifact.get("aggregation_rule"),
        "producer_code_path_hash": artifact.get("producer_code_path_hash"),
    }


def validate_lineage_universe(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    ref = route_guard.get("lineage_universe") or {}
    relative = str(ref.get("path") or "")
    artifact_path = ROOT / relative
    artifact, artifact_error = _read_json_file(artifact_path)
    errors: list[str] = []
    if artifact_error or artifact is None:
        return {"status": "fail", "errors": ["lineage_universe_artifact_unavailable"]}
    raw_sha = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if raw_sha != ref.get("artifact_payload_sha256"):
        errors.append("lineage_universe_artifact_sha256_mismatch")
    expected = discover_card2_lineage_universe(run_id=str(artifact.get("run_id") or ""))
    if artifact != expected:
        errors.append("lineage_universe_callable_recompute_mismatch")
    errors.extend(validate_lineage_records(expected["records"], list(artifact.get("records") or [])))
    if any(not all(bool(evidence.get("exists")) for evidence in record.get("discovery_evidence") or []) for record in expected["records"]):
        errors.append("lineage_universe_source_missing")
    discovered_ids = [record["lineage_id"] for record in expected["records"]]
    if expected.get("omission_positive_control", {}).get("rejected") is not True:
        errors.append("lineage_omission_positive_control_did_not_fire")
    if ref.get("discovered_count") != len(discovered_ids) or ref.get("universe_sha256") != expected.get("universe_sha256"):
        errors.append("lineage_universe_program_ref_mismatch")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "artifact_payload_sha256": raw_sha,
        "discovered_count": len(discovered_ids),
        "universe_sha256": expected.get("universe_sha256"),
        "omission_positive_control": expected.get("omission_positive_control"),
        "producer_function": expected.get("producer_function"),
        "run_id": expected.get("run_id"),
        "aggregation_rule": expected.get("aggregation_rule"),
        "producer_code_path_hash": expected.get("producer_code_path_hash"),
    }


def validate_card2_action_paths(
    *,
    route_state: dict[str, Any],
    changed_paths: list[str],
    scope_loaded: bool,
    scope_allowed_paths: list[str],
) -> dict[str, Any]:
    policy = route_state.get("action_path_policy") or {}
    errors: list[str] = []
    if not scope_loaded:
        errors.append("missing_mutation_scope_for_card2_action")
    if policy.get("action_id") != CARD2_BANK_ACTION_ID:
        errors.append("card2_action_path_policy_identity_mismatch")
    allowed_exact = [str(item) for item in policy.get("allowed_exact_paths") or []]
    allowed_prefixes = [str(item) for item in policy.get("allowed_path_prefixes") or []]
    forbidden_prefixes = [str(item) for item in policy.get("forbidden_path_prefixes") or []]
    if allowed_exact != [] or allowed_prefixes != [CARD2_TASK_PREFIX]:
        errors.append("card2_action_path_policy_allowlist_mismatch")
    required_forbidden = {"EgoOperator/", "EgoDesktop/", "packages/", "src/", "scripts/", "tests/", "artifacts/"}
    if not required_forbidden.issubset(set(forbidden_prefixes)):
        errors.append("card2_action_path_policy_forbidden_prefix_missing")
    if policy.get("execution_inference") != "CHANGED_PATHS_NOT_DECLARED_BOOLEAN" or policy.get(
        "missing_mutation_scope"
    ) != "REJECT":
        errors.append("card2_action_path_policy_fail_closed_mismatch")
    inferred_execution_paths = [
        path
        for path in changed_paths
        if any(path.startswith(prefix) for prefix in forbidden_prefixes)
        or not (path in allowed_exact or any(path.startswith(prefix) for prefix in allowed_prefixes))
    ]
    if inferred_execution_paths:
        errors.append("card2_execution_inferred_from_changed_paths")
    invalid_scope_paths = [
        path
        for path in scope_allowed_paths
        if not (path in allowed_exact or any(path.startswith(prefix) for prefix in allowed_prefixes))
    ]
    if invalid_scope_paths:
        errors.append("card2_scope_expands_action_path_policy")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "inferred_execution_paths": inferred_execution_paths,
        "producer_function": "scripts.codex_session_guard.validate_card2_action_paths",
        "aggregation_rule": "reject missing scope and any actual or declared allowed path outside the committed ITL action-specific policy",
        "producer_code_path_hash": _script_code_path_hash(),
    }


def validate_visible_life_action_paths(
    *,
    changed_paths: list[str],
    scope_allowed_paths: list[str],
    require_complete_set: bool,
) -> dict[str, Any]:
    expected = list(VISIBLE_LIFE_TARGETS)
    changed = sorted(set(str(path) for path in changed_paths))
    declared = sorted(set(str(path) for path in scope_allowed_paths))
    errors: list[str] = []
    if declared != sorted(expected):
        errors.append("visible_life_scope_exact_six_mismatch")
    outside = sorted(path for path in changed if path not in expected)
    if outside:
        errors.append("visible_life_changed_path_outside_exact_six")
    if require_complete_set and changed != sorted(expected):
        errors.append("visible_life_changed_path_set_incomplete")
    if any(
        path.startswith(prefix)
        for path in changed + declared
        for prefix in VISIBLE_LIFE_FORBIDDEN_PREFIXES
    ):
        errors.append("visible_life_forbidden_surface_path")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "expected_paths": expected,
        "changed_paths": changed,
        "declared_paths": declared,
        "producer_function": "scripts.codex_session_guard.validate_visible_life_action_paths",
        "aggregation_rule": "require the exact six frozen implementation paths and reject every other path or prefix",
        "producer_code_path_hash": _script_code_path_hash(),
    }


def validate_visible_life_product_authority(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    product = route_guard.get("product_authority") or {}
    errors: list[str] = []
    if product.get("authority_axis") != "EGO_PRODUCT_CAPABILITY_ONLY":
        errors.append("visible_life_product_authority_axis_mismatch")
    if product.get("task_id") != VISIBLE_LIFE_TASK_ID:
        errors.append("visible_life_product_task_id_mismatch")
    if product.get("action_id") != VISIBLE_LIFE_IMPLEMENT_ACTION_ID:
        errors.append("visible_life_product_action_id_mismatch")
    if product.get("state") != "AUTHORIZED_NOT_STARTED":
        errors.append("visible_life_product_state_mismatch")
    if product.get("allowed_next_actions") != [
        VISIBLE_LIFE_IMPLEMENT_ACTION_ID,
        "run_route_state_machine_validation",
    ]:
        errors.append("visible_life_product_allowed_actions_mismatch")
    if product.get("forbidden_next_actions") != VISIBLE_LIFE_FORBIDDEN_ACTIONS:
        errors.append("visible_life_product_forbidden_actions_mismatch")
    authorizations = product.get("authorizations") or {}
    expected_authorizations = {
        "implementation": True,
        "local_manual_validation": True,
        "experiment_execution": False,
        "mainline": False,
        "mechanism_evidence": False,
        "remote_anchor": False,
        "runtime": False,
        "science_successor": False,
        "scoring": False,
    }
    if authorizations != expected_authorizations:
        errors.append("visible_life_product_authorizations_mismatch")
    if product.get("authorized_implementation_targets") != VISIBLE_LIFE_TARGETS:
        errors.append("visible_life_product_targets_mismatch")
    for key, expected in {
        "enabled": False,
        "default_enabled": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "science_weight": 0,
        "real_trigger_evidence": "absent_pre_phase_b",
    }.items():
        if product.get(key) != expected:
            errors.append(f"visible_life_product_{key}_mismatch")
    policy = product.get("action_path_policy") or {}
    if policy.get("allowed_exact_paths") != VISIBLE_LIFE_TARGETS or policy.get("allowed_path_prefixes") != []:
        errors.append("visible_life_product_path_policy_mismatch")
    if policy.get("missing_mutation_scope") != "REJECT" or policy.get("self_declared_scope_expansion") is not False:
        errors.append("visible_life_product_path_policy_fail_closed_mismatch")
    required_forbidden = {
        "EgoDesktop/",
        "EgoOperator/",
        "packages/",
        "providers/",
        "deployment/",
        "network/",
        "LLM/",
    }
    if set(policy.get("forbidden_path_prefixes") or []) != required_forbidden:
        errors.append("visible_life_product_forbidden_prefixes_mismatch")
    firewall = product.get("science_firewall") or {}
    if firewall != {
        "science_weight": 0,
        "may_supply_mechanism_attribution": False,
        "may_satisfy_science_successor_boundary": False,
        "inherits_old_k0": False,
        "may_reopen_old_k0": False,
    }:
        errors.append("visible_life_product_science_firewall_mismatch")
    phase_b = product.get("phase_b_contract") or {}
    if phase_b.get("mutation_scope_path") != VISIBLE_LIFE_PHASE_B_SCOPE_PATH:
        errors.append("visible_life_phase_b_scope_ref_mismatch")
    if phase_b.get("exact_changed_paths") != VISIBLE_LIFE_TARGETS:
        errors.append("visible_life_phase_b_exact_paths_mismatch")
    try:
        phase_b_scope = _load_yaml(ROOT / VISIBLE_LIFE_PHASE_B_SCOPE_PATH, code="missing_visible_life_phase_b_scope")
    except GuardError:
        phase_b_scope = {}
        errors.append("visible_life_phase_b_scope_unavailable")
    if phase_b_scope:
        expected_scope = {
            "task_id": VISIBLE_LIFE_TASK_ID,
            "task_kind": "local_product_clock_visible_playground",
            "requested_action_id": VISIBLE_LIFE_IMPLEMENT_ACTION_ID,
            "source_route_revision_id": VISIBLE_LIFE_ROUTE_REVISION,
            "source_route_fingerprint": compute_route_fingerprint(program_state),
            "expected_target_route_revision_id": VISIBLE_LIFE_ROUTE_REVISION,
            "independent_red_review_required": False,
            "red_review_ref": None,
            "allowed_mutation_paths": VISIBLE_LIFE_TARGETS,
            "execution_requested": True,
            "mainline_connected": False,
            "runtime_authority": "none",
            "science_weight": 0,
            "auto_remote_anchor": "forbidden",
            "push": "forbidden",
            "tag": "forbidden",
        }
        if phase_b_scope != expected_scope:
            errors.append("visible_life_phase_b_scope_contract_mismatch")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "producer_function": "scripts.codex_session_guard.validate_visible_life_product_authority",
        "aggregation_rule": "require one Ego-owned product-only action with exact six targets and all runtime/mainline/science authorities false",
        "producer_code_path_hash": _script_code_path_hash(),
    }


def _visible_life_core_report_critical_fields(report: dict[str, Any]) -> dict[str, Any]:
    provenance = report.get("provenance") or {}
    return {
        "schema_version": report.get("schema_version"),
        "task_id": report.get("task_id"),
        "baseline_id": report.get("baseline_id"),
        "computed_verdict": report.get("computed_verdict"),
        "baseline_commit": report.get("baseline_commit"),
        "baseline_parent": report.get("baseline_parent"),
        "baseline_tree": report.get("baseline_tree"),
        "exact_change_set_verified": report.get("exact_change_set_verified"),
        "head_descends_from_baseline": report.get("head_descends_from_baseline"),
        "manifest_sha256": provenance.get("manifest_sha256"),
        "producer_code_path_hash": provenance.get("producer_code_path_hash"),
        "trace_payload_sha256": report.get("trace_payload_sha256"),
        "trace_validation_status": report.get("trace_validation_status"),
        "trace_replay_status": report.get("trace_replay_status"),
        "trace_replay_input": report.get("trace_replay_input"),
        "database_path": report.get("database_path"),
        "database_payload_sha256": report.get("database_payload_sha256"),
        "database_provenance_status": report.get("database_provenance_status"),
        "sqlite_recovery_status": report.get("sqlite_recovery_status"),
        "sqlite_export_status": report.get("sqlite_export_status"),
        "serialized_initial_state_status": report.get("serialized_initial_state_status"),
        "direct_engine_replay_status": report.get("direct_engine_replay_status"),
        "errors": report.get("errors"),
        "claim_ceiling": report.get("claim_ceiling"),
    }


def validate_visible_life_core_evidence(
    program_state: dict[str, Any],
    *,
    runner: GuardRunner | None = None,
) -> dict[str, Any]:
    """Recompute the frozen V0 evidence through the standalone validator."""

    cache_allowed = runner is None
    runner = runner or GuardRunner()
    product = ((program_state.get("route_guard") or {}).get("product_authority") or {})
    baseline = product.get("historical_baseline") or {}
    errors: list[str] = []
    paths = {
        key: ROOT / str(baseline.get(key) or "")
        for key in VISIBLE_LIFE_CORE_BASELINE_REFS
    }
    for name, expected_relative in VISIBLE_LIFE_CORE_BASELINE_REFS.items():
        if baseline.get(name) != expected_relative:
            errors.append(f"core_evidence_{name}_ref_mismatch")
        if not paths[name].is_file():
            errors.append(f"core_evidence_{name}_unavailable")
    if errors:
        return {
            "status": "fail",
            "errors": sorted(set(errors)),
            "producer_function": "scripts.codex_session_guard.validate_visible_life_core_evidence",
            "run_id": "live_repo_recompute",
            "aggregation_rule": "fail closed before execution if any frozen evidence or validator path is absent or misbound",
            "producer_code_path_hash": _script_code_path_hash(),
        }

    file_hashes = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }
    cache_key: tuple[Any, ...] | None = None
    if cache_allowed:
        head_probe = _git_repo(ROOT, ["rev-parse", "HEAD"])
        head_oid = head_probe.stdout.strip() if head_probe.returncode == 0 else "HEAD_UNAVAILABLE"
        cache_key = (
            head_oid,
            *(item for key in sorted(paths) for item in (key, str(baseline.get(key) or ""), file_hashes[key])),
        )
        cached = _VISIBLE_LIFE_CORE_EVIDENCE_CACHE.get(cache_key)
        if cached is not None:
            return json.loads(json.dumps(cached))
    stored_report, stored_error = _read_json_file(paths["validation_report_path"])
    if stored_error or not isinstance(stored_report, dict):
        errors.append("core_evidence_stored_report_invalid")
        stored_report = {}
    if stored_report:
        stored_critical = _visible_life_core_report_critical_fields(stored_report)
        if stored_critical.get("manifest_sha256") != file_hashes["manifest_path"]:
            errors.append("core_evidence_stored_manifest_sha256_mismatch")
        if stored_critical.get("trace_payload_sha256") != file_hashes["trace_path"]:
            errors.append("core_evidence_stored_trace_sha256_mismatch")
        if stored_critical.get("database_payload_sha256") != file_hashes["database_path"]:
            errors.append("core_evidence_stored_database_sha256_mismatch")
        if stored_critical.get("producer_code_path_hash") != file_hashes["validator_path"]:
            errors.append("core_evidence_stored_validator_sha256_mismatch")

    computed_report: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="ego_life_core_route_gate_") as directory:
        output_path = Path(directory) / "computed_report.json"
        result = runner.run(
            [
                sys.executable,
                str(paths["validator_path"]),
                "--repo-root",
                str(ROOT),
                "--manifest",
                str(paths["manifest_path"]),
                "--trace",
                str(paths["trace_path"]),
                "--database",
                str(paths["database_path"]),
                "--output",
                str(output_path),
            ]
        )
        if result.returncode != 0:
            errors.append("core_evidence_validator_nonzero_exit")
        computed_report_candidate, computed_error = _read_json_file(output_path)
        if computed_error or not isinstance(computed_report_candidate, dict):
            errors.append("core_evidence_computed_report_invalid")
        else:
            computed_report = computed_report_candidate

    computed_critical = _visible_life_core_report_critical_fields(computed_report)
    expected_statuses = {
        "schema_version": "ego.life_core_v0_baseline_validation.v1",
        "task_id": VISIBLE_LIFE_CORE_TASK_ID,
        "baseline_id": "EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A",
        "computed_verdict": "PASS",
        "baseline_commit": VISIBLE_LIFE_CORE_BASELINE_COMMIT,
        "baseline_parent": VISIBLE_LIFE_CORE_BASELINE_PARENT,
        "baseline_tree": VISIBLE_LIFE_CORE_BASELINE_TREE,
        "exact_change_set_verified": True,
        "head_descends_from_baseline": True,
        "trace_validation_status": "PASS",
        "trace_replay_status": "PASS",
        "trace_replay_input": "serialized_initial_state_and_typed_commands_from_sqlite_artifact",
        "database_path": str(paths["database_path"].resolve()),
        "database_provenance_status": "PASS",
        "sqlite_recovery_status": "PASS",
        "sqlite_export_status": "PASS",
        "serialized_initial_state_status": "PASS",
        "direct_engine_replay_status": "PASS",
        "errors": [],
    }
    for key, expected in expected_statuses.items():
        if computed_critical.get(key) != expected:
            errors.append(f"core_evidence_computed_{key}_mismatch")
    if computed_critical.get("manifest_sha256") != file_hashes["manifest_path"]:
        errors.append("core_evidence_computed_manifest_sha256_mismatch")
    if computed_critical.get("trace_payload_sha256") != file_hashes["trace_path"]:
        errors.append("core_evidence_computed_trace_sha256_mismatch")
    if computed_critical.get("database_payload_sha256") != file_hashes["database_path"]:
        errors.append("core_evidence_computed_database_sha256_mismatch")
    if computed_critical.get("producer_code_path_hash") != file_hashes["validator_path"]:
        errors.append("core_evidence_computed_validator_sha256_mismatch")
    if stored_report and _visible_life_core_report_critical_fields(stored_report) != computed_critical:
        errors.append("core_evidence_stored_computed_critical_mismatch")
    response = {
        "status": "pass" if not errors else "fail",
        "errors": sorted(set(errors)),
        "producer_function": "scripts.codex_session_guard.validate_visible_life_core_evidence",
        "run_id": "live_repo_recompute",
        "input_artifacts": [str(baseline.get(key) or "") for key in sorted(paths)],
        "aggregation_rule": (
            "PASS iff the fresh standalone validator exits zero; stored and computed critical reports match; Git pins, "
            "manifest/trace/database/validator hashes match; and trace, serialized-state, SQLite recovery/export, and replay statuses pass"
        ),
        "producer_code_path_hash": _script_code_path_hash(),
        "artifact_hashes": file_hashes,
        "computed_critical": computed_critical,
    }
    if cache_allowed and cache_key is not None:
        _VISIBLE_LIFE_CORE_EVIDENCE_CACHE[cache_key] = json.loads(json.dumps(response))
    return response


def validate_visible_life_core_product_authority(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    product = route_guard.get("product_authority") or {}
    errors: list[str] = []
    authority = route_guard.get("authority_source") or {}
    if authority.get("pinned_commit") != VISIBLE_LIFE_CORE_ITL_COMMIT:
        errors.append("visible_life_core_itl_commit_mismatch")
    authority_objects = authority.get("objects") or {}
    for name, expected_pin in VISIBLE_LIFE_CORE_ITL_OBJECTS.items():
        if authority_objects.get(name) != expected_pin:
            errors.append(f"visible_life_core_itl_pin_mismatch:{name}")

    source = read_itl_authority_objects(program_state)
    if source.get("status") != "pass":
        errors.extend(f"visible_life_core_source:{item}" for item in source.get("errors") or [])
    payloads = source.get("payloads") or {}
    axis = payloads.get("product_axis_state") or {}
    source_state = payloads.get("product_core_state") or {}
    source_closure = payloads.get("product_core_closure") or {}
    source_report = payloads.get("product_core_validation_report") or {}
    source_receipt = payloads.get("product_core_red_receipt") or {}
    source_event_text = payloads.get("product_core_events") or ""
    source_event_rows: list[dict[str, Any]] = []
    if isinstance(source_event_text, str):
        try:
            source_event_rows = [json.loads(line) for line in source_event_text.splitlines() if line.strip()]
        except json.JSONDecodeError:
            errors.append("visible_life_core_event_jsonl_invalid")
    if len(source_event_rows) != 1:
        errors.append("visible_life_core_event_count_mismatch")
    else:
        source_event = source_event_rows[0]
        expected_event = {
            "axis": "PRODUCT_DEVELOPMENT",
            "closure_type": "ARTIFACT_ONLY",
            "current_state": "ADJUDICATED",
            "default_enabled": False,
            "event": "visible_life_proxy_v0_product_core_adoption_recorded",
            "event_id": f"{VISIBLE_LIFE_CORE_ITL_ROUTE_ID}:ADJUDICATED:001",
            "phase": "V0_PRODUCT_CORE_AUTHORITY_RECORDED_EGO_SYNC_PENDING",
            "product_development_core_lineage": "SOLE",
            "route_id": VISIBLE_LIFE_CORE_ITL_ROUTE_ID,
            "runtime_authority": "none",
            "runtime_mainline_connected": False,
            "science_weight": 0,
            "source_commit": VISIBLE_LIFE_CORE_BASELINE_COMMIT,
            "task_id": "ITL-EGO-VISIBLE-LIFE-PROXY-V0-PRODUCT-CORE-ADOPTION-TRANSITION-001A",
        }
        if any(source_event.get(key) != value for key, value in expected_event.items()):
            errors.append("visible_life_core_event_semantics_mismatch")
    if (
        source_report.get("verdict") != "semantic_precheck_pass"
        or source_report.get("validation_errors") != []
        or source_report.get("real_trigger_evidence") != "UNVERIFIED_IN_THIS_ITL_TRANSITION"
    ):
        errors.append("visible_life_core_source_report_semantics_mismatch")
    if source_receipt.get("verdict") != "NO_BLOCKING_FINDINGS" or source_receipt.get("blocking_findings") != []:
        errors.append("visible_life_core_source_red_receipt_semantics_mismatch")
    if source_receipt.get("claim_ceiling_acknowledged") is not True:
        errors.append("visible_life_core_source_red_receipt_claim_ceiling_missing")
    axis_data = axis.get("product_development_axis") or {}
    if (
        axis.get("authority_semantics") != "SOLE_MACHINE_READABLE_PRODUCT_DEVELOPMENT_AXIS_AUTHORITY"
        or axis_data.get("authority") != "SOLE"
        or axis_data.get("authority_route_id") != VISIBLE_LIFE_CORE_ITL_ROUTE_ID
        or axis_data.get("core_id") != "ego_life_playground_v0"
        or axis_data.get("source_commit") != VISIBLE_LIFE_CORE_BASELINE_COMMIT
        or axis_data.get("state") != "AUTHORITY_RECORDED_EGO_SYNC_PENDING"
        or axis_data.get("currently_executable_actions")
        != [VISIBLE_LIFE_CORE_SYNC_ACTION_ID, "run_route_state_machine_validation"]
    ):
        errors.append("visible_life_core_product_axis_semantics_mismatch")
    if (
        source_state.get("route_id") != VISIBLE_LIFE_CORE_ITL_ROUTE_ID
        or source_state.get("current_state") != "ADJUDICATED"
        or source_state.get("phase") != "V0_PRODUCT_CORE_AUTHORITY_RECORDED_EGO_SYNC_PENDING"
        or (source_state.get("authorizations") or {}).get("v1_card_draft") is not False
        or (source_state.get("authorizations") or {}).get("v1_implementation") is not False
        or source_state.get("currently_executable_actions")
        != [VISIBLE_LIFE_CORE_SYNC_ACTION_ID, "run_route_state_machine_validation"]
        or ((source_state.get("conditional_actions") or {}).get(VISIBLE_LIFE_CORE_DRAFT_V1_ACTION_ID) or {}).get(
            "state"
        )
        != "BLOCKED_UNTIL_EGO_SYNC_VALIDATED"
    ):
        errors.append("visible_life_core_source_state_semantics_mismatch")
    source_evidence = source_closure.get("evidence_status") or {}
    source_runtime = source_closure.get("runtime_boundary") or {}
    source_science = source_closure.get("science_firewall") or {}
    if (
        source_closure.get("route_id") != VISIBLE_LIFE_CORE_ITL_ROUTE_ID
        or source_evidence.get("real_trigger_evidence") != "UNVERIFIED_IN_THIS_ITL_TRANSITION"
        or source_runtime
        != {
            "default_enabled": False,
            "ego_operator_active_default_unchanged": True,
            "runtime_authority": "none",
            "runtime_mainline_connected": False,
        }
        or source_science
        != {
            "inherits_old_k0": False,
            "may_satisfy_science_successor": False,
            "mechanism_attribution": False,
            "product_trace_is_science_evidence": False,
            "reopens_card2": False,
            "science_weight": 0,
        }
    ):
        errors.append("visible_life_core_source_closure_semantics_mismatch")

    crosswalk = validate_visible_life_core_authority_crosswalk(program_state)
    if crosswalk.get("status") != "pass":
        errors.extend(f"visible_life_core_crosswalk:{item}" for item in crosswalk.get("errors") or [])
    expected_authorizations = {
        "task_card_drafting": True,
        "local_manual_validation": True,
        "implementation": False,
        "experiment_execution": False,
        "mainline_runtime": False,
        "mechanism_evidence": False,
        "remote_anchor": False,
        "runtime": False,
        "science_successor": False,
        "scoring": False,
    }
    if product.get("authority_axis") != "EGO_PRODUCT_CAPABILITY_ONLY":
        errors.append("visible_life_core_authority_axis_mismatch")
    if product.get("task_id") != VISIBLE_LIFE_CORE_TASK_ID:
        errors.append("visible_life_core_task_id_mismatch")
    if product.get("predecessor_task_id") != VISIBLE_LIFE_TASK_ID:
        errors.append("visible_life_core_predecessor_task_mismatch")
    predecessor = product.get("predecessor_action") or {}
    if predecessor != {
        "action_id": VISIBLE_LIFE_IMPLEMENT_ACTION_ID,
        "state": "CONSUMED_IMPLEMENTED",
        "implementation_commit": VISIBLE_LIFE_CORE_BASELINE_COMMIT,
    }:
        errors.append("visible_life_core_predecessor_action_not_consumed")
    for key, expected in {
        "state": "ITL_PRODUCT_CORE_AUTHORITY_SYNCED",
        "product_development_core_lineage": "SOLE_VISIBLE_LIFE_PRODUCT_DEVELOPMENT_LINEAGE",
        "product_development_core": "ego_life_playground_v0",
        "sole_visible_life_product_core": True,
        "enabled": False,
        "default_enabled": False,
        "runtime_mainline_connected": False,
        "mainline_connected": False,
        "runtime_authority": "none",
        "science_weight": 0,
        "real_trigger_evidence": "UNVERIFIED_IN_THIS_ITL_TRANSITION",
        "ego_local_product_trigger_evidence": "BANKED_RECOMPUTING_PRODUCT_TRIGGER",
    }.items():
        if product.get(key) != expected:
            errors.append(f"visible_life_core_{key}_mismatch")
    if product.get("core_registry") != {"visible_life": "ego_life_playground_v0"}:
        errors.append("visible_life_core_registry_mismatch")
    if "product_development_mainline" in product:
        errors.append("visible_life_core_ambiguous_mainline_field_forbidden")
    if product.get("allowed_next_actions") != [
        VISIBLE_LIFE_CORE_DRAFT_V1_ACTION_ID,
        "run_route_state_machine_validation",
    ]:
        errors.append("visible_life_core_allowed_actions_mismatch")
    if product.get("forbidden_next_actions") != VISIBLE_LIFE_CORE_FORBIDDEN_ACTIONS:
        errors.append("visible_life_core_forbidden_actions_mismatch")
    if product.get("authorizations") != expected_authorizations:
        errors.append("visible_life_core_authorizations_mismatch")
    if product.get("authorized_implementation_targets") != []:
        errors.append("visible_life_core_targets_must_be_empty")
    if product.get("source_currently_executable_actions") != [
        VISIBLE_LIFE_CORE_SYNC_ACTION_ID,
        "run_route_state_machine_validation",
    ]:
        errors.append("visible_life_core_source_executable_actions_mismatch")
    if product.get("sync_action") != {
        "action_id": VISIBLE_LIFE_CORE_SYNC_ACTION_ID,
        "disposition": "CONSUMED_BY_EGO_AUTHORITY_SYNC",
        "source_route_id": VISIBLE_LIFE_CORE_ITL_ROUTE_ID,
        "source_commit": VISIBLE_LIFE_CORE_ITL_COMMIT,
    }:
        errors.append("visible_life_core_sync_action_mismatch")
    baseline = product.get("historical_baseline") or {}
    expected_baseline = {
        "source_commit": VISIBLE_LIFE_CORE_BASELINE_COMMIT,
        "source_parent": VISIBLE_LIFE_CORE_BASELINE_PARENT,
        "source_tree": VISIBLE_LIFE_CORE_BASELINE_TREE,
        "source_paths": VISIBLE_LIFE_TARGETS,
        "lineage_mode": "IMMUTABLE_HISTORICAL_BOUNDARY_WITH_DECLARED_DESCENDANT_EDITS",
        **VISIBLE_LIFE_CORE_BASELINE_REFS,
    }
    if baseline != expected_baseline:
        errors.append("visible_life_core_historical_baseline_mismatch")
    evidence = validate_visible_life_core_evidence(program_state)
    if evidence.get("status") != "pass":
        errors.extend(f"visible_life_core_evidence:{item}" for item in evidence.get("errors") or [])
    successor = product.get("successor_contract") or {}
    if successor != {
        "required_ancestor_commit": VISIBLE_LIFE_CORE_BASELINE_COMMIT,
        "allowed_draft_action": VISIBLE_LIFE_CORE_DRAFT_V1_ACTION_ID,
        "source_condition": "BLOCKED_UNTIL_EGO_SYNC_VALIDATED",
        "condition_resolution": "RESOLVED_BY_THIS_CALLABLE_EGO_SYNC_AFTER_COMMIT",
        "implementation_authorized": False,
        "second_core_requires_explicit_supersession": True,
    }:
        errors.append("visible_life_core_successor_contract_mismatch")
    firewall = product.get("science_firewall") or {}
    if firewall != {
        "science_weight": 0,
        "may_supply_mechanism_attribution": False,
        "may_satisfy_science_successor_boundary": False,
        "inherits_old_k0": False,
        "may_reopen_old_k0": False,
    }:
        errors.append("visible_life_core_science_firewall_mismatch")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "producer_function": "scripts.codex_session_guard.validate_visible_life_core_product_authority",
        "aggregation_rule": (
            "require exact committed ITL product-axis authority, exhaustive transcription, a consumed sync action, "
            "separate ITL/Ego trigger statuses, an immutable V0 boundary, draft-only conditional successor authority, "
            "and runtime/science permissions closed"
        ),
        "producer_code_path_hash": _script_code_path_hash(),
        "computed_evidence": evidence,
        "source": source,
        "crosswalk": crosswalk,
    }


def validate_red_review_record(receipt_path: str, *, require_committed: bool) -> dict[str, Any]:
    path = ROOT / receipt_path
    errors: list[str] = []
    commit: str | None = None
    if require_committed:
        log = _git_repo(ROOT, ["log", "--diff-filter=A", "--format=%H", "--", receipt_path])
        commits = [line for line in log.stdout.splitlines() if line]
        if not commits:
            return {"status": "fail", "errors": ["red_review_record_not_committed"]}
        commit = commits[-1]
        receipt_probe = _git_repo(ROOT, ["show", f"{commit}:{receipt_path}"], text=False)
        try:
            receipt = json.loads(receipt_probe.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"status": "fail", "errors": ["committed_red_review_record_invalid_json"]}
    else:
        receipt, receipt_error = _read_json_file(path)
        if receipt_error or receipt is None:
            return {"status": "fail", "errors": ["candidate_red_review_record_unavailable"]}
    manifest = receipt.get("reviewed_semantic_manifest") or {}
    manifest_sha = hashlib.sha256(_canonical_json_bytes(manifest)).hexdigest()
    if manifest_sha != receipt.get("reviewed_semantic_manifest_sha256"):
        errors.append("red_review_semantic_manifest_hash_mismatch")
    reviewed_paths = [str(item) for item in receipt.get("sorted_reviewed_paths") or []]
    if reviewed_paths != sorted(reviewed_paths) or reviewed_paths != manifest.get("sorted_reviewed_paths"):
        errors.append("red_review_path_set_mismatch")
    if receipt.get("verdict") != "NO_BLOCKING_FINDINGS" or receipt.get("blocking_findings") != []:
        errors.append("red_review_blocking_or_invalid_verdict")
    if receipt.get("reviewer") != "Claude" or not str(receipt.get("reviewer_session_id") or "").strip():
        errors.append("red_review_reviewer_identity_missing")
    if receipt.get("reviewer_session_id") == receipt.get("executor_session_id"):
        errors.append("red_review_role_separation_missing")
    base_commit = str(receipt.get("base_commit") or "")
    target_ref = commit if require_committed else None
    if require_committed and commit:
        parent = _git_repo(ROOT, ["rev-parse", f"{commit}^"])
        if parent.returncode != 0 or parent.stdout.strip() != base_commit:
            errors.append("committed_red_review_base_parent_mismatch")
        changed = _git_repo(ROOT, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit])
        expected_paths = set(reviewed_paths + [receipt_path])
        if set(changed.stdout.splitlines()) != expected_paths:
            errors.append("committed_red_review_exact_path_set_mismatch")
        diff_probe = _git_repo(
            ROOT,
            ["diff", "--binary", "--no-ext-diff", "--full-index", base_commit, commit, "--", *reviewed_paths],
            text=False,
        )
    else:
        diff_probe = _git_repo(
            ROOT,
            ["diff", "--cached", "--binary", "--no-ext-diff", "--full-index", "--", *reviewed_paths],
            text=False,
        )
    if diff_probe.returncode != 0 or hashlib.sha256(diff_probe.stdout).hexdigest() != receipt.get(
        "reviewed_diff_sha256"
    ):
        errors.append("red_review_diff_sha256_mismatch")
    for reviewed_path, row in (manifest.get("per_path_reviewed_blob_or_worktree_sha256") or {}).items():
        ref = f"{commit}:{reviewed_path}" if require_committed and commit else f":{reviewed_path}"
        oid = _git_repo(ROOT, ["rev-parse", ref])
        if oid.returncode != 0 or oid.stdout.strip() != row.get("reviewed_blob"):
            errors.append(f"red_review_blob_mismatch:{reviewed_path}")
            continue
        blob = _git_repo(ROOT, ["cat-file", "blob", oid.stdout.strip()], text=False)
        expected_blob_sha = row.get("reviewed_blob_payload_sha256") or row.get("worktree_sha256")
        if blob.returncode != 0 or hashlib.sha256(blob.stdout).hexdigest() != expected_blob_sha:
            errors.append(f"red_review_blob_payload_mismatch:{reviewed_path}")
    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "commit": commit,
        "base_commit": base_commit,
        "reviewed_diff_sha256": receipt.get("reviewed_diff_sha256"),
        "reviewed_semantic_manifest_sha256": receipt.get("reviewed_semantic_manifest_sha256"),
        "review_id": receipt.get("review_id"),
        "producer_function": "scripts.codex_session_guard.validate_red_review_record",
        "aggregation_rule": "require NO_BLOCKING_FINDINGS plus exact base, committed path set, reviewed diff SHA-256, and per-path committed blob binding",
        "producer_code_path_hash": _script_code_path_hash(),
    }


def compute_card2_sync_dependencies(program_state: dict[str, Any]) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    route_state = ((route_guard.get("transcribed_itl") or {}).get("route_state") or {})
    crosswalk = validate_field_crosswalk(program_state)
    lineage = validate_lineage_universe(program_state)
    action_allowed = validate_card2_action_paths(
        route_state=route_state,
        changed_paths=[f"{CARD2_TASK_PREFIX}STAGE_CARD.md"],
        scope_loaded=True,
        scope_allowed_paths=[CARD2_TASK_PREFIX],
    )
    action_forbidden = validate_card2_action_paths(
        route_state=route_state,
        changed_paths=["EgoOperator/agent_base.py"],
        scope_loaded=True,
        scope_allowed_paths=[CARD2_TASK_PREFIX],
    )
    action_missing_scope = validate_card2_action_paths(
        route_state=route_state,
        changed_paths=[f"{CARD2_TASK_PREFIX}STAGE_CARD.md"],
        scope_loaded=False,
        scope_allowed_paths=[],
    )
    action_policy_pass = (
        action_allowed.get("status") == "pass"
        and "card2_execution_inferred_from_changed_paths" in (action_forbidden.get("errors") or [])
        and "missing_mutation_scope_for_card2_action" in (action_missing_scope.get("errors") or [])
    )
    red_ref = ((route_guard.get("red_review") or {}).get("phase_b") or {}).get("path")
    red_review = validate_red_review_record(str(red_ref or ""), require_committed=True)
    statuses = {
        "EGO_FIELD_BY_FIELD_AUTHORITY_SYNC_BANKED": crosswalk.get("status") == "pass",
        "ACTION_SPECIFIC_PATH_POLICY_ENFORCED": action_policy_pass,
        "LINEAGE_OMISSION_POSITIVE_CONTROL_ENFORCED": lineage.get("status") == "pass",
        "COMMITTED_RED_REVIEW_RECORD_BOUND_TO_DIFF": red_review.get("status") == "pass",
    }
    return {
        "producer_function": "scripts.codex_session_guard.compute_card2_sync_dependencies",
        "run_id": "live_repo_recompute",
        "input_artifacts": [
            str((route_guard.get("field_crosswalk") or {}).get("path") or ""),
            str((route_guard.get("lineage_universe") or {}).get("path") or ""),
            str(red_ref or ""),
        ],
        "aggregation_rule": "all four committed ITL consumption dependencies must recompute true",
        "producer_code_path_hash": _script_code_path_hash(),
        "dependencies": statuses,
        "all_satisfied": all(statuses.values()),
        "crosswalk": crosswalk,
        "action_path_policy": {
            "status": "pass" if action_policy_pass else "fail",
            "allowed_control": action_allowed,
            "forbidden_path_positive_control": action_forbidden,
            "missing_scope_positive_control": action_missing_scope,
        },
        "lineage_universe": lineage,
        "committed_red_review": red_review,
    }


def compute_visible_life_phase_b_dependencies(
    program_state: dict[str, Any],
    *,
    require_committed_review: bool,
) -> dict[str, Any]:
    route_guard = program_state.get("route_guard") or {}
    source = read_itl_authority_objects(program_state)
    crosswalk = validate_visible_life_closure_crosswalk(program_state)
    product = validate_visible_life_product_authority(program_state)
    red_ref = str(((route_guard.get("red_review") or {}).get("phase_a") or {}).get("path") or "")
    review = validate_red_review_record(red_ref, require_committed=require_committed_review)
    exact_scope = validate_visible_life_action_paths(
        changed_paths=VISIBLE_LIFE_TARGETS,
        scope_allowed_paths=VISIBLE_LIFE_TARGETS,
        require_complete_set=True,
    )
    extra_path_control = validate_visible_life_action_paths(
        changed_paths=[*VISIBLE_LIFE_TARGETS, "EgoDesktop/forbidden.py"],
        scope_allowed_paths=VISIBLE_LIFE_TARGETS,
        require_complete_set=True,
    )
    statuses = {
        "COMMITTED_ITL_CLOSURE_PIN_VALID": source.get("status") == "pass",
        "EXHAUSTIVE_ITL_CLOSURE_CROSSWALK_VALID": crosswalk.get("status") == "pass",
        "EGO_PRODUCT_AUTHORITY_EXACT": product.get("status") == "pass",
        "EGO_PHASE_A_RED_REVIEW_BOUND": review.get("status") == "pass",
        "EXACT_SIX_PATH_POLICY_ENFORCED": (
            exact_scope.get("status") == "pass"
            and "visible_life_changed_path_outside_exact_six" in (extra_path_control.get("errors") or [])
        ),
    }
    return {
        "producer_function": "scripts.codex_session_guard.compute_visible_life_phase_b_dependencies",
        "run_id": "live_repo_recompute",
        "input_artifacts": [VISIBLE_LIFE_CROSSWALK_PATH, red_ref, VISIBLE_LIFE_PHASE_B_SCOPE_PATH],
        "aggregation_rule": "all committed closure, exhaustive transcription, product authority, Red review, and exact-path gates must pass",
        "producer_code_path_hash": _script_code_path_hash(),
        "dependencies": statuses,
        "all_satisfied": all(statuses.values()),
        "source": source,
        "crosswalk": crosswalk,
        "product_authority": product,
        "red_review": review,
        "exact_path_policy": {
            "control": exact_scope,
            "forbidden_positive_control": extra_path_control,
        },
    }


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
        "authority_sync_exception": payload.get("authority_sync_exception") or {},
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
    authority = route_guard.get("authority_source") or {}
    expected_head = str(authority.get("pinned_commit") or "")
    head = runner.run(["git", "-C", str(ITL_ROOT), "rev-parse", "HEAD"])
    failures: list[str] = []
    if head.returncode != 0 or head.stdout.strip() != expected_head:
        failures.append("head")
    for name, pin in (authority.get("objects") or {}).items():
        if not isinstance(pin, dict):
            failures.append(str(name))
            continue
        path = str(pin.get("path") or "")
        oid = runner.run(["git", "-C", str(ITL_ROOT), "rev-parse", f"{expected_head}:{path}"])
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
    route_state = ((route_guard.get("transcribed_itl") or {}).get("route_state") or {})
    red_review = route_guard.get("red_review") or {}
    computed = compute_route_fingerprint(program_state)
    stored = route_guard.get("route_fingerprint")
    pin_status = science_authority_pin_status(program_state, runner)
    schema_version = route_guard.get("schema_version")
    dependency_readback = (
        compute_card2_sync_dependencies(program_state)
        if schema_version == "ego.route_guard.v2"
        else compute_visible_life_phase_b_dependencies(program_state, require_committed_review=True)
        if schema_version == "ego.route_guard.v3"
        else validate_visible_life_core_product_authority(program_state)
        if schema_version == "ego.route_guard.v4"
        else {}
    )
    product = route_guard.get("product_authority") or {}
    is_visible_life = schema_version in {"ego.route_guard.v3", "ego.route_guard.v4"}
    is_visible_life_core = schema_version == "ego.route_guard.v4"
    return {
        "route_revision_id": route_guard.get("route_revision_id"),
        "route_fingerprint": computed if stored == computed else f"MISMATCH:{computed}",
        "current_phase": program.get("current_phase"),
        "current_layer": program.get("current_layer"),
        "allowed_next_action_ids": (
            product.get("allowed_next_actions") or [] if is_visible_life else route_state.get("allowed_next_actions") or []
        ),
        "forbidden_action_classes": (
            product.get("forbidden_next_actions") or [] if is_visible_life else route_state.get("forbidden_next_actions") or []
        ),
        "blocked_until": (((route_state.get("action_dependencies") or {}).get(CARD2_BANK_ACTION_ID) or {}).get("blocked_until") or []),
        "authorized_implementation_targets": (
            product.get("authorized_implementation_targets") or []
            if is_visible_life
            else route_state.get("authorized_implementation_targets") or []
        ),
        "card2_execution_authorized": (((route_state.get("action_dependencies") or {}).get(CARD2_BANK_ACTION_ID) or {}).get("execution_authorized")),
        "effective_card2_bank_action_admitted": False if is_visible_life else bool(dependency_readback.get("all_satisfied")),
        "visible_life_phase_b_admitted": (
            bool(dependency_readback.get("all_satisfied")) if schema_version == "ego.route_guard.v3" else False
        ),
        "product_development_core_lineage": product.get("product_development_core_lineage") if is_visible_life_core else None,
        "product_development_core": product.get("product_development_core") if is_visible_life_core else None,
        "dependency_status": dependency_readback.get("dependencies") or {},
        "science_firewall": (
            product.get("science_firewall") or {} if is_visible_life else route_state.get("science_firewall") or {}
        ),
        "claim_ceiling": product.get("claim_ceiling") or {} if is_visible_life else route_state.get("claim_ceiling") or {},
        "undisposed_lineage_count": None,
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
    route_state = ((route_guard.get("transcribed_itl") or {}).get("route_state") or {})
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
    product_authority = route_guard.get("product_authority") or {}
    authority_sync = scope.get("authority_sync_exception") or {}
    phase_b_receipt_path = str(((route_guard.get("red_review") or {}).get("phase_b") or {}).get("path") or "")
    committed_phase_b = validate_red_review_record(phase_b_receipt_path, require_committed=True)
    authority_sync_completion = (
        task_id == CARD2_SYNC_TASK_ID
        and requested_action == CARD2_SYNC_ACTION_ID
        and current_revision == CARD2_SYNC_ROUTE_REVISION
        and scope.get("source_route_revision_id") == "EGO_ROUTE_8692_SUPERSESSION_001A"
        and scope.get("source_route_fingerprint") == "f605f59393dbba586d50c9e4ee7e085570de7b8d012b0b09bc7ccf75865d52b4"
        and scope.get("expected_target_route_revision_id") == current_revision
        and "docs/PROGRAM_STATE_UNIFIED.yaml" in changed_paths
        and authority_sync.get("exact_task_id") == CARD2_SYNC_TASK_ID
        and authority_sync.get("itl_route_state_blob") == "8b2db13a023873775b80bfe4e8eab7e53a7bba62"
        and authority_sync.get("enabled") is False
        and authority_sync.get("consumed") is True
        and authority_sync.get("wildcard_allowed") is False
        and authority_sync.get("operator_override_allowed") is False
        and committed_phase_b.get("status") != "pass"
    )
    visible_life_transition_requested = (
        task_id == VISIBLE_LIFE_TASK_ID
        and requested_action == VISIBLE_LIFE_TRANSITION_ACTION_ID
    )
    visible_life_transition_task_dir = VISIBLE_LIFE_TASK_PREFIX.rstrip("/")
    visible_life_transition = (
        visible_life_transition_requested
        and visible_life_transition_task_dir in added_task_dirs
        and current_revision == VISIBLE_LIFE_ROUTE_REVISION
        and scope.get("source_route_revision_id") == CARD2_SYNC_ROUTE_REVISION
        and scope.get("source_route_fingerprint") == "39775f663c17adf8dc0efb777d3ad49ee75181c43fea4546808e3dd48a697881"
        and scope.get("expected_target_route_revision_id") == VISIBLE_LIFE_ROUTE_REVISION
        and "docs/PROGRAM_STATE_UNIFIED.yaml" in changed_paths
        and f"{VISIBLE_LIFE_TASK_PREFIX}STAGE_CARD.md" in changed_paths
        and route_guard.get("schema_version") == "ego.route_guard.v3"
        and (route_guard.get("authority_source") or {}).get("pinned_commit") == VISIBLE_LIFE_ITL_COMMIT
        and product_authority.get("action_id") == VISIBLE_LIFE_IMPLEMENT_ACTION_ID
    )
    if visible_life_transition_requested and visible_life_transition_task_dir not in added_task_dirs:
        blockers.append({"reason": "visible_life_transition_reused_or_invalid"})
    visible_life_phase_b = (
        task_id == VISIBLE_LIFE_TASK_ID
        and requested_action == VISIBLE_LIFE_IMPLEMENT_ACTION_ID
        and current_revision == VISIBLE_LIFE_ROUTE_REVISION
    )
    visible_life_core_sync_requested = (
        task_id == VISIBLE_LIFE_CORE_TASK_ID
        and requested_action == VISIBLE_LIFE_CORE_SYNC_ACTION_ID
    )
    visible_life_core_task_dir = VISIBLE_LIFE_CORE_TASK_PREFIX.rstrip("/")
    visible_life_core_sync = (
        visible_life_core_sync_requested
        and visible_life_core_task_dir in added_task_dirs
        and current_revision == VISIBLE_LIFE_CORE_ROUTE_REVISION
        and scope.get("source_route_revision_id") == VISIBLE_LIFE_ROUTE_REVISION
        and scope.get("source_route_fingerprint") == "63a54cb04c634042e27b1af9500cbb1dd87d5d9941959a5abfeac28954f1f4de"
        and scope.get("expected_target_route_revision_id") == VISIBLE_LIFE_CORE_ROUTE_REVISION
        and "docs/PROGRAM_STATE_UNIFIED.yaml" in changed_paths
        and f"{VISIBLE_LIFE_CORE_TASK_PREFIX}STAGE_CARD.md" in changed_paths
        and route_guard.get("schema_version") == "ego.route_guard.v4"
        and (route_guard.get("authority_source") or {}).get("pinned_commit") == VISIBLE_LIFE_CORE_ITL_COMMIT
        and product_authority.get("state") == "ITL_PRODUCT_CORE_AUTHORITY_SYNCED"
        and product_authority.get("product_development_core") == "ego_life_playground_v0"
    )
    if visible_life_core_sync_requested and visible_life_core_task_dir not in added_task_dirs:
        blockers.append({"reason": "visible_life_core_sync_reused_or_invalid"})
    if (
        scope.get("source_route_fingerprint") != current_fingerprint
        and not authority_sync_completion
        and not visible_life_transition
        and not visible_life_core_sync
    ):
        blockers.append(
            {
                "reason": "stale_route_fingerprint",
                "source": scope.get("source_route_fingerprint"),
                "current": current_fingerprint,
            }
        )
    expected_source_revision = (
        "EGO_ROUTE_8692_SUPERSESSION_001A"
        if authority_sync_completion
        else CARD2_SYNC_ROUTE_REVISION
        if visible_life_transition
        else VISIBLE_LIFE_ROUTE_REVISION
        if visible_life_core_sync
        else current_revision
    )
    if scope.get("source_route_revision_id") != expected_source_revision:
        blockers.append(
            {
                "reason": "source_route_revision_mismatch",
                "source": scope.get("source_route_revision_id"),
                "expected": expected_source_revision,
            }
        )
    allowed_actions = (
        product_authority.get("allowed_next_actions") or []
        if route_guard.get("schema_version") in {"ego.route_guard.v3", "ego.route_guard.v4"}
        else route_state.get("allowed_next_actions") or []
    )
    if requested_action not in allowed_actions and not visible_life_transition and not visible_life_core_sync:
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
    if red_triggers:
        red_review_ref = str(scope.get("red_review_ref") or "")
        if not red_review_ref:
            blockers.append({"reason": "authority_change_without_red_review_ref", "triggers": red_triggers})
        else:
            candidate_review = validate_red_review_record(red_review_ref, require_committed=False)
            if candidate_review.get("status") != "pass":
                blockers.append(
                    {
                        "reason": "red_review_not_bound_to_candidate_diff",
                        "red_review_ref": red_review_ref,
                        "errors": candidate_review.get("errors") or [],
                    }
                )
    task_kind = str(scope.get("task_kind") or "")
    if task_id == CARD2_SYNC_TASK_ID and not authority_sync_completion:
        blockers.append({"reason": "authority_sync_exception_reused_or_invalid"})
    if route_state.get("authorized_implementation_targets") != [] or route_state.get("implementation_authorized") is not False:
        blockers.append({"reason": "unauthorized_implementation_targets_nonempty"})
    if visible_life_transition:
        if task_kind != "operator_authorized_red_route_replacement":
            blockers.append({"reason": "visible_life_transition_task_kind_mismatch"})
        if (scope.get("raw") or {}).get("execution_requested") is not False:
            blockers.append({"reason": "visible_life_transition_execution_flag_mismatch"})
        source = read_itl_authority_objects(program_state)
        if source.get("status") != "pass":
            blockers.append({"reason": "visible_life_itl_closure_pin_invalid", "errors": source.get("errors") or []})
        crosswalk = validate_visible_life_closure_crosswalk(program_state)
        if crosswalk.get("status") != "pass":
            blockers.append({"reason": "visible_life_crosswalk_invalid", "errors": crosswalk.get("errors") or []})
        product = validate_visible_life_product_authority(program_state)
        if product.get("status") != "pass":
            blockers.append({"reason": "visible_life_product_authority_invalid", "errors": product.get("errors") or []})
    if visible_life_phase_b:
        if task_kind != "local_product_clock_visible_playground":
            blockers.append({"reason": "visible_life_phase_b_task_kind_mismatch"})
        if (scope.get("raw") or {}).get("execution_requested") is not True:
            blockers.append({"reason": "visible_life_phase_b_execution_flag_mismatch"})
        action_paths = validate_visible_life_action_paths(
            changed_paths=changed_paths,
            scope_allowed_paths=allowed_paths,
            require_complete_set=True,
        )
        for error in action_paths.get("errors") or []:
            blockers.append({"reason": error, "paths": action_paths.get("changed_paths") or []})
        dependencies = compute_visible_life_phase_b_dependencies(
            program_state,
            require_committed_review=True,
        )
        if not dependencies.get("all_satisfied"):
            blockers.append(
                {
                    "reason": "visible_life_phase_b_dependencies_unsatisfied",
                    "dependencies": dependencies.get("dependencies") or {},
                }
            )
    if visible_life_core_sync:
        if task_kind != "cross_repo_product_core_authority_sync":
            blockers.append({"reason": "visible_life_core_sync_task_kind_mismatch"})
        if (scope.get("raw") or {}).get("execution_requested") is not True:
            blockers.append({"reason": "visible_life_core_sync_execution_flag_mismatch"})
        if sorted(set(allowed_paths)) != sorted(VISIBLE_LIFE_CORE_SYNC_PATHS):
            blockers.append({"reason": "visible_life_core_sync_allowlist_mismatch"})
        if (scope.get("raw") or {}).get("itl_product_axis_commit") != VISIBLE_LIFE_CORE_ITL_COMMIT:
            blockers.append({"reason": "visible_life_core_sync_itl_commit_mismatch"})
        if (scope.get("raw") or {}).get("itl_product_axis_route_id") != VISIBLE_LIFE_CORE_ITL_ROUTE_ID:
            blockers.append({"reason": "visible_life_core_sync_itl_route_mismatch"})
        core = validate_visible_life_core_product_authority(program_state)
        if core.get("status") != "pass":
            blockers.append(
                {
                    "reason": "visible_life_core_product_authority_invalid",
                    "errors": core.get("errors") or [],
                }
            )
    if requested_action == CARD2_BANK_ACTION_ID:
        if task_kind != "executable_candidate_independent_headroom":
            blockers.append({"reason": "card2_task_kind_mismatch"})
        action_paths = validate_card2_action_paths(
            route_state=route_state,
            changed_paths=changed_paths,
            scope_loaded=scope.get("status") == "loaded" or bool(scope.get("allowed_mutation_paths")),
            scope_allowed_paths=allowed_paths,
        )
        for error in action_paths.get("errors") or []:
            blockers.append({"reason": error, "paths": action_paths.get("inferred_execution_paths") or []})
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
    card2_governance_path_touched = any(
        path.startswith(CARD2_TASK_PREFIX)
        or path.startswith(CARD2_SYNC_TASK_PREFIX)
        or path.startswith(VISIBLE_LIFE_TASK_PREFIX)
        or path.startswith(VISIBLE_LIFE_CORE_TASK_PREFIX)
        for path in changed_paths
    )
    if changed_paths and (red_triggers or card2_governance_path_touched) and scope.get("status") != "loaded":
        missing_scope = {
            "reason": "missing_mutation_scope_fail_closed",
            "red_trigger_count": len(red_triggers),
            "card2_governance_path_touched": card2_governance_path_touched,
        }
        route_scope_blockers.append(missing_scope)
        blockers.append(missing_scope)
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
