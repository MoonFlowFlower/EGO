# PSPC Disabled Shadow Hook v0 Acceptance

Claim ceiling: `lab_only_proto_self_mechanism_candidate / disabled_shadow_hook_only`

## Required Acceptance Signals

- Hook module exists.
- Hook is disabled by default.
- Hook is mainline-disconnected by default.
- Hook has `runtime_authority=none`.
- Hook output is audit-only and non-executable.
- Hook rejects runtime-connected contexts.
- Hook rejects `enabled=true` and `mainline_connected=true` PSPC audit candidates.
- Hook rejects executable PSPC fields.
- Runner writes only artifact output.
- Runtime sources do not import or register the hook.
- No runtime gate, memory writer, approval executor, transport sender, proactive scheduler, PSPC planner, PSPC training, or user-message renderer is called.

## Required Checks

- `python -m pytest -q tests/test_pspc_disabled_shadow_hook.py`
- `python scripts/run_pspc_disabled_shadow_hook_review.py --out artifacts/pspc_disabled_shadow_hook_v0`
- `python -m pytest -q tests/test_pspc_lab_adapter_contract.py tests/test_pspc_adapter_dry_run.py tests/test_pspc_static_compatibility_review.py tests/test_pspc_fixture_shadow_trace.py tests/test_pspc_disabled_shadow_hook.py`
- `python scripts/codex/check_program_state_integrity.py`
- `python scripts/codex/verify_route_convergence.py`
- `python scripts/codex/verify_mainline_clarity.py`
- `python scripts/codex/lint_repo.py`
- `git diff --check`
- `python scripts/codex_session_guard.py closeout-check --format markdown`

## What This Proves

This proves a disabled PSPC read-only shadow hook can render audit-only data from fixture shadow trace data without runtime registration or side effects.

## What This Does Not Prove

It does not prove runtime registration safety, live runtime hook safety, real EgoOperator trace compatibility, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Rollback

Delete `EgoOperator/adapters/pspc_read_only_shadow_hook.py`, `scripts/run_pspc_disabled_shadow_hook_review.py`, `tests/test_pspc_disabled_shadow_hook.py`, this task directory, `artifacts/pspc_disabled_shadow_hook_v0/`, and matching governance/ledger/generated-view entries.
