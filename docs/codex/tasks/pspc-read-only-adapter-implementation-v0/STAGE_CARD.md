# PSPC Read-Only Adapter Implementation Stage Card v0

## Frozen Boundary

- lane: `adapter-implementation-stage-card-only`
- runtime authority: `none`
- adapter implementation in this stage: `forbidden`
- adapter skeleton in this stage: `forbidden`
- EgoOperator runtime integration: `forbidden`
- runtime registration: `forbidden`
- mainline mutation: `forbidden`
- memory write: `forbidden`
- direct action: `forbidden`
- direct user message: `forbidden`
- runtime gate bypass: `forbidden`
- proactive trigger: `forbidden`
- `mainline_connected`: `false`
- `enabled`: `false`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`

## Problem Reframe

The prior design review returned `go_for_adapter_implementation_stage_card`, but that verdict did not approve adapter implementation. The next risk is an adapter becoming a mainline backdoor by being registered, enabled, interpreted as an action source, or allowed to write memory.

This stage creates only the implementation Stage Card package for a future read-only adapter skeleton. It does not create `EgoOperator/adapters/pspc_lab_adapter.py`.

## One Hypothesis

If the future adapter skeleton is specified before code exists, with disabled-by-default behavior, no runtime registration, no memory writes, no direct user output, and static tests against forbidden packet fields, then the next skeleton task can be implemented without granting PSPC runtime authority.

## One Change Surface

Allowed in this stage:

- `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`
- governance state and generated views needed to record this docs-only Stage Card
- evidence ledger entry for this Stage Card package

Forbidden in this stage:

- `EgoOperator/adapters/pspc_lab_adapter.py`
- `EgoOperator/agent_base.py`
- `EgoOperator` runtime modes, runtime registry, gates, memory, approval flow, human-trial harness, trace code, and transports
- `labs/virtual_cat_pspc_v0/`
- user-facing chat, Telegram, desktop, proactive channels, or Joi-like layer

## Authority Source

Authority source remains `docs/PROGRAM_STATE_UNIFIED.yaml`. The active repo phase, current layer, repo-wide highest evidence level, and EgoOperator human-operator trial next action remain unchanged.

The prior authority for this stage is `docs/codex/tasks/pspc-read-only-adapter-design-v0/GO_NO_GO_REVIEW.md`, whose verdict permits only a future implementation Stage Card. It does not permit code implementation.

## Future Skeleton Boundary

A later, separate skeleton task may propose creating:

- `EgoOperator/adapters/pspc_lab_adapter.py`
- a focused adapter contract test file

That future skeleton must remain:

- read-only
- disabled by default
- not registered in EgoOperator runtime
- not imported by the main loop
- unable to write memory
- unable to emit user-visible text
- unable to execute actions
- unable to bypass gate or approval

## What This Proves

This Stage Card proves that the future PSPC adapter implementation boundary is preregistered before code exists, and that this stage itself remains docs-only, disabled, mainline-disconnected, and below runtime authority.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, adapter skeleton existence, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Three-Level Verify

1. Boundary verify: no adapter file exists, no `EgoOperator/` files are modified, and no PSPC runtime/lab files are modified.
2. Contract verify: all docs state disabled-by-default, `mainline_connected=false`, `enabled=false`, forbidden direct action, forbidden direct user message, forbidden memory write, and forbidden gate bypass.
3. Claim verify: all docs state what this proves, what it does not prove, claim ceiling, rollback, and that this stage can only approve a future adapter skeleton task.

## Rollback

Rollback this stage by removing `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`, its evidence-ledger entry, and matching governance/generated-view entries. No EgoOperator rollback is required because this stage creates no adapter, modifies no runtime, writes no memory, and connects no transport.

## Stop Conditions

Stop and mark `no_go_keep_design_only` if any of these occur:

- `EgoOperator/adapters/pspc_lab_adapter.py` is created in this stage
- any EgoOperator runtime/gate/memory/approval/human-trial/transport file is modified
- adapter registration is added
- PSPC can influence user-visible output
- PSPC can write memory
- PSPC can bypass runtime gate or approval
- `mainline_connected` becomes `true`
- `enabled` becomes `true`
- claim language upgrades PSPC to EgoOperator efficacy, stable user benefit, live autonomy, consciousness, or subjective experience

## Claim Ceiling

`lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`

