# PSPC Read-Only Adapter Skeleton v0 Acceptance

## Acceptance Signals

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_skeleton_only`

| signal | expected |
|---|---|
| adapter skeleton exists | `EgoOperator/adapters/pspc_lab_adapter.py` exists. |
| disabled by default | `PSPCLabAdapter.enabled is False`. |
| mainline disconnected | `PSPCLabAdapter.mainline_connected is False`. |
| no runtime authority | `runtime_authority == "none"`. |
| no side-effect methods | no `send_message`, `write_memory`, `select_action`, `register_runtime`, `invoke_gate`, `run_planner`, or `train_model`. |
| rejects unsafe packets | rejects direct action, direct user message, direct memory write, runtime gate bypass, runtime registration, proactive trigger, `enabled=true`, and `mainline_connected=true`. |
| audit-only output | `to_audit_candidate` emits no executable action, tool call, user message, memory write, gate decision, approval, transport, or schedule field. |
| not registered | no EgoOperator runtime source imports or references `pspc_lab_adapter` / `PSPCLabAdapter`. |
| runtime untouched | no EgoOperator files other than `EgoOperator/adapters/pspc_lab_adapter.py` are modified. |
| rollback simple | deleting adapter, tests, docs, artifacts, and ledger/status entries reverts this task. |

## Verification Commands

- `python -m py_compile EgoOperator\adapters\pspc_lab_adapter.py`
- `python -m pytest -q tests\test_pspc_lab_adapter_contract.py`
- static check that `git diff --name-only -- EgoOperator` contains only `EgoOperator/adapters/pspc_lab_adapter.py`
- `python scripts\codex\check_program_state_integrity.py`
- `python scripts\codex\verify_route_convergence.py`
- `python scripts\codex\verify_mainline_clarity.py`
- `python scripts\codex\lint_repo.py`
- `git diff --check`
- `python scripts\codex_session_guard.py closeout-check --format markdown`

## What This Proves

Passing acceptance proves a PSPC lab evidence packet can be safely validated and represented as audit-only data inside the repo without runtime registration, direct action, user messages, memory writes, or gate bypass.

## What This Does Not Prove

It does not prove adapter readiness, runtime integration safety, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, production safety, consciousness, or subjective experience.

## Rollback

Delete `EgoOperator/adapters/pspc_lab_adapter.py`, `tests/test_pspc_lab_adapter_contract.py`, this task directory, `artifacts/pspc_adapter_skeleton_v0/`, and matching governance/ledger/generated-view entries.

