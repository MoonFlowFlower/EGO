# EGO-K0 Foundation Trace/Replay Contract

Contract id: `ego_k0.trace_replay.v1`

Parent task: `EGO-K0-FOUNDATION-001A`

## Canonical trace row

The package owns one versioned row schema. Names matching historical
`kernel_trace_v0` semantics are retained; divergence is explicit rather than
silently creating a second meaning.

```text
schema_version
task_id
run_id
episode_id
step_id
state_before_hash
observation
observation_source_refs
event_sequence_before
memory_read_refs
action_candidates
prediction                 # nullable in Foundation
decision_factors
selected_action_proposal
feedback                   # nullable in Foundation
prediction_error           # nullable in Foundation
update_events
replay_batch_refs
state_after_hash
event_sequence_after
component_attribution
seed_context
code_path_hash
contract_hash
```

`selected_action_proposal.execution_authority` is always `false` in Foundation.
`family_id`, split identity, sequence position, heldout labels, and evaluator
verdicts are forbidden kernel/trace inputs; an evaluator may add them only in a
separate report namespace.

## Canonicalization

- UTF-8 JSON, sorted object keys, compact separators, no NaN/Infinity.
- Integer step/event sequence; finite numeric values only.
- Hashes are SHA-256 over schema-versioned canonical bytes.
- All RNG seeds and draw counters used by the probe are serialized.
- Database row ids, wall-clock time, absolute paths, and process ids cannot enter
  state/action hashes.

## Replay definition

Valid replay performs:

```text
checkpoint + ordered source events + observation
  -> restore state
  -> recompute candidates/proposal
  -> recompute update events and next state
  -> compare canonical proposal and state hashes
```

The replay path must call the same proposal/update functions used by the source
run. Reading a stored action, copying a stored next state, or comparing only a
stored digest is invalid.

Required modes:

1. full fresh-process replay from tick 0, twice;
2. mid-chain resume from a persisted checkpoint;
3. replay after removal of stored action fields;
4. cloned-store event deletion/alteration intervention;
5. corrupt-hash detector positive control.

## Computed provenance

Every replay report records:

```text
producer_function
input_artifact_hashes
task_id / run_id / episode_ids / seed_context
aggregation_rule
code_path_hash
contract_hash
parent_commit
mismatch rows and reasons
```

No report may contain a hand-authored pass field that was not derived from the
callable replay comparison.

## Acceptance semantics

- Untampered fresh replay and resume: zero proposal/state mismatches.
- Removing stored actions: replay still succeeds by recomputation.
- Altering a source event: detector fires or recomputed chain diverges at/after
  the intervention.
- Corrupting a state/trace hash: detector fires.
- A blind positive control produces
  `foundation_instrument_invalid_<detector>`, never pass.

## Claim ceiling

Trace/replay determinism and detector sensitivity on the Foundation probe only.
This is not mechanism replay evidence and proves no learning, model utility,
memory contribution, transfer, initiative, or mainline effect.
