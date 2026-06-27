# EGO-FS-115: EgoOperator Operation Learning Gate v0

## Problem Definition

Before adding any proactive communication path, EgoOperator needs a default-off
operation-learning gate that can consume reviewed operator evidence and produce
reviewable learning candidates without mutating core memory, default runtime
behavior, files, tools, network, or external messaging.

The first implementation slice adds a default-off, task-local candidate runner.
It does not enable the gate in the runtime and does not authorize memory,
tooling, proactive communication, scheduler, or transport effects.

## Current Stage / Layer

- current_layer: `engineering implementation / operation learning candidate runner`
- mainline target: `EgoOperator proposal -> runtime gate -> trace path`
- mainline integration status: `not_connected_to_default_runtime`
- enabled status: `not_enabled`
- real trigger evidence: `explicit_cli_artifact_runner_only`

## Mainline Target

Future implementation should attach to the current EgoOperator runtime as a
default-off review path after evidence import, not as a second runtime and not
as a keyword/template fallback.

The target flow is:

1. Load an accepted human-review evidence packet.
2. Load a selected-source desktop trigger report with a validated three-source
   capture manifest and desktop trigger contract.
3. Recompute admission checks from callable code.
4. Emit operation-learning candidate records for human review only.
5. Block all memory promotion, file/tool/network effects, proactive sends, and
   default-runtime changes unless a later task explicitly adds and verifies
   those gates.

## Enabled-State Requirement

The gate must be disabled by default. A future implementation may run only from
an explicit CLI flag or task-local runner. No ordinary EgoOperator conversation,
desktop chat turn, startup hook, timer, scheduler, memory update, or subagent
route may invoke it by default.

## Real-Trigger Evidence Requirement

The implementation slice has only explicit local CLI runner evidence.

A future implementation cannot pass unless it records all of the following:

- producer function and code path hash for every admission decision;
- input artifact paths and hashes;
- selected scenario or row IDs;
- run ID;
- explicit disabled/default-off state;
- emitted candidate IDs;
- proof that no file/tool/network/message/memory side effect executed.

## Hypothesis

A default-off operation-learning gate can convert human-reviewed trial evidence
and selected-source desktop-trigger evidence into reviewable operation-learning
candidates while preserving authority boundaries and avoiding premature
proactive behavior.

## Strongest Baseline

The strongest baseline is no learning gate: keep human-trial review and
selected-source capture artifacts as separate evidence, and require a human to
manually author the next runtime task. The new gate is worthwhile only if it
adds traceable candidate generation without relaxing evidence or authority
boundaries.

## Strongest Invalidity Reason

The task is invalid if imported evidence is still unreviewed, if capture
contracts are only reported but not recomputed, if candidate generation writes
state directly, or if the gate becomes a hidden path to proactive communication.

## Falsification Signal

The framing is falsified if a future prototype can produce candidates from an
unedited human-review template, a stale/two-source manifest, a report lacking
desktop trigger contract fields, or a direct runtime call without IPC trigger
provenance.

## Insufficient Evidence

The following remain insufficient:

- a unit test that only asserts a static verdict;
- a candidate JSON file without callable provenance;
- a desktop trigger smoke without replay/admission checks;
- a scripted score without human-review clearance;
- any report that omits negative controls for unreviewed or stale inputs.

## Mechanism Versus Resemblance

This task tests evidence hygiene and authority routing for operation-learning
candidate generation. It does not test proactive agency, stable user benefit,
durable memory efficacy, emotion, subjectivity, or consciousness.

## Risk Checks

- hard-coding: admission must not rely on static pass strings.
- local optimum: candidate generation must not become a template branch.
- Zeno trap: do not keep repairing review/import formats without producing
  discriminative candidate admission checks.
- evidence leakage: no raw source text from capture cache may be staged.
- weak baseline: compare against the no-gate manual-authoring baseline.
- schema split: human review, trigger report, and gate candidate schemas must
  have one declared authority each.
- second logic path: no alternate memory/subagent/tool path may bypass the gate.
- replay weakness: selected-source evidence must not be treated as behavior
  replay unless a separate replay task authorizes it.
- claim inflation: task-card acceptance does not imply gate implementation.

## Ablation Requirement

Future implementation must include negative controls for:

- unedited human-review template;
- high imported scores with `human_review_required=true`;
- stale or two-source capture manifest;
- missing desktop trigger contract;
- missing future trace fields;
- direct call without IPC entrypoint provenance.

## Trace / Replay Requirement

Trace is required for future candidate generation. Replay is not required in
this task-card slice. If the future implementation claims replay, it must open a
separate replay contract and recompute behavior from serialized state plus
observation.

## Computed-Evidence Provenance Gate

Future evidence-bearing output must record:

- `producer_function`;
- input artifact paths and hashes;
- `run_id`;
- scenario, source row, or episode IDs;
- aggregation/admission rule;
- code path hash;
- side-effect absence report;
- negative-control outcomes.

No literal verdict dictionary or hand-written score may satisfy the gate.

## Acceptance Gate

This implementation slice is accepted only if:

- the task keeps operation-learning before proactive communication;
- the runner remains default-off and task-local;
- the runner requires human-review clearance before learning input admission;
- the runner requires three-source capture manifest and desktop trigger contract
  validation before selected-source input admission;
- the runner forbids memory promotion, tool calls, file writes, network calls,
  message sends, timers, schedulers, and default runtime enablement;
- tests cover negative controls and provenance requirements;
- `Tasks/TASK_BOARD.yaml` registers the runner without claiming runtime integration;
- no `docs/PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger claim is upgraded.

## Claim Ceiling

`default_off_operation_learning_candidate_runner_only`.

This task does not prove operation learning effectiveness, proactive
communication readiness, runtime integration safety, stable operator benefit,
durable memory efficacy, live autonomy, subjectivity, emotion, or consciousness.

## Stop Condition

Stop before implementation if any authority source conflicts, if human-review
evidence remains unreviewed, if selected-source trigger evidence is missing its
three-source/desktop-trigger contract, or if the next step would enable a
runtime/proactive side effect.

## Rollback Plan

Delete `scripts/codex/run_egooperator_operation_learning_gate.py`,
`scripts/tests/test_run_egooperator_operation_learning_gate.py`,
`artifacts/egooperator_operation_learning_gate_v0/`, and
`docs/codex/tasks/egooperator-operation-learning-gate-v0/`; remove `EGO-FS-115`
from `Tasks/TASK_BOARD.yaml`; regenerate derived task views if they changed; and
leave human-trial and selected-source evidence at their prior claim ceilings.

## Expected Changed Files

Current implementation slice:

- `docs/codex/tasks/egooperator-operation-learning-gate-v0/SPEC.md`
- `docs/codex/tasks/egooperator-operation-learning-gate-v0/PLAN.md`
- `docs/codex/tasks/egooperator-operation-learning-gate-v0/IMPLEMENT.md`
- `docs/codex/tasks/egooperator-operation-learning-gate-v0/STATUS.md`
- `docs/codex/tasks/egooperator-operation-learning-gate-v0/MUTATION_SCOPE.yaml`
- `Tasks/TASK_BOARD.yaml`
- `scripts/codex/run_egooperator_operation_learning_gate.py`
- `scripts/tests/test_run_egooperator_operation_learning_gate.py`
- `artifacts/egooperator_operation_learning_gate_v0/`

Future implementation, if separately authorized, may touch EgoOperator runtime
or harness files only after a new implementation plan and verification scope.

## Forbidden Changes

- no proactive communication implementation;
- no default runtime enablement;
- no memory promotion;
- no file/tool/network/message side effects;
- no scheduler/timer/daemon;
- no legacy EgoCore/OpenEmotion runtime restoration;
- no raw source text staging;
- no program-state or evidence-ledger upgrade;
- no push, tag, or remote anchor.

## Auto-Remote-Anchor Decision

`forbidden`.
