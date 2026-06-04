# PSPC Read-Only Adapter Implementation v0 Static Test Plan

## Purpose

Define the static tests required for a future adapter skeleton task. This stage does not implement those tests and does not create the adapter.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`

## Future Test Targets

A later skeleton task may add a focused test file for the adapter contract. Tests must remain static/unit-level and must not run PSPC inside EgoOperator runtime.

## Required Future Static Tests

| test | required assertion |
|---|---|
| adapter exists but is not registered | Adapter file exists only in the future skeleton stage and no EgoOperator runtime import/registry path references it. |
| valid packet accepted | A disabled, mainline-disconnected PSPC evidence packet validates as audit-only. |
| missing forbidden flags rejected | Packets missing direct action, direct user message, direct memory write, runtime gate bypass, runtime registration, or proactive trigger flags are rejected. |
| `enabled=true` rejected | Adapter rejects enabled packets. |
| `mainline_connected=true` rejected | Adapter rejects mainline-connected packets. |
| action fields rejected | Adapter rejects `action`, `tool_call`, `command`, `send`, `schedule`, and transport fields. |
| memory fields rejected | Adapter rejects `memory_write`, `memory_patch`, and operator memory update fields. |
| user message fields rejected | Adapter rejects direct user-message text fields. |
| gate/approval fields rejected | Adapter rejects `gate_decision`, `approval_id`, and `preapproved`. |
| output audit-only | Adapter output has `adapter_status=disabled_read_only`, no runtime action, no user text, no memory write, and no approval. |
| no runtime import | Static scan proves the adapter does not import `agent_base`, gate, approval, memory, human-trial, or transport modules. |

## Required Future Negative Controls

- A packet with `forbidden.direct_action=false` must fail.
- A packet with `forbidden.direct_user_message=false` must fail.
- A packet with `forbidden.direct_memory_write=false` must fail.
- A packet with `forbidden.runtime_gate_bypass=false` must fail.
- A packet with `forbidden.runtime_registration=false` must fail.
- A packet with `forbidden.proactive_trigger=false` must fail.

## Current Stage Static Checks

This Stage Card package must verify:

- no adapter file exists
- no EgoOperator files changed
- docs state disabled-by-default and mainline-disconnected requirements
- docs state forbidden direct action, user message, memory write, gate bypass, runtime registration, and proactive trigger

## What This Proves

This static test plan proves that a future skeleton task has predefined contract tests focused on no registration, no runtime import, no direct action, no user message, no memory write, and no gate bypass.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, adapter skeleton existence, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback

Rollback this stage by removing `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`, its evidence-ledger entry, and matching governance/generated-view entries. No EgoOperator rollback is required because this stage creates no adapter and modifies no runtime.

