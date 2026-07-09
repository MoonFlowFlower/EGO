# EGO-K0 Reference Kernel Contract

Contract id: `ego_k0.reference_kernel.v1`

## Required callable surface

```text
initialize(config, seed) -> serialized_state
propose(serialized_state, observation, legal_actions) -> proposal, next_state
observe_outcome(serialized_state, transition) -> next_state, update_record
train_replay(serialized_state, replay_batch_refs) -> next_state, update_record
```

The interface is task-agnostic. The kernel receives only typed observations,
legal actions, feedback, and declared state/replay references. `family_id`,
split, sequence position, hidden rule, label, oracle fields, renderer state, and
evaluator verdicts are forbidden.

## Mandatory learned core

- action-conditioned outcome predictor with real seeded fit/update;
- serialized parameters and optimizer state;
- online update from legal outcome feedback;
- bounded replay buffer and replay-training update;
- horizon `H=1-2` constrained planner using predictor outputs;
- direct structured memory/state features in action scoring;
- one typed action-proposal path with `execution_authority=false`.

The predictor cannot be a static verdict table, rule id, task switch, or logged
decoration. The planner cannot fall back to an untraced selector.

## State and authority boundary

State contains only versioned canonical records and declared hashes. The kernel
does not own environment effects, persistence adapters, UI, LLM, network,
runtime registration, safety/permission grants, or execution. Adapters cannot
mutate parameters/state except through the callable surface.

Dev task adapters and public-dev fixture/smoke manifests live under
`scripts/ego_k0_reference_dev/`, outside the wheel, and are byte-pinned by the
computed H0 prerequisite report. They may not read the ITL working tree.

## Memory and replay ceiling

K0 memory means structured conditioning/use with provenance. It does not include
a learned memory-write policy. Replay is replay training; no consolidation claim
is permitted. Both are serialized and intervention-addressable.

## Required load-bearing checks

- no-update;
- shuffled outcome;
- predictor checkpoint swap/counterfactual;
- planner bypass;
- replay-off/corruption;
- memory read-off/source deletion;
- fresh-process replay from state + observation.

Dev checks produce smoke evidence only. Formal component states are forbidden.
Each smoke subclaim is conditional on its own directional check; a negative or
unrun replay/memory arm cannot be included in a combined load-bearing claim.

K0-R starts only after the callable prerequisite verifier proves parent
ancestry, Foundation acceptance/regression hashes, H0 acceptance/status/hashes,
public-dev fixture/smoke hashes, and heldout denial. Manual readback edits have
no authority.

## Packaging boundary

The later wheel may include this kernel code and core contracts. It must exclude
SQLite/product adapters, UI/runtime code, ITL generators/evaluators, dev fixtures,
and heldout data. K0-R itself does not build or publish a wheel.

## Claim ceiling

Reference implementation and dev-only load-bearing smoke evidence. No formal
learning, replay, memory, transfer, specialness, agency, subjectivity, or
mainline claim.
