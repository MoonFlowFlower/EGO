# PSPC Read-Only Adapter Implementation v0 Acceptance

## Scope

This acceptance file defines completion for the Stage Card package only. It does not accept adapter implementation, adapter registration, runtime integration, memory writes, user-visible behavior, or proactive behavior.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`

## Required Acceptance Signals

| signal | required result |
|---|---|
| Stage Card package exists | `STAGE_CARD.md`, `CONTRACT.md`, `ACCEPTANCE.md`, `ROLLBACK.md`, `STATIC_TEST_PLAN.md`, and `GO_NO_GO_REVIEW.md` exist. |
| no adapter file | `EgoOperator/adapters/pspc_lab_adapter.py` does not exist after this stage. |
| no runtime mutation | `git diff --name-only -- EgoOperator` is empty. |
| disabled-by-default recorded | Docs state `enabled=false` and `mainline_connected=false`. |
| forbidden behaviors recorded | Docs forbid direct action, direct user message, direct memory write, gate bypass, runtime registration, and proactive trigger. |
| future skeleton only | GO/NO-GO permits at most a future separate adapter skeleton task. |
| rollback scoped | Rollback requires only removing this docs package and governance/ledger/generated-view entries. |
| claim ceiling unchanged | Repo-wide `highest_evidence_level` remains unchanged and PSPC claims stay at `lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`. |

## Required Checks

- `Test-Path EgoOperator\adapters\pspc_lab_adapter.py` must return false.
- `git diff --name-only -- EgoOperator` must return no paths.
- Packet/contract docs must include forbidden direct action, direct user message, direct memory write, runtime gate bypass, runtime registration, and proactive trigger.
- Every document in this task directory must include what it proves, what it does not prove, claim ceiling, and rollback.
- `python scripts\codex\check_program_state_integrity.py`
- `python scripts\codex\verify_route_convergence.py`
- `python scripts\codex\verify_mainline_clarity.py`
- `python scripts\codex\lint_repo.py`
- `git diff --check`
- `python scripts\codex_session_guard.py closeout-check --format markdown`

## Pass Meaning

Pass means the future adapter skeleton task has a bounded contract and static test plan. It does not mean adapter code exists or that PSPC is connected to EgoOperator.

## Failure Meaning

Failure means either the stage package is incomplete or the boundary has drifted toward implementation/runtime integration. If any runtime file changes or the adapter file exists, this stage must be rolled back or reclassified before proceeding.

## What This Proves

This acceptance spec proves that the stage has a concrete docs-only done definition and that completion must be checked against no-adapter, no-runtime-mutation, disabled-by-default, forbidden-behavior, and rollback signals.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, adapter skeleton existence, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback

Rollback this stage by removing `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`, its evidence-ledger entry, and matching governance/generated-view entries. No EgoOperator rollback is required because this stage creates no adapter and modifies no runtime.

