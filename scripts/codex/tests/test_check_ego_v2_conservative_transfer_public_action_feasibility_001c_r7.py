from __future__ import annotations

import ast
from hashlib import sha256
import importlib.util
from itertools import combinations, permutations
import json
from pathlib import Path
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "check_ego_v2_conservative_transfer_public_action_feasibility_001c_r7.py"
)
TASK_ID = (
    "EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("public_action_r7", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load public-action producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_authority_and_prototype_bytes_are_derived() -> None:
    module = _load_module()

    receipts = module.authority_receipts()
    assert [row["role"] for row in receipts[:4]] == [
        "r7_parent_card",
        "r7_parent_collision",
        "r7_parent_design",
        "r7_implementation_card",
    ]
    signatures = module.fixed_signatures()
    assert signatures["prototype_sha256"] == [
        "22659515e916b3b5ead3390438733bda2e15df9b44b6b0b9afcab30718b0dae9",
        "9799be678e4269454a06e199889f37eee9cc1aec02b810befdef3fcc583b04b8",
        "3d6288b3042ee89950548d7a3ef44d183243feb7af0913ce9a25b9a2b040099f",
        "4df0754afbdd63f7e4865bfd10062c20ec5414e469c6b4f8776cddbd8babd5ff",
        "846bdcd2a0768a906623d807c95580c025a63b99d87b2335d7d097f972f71c16",
    ]
    assert signatures["prototype_micro_units"] == [
        [0, -20_000, 0, 160_000],
        [0, -180_000, 0, 40_000],
        [0, 0, 160_000, 20_000],
        [0, 120_000, 0, 0],
        [280_000, 0, 0, 0],
    ]
    assert signatures["prototype_canonical_json"] == [
        raw.decode("ascii") for raw in module.PROTOTYPE_BYTES
    ]
    assert [sha256(raw).hexdigest() for raw in module.PROTOTYPE_BYTES] == (
        signatures["prototype_sha256"]
    )


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [(1, 2, 0), (3, 2, 2), (5, 2, 2), (-1, 2, 0), (-3, 2, -2)],
)
def test_exact_half_even_integer_rounding(
    numerator: int, denominator: int, expected: int
) -> None:
    module = _load_module()
    assert module.round_half_even(numerator, denominator) == expected


def test_public_median_beats_or_ties_mean_on_every_geometry() -> None:
    module = _load_module()

    receipts = module.geometry_receipts()
    assert len(receipts) == 10
    assert all(row["completion_count"] == 6 for row in receipts)
    assert all(row["median_is_unique"] for row in receipts)
    assert all(row["median_is_minimax"] for row in receipts)
    assert all(row["mean_aggregate_excess_error_micro"] >= 0 for row in receipts)
    assert any(row["mean_aggregate_excess_error_micro"] > 0 for row in receipts)


def test_six_completion_loss_sum_identity_uses_multiplicity_two() -> None:
    module = _load_module()

    remaining = (0, 2, 4)
    completions = tuple(permutations(remaining))
    action = (
        (13_579, -24_680, 91_357, -42),
        (-7, 120_001, 8_888, 90_000),
        (300_000, -200_000, 3, 4),
    )
    explicit = sum(module.completion_loss(action, truth) for truth in completions)
    factored = module.factored_loss_sum(action, remaining)
    assert explicit == factored
    assert module.completion_multiplicity(remaining) == (
        (2, 2, 2),
        (2, 2, 2),
        (2, 2, 2),
    )


def test_unique_scalar_median_certificate_has_strict_equality_condition() -> None:
    module = _load_module()

    for remaining in combinations(range(5), 3):
        for component in range(4):
            values = tuple(module.PROTOTYPES[index][component] for index in remaining)
            certificate = module.unique_scalar_median_certificate(values)
            assert certificate["unique"] is True
            median = certificate["median"]
            base = sum(abs(median - value) for value in values)
            for candidate in range(min(values) - 2, max(values) + 3):
                observed = sum(abs(candidate - value) for value in values)
                assert observed >= base
                assert (observed == base) is (candidate == median)


def test_all_masks_and_membership_sizes_close_strict_and_bounded_contracts() -> None:
    module = _load_module()

    summary = module.formal_feasibility_summary()
    assert summary["loss_geometry_count"] == 10
    assert summary["nonempty_mask_count_per_geometry"] == 63
    assert summary["evaluated_geometry_mask_count"] == 630
    assert summary["strict_feasible_mask_count"] == 0
    assert summary["bounded_feasible_mask_count"] == 0
    assert summary["inconclusive_mask_count"] == 0
    assert summary["membership_size_case_counts"] == {
        "1": 60,
        "2": 150,
        "3": 200,
        "4": 150,
        "5": 60,
        "6": 10,
    }
    assert summary["bounds_by_membership_size"]["1"] == {
        "bounded_constraint_sum_upper_micro": 0,
        "bounded_infeasibility_reason": "unique_equality_forces_A_equals_B_and_zero_true_gain",
        "strict_constraint_sum_upper_micro": -437_500,
        "strict_infeasibility_reason": "constraint_sum_below_public_L1_lower_bound",
    }
    assert summary["bounds_by_membership_size"]["2"][
        "bounded_constraint_sum_upper_micro"
    ] == -525_000


def test_nondecisive_loss_sum_bound_is_inconclusive_not_infeasible() -> None:
    module = _load_module()

    receipt = module._bound_receipt(
        membership_size=1,
        true_gain_micro=100,
        nonmember_margin_micro=100,
    )
    assert receipt["constraint_sum_upper_micro"] == 400
    assert receipt["status"] == "inconclusive"
    assert module.dispatch_verdict(
        {
            "strict_feasible_mask_count": 0,
            "bounded_feasible_mask_count": 0,
            "inconclusive_mask_count": 1,
        }
    ) == "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"


def test_zero_gain_public_median_positive_control_uses_same_loss_path() -> None:
    module = _load_module()

    control = module.zero_gain_positive_control(remaining=(0, 1, 2), mask=1)
    assert control["action_equals_public_median"] is True
    assert control["truth_benefits_micro"] == [0, 0, 0, 0, 0, 0]
    assert control["strict_feasible"] is True
    assert module.dispatch_verdict(control["dispatch_summary"]) == (
        "R7_STATIC_REFERENCE_FEASIBLE"
    )


def test_outcome_neutral_dispatch_priority_and_all_branches() -> None:
    module = _load_module()

    absent = {"strict_feasible_mask_count": 0, "bounded_feasible_mask_count": 0}
    bounded = {"strict_feasible_mask_count": 0, "bounded_feasible_mask_count": 1}
    strict = {"strict_feasible_mask_count": 1, "bounded_feasible_mask_count": 1}
    assert module.dispatch_verdict(absent) == (
        "PUBLIC_INFORMATION_TWO_SIDED_HEADROOM_ABSENT"
    )
    assert module.dispatch_verdict(bounded) == "BOUNDED_REGRET_ONLY"
    assert module.dispatch_verdict(strict) == "R7_STATIC_REFERENCE_FEASIBLE"
    assert module.dispatch_verdict(strict, instrument_invalid=True) == (
        "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    )
    assert module.dispatch_verdict(
        strict, instrument_invalid=True, private_truth_or_seed_input=True
    ) == "PRIVATE_TRUTH_OR_SEED_INPUT"
    assert module.dispatch_verdict({}) == (
        "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    )


def test_relabel_and_quotient_receipts_are_invariant() -> None:
    module = _load_module()

    receipt = module.relabel_invariance_receipt()
    assert receipt["observed_order_invariant"] is True
    assert receipt["unobserved_token_relabel_invariant"] is True
    assert receipt["prototype_relabel_invariant"] is True
    assert receipt["geometry_quotient_complete"] is True
    assert receipt["universal_bank_and_action_quantifier"] == (
        "for_every_B_H2_M_of_B_H2_and_A_of_B_H2"
    )


def test_universal_identity_and_randomized_extension_enter_proof_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    receipts = module.geometry_receipts()
    assert all(row["universal_loss_sum_identity_valid"] for row in receipts)
    randomized = module.randomized_extension_receipt(receipts)
    assert randomized["deterministic_lower_bound_valid"] is True
    assert randomized["unique_equality_condition_valid"] is True
    assert randomized["expectation_linearity_valid"] is True
    assert randomized["randomized_extension_valid"] is True

    receipts[0]["universal_loss_sum_identity_valid"] = False
    monkeypatch.setattr(module, "geometry_receipts", lambda: receipts)
    payloads, _, _ = module._artifact_payloads()
    assert payloads["result.json"]["verdict"] == (
        "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    )


def test_parser_has_only_output_and_replay_paths_and_rejects_unknown() -> None:
    module = _load_module()

    parser = module.build_parser()
    dests = {action.dest for action in parser._actions}
    assert dests == {"help", "output_dir", "replay_expected_dir"}
    with pytest.raises(SystemExit):
        parser.parse_args(["--seed", "1"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--world", "60"])


def test_producer_imports_only_standard_library_and_no_runtime_surface() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported <= {
        "__future__",
        "argparse",
        "collections",
        "decimal",
        "hashlib",
        "itertools",
        "json",
        "math",
        "pathlib",
        "platform",
        "subprocess",
        "sys",
        "typing",
    }
    forbidden_names = {
        "_token_mapping",
        "objects_by_cause",
        "transition_world",
        "compute_step",
        "plan_action",
    }
    names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    assert names.isdisjoint(forbidden_names)


def test_provenance_classifier_rejects_dirty_source_and_extra_diff() -> None:
    module = _load_module()
    allowed = {
        module.IMPLEMENTATION_CARD,
        module.PRODUCER_RELATIVE_PATH,
        module.TEST_RELATIVE_PATH,
    }
    clean = module.evaluate_provenance_state(
        phase_a_is_ancestor=True,
        cumulative_diff_paths=allowed,
        dirty_paths=set(),
        sources_tracked_and_match_head=True,
        replay_expected_artifact_paths=set(),
    )
    assert clean["formal_eligible"] is True
    dirty = module.evaluate_provenance_state(
        phase_a_is_ancestor=True,
        cumulative_diff_paths=allowed,
        dirty_paths={module.PRODUCER_RELATIVE_PATH},
        sources_tracked_and_match_head=False,
        replay_expected_artifact_paths=set(),
    )
    assert dirty["formal_eligible"] is False
    assert "source_bytes_not_tracked_clean_HEAD" in dirty["failure_codes"]
    extra = module.evaluate_provenance_state(
        phase_a_is_ancestor=True,
        cumulative_diff_paths=allowed | {"labs/unauthorized.py"},
        dirty_paths=set(),
        sources_tracked_and_match_head=True,
        replay_expected_artifact_paths=set(),
    )
    assert extra["formal_eligible"] is False
    assert "cumulative_diff_outside_allowlist" in extra["failure_codes"]


def test_git_provenance_runtime_is_bound_and_wrong_root_fails_closed() -> None:
    module = _load_module()
    receipt = module.git_runtime_receipt()
    assert receipt["role"] == "external_provenance_tool_only"
    assert receipt["version"].startswith("git version ")
    assert Path(receipt["repository_root"]).resolve() == REPO_ROOT.resolve()
    with pytest.raises(RuntimeError, match="repository root mismatch"):
        module.validate_git_runtime(
            version="git version 2.test",
            repository_root=REPO_ROOT.parent,
        )
    with pytest.raises(RuntimeError, match="version receipt invalid"):
        module.validate_git_runtime(
            version="not-git",
            repository_root=REPO_ROOT,
        )


def test_evidence_bundle_and_fresh_process_replay_are_exact(tmp_path: Path) -> None:
    module = _load_module()
    canonical = tmp_path / "canonical"
    replayed = tmp_path / "replayed"

    first = module.write_evidence_bundle(canonical)
    assert first["result"]["verdict"] == (
        "PUBLIC_INFORMATION_TWO_SIDED_HEADROOM_ABSENT"
    )
    expected_files = {
        "result.json",
        "trace.jsonl",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "failure_manifest.json",
        "claim_ceiling.txt",
    }
    assert {path.name for path in canonical.iterdir()} == expected_files

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--output-dir",
            str(replayed),
            "--replay-expected-dir",
            str(canonical),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    replay = json.loads((replayed / "replay_report.json").read_text("utf-8"))
    assert replay["comparison_mode"] == (
        "fresh_process_recompute_then_external_bundle_readback"
    )
    assert replay["recomputed_equal"] is True
    assert replay["stored_verdict_action_or_witness_used_as_input"] is False
    for name in module.CORE_FILE_NAMES:
        assert (replayed / name).read_bytes() == (canonical / name).read_bytes()


def test_fresh_process_replay_fails_closed_on_tampered_stored_result(
    tmp_path: Path,
) -> None:
    module = _load_module()
    canonical = tmp_path / "canonical"
    replayed = tmp_path / "replayed"
    module.write_evidence_bundle(canonical)

    stored = json.loads((canonical / "result.json").read_text("utf-8"))
    stored["verdict"] = "R7_STATIC_REFERENCE_FEASIBLE"
    stored["formal_feasibility"]["strict_feasible_mask_count"] = 999
    (canonical / "result.json").write_text(
        json.dumps(stored, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--output-dir",
            str(replayed),
            "--replay-expected-dir",
            str(canonical),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "does not match expected core bundle" in completed.stderr
    assert not replayed.exists() or not any(replayed.iterdir())


def test_writer_rejects_stale_output_and_extra_expected_file(tmp_path: Path) -> None:
    module = _load_module()
    stale = tmp_path / "stale"
    stale.mkdir()
    (stale / "stale.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="output directory must be empty"):
        module.write_evidence_bundle(stale)

    canonical = tmp_path / "canonical"
    module.write_evidence_bundle(canonical)
    (canonical / "unexpected.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(RuntimeError, match="expected bundle file set drift"):
        module.write_evidence_bundle(
            tmp_path / "replayed", replay_expected_dir=canonical
        )


def test_formal_result_has_bounded_claim_and_computed_failure_manifest(
    tmp_path: Path,
) -> None:
    module = _load_module()
    output = tmp_path / "bundle"
    bundle = module.write_evidence_bundle(output)
    result = bundle["result"]
    failure = json.loads((output / "failure_manifest.json").read_text("utf-8"))

    assert result["formal_feasibility"]["strict_feasible_mask_count"] == 0
    assert result["formal_feasibility"]["bounded_feasible_mask_count"] == 0
    assert result["same_model_lineage"] is True
    assert result["external_independent_audit"] is False
    assert failure["failure_count"] == 1
    assert failure["failures"][0]["code"] == (
        "UNIVERSAL_MEMBER_NONMEMBER_ACTION_INTERSECTION_EMPTY"
    )
    claim = (output / "claim_ceiling.txt").read_text("utf-8")
    assert "does not adjudicate R5 D2/D3/D4" in claim
    assert "AGI" in claim and "electronic life" in claim


def test_artifact_dispatch_fails_closed_on_broken_geometry_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    receipts = module.geometry_receipts()
    receipts[0]["loss_sum_identity_holds"] = False
    monkeypatch.setattr(module, "geometry_receipts", lambda: receipts)

    payloads, _, _ = module._artifact_payloads()
    assert payloads["result.json"]["verdict"] == (
        "PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID"
    )
    assert payloads["failure_manifest.json"]["failures"][0]["code"] == (
        "PUBLIC_ACTION_PROOF_CERTIFICATE_INVALID"
    )
