#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_simulated_whole_chain_v1"
SAMPLE_ROOT = ARTIFACT_ROOT / "simulated_telegram"
REPORTS_DIR = ARTIFACT_ROOT / "reports"

MANIFEST_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_SAMPLE_MANIFEST_CURRENT.json"
FAILURES_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_FAILURES_CURRENT.json"
EXECUTION_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_EXECUTION_REPORT_CURRENT.json"
TRACE_JSON = REPORTS_DIR / "LLM_WHOLE_CHAIN_TRACE_READINESS_CURRENT.json"

EXTRA_TRACE_FILES = {
    "ingress_event.json",
    "native_loop_trace.json",
    "contract_runtime_trace.json",
    "model_trace.json",
    "tool_trace.json",
}
EVIDENCE_FILES = {
    "raw_update.json",
    "normalized_event.json",
    "openemotion_result.json",
    "response_plan.json",
    "outbox_record.json",
    "timeline.json",
    "tape.json",
    "replay.json",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    manifest = _read(MANIFEST_JSON)
    failures = _read(FAILURES_JSON)
    execution = _read(EXECUTION_JSON)
    trace = _read(TRACE_JSON)

    rows = list(manifest.get("rows") or [])
    assert len(rows) == 2, f"expected 2 manifest rows, got {len(rows)}"
    assert execution["summary"]["expected_cases"] == 2
    assert execution["hard_rule_status"]["relabeled_as_replay"] is False
    assert execution["hard_rule_status"]["repo_level_state_upgraded"] is False
    assert execution["hard_rule_status"]["runtime_efficacy_claim"] is False
    assert execution["summary"]["failed_cases"] == failures["failure_count"]

    trace_rows = list(trace.get("rows") or [])
    assert len(trace_rows) == 2, f"expected 2 trace rows, got {len(trace_rows)}"
    for row in rows:
        assert row["status"] == "completed", f"case not completed: {row}"
        sample_dir = ROOT / row["sample_dir"]
        assert sample_dir.exists(), f"missing sample dir: {sample_dir}"
        for name in EVIDENCE_FILES | EXTRA_TRACE_FILES:
            assert (sample_dir / name).exists(), f"missing artifact {name} in {sample_dir}"

    for row in trace_rows:
        assert row["replay_ready_without_requery"] is True, f"trace not replay-ready: {row}"
        assert row["model_interaction_count"] >= 2, f"expected >=2 model interactions: {row}"

    print(
        json.dumps(
            {
                "ok": True,
                "cases": len(rows),
                "failures": failures["failure_count"],
                "replay_ready_cases": execution["summary"]["replay_ready_cases"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
