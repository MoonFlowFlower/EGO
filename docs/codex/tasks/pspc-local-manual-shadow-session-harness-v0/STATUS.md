# PSPC Local Manual Shadow Session Harness v0

- status: `accepted`
- task_board_id: `PSPC-SHADOW-HOOK-006`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / local_manual_shadow_session_only`
- session_id: `pspc_manual_shadow_fixture_v0`
- input_mode: `default_fixture`
- record_count: `2`
- enabled: `false`
- mainline_connected: `false`
- runtime_authority: `none`

## Scope

This task creates a local CLI harness that consumes operator-provided prompts and optional baseline replies, then writes PSPC shadow observations as separate artifacts. It does not invoke EgoOperator runtime, generate user-visible replies, register a hook, write memory, invoke gate/approval, call transport, trigger proactive behavior, call planner/training/model execution, or raise the claim ceiling.

## Evidence

- runner: `scripts/run_pspc_local_manual_shadow_session.py`
- tests: `tests/test_pspc_local_manual_shadow_session_harness.py`
- result JSON: `artifacts/pspc_local_manual_shadow_session_harness_v0/local_manual_shadow_session.json`
- report: `artifacts/pspc_local_manual_shadow_session_harness_v0/LOCAL_MANUAL_SHADOW_SESSION_REPORT.md`

## Result

- local CLI only: `true`
- live transport channel: `false`
- runtime invocation: `false`
- record count: `2`
- baseline user-output diff: `false`
- runtime-authority fields: `0`
- active runtime scan offenders: `0`
- side effects: `none`
- next allowed step: `manual_shadow_review_go_no_go_only`

## Manual Use

Quick prompt-only shadow artifact:

```powershell
python scripts\run_pspc_local_manual_shadow_session.py --prompt "你的测试输入" --out artifacts\pspc_local_manual_shadow_session_harness_v0\manual_run
```

Transcript shadow artifact with operator-provided baseline replies:

```powershell
python scripts\run_pspc_local_manual_shadow_session.py --input-jsonl path\to\manual_inputs.jsonl --out artifacts\pspc_local_manual_shadow_session_harness_v0\manual_run
```

The JSONL input format is one object per line with `prompt`, optional `baseline_user_output`, and optional `scenario_id`.

## What This Proves

Operator-provided or fixture prompt transcripts can be converted into separate PSPC shadow artifacts through a local CLI harness without live transport, runtime invocation, runtime registration, user response mutation, proposal/plan mutation, memory write, gate or approval invocation, proactive trigger, planner call, training call, model execution, or claim-ceiling upgrade.

## What This Does Not Prove

This does not prove live EgoOperator runtime integration safety, live user-visible improvement, proposal hinting safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure would mean the harness cannot be used for manual PSPC shadow review and PSPC must remain disabled artifact-only shadow evidence until the no-side-effect boundary is restored.

## Rollback

Delete `scripts/run_pspc_local_manual_shadow_session.py`, `tests/test_pspc_local_manual_shadow_session_harness.py`, `docs/codex/tasks/pspc-local-manual-shadow-session-harness-v0/`, `artifacts/pspc_local_manual_shadow_session_harness_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.

## Next Allowed Step

Only `PSPC-SHADOW-HOOK-007` manual shadow review go/no-go may proceed next. PSPC remains disabled, mainline-disconnected, audit-only, and side-effect-free.
