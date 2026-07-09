# EGO-K0 Foundation Kernel/Adapter Contract

Contract id: `ego_k0.kernel_adapter.v1`

Parent task: `EGO-K0-FOUNDATION-001A`

## Ownership boundary

The `ego_k0_kernel` package owns typed records, canonicalization, state
transition/replay orchestration, and port definitions. It owns no environment,
database, renderer, network, user channel, or operating-system effect.

Adapters live outside the wheel. They may translate external data into a typed
observation or persist package records through a port. They cannot select an
action, alter a score, mutate kernel state directly, execute an action proposal,
or reinterpret evidence.

## Required typed records

Every record carries `schema_version` and stable ids.

```text
ObservationRecord
  observation_id, episode_id, step_id, payload, source_refs

EventRecord
  event_id, episode_id, step_id, event_type, payload, provenance

KernelStateRecord
  episode_id, step_id, substates, rng_state, state_hash

ActionCandidate
  action_id, typed_parameters, admissible, constraint_reasons

ActionProposal
  selected_action_id, candidates, decision_factors, execution_authority=false

CheckpointRecord
  checkpoint_id, state, last_event_sequence, code_contract_version

AdapterCapabilityManifest
  adapter_id, readable_fields, writable_ports, forbidden_capabilities
```

Free-form renderer text is not a canonical action or state field.

## Port contract

### `EventStorePort`

The core may call only:

```text
append_events(expected_sequence, events) -> committed_sequence
read_events(episode_id, after_sequence) -> ordered events
write_checkpoint(expected_sequence, checkpoint) -> checkpoint_id
read_latest_checkpoint(episode_id) -> checkpoint | null
```

Requirements:

- append is transactional and fails closed on sequence mismatch;
- event order is explicit, monotonic, and stable;
- returned records are byte-independent copies;
- overwrite/delete is absent from the production port;
- test-only cloned-store interventions cannot mutate the source store.

The first adapter is
`scripts/ego_k0_adapters/sqlite_event_store.py`. It is outside the wheel, uses a
caller-supplied database path, and has no authority beyond this port.

### `PolicyPort`

Foundation validation may inject a deterministic probe policy through:

```text
propose(state, observation) -> ActionProposal
```

The foundation package does not ship a learned or product policy. The probe is a
test instrument and cannot execute its proposal.

### `TraceSinkPort`

Trace output is append-only and accepts only validated rows under
`ego_k0.trace.v1`. A trace sink cannot feed data back into policy/state during
the same run.

## Capability-deny list

Every adapter manifest must deny:

```text
execute_action
send_user_message
write_mainline_memory
invoke_gate_or_approval
network_or_transport
schedule_background_work
start_runtime
select_or_rescore_action
change_claim_or_verdict
read_family_or_split_identity
```

Unknown capabilities fail closed.

## Import-direction rule

Allowed:

```text
external adapter -> ego_k0_kernel ports/contracts
validator        -> adapter + ego_k0_kernel
```

Forbidden:

```text
ego_k0_kernel -> SQLite/EgoDesktop/EgoOperator/task adapter/ITL
adapter       -> policy internals
renderer      -> canonical state or evidence verdict
```

## Failure and rollback semantics

Contract/schema mismatch, duplicate event ids, sequence conflict, invalid hash,
or forbidden capability aborts before state advance. Partial commits are not
accepted. Recovery starts from the latest valid checkpoint plus committed
ordered events; it never trusts an uncommitted UI/cache copy.

## Claim ceiling

This contract establishes an engineering ownership boundary only. It does not
establish mechanism validity, durable product memory, learning, useful behavior,
initiative, autonomy, subjectivity, or mainline effect.
