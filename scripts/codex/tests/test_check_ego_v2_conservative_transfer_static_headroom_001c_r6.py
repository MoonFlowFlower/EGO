from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "codex"
    / "check_ego_v2_conservative_transfer_static_headroom_001c_r6.py"
)
TASK_ID = "EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6"


def _load_module():
    spec = importlib.util.spec_from_file_location("static_headroom_r6", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("could not load static-headroom producer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fixed_public_signatures_and_finite_grammar() -> None:
    module = _load_module()

    signatures = module.fixed_signatures()
    assert np.array_equal(
        module.PROTOTYPES, module.prototype_micro_units_from_frozen_bytes()
    )
    assert signatures["prototype_sha256"] == [
        "22659515e916b3b5ead3390438733bda2e15df9b44b6b0b9afcab30718b0dae9",
        "9799be678e4269454a06e199889f37eee9cc1aec02b810befdef3fcc583b04b8",
        "3d6288b3042ee89950548d7a3ef44d183243feb7af0913ce9a25b9a2b040099f",
        "4df0754afbdd63f7e4865bfd10062c20ec5414e469c6b4f8776cddbd8babd5ff",
        "846bdcd2a0768a906623d807c95580c025a63b99d87b2335d7d097f972f71c16",
    ]
    assert signatures["permutation_indices"] == {
        "identity": 0,
        "swap_0_1": 24,
        "reverse": 119,
    }
    assert len(module.source_vectors()) == 13
    states = module.six_source_states()
    assert states.shape == (18_564, 6)


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [
        (1, 2, 0),
        (3, 2, 2),
        (5, 2, 2),
        (-1, 2, 0),
        (-3, 2, -2),
        (7, 3, 2),
    ],
)
def test_exact_half_even_rounding(
    numerator: int, denominator: int, expected: int
) -> None:
    module = _load_module()
    assert module.round_half_even_scalar(numerator, denominator) == expected
    vector_result = module._round_half_even_ratio(
        np.array([[numerator]], dtype=np.int64),
        np.array([[denominator]], dtype=np.int64),
    )
    assert int(vector_result[0, 0]) == expected


def test_exact_five_percent_quantile_boundary() -> None:
    module = _load_module()

    assert module.weighted_lower_quantile(
        benefits=[-100_000, 0], weights=[1, 19], numerator=1, denominator=20
    ) == -100_000
    assert module.weighted_lower_quantile(
        benefits=[-100_000, 0], weights=[1, 24], numerator=1, denominator=20
    ) == 0
    q05, use_candidate = module._posterior_gate_decisions(
        benefits=np.array([[-100_000, 0], [-100_000, 0]], dtype=np.int64),
        weights=np.array([[1, 19], [1, 24]], dtype=np.int64),
    )
    assert q05.tolist() == [-100_000, 0]
    assert use_candidate.tolist() == [False, True]


def test_outcome_neutral_dispatch_has_reachable_positive_and_priority_branches() -> None:
    module = _load_module()
    negative = {"true_analogy_maximum_total_absolute_error_reduction_micro": 0}
    positive = {
        "true_analogy_maximum_total_absolute_error_reduction_micro": 437_500
    }

    assert module.dispatch_verdict(negative) == (
        "CONSERVATIVE_TRANSFER_NO_LEGAL_HEADROOM"
    )
    assert module.dispatch_verdict(positive) == "STATIC_REFERENCE_HEADROOM_FEASIBLE"
    assert module.dispatch_verdict(
        positive, instrument_invalid=True
    ) == "STATIC_HEADROOM_INSTRUMENT_INVALID"
    assert module.dispatch_verdict(
        positive, private_truth_or_seed_input=True, instrument_invalid=True
    ) == "PRIVATE_TRUTH_OR_SEED_INPUT"


def test_artifact_builder_can_emit_positive_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module()
    primary = module.exhaustive_result()
    primary["maximum_total_absolute_error_reduction_micro"] = 437_500
    primary["maximum_mae_improvement"] = "437500/20000000"
    primary["positive_budget2_case_count"] = 1
    primary["nontrivial_transfer_gate_use_count"] = 1
    primary["true_analogy_maximum_total_absolute_error_reduction_micro"] = 437_500
    primary["true_analogy_maximum_mae_improvement"] = "437500/20000000"
    primary["true_analogy_positive_budget2_case_count"] = 1
    primary["admission_possible"] = True
    crosscheck = module.ordered_pair_symmetry_crosscheck()
    crosscheck["maximum_total_absolute_error_reduction_micro"] = primary[
        "maximum_total_absolute_error_reduction_micro"
    ]
    crosscheck["positive_budget2_case_count"] = 2
    monkeypatch.setattr(module, "exhaustive_result", lambda: primary)
    monkeypatch.setattr(
        module, "ordered_pair_symmetry_crosscheck", lambda: crosscheck
    )

    payloads, _, claim = module._artifact_payloads()
    assert payloads["result.json"]["verdict"] == "STATIC_REFERENCE_HEADROOM_FEASIBLE"
    assert payloads["result.json"]["status"] == (
        "static_feasibility_return_requires_separate_implementation_card"
    )
    assert payloads["result.json"]["agreement"][
        "positive_case_count_symmetry_agrees"
    ] is True
    assert payloads["failure_manifest.json"]["failure_count"] == 0
    assert "feasibility adjudication" in claim


def test_exhaustive_and_ordered_pair_crosscheck_close_the_frozen_gate() -> None:
    module = _load_module()

    primary = module.exhaustive_result()
    crosscheck = module.ordered_pair_symmetry_crosscheck()

    assert primary["covered_target_mapping_count"] == 120
    assert primary["evaluated_prior_target_case_count"] == 1_113_840
    assert primary["positive_budget2_case_count"] == 0
    assert primary["nontrivial_transfer_gate_use_count"] == 0
    assert primary["maximum_total_absolute_error_reduction_micro"] == 0
    assert primary["true_analogy_state_count_per_target"] == 6_188
    assert primary["true_analogy_evaluated_case_count"] == 371_280
    assert (
        primary[
            "true_analogy_full_target_case_count_including_observed_order_symmetry"
        ]
        == 742_560
    )
    assert primary["true_analogy_positive_budget2_case_count"] == 0
    assert (
        primary["true_analogy_maximum_total_absolute_error_reduction_micro"]
        == 0
    )
    assert primary["required_total_absolute_error_reduction_micro"] == 437_500
    assert primary["admission_possible"] is False
    assert crosscheck == {
        "method": "ordered_observed_pair_enumeration",
        "evaluated_prior_target_case_count": 2_227_680,
        "positive_budget2_case_count": 0,
        "maximum_total_absolute_error_reduction_micro": 0,
    }


def test_gate_deletion_is_diagnostic_only_and_exposes_both_benefit_and_harm() -> None:
    module = _load_module()

    ablation = module.ungated_bma_diagnostic()
    assert ablation["verdict_role"] == "diagnostic_only_cannot_rescue"
    assert ablation["positive_case_count"] == 446_982
    assert ablation["maximum_total_absolute_error_reduction_micro"] == 641_974
    assert ablation["minimum_total_absolute_error_reduction_micro"] == -365_433


def test_producer_has_no_semantic_input_or_repository_runtime_import() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__",
        "argparse",
        "decimal",
        "hashlib",
        "itertools",
        "json",
        "pathlib",
        "shutil",
        "sys",
        "tempfile",
        "typing",
        "numpy",
    }
    text = SCRIPT.read_text(encoding="utf-8")
    assert "_token_mapping" not in text
    assert "objects_by_cause" not in text
    parser = _load_module().build_parser()
    option_strings = {
        option
        for action in parser._actions
        for option in action.option_strings
    }
    assert option_strings == {"-h", "--help", "--output-dir", "--replay"}
    parsed_defaults = parser.parse_args([])
    assert parsed_defaults.output_dir == REPO_ROOT / "artifacts" / TASK_ID
    authority_paths = {
        row["path"] for row in _load_module().authority_receipts()
    }
    assert authority_paths == {
        "docs/codex/tasks/EGO-V2-P1-CONSERVATIVE-TRANSFER-BENCHMARK-ADMISSION-001C-R5.md",
        "docs/codex/tasks/ego-v2-p1-conservative-transfer-benchmark-admission-001c-r5/COLLISION_RECORD.md",
        "docs/codex/tasks/ego-v2-p1-conservative-transfer-benchmark-admission-001c-r5/FROZEN_DESIGN.json",
        "docs/codex/tasks/EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6.md",
        "docs/codex/tasks/ego-v2-p1-conservative-transfer-static-headroom-preflight-001c-r6/COLLISION_RECORD.md",
        "scripts/codex/tests/test_check_ego_v2_conservative_transfer_static_headroom_001c_r6.py",
    }
    with pytest.raises(SystemExit):
        parser.parse_args(["--seed", "17"])
    with pytest.raises(TypeError):
        _load_module().write_evidence_bundle(Path("unused"), seed=17)


def _run_producer(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_callable_evidence_bundle_and_fresh_process_replay(tmp_path: Path) -> None:
    module = _load_module()
    first = tmp_path / "first"
    second = tmp_path / "second"

    bundle = module.write_evidence_bundle(first)
    replay_process = _run_producer(
        "--output-dir", str(second), "--replay", str(first)
    )
    assert replay_process.returncode == 0, replay_process.stderr
    replay_report = json.loads((second / "replay_report.json").read_text(encoding="utf-8"))

    expected_names = {
        "result.json",
        "trace.jsonl",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "failure_manifest.json",
        "claim_ceiling.txt",
    }
    assert {path.name for path in first.iterdir()} == expected_names
    assert bundle["result"]["verdict"] == "CONSERVATIVE_TRANSFER_NO_LEGAL_HEADROOM"
    assert bundle["result"]["status"] == "bounded_negative_preimplementation_stop"
    assert replay_report["recomputed_equal"] is True
    assert replay_report["comparison_mode"] == (
        "fresh_process_recompute_then_external_bundle_readback"
    )

    for name in expected_names - {"claim_ceiling.txt", "trace.jsonl"}:
        parsed = json.loads((first / name).read_text(encoding="utf-8"))
        assert parsed["task_id"] == TASK_ID
        assert parsed["producer_function"].startswith(
            "check_ego_v2_conservative_transfer_static_headroom_001c_r6."
        )
        assert parsed["run_id"].startswith("static-headroom-")
        assert len(parsed["code_path_hash"]) == 64
        assert parsed["input_artifacts"]
        assert parsed["aggregation_rule"]
        assert parsed["runtime_receipt"]["numpy_version"] == np.__version__
        assert parsed["runtime_receipt"]["dtype"] == np.dtype(np.int64).str

    canonical = json.dumps(
        bundle["result"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    assert hashlib.sha256(canonical).hexdigest() == bundle["result_sha256"]


def test_replay_tamper_is_comparison_only_and_fails_closed(tmp_path: Path) -> None:
    original = tmp_path / "original"
    replay = tmp_path / "replay"
    first = _run_producer("--output-dir", str(original))
    assert first.returncode == 0, first.stderr
    result_path = original / "result.json"
    tampered = json.loads(result_path.read_text(encoding="utf-8"))
    tampered["verdict"] = "STATIC_REFERENCE_HEADROOM_FEASIBLE"
    tampered["primary_enumeration"][
        "true_analogy_maximum_total_absolute_error_reduction_micro"
    ] = 999_999
    result_path.write_text(
        json.dumps(tampered, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    second = _run_producer(
        "--output-dir", str(replay), "--replay", str(original)
    )
    assert second.returncode != 0
    assert "does not match fresh recomputation" in second.stderr
