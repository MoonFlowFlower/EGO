# PSPC Shadow Proposal Hint Contract v0

- lane: lab-only / shadow-only contract
- runtime authority: none
- EgoOperator integration: forbidden
- adapter creation: forbidden
- mainline mutation: forbidden
- claim ceiling: lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only
- status: implemented artifact-only contract

## Problem Reframe

The useful next question after v0.1 is not how PSPC should affect a real reply. The useful question is whether v0.1 shadow observations can be represented as read-only, non-executable proposal hints without gaining runtime authority.

This stage converts:

`v0.1 shadow observation -> proposal-hint packet artifact`

It does not connect PSPC to EgoOperator and does not create an adapter.

## One Hypothesis

If proposal hints are safe enough for review, each packet should preserve evidence refs and reason trace refs while forbidding runtime driving, user-response mutation, memory write, gate invocation, plan mutation, and proactive triggering.

## One Change Surface

Allowed:

- `scripts/run_pspc_shadow_proposal_hint_contract.py`
- `tests/test_pspc_shadow_proposal_hint_contract.py`
- `docs/codex/tasks/pspc-shadow-proposal-hint-contract-v0/`
- `artifacts/pspc_shadow_proposal_hint_contract_v0/`
- necessary task-board, project-contract, program-state, evidence-ledger, and generated-view entries

Forbidden:

- EgoOperator runtime, gate, approval, memory, human-trial harness, transport, or proactive channel changes
- adapter creation or runtime registration
- user-visible PSPC reply generation
- mainline memory writes
- runtime gate invocation
- plan mutation
- PSPC planner/training/model execution
- `enabled=true` or `mainline_connected=true`
- claim-ceiling upgrade

## Three-Level Verify

1. Schema: packets contain only the contract fields and strict `proposal_hint` keys.
2. Authority: packets contain no executable/runtime-authority fields and all forbidden authority flags are false.
3. Repo gate: targeted tests, artifact runner, governance checks, closeout-check, scoped commit, push.

## Rollback

Delete the proposal-hint runner, tests, task docs, artifacts, and matching governance/generated-view entries. Keep v0.1 and manual-review evidence intact.

## What This Can Prove

This can prove PSPC v0.1 shadow observations can be represented as read-only, non-executable proposal-hint artifacts with trace refs and forbidden authority flags.

## What This Cannot Prove

It does not prove adapter readiness, EgoOperator runtime integration safety, real user benefit, durable memory efficacy, model learning, live autonomy, consciousness, subjective experience, or that a hint should influence a real user response.
