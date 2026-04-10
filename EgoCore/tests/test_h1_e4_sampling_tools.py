from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "scripts" / "codex" / "h1_e4_sampling_common.py"
CLEAN_BIND = ROOT / "scripts" / "codex" / "run_h1_clean_bind_cycle.py"


def _load_module(path: Path, name: str):
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _make_sample(
    real_dir: Path,
    sample_id: str,
    *,
    timestamp: str,
    text: str,
    shadow_h1: dict | None,
    complete: bool = True,
) -> None:
    sample_dir = real_dir / sample_id
    sample_dir.mkdir(parents=True, exist_ok=True)
    raw_update = {"update_id": 1, "message": {"text": text}}
    normalized_event = {
        "event_id": f"evt_{sample_id}",
        "conversation_context": {
            "session_id": "telegram:dm:test",
            "thread_id": "telegram:dm:test",
            "turn_id": "turn_001",
        },
    }
    result_payload = {
        "schema_version": "proto_self.output.v2",
        "event_id": f"evt_{sample_id}",
        "policy_hint": {"ask_preferred": False},
        "response_tendency": {"ask_needed": False},
        "confidence_meta": {},
        "trace_payload": {"schema_version": "proto_self.trace.v2", "event_id": f"evt_{sample_id}"},
    }
    if shadow_h1:
        result_payload["trace_payload"]["shadow_h1"] = shadow_h1
        result_payload["confidence_meta"].update(
            {
                "shadow_h1_enabled": True,
                "shadow_h1_action_key": shadow_h1.get("action_key"),
                "shadow_h1_predicted_success": shadow_h1.get("predicted_success"),
                "shadow_h1_threshold": shadow_h1.get("threshold"),
                "shadow_h1_would_guard": shadow_h1.get("would_guard"),
                "shadow_h1_would_ask": shadow_h1.get("would_ask"),
            }
        )
    response_plan = {"status": "completed_verified", "delivery_kind": "final", "reply_length": 4}
    outbox_record = {"chat_id": 1, "message_id": 2, "text_length": 4, "success": True}
    timeline = [{"stage": "message_sent", "timestamp": timestamp}]
    tape = {"tape_id": f"tape_{sample_id}", "timestamp": timestamp}
    replay = {"sample_id": sample_id, "primary_ledger_ref": "ledger.json"}
    ledger = {
        "sample_id": sample_id,
        "timestamp": timestamp,
        "ids": {"session_id": "telegram:dm:test"},
        "openemotion": {"result": result_payload, "trace_payload": result_payload["trace_payload"], "events": []},
        "host": {"response_plan": response_plan, "outbox_record": outbox_record, "timeline": timeline},
        "evidence_completeness": {
            "raw_update": complete,
            "normalized_event": complete,
            "openemotion_result": complete,
            "response_plan": complete,
            "outbox_record": complete,
            "timeline": complete,
            "tape": complete,
            "replay": complete,
        },
    }
    files = {
        "ledger.json": ledger,
        "raw_update.json": raw_update,
        "normalized_event.json": normalized_event,
        "openemotion_result.json": result_payload,
        "response_plan.json": response_plan,
        "outbox_record.json": outbox_record,
        "timeline.json": timeline,
        "tape.json": tape,
        "replay.json": replay,
    }
    for filename, payload in files.items():
        if complete or filename not in {"outbox_record.json"}:
            _write_json(sample_dir / filename, payload)
    (sample_dir / "summary.md").write_text(f"# {sample_id}\n", encoding="utf-8")


def test_build_preflight_payload_closes_on_same_surface_contamination():
    module = _load_module(COMMON, "h1_e4_sampling_common_preflight")
    sample_matrix = {
        "binding_mode": "require_clean_commit",
        "rows": [
            {"manifest_id": "S1", "negative_control": False, "expected_path": ["telegram_bot", "native_loop", "runtime_observation"]},
        ],
    }
    payload = module.build_preflight_payload(
        sample_matrix=sample_matrix,
        head_short="abcd123",
        dirty_paths=[],
        live_process_version={
            "process_kind": "telegram",
            "git_commit_short": "abcd123",
            "git_dirty": False,
            "observed_at": "2026-04-09T10:00:00",
        },
        targeted_checks=[
            {"name": "native_path_surface", "status": "failed", "command": "pytest native"},
            {"name": "runtime_mainline_observation", "status": "passed", "command": "pytest obs"},
        ],
    )

    assert payload["decision"] == "close"
    assert payload["report_kind"] == "causality_exclusion"
    assert payload["surface_classification"]["contamination_detected"] is True


def test_build_preflight_payload_allows_runtime_generated_dirty_paths():
    module = _load_module(COMMON, "h1_e4_sampling_common_runtime_dirty")
    sample_matrix = {
        "binding_mode": "require_clean_commit",
        "rows": [
            {"manifest_id": "S1", "negative_control": False, "expected_path": ["telegram_bot", "native_loop", "runtime_observation"]},
        ],
    }
    payload = module.build_preflight_payload(
        sample_matrix=sample_matrix,
        head_short="abcd123",
        dirty_paths=[
            "EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json",
            "EgoCore/logs/egocore_run.log",
        ],
        live_process_version={
            "process_kind": "telegram",
            "git_commit_short": "abcd123",
            "git_dirty": False,
            "observed_at": "2026-04-09T10:00:00",
        },
        targeted_checks=[
            {"name": "native_path_surface", "status": "passed", "command": "pytest native"},
            {"name": "runtime_mainline_observation", "status": "passed", "command": "pytest obs"},
        ],
    )

    assert payload["workspace_clean"] is True
    assert payload["allowed_runtime_dirty_paths"] == [
        "EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json",
        "EgoCore/logs/egocore_run.log",
    ]
    assert payload["unexpected_tracked_dirty_paths"] == []
    assert payload["decision"] == "continue"


def test_build_sample_manifest_and_reports_match_shadow_and_negative_control(tmp_path):
    module = _load_module(COMMON, "h1_e4_sampling_common_manifest")
    real_dir = tmp_path / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"

    _make_sample(
        real_dir,
        "sample_20260409_110000_aaaaaaaa",
        timestamp="2026-04-09T11:00:00",
        text=r"读取并总结这个文件：D:\Project\AIProject\MyProject\Ego\__h1_shadow_missing__.md",
        shadow_h1={
            "enabled": True,
            "action_key": "tool:file",
            "predicted_success": 0.18,
            "threshold": 0.35,
            "would_guard": True,
            "would_ask": True,
            "source": "canonical_shadow",
        },
    )
    _make_sample(
        real_dir,
        "sample_20260409_110100_bbbbbbbb",
        timestamp="2026-04-09T11:01:00",
        text="用一句话总结今天的主线风险，不要执行任何工具。",
        shadow_h1=None,
    )

    bundles = module.load_sample_bundles(real_dir)
    manifest = module.build_sample_manifest_payload(
        sample_matrix={
            "binding_mode": "require_clean_commit",
            "rows": [
                {
                    "manifest_id": "S1",
                    "bucket": "positive_low_success_retry",
                    "negative_control": False,
                    "prompt_text": r"读取并总结这个文件：D:\Project\AIProject\MyProject\Ego\__h1_shadow_missing__.md",
                    "expected_path": ["telegram_bot", "native_loop"],
                    "expected_action_key": "tool:file",
                    "expected_shadow_mode": "guard_true",
                },
                {
                    "manifest_id": "S3",
                    "bucket": "negative_controls",
                    "negative_control": True,
                    "prompt_text": "用一句话总结今天的主线风险，不要执行任何工具。",
                    "expected_path": ["telegram_bot", "runtime_v2"],
                    "expected_action_key": "ingress:user_request",
                    "expected_shadow_mode": "absent",
                },
            ],
        },
        bundles=bundles,
        live_process_version={"observed_at": "2026-04-09T10:30:00", "git_commit_short": "abcd123"},
    )
    appearance = module.build_appearance_payload(manifest)
    failures = module.build_failures_payload(manifest)
    final_report = module.build_final_sample_report(
        preflight_payload={"decision": "continue"},
        manifest_payload=manifest,
        appearance_payload=appearance,
        failures_payload=failures,
    )

    assert manifest["summary"]["matched_complete"] == 2
    assert appearance["summary"]["shadow_present"] == 1
    assert appearance["summary"]["guard_true_count"] == 1
    assert failures["summary"]["failure_count"] == 0
    assert final_report["decision"] == "sample_level_observation_ready"


def test_resolve_sampling_source_root_prefers_admitted_preflight_worktree(tmp_path):
    module = _load_module(COMMON, "h1_e4_sampling_common_source_root")
    worktree_root = tmp_path / "clean_bind"
    worktree_root.mkdir(parents=True)

    resolved = module.resolve_sampling_source_root(
        preflight_payload={
            "decision": "continue",
            "evaluated_repo_root": str(worktree_root),
        }
    )

    assert resolved == worktree_root.resolve()


def test_build_causality_clear_payload_tracks_surface_transition(tmp_path):
    module = _load_module(CLEAN_BIND, "run_h1_clean_bind_cycle")
    previous_exclusion = {
        "surface_classification": {
            "records": [
                {"surface": "native_loop", "category": "same_surface_blocking"},
                {"surface": "runtime_observation", "category": "same_surface_cleared"},
            ]
        }
    }
    new_preflight = {
        "decision": "continue",
        "clean_bind_ready": True,
        "live_process_ok": True,
        "surface_classification": {
            "records": [
                {"surface": "native_loop", "category": "same_surface_cleared"},
                {"surface": "runtime_observation", "category": "same_surface_cleared"},
            ]
        },
    }
    worktree_root = tmp_path / "clean_bind"
    worktree_root.mkdir(parents=True)

    module._pid_alive = lambda pid: pid == "456"
    payload = module.build_causality_clear_payload(
        previous_exclusion=previous_exclusion,
        new_preflight=new_preflight,
        worktree_root=worktree_root,
        worktree_branch="codex/h1-clean-bind-demo",
        worktree_head_short="abcd123",
        mirrored_files=["EgoCore/tests/test_native_loop.py"],
        optional_files=["EgoCore/.env"],
        stopped_pids=["111", "222"],
        started_pid="456",
    )

    transitions = {item["surface"]: item for item in payload["surface_transition"]}
    assert payload["decision"] == "sampling_path_cleared"
    assert payload["clean_bind_ready"] is True
    assert payload["started_pid_alive"] is True
    assert transitions["native_loop"]["before"] == "same_surface_blocking"
    assert transitions["native_loop"]["after"] == "same_surface_cleared"


def test_wait_for_live_bind_timeout_tolerates_bom_launcher_meta(tmp_path):
    module = _load_module(CLEAN_BIND, "run_h1_clean_bind_cycle_bom")
    worktree_root = tmp_path / "clean_bind"
    launcher_meta = worktree_root / "EgoCore" / "logs" / "telegram_launcher_meta.json"
    launcher_meta.parent.mkdir(parents=True, exist_ok=True)
    launcher_meta.write_text(
        "\ufeff" + json.dumps({"resolved_repo_root": "D:/clean_bind"}, ensure_ascii=False),
        encoding="utf-8",
    )

    payload = module._wait_for_live_bind(
        worktree_root=worktree_root,
        expected_commit="abcd123",
        timeout_seconds=0,
        started_after=0.0,
    )

    assert payload["status"] == "timeout"
    assert payload["launcher_meta_payload"]["resolved_repo_root"] == "D:/clean_bind"
