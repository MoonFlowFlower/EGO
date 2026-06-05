# PSPC Shadow Proposal Hint Contract v0 Acceptance

## Required Checks

- The converter reads `artifacts/pspc_sequence_experience_eval_v0_1/sequence_experience_eval_v0_1.json`.
- It writes `artifacts/pspc_shadow_proposal_hint_contract_v0/proposal_hint_contract.json`.
- It writes `artifacts/pspc_shadow_proposal_hint_contract_v0/PROPOSAL_HINT_CONTRACT_REPORT.md`.
- Each packet validates against the required packet schema.
- Each packet has `packet_type=shadow_proposal_hint`.
- Each packet has `enabled=false`, `mainline_connected=false`, and `runtime_authority=none`.
- Each packet preserves reason trace refs.
- Each packet preserves `PSPC-SHADOW-HOOK-007_human_required_preserved`.
- Forbidden authority flags are all false.
- Runtime-authority fields are absent.
- Claim ceiling remains `lab_only_proto_self_mechanism_candidate / sequence_experience_eval_only`.

## Forbidden

- No EgoOperator runtime, gate, memory, approval, human-trial harness, transport, or proactive channel changes.
- No adapter creation.
- No user response mutation.
- No memory write.
- No gate invocation.
- No plan mutation.
- No proactive trigger.
- No planner/training/model execution.

## Acceptance Verdicts

Pass verdict:

`proposal_hint_contract_pass__manual_review_only`

Fail verdict:

`no_go_keep_shadow_only_for_proposal_hint_contract`

Passing this stage may only allow manual review to consider a future product-only local behavior prototype design. It does not allow EgoOperator adapter or runtime integration.
