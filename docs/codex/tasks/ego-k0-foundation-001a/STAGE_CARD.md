# EGO-K0-FOUNDATION-001A — Event-Sourced Kernel Foundation

Status: EXECUTABLE AFTER THIS CARD IS LOCALLY BANKED AND CANONICAL ITL ROUTE
READBACK AUTHORIZES THE FOUNDATION CHILD / DEFAULT-OFF / NOT_RUNTIME_CONNECTED /
FOUNDATION ONLY

Auto-Remote-Anchor: forbidden

## Task identity and source pins

- Task id: `EGO-K0-FOUNDATION-001A`
- Parent: `K0-DUAL-TRACK-SUPERSESSION-001A`
- Canonical parent repo: `D:/Project/AIProject/MyProject/intelligence-theory-lab`
- Canonical parent commit:
  `4e4700ca6e00b1a0e2dc3adf6a6e473b2f6ef6be`
- Parent-card path:
  `docs/codex/tasks/K0-DUAL-TRACK-SUPERSESSION-001A.md`
- Parent-card git blob: `11b0e09025d1064a1eb790f42d79f1db3c690f6d`
- Parent-card SHA-256:
  `f93af34291de34457c08ba6f705886185321635d7333d175d987470f66b7d238`
- Ego drafting base: branch `main`, commit
  `760912a415f96547fbcb50cd42e0634aa787ab62`, clean, ahead `0`, behind `0`.

The ITL parent is the sole parent authority. This card does not duplicate or
weaken it. Material source-pin drift before banking is a hard stop.

## Problem definition

K0 needs one package-owned state/event/trace/replay contract before a learned
reference kernel can exist. The current Ego R0 substrate and pet paths are
valuable historical engineering evidence, but they are closed/frozen lanes and
are not a standalone freezeable K0 package. Putting persistence or policy into
EgoDesktop would also create a second kernel and make UI state authoritative.

Build a small, import-safe package foundation plus an external SQLite event-store
adapter. The package owns only typed contracts, canonical state/event records,
ports, trace construction, and replay orchestration. SQLite is an adapter outside
the package and must never be included in the later frozen wheel.

## Current layer

Engineering implementation. This task supplies evidence hygiene and shared
infrastructure only; it does not test a mechanism hypothesis.

## Mainline, enabled state, and real trigger

- Mainline target: none.
- `mainline_connected=false`, `enabled=false`, `runtime_authority=none`.
- Entrypoint: explicit local validation CLI only.
- With no explicit invocation: no process, database, artifact, state mutation,
  network call, LLM call, timer, background loop, UI output, or external effect.
- Real trigger required for acceptance: the local validator must submit a typed
  observation through the public foundation contract, append events through the
  external event-store port, restart from persisted state, and recompute the same
  typed action proposal through replay.
- EgoOperator and EgoDesktop remain untouched and unchanged.
- Card bank alone does not override a canonical ITL route still limited to child
  banking. Execution starts only after that route's separately validated child
  authorization readback.

## Landing-only Ego route registration

The card-bank commit may add one disabled, non-mainline workstream
`k0_developmental_kernel_dual_track`, pinning the canonical ITL parent commit.
It may also add explicit generated-lane classifications: Foundation as
`supporting_active` engineering work and Reference Kernel as `parked` until its
prerequisites pass. This is repo routing only: `enabled=false`,
`mainline_connected=false`, and it must not alter the closed R-track or the
EgoOperator active-default lane.

## Hypothesis

If canonical state, append-only events, adapter capabilities, deterministic
serialization, and recomputing replay are owned by one import-safe package, then
the later K0-R learner and the ITL instrument can share a freezeable boundary
without copying policy or granting an adapter runtime authority.

## Strongest baseline and framing risk

The strongest baseline is the existing `scripts/ego_kernel/` substrate plus a
stored-action transcript or an in-memory dictionary. It can match serialization
and apparent replay on a constructed probe. Therefore this card claims no novel
mechanism or product value. Its discriminating engineering requirement is that
an external persistent event store can reconstruct state after process restart
and replay must recompute the action proposal rather than trust a stored action
or hash.

Strongest invalidity risk: persistence logic leaks into the wheel, the SQLite
adapter becomes a second state authority, or a replay verifier only compares
recorded hashes. Falsifier: deleting stored actions still permits recomputation,
whereas tampering with an input event must be detected or change the recomputed
chain. Evidence still insufficient: a passing restart/replay smoke does not show
learning, model utility, memory causality, transfer, or initiative.

## Collision record

### Candidate A — extend frozen `scripts/ego_kernel/`

- Evidence produced: another local substrate pass.
- Cheap match: the existing R0 probe already supplies it.
- Leakage/hard-coding risk: old task semantics and new K0 semantics become mixed.
- Smallest falsifier: an edit is required in a frozen R0 or pet file.
- Expected failure: historical evidence is silently re-adjudicated.

### Candidate B — put SQLite/state authority in EgoDesktop

- Evidence produced: visible persistence after restart.
- Cheap match: UI-local storage and scripted action playback.
- Leakage/hard-coding risk: maximum; renderer/adapter becomes kernel authority.
- Smallest falsifier: headless replay cannot reconstruct without Electron.
- Expected failure: product illusion and a second logic path.

### Candidate C — package contracts/core plus external adapters (selected)

- Evidence produced: headless restart, canonical trace, and recomputing replay.
- Cheap match: stored-action playback, tested as a negative control.
- Leakage/hard-coding risk: adapter capability creep.
- Smallest falsifier: core imports SQLite, EgoDesktop, EgoOperator, or task code.
- Expected failure: interface/schema mismatch, which must stop this task.

## Implementation target

Core/wheel-owned future paths:

```text
packages/ego_k0_kernel/pyproject.toml
packages/ego_k0_kernel/src/ego_k0_kernel/__init__.py
packages/ego_k0_kernel/src/ego_k0_kernel/contracts.py
packages/ego_k0_kernel/src/ego_k0_kernel/state.py
packages/ego_k0_kernel/src/ego_k0_kernel/events.py
packages/ego_k0_kernel/src/ego_k0_kernel/ports.py
packages/ego_k0_kernel/src/ego_k0_kernel/trace.py
packages/ego_k0_kernel/src/ego_k0_kernel/replay.py
packages/ego_k0_kernel/src/ego_k0_kernel/cli.py
```

Harness/adapter paths outside the wheel:

```text
scripts/ego_k0_adapters/__init__.py
scripts/ego_k0_adapters/sqlite_event_store.py
scripts/run_ego_k0_foundation_validation.py
tests/test_ego_k0_foundation.py
artifacts/ego_k0_foundation_001a/
```

The SQLite adapter implements the package port and is never imported by the
package. Database paths are caller-supplied; tests use temporary directories.

## Ablation/intervention requirement

No mechanism ablation is authorized. Engineering interventions must be callable:

1. freeze writes after a checkpoint;
2. delete or alter one source event in a cloned store;
3. remove recorded actions while retaining state plus observations;
4. corrupt one trace/state hash as a detector positive control.

These interventions validate that persistence and replay controls are live. They
carry no behavioral-mechanism interpretation.

## Trace/replay requirement

`TRACE_REPLAY_CONTRACT.md` is binding. Replay must instantiate the kernel from a
serialized checkpoint plus ordered source events/observations and recompute each
candidate/action proposal and next state. Comparing stored actions or hash chains
without recomputation is forbidden. Fresh-process replay x2 and mid-chain resume
must be deterministic. Every RNG seed/draw counter used by the probe lives in
serialized state.

## Computed-evidence provenance gate

The validation result must come from a callable producer and record:

- `producer_function`;
- input artifact hashes;
- `task_id`, `run_id`, seed/context/episode ids;
- aggregation rule;
- code-path hash;
- parent commit/card hash;
- per-gate outcomes and claim ceiling.

A literal pass dictionary, unconditional clean report, or test that only asserts
`pass` is forbidden. Tamper and stored-action-playback positive controls must
fire.

## Acceptance gate

1. Parent pins match the banked ITL object and this card is an ancestor of code.
2. Public contracts distinguish state, event, observation, action proposal,
   checkpoint, and adapter capability.
3. SQLite remains outside the package and satisfies the event-store contract.
4. Canonical serialization/hash is stable across fresh processes.
5. Restart reconstructs the same state from checkpoint plus ordered events.
6. Replay x2 plus mid-chain resume recomputes identical action/state chains.
7. Input/event tampering and stored-action playback controls are detected.
8. Static scans find no package import of SQLite, EgoDesktop, EgoOperator,
   `scripts.ego_kernel`, `scripts.ego_pet`, ITL task code, network, or LLM code.
9. Absence of explicit CLI invocation is side-effect-free.
10. Focused tests, import/compile checks, and `git diff --check` pass.

Acceptance verdict vocabulary:

- `foundation_engineering_pass`
- `foundation_engineering_fail_<gate>`
- `foundation_instrument_invalid_<detector>`

## Claim ceiling

Shared event/state contracts, external persistence-adapter conformance,
serialization, and recomputing trace/replay engineering only. No learned model,
online-learning contribution, replay-training contribution, learned memory,
transfer, specialness, initiative, agency, autonomy, subjectivity,
functional-subject status, electronic life, product benefit, EGO readiness,
companion readiness, or mainline effect.

## Stop conditions

Stop and preserve failure evidence if:

- a source pin or clean-base prerequisite drifts materially;
- implementation needs to edit/import a frozen R0, pet, EgoDesktop, or
  EgoOperator path;
- SQLite or any environment adapter enters the wheel package;
- replay cannot recompute without stored actions;
- a tamper/negative-control detector is blind;
- an undeclared RNG, second schema authority, or second policy path appears;
- any push, tag, or remote anchor is required.

## Rollback plan

Before any commit, delete only the task-authorized new paths. After a local bank,
use a new additive corrective card/commit; do not rewrite parent or historical
artifacts. No runtime rollback exists because no runtime path is touched.

## Expected changed files

The card-bank commit changes only
`docs/codex/tasks/ego-k0-foundation-001a/`. The Reference card is banked in its
own commit and under its own scope. A later, separate route-registration commit
may change only the landing workstream/override and mechanically regenerated
route views:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `scripts/codex/route_convergence_common.py`
- `docs/STATUS.md`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `docs/REPO_HYGIENE_POLICY.md`
- `artifacts/reports/program_state_summary.md`

Implementation/artifact commits later use only the implementation paths above.
Task board, evidence ledger, EgoDesktop, EgoOperator, old scripts/artifacts, and
parent ITL files remain unauthorized.

## Forbidden changes

- `scripts/ego_kernel/**`, `scripts/ego_pet/**`,
  `scripts/ego_pet_capability/**`;
- `EgoDesktop/**`, `EgoOperator/**`;
- prior task cards/configs/artifacts or any ITL file;
- runtime registration, UI hooks, mainline flags, memory/gate/approval/transport,
  proactive behavior, LLM/network/API/deployment surfaces;
- wheel/dist/freeze publication (owned by `K0-IMMUTABLE-FREEZE-001A`);
- evidence-ledger, task-board, push, or tag work; program-state/generated-view
  changes are allowed only for the exact landing registration above and later
  completion-state updates under a separately reviewed transition.

## Local commit authorization

After review, this user-authorized landing turn may make separate exact-path
commits for (1) this card bank and (2) route registration after both child-card
commits are readable. Implementation and result commits are separate phases and
must use their phase-specific paths only. Push, tag, and remote anchor remain
forbidden.

## Next action on acceptance

Foundation acceptance plus a separately banked H0 readback permits the
`EGO-K0-REFERENCE-KERNEL-001A` precondition readback. It does not itself start
K0-R, H1, freeze, formal evidence, product integration, or mainline work.

## What this does not prove

It does not prove that the later learned kernel works, that SQLite is the final
product store, that persistence changes useful behavior, or that any mechanism
proxy, transfer, initiative, self-boundary, social inference, subjectivity, or
life-like property exists.
