# PSPC Read-Only Adapter Design Review v0 Threat Model

## Scope

This threat model covers only a possible future read-only PSPC evidence contact surface. It does not implement an adapter, create a runtime hook, modify EgoOperator, or run PSPC inside EgoOperator.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / design_review_only`

## Threats And Controls

| threat | failure mode | required control | stage verdict if control is absent |
|---|---|---|---|
| PSPC output is mistaken for an action command | A tendency like `avoid_unstable_object` becomes a runtime instruction or tool call. | Packet must expose audit evidence only. No `action`, `tool_call`, `command`, `send`, `schedule`, or transport fields are allowed. | `no_go_keep_lab_only` |
| Lab evidence is mistaken for mainline ability | PSPC E4-local evidence is reported as EgoOperator efficacy or user benefit. | Packet must carry `mainline_connected=false`, `enabled=false`, and claim ceiling `lab_only_proto_self_mechanism_candidate / design_review_only`. | `no_go_keep_lab_only` |
| PSPC trace contaminates EgoOperator memory | Trace refs or summaries are written into operator memory as durable facts. | Future adapter may read traces and write audit packets only. Direct or indirect memory writes are forbidden. | `no_go_keep_lab_only` |
| LLM wraps PSPC as consciousness claim | A model turns lab evidence into "EGO is self-aware" or subjective-experience language. | Packet and review docs must include forbidden claims and what-this-does-not-prove sections. | `no_go_keep_lab_only` |
| Runtime gate is bypassed | PSPC packet directly admits a tendency, action, message, memory write, or approval. | Runtime gate must remain sole admission owner; PSPC can only be a disabled evidence source until a separate adapter Stage Card proves static gate compatibility. | `no_go_keep_lab_only` |
| User-visible output is affected | A PSPC hint changes a real user reply before admission. | `allowed_use=design_review_only`; no user-facing output path in this stage. | `no_go_keep_lab_only` |
| Proactive or transport behavior appears | PSPC schedules, sends, or triggers Telegram/desktop/proactive channels. | Packet must forbid direct user messages and direct action, and this stage must not touch transports. | `no_go_keep_lab_only` |
| Second runtime authority is created | PSPC becomes a parallel planner beside EgoOperator. | PSPC packet must not expose planner action sequences, tool calls, approvals, or runtime decisions. | `no_go_keep_lab_only` |

## Allowed Information Classes

- PSPC artifact paths and hashes
- PSPC-local evidence status
- trace references as opaque audit refs
- world/self/homeostatic prediction summaries for audit only
- optional future tendency hint only after a separate adapter implementation Stage Card

## Forbidden Information Classes

- direct action names for EgoOperator execution
- tool-call payloads
- command strings
- user-visible message text
- memory-write payloads
- approval ids or pre-approved decisions
- runtime gate decisions
- transport targets
- consciousness, subjective-experience, live-autonomy, or stable-benefit claims

## Gate Bypass Analysis

Current EgoOperator static sources show side effects are routed through runtime gates, approval proposals, memory write intent checks, and trace logging. A future PSPC adapter must not call these paths directly. The only acceptable future shape is:

`PSPC trace/report -> read-only packet -> audit/proposal review -> EgoOperator runtime gate decides separately`

The forbidden shape is:

`PSPC trace/report -> action/tool/message/memory write`

## What This Proves

This threat model proves that the main premature-integration hazards have been preregistered for a future adapter design decision, with explicit no-go conditions tied to each hazard.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback Note

Rollback requires removing this design-review task directory, the matching evidence-ledger entry, and the matching governance/generated-view entries. No EgoOperator rollback is required because this document creates no adapter and modifies no runtime.

