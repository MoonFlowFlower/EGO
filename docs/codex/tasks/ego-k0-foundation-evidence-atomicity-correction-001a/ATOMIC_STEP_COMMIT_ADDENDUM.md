# EGO-K0 Foundation Atomic Step Commit and Evidence Producer Addendum

Addendum id: `ego_k0.foundation_atomicity_correction.v1`

Parent task: `EGO-K0-FOUNDATION-001A`

Correction task: `EGO-K0-FOUNDATION-EVIDENCE-ATOMICITY-CORRECTION-001A`

This additive addendum controls only the event/trace atomicity and callable
formal-producer gaps. All Foundation scientific/probe semantics remain frozen.

## 1. Canonical transactional trace outbox

The package `EventStorePort` adds:

```text
append_step(expected_sequence, source_event, trace_row)
  -> committed_sequence

read_trace_rows(episode_id, after_sequence)
  -> ordered canonical TraceRow values
```

For every accepted Foundation observation, the external SQLite adapter must use
one `BEGIN IMMEDIATE ... COMMIT` transaction to insert:

1. the canonical source event at `expected_sequence + 1`; and
2. one canonical trace/outbox row at the same episode and sequence.

The outbox row stores schema version, episode, step, event sequence, trace hash,
and canonical trace JSON. Its primary identity is `(episode_id, sequence)`; its
content identity is `trace_hash`. Readback reconstructs `TraceRow` from canonical
bytes and compares all stored metadata before returning an independent object.

Before either insert, the adapter validates:

- source event and trace types;
- episode, step, and sequence identity;
- trace observation equality with the source event's typed observation;
- trace `event_sequence_before/after` relation;
- current committed sequence.

Any validation, constraint, or write failure rolls back both inserts. Merely
writing trace first is forbidden because it creates the reverse orphan.

`append_events` remains only as the already banked low-level adapter conformance
surface. The canonical source execution path and evidence producer must call
`append_step`; they must not split source event and canonical trace persistence.

## 2. Non-authoritative delivery sink and typed receipt

`TraceSinkPort` remains an optional delivery surface after canonical commit. It
is not the trace authority.

- Delivery success: return the computed step normally.
- Delivery failure: raise `PostCommitTraceDeliveryError` chained from the sink
  exception.
- The error must expose `committed=true`, `episode_id`, `step_id`,
  `committed_sequence`, and `trace_hash`.
- The canonical source event and trace row remain readable from the outbox.
- The caller recovers delivery from the canonical trace row and must not replay
  the source append. A repeated append with the old expected sequence must fail
  closed.

No exception may leave the caller unable to distinguish rollback from committed
state.

## 3. Replay source

Source execution writes traces through `append_step`. Validation and replay read
the canonical rows through `read_trace_rows`; any collecting delivery sink is
only compared against canonical readback. Replay continues to call the same
proposal/update functions from serialized checkpoint plus ordered source event
and observation. The comparison fields and stored-action-removal control do not
change.

## 4. Callable evidence producer and resolver

The runner adds a callable evidence producer with separate trial and official
target controls. During this correction only the trial control may execute and
its output must live in a `TemporaryDirectory`. The official target is exactly:

```text
artifacts/ego_k0_foundation_001a/
```

The official target must not be created by this task. The output directory is
claimed once; if it already exists, the producer refuses without overwriting any
byte.

The resolver consumes the actual `per_gate_outcomes` mapping returned by the
validation runner:

```text
all engineering and integrity gates pass
  -> foundation_engineering_pass

any named detector positive-control gate is blind
  -> foundation_instrument_invalid_<detector>

otherwise, first failed gate in stable sorted order
  -> foundation_engineering_fail_<gate>
```

No literal pass dictionary or hand-edited verdict is permitted. Detector
invalidity takes precedence over ordinary failures so a blind instrument cannot
be hidden by another red gate.

The producer writes `result.json` atomically on normal pass, normal gate failure,
or caught producer exception. A caught exception additionally writes
`failure_manifest.json` atomically with exception type/message, phase, run id,
and any already verified provenance. Raw files never stand alone as an
official-looking bank without a machine result.

## 5. Formal provenance verifier

Before creating an output directory, the producer verifies:

### EGO repository

- branch `main`;
- clean worktree and index;
- implementation base commit
  `fc2c9b1fa9bc3ef010592783d0a959b2aa4485a6` exists;
- that commit's direct parent is
  `1e25ddead74da9dad810622a657d82f03564091e`;
- that commit changes exactly the banked 13 implementation paths;
- correction producer HEAD is the direct child of this correction card-bank
  commit and changes exactly the six implementation-correction paths;
- Foundation card commit/blob/raw hash and ancestry;
- correction card commit/blobs/raw hashes and ancestry;
- each executed implementation file's working SHA-256, HEAD blob id, and
  `git hash-object --path` value are equal to the verified committed bytes.

### ITL repository

- clean worktree and HEAD
  `07c0f1f85a3c855511ff1610ec9629f8e94e89b1`;
- route object
  `artifacts/ROUTE-STATE-MACHINE-001A/routes/K0-DUAL-TRACK-SUPERSESSION-001A/state.json`;
- blob `5afe5060fa67caf7aaebfc92ba677d6fa9ee16e3`;
- SHA-256
  `ba97b56a971c3325b2862b00ff564f149df46dba178af61a780632f456c69c37`;
- route state and authorization JSON permits exactly Foundation implementation,
  while H0, K0-R, H1, Freeze, Formal, experiment, scoring, runtime, remote anchor,
  and other prohibited authorities remain false.

The resulting `execution_authority_hash` hashes this verified EGO/ITL object
readback, including commit/blob identities and authorized target set. It is not a
self-description of disabled execution authority.

## 6. Frozen semantics

This correction must not change:

- `DeterministicProbePolicy` proposal/selection semantics;
- the observation or state-update formula;
- seed `1701`, episode id, four source steps, or checkpoint positions;
- stored-action-removal challenge;
- replay comparison fields;
- the original 18 gate names, calculations, or thresholds;
- Foundation claim ceiling.

Additional integrity gates may be appended for atomic transaction rollback and
post-commit sink recovery. They cannot replace or relax the original 18 gates.

## 7. Required mutation coverage

Tests must force and observe:

1. delivery-sink exception after canonical commit;
2. second SQLite write failure with zero event/trace residue;
3. canonical recovery plus retry sequence rejection;
4. replay from committed event and trace readback;
5. pass/fail/instrument-invalid resolver branches;
6. wrong Git/card/ITL pins and dirty state fail-closed;
7. producer exception still yielding `result.json` and
   `failure_manifest.json`;
8. raw working bytes versus Git object mismatch;
9. output-target overwrite refusal;
10. existing import, side-effect, capability, tamper, and stored-action controls.

## 8. Claim ceiling and stop

Claim ceiling: Foundation atomic persistence, canonical trace recovery, and
formal evidence-producer engineering only. No mechanism claim.

Stop if any formal artifact bank must be run, any scientific semantics must
change, any listed scope must widen, or any push/tag/remote anchor is required.
