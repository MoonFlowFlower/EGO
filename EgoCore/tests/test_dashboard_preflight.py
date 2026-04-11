from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.dashboard.chat_service import DashboardChatService
from app.dashboard.preflight import (
    DeterministicDashboardPreflightRunner,
    build_dashboard_preflight_report,
    execute_dashboard_preflight,
    render_dashboard_preflight_markdown,
)
from app.openemotion_hooks.subject_gate import SubjectGateVerdict
from scripts.codex import prove_live_chat_subjective_variability as live_proof


class _AllowSubjectGate:
    def process_ingress(self, **kwargs):
        return SubjectGateVerdict.allow(stage="ingress")

    def process_finalized_result(self, **kwargs):
        return SubjectGateVerdict.allow(stage="finalized_result")

    def capture_response_plan(self, **kwargs):
        return SubjectGateVerdict.allow(stage="response_plan")

    def finalize_host_owned_result(self, **kwargs):
        return SubjectGateVerdict.allow(stage="response_plan")


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def test_dashboard_preflight_builds_acceptance_report() -> None:
    service = DashboardChatService(
        runner=DeterministicDashboardPreflightRunner(),
        subject_gate=_AllowSubjectGate(),
        llm_client_resolver=lambda: None,
    )

    preflight_result = execute_dashboard_preflight(service, session_name="preflight")
    report = build_dashboard_preflight_report(preflight_result, git_commit_short="abc1234")
    markdown = render_dashboard_preflight_markdown(report)

    assert report["source"] == "dashboard_local_preflight"
    assert report["claim_ceiling"] == "preflight_only"
    assert report["aggregate"]["ordinary_chat_mainline"] == 5
    assert report["aggregate"]["ordinary_chat_with_richer_fields"] == 5
    assert report["aggregate"]["tendency_delta_present"] is True
    assert report["aggregate"]["cadence_delta_present"] is True
    assert report["aggregate"]["hold_for_followup_artifact"] is True
    assert report["aggregate"]["subject_gate_all_ingress_ok"] is True
    assert report["aggregate"]["response_contract_present"] is True
    assert report["aggregate"]["no_raw_send_without_finalize"] is True
    assert report["aggregate"]["acceptance_met"] is True
    assert len(report["turn_records"]) == 5
    assert report["session_state"]["pending_proactive_outbox_count"] == 1
    assert report["assistant_turns"][-1]["host_proactive_candidate_present"] is True
    assert report["assistant_turns"][-1]["pending_proactive_outbox_count"] == 1
    assert "Dashboard Chat Preflight" in markdown
    assert "acceptance_met: `True`" in markdown


def test_live_chat_subjective_variability_proof_ignores_dashboard_only_samples(monkeypatch) -> None:
    with tempfile.TemporaryDirectory(prefix="dashboard-proof-ignore-") as tempdir:
        temp_root = Path(tempdir)
        real_root = temp_root / "artifacts" / "telegram_real_mainline_v1" / "real_telegram"
        dashboard_root = temp_root / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
        real_root.mkdir(parents=True, exist_ok=True)
        dashboard_sample = dashboard_root / "sample_dashboard_only"
        dashboard_sample.mkdir(parents=True, exist_ok=True)

        _write_json(
            dashboard_sample / "ledger.json",
            {
                "timestamp": "2026-04-11T12:00:00+00:00",
                "openemotion": {"result": {"response_tendency": {"preferred_mode": "ask"}}},
            },
        )
        _write_json(
            dashboard_sample / "raw_update.json",
            {
                "message": {
                    "text": "你好",
                    "chat": {"id": 123, "type": "private"},
                }
            },
        )
        _write_json(
            dashboard_sample / "response_plan.json",
            {
                "status": "chat",
                "reply_authority": "model_chat",
                "reply_origin": "chat_mainline",
                "delivery_kind": "chat",
                "metadata": {"chat_cadence_mode": "reply_now_short"},
            },
        )

        monkeypatch.setattr(live_proof, "REAL_ROOT", real_root)
        monkeypatch.setattr(live_proof, "_git_commit_timestamp", lambda commitish: "2026-04-10T00:00:00+00:00")

        payload = live_proof.build_payload("dummy")

        assert payload["fresh_sample_count"] == 0
        assert payload["ordinary_chat_rows"] == 0
        assert payload["acceptance_met"] is False
