#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import sys
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "EgoCore") not in sys.path:
    sys.path.insert(0, str(ROOT / "EgoCore"))

from app.dashboard.stage3_stance_integrity import (
    DEFAULT_STAGE3_CASES,
    STAGE3_SESSION_BOUNDARY,
    Stage3LifecycleTracker,
    assemble_stage3_stance_integrity_report,
    bootstrap_stage3_environment,
    build_stage3_lifecycle_debug_report,
    build_stage3_run_state,
    get_stage3_remaining_cases,
    record_stage3_completed_case,
    render_stage3_lifecycle_markdown,
    render_stage3_stance_integrity_markdown,
    sync_stage3_run_state_with_lifecycle,
    validate_stage3_run_state,
    run_stage3_stance_integrity,
)


ARTIFACT_ROOT = ROOT / "artifacts" / "telegram_real_mainline_v1" / "dashboard_v1"
REPORT_JSON = ARTIFACT_ROOT / "STAGE3_STANCE_INTEGRITY_GATE_CURRENT.json"
REPORT_MD = ARTIFACT_ROOT / "STAGE3_STANCE_INTEGRITY_GATE_CURRENT.md"
LIFECYCLE_JSON = ARTIFACT_ROOT / "STAGE3_STANCE_INTEGRITY_LIFECYCLE_CURRENT.json"
LIFECYCLE_MD = ARTIFACT_ROOT / "STAGE3_STANCE_INTEGRITY_LIFECYCLE_CURRENT.md"
RUN_STATE_JSON = ARTIFACT_ROOT / "STAGE3_STANCE_INTEGRITY_RUN_STATE_CURRENT.json"
RUN_STATE_MD = ARTIFACT_ROOT / "STAGE3_STANCE_INTEGRITY_RUN_STATE_CURRENT.md"


class Stage3LifecycleInterrupted(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bounded dashboard Stage 3 stance-integrity gate")
    parser.add_argument("--session-prefix", default="stage3-stance-integrity")
    parser.add_argument("--case-limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--reset-run", action="store_true")
    return parser.parse_args()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_lifecycle_report(report: dict) -> None:
    _write_json(LIFECYCLE_JSON, report)
    _write_text(LIFECYCLE_MD, render_stage3_lifecycle_markdown(report))


def _write_run_state(payload: dict) -> None:
    _write_json(RUN_STATE_JSON, payload)
    _write_text(RUN_STATE_MD, _render_run_state_markdown(payload))


def _load_run_state() -> dict | None:
    if not RUN_STATE_JSON.exists():
        return None
    return json.loads(RUN_STATE_JSON.read_text(encoding="utf-8"))


def _new_run_id() -> str:
    return f"stage3-{uuid.uuid4().hex[:12]}"


def _resume_command(case_limit: int | None) -> str:
    command = "python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py --resume"
    effective_limit = 2 if case_limit is None or case_limit <= 0 else int(case_limit)
    return f"{command} --case-limit {effective_limit}"


def _render_run_state_markdown(payload: dict) -> str:
    invariants = dict(payload.get("config_invariants") or {})
    lines = [
        "# Stage 3 Run State",
        "",
        f"- schema_version: `{payload.get('schema_version')}`",
        f"- run_id: `{payload.get('run_id')}`",
        f"- status: `{payload.get('status')}`",
        f"- started_at: `{payload.get('started_at')}`",
        f"- updated_at: `{payload.get('updated_at')}`",
        f"- session_prefix: `{payload.get('session_prefix')}`",
        f"- session_boundary: `{payload.get('session_boundary')}`",
        f"- current_case_id: `{payload.get('current_case_id')}`",
        f"- current_round_id: `{payload.get('current_round_id')}`",
        f"- completed_case_ids: `{payload.get('completed_case_ids')}`",
        f"- remaining_case_ids: `{payload.get('remaining_case_ids')}`",
        f"- resume_recommended_command: `{payload.get('resume_recommended_command')}`",
        "",
        "## Config Invariants",
        "",
        f"- entrypoint: `{invariants.get('entrypoint')}`",
        f"- claim_ceiling: `{invariants.get('claim_ceiling')}`",
        f"- chat_compaction_mode: `{invariants.get('chat_compaction_mode')}`",
        f"- chat_provider: `{invariants.get('chat_provider')}`",
        f"- chat_model: `{invariants.get('chat_model')}`",
        f"- chat_fallback_enabled: `{invariants.get('chat_fallback_enabled')}`",
        f"- case_set_fingerprint: `{invariants.get('case_set_fingerprint')}`",
        "",
        "## Claim Ceiling",
        "",
        "- This artifact only records resumable execution state for the dashboard-only single-entry Stage 3 gate.",
        "- It does not prove cross-entry behavior, runtime efficacy, broad real-user benefit, or AI self-awareness achieved.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    interrupted = {"reason": None}
    all_cases = list(DEFAULT_STAGE3_CASES)
    environment = bootstrap_stage3_environment()
    resume_command = _resume_command(args.case_limit)

    if args.resume and not args.reset_run:
        run_state = _load_run_state()
        if run_state is None:
            raise RuntimeError("No unfinished Stage 3 run-state exists; start a new run or use --reset-run.")
        validate_stage3_run_state(run_state=run_state, cases=all_cases, environment=environment)
    else:
        run_state = build_stage3_run_state(
            run_id=_new_run_id(),
            cases=all_cases,
            environment=environment,
            session_prefix=args.session_prefix,
        )
    run_state["resume_recommended_command"] = resume_command

    remaining_cases = get_stage3_remaining_cases(run_state=run_state, cases=all_cases)
    if args.case_limit is not None and args.case_limit > 0:
        invocation_cases = remaining_cases[: args.case_limit]
    else:
        invocation_cases = remaining_cases

    lifecycle_tracker = Stage3LifecycleTracker(
        run_id=run_state.get("run_id"),
        expected_case_count=len(all_cases),
    )

    def _persist_views(*, status: str | None = None) -> None:
        sync_stage3_run_state_with_lifecycle(
            run_state,
            lifecycle_snapshot=lifecycle_tracker.snapshot(),
            status=status,
            resume_recommended_command=resume_command,
        )
        _write_run_state(run_state)
        _write_lifecycle_report(
            build_stage3_lifecycle_debug_report(
                tracker=lifecycle_tracker,
                environment=environment,
                run_state=run_state,
                resume_recommended_command=resume_command,
            )
        )

    lifecycle_tracker._persist_hook = lambda _snapshot: _persist_views()

    def _case_complete_hook(case_result: dict) -> None:
        record_stage3_completed_case(run_state, case_result)
        _persist_views(status="running")

    _persist_views(status="running")

    def _signal_handler(signum, _frame) -> None:
        interrupted["reason"] = f"signal_{signum}"
        lifecycle_tracker.mark_blocked(
            kind="Stage3LifecycleInterrupted",
            message=f"Interrupted by signal {signum}",
            phase=lifecycle_tracker.current_phase,
        )
        raise Stage3LifecycleInterrupted(f"Interrupted by signal {signum}")

    previous_sigint = signal.signal(signal.SIGINT, _signal_handler)
    previous_sigterm = signal.signal(signal.SIGTERM, _signal_handler)
    try:
        if invocation_cases:
            run_stage3_stance_integrity(
                session_prefix=str(run_state.get("session_prefix") or args.session_prefix),
                cases=invocation_cases,
                lifecycle_tracker=lifecycle_tracker,
                case_complete_hook=_case_complete_hook,
            )
        completed_case_ids = list(run_state.get("completed_case_ids") or [])
        if len(completed_case_ids) == len(all_cases):
            run_state["status"] = "completed"
            final_report = assemble_stage3_stance_integrity_report(
                results=list(run_state.get("completed_case_results") or []),
                expected_cases=all_cases,
                environment=environment,
                run_metadata={
                    "run_id": run_state.get("run_id"),
                    "session_boundary": run_state.get("session_boundary") or STAGE3_SESSION_BOUNDARY,
                    "completed_case_ids": completed_case_ids,
                    "config_invariants": dict(run_state.get("config_invariants") or {}),
                },
            )
            with lifecycle_tracker.phase("write_current_artifact"):
                _write_json(REPORT_JSON, final_report)
                _write_text(REPORT_MD, render_stage3_stance_integrity_markdown(final_report))
            _persist_views(status="completed")
            print(json.dumps(final_report.get("summary") or {}, ensure_ascii=False, indent=2))
        else:
            run_state["status"] = "ready_for_resume"
            _persist_views(status="ready_for_resume")
            print(
                json.dumps(
                    {
                        "run_id": run_state.get("run_id"),
                        "status": run_state.get("status"),
                        "completed_case_ids": run_state.get("completed_case_ids"),
                        "remaining_case_ids": run_state.get("remaining_case_ids"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        return 0
    except BaseException as exc:
        lifecycle_tracker.mark_blocked(
            kind=type(exc).__name__,
            message=interrupted["reason"] or str(exc),
            phase=lifecycle_tracker.current_phase,
        )
        _persist_views(status="interrupted")
        raise
    finally:
        signal.signal(signal.SIGINT, previous_sigint)
        signal.signal(signal.SIGTERM, previous_sigterm)


if __name__ == "__main__":
    raise SystemExit(main())
