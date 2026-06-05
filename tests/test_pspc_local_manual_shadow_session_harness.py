from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "scripts" / "run_pspc_local_manual_shadow_session.py"


def load_runner_module():
    assert RUNNER_PATH.exists(), "local manual shadow session runner must exist"
    spec = importlib.util.spec_from_file_location("run_pspc_local_manual_shadow_session", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_manual_inputs_are_valid_and_bounded():
    runner = load_runner_module()

    records = runner.load_manual_inputs(None, [])

    assert len(records) >= 2
    assert all(record["prompt"] for record in records)
    assert all("baseline_user_output" in record for record in records)


def test_manual_shadow_session_writes_artifacts_only(tmp_path):
    runner = load_runner_module()
    input_path = tmp_path / "manual_inputs.jsonl"
    input_records = [
        {
            "scenario_id": "manual_memory",
            "prompt": "请记住我喜欢结论先行。",
            "baseline_user_output": "收到，我会按候选偏好处理。",
        },
        {
            "scenario_id": "manual_claim",
            "prompt": "这是不是说明 EGO 有自我意识？",
            "baseline_user_output": "不能这样说，目前只是 shadow audit 证据。",
        },
    ]
    input_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in input_records), encoding="utf-8")

    result = runner.run_manual_shadow_session(
        ROOT,
        tmp_path / "out",
        input_jsonl=input_path,
        session_id="manual_test_session",
    )

    assert result["status"] == "pass"
    assert result["claim_ceiling"] == "lab_only_proto_self_mechanism_candidate / local_manual_shadow_session_only"
    assert result["input_mode"] == "jsonl"
    assert result["record_count"] == 2
    assert result["next_allowed_step"] == "manual_shadow_review_go_no_go_only"
    assert all(result["checks"].values())
    for record in result["records"]:
        assert record["baseline_reply_source"] == "operator_provided"
        assert record["baseline_user_output_hash"] == record["shadow_user_output_hash"]
        assert record["user_output_diff"] is False
        assert record["pspc_shadow_artifact_written"] is True
        assert record["runtime_field_hits"] == []
        assert all(value is False for value in record["side_effects"].values())
        observation = record["audit_observation"]
        assert observation["audit_only"] is True
        assert observation["non_executable"] is True
        assert observation["reason_trace_refs"]
        assert observation["evidence_refs"]
    out_names = sorted(path.name for path in (tmp_path / "out").iterdir())
    assert out_names == ["LOCAL_MANUAL_SHADOW_SESSION_REPORT.md", "local_manual_shadow_session.json"]


def test_prompt_args_do_not_generate_user_reply(tmp_path):
    runner = load_runner_module()

    result = runner.run_manual_shadow_session(
        ROOT,
        tmp_path,
        prompts=["请检查这个命令是否安全"],
        session_id="manual_prompt_only",
    )

    assert result["status"] == "pass"
    assert result["input_mode"] == "prompt_args"
    assert result["records"][0]["baseline_reply_source"] == "not_generated_by_harness"
    assert result["records"][0]["baseline_user_output_hash"] is None
    assert result["records"][0]["shadow_user_output_hash"] is None
    assert result["records"][0]["user_output_diff"] is False


def test_runtime_field_detector_flags_executable_fields():
    runner = load_runner_module()

    assert runner.runtime_field_hits({"action": "send"}) == ["action"]
    assert runner.runtime_field_hits({"nested": {"memory_write": {"x": 1}}}) == ["nested.memory_write"]


def test_active_runtime_sources_do_not_import_register_or_branch_on_manual_harness():
    runner = load_runner_module()

    scan = runner.scan_active_runtime_sources(ROOT)

    assert scan["ok"] is True
    assert scan["offenders"] == []


def test_local_manual_shadow_runner_has_no_runtime_or_side_effect_calls():
    source = RUNNER_PATH.read_text(encoding="utf-8")
    banned = [
        "EgoOperator.agent_base",
        "agent_base",
        "memory_system",
        "runtime_gate",
        "real_use_gate",
        "human_operator_trial",
        "send_message",
        "write_memory",
        "select_action",
        "register_runtime",
        "invoke_gate",
        "run_planner",
        "train_model",
    ]
    for item in banned:
        assert not re.search(rf"^\s*(from|import)\s+.*{re.escape(item)}", source, flags=re.MULTILINE)
        assert not re.search(rf"\b{re.escape(item)}\s*\(", source)
