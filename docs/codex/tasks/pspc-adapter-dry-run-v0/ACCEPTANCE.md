# PSPC Adapter Dry-Run Harness v0 Acceptance

## Acceptance Signals

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_dry_run_only`

| signal | expected |
|---|---|
| dry-run report exists | `artifacts/pspc_adapter_dry_run_v0/DRY_RUN_REPORT.md` exists. |
| dry-run JSON exists | `artifacts/pspc_adapter_dry_run_v0/dry_run_result.json` exists. |
| packet source | `source=virtual_cat_pspc_v0`. |
| disabled flags | `enabled=false` and `mainline_connected=false`. |
| adapter authority | `runtime_authority=none`. |
| audit-only output | output has no action, tool call, user message, memory write, gate decision, approval, transport, or schedule field. |
| no runtime registration | runtime sources do not import or reference `pspc_lab_adapter` / `PSPCLabAdapter`. |
| no side effects | report records no gate invocation, memory write, direct action, user message, proactive trigger, planner call, or training call. |
| claim ceiling unchanged | repo-wide `highest_evidence_level` remains unchanged. |

## Required Commands

- `python -m py_compile scripts\run_pspc_adapter_dry_run.py`
- `python -m pytest -q tests\test_pspc_adapter_dry_run.py`
- `python scripts\run_pspc_adapter_dry_run.py --out artifacts\pspc_adapter_dry_run_v0`
- `python scripts\codex\check_program_state_integrity.py`
- `python scripts\codex\verify_route_convergence.py`
- `python scripts\codex\verify_mainline_clarity.py`
- `python scripts\codex\lint_repo.py`
- `git diff --check`
- `python scripts\codex_session_guard.py closeout-check --format markdown`

## What This Proves

This acceptance proves a PSPC evidence packet can be validated and converted into audit-only artifact data by the disabled adapter in an isolated dry-run.

## What This Does Not Prove

It does not prove runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means no future runtime-adjacent review should start until the dry-run packet boundary or artifact-only behavior is repaired.

## Rollback

Delete `scripts/run_pspc_adapter_dry_run.py`, `tests/test_pspc_adapter_dry_run.py`, this task directory, `artifacts/pspc_adapter_dry_run_v0/`, and matching governance/ledger/generated-view entries.

