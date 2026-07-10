# EGO-K0-FOUNDATION-READY-SYNC-001A — Cross-Repo Authority Synchronization

Status: EXECUTABLE FOR AUTHORITY SYNCHRONIZATION ONLY / STOP AFTER SYNC / NO
FOUNDATION IMPLEMENTATION

Auto-Remote-Anchor: forbidden

## Problem definition

Ego's local K0 authority mirror is stale. The canonical ITL route now authorizes
exactly `EGO-K0-FOUNDATION-001A`, while Ego's
`docs/PROGRAM_STATE_UNIFIED.yaml` still says that the K0 route is registered and
that a READY transition is required. Ego's session guard treats that file as
the current Ego authority, so Foundation implementation must not start while
the local authority still forbids it.

This task synchronizes only Ego's canonical program state and mechanically
generated views with the pinned ITL route. It does not implement, enable, run,
or connect Foundation.

## Current layer and stage

- Current layer: engineering evidence-governance / cross-repo route
  synchronization.
- Current stage: local authority synchronization before a separately authorized
  Foundation implementation session.
- Mainline target: none. `EgoOperator` remains the active default mainline and
  execution owner.
- Mechanism test status: none. This task tests governance/readback consistency,
  not a mechanism hypothesis or behavioral resemblance.

## Enabled-state and real-trigger distinction

- Foundation implementation authorization: `true` after successful sync.
- Foundation package/runtime enabled: `false`.
- `mainline_connected=false`.
- `runtime_authority=none`.
- Foundation evidence level remains `E0`.
- Real-trigger evidence requirement for this task: callable Ego generators,
  integrity checks, route-convergence checks, mainline-clarity checks, repo
  verification, bootstrap, and mutation-scope closeout must recompute the same
  Foundation-only READY readback from the edited canonical state.
- Real Foundation trigger evidence: absent and forbidden in this task.

## Canonical ITL authority pins

Read-only dependency:
`D:/Project/AIProject/MyProject/intelligence-theory-lab`

- Branch: `codex/meta-theory-scaffold`.
- Closure/readback commit:
  `07c0f1f85a3c855511ff1610ec9629f8e94e89b1`.
- Route id: `K0-DUAL-TRACK-SUPERSESSION-001A`.
- Current state: `READY_TO_IMPLEMENT`.
- Phase:
  `CODE_FIRST_H0_PREBANK_PRECONDITION_FAILED_SCIENCE_BRANCH_CLOSED`.
- Authorized implementation targets exactly:
  `EGO-K0-FOUNDATION-001A`.
- Route-state path:
  `artifacts/ROUTE-STATE-MACHINE-001A/routes/K0-DUAL-TRACK-SUPERSESSION-001A/state.json`.
- Route-state Git blob:
  `5afe5060fa67caf7aaebfc92ba677d6fa9ee16e3`.
- Route-state SHA-256:
  `ba97b56a971c3325b2862b00ff564f149df46dba178af61a780632f456c69c37`.
- Validation-report Git blob:
  `bc359eab97c6faff19a754844296491ff3d8f6ba`.
- Ledger requirement: exactly one `L-026`.
- Closure-event requirement: exactly one
  `h0_code_first_prebank_precondition_failed_science_branch_closed`.
- Authorization truth: Foundation implementation `true`; code-first prebank,
  H0, Reference Kernel/K0-R, H1, Freeze, Formal, scoring, experiment execution,
  EGO mainline/runtime, and remote anchor `false`.

Ego child-card pins:

- Foundation card commit:
  `13bd9268993f74a41b4cc219855761681ab12b66`.
- Foundation stage-card Git blob:
  `f100d78e48b8d9b21327ed86a5fb35305d11d534`.
- Reference Kernel card commit:
  `0f043254710b47700f2088213232aba777bd3f46`.

Material drift in any required branch, commit, cleanliness, ahead/behind count,
pin, route state, target set, or false authorization is a hard stop.

## Hypothesis

If Ego's single canonical program-state authority records the pinned ITL
Foundation-only READY boundary and the existing generators recompute all derived
views from it, then Ego bootstrap and route validators will permit only a future
separate Foundation implementation while keeping Foundation disabled,
non-mainline, and without runtime authority.

## Strongest baseline and invalidity risk

The strongest baseline explanation is that the live ITL authorization is
sufficient and Ego's stale mirror is merely documentation. That baseline is
insufficient because Ego's `AGENTS.md` and session guard treat
`docs/PROGRAM_STATE_UNIFIED.yaml` as the current Ego authority. Bypassing it
would create a cross-repo authority disagreement and a second execution path.

The strongest invalidity risk is authorization inflation: copying the ITL state
wholesale, enabling Foundation, or accidentally authorizing H0/K0-R/H1/Freeze/
Formal. Another invalidity risk is changing route-convergence logic to make a
new state appear valid rather than expressing it through the existing canonical
schema and generators.

Falsifier: if the pre-edit Ego bootstrap already reports the current
Foundation-only READY authority, this sync framing is stale and the task must
stop. Evidence still insufficient after a successful sync: generated documents
and local governance checks cannot show Foundation engineering, a real
Foundation trigger, persistence/replay behavior, mechanism validity, or
mainline effect.

## Collision record

### Candidate A — execute Foundation directly from live ITL authority

- Evidence produced: implementation artifacts under a valid external route.
- Strongest cheap match: bypass Ego's local authority and rely on the ITL text.
- Leakage/hard-coding risk: cross-repo authority disagreement and an undeclared
  second execution path.
- Smallest falsifying test: Ego bootstrap still says implementation is
  unauthorized.
- Expected failure mode: implementation begins while Ego's canonical source
  explicitly denies it.
- Decision: reject.

### Candidate B — copy ITL state into Ego or authorize H0/K0-R

- Evidence produced: matching-looking route fields.
- Strongest cheap match: duplicate the external schema and broaden booleans.
- Leakage/hard-coding risk: schema duplication and authorization inflation.
- Smallest falsifying test: the authorized target set contains anything other
  than `EGO-K0-FOUNDATION-001A`.
- Expected failure mode: stale mirrors diverge again or blocked children become
  executable.
- Decision: reject.

### Candidate C — synchronize only Ego authority and generated views

- Evidence produced: callable generators and validators converge on the pinned
  Foundation-only READY boundary.
- Strongest cheap match: hand-edit generated prose without changing canonical
  state.
- Leakage/hard-coding risk: generator bypass or a second route-convergence logic
  path.
- Smallest falsifying test: regenerate views and observe the READY readback
  disappear or broaden.
- Expected failure mode: the existing generator cannot express the required
  state without route-logic changes.
- Decision: select; stop rather than change route-convergence logic if that
  failure occurs.

## Ablation/contrast requirement

No mechanism ablation or experiment rerun is authorized. The governance contrast
is the callable bootstrap before and after synchronization:

1. before: stale `REGISTERED / READY transition required` wording and Foundation
   implementation unauthorized;
2. after: only Foundation authorized for a future implementation session while
   runtime enabled, mainline connection, and runtime authority remain false,
   false, and none.

This contrast is route-governance evidence only.

## Trace/readback requirement

- Preserve the pre-edit bootstrap readback.
- Regenerate views only through
  `scripts/codex/generate_program_state_views.py` and
  `scripts/codex/generate_route_convergence_views.py`.
- Run callable integrity, convergence, mainline-clarity, fast-repo, bootstrap,
  and scoped-closeout checks.
- Inspect staged paths and committed Git objects for both phases.
- Confirm no Foundation implementation/evidence path appears, no ITL path
  changes, and no task-board/evidence-ledger path changes.

Replay of Foundation behavior is not applicable and is forbidden because no
Foundation implementation or runtime trigger may occur in this task.

## Computed-provenance requirement

All acceptance readbacks must come from callable existing functions and Git
object/hash commands over named inputs. A hand-written pass, static verdict, or
edited generated view is insufficient. Required producers/inputs include:

- ITL `route_state_machine_001a.validator.build_status` and
  `build_dashboard` over the pinned serialized route artifacts;
- Ego canonical generators over `docs/PROGRAM_STATE_UNIFIED.yaml`;
- Ego integrity, route-convergence, mainline-clarity, fast-repo, bootstrap, and
  mutation-scope closeout entrypoints;
- Git object readback for the task-card and program-state sync commits/blobs.

No score, baseline metric, ablation metric, or mechanism verdict is produced by
this task.

## Acceptance gate

All conditions must hold:

1. Ego canonical state pins ITL commit
   `07c0f1f85a3c855511ff1610ec9629f8e94e89b1`, route-state blob
   `5afe5060fa67caf7aaebfc92ba677d6fa9ee16e3`, and route-state SHA-256
   `ba97b56a971c3325b2862b00ff564f149df46dba178af61a780632f456c69c37`.
2. Foundation implementation authorization is true.
3. Foundation runtime enabled remains false.
4. `mainline_connected=false` and `runtime_authority=none` for Foundation.
5. H0/K0-R/H1/Freeze/Formal remain false/blocked and H0 remains
   `closed_pre_run_implementation_defect / NOT_TESTED`.
6. EgoOperator remains the active default and the global `E3` ceiling, closed
   R-track, evidence ledger, and task board are unchanged.
7. Foundation implementation/evidence paths remain absent.
8. No ITL file is modified.
9. Existing canonical generators express the state without modifying
   `scripts/codex/route_convergence_common.py` or adding a second logic path.
10. Program-state integrity, route convergence, mainline clarity, fast verify,
    bootstrap, and scoped closeout pass.
11. Each phase changes and commits only its declared paths; final worktree and
    index are clean.
12. No push, tag, or remote-anchor action occurs.

Acceptance verdict: `EGO_K0_FOUNDATION_READY_AUTHORITY_SYNCED`.

## Claim ceiling

Local cross-repo Foundation READY authority synchronization only. The result may
say that Foundation implementation is authorized for a separate session while
the Foundation package/runtime is disabled, non-mainline, has no runtime
authority, and has no trigger evidence. It may not claim Foundation engineering
passed, Foundation is enabled/live/integrated, mechanism validity, learning,
memory/replay efficacy, agency, autonomy, subjectivity, consciousness, stable
user benefit, EGO readiness, companion readiness, production readiness, or
mainline effect.

## Stop conditions

Stop without repair if:

- either repo's branch, HEAD, cleanliness, ahead/behind count, pins, or route
  state drifts materially;
- ITL no longer authorizes exactly Foundation;
- the pre-edit Ego bootstrap already has the current Foundation-only READY
  authority;
- Foundation implementation begins or any package, adapter, test, runner, or
  Foundation evidence artifact appears;
- H0/K0-R/H1/Freeze/Formal becomes true;
- `EgoOperator/**`, `EgoDesktop/**`, evidence-ledger, task-board, or ITL paths
  would change;
- `scripts/codex/route_convergence_common.py` or any second route logic path
  would be required;
- an unexpected user change exists;
- reset, stash, rebase, amend, squash, history rewrite, push, tag, or remote
  action would be required.

## Rollback plan

Before each local commit, remove only uncommitted files/edits created in that
phase if validation fails. After a phase is committed, preserve history and use
an additive corrective commit under a separately authorized card; do not amend,
reset, rebase, or rewrite history. No runtime rollback exists because runtime
and implementation are untouched.

## Expected changed files and phase boundaries

Phase A — task-card bank, exactly:

- `docs/codex/tasks/ego-k0-foundation-ready-sync-001a/STAGE_CARD.md`
- `docs/codex/tasks/ego-k0-foundation-ready-sync-001a/MUTATION_SCOPE.yaml`

Phase B — canonical state plus actual byte-changed generated views only:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/STATUS.md`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `artifacts/reports/program_state_summary.md`

`docs/REPO_HYGIENE_POLICY.md` may be regenerated but must not be staged if its
bytes are unchanged.

## Forbidden changes

- Foundation package, adapter, runner, test, or evidence paths;
- `scripts/codex/route_convergence_common.py` or another route-logic path;
- `EgoOperator/**`, `EgoDesktop/**`, `scripts/ego_kernel/**`,
  `scripts/ego_pet/**`, or `scripts/ego_pet_capability/**`;
- `artifacts/evidence_ledger/**`, `Tasks/TASK_BOARD.yaml`, or
  `.codex/project_contract.yaml`;
- prior task cards/artifacts, any ITL path, runtime registration, UI hooks,
  memory/gate/approval/transport, proactive behavior, LLM/network/API/deployment,
  push, tag, or remote-anchor work.

## Local commit authorization

This task authorizes exactly two local commits after each phase's scoped staged
set and checks pass:

1. `docs: bank EGO K0 Foundation READY sync`
2. `governance: sync EGO K0 Foundation READY authority`

Stage only literal phase paths. `git add -A` is forbidden. Push, tag, and remote
anchor are forbidden.

## Next minimal closed-loop action

After this task reaches its acceptance verdict, stop. In a separate session,
execute only the implementation phase of `EGO-K0-FOUNDATION-001A` against the
pinned synchronized authority.

## What this does not prove

This task does not prove Foundation engineering, persistence, trace/replay
correctness, adapter conformance, learning, mechanism validity, mainline
integration, runtime enablement, a real trigger, stable user benefit, agency,
autonomy, subjectivity, consciousness, EGO readiness, companion readiness, or
production readiness.
