"""Callable temporary-output validation runner for EGO-K0-FOUNDATION-001A."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from typing import Any, Callable, Mapping, Sequence
import uuid


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = REPO_ROOT / "packages" / "ego_k0_kernel" / "src"
CODEX_SCRIPT_DIR = REPO_ROOT / "scripts" / "codex"
for import_root in (REPO_ROOT, PACKAGE_SRC, CODEX_SCRIPT_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from ego_k0_kernel import (  # noqa: E402
    ActionCandidate,
    ActionProposal,
    AdapterCapabilityManifest,
    CapabilityDeniedError,
    CheckpointRecord,
    ContractValidationError,
    EventRecord,
    FOUNDATION_CODE_CONTRACT_VERSION,
    HashMismatchError,
    KernelStateRecord,
    ObservationRecord,
    PostCommitTraceDeliveryError,
    SchemaVersionError,
    TraceRow,
    canonical_hash,
    canonical_json_bytes,
    execute_observation,
    initial_state,
    replay_from_checkpoint,
    stable_id,
)
from ego_k0_kernel.events import observation_to_event  # noqa: E402
from ego_k0_kernel.ports import (  # noqa: E402
    REQUIRED_DENIED_CAPABILITIES,
    assert_capability_allowed,
    validate_adapter_manifest,
)
from scripts.ego_k0_adapters.sqlite_event_store import (  # noqa: E402
    AtomicStepCommitError,
    DuplicateRecordError,
    SequenceConflictError,
    SQLiteEventStore,
    WritesFrozenError,
)
from route_convergence_common import (  # noqa: E402
    load_program_state,
    render_task_lane_index,
)


TASK_ID = "EGO-K0-FOUNDATION-001A"
IMPLEMENTATION_PARENT = "1e25ddead74da9dad810622a657d82f03564091e"
FOUNDATION_IMPLEMENTATION_COMMIT = "fc2c9b1fa9bc3ef010592783d0a959b2aa4485a6"
CORRECTION_CARD_COMMIT = "3404ff008e1920c4e3b6ee93408edaf308d6a975"
ROUTE_SCOPE_REPAIR_COMMIT = "6e9422f31b57a180c7d9719a55f7bde31c6d88ae"
OFFICIAL_OUTPUT_DIR = REPO_ROOT / "artifacts" / "ego_k0_foundation_001a"
CLAIM_CEILING = (
    "additive generated-route-view synchronization, portable provenance enforcement, "
    "Foundation atomic persistence, canonical trace recovery, and evidence-producer "
    "engineering only; no mechanism claim, learned model, learning/replay/memory "
    "contribution, transfer, specialness, initiative, agency, autonomy, subjectivity, "
    "consciousness, functional-subject status, electronic life, product benefit, "
    "EGO/companion readiness, or mainline effect"
)

FOUNDATION_IMPLEMENTATION_PATHS = (
    "packages/ego_k0_kernel/pyproject.toml",
    "packages/ego_k0_kernel/src/ego_k0_kernel/__init__.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/cli.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/contracts.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/events.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/ports.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/replay.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/state.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/trace.py",
    "scripts/ego_k0_adapters/__init__.py",
    "scripts/ego_k0_adapters/sqlite_event_store.py",
    "scripts/run_ego_k0_foundation_validation.py",
    "tests/test_ego_k0_foundation.py",
)
CORRECTION_IMPLEMENTATION_PATHS = (
    "packages/ego_k0_kernel/src/ego_k0_kernel/__init__.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/ports.py",
    "packages/ego_k0_kernel/src/ego_k0_kernel/replay.py",
    "scripts/ego_k0_adapters/sqlite_event_store.py",
    "scripts/run_ego_k0_foundation_validation.py",
    "tests/test_ego_k0_foundation.py",
)
CORRECTION_CARD_PATHS = (
    "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ATOMIC_STEP_COMMIT_ADDENDUM.md",
    "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/MUTATION_SCOPE.yaml",
    "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/STAGE_CARD.md",
)
TASK_LANE_INDEX_REPO_PATH = "docs/codex/tasks/TASK_LANE_INDEX.md"
ROUTE_SCOPE_REPAIR_PATHS = (
    TASK_LANE_INDEX_REPO_PATH,
    "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_ADDENDUM.md",
    "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_MUTATION_SCOPE.yaml",
)
EXECUTED_SOURCE_PATHS = tuple(
    path
    for path in FOUNDATION_IMPLEMENTATION_PATHS
    if path.endswith(".py") and path != "tests/test_ego_k0_foundation.py"
)
ORIGINAL_GATE_NAMES = (
    "typed_schema_contracts",
    "canonical_fresh_process_stability",
    "restart_recovery",
    "fresh_process_replay_x2",
    "mid_chain_checkpoint_resume",
    "stored_action_removal_recomputes",
    "event_tamper_positive_control",
    "sqlite_metadata_tamper_positive_controls",
    "corrupt_state_trace_hash_positive_controls",
    "nested_trace_schema_positive_control",
    "freeze_writes_intervention",
    "sequence_duplicate_fail_closed",
    "package_import_leakage_scan",
    "forbidden_input_leakage_positive_controls",
    "import_without_cli_side_effect_free",
    "adapter_capability_fail_closed",
    "byte_independent_store_records",
    "trace_sink_no_same_round_feedback",
)
INTEGRITY_GATE_NAMES = (
    "canonical_transactional_trace_outbox",
    "atomic_second_write_rollback",
    "post_commit_trace_delivery_recovery",
)
REQUIRED_FORMAL_GATE_NAMES = ORIGINAL_GATE_NAMES + INTEGRITY_GATE_NAMES
DETECTOR_POSITIVE_CONTROL_FIELDS: Mapping[str, tuple[str, ...]] = {
    "event_tamper_positive_control": ("detector_fired",),
    "sqlite_metadata_tamper_positive_controls": (
        "event_metadata_detector_fired",
        "checkpoint_metadata_detector_fired",
    ),
    "corrupt_state_trace_hash_positive_controls": (
        "state_hash_detector_fired",
        "trace_hash_detector_fired",
    ),
    "nested_trace_schema_positive_control": ("detector_fired",),
    "package_import_leakage_scan": ("positive_control_fired",),
    "forbidden_input_leakage_positive_controls": (
        "state_positive_control_fired",
        "observation_positive_control_fired",
    ),
}
DETECTOR_GATE_NAMES = tuple(DETECTOR_POSITIVE_CONTROL_FIELDS)
FORMAL_PROVENANCE_PINS: Mapping[str, Any] = {
    "foundation_card": {
        "commit": "13bd9268993f74a41b4cc219855761681ab12b66",
        "path": "docs/codex/tasks/ego-k0-foundation-001a/STAGE_CARD.md",
        "blob": "f100d78e48b8d9b21327ed86a5fb35305d11d534",
        "sha256": "dbd59aa86faba5bdee3b8f99334dc8bf19e7aea0de96a137d7160bcc7a64acef",
    },
    "correction_cards": (
        {
            "commit": CORRECTION_CARD_COMMIT,
            "path": "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/STAGE_CARD.md",
            "blob": "caf5ee634e42b250a72f6d7fc0f5b953ed15af71",
            "sha256": "1d069194b8ec61efead5c7a904b10e2a7c928a64a6d5278445eef290dc5cce77",
        },
        {
            "commit": CORRECTION_CARD_COMMIT,
            "path": "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/MUTATION_SCOPE.yaml",
            "blob": "39e72b222d94990d80dca299cf6cf14b9de38fea",
            "sha256": "43a19c61fa7e95b0595356e5ba24baf10038a16107be9142d50ab88cf692a356",
        },
        {
            "commit": CORRECTION_CARD_COMMIT,
            "path": "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ATOMIC_STEP_COMMIT_ADDENDUM.md",
            "blob": "500abedcc35f2ea84c8427afa94e67d73ec2cc07",
            "sha256": "90a75e25ee3ee65dda34c3f5b972f46f1c3eb69299f0d6ec8a4e7fc86415f3da",
        },
    ),
    "route_scope_commit": ROUTE_SCOPE_REPAIR_COMMIT,
    "route_scope_objects": (
        {
            "commit": ROUTE_SCOPE_REPAIR_COMMIT,
            "path": "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_ADDENDUM.md",
            "blob": "569e51ae1112a7801d3aedd8a8782387b01a64ba",
            "sha256": "3eb8fedb56f81a4f58c94d6a3765b8e1a44ef0f819e43807b188b58b292a8b1e",
        },
        {
            "commit": ROUTE_SCOPE_REPAIR_COMMIT,
            "path": "docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_MUTATION_SCOPE.yaml",
            "blob": "9718c49335e3cc9a94918fb4a8528a035942704e",
            "sha256": "7ac105eed9b07aea6c2da5d17e250034ed369247b3f838a9e92e7d0e50dcb35f",
        },
        {
            "commit": ROUTE_SCOPE_REPAIR_COMMIT,
            "path": TASK_LANE_INDEX_REPO_PATH,
            "blob": "326c0ffc2ffac9cc3057c497a4786db77065d9ef",
            "sha256": "5b6a9b16c0391a933489edcb655032db31ddd38c342c8cc2e773ee99cb3bd80e",
        },
    ),
    "itl": {
        "authority_commit": "07c0f1f85a3c855511ff1610ec9629f8e94e89b1",
        "route_path": "artifacts/ROUTE-STATE-MACHINE-001A/routes/K0-DUAL-TRACK-SUPERSESSION-001A/state.json",
        "route_blob": "5afe5060fa67caf7aaebfc92ba677d6fa9ee16e3",
        "route_sha256": "ba97b56a971c3325b2862b00ff564f149df46dba178af61a780632f456c69c37",
    },
}


class EvidenceProvenanceError(RuntimeError):
    """A formal evidence source or authority pin failed closed."""


class OutputTargetExistsError(RuntimeError):
    """An evidence producer refuses to overwrite any existing target."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _code_path_hash() -> str:
    paths = [REPO_ROOT / Path(path) for path in EXECUTED_SOURCE_PATHS]
    digest = hashlib.sha256()
    for path in paths:
        relative = path.relative_to(REPO_ROOT).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _aggregate_code_path_bytes(path_bytes: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256()
    for path in sorted(path_bytes):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path_bytes[path])
        digest.update(b"\0")
    return digest.hexdigest()


def _contract_hashes() -> dict[str, str]:
    task_dir = REPO_ROOT / "docs" / "codex" / "tasks" / "ego-k0-foundation-001a"
    correction_dir = (
        REPO_ROOT
        / "docs"
        / "codex"
        / "tasks"
        / "ego-k0-foundation-evidence-atomicity-correction-001a"
    )
    return {
        "stage_card": _sha256_file(task_dir / "STAGE_CARD.md"),
        "kernel_adapter_contract": _sha256_file(task_dir / "KERNEL_ADAPTER_CONTRACT.md"),
        "trace_replay_contract": _sha256_file(task_dir / "TRACE_REPLAY_CONTRACT.md"),
        "mutation_scope": _sha256_file(task_dir / "MUTATION_SCOPE.yaml"),
        "correction_stage_card": _sha256_file(correction_dir / "STAGE_CARD.md"),
        "correction_mutation_scope": _sha256_file(
            correction_dir / "MUTATION_SCOPE.yaml"
        ),
        "atomic_step_commit_addendum": _sha256_file(
            correction_dir / "ATOMIC_STEP_COMMIT_ADDENDUM.md"
        ),
        "route_index_provenance_scope_repair_addendum": _sha256_file(
            correction_dir / "ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_ADDENDUM.md"
        ),
        "route_index_provenance_scope_repair_mutation_scope": _sha256_file(
            correction_dir / "ROUTE_INDEX_PROVENANCE_SCOPE_REPAIR_MUTATION_SCOPE.yaml"
        ),
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def _write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_bytes(canonical_json_bytes(value))
    os.replace(temporary, path)


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise EvidenceProvenanceError(
            f"git {' '.join(args)} failed in {repo}: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def _git_bytes(repo: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise EvidenceProvenanceError(
            f"git {' '.join(args)} failed in {repo}: "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return completed.stdout


def _git_blob_id(repo: Path, commit: str, path: str) -> str:
    line = _git(repo, "ls-tree", commit, "--", path)
    if not line or "\t" not in line:
        raise EvidenceProvenanceError(f"missing Git object {commit}:{path}")
    metadata, actual_path = line.split("\t", 1)
    parts = metadata.split()
    if actual_path != path or len(parts) != 3 or parts[1] != "blob":
        raise EvidenceProvenanceError(f"unexpected Git object record for {commit}:{path}")
    return parts[2]


def _git_changed_paths(repo: Path, commit: str) -> tuple[str, ...]:
    output = _git(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "-r",
        commit,
    )
    return tuple(sorted(line for line in output.splitlines() if line))


def _git_quiet(repo: Path, *args: str) -> bool:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
    )
    if completed.returncode not in (0, 1):
        raise EvidenceProvenanceError(
            f"git {' '.join(args)} failed in {repo}: "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return completed.returncode == 0


def _require_clean_repo(repo: Path) -> dict[str, Any]:
    """Require semantic Git cleanliness without treating EOL materialization as content."""

    index_clean = _git_quiet(repo, "diff", "--cached", "--quiet", "--")
    worktree_clean = _git_quiet(repo, "diff", "--quiet", "--")
    untracked = tuple(
        line
        for line in _git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
        if line
    )
    porcelain = tuple(
        line
        for line in _git(
            repo, "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line
    )
    if not index_clean or not worktree_clean or untracked:
        raise EvidenceProvenanceError(
            f"repository is dirty: {repo}; index_clean={index_clean}, "
            f"worktree_clean={worktree_clean}, untracked={list(untracked)}"
        )
    return {
        "index_semantically_clean": True,
        "worktree_semantically_clean": True,
        "untracked_paths": [],
        "porcelain_status_recorded": list(porcelain),
        "representation_only_status_allowed": bool(porcelain),
    }


def _require_direct_child(repo: Path, child: str, parent: str) -> None:
    actual_parents = tuple(
        item for item in _git(repo, "show", "-s", "--format=%P", child).split() if item
    )
    if actual_parents != (parent,):
        raise EvidenceProvenanceError(
            f"wrong direct parent for {child}: expected exactly [{parent}], "
            f"got {list(actual_parents)}"
        )


def _require_exact_changed_paths(
    repo: Path, commit: str, expected_paths: Sequence[str], *, label: str
) -> tuple[str, ...]:
    actual = _git_changed_paths(repo, commit)
    expected = tuple(sorted(expected_paths))
    if actual != expected:
        raise EvidenceProvenanceError(
            f"{label} path set drifted: expected {list(expected)}, got {list(actual)}"
        )
    return actual


def _verify_git_object_pin(
    repo: Path,
    *,
    head: str,
    commit: str,
    path: str,
    expected_blob: str,
    expected_sha256: str,
) -> dict[str, Any]:
    actual_blob = _git_blob_id(repo, commit, path)
    raw = _git_bytes(repo, "show", f"{commit}:{path}")
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_blob != expected_blob or actual_sha256 != expected_sha256:
        raise EvidenceProvenanceError(
            f"Git object pin mismatch for {commit}:{path}; "
            f"blob={actual_blob}, sha256={actual_sha256}"
        )
    ancestry = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", commit, head],
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise EvidenceProvenanceError(f"{commit} is not an ancestor of {head}")
    return {
        "commit": commit,
        "path": path,
        "blob": actual_blob,
        "sha256": actual_sha256,
        "ancestor_of_head": True,
    }


def _verify_git_working_file(repo: Path, path: str, *, head: str) -> dict[str, Any]:
    working_path = repo / Path(path)
    if not working_path.is_file():
        raise EvidenceProvenanceError(f"executed path is missing: {path}")
    blob = _git_blob_id(repo, head, path)
    working_bytes = working_path.read_bytes()
    committed_bytes = _git_bytes(repo, "show", f"{head}:{path}")
    working_sha256 = hashlib.sha256(working_bytes).hexdigest()
    git_blob_sha256 = hashlib.sha256(committed_bytes).hexdigest()
    index_blob = _git(repo, "rev-parse", f":{path}")
    if index_blob != blob:
        raise EvidenceProvenanceError(
            f"index blob does not match HEAD Git object for {path}: {index_blob} != {blob}"
        )
    hash_object = _git(repo, "hash-object", f"--path={path}", path)
    if hash_object != blob:
        raise EvidenceProvenanceError(
            f"working bytes do not match Git object for {path}: {hash_object} != {blob}"
        )
    return {
        "raw_working_sha256": working_sha256,
        "working_sha256": working_sha256,
        "canonical_git_blob_sha256": git_blob_sha256,
        "git_blob_sha256": git_blob_sha256,
        "raw_sha256_parity": working_sha256 == git_blob_sha256,
        "working_representation_differs": working_sha256 != git_blob_sha256,
        "git_blob": blob,
        "index_blob": index_blob,
        "index_blob_parity": True,
        "git_hash_object_path": hash_object,
        "hash_object_parity": True,
    }


def _verify_itl_authority(itl_repo: Path, pins: Mapping[str, Any]) -> dict[str, Any]:
    authority_commit = str(pins["authority_commit"])
    live_head = _git(itl_repo, "rev-parse", "HEAD")
    ancestry = subprocess.run(
        [
            "git",
            "-C",
            str(itl_repo),
            "merge-base",
            "--is-ancestor",
            authority_commit,
            live_head,
        ],
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise EvidenceProvenanceError(
            f"ITL authority commit {authority_commit} is not an ancestor of {live_head}"
        )
    route_path = str(pins["route_path"])
    authority_route_blob = _git_blob_id(itl_repo, authority_commit, route_path)
    live_route_blob = _git_blob_id(itl_repo, live_head, route_path)
    index_blob = _git(itl_repo, "rev-parse", f":{route_path}")
    route_file = itl_repo / Path(route_path)
    if not route_file.is_file():
        raise EvidenceProvenanceError(f"ITL authority working path is missing: {route_path}")
    canonical_route_bytes = _git_bytes(
        itl_repo, "show", f"{authority_commit}:{route_path}"
    )
    route_sha256 = hashlib.sha256(canonical_route_bytes).hexdigest()
    raw_working_sha256 = _sha256_file(route_file)
    hash_object = _git(itl_repo, "hash-object", f"--path={route_path}", route_path)
    cached_clean = _git_quiet(
        itl_repo, "diff", "--cached", "--quiet", "--", route_path
    )
    working_clean = _git_quiet(itl_repo, "diff", "--quiet", "--", route_path)
    authority_untracked = tuple(
        line
        for line in _git(
            itl_repo,
            "ls-files",
            "--others",
            "--exclude-standard",
            "--",
            route_path,
        ).splitlines()
        if line
    )
    expected_blob = str(pins["route_blob"])
    if (
        authority_route_blob != expected_blob
        or live_route_blob != expected_blob
        or index_blob != expected_blob
        or route_sha256 != pins["route_sha256"]
        or hash_object != expected_blob
        or not cached_clean
        or not working_clean
        or authority_untracked
    ):
        raise EvidenceProvenanceError(
            "ITL route authority path/blob parity failed: "
            f"authority={authority_route_blob}, live={live_route_blob}, "
            f"index={index_blob}, working={hash_object}, "
            f"cached_clean={cached_clean}, working_clean={working_clean}, "
            f"untracked={list(authority_untracked)}"
        )
    try:
        route = json.loads(canonical_route_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceProvenanceError(
            "pinned ITL route Git object is not valid UTF-8 JSON"
        ) from exc
    true_authorities = sorted(
        key for key, value in route.get("authorizations", {}).items() if value is True
    )
    child_authorizations = route.get("child_authorizations", {})
    blocked_children = (
        "ITL-K0-H0-H1-INSTRUMENT-001A:H0",
        "EGO-K0-REFERENCE-KERNEL-001A",
        "ITL-K0-H0-H1-INSTRUMENT-001A:H1",
        "K0-IMMUTABLE-FREEZE-001A",
        "ITL-K0-FORMAL-EVIDENCE-001A",
    )
    valid_authority = (
        route.get("implementation_authorized") is True
        and route.get("authorized_implementation_targets") == [TASK_ID]
        and true_authorities == ["foundation_implementation"]
        and child_authorizations.get(TASK_ID) is True
        and all(child_authorizations.get(name) is False for name in blocked_children)
        and route.get("current_state") == "READY_TO_IMPLEMENT"
    )
    if not valid_authority:
        raise EvidenceProvenanceError("ITL route does not carry Foundation-only authority")
    global_status = tuple(
        line
        for line in _git(
            itl_repo, "status", "--porcelain=v1", "--untracked-files=all"
        ).splitlines()
        if line
    )
    authority_status = tuple(
        line
        for line in _git(
            itl_repo,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            route_path,
        ).splitlines()
        if line
    )
    unrelated_untracked = tuple(
        line
        for line in _git(
            itl_repo, "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        if line and line != route_path
    )
    blocked_authorizations = {
        name: child_authorizations[name] for name in blocked_children
    }
    authority_hash_material = {
        "authority_commit": authority_commit,
        "route_path": route_path,
        "route_blob": authority_route_blob,
        "route_sha256": route_sha256,
        "authorized_implementation_targets": route["authorized_implementation_targets"],
        "true_authorities": true_authorities,
        "blocked_child_authorizations": blocked_authorizations,
        "ancestor_of_live_head": True,
        "live_route_blob_matches_authority": True,
    }
    return {
        "authority_commit": authority_commit,
        "live_head": live_head,
        "authority_commit_ancestor_of_live_head": True,
        "route_path": route_path,
        "route_blob": authority_route_blob,
        "authority_route_blob": authority_route_blob,
        "live_route_blob": live_route_blob,
        "index_blob": index_blob,
        "route_sha256": route_sha256,
        "raw_working_sha256": raw_working_sha256,
        "raw_sha256_parity": raw_working_sha256 == route_sha256,
        "working_representation_differs": raw_working_sha256 != route_sha256,
        "git_hash_object_path": hash_object,
        "authority_path_cached_clean": True,
        "authority_path_working_clean": True,
        "authority_path_status_recorded": list(authority_status),
        "repo_status_context": list(global_status),
        "unrelated_untracked_paths": list(unrelated_untracked),
        "authorized_implementation_targets": route["authorized_implementation_targets"],
        "true_authorities": true_authorities,
        "blocked_child_authorizations": blocked_authorizations,
        "authority_hash_material": authority_hash_material,
    }


def _render_canonical_task_lane_index_bytes() -> bytes:
    return render_task_lane_index(load_program_state()).encode("utf-8")


def _verify_canonical_route_index(
    repo: Path,
    *,
    head: str,
    intermediate_commit: str,
    pin: Mapping[str, Any],
    renderer: Callable[[], str | bytes] | None = None,
) -> dict[str, Any]:
    if pin.get("commit") != intermediate_commit:
        raise EvidenceProvenanceError(
            "canonical route index pin does not use the intermediate commit"
        )
    pinned = _verify_git_object_pin(
        repo,
        head=head,
        commit=intermediate_commit,
        path=str(pin["path"]),
        expected_blob=str(pin["blob"]),
        expected_sha256=str(pin["sha256"]),
    )
    live_blob = _git_blob_id(repo, head, str(pin["path"]))
    pinned_bytes = _git_bytes(repo, "show", f"{intermediate_commit}:{pin['path']}")
    live_bytes = _git_bytes(repo, "show", f"{head}:{pin['path']}")
    if live_blob != pin["blob"] or live_bytes != pinned_bytes:
        raise EvidenceProvenanceError(
            "canonical TASK_LANE_INDEX no longer inherits the pinned generated view"
        )
    rendered = (renderer or _render_canonical_task_lane_index_bytes)()
    rendered_bytes = rendered.encode("utf-8") if isinstance(rendered, str) else rendered
    if rendered_bytes != pinned_bytes:
        raise EvidenceProvenanceError(
            "canonical TASK_LANE_INDEX renderer output differs from the pinned view"
        )
    working = _verify_git_working_file(repo, str(pin["path"]), head=head)
    return {
        **pinned,
        "live_blob": live_blob,
        "live_inherits_pinned_blob": True,
        "renderer_matches_pinned_bytes": True,
        "rendered_sha256": hashlib.sha256(rendered_bytes).hexdigest(),
        "working_file": working,
    }


def verify_formal_provenance(
    *,
    repo_root: Path = REPO_ROOT,
    itl_repo: Path | None = None,
    pins: Mapping[str, Any] = FORMAL_PROVENANCE_PINS,
) -> dict[str, Any]:
    """Verify Git objects, working bytes, ancestry, and ITL route authority."""

    repo_root = Path(repo_root)
    itl_repo = Path(itl_repo or repo_root.parent / "intelligence-theory-lab")
    semantic_cleanliness = _require_clean_repo(repo_root)
    branch = _git(repo_root, "branch", "--show-current")
    head = _git(repo_root, "rev-parse", "HEAD")
    route_scope_commit = str(pins["route_scope_commit"])
    if branch != "main":
        raise EvidenceProvenanceError(f"wrong EGO branch: {branch}")
    _require_direct_child(repo_root, FOUNDATION_IMPLEMENTATION_COMMIT, IMPLEMENTATION_PARENT)
    _require_exact_changed_paths(
        repo_root,
        FOUNDATION_IMPLEMENTATION_COMMIT,
        FOUNDATION_IMPLEMENTATION_PATHS,
        label="Foundation implementation commit",
    )
    _require_direct_child(
        repo_root, CORRECTION_CARD_COMMIT, FOUNDATION_IMPLEMENTATION_COMMIT
    )
    _require_exact_changed_paths(
        repo_root,
        CORRECTION_CARD_COMMIT,
        CORRECTION_CARD_PATHS,
        label="correction card commit",
    )
    _require_direct_child(repo_root, route_scope_commit, CORRECTION_CARD_COMMIT)
    _require_exact_changed_paths(
        repo_root,
        route_scope_commit,
        ROUTE_SCOPE_REPAIR_PATHS,
        label="route/provenance scope-repair commit",
    )
    _require_direct_child(repo_root, head, route_scope_commit)
    _require_exact_changed_paths(
        repo_root,
        head,
        CORRECTION_IMPLEMENTATION_PATHS,
        label="correction producer HEAD",
    )

    foundation_card = _verify_git_object_pin(
        repo_root,
        head=head,
        commit=pins["foundation_card"]["commit"],
        path=pins["foundation_card"]["path"],
        expected_blob=pins["foundation_card"]["blob"],
        expected_sha256=pins["foundation_card"]["sha256"],
    )
    correction_cards = [
        _verify_git_object_pin(
            repo_root,
            head=head,
            commit=item["commit"],
            path=item["path"],
            expected_blob=item["blob"],
            expected_sha256=item["sha256"],
        )
        for item in pins["correction_cards"]
    ]
    route_scope_pins = tuple(pins["route_scope_objects"])
    if tuple(sorted(str(item["path"]) for item in route_scope_pins)) != tuple(
        sorted(ROUTE_SCOPE_REPAIR_PATHS)
    ):
        raise EvidenceProvenanceError("route-scope object pin path set drifted")
    route_scope_objects: list[dict[str, Any]] = []
    canonical_route_index: dict[str, Any] | None = None
    for item in route_scope_pins:
        if item.get("commit") != route_scope_commit:
            raise EvidenceProvenanceError(
                f"route-scope object pin uses wrong intermediate commit: {item.get('path')}"
            )
        if item["path"] == TASK_LANE_INDEX_REPO_PATH:
            canonical_route_index = _verify_canonical_route_index(
                repo_root,
                head=head,
                intermediate_commit=route_scope_commit,
                pin=item,
            )
            route_scope_objects.append(canonical_route_index)
        else:
            route_scope_objects.append(
                _verify_git_object_pin(
                    repo_root,
                    head=head,
                    commit=route_scope_commit,
                    path=item["path"],
                    expected_blob=item["blob"],
                    expected_sha256=item["sha256"],
                )
            )
    if canonical_route_index is None:
        raise EvidenceProvenanceError("canonical TASK_LANE_INDEX object pin is missing")
    executed_files = {
        path: _verify_git_working_file(repo_root, path, head=head)
        for path in EXECUTED_SOURCE_PATHS
    }
    code_path_hashes = {
        "executed_working_hash": _aggregate_code_path_bytes(
            {
                path: (repo_root / Path(path)).read_bytes()
                for path in EXECUTED_SOURCE_PATHS
            }
        ),
        "canonical_git_object_hash": _aggregate_code_path_bytes(
            {
                path: _git_bytes(repo_root, "show", f"{head}:{path}")
                for path in EXECUTED_SOURCE_PATHS
            }
        ),
        "aggregation_rule": "sorted repo-relative path, NUL, bytes, NUL, SHA-256",
    }
    itl = _verify_itl_authority(itl_repo, pins["itl"])
    authority_material = {
        "ego_head": head,
        "foundation_card_blob": foundation_card["blob"],
        "correction_card_blobs": [item["blob"] for item in correction_cards],
        "route_scope_commit": route_scope_commit,
        "route_scope_blobs": [item["blob"] for item in route_scope_objects],
        "itl_authority": itl["authority_hash_material"],
        "runtime_authority": "none",
        "mainline_connected": False,
        "enabled": False,
    }
    return {
        "producer_function": "scripts.run_ego_k0_foundation_validation.verify_formal_provenance",
        "ego": {
            "branch": branch,
            "head": head,
            "semantic_worktree_and_index_clean": True,
            "porcelain_clean": not semantic_cleanliness[
                "porcelain_status_recorded"
            ],
            "semantic_cleanliness": semantic_cleanliness,
            "implementation_base_commit": FOUNDATION_IMPLEMENTATION_COMMIT,
            "implementation_parent": IMPLEMENTATION_PARENT,
            "implementation_changed_paths": list(FOUNDATION_IMPLEMENTATION_PATHS),
            "correction_card_commit": CORRECTION_CARD_COMMIT,
            "correction_card_changed_paths": list(CORRECTION_CARD_PATHS),
            "route_scope_commit": route_scope_commit,
            "route_scope_changed_paths": list(ROUTE_SCOPE_REPAIR_PATHS),
            "correction_changed_paths": list(CORRECTION_IMPLEMENTATION_PATHS),
            "executed_files": executed_files,
            "code_path_hash_provenance": code_path_hashes,
            "foundation_card": foundation_card,
            "correction_cards": correction_cards,
            "route_scope_objects": route_scope_objects,
            "canonical_route_index": canonical_route_index,
        },
        "itl": itl,
        "execution_authority_hash": canonical_hash(authority_material),
        "claim_ceiling": CLAIM_CEILING,
    }


def resolve_foundation_verdict(
    per_gate_outcomes: Mapping[str, Mapping[str, Any]],
) -> str:
    """Resolve a formal vocabulary value only from callable gate outcomes."""

    if not per_gate_outcomes:
        return "foundation_engineering_fail_no_gates"
    missing = sorted(set(REQUIRED_FORMAL_GATE_NAMES) - set(per_gate_outcomes))
    if missing:
        return f"foundation_engineering_fail_missing_gate_{missing[0]}"
    for detector in DETECTOR_GATE_NAMES:
        details = per_gate_outcomes.get(detector)
        positive_control_fields = DETECTOR_POSITIVE_CONTROL_FIELDS[detector]
        if (
            details is not None
            and any(details.get(field) is not True for field in positive_control_fields)
        ):
            return f"foundation_instrument_invalid_{detector}"
    failed = sorted(
        name for name, details in per_gate_outcomes.items() if details.get("ok") is not True
    )
    if failed:
        return f"foundation_engineering_fail_{failed[0]}"
    return "foundation_engineering_pass"


def _claim_output_directory(output_dir: Path) -> None:
    try:
        output_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise OutputTargetExistsError(
            f"evidence output already exists and will not be overwritten: {output_dir}"
        ) from exc


def run_evidence_producer(
    *,
    output_dir: Path,
    run_id: str,
    official: bool,
    itl_repo: Path | None = None,
    validation_producer: Callable[..., dict[str, Any]] | None = None,
    provenance_producer: Callable[..., dict[str, Any]] = verify_formal_provenance,
) -> dict[str, Any]:
    """Run the formal producer path; trials remain explicitly non-official."""

    output_dir = Path(output_dir)
    if output_dir.exists():
        raise OutputTargetExistsError(
            f"evidence output already exists and will not be overwritten: {output_dir}"
        )
    validation_producer_supplied = validation_producer is not None
    validation_producer = validation_producer or run_validation
    producer_code_path_hash: str | None = None
    producer_contract_hashes: dict[str, str] = {}
    provenance: dict[str, Any] | None = None
    phase = "producer_setup"
    output_claimed = False
    try:
        if official and output_dir.resolve() != OFFICIAL_OUTPUT_DIR.resolve():
            raise EvidenceProvenanceError(
                f"official evidence target must be {OFFICIAL_OUTPUT_DIR}"
            )
        if official and (
            validation_producer_supplied
            or provenance_producer is not verify_formal_provenance
        ):
            raise EvidenceProvenanceError(
                "official evidence production forbids injected validation or provenance producers"
            )
        producer_code_path_hash = _code_path_hash()
        producer_contract_hashes = _contract_hashes()
        phase = "provenance"
        provenance = provenance_producer(
            repo_root=REPO_ROOT,
            itl_repo=itl_repo,
            pins=FORMAL_PROVENANCE_PINS,
        )
        code_path_hash_provenance = (
            provenance.get("ego", {}).get("code_path_hash_provenance")
            if isinstance(provenance, Mapping)
            else None
        )
        if code_path_hash_provenance is not None and (
            code_path_hash_provenance.get("executed_working_hash")
            != producer_code_path_hash
        ):
            raise EvidenceProvenanceError(
                "producer executed-working code-path hash changed during provenance"
            )
        _claim_output_directory(output_dir)
        output_claimed = True
        phase = "computed_gates"
        validation = validation_producer(
            output_dir=output_dir / "raw_validation", run_id=run_id
        )
        per_gate_outcomes = validation["per_gate_outcomes"]
        if code_path_hash_provenance is not None and (
            validation["code_path_hash"]
            != code_path_hash_provenance["executed_working_hash"]
        ):
            raise EvidenceProvenanceError(
                "validation code-path hash differs from verified executed-working hash"
            )
        candidate_verdict = resolve_foundation_verdict(per_gate_outcomes)
        result = {
            "schema_version": "ego_k0.foundation_evidence_result.v1",
            "producer_function": "scripts.run_ego_k0_foundation_validation.run_evidence_producer",
            "task_id": TASK_ID,
            "run_id": run_id,
            "episode_ids": validation["episode_ids"],
            "context_ids": validation["context_ids"],
            "seed_context": validation["seed_context"],
            "aggregation_rule": (
                "detector blindness precedence, then stable first failed gate, "
                "else logical AND engineering pass"
            ),
            "code_path_hash": validation["code_path_hash"],
            "code_path_hash_provenance": code_path_hash_provenance,
            "contract_hashes": validation["contract_hashes"],
            "input_artifact_hashes": {
                **validation["input_artifact_hashes"],
                "verified_provenance": canonical_hash(provenance),
                "computed_gate_outcomes": canonical_hash(per_gate_outcomes),
            },
            "per_gate_outcomes": per_gate_outcomes,
            "candidate_verdict": candidate_verdict,
            "verdict": candidate_verdict if official else "NOT_ADJUDICATED_TRIAL",
            "foundation_task_final_acceptance": (
                candidate_verdict if official else "NOT_ADJUDICATED"
            ),
            "official_run_attempted": official,
            "official_evidence_bank": official,
            "producer_completed": True,
            "provenance": provenance,
            "execution_authority_hash": provenance["execution_authority_hash"],
            "mainline_connected": False,
            "enabled": False,
            "runtime_authority": "none",
            "claim_ceiling": CLAIM_CEILING,
        }
        _write_json_atomic(output_dir / "result.json", result)
        if candidate_verdict != "foundation_engineering_pass":
            failure_manifest = {
                "schema_version": "ego_k0.foundation_failure_manifest.v1",
                "run_id": run_id,
                "phase": "adjudication",
                "candidate_verdict": candidate_verdict,
                "failed_gates": sorted(
                    name
                    for name, details in per_gate_outcomes.items()
                    if details.get("ok") is not True
                ),
            }
            _write_json_atomic(output_dir / "failure_manifest.json", failure_manifest)
        return result
    except Exception as exc:
        if isinstance(exc, OutputTargetExistsError):
            raise
        if not output_claimed:
            _claim_output_directory(output_dir)
        failure_manifest = {
            "schema_version": "ego_k0.foundation_failure_manifest.v1",
            "run_id": run_id,
            "phase": phase,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "verified_provenance": provenance,
        }
        result = {
            "schema_version": "ego_k0.foundation_evidence_result.v1",
            "producer_function": "scripts.run_ego_k0_foundation_validation.run_evidence_producer",
            "task_id": TASK_ID,
            "run_id": run_id,
            "episode_ids": ["foundation-probe-episode-v1"],
            "context_ids": [
                "foundation_probe_v1",
                "restart",
                "stored_action_removal",
            ],
            "seed_context": {"seed": 1701, "initial_draw_count": 0},
            "aggregation_rule": (
                "caught producer exception classified by failing producer phase; "
                "no Foundation acceptance adjudicated"
            ),
            "code_path_hash": producer_code_path_hash
            or "UNAVAILABLE_DUE_TO_PRODUCER_SETUP_FAILURE",
            "code_path_hash_provenance": (
                provenance.get("ego", {}).get("code_path_hash_provenance")
                if isinstance(provenance, Mapping)
                else None
            ),
            "contract_hashes": producer_contract_hashes,
            "input_artifact_hashes": (
                {"verified_provenance": canonical_hash(provenance)}
                if provenance is not None
                else {}
            ),
            "candidate_verdict": f"foundation_engineering_fail_producer_{phase}",
            "verdict": "NOT_ADJUDICATED_PRODUCER_FAILURE",
            "foundation_task_final_acceptance": "NOT_ADJUDICATED",
            "official_run_attempted": official,
            "official_evidence_bank": False,
            "producer_completed": False,
            "failure_manifest": "failure_manifest.json",
            "provenance": provenance,
            "execution_authority_hash": (
                provenance.get("execution_authority_hash")
                if provenance is not None
                else None
            ),
            "mainline_connected": False,
            "enabled": False,
            "runtime_authority": "none",
            "claim_ceiling": CLAIM_CEILING,
        }
        _write_json_atomic(output_dir / "failure_manifest.json", failure_manifest)
        _write_json_atomic(output_dir / "result.json", result)
        return result


FORBIDDEN_PACKAGE_IMPORT_ROOTS = frozenset(
    {
        "sqlite3",
        "requests",
        "httpx",
        "http",
        "aiohttp",
        "urllib3",
        "websocket",
        "websockets",
        "socket",
        "ssl",
        "urllib",
        "ftplib",
        "smtplib",
        "telnetlib",
        "grpc",
        "openai",
        "anthropic",
        "litellm",
        "transformers",
        "EgoOperator",
        "EgoDesktop",
        "scripts",
    }
)


def scan_forbidden_package_imports(source: str, *, label: str) -> list[str]:
    """Parse imports; used for both the real tree and a firing positive control."""

    tree = ast.parse(source, filename=label)
    findings: list[str] = []
    for node in ast.walk(tree):
        names: list[str] = []
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        for name in names:
            root = name.split(".", 1)[0]
            if root in FORBIDDEN_PACKAGE_IMPORT_ROOTS or root.startswith("itl_"):
                findings.append(f"{label}:{node.lineno}:{name}")
    return findings


def _typed_contract_gate() -> dict[str, Any]:
    observation = _observation("typed-runner-episode", 1)
    state = initial_state("typed-runner-episode", seed=11)
    candidate = ActionCandidate("probe.typed", {"weight": 0.5}, True)
    proposal = ActionProposal(
        proposal_id="proposal-typed-runner",
        episode_id="typed-runner-episode",
        step_id=1,
        selected_action_id=candidate.action_id,
        candidates=(candidate,),
        decision_factors={"source": "typed_contract_gate"},
    )
    checkpoint = _checkpoint(state, 0, "typed-runner")
    event = observation_to_event(observation, sequence=1)
    manifest = AdapterCapabilityManifest(
        adapter_id="typed-runner-adapter",
        readable_fields=("events",),
        writable_ports=("append_events",),
        forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
    )
    distinct_count = len(
        {
            type(observation),
            type(event),
            type(state),
            type(candidate),
            type(proposal),
            type(checkpoint),
            type(manifest),
        }
    )
    finite_rejected = False
    schema_rejected = False
    contract_version_rejected = False
    try:
        ObservationRecord("bad-finite", "typed-runner-episode", 1, {"x": float("nan")})
    except ContractValidationError:
        finite_rejected = True
    wrong_schema = event.to_dict()
    wrong_schema["schema_version"] = "ego_k0.event.future"
    try:
        EventRecord.from_dict(wrong_schema)
    except SchemaVersionError:
        schema_rejected = True
    wrong_contract = checkpoint.to_dict()
    wrong_contract["code_contract_version"] = "ego_k0.trace_replay.future"
    try:
        CheckpointRecord.from_dict(wrong_contract)
    except SchemaVersionError:
        contract_version_rejected = True
    ok = (
        distinct_count == 7
        and finite_rejected
        and schema_rejected
        and contract_version_rejected
        and proposal.execution_authority is False
    )
    return {
        "ok": ok,
        "distinct_record_type_count": distinct_count,
        "finite_number_rejected": finite_rejected,
        "schema_mismatch_rejected": schema_rejected,
        "contract_version_mismatch_rejected": contract_version_rejected,
    }


def _forbidden_input_leakage_gate() -> dict[str, Any]:
    state_control_fired = False
    observation_control_fired = False
    try:
        KernelStateRecord(
            episode_id="leakage-positive-control",
            step_id=0,
            substates={"observation_count": 0},
            rng_state={"seed": 1, "draw_count": 0, "family_id": "forbidden"},
        )
    except ContractValidationError:
        state_control_fired = True
    try:
        ObservationRecord(
            observation_id="leakage-observation-control",
            episode_id="leakage-positive-control",
            step_id=1,
            payload={"nested": {"heldout_label": "forbidden"}},
        )
    except ContractValidationError:
        observation_control_fired = True
    return {
        "ok": state_control_fired and observation_control_fired,
        "state_positive_control_fired": state_control_fired,
        "observation_positive_control_fired": observation_control_fired,
    }


def _canonical_fresh_process_gate(output_dir: Path) -> dict[str, Any]:
    payload = {"z": [1, 2.5, "猫"], "a": {"flag": True}}
    expected = canonical_hash(payload)
    program = (
        "from ego_k0_kernel.contracts import canonical_hash; "
        f"print(canonical_hash({payload!r}))"
    )
    env = dict(os.environ)
    env["PYTHONPATH"] = str(PACKAGE_SRC)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    probe_dir = output_dir / "canonical_process_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for _ in range(2):
        completed = subprocess.run(
            [sys.executable, "-c", program],
            cwd=probe_dir,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        outputs.append(completed.stdout.strip() if completed.returncode == 0 else "")
    return {"ok": outputs == [expected, expected], "expected": expected, "observed": outputs}


def _import_leakage_gate() -> dict[str, Any]:
    package_dir = PACKAGE_SRC / "ego_k0_kernel"
    actual_findings: list[str] = []
    for path in sorted(package_dir.glob("*.py")):
        actual_findings.extend(
            scan_forbidden_package_imports(
                path.read_text(encoding="utf-8"), label=path.name
            )
        )
    positive_findings = scan_forbidden_package_imports(
        "import sqlite3\nfrom scripts.ego_kernel import state\n",
        label="positive_control.py",
    )
    positive_roots = {finding.rsplit(":", 1)[-1].split(".", 1)[0] for finding in positive_findings}
    positive_control_fired = {"sqlite3", "scripts"}.issubset(positive_roots)
    return {
        "ok": not actual_findings and positive_control_fired,
        "actual_findings": actual_findings,
        "actual_scan_clean": not actual_findings,
        "positive_control_fired": positive_control_fired,
        "positive_control_findings": positive_findings,
    }


def _import_side_effect_gate(output_dir: Path) -> dict[str, Any]:
    probe_dir = output_dir / "import_side_effect_probe"
    probe_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(PACKAGE_SRC), str(REPO_ROOT)))
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    program = (
        "import pathlib; before=sorted(p.name for p in pathlib.Path('.').iterdir()); "
        "import ego_k0_kernel; import scripts.ego_k0_adapters.sqlite_event_store; "
        "after=sorted(p.name for p in pathlib.Path('.').iterdir()); "
        "assert before == after"
    )
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=probe_dir,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    residue = sorted(item.name for item in probe_dir.iterdir())
    return {
        "ok": completed.returncode == 0 and not residue,
        "returncode": completed.returncode,
        "residue": residue,
    }


def _adapter_capability_gate() -> dict[str, Any]:
    manifest = validate_adapter_manifest(
        AdapterCapabilityManifest(
            adapter_id="runner-capability-probe",
            readable_fields=("events", "checkpoints"),
            writable_ports=("append_events", "write_checkpoint"),
            forbidden_capabilities=tuple(sorted(REQUIRED_DENIED_CAPABILITIES)),
        )
    )
    denied = False
    unknown = False
    try:
        assert_capability_allowed(manifest, "execute_action")
    except CapabilityDeniedError:
        denied = True
    try:
        assert_capability_allowed(manifest, "unknown_probe_capability")
    except CapabilityDeniedError:
        unknown = True
    return {"ok": denied and unknown, "deny_control_fired": denied, "unknown_control_fired": unknown}


def _fail_closed_store_gate(output_dir: Path) -> dict[str, Any]:
    database_path = output_dir / "fail_closed_probe.sqlite3"
    episode_id = "fail-closed-runner-episode"
    first = observation_to_event(_observation(episode_id, 1), sequence=1)
    sequence_rejected = False
    duplicate_rejected = False
    with SQLiteEventStore(database_path) as store:
        try:
            store.append_events(1, (first,))
        except SequenceConflictError:
            sequence_rejected = True
        store.append_events(0, (first,))
        duplicate = EventRecord(
            event_id=first.event_id,
            episode_id=episode_id,
            step_id=2,
            sequence=2,
            event_type=first.event_type,
            payload={"observation": _observation(episode_id, 2).to_dict()},
            provenance=first.provenance,
        )
        try:
            store.append_events(1, (duplicate,))
        except DuplicateRecordError:
            duplicate_rejected = True
    return {
        "ok": sequence_rejected and duplicate_rejected,
        "sequence_mismatch_rejected": sequence_rejected,
        "duplicate_id_rejected": duplicate_rejected,
    }


class DeterministicProbePolicy:
    """Validation-only deterministic policy; it cannot execute its proposal."""

    def propose(
        self, state: KernelStateRecord, observation: ObservationRecord
    ) -> ActionProposal:
        decision_digest = canonical_hash(
            {
                "seed": state.rng_state["seed"],
                "draw_count": state.rng_state["draw_count"],
                "observation": observation.to_dict(),
            }
        )
        candidates = (
            ActionCandidate(
                action_id="probe.record",
                typed_parameters={"mode": "record"},
                admissible=True,
            ),
            ActionCandidate(
                action_id="probe.defer",
                typed_parameters={"mode": "defer"},
                admissible=True,
            ),
        )
        selected = candidates[int(decision_digest[-1], 16) % len(candidates)].action_id
        proposal_body = {
            "episode_id": observation.episode_id,
            "step_id": observation.step_id,
            "selected": selected,
            "decision_digest": decision_digest,
        }
        return ActionProposal(
            proposal_id=stable_id("proposal", proposal_body),
            episode_id=observation.episode_id,
            step_id=observation.step_id,
            selected_action_id=selected,
            candidates=candidates,
            decision_factors={
                "probe_policy": "deterministic_sha256_choice",
                "decision_digest": decision_digest,
                "execution_authority": False,
            },
            execution_authority=False,
        )


class CollectingTraceSink:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def append(self, row: object) -> None:
        self.rows.append(row.to_dict())


def _observation(episode_id: str, step_id: int) -> ObservationRecord:
    signals = ("amber", "blue", "green", "violet")
    payload = {
        "signal": signals[(step_id - 1) % len(signals)],
        "magnitude": step_id / 10,
        "note": f"foundation-observation-{step_id}",
    }
    return ObservationRecord(
        observation_id=stable_id(
            "observation", {"episode_id": episode_id, "step_id": step_id, "payload": payload}
        ),
        episode_id=episode_id,
        step_id=step_id,
        payload=payload,
        source_refs=(f"context:foundation:{step_id}",),
    )


def _checkpoint(state: KernelStateRecord, sequence: int, label: str) -> CheckpointRecord:
    return CheckpointRecord(
        checkpoint_id=stable_id(
            "checkpoint",
            {"label": label, "state_hash": state.state_hash, "sequence": sequence},
        ),
        state=state,
        last_event_sequence=sequence,
        code_contract_version=FOUNDATION_CODE_CONTRACT_VERSION,
    )


def _trace_sink_feedback_gate(
    *, output_dir: Path, code_path_hash: str, contract_hash: str
) -> dict[str, Any]:
    class MutatingCopySink:
        def __init__(self) -> None:
            self.captured: dict[str, Any] | None = None

        def append(self, row: TraceRow) -> None:
            self.captured = row.to_dict()
            self.captured["state_after_hash"] = "mutated-sink-copy"
            self.captured["selected_action_proposal"]["selected_action_id"] = "mutated"

    episode_id = "trace-feedback-runner-episode"
    state = initial_state(episode_id, seed=31)
    sink = MutatingCopySink()
    with SQLiteEventStore(output_dir / "trace_feedback_probe.sqlite3") as store:
        result = execute_observation(
            state=state,
            observation=_observation(episode_id, 1),
            policy=DeterministicProbePolicy(),
            event_store=store,
            trace_sink=sink,
            expected_sequence=0,
            task_id=TASK_ID,
            run_id="trace-feedback-probe",
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        )
    unaffected = (
        result.state_after.state_hash != "mutated-sink-copy"
        and result.proposal.selected_action_id != "mutated"
        and result.trace_row.state_after_hash == result.state_after.state_hash
    )
    return {
        "ok": unaffected and sink.captured is not None,
        "sink_copy_mutation_observed": sink.captured is not None,
        "same_round_result_unaffected": unaffected,
    }


def _atomic_second_write_rollback_gate(
    *, output_dir: Path, code_path_hash: str, contract_hash: str
) -> dict[str, Any]:
    database_path = output_dir / "atomic_second_write_probe.sqlite3"
    episode_id = "atomic-second-write-runner-episode"
    with SQLiteEventStore(database_path):
        pass
    connection = sqlite3.connect(str(database_path))
    try:
        connection.execute(
            """
            CREATE TRIGGER force_trace_outbox_failure
            BEFORE INSERT ON trace_outbox
            BEGIN
                SELECT RAISE(ROLLBACK, 'forced second write failure');
            END;
            """
        )
        connection.commit()
    finally:
        connection.close()

    rolled_back = False
    sink = CollectingTraceSink()
    with SQLiteEventStore(database_path) as store:
        try:
            execute_observation(
                state=initial_state(episode_id, seed=37),
                observation=_observation(episode_id, 1),
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=sink,
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="atomic-second-write-probe",
                code_path_hash=code_path_hash,
                contract_hash=contract_hash,
            )
        except AtomicStepCommitError as exc:
            rolled_back = exc.committed is False
        events = store.read_events(episode_id, 0)
        traces = store.read_trace_rows(episode_id, 0)
    return {
        "ok": rolled_back and not events and not traces and not sink.rows,
        "typed_rollback_error": rolled_back,
        "committed_event_count": len(events),
        "committed_trace_count": len(traces),
        "delivery_sink_count": len(sink.rows),
    }


def _post_commit_delivery_recovery_gate(
    *, output_dir: Path, code_path_hash: str, contract_hash: str
) -> dict[str, Any]:
    class ThrowingTraceSink:
        def append(self, row: TraceRow) -> None:
            raise RuntimeError(f"forced delivery failure for {row.trace_hash}")

    database_path = output_dir / "post_commit_delivery_probe.sqlite3"
    episode_id = "post-commit-delivery-runner-episode"
    state = initial_state(episode_id, seed=41)
    receipt: dict[str, Any] | None = None
    retry_rejected = False
    with SQLiteEventStore(database_path) as store:
        try:
            execute_observation(
                state=state,
                observation=_observation(episode_id, 1),
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=ThrowingTraceSink(),
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="post-commit-delivery-probe",
                code_path_hash=code_path_hash,
                contract_hash=contract_hash,
            )
        except PostCommitTraceDeliveryError as exc:
            receipt = exc.to_dict()
        events = store.read_events(episode_id, 0)
        traces = store.read_trace_rows(episode_id, 0)
        try:
            execute_observation(
                state=state,
                observation=_observation(episode_id, 1),
                policy=DeterministicProbePolicy(),
                event_store=store,
                trace_sink=CollectingTraceSink(),
                expected_sequence=0,
                task_id=TASK_ID,
                run_id="post-commit-delivery-retry-probe",
                code_path_hash=code_path_hash,
                contract_hash=contract_hash,
            )
        except SequenceConflictError:
            retry_rejected = True
    identity_matches = (
        receipt is not None
        and receipt["committed"] is True
        and receipt["committed_sequence"] == 1
        and len(events) == 1
        and len(traces) == 1
        and receipt["trace_hash"] == traces[0].trace_hash
    )
    replay = replay_from_checkpoint(
        checkpoint=_checkpoint(state, 0, "post-commit-delivery"),
        events=events,
        policy=DeterministicProbePolicy(),
        task_id=TASK_ID,
        run_id="post-commit-delivery-replay",
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
        context_ids=("post_commit_delivery_recovery",),
        expected_traces=[item.to_dict() for item in traces],
    )
    return {
        "ok": identity_matches and retry_rejected and replay.ok,
        "typed_delivery_receipt": receipt,
        "committed_event_count": len(events),
        "committed_trace_count": len(traces),
        "retry_source_append_rejected": retry_rejected,
        "canonical_replay_ok": replay.ok,
    }


def run_replay(
    *,
    output_dir: Path,
    database_path: Path,
    checkpoint_path: Path,
    trace_path: Path | None,
    run_id: str,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = CheckpointRecord.from_dict(
        json.loads(checkpoint_path.read_text(encoding="utf-8"))
    )
    expected_traces = None
    if trace_path is not None:
        expected_traces = json.loads(trace_path.read_text(encoding="utf-8"))
    code_path_hash = _code_path_hash()
    contracts = _contract_hashes()
    contract_hash = canonical_hash(contracts)
    with SQLiteEventStore(database_path) as store:
        events = store.read_events(
            checkpoint.state.episode_id, checkpoint.last_event_sequence
        )
    result = replay_from_checkpoint(
        checkpoint=checkpoint,
        events=events,
        policy=DeterministicProbePolicy(),
        task_id=TASK_ID,
        run_id=run_id,
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
        context_ids=("foundation_probe_v1",),
        expected_traces=expected_traces,
    )
    report = result.to_report()
    _write_json(output_dir / "replay_report.json", report)
    return report


def _run_fresh_replay(
    *,
    output_dir: Path,
    database_path: Path,
    checkpoint_path: Path,
    trace_path: Path,
    run_id: str,
) -> dict[str, Any]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--mode",
        "replay",
        "--output-dir",
        str(output_dir),
        "--database-path",
        str(database_path),
        "--checkpoint-path",
        str(checkpoint_path),
        "--trace-path",
        str(trace_path),
        "--run-id",
        run_id,
    ]
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"fresh replay failed ({completed.returncode}): "
            f"stdout={completed.stdout!r} stderr={completed.stderr!r}"
        )
    return json.loads((output_dir / "replay_report.json").read_text(encoding="utf-8"))


def run_validation(*, output_dir: Path, run_id: str | None = None) -> dict[str, Any]:
    """Run callable Foundation implementation gates into a caller-supplied directory."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_id = run_id or f"foundation-{uuid.uuid4()}"
    episode_id = "foundation-probe-episode-v1"
    code_path_hash = _code_path_hash()
    contract_hashes = _contract_hashes()
    contract_hash = canonical_hash(contract_hashes)
    policy = DeterministicProbePolicy()
    database_path = output_dir / "foundation.sqlite3"
    checkpoint_path = output_dir / "initial_checkpoint.json"
    trace_path = output_dir / "source_traces.json"

    state = initial_state(episode_id, seed=1701)
    initial_checkpoint = _checkpoint(state, 0, "initial")
    mid_checkpoint: CheckpointRecord | None = None
    sink = CollectingTraceSink()
    source_steps = []
    with SQLiteEventStore(database_path) as store:
        store.write_checkpoint(0, initial_checkpoint)
        for step_id in range(1, 5):
            step = execute_observation(
                state=state,
                observation=_observation(episode_id, step_id),
                policy=policy,
                event_store=store,
                trace_sink=sink,
                expected_sequence=step_id - 1,
                task_id=TASK_ID,
                run_id=run_id,
                code_path_hash=code_path_hash,
                contract_hash=contract_hash,
            )
            source_steps.append(step)
            state = step.state_after
            if step_id == 2:
                mid_checkpoint = _checkpoint(state, 2, "mid")
                store.write_checkpoint(2, mid_checkpoint)
        canonical_trace_rows = store.read_trace_rows(episode_id, 0)
    if mid_checkpoint is None:
        raise RuntimeError("mid-chain checkpoint was not created")
    source_final_state_hash = state.state_hash
    source_proposal_hashes = [canonical_hash(item.proposal) for item in source_steps]
    _write_json(checkpoint_path, initial_checkpoint.to_dict())
    canonical_traces = [item.to_dict() for item in canonical_trace_rows]
    _write_json(trace_path, canonical_traces)

    fresh_reports = [
        _run_fresh_replay(
            output_dir=output_dir / f"fresh_replay_{index}",
            database_path=database_path,
            checkpoint_path=checkpoint_path,
            trace_path=trace_path,
            run_id=f"{run_id}-fresh-{index}",
        )
        for index in (1, 2)
    ]

    with SQLiteEventStore(database_path) as restarted_store:
        latest = restarted_store.read_latest_checkpoint(episode_id)
        if latest is None:
            raise RuntimeError("restart did not recover a checkpoint")
        remaining = restarted_store.read_events(episode_id, latest.last_event_sequence)
        restarted = replay_from_checkpoint(
            checkpoint=latest,
            events=remaining,
            policy=policy,
            task_id=TASK_ID,
            run_id=f"{run_id}-restart",
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
            context_ids=("restart", "mid_checkpoint"),
            expected_traces=canonical_traces[latest.state.step_id :],
        )
        all_events = restarted_store.read_events(episode_id, 0)
        independently_read_traces = restarted_store.read_trace_rows(episode_id, 0)
        independently_read_events = restarted_store.read_events(episode_id, 0)
    event_copy = all_events[0].to_dict()
    event_copy["payload"]["observation"]["payload"]["signal"] = "local-copy-mutation"
    byte_independent_records = (
        all_events[0] is not independently_read_events[0]
        and independently_read_events[0].payload["observation"]["payload"]["signal"]
        != "local-copy-mutation"
    )

    stripped_traces = []
    for row in canonical_traces:
        stripped = dict(row)
        stripped.pop("selected_action_proposal", None)
        stripped.pop("action_candidates", None)
        stripped.pop("trace_hash", None)
        stripped_traces.append(stripped)
    action_removed = replay_from_checkpoint(
        checkpoint=initial_checkpoint,
        events=all_events,
        policy=policy,
        task_id=TASK_ID,
        run_id=f"{run_id}-action-removed",
        code_path_hash=code_path_hash,
        contract_hash=contract_hash,
        context_ids=("stored_action_removal",),
        expected_traces=stripped_traces,
    )

    source_database_hash_before = _sha256_file(database_path)
    tampered_database = output_dir / "tampered_clone.sqlite3"
    shutil.copy2(database_path, tampered_database)
    tamper_detected = False
    connection = sqlite3.connect(str(tampered_database))
    try:
        row = connection.execute(
            "SELECT event_json FROM events WHERE episode_id = ? AND sequence = 2",
            (episode_id,),
        ).fetchone()
        data = json.loads(bytes(row[0]).decode("utf-8"))
        data["payload"]["observation"]["payload"]["signal"] = "tampered"
        connection.execute(
            "UPDATE events SET event_json = ? WHERE episode_id = ? AND sequence = 2",
            (sqlite3.Binary(canonical_json_bytes(data)), episode_id),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(tampered_database) as tampered_store:
            tampered_store.read_events(episode_id, 0)
    except HashMismatchError:
        tamper_detected = True
    source_unchanged = _sha256_file(database_path) == source_database_hash_before

    metadata_event_detected = False
    metadata_event_database = output_dir / "metadata_event_tampered_clone.sqlite3"
    shutil.copy2(database_path, metadata_event_database)
    connection = sqlite3.connect(str(metadata_event_database))
    try:
        connection.execute(
            "UPDATE events SET sequence = 9 WHERE episode_id = ? AND sequence = 2",
            (episode_id,),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(metadata_event_database) as metadata_event_store:
            metadata_event_store.read_events(episode_id, 0)
    except ContractValidationError:
        metadata_event_detected = True

    metadata_checkpoint_detected = False
    metadata_checkpoint_database = output_dir / "metadata_checkpoint_tampered_clone.sqlite3"
    shutil.copy2(database_path, metadata_checkpoint_database)
    connection = sqlite3.connect(str(metadata_checkpoint_database))
    try:
        connection.execute(
            """
            UPDATE checkpoints SET last_event_sequence = 3
            WHERE episode_id = ? AND last_event_sequence = 2
            """,
            (episode_id,),
        )
        connection.commit()
    finally:
        connection.close()
    try:
        with SQLiteEventStore(metadata_checkpoint_database) as metadata_checkpoint_store:
            metadata_checkpoint_store.read_latest_checkpoint(episode_id)
    except ContractValidationError:
        metadata_checkpoint_detected = True
    source_unchanged = (
        source_unchanged
        and _sha256_file(database_path) == source_database_hash_before
    )

    corrupt_state_hash_detected = False
    corrupt_checkpoint = initial_checkpoint.to_dict()
    corrupt_checkpoint["state"]["state_hash"] = "0" * 64
    try:
        CheckpointRecord.from_dict(corrupt_checkpoint)
    except HashMismatchError:
        corrupt_state_hash_detected = True
    corrupt_trace_hash_detected = False
    corrupt_traces = [dict(row) for row in canonical_traces]
    corrupt_traces[0] = dict(corrupt_traces[0])
    corrupt_traces[0]["state_after_hash"] = "0" * 64
    try:
        replay_from_checkpoint(
            checkpoint=initial_checkpoint,
            events=all_events,
            policy=policy,
            task_id=TASK_ID,
            run_id=f"{run_id}-corrupt-trace",
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
            context_ids=("corrupt_trace_positive_control",),
            expected_traces=corrupt_traces,
        )
    except HashMismatchError:
        corrupt_trace_hash_detected = True

    nested_trace_schema_detected = False
    invalid_nested_trace = json.loads(json.dumps(canonical_traces[0]))
    invalid_nested_trace["observation"]["schema_version"] = "ego_k0.observation.future"
    invalid_nested_trace_body = dict(invalid_nested_trace)
    invalid_nested_trace_body.pop("trace_hash")
    invalid_nested_trace["trace_hash"] = canonical_hash(invalid_nested_trace_body)
    try:
        TraceRow.from_dict(invalid_nested_trace)
    except SchemaVersionError:
        nested_trace_schema_detected = True

    freeze_blocked = False
    with SQLiteEventStore(database_path) as frozen_store:
        frozen_store.freeze_writes()
        try:
            frozen_store.append_events(4, (observation_to_event(_observation(episode_id, 5), sequence=5),))
        except WritesFrozenError:
            freeze_blocked = True

    fresh_ok = all(
        report["ok"]
        and report["final_state_hash"] == source_final_state_hash
        and report["proposal_hashes"] == source_proposal_hashes
        for report in fresh_reports
    )
    gate_details = {
        "typed_schema_contracts": _typed_contract_gate(),
        "canonical_fresh_process_stability": _canonical_fresh_process_gate(output_dir),
        "restart_recovery": {
            "ok": restarted.ok
            and restarted.final_state.state_hash == source_final_state_hash,
            "mismatch_count": len(restarted.mismatches),
        },
        "fresh_process_replay_x2": {
            "ok": fresh_ok
            and fresh_reports[0]["final_state_hash"]
            == fresh_reports[1]["final_state_hash"],
            "process_count": len(fresh_reports),
        },
        "mid_chain_checkpoint_resume": {
            "ok": restarted.ok
            and latest.last_event_sequence == 2
            and len(remaining) == 2,
            "checkpoint_sequence": latest.last_event_sequence,
            "remaining_event_count": len(remaining),
        },
        "stored_action_removal_recomputes": {
            "ok": action_removed.ok
            and action_removed.final_state.state_hash == source_final_state_hash
            and [canonical_hash(item.proposal) for item in action_removed.steps]
            == source_proposal_hashes,
            "recomputed_proposal_count": len(action_removed.steps),
        },
        "event_tamper_positive_control": {
            "ok": tamper_detected and source_unchanged,
            "detector_fired": tamper_detected,
            "source_store_unchanged": source_unchanged,
        },
        "sqlite_metadata_tamper_positive_controls": {
            "ok": metadata_event_detected
            and metadata_checkpoint_detected
            and source_unchanged,
            "event_metadata_detector_fired": metadata_event_detected,
            "checkpoint_metadata_detector_fired": metadata_checkpoint_detected,
            "source_store_unchanged": source_unchanged,
        },
        "corrupt_state_trace_hash_positive_controls": {
            "ok": corrupt_state_hash_detected and corrupt_trace_hash_detected,
            "state_hash_detector_fired": corrupt_state_hash_detected,
            "trace_hash_detector_fired": corrupt_trace_hash_detected,
        },
        "nested_trace_schema_positive_control": {
            "ok": nested_trace_schema_detected,
            "detector_fired": nested_trace_schema_detected,
        },
        "freeze_writes_intervention": {
            "ok": freeze_blocked,
            "write_blocked": freeze_blocked,
        },
        "sequence_duplicate_fail_closed": _fail_closed_store_gate(output_dir),
        "package_import_leakage_scan": _import_leakage_gate(),
        "forbidden_input_leakage_positive_controls": _forbidden_input_leakage_gate(),
        "import_without_cli_side_effect_free": _import_side_effect_gate(output_dir),
        "adapter_capability_fail_closed": _adapter_capability_gate(),
        "byte_independent_store_records": {
            "ok": byte_independent_records,
            "separate_record_instances": all_events[0] is not independently_read_events[0],
        },
        "trace_sink_no_same_round_feedback": _trace_sink_feedback_gate(
            output_dir=output_dir,
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        ),
        "canonical_transactional_trace_outbox": {
            "ok": len(canonical_traces) == 4
            and canonical_traces == sink.rows
            and [item.to_dict() for item in independently_read_traces]
            == canonical_traces,
            "canonical_trace_count": len(canonical_traces),
            "delivery_trace_count": len(sink.rows),
            "independent_read_count": len(independently_read_traces),
        },
        "atomic_second_write_rollback": _atomic_second_write_rollback_gate(
            output_dir=output_dir,
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        ),
        "post_commit_trace_delivery_recovery": _post_commit_delivery_recovery_gate(
            output_dir=output_dir,
            code_path_hash=code_path_hash,
            contract_hash=contract_hash,
        ),
    }
    gates = {name: bool(details["ok"]) for name, details in gate_details.items()}
    all_gates_ok = all(gates.values())
    database_hash = _sha256_file(database_path)
    report = {
        "schema_version": "ego_k0.foundation_implementation_validation.v1",
        "producer_function": "scripts.run_ego_k0_foundation_validation.run_validation",
        "input_artifact_hashes": {
            **contract_hashes,
            "initial_checkpoint": canonical_hash(initial_checkpoint),
            "source_event_store": database_hash,
            "source_traces": _sha256_file(trace_path),
            "stored_action_removed_traces": canonical_hash(stripped_traces),
            "fresh_replay_1_report": canonical_hash(fresh_reports[0]),
            "fresh_replay_2_report": canonical_hash(fresh_reports[1]),
            "restart_replay_report": canonical_hash(restarted.to_report()),
            "stored_action_removed_replay_report": canonical_hash(
                action_removed.to_report()
            ),
            "event_tampered_clone": _sha256_file(tampered_database),
            "metadata_event_tampered_clone": _sha256_file(metadata_event_database),
            "metadata_checkpoint_tampered_clone": _sha256_file(
                metadata_checkpoint_database
            ),
            "corrupt_checkpoint_control": canonical_hash(corrupt_checkpoint),
            "corrupt_trace_control": canonical_hash(corrupt_traces),
            "invalid_nested_trace_control": canonical_hash(invalid_nested_trace),
        },
        "task_id": TASK_ID,
        "run_id": run_id,
        "episode_ids": [episode_id],
        "context_ids": ["foundation_probe_v1", "restart", "stored_action_removal"],
        "seed_context": {"seed": 1701, "initial_draw_count": 0},
        "aggregation_rule": "logical AND over independently executed implementation gates",
        "code_path_hash": code_path_hash,
        "contract_hashes": contract_hashes,
        "contract_hash": contract_hash,
        "card_hash": contract_hashes["stage_card"],
        "implementation_base_commit": FOUNDATION_IMPLEMENTATION_COMMIT,
        "correction_card_commit": CORRECTION_CARD_COMMIT,
        "route_scope_repair_commit": ROUTE_SCOPE_REPAIR_COMMIT,
        "parent_commit": IMPLEMENTATION_PARENT,
        "parent_hash": IMPLEMENTATION_PARENT,
        "execution_authority_hash": canonical_hash(
            {
                "implementation_base_commit": FOUNDATION_IMPLEMENTATION_COMMIT,
                "foundation_card_blob": FORMAL_PROVENANCE_PINS["foundation_card"][
                    "blob"
                ],
                "correction_card_commit": CORRECTION_CARD_COMMIT,
                "route_scope_repair_commit": ROUTE_SCOPE_REPAIR_COMMIT,
                "itl_authority_commit": FORMAL_PROVENANCE_PINS["itl"][
                    "authority_commit"
                ],
                "itl_route_blob": FORMAL_PROVENANCE_PINS["itl"]["route_blob"],
                "contract_hash": contract_hash,
                "runtime_authority": "none",
            }
        ),
        "per_gate_outcomes": {
            name: {
                **details,
                "outcome": "pass" if details["ok"] else "fail",
            }
            for name, details in gate_details.items()
        },
        "status": "implementation_validation_ok" if all_gates_ok else "implementation_validation_failed",
        "task_local_implementation_acceptance": all_gates_ok,
        "foundation_task_final_acceptance": "NOT_ADJUDICATED",
        "official_evidence_bank": False,
        "mainline_connected": False,
        "enabled": False,
        "runtime_authority": "none",
        "claim_ceiling": CLAIM_CEILING,
    }
    _write_json(output_dir / "implementation_validation_report.json", report)
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("validate", "replay", "evidence-trial", "evidence-bank"),
        default="validate",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--database-path", type=Path)
    parser.add_argument("--checkpoint-path", type=Path)
    parser.add_argument("--trace-path", type=Path)
    parser.add_argument("--itl-repo", type=Path)
    parser.add_argument("--run-id", default=f"foundation-{uuid.uuid4()}")
    args = parser.parse_args(argv)
    if args.mode == "validate":
        report = run_validation(output_dir=args.output_dir, run_id=args.run_id)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if report["task_local_implementation_acceptance"] else 1
    if args.mode in {"evidence-trial", "evidence-bank"}:
        report = run_evidence_producer(
            output_dir=args.output_dir,
            run_id=args.run_id,
            official=args.mode == "evidence-bank",
            itl_repo=args.itl_repo,
        )
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0 if (
            report["producer_completed"]
            and report["candidate_verdict"] == "foundation_engineering_pass"
        ) else 1
    if args.database_path is None or args.checkpoint_path is None:
        parser.error("replay mode requires --database-path and --checkpoint-path")
    report = run_replay(
        output_dir=args.output_dir,
        database_path=args.database_path,
        checkpoint_path=args.checkpoint_path,
        trace_path=args.trace_path,
        run_id=args.run_id,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
