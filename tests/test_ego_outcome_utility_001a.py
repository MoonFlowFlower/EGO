from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages" / "ego_outcome_utility" / "src"
sys.path.insert(0, str(SRC))

from ego_outcome_utility import functional_checks, utility  # noqa: E402
from ego_outcome_utility.cli import load_transcript, process_transcript  # noqa: E402

CONTRACT_PATH = (
    ROOT
    / "docs"
    / "codex"
    / "tasks"
    / "ego-engineering-only-outcome-utility-route-replacement-001a"
    / "FUNCTIONAL_CONTRACT.json"
)
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "ego_outcome_utility_001a" / "transcript.json"
RUNNER = ROOT / "scripts" / "run_ego_outcome_utility_001a.py"


def transcript() -> dict:
    return load_transcript(FIXTURE_PATH)


def first_step() -> tuple[dict, dict, dict]:
    data = transcript()
    step = data["steps"][0]
    return utility.new_state(data["model_id"]), step["observation"], step["feedback"]


def test_fixture_matches_frozen_contract() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert transcript() == contract["frozen_fixture"]["transcript_object"]


def test_new_state_is_canonical_and_roundtrips() -> None:
    state = utility.new_state("model.test")
    payload = utility.serialize_state(state)
    assert utility.deserialize_state(payload) == state
    assert not payload.endswith(b"\n")


@pytest.mark.parametrize("model_id", ["", "bad value", "é", "x" * 129])
def test_identifier_validation(model_id: str) -> None:
    with pytest.raises(ValueError, match=r"^EOU_IDENTIFIER:"):
        utility.new_state(model_id)


def test_observation_exact_schema_rejects_extra_key() -> None:
    state, observation, _ = first_step()
    observation = {**observation, "extra": 1}
    with pytest.raises(ValueError, match=r"^EOU_OBSERVATION_SCHEMA:"):
        utility.predict(state, observation)


def test_observation_requires_canonical_action_order() -> None:
    state, observation, _ = first_step()
    observation = deepcopy(observation)
    observation["legal_action_ids"].reverse()
    with pytest.raises(ValueError, match=r"^EOU_OBSERVATION_SCHEMA:"):
        utility.predict(state, observation)


def test_exact_rational_ordering_uses_cross_multiplication() -> None:
    state, observation, feedback = first_step()
    first = utility.run_step(state, observation, feedback)
    second_observation = deepcopy(observation)
    second_observation["observation_id"] = "observation.test.2"
    second_observation["step_id"] = 2
    prediction = utility.predict(first["next_state"], second_observation)
    assert prediction["selected_action_id"] == "action.b"
    assert all(type(score["score_numerator"]) is int for score in prediction["scores"])


def test_targeted_update_is_immutable() -> None:
    state, observation, feedback = first_step()
    before = utility.serialize_state(state)
    result = utility.run_step(state, observation, feedback)
    assert utility.serialize_state(state) == before
    assert result["next_state"]["revision"] == 1
    assert result["trace_record"]["update_delta"]["action_id"] == feedback["action_id"]


def test_duplicate_feedback_fails_closed() -> None:
    state, observation, feedback = first_step()
    result = utility.run_step(state, observation, feedback)
    with pytest.raises(ValueError, match=r"^EOU_DUPLICATE_FEEDBACK:"):
        utility.run_step(result["next_state"], observation, feedback)


def test_feedback_observation_mismatch_fails() -> None:
    state, observation, feedback = first_step()
    feedback = {**feedback, "observation_id": "observation.other"}
    with pytest.raises(ValueError, match=r"^EOU_FEEDBACK_MISMATCH:"):
        utility.run_step(state, observation, feedback)


@pytest.mark.parametrize("outcome", [-1_000_001, 1_000_001, True])
def test_feedback_integer_range(outcome: object) -> None:
    state, observation, feedback = first_step()
    feedback = {**feedback, "outcome_micros": outcome}
    with pytest.raises(ValueError, match=r"^EOU_(OUTCOME_RANGE|INTEGER):"):
        utility.run_step(state, observation, feedback)


def test_feedback_must_target_selected_action() -> None:
    state, observation, feedback = first_step()
    feedback = {**feedback, "action_id": "action.b"}
    with pytest.raises(ValueError, match=r"^EOU_FEEDBACK_ACTION:"):
        utility.run_step(state, observation, feedback)


def test_noncanonical_state_bytes_rejected() -> None:
    payload = utility.serialize_state(utility.new_state("model.test"))
    with pytest.raises(ValueError, match=r"^EOU_STATE_BYTES:"):
        utility.deserialize_state(payload + b" ")


def test_duplicate_state_json_key_rejected() -> None:
    payload = utility.serialize_state(utility.new_state("model.test"))
    duplicate = payload[:-1] + b',"state_hash":"0"}'
    with pytest.raises(ValueError, match=r"^EOU_DUPLICATE_KEY:"):
        utility.deserialize_state(duplicate)


def test_wrong_state_hash_rejected() -> None:
    state = utility.new_state("model.test")
    state["state_hash"] = "0" * 64
    payload = utility._canonical_bytes(state)
    with pytest.raises(ValueError, match=r"^EOU_STATE_HASH:"):
        utility.deserialize_state(payload)


def test_full_replay_recomputes_trace() -> None:
    data = transcript()
    response = process_transcript(data)
    checkpoint = utility.serialize_state(utility.new_state(data["model_id"]))
    replay = utility.replay(checkpoint, data["steps"], response["trace"])
    assert replay["mismatch_count"] == 0
    assert replay["trace"] == response["trace"]


def test_suffix_replay_from_intermediate_checkpoint() -> None:
    data = transcript()
    state = utility.new_state(data["model_id"])
    first = utility.run_step(state, **data["steps"][0])
    rest = process_transcript(data)["trace"][1:]
    replay = utility.replay(
        utility.serialize_state(first["next_state"]), data["steps"][1:], rest
    )
    assert replay["mismatch_count"] == 0
    assert replay["trace"] == rest


def test_tampered_expected_trace_reports_leaf_mismatch() -> None:
    data = transcript()
    response = process_transcript(data)
    expected = deepcopy(response["trace"])
    expected[1]["selected_action_id"] = "action.a"
    replay = utility.replay(
        utility.serialize_state(utility.new_state(data["model_id"])),
        data["steps"],
        expected,
    )
    assert replay["mismatch_count"] == 1
    assert replay["mismatches"][0]["path"] == "/selected_action_id"


def test_zero_baseline_is_independent() -> None:
    _, observation, _ = first_step()
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(utility, "predict", lambda *_: (_ for _ in ()).throw(AssertionError()))
        baseline = functional_checks.zero_utility_predict(observation)
    assert baseline["selected_action_id"] == observation["legal_action_ids"][0]


def test_no_update_ablation_keeps_checkpoint_hash() -> None:
    data = transcript()
    checkpoint = utility.serialize_state(utility.new_state(data["model_id"]))
    result = functional_checks.replay_without_updates(checkpoint, data["steps"])
    assert result["update_invocation_count"] == 0
    assert result["initial_state_hash"] == result["final_state_hash"]
    assert result["selection_sequence"] == ["action.a"] * 3


def test_clean_leakage_scanner() -> None:
    for step in transcript()["steps"]:
        assert functional_checks.scan_observation_mapping(step["observation"]) == []


def test_leakage_positive_control_and_parser_rejection() -> None:
    state, observation, _ = first_step()
    planted = {**observation, "target_outcome_micros": 0}
    assert [item["fragment"] for item in functional_checks.scan_observation_mapping(planted)] == [
        "outcome",
        "target",
    ]
    with pytest.raises(ValueError, match=r"^EOU_OBSERVATION_SCHEMA:"):
        utility.predict(state, planted)


def test_leakage_scanner_traverses_lists_and_escapes_pointer() -> None:
    findings = functional_checks.scan_observation_mapping(
        {"safe": [{"reward/value": 1}]}
    )
    assert findings == [
        {
            "json_pointer": "/safe/0/reward~1value",
            "key": "reward/value",
            "fragment": "reward",
        }
    ]


def test_dynamic_nonfixture_identifiers() -> None:
    assert functional_checks._dynamic_identifier_check("1" * 64)


def test_resolve_verdict_synthetic_success_and_failure() -> None:
    assert functional_checks.resolve_verdict(
        required_check_names=["x"],
        observed_checks={"x": True},
        success_label="S",
        failure_label="F",
    ) == "S"
    assert functional_checks.resolve_verdict(
        required_check_names=["x"],
        observed_checks={"x": False},
        success_label="S",
        failure_label="F",
    ) == "F"


@pytest.mark.parametrize(
    "observed",
    [{}, {"x": True, "y": True}, {"x": 1}, {"x": "yes"}],
)
def test_resolve_verdict_rejects_missing_unknown_and_nonbool(observed: dict) -> None:
    with pytest.raises(ValueError, match=r"^EOU_VERDICT_CHECKS:"):
        functional_checks.resolve_verdict(
            required_check_names=["x"],
            observed_checks=observed,
            success_label="S",
            failure_label="F",
        )


def test_process_response_schema_and_expected_sequence() -> None:
    response = process_transcript(transcript())
    assert list(response) == [
        "schema_version",
        "model_id",
        "selection_sequence",
        "final_state",
        "trace",
        "producer_function",
    ]
    assert response["selection_sequence"] == ["action.a", "action.b", "action.b"]


def test_cli_subprocess_process(tmp_path: Path) -> None:
    output = tmp_path / "response.json"
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "process", "--input", str(FIXTURE_PATH), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""
    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert parsed == process_transcript(transcript())


def test_functional_validation_success_bundle(tmp_path: Path) -> None:
    output = tmp_path / "success"
    response = functional_checks.run_functional_validation(
        CONTRACT_PATH, FIXTURE_PATH, output, "test.validation.success"
    )
    assert response["output_files"] == sorted(path.name for path in output.iterdir())
    assert set(response["output_files"]) == {
        "result.json",
        "trace.jsonl",
        "baseline_comparison.json",
        "ablation_report.json",
        "replay_report.json",
        "leakage_report.json",
        "claim_ceiling.txt",
    }
    result = json.loads((output / "result.json").read_text(encoding="utf-8"))
    assert all(result["payload"]["required_checks"].values())


def test_cli_validate_is_deterministic_for_same_run_id(tmp_path: Path) -> None:
    outputs = [tmp_path / "one", tmp_path / "two"]
    stdout = []
    for output in outputs:
        completed = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "validate",
                "--contract",
                str(CONTRACT_PATH),
                "--fixture",
                str(FIXTURE_PATH),
                "--output-dir",
                str(output),
                "--run-id",
                "test.validation.deterministic",
            ],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0
        assert completed.stderr == b""
        stdout.append(completed.stdout)
    assert stdout[0] == stdout[1]
    assert {p.name: p.read_bytes() for p in outputs[0].iterdir()} == {
        p.name: p.read_bytes() for p in outputs[1].iterdir()
    }


def test_handled_failure_bundle_has_exact_surface(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(functional_checks, "_dynamic_identifier_check", lambda _: False)
    output = tmp_path / "failure"
    with pytest.raises(functional_checks.FunctionalValidationFailure):
        functional_checks.run_functional_validation(
            CONTRACT_PATH, FIXTURE_PATH, output, "test.validation.failure"
        )
    assert sorted(path.name for path in output.iterdir()) == [
        "claim_ceiling.txt",
        "failure_manifest.json",
    ]
    manifest = json.loads((output / "failure_manifest.json").read_text(encoding="utf-8"))
    assert manifest["payload"]["partial_evidence_authoritative"] is False
    assert "result.json" not in {path.name for path in output.iterdir()}


def test_result_postbuild_validation_abort_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(functional_checks, "_validate_final_result_structure", lambda *_: False)
    output = tmp_path / "abort"
    with pytest.raises(functional_checks.ProducerStructureAbort):
        functional_checks.run_functional_validation(
            CONTRACT_PATH, FIXTURE_PATH, output, "test.validation.abort"
        )
    assert not output.exists()
    assert not Path(str(output) + ".staging").exists()


def test_fixture_literals_absent_from_production_sources() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert functional_checks._source_literal_scan(ROOT, contract)


def test_package_import_has_no_file_side_effects(tmp_path: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC)
    completed = subprocess.run(
        [sys.executable, "-c", "import ego_outcome_utility; import ego_outcome_utility.functional_checks"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert list(tmp_path.iterdir()) == []


def test_single_logic_path_definitions_and_spies() -> None:
    assert functional_checks._single_logic_path_check(ROOT, transcript())


def test_no_mainline_runtime_imports() -> None:
    production = [
        ROOT / "packages" / "ego_outcome_utility" / "src" / "ego_outcome_utility" / name
        for name in ("__init__.py", "utility.py", "functional_checks.py", "cli.py")
    ] + [RUNNER]
    forbidden_roots = {"EgoOperator", "EgoCore", "OpenEmotion"}
    for path in production:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        assert imported.isdisjoint(forbidden_roots)
