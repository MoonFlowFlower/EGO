# PSPC Read-Only Adapter Design Review v0 Static Compatibility Review

## Scope

This is a static, read-only review of how a future PSPC evidence packet could remain compatible with EgoOperator boundaries. It does not implement an adapter, import EgoOperator runtime code, modify gates, write memory, run human-trial harnesses, or test PSPC inside EgoOperator.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / design_review_only`

## Sources Reviewed

- `EgoOperator/agent_base.py`
- `EgoOperator/primitives/runtime_gate.py`
- `EgoOperator/real_use_gate.py`
- `EgoOperator/tests/test_permission_gates.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `EgoOperator/tests/test_real_use_memory_gate.py`
- `artifacts/virtual_cat_pspc_v0/ADMISSION_PACKET_CONTRACT_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/GO_NO_GO_REVIEW.md`

## Current EgoOperator Boundary Observations

- `EgoOperator/primitives/runtime_gate.py` describes `AgentRuntime/SafetyGate` as the admission path and keeps side-effect defaults off for tools, network, file write, command, and memory write.
- `EgoOperator/agent_base.py` routes tool calls through runtime gate checks, permission proposals, approval commands, and trace records.
- `EgoOperator/tests/test_permission_gates.py` checks that direct side-effect tools are not exposed by default, mutation needs approval, broad destructive commands are blocked, and `remember_note` requires explicit user intent.
- `EgoOperator/tests/test_real_use_memory_gate.py` keeps memory and tool-gate behavior under candidate-local observation, not repo-wide proof.

These observations support a future design rule: PSPC must not join the runtime path as an actor. It can only be an external evidence source whose packet is read for audit.

## Compatible Future Flow

Allowed future shape, only after a separate adapter implementation Stage Card:

`PSPC trace/report -> read-only adapter packet -> audit trace/proposal review -> EgoOperator gate independently admits or rejects later runtime behavior`

The packet may be stored as audit evidence only if a future Stage Card defines exact paths and tests.

## Incompatible Future Flow

Forbidden shapes:

- `PSPC trace/report -> direct tool call`
- `PSPC trace/report -> direct user message`
- `PSPC trace/report -> EgoOperator memory write`
- `PSPC trace/report -> approval grant`
- `PSPC trace/report -> runtime gate decision`
- `PSPC planner -> EgoOperator action selection`
- `PSPC evidence -> consciousness or live-autonomy claim`

## Field Routing Review

| packet field | future routing ceiling | must not enter |
|---|---|---|
| `source` | audit metadata | planner/action selection |
| `claim_level` | audit metadata and claim guard | user-visible claim elevation |
| `mainline_connected` | gate/static contract check | runtime enablement |
| `enabled` | gate/static contract check | runtime enablement |
| `allowed_use` | audit/design review only | runtime execution |
| `evidence_refs` | audit trace refs | memory write, tool args, user text |
| `proposal_hint` | `null` in this stage; future audit hint only if separately approved | action, command, message, memory write |
| `forbidden` | static contract guard | optional metadata |

## Static Contract Test Requirements For Future Stage

A future adapter implementation Stage Card must include static tests that prove:

- adapter creation is explicit and scoped to the adapter file plus tests
- packet validation rejects action, tool, message, memory, gate, approval, transport, schedule, and enablement fields
- packet creation imports no EgoOperator runtime/gate/memory modules
- packet creation writes no EgoOperator memory files
- packet creation emits no user-visible text
- forbidden flags must all be `true`
- `mainline_connected` and `enabled` must remain `false`
- claim ceiling remains `lab_only_proto_self_mechanism_candidate`

## What This Proves

This review proves that the future PSPC packet can be framed as read-only audit input without requiring EgoOperator runtime changes, and it identifies which fields must never enter runtime, memory, approval, transport, or user-output surfaces.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback Note

Rollback requires removing this design-review task directory, the matching evidence-ledger entry, and the matching governance/generated-view entries. No EgoOperator rollback is required because this review creates no adapter and modifies no runtime.

