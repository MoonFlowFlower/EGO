# PSPC Read-Only Adapter Implementation v0 Rollback

## Scope

This rollback plan applies to the Stage Card package only. Since this stage must not create an adapter or modify EgoOperator, rollback must not require runtime repair.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`

## Rollback Trigger

Rollback this stage if:

- an adapter file is created
- EgoOperator runtime/gate/memory/approval/human-trial/transport files are modified
- adapter registration is added
- PSPC can affect user-visible output
- PSPC can write memory
- PSPC can bypass gate or approval
- `mainline_connected=true`
- `enabled=true`
- claim language upgrades PSPC beyond lab/design evidence

## Rollback Steps

1. Remove `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`.
2. Remove the matching evidence-ledger entry.
3. Remove the matching `pspc_read_only_adapter_implementation_v0` workstream/status entry.
4. Regenerate derived program-state and route-convergence views.
5. Re-run closeout boundary checks proving no adapter file exists and no EgoOperator runtime files changed.

## Forbidden Rollback Dependencies

Rollback must not depend on:

- editing EgoOperator runtime files
- deleting runtime registry entries
- clearing EgoOperator memory
- undoing user-visible messages
- reverting transport/proactive side effects

If any of those are required, this stage violated its boundary.

## What This Proves

This rollback plan proves that the Stage Card package is reversible as docs/governance only and that any need for runtime rollback would be evidence of boundary failure.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, adapter skeleton existence, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback

Rollback this stage by removing `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`, its evidence-ledger entry, and matching governance/generated-view entries. No EgoOperator rollback is required because this stage creates no adapter and modifies no runtime.

