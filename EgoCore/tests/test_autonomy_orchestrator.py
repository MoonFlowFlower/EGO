import asyncio

import pytest

from app.autonomy import (
    AutonomyExecutorKind,
    AutonomyOrchestrator,
    AutonomyRun,
    AutonomyRunRepository,
    AutonomyRunStatus,
    AutonomySliceOutcome,
)
from app.storage.db import Database


@pytest.mark.asyncio
async def test_autonomy_orchestrator_auto_resumes_until_completed(tmp_path):
    repo = AutonomyRunRepository(Database(tmp_path / "autonomy.db"))
    orchestrator = AutonomyOrchestrator(repository=repo)
    calls = {"count": 0}

    async def initial_execute(_run: AutonomyRun) -> AutonomySliceOutcome:
        calls["count"] += 1
        return AutonomySliceOutcome(
            status=AutonomyRunStatus.RESUMABLE_PAUSE,
            stop_reason="planning_timeout",
            current_phase="planning_current_slice",
            checkpoint_payload={"slice": 1},
            runtime_state_snapshot={"session_id": "telegram:dm:test"},
            last_result_summary={"status": "resumable_pause"},
        )

    async def resume_execute(run: AutonomyRun, _trigger_source: str) -> AutonomySliceOutcome:
        calls["count"] += 1
        if calls["count"] == 2:
            return AutonomySliceOutcome(
                status=AutonomyRunStatus.RESUMABLE_PAUSE,
                stop_reason="max_steps_exhausted",
                current_phase="executing_changes",
                checkpoint_payload={"slice": 2},
                runtime_state_snapshot={"session_id": run.session_key},
                last_result_summary={"status": "resumable_pause"},
            )
        return AutonomySliceOutcome(
            status=AutonomyRunStatus.COMPLETED,
            stop_reason="completed",
            current_phase="completed",
            runtime_state_snapshot={"session_id": run.session_key},
            last_result_summary={"status": "completed_verified"},
        )

    orchestrator.register_surface("telegram", resume_execute)
    run = await orchestrator.submit_ingress(
        surface="telegram",
        session_key="telegram:dm:test",
        objective="在 Test 目录下创建 demo.txt",
        executor_kind=AutonomyExecutorKind.GENERIC_RUNTIME,
        metadata={},
        initial_execute=initial_execute,
    )

    terminal = await orchestrator.wait_for_terminal(run.id, timeout_seconds=2.0)

    assert terminal is not None
    assert terminal.status == AutonomyRunStatus.COMPLETED
    assert terminal.current_phase == "completed"
    assert terminal.resume_count == 2
    assert calls["count"] == 3
