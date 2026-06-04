# PSPC Read-Only Shadow Hook Stage Card v0 Acceptance

Claim ceiling: `lab_only_proto_self_mechanism_candidate / shadow_hook_stage_card_only`

## Required Acceptance Signals

- Stage card exists.
- Hook boundary contract exists.
- Hook is specified as default disabled.
- Hook is specified as shadow/audit mode only.
- Hook is specified as read-only and non-mutating.
- Hook cannot change proposal, plan, approval, gate, user response, memory, transport, proactive state, runtime registry, or claim ceiling.
- Hook cannot call runtime gate, memory writer, approval executor, transport sender, proactive scheduler, PSPC planner, PSPC training, user-message renderer, or runtime registration.
- EgoOperator runtime files are not modified.
- `PSPCLabAdapter` remains unregistered by runtime.

## Required Verification

- `git diff --name-only -- EgoOperator` returns no modified runtime files for this stage.
- Static scan finds no `pspc_lab_adapter` or `PSPCLabAdapter` import/registry reference in non-adapter EgoOperator runtime sources.
- `python scripts/codex/check_program_state_integrity.py`
- `python scripts/codex/verify_route_convergence.py`
- `python scripts/codex/verify_mainline_clarity.py`
- `git diff --check`
- `python scripts/codex_session_guard.py closeout-check --format markdown`

## What This Proves

This proves only that the future read-only shadow hook implementation boundary has been pre-registered and constrained before code exists.

## What This Does Not Prove

It does not prove a hook exists, a hook is safe, runtime integration safety, adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Rollback

Delete this task directory, `artifacts/pspc_read_only_shadow_hook_stage_card_v0/`, and matching governance/ledger/generated-view entries.
