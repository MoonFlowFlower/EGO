from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "codex" / "verify_ego_life_core_v0_baseline.py"
MANIFEST = (
    ROOT
    / "artifacts"
    / "EGO-LIFE-CORE-V0-DEVELOPMENT-BASELINE-001A"
    / "core_baseline_manifest.json"
)
BASELINE_COMMIT = "546e3639299d7b11b599df3d00645666a6953bac"
BASELINE_PARENT = "d5d98ac0783a7e67b6d003b460470bdf4350d4bd"
BASELINE_TREE = "fe79061dca2991c822cf2b0b5547a08d9b4682f9"
EXPECTED_FILES = {
    "labs/ego_life_playground_v0/__init__.py": {
        "mode": "100644",
        "blob_oid": "aba2ad3ee2ef6963b74bd538bf985f03e5420110",
        "byte_count": 550,
        "sha256": "117dedb39ab10afda706a32760fee55f4d5010db20dfa9b40b037584af344a82",
    },
    "labs/ego_life_playground_v0/app.py": {
        "mode": "100644",
        "blob_oid": "856b55636df36d5754db5b9ebbc9f263075f3218",
        "byte_count": 13997,
        "sha256": "60ad14bac892fd5fdf694fef8a4674fcbf4cc6fe9e8fcc7ebae791c9cb578fcf",
    },
    "labs/ego_life_playground_v0/engine.py": {
        "mode": "100644",
        "blob_oid": "2b5aa6ac5a38caa0bcb4905826e1e891eeb65915",
        "byte_count": 19165,
        "sha256": "c4d05790fb67752787aa0555f9dc99df71b6401c1c85e699e75c8fa85721cc35",
    },
    "labs/ego_life_playground_v0/store.py": {
        "mode": "100644",
        "blob_oid": "c49a564ea772512e2cb0dc6352ef63ffa95c2a80",
        "byte_count": 11693,
        "sha256": "7966075e8804da28ded96c0a690b673a4880219d97775cfa7b0043beae08dd2c",
    },
    "scripts/run_ego_life_playground_v0.py": {
        "mode": "100644",
        "blob_oid": "dd83f1919d6860d26eb1ce4791c008a6e073b0ac",
        "byte_count": 2431,
        "sha256": "e12e7d2bf69df89c5138ee63ed36ef01698273debe567f7f3cf0ae9cb357590a",
    },
    "tests/test_ego_life_playground_v0.py": {
        "mode": "100644",
        "blob_oid": "e3bc77a3fefda06dfdb7b14236e9c2da42501be6",
        "byte_count": 19079,
        "sha256": "94be0adcfdb6df3c49109d2cb11cf36c40c25aa77299f35bee0db318156f3b44",
    },
}


def load_validator():
    assert SCRIPT.is_file(), f"validator is missing: {SCRIPT}"
    spec = importlib.util.spec_from_file_location("verify_ego_life_core_v0_baseline", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_manifest() -> dict:
    assert MANIFEST.is_file(), f"manifest is missing: {MANIFEST}"
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def error_codes(report: dict) -> set[str]:
    return {str(error["code"]) for error in report["errors"]}


def validate_mutation(mutator, *, head_ref: str = "HEAD") -> dict:
    validator = load_validator()
    manifest = copy.deepcopy(
        validator.build_manifest_from_git_objects(
            repo_root=ROOT,
            baseline_commit=BASELINE_COMMIT,
        )
    )
    mutator(manifest)
    return validator.validate_baseline(
        manifest,
        repo_root=ROOT,
        head_ref=head_ref,
        manifest_bytes=validator.canonical_json_bytes(manifest),
    )


def build_exported_evidence(tmp_path: Path) -> tuple[bytes, Path]:
    from labs.ego_life_playground_v0.app import PlaygroundController
    from labs.ego_life_playground_v0.engine import DEFAULT_TOGGLES
    from labs.ego_life_playground_v0.store import SQLiteEventStore

    database = tmp_path / "core-trigger.sqlite3"
    run_id = "core-v0-baseline-test"
    store = SQLiteEventStore(database)
    try:
        controller = PlaygroundController(
            store,
            run_id=run_id,
            seed=73,
            episode_id="core-v0-baseline-episode",
        )
        result = controller.dispatch("resource", DEFAULT_TOGGLES)
        assert result.receipt.committed is True
    finally:
        store.close()

    restarted_store = SQLiteEventStore(database)
    try:
        restarted = PlaygroundController(restarted_store, run_id=run_id, seed=999)
        assert restarted.recovery_status == "recomputed 1 command(s)"
        output = restarted.export(tmp_path / "core-trigger.jsonl")
        return output.read_bytes(), database
    finally:
        restarted_store.close()


def test_committed_git_objects_recompute_to_a_passing_report() -> None:
    validator = load_validator()
    raw_manifest = MANIFEST.read_bytes()
    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        head_ref="HEAD",
        manifest_bytes=raw_manifest,
    )

    assert report["computed_verdict"] == "PASS"
    assert report["baseline_commit"] == BASELINE_COMMIT
    assert report["baseline_parent"] == BASELINE_PARENT
    assert report["baseline_tree"] == BASELINE_TREE
    assert report["exact_change_set_verified"] is True
    assert report["head_descends_from_baseline"] is True
    assert report["head_path_parity"] is True
    assert report["errors"] == []
    assert report["provenance"]["producer_function"].endswith("validate_baseline")
    assert report["provenance"]["producer_code_path_hash"]
    assert report["provenance"]["manifest_sha256"]
    assert report["provenance"]["run_id"]


def test_manifest_is_the_exact_git_computed_pin_set() -> None:
    validator = load_validator()
    manifest = load_manifest()
    rebuilt = validator.build_manifest_from_git_objects(
        repo_root=ROOT,
        baseline_commit=BASELINE_COMMIT,
    )

    assert rebuilt == manifest
    assert manifest["source"]["commit_oid"] == BASELINE_COMMIT
    assert manifest["source"]["parent_oid"] == BASELINE_PARENT
    assert manifest["source"]["tree_oid"] == BASELINE_TREE
    assert {
        entry["path"]: {
            "mode": entry["mode"],
            "blob_oid": entry["blob_oid"],
            "byte_count": entry["byte_count"],
            "sha256": entry["sha256"],
        }
        for entry in manifest["source"]["files"]
    } == EXPECTED_FILES


@pytest.mark.parametrize(
    ("field", "replacement", "expected_error"),
    [
        ("commit_oid", "0" * 40, "baseline_commit_pin_mismatch"),
        ("parent_oid", "0" * 40, "baseline_parent_oid_mismatch"),
        ("tree_oid", "0" * 40, "baseline_tree_oid_mismatch"),
    ],
)
def test_commit_parent_and_tree_pin_mutations_fail_closed(
    field: str,
    replacement: str,
    expected_error: str,
) -> None:
    report = validate_mutation(
        lambda manifest: manifest["source"].__setitem__(field, replacement)
    )

    assert report["computed_verdict"] == "FAIL"
    assert expected_error in error_codes(report)


@pytest.mark.parametrize(
    ("field", "replacement", "expected_error"),
    [
        ("mode", "100755", "file_mode_mismatch"),
        ("blob_oid", "0" * 40, "file_blob_oid_mismatch"),
        ("byte_count", 1, "file_byte_count_mismatch"),
        ("sha256", "0" * 64, "file_sha256_mismatch"),
    ],
)
def test_blob_mode_size_and_payload_mutations_fail_closed(
    field: str,
    replacement: str | int,
    expected_error: str,
) -> None:
    report = validate_mutation(
        lambda manifest: manifest["source"]["files"][0].__setitem__(field, replacement)
    )

    assert report["computed_verdict"] == "FAIL"
    assert any(code.startswith(expected_error + ":") for code in error_codes(report))


def test_path_set_mutation_fails_closed() -> None:
    report = validate_mutation(
        lambda manifest: manifest["source"]["files"].pop()
    )

    assert report["computed_verdict"] == "FAIL"
    assert "baseline_path_set_mismatch" in error_codes(report)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("runtime_mainline_connected", True),
        ("runtime_authority", "ego_life_playground_v0"),
        ("default_enabled", True),
        ("science_weight", 1),
    ],
)
def test_runtime_and_science_boundary_mutations_fail_closed(
    field: str,
    replacement: object,
) -> None:
    report = validate_mutation(
        lambda manifest: manifest["development_boundary"].__setitem__(field, replacement)
    )

    assert report["computed_verdict"] == "FAIL"
    assert f"development_boundary_mismatch:{field}" in error_codes(report)


def test_boundary_describes_only_the_local_candidate_and_runtime_firewall() -> None:
    validator = load_validator()
    manifest = validator.build_manifest_from_git_objects(
        repo_root=ROOT,
        baseline_commit=BASELINE_COMMIT,
    )
    boundary = manifest["development_boundary"]

    assert "product_development_core_lineage" not in boundary
    assert boundary["product_development_core"] == "ego_life_playground_v0"
    assert boundary["runtime_mainline_connected"] is False
    assert "product_development_mainline" not in boundary
    assert "separate route synchronization" in manifest["claim_ceiling"]


def test_injected_product_lineage_authority_fails_closed() -> None:
    report = validate_mutation(
        lambda manifest: manifest["development_boundary"].__setitem__(
            "product_development_core_lineage",
            "SOLE_VISIBLE_LIFE_PRODUCT_DEVELOPMENT_LINEAGE",
        )
    )

    assert report["computed_verdict"] == "FAIL"
    assert "development_boundary_key_set_mismatch" in error_codes(report)


def test_non_descendant_head_fails_closed() -> None:
    report = validate_mutation(lambda manifest: None, head_ref=BASELINE_PARENT)

    assert report["computed_verdict"] == "FAIL"
    assert report["head_descends_from_baseline"] is False
    assert "head_not_descendant_of_baseline" in error_codes(report)


def test_descendant_live_path_drift_is_informational_not_a_failure(tmp_path: Path) -> None:
    descendant_repo = tmp_path / "descendant-repo"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-checkout", "--shared", str(ROOT), str(descendant_repo)],
        check=True,
    )
    subprocess.run(
        ["git", "read-tree", BASELINE_COMMIT],
        cwd=descendant_repo,
        check=True,
    )
    blob = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=descendant_repo,
        input=b"# simulated descendant live-path drift\n",
        capture_output=True,
        check=True,
    ).stdout.decode("ascii").strip()
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            f"100644,{blob},labs/ego_life_playground_v0/engine.py",
        ],
        cwd=descendant_repo,
        check=True,
    )
    tree = subprocess.run(
        ["git", "write-tree"],
        cwd=descendant_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "baseline-test",
        "GIT_AUTHOR_EMAIL": "baseline-test@example.invalid",
        "GIT_COMMITTER_NAME": "baseline-test",
        "GIT_COMMITTER_EMAIL": "baseline-test@example.invalid",
    }
    descendant = subprocess.run(
        ["git", "commit-tree", tree, "-p", BASELINE_COMMIT],
        cwd=descendant_repo,
        input="simulated descendant\n",
        capture_output=True,
        text=True,
        check=True,
        env=env,
    ).stdout.strip()
    validator = load_validator()
    raw_manifest = MANIFEST.read_bytes()

    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=descendant_repo,
        head_ref=descendant,
        manifest_bytes=raw_manifest,
    )

    assert report["computed_verdict"] == "PASS"
    assert report["head_descends_from_baseline"] is True
    assert report["head_path_parity"] is False
    assert report["errors"] == []


def test_sqlite_artifact_is_authoritative_and_export_is_byte_identical(tmp_path: Path) -> None:
    validator = load_validator()
    raw_manifest = MANIFEST.read_bytes()
    trace_bytes, database = build_exported_evidence(tmp_path)
    database_bytes = database.read_bytes()

    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        head_ref="HEAD",
        manifest_bytes=raw_manifest,
        trace_bytes=trace_bytes,
        trace_path=tmp_path / "core-trigger.jsonl",
        database_bytes=database_bytes,
        database_path=database,
        require_trace=True,
        require_database=True,
    )

    assert report["computed_verdict"] == "PASS"
    assert report["trace_validation_status"] == "PASS"
    assert report["trace_replay_status"] == "PASS"
    assert report["direct_engine_replay_status"] == "PASS"
    assert report["database_provenance_status"] == "PASS"
    assert report["sqlite_recovery_status"] == "PASS"
    assert report["sqlite_export_status"] == "PASS"
    assert report["serialized_initial_state_status"] == "PASS"
    assert report["trace_replay_input"] == (
        "serialized_initial_state_and_typed_commands_from_sqlite_artifact"
    )
    assert report["database_path"] == str(database.resolve())
    assert report["database_payload_sha256"] == hashlib.sha256(database_bytes).hexdigest()
    assert report["trace_record_count"] == 1
    assert report["trace_payload_sha256"]
    assert report["trace_header"]["producer_function"].endswith(
        "SQLiteEventStore.export_run"
    )
    assert report["trace_header"]["run_id"] == "core-v0-baseline-test"
    assert report["trace_header"]["seed"] == 73
    assert report["trace_header"]["episode_id"] == "core-v0-baseline-episode"


def test_rehashed_trace_behavior_tamper_fails_recomputation(tmp_path: Path) -> None:
    validator = load_validator()
    trace_bytes, database = build_exported_evidence(tmp_path)
    records = [
        json.loads(line)
        for line in trace_bytes.decode("utf-8").splitlines()
    ]
    records[1]["trace"]["selected_action"] = "withdraw"
    records[1]["trace"]["trace_hash"] = validator.canonical_hash(
        {
            key: value
            for key, value in records[1]["trace"].items()
            if key != "trace_hash"
        }
    )
    tampered = ("\n".join(validator.canonical_json(record) for record in records) + "\n").encode(
        "utf-8"
    )
    raw_manifest = MANIFEST.read_bytes()

    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        manifest_bytes=raw_manifest,
        trace_bytes=tampered,
        trace_path=tmp_path / "tampered.jsonl",
        database_bytes=database.read_bytes(),
        database_path=database,
        require_trace=True,
        require_database=True,
    )

    assert report["computed_verdict"] == "FAIL"
    assert report["trace_replay_status"] == "FAIL"
    assert report["sqlite_export_status"] == "FAIL"
    assert "sqlite_export_trace_mismatch" in error_codes(report)
    assert "trace_replay_mismatch:1" in error_codes(report)


@pytest.mark.parametrize(
    ("field", "replacement", "expected_error"),
    [
        ("producer_function", "handwritten", "trace_header_producer_mismatch"),
        ("run_id", "", "trace_header_run_id_invalid"),
        ("seed", "73", "trace_header_seed_invalid"),
        ("episode_id", "", "trace_header_episode_id_invalid"),
        ("aggregation_rule", "stored_hash_only", "trace_header_aggregation_rule_mismatch"),
        ("code_path_hash", "0" * 64, "trace_header_code_path_hash_mismatch"),
        ("command_count", 2, "trace_header_command_count_mismatch"),
        (
            "input_artifacts",
            ["C:/substituted.sqlite3"],
            "trace_header_database_provenance_mismatch",
        ),
    ],
)
def test_trace_header_provenance_mutations_fail_closed(
    tmp_path: Path,
    field: str,
    replacement: object,
    expected_error: str,
) -> None:
    validator = load_validator()
    trace_bytes, database = build_exported_evidence(tmp_path)
    records = [
        json.loads(line)
        for line in trace_bytes.decode("utf-8").splitlines()
    ]
    records[0][field] = replacement
    tampered = ("\n".join(validator.canonical_json(record) for record in records) + "\n").encode(
        "utf-8"
    )
    raw_manifest = MANIFEST.read_bytes()

    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        manifest_bytes=raw_manifest,
        trace_bytes=tampered,
        trace_path=tmp_path / "tampered-header.jsonl",
        database_bytes=database.read_bytes(),
        database_path=database,
        require_trace=True,
        require_database=True,
    )

    assert report["computed_verdict"] == "FAIL"
    assert expected_error in error_codes(report)


def test_missing_database_fails_closed(tmp_path: Path) -> None:
    validator = load_validator()
    trace_bytes, _ = build_exported_evidence(tmp_path)
    raw_manifest = MANIFEST.read_bytes()

    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        manifest_bytes=raw_manifest,
        trace_bytes=trace_bytes,
        trace_path=tmp_path / "core-trigger.jsonl",
        require_trace=True,
        require_database=True,
    )

    assert report["computed_verdict"] == "FAIL"
    assert report["sqlite_recovery_status"] == "FAIL"
    assert report["sqlite_export_status"] == "FAIL"
    assert "database_required_missing" in error_codes(report)


def test_tampered_database_fails_sqlite_recovery(tmp_path: Path) -> None:
    validator = load_validator()
    trace_bytes, database = build_exported_evidence(tmp_path)
    database_bytes = database.read_bytes()
    tampered_database = bytes([database_bytes[0] ^ 0xFF]) + database_bytes[1:]
    raw_manifest = MANIFEST.read_bytes()

    report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        manifest_bytes=raw_manifest,
        trace_bytes=trace_bytes,
        trace_path=tmp_path / "core-trigger.jsonl",
        database_bytes=tampered_database,
        database_path=database,
        require_trace=True,
        require_database=True,
    )

    assert report["computed_verdict"] == "FAIL"
    assert report["sqlite_recovery_status"] == "FAIL"
    assert report["sqlite_export_status"] == "FAIL"
    assert "sqlite_recovery_failed" in error_codes(report)


def test_unrelated_database_and_provenance_path_substitution_fail(tmp_path: Path) -> None:
    from labs.ego_life_playground_v0.store import SQLiteEventStore

    validator = load_validator()
    trace_bytes, database = build_exported_evidence(tmp_path)
    unrelated = tmp_path / "unrelated.sqlite3"
    store = SQLiteEventStore(unrelated)
    store.close()
    raw_manifest = MANIFEST.read_bytes()

    unrelated_report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        manifest_bytes=raw_manifest,
        trace_bytes=trace_bytes,
        trace_path=tmp_path / "core-trigger.jsonl",
        database_bytes=unrelated.read_bytes(),
        database_path=unrelated,
        require_trace=True,
        require_database=True,
    )
    substituted_path_report = validator.validate_baseline(
        json.loads(raw_manifest),
        repo_root=ROOT,
        manifest_bytes=raw_manifest,
        trace_bytes=trace_bytes,
        trace_path=tmp_path / "core-trigger.jsonl",
        database_bytes=database.read_bytes(),
        database_path=tmp_path / "substituted.sqlite3",
        require_trace=True,
        require_database=True,
    )

    assert unrelated_report["computed_verdict"] == "FAIL"
    assert "database_run_inventory_mismatch" in error_codes(unrelated_report)
    assert substituted_path_report["computed_verdict"] == "FAIL"
    assert "trace_header_database_provenance_mismatch" in error_codes(
        substituted_path_report
    )


def test_cli_returns_computed_json_and_rejects_a_mutated_manifest(tmp_path: Path) -> None:
    _, database = build_exported_evidence(tmp_path)
    passing = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(ROOT),
            "--manifest",
            str(MANIFEST),
            "--database",
            str(database),
            "--manifest-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert passing.returncode == 0, passing.stderr
    assert json.loads(passing.stdout)["computed_verdict"] == "PASS"

    mutated = load_manifest()
    mutated["source"]["files"][0]["sha256"] = "f" * 64
    mutated_path = tmp_path / "mutated.json"
    mutated_path.write_text(json.dumps(mutated), encoding="utf-8")
    failing = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(ROOT),
            "--manifest",
            str(mutated_path),
            "--database",
            str(database),
            "--manifest-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert failing.returncode == 1
    assert json.loads(failing.stdout)["computed_verdict"] == "FAIL"


def test_cli_requires_an_explicit_database_argument() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--repo-root",
            str(ROOT),
            "--manifest",
            str(MANIFEST),
            "--manifest-only",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "--database" in result.stderr
