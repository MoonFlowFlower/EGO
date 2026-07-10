# EGO-K0-FOUNDATION-EVIDENCE-ATOMICITY-CORRECTION-001A

Status: AUTHORIZED CORRECTION / FORMAL EVIDENCE BANK FORBIDDEN

Auto-Remote-Anchor: forbidden

## Problem definition

`EGO-K0-FOUNDATION-001A` has two computed engineering gaps:

1. `execute_observation` commits the canonical source event before invoking the
   trace sink. A throwing sink therefore returns an exception after the event
   sequence advanced, with no canonical trace recovery API and no typed commit
   receipt.
2. `run_ego_k0_foundation_validation.py` produces implementation validation but
   does not provide a callable, fail-closed formal evidence producer whose
   verdict is derived from computed gates and whose provenance verifies the Git
   and ITL authority objects.

This correction must remove the ambiguous persistence state and add the formal
producer implementation without running the official Foundation evidence bank.

## Bounded audit

- Real objective: make each Foundation step's source event and canonical trace
  one persistence unit, then make any future formal verdict reproducible from a
  callable computation path with verified source authority.
- Current layer: engineering implementation plus evidence-production integrity.
- Mechanism test: none. This tests persistence, replay, and adjudication
  plumbing, not behavioral resemblance or a mechanism hypothesis.
- Strongest baseline: the current event-first implementation plus a best-effort
  external trace sink and a separately interpreted implementation report.
- Strongest reason the task could be invalid: a nominal outbox could become a
  second trace authority, or a nominal formal producer could merely restate pins
  and hand-authored verdicts without checking Git objects and rerunning gates.
- Falsifier: any forced second write failure leaves an event or trace row; any
  sink failure leaves the caller unable to determine the committed sequence and
  canonical trace identity; or any verdict can change without changing computed
  gate outcomes.
- Evidence still insufficient: green unit tests, temporary producer trials, or
  a local correction commit do not constitute the official evidence bank and do
  not test a mechanism.

### Invalid shortcuts rejected

- Rename `implementation_validation_ok` to a Foundation pass.
- Copy raw artifacts and write a verdict separately.
- Swap event and trace write order, creating a reverse orphan.
- Catch trace delivery failure without a canonical recovery receipt.
- Weaken the contract to permit partial commit.
- Use a literal pass dictionary, self-described authority hash, unverified raw
  path, weak baseline, or stored-result replay.
- Add a second schema, persistence path, policy path, or verdict authority.

The task is not a Zeno repair: acceptance requires the two gaps to be removed in
one bounded correction. If that cannot be done without changing scientific
semantics or widening scope, stop rather than add governance layers.

## Mainline, enabled state, and real trigger

- Mainline target: none.
- `mainline_connected=false`, `enabled=false`, `runtime_authority=none`.
- No EgoOperator or EgoDesktop entrypoint is introduced.
- Engineering trigger evidence required: a typed observation must traverse the
  public Foundation execution path, commit event plus canonical trace in one
  SQLite transaction, expose the canonical row for replay, and produce a typed
  post-commit delivery receipt when a non-authoritative sink throws.
- Formal-producer trigger evidence required in this correction: only temporary
  directory trials and mutation tests. The canonical official artifact path
  must remain absent.

## Hypothesis

If the EventStorePort owns an atomic `append_step` operation and a canonical
trace outbox, while the external trace sink is explicitly post-commit and
non-authoritative, then transaction failure can roll back both records and sink
failure can be recovered without replaying the source append. If a separate
callable producer verifies Git/ITL provenance and resolves verdicts solely from
rerun gates, then a later authorized formal bank can fail closed without manual
adjudication.

## Selected architecture and authority source

`ATOMIC_STEP_COMMIT_ADDENDUM.md` is binding for this correction. The package
port contract owns the atomic operation and typed delivery error. The external
SQLite adapter owns the transaction and canonical outbox table. The validation
runner owns computed engineering gates, formal provenance verification, and
callable verdict resolution. The ITL route object remains the sole execution
authorization source.

No external trace sink, report file, test, or copied raw artifact becomes a
second authority.

## Ablation and mutation requirement

No mechanism ablation is authorized. The following callable engineering
mutations are required:

1. throwing non-authoritative trace sink;
2. forced failure on the transaction's second write;
3. wrong EGO HEAD/direct-parent pin and dirty tree;
4. wrong Foundation/correction card or ITL route object/blob/ancestry pin;
5. one forced ordinary gate failure;
6. one forced detector-positive-control blindness;
7. producer exception before normal completion;
8. raw working bytes versus Git-object mismatch;
9. existing official output target.

## Trace and replay requirement

Canonical trace rows must be read from the committed SQLite outbox in event
sequence order. Replay must continue to recompute proposal, update event, trace,
and next state from checkpoint plus serialized source event/observation. Stored
actions and stored next states remain forbidden as replay inputs. The original
replay comparison fields, policy semantics, seed, episode, and step counts are
frozen.

## Computed-evidence provenance gate

The formal producer must verify and record, through callable Git/filesystem/JSON
checks:

- implementation base commit `fc2c9b1fa9bc3ef010592783d0a959b2aa4485a6`;
- correction card commit and correction producer HEAD/direct-parent relation;
- clean EGO worktree and index on branch `main`;
- exact original 13-file implementation commit and exact six-file correction
  commit path sets;
- raw SHA-256, corresponding Git blob id, and `git hash-object --path` parity for
  executed implementation files;
- Foundation and correction card commits, blobs, hashes, and ancestry;
- ITL HEAD, clean state, route blob, raw SHA-256, route JSON, Foundation-only
  authorization, and all blocked child authorizations;
- producer function, run/episode/context/seed ids, aggregation rule,
  `code_path_hash`, contract hashes, and claim ceiling.

`execution_authority_hash` must be derived from the verified Git and ITL
authority readback, not from a literal `{execution_authority: false}` object.
Every declared context/seed is consumed by the executed probe or blocks the
claim.

## Acceptance gate

1. Source event plus canonical trace row are inserted in one SQLite transaction.
2. A forced second insert failure leaves zero event and zero trace rows.
3. Sink failure raises a typed post-commit error with `committed=true`, episode,
   step, sequence, and trace hash; the canonical pair is readable and replayable.
4. Repeating the source append after that error fails closed on sequence.
5. The original 18 gate thresholds and scientific semantics are unchanged.
6. Verdict resolution covers engineering pass, ordinary gate failure, and blind
   detector positive control from computed gate inputs.
7. Wrong Git/card/ITL/raw-byte provenance fails closed.
8. Producer exceptions still leave machine-readable `result.json` and
   `failure_manifest.json`; an existing output target is never overwritten.
9. Package import, no-side-effect, stored-action-removal, tamper, and replay
   controls continue to pass.
10. All producer trials write only to a `TemporaryDirectory`; the canonical
    `artifacts/ego_k0_foundation_001a/` path remains absent.

## Claim ceiling

Foundation atomic persistence, canonical trace recovery, and formal
evidence-producer engineering only. No mechanism claim.

## Stop conditions

Stop without widening scope if the correction requires any change to state
transition, probe policy, threshold, scenario semantics, seed/episode/step
count, replay comparison fields, EgoOperator, EgoDesktop, program state,
evidence ledger, task board, ITL, H0, K0-R, H1, Freeze, Formal, push, tag, or
remote anchor; if ambiguous partial commit remains; or if a formal verdict still
requires manual rewriting.

## Rollback plan

Before each commit, remove only newly authored task files or revert only the six
unstaged correction files with a new manual patch. After a commit, preserve the
history and use an additive correction; do not amend or rewrite prior evidence.
No runtime rollback exists because no runtime or mainline path is touched.

## Expected changed files

Card-bank phase only:

- `docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/STAGE_CARD.md`
- `docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/MUTATION_SCOPE.yaml`
- `docs/codex/tasks/ego-k0-foundation-evidence-atomicity-correction-001a/ATOMIC_STEP_COMMIT_ADDENDUM.md`

Implementation-correction phase only:

- `packages/ego_k0_kernel/src/ego_k0_kernel/__init__.py`
- `packages/ego_k0_kernel/src/ego_k0_kernel/ports.py`
- `packages/ego_k0_kernel/src/ego_k0_kernel/replay.py`
- `scripts/ego_k0_adapters/sqlite_event_store.py`
- `scripts/run_ego_k0_foundation_validation.py`
- `tests/test_ego_k0_foundation.py`

## Forbidden changes

- `artifacts/ego_k0_foundation_001a/**` and all other formal evidence paths;
- `docs/PROGRAM_STATE_UNIFIED.yaml`, `artifacts/evidence_ledger/**`,
  `Tasks/TASK_BOARD.yaml`, `.codex/project_contract.yaml`;
- all other Foundation package files;
- `EgoOperator/**`, `EgoDesktop/**`, `scripts/ego_kernel/**`, ITL files;
- policy/state/scenario/threshold/seed/replay-science semantics;
- push, tag, remote anchor, or publication.

## Commit and closeout rule

Two exact-scope local commits are authorized. `push_pending` is the only
non-blocking publication-only state. It does not make the repo globally
closeout-eligible: `repo_global_closeout_eligible=false`. Any other closeout
blocker stops the task.

## What this does not prove

This correction does not prove Foundation final acceptance, mechanism validity,
learning, memory/replay contribution, transfer, initiative, agency, autonomy,
subjectivity, consciousness, electronic life, EGO readiness, product benefit,
or mainline effect.
