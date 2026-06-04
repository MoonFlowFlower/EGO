# PSPC Disabled Shadow Hook v0 Contract

Claim ceiling: `lab_only_proto_self_mechanism_candidate / disabled_shadow_hook_only`

## Class Contract

`PSPCReadOnlyShadowHook` must remain:

- `enabled=false`
- `mainline_connected=false`
- `runtime_authority=none`
- `mode=shadow_audit_only`
- `side_effects_allowed=false`

## Allowed Methods

- `assert_no_runtime_authority()`
- `validate_inputs(operator_context, audit_candidate)`
- `render_shadow_audit(operator_context, audit_candidate)`

## Forbidden Methods

- `send_message()`
- `write_memory()`
- `select_action()`
- `register_runtime()`
- `invoke_gate()`
- `run_planner()`
- `train_model()`

## Input Boundary

The hook may read only fixture or future approved shadow context plus PSPC audit candidates. It must reject runtime-connected contexts, `enabled=true`, `mainline_connected=true`, and executable fields such as `action`, `tool_call`, `user_message`, `memory_write`, `gate_decision`, `approval_id`, `transport`, or `runtime_registration`.

## Output Boundary

The hook may output only audit observation data. It must not output executable actions, user messages, memory patches, gate decisions, approval changes, transport payloads, proactive triggers, runtime registry changes, or claim-ceiling changes.

## What This Proves

This proves the disabled hook has a narrow code contract and can be tested without entering runtime.

## What This Does Not Prove

It does not prove runtime registration safety, live runtime hook safety, real EgoOperator trace compatibility, adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Rollback

Delete the hook file, runner, tests, this task directory, artifacts, and matching governance/ledger/generated-view entries.
