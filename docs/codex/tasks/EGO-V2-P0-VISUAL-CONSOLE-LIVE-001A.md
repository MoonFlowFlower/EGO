# EGO-V2-P0-VISUAL-CONSOLE-LIVE-001A

Status: `AUTHORIZED_DEFAULT_OFF_IMPLEMENTATION_PENDING`

## Problem definition

The existing local microworld has canonical controller, SQLite persistence,
recovery frames, trace, and recomputing replay, but no validated live visual
console. Implement one Chinese Tk console that renders the canonical path and
does not create a second action-selection, scoring, transition, memory,
prediction, or replay path.

## Current layer and lane

- Layer: 2, engineering implementation and integration evidence.
- Lane: local product/capability implementation.
- Mainline target: the existing `ego_life_playground_v0` local entrypoint only;
  Ego runtime/mainline is forbidden.
- Enabled-state requirement: default-off; starting the explicit Tk entrypoint is
  the only enablement.
- Real-trigger requirement: a real UI Step/Run action must invoke the canonical
  controller and produce a committed SQLite transition recovered into the same
  `RecoveryFrame` used by every panel.

## Real objective and lockstep contract

The required loop is:

```text
Tk Step/Run
  -> canonical controller.dispatch
  -> SQLite committed transition
  -> canonical recover
  -> one RecoveryFrame
  -> recovered shortest_path_coordinates waypoint animation
  -> Chinese trace-supported causal display
  -> animation completion
  -> next dispatch (Run only)
```

No next dispatch is allowed while the current committed path is animating.
Pause and Close must cancel future timers and may not create an extra dispatch.

## Hypothesis

The existing controller/recovery API is sufficient to supply a single-source
visual console without modifying engine, microworld, store, claims, launcher,
or SQLite schema.

## Strongest baseline / shortcut explanation

A frozen-trace player or a UI-local simulation can look convincing while never
calling `controller.dispatch`, committing SQLite, or following the recovered
path. It is not admissible. Tests must distinguish the real lockstep path from
this shortcut.

## Collision decision

Use the existing controller and recovery result directly. Do not duplicate
state machines, candidate scoring, translations of private/oracle data, or
replay computation. See the R1 collision record for rejected alternatives.

## UI contract

Ordinary UI text is Chinese. Technical identifiers and hashes belong only in
`高级详情`.

Each committed step shows only fields supported by the same recovery frame:

1. `步骤发生前`: 当前目标、正在执行的动作、当前预期、决策依据、关键内部状态、读取的记忆及来源。
2. `外部事件`: 发生了什么、事件中文标签、可观察线索、是否来自用户 Inject。
3. `候选与选择`: 排名、分数拆解、selected action，以及 trace 字段支持的胜出依据。
4. `结果与变化`: prediction、actual outcome、prediction error、update/consolidation、内部状态和 memory/provenance 前后值。
5. `动作连续性`: 继续、完成或被中断；中断原因；是否重新选择；新动作和目标。

Missing trace evidence must display `未记录／未知`. The UI must not describe
the data as real thought, feeling, intention, subjectivity, or agency.

## Animation contract

- The animator schedules the exact ordered coordinates from
  `RecoveryFrame.trace.world_transition.path.shortest_path_coordinates`.
- A test fixture must contain a multi-segment path and compare actual scheduled
  waypoints element by element.
- A hostile straight-line decoy must fail.
- Idle agent rendering is static: no pulse, breathing, floating, or decorative
  life-like animation.
- Pause may stop only at a committed boundary or the recorded prefix semantics;
  Close cancels all timers and future dispatch.

## Canonical controls

- Step: one real `controller.dispatch` followed by commit, recover, render, and animation.
- Run: repeated real dispatches under the lockstep latch; never frozen replay.
- Pause: cancels future Run dispatch and obeys the animation prefix contract.
- Inject: delegates to the canonical event API.
- Save/Export: raw bytes must equal direct `controller.export` output.
- Load/Reset/Replay: delegate to existing controller APIs.

## Baseline requirement

Callable evidence must compare the live path with a frozen-player/no-dispatch
baseline and show that only the live path increments the committed sequence and
fresh recovery. This baseline is UX/integration evidence only.

## Ablation requirement

Rerun real episodes with at least:

- dispatch replaced by a no-op;
- recovered path replaced by a straight-line decoy;
- animation-complete latch held closed;
- translation layer removed or replaced with ID-only output;
- private/oracle positive-control token injected into a repo-external fixture.

Each intervention must produce the predeclared failure, not a handwritten
verdict.

## Trace/replay requirement

- All panels in one step must retain one `RecoveryFrame` identity/sequence.
- Replay must recompute candidate behavior from serialized state plus
  observation, not only compare stored hashes.
- The visual verifier records producer function, input artifacts, run ID,
  seed/world-seed/context IDs, aggregation rule, and code-path hashes.
- Chinese mapping must not change causal bytes.

## Computed-evidence provenance gate

Required callable checks:

1. UI Step calls canonical `dispatch`.
2. SQLite records a committed transition.
3. fresh-process recover returns the committed sequence.
4. every panel uses the same RecoveryFrame.
5. actual scheduled waypoints equal the recovered path element by element.
6. Run obeys commit/recover/animate lockstep.
7. Pause/Close produce zero extra dispatch.
8. export bytes equal direct controller export bytes.
9. replay recomputes from serialized state plus observation.
10. Chinese mapping leaves causal bytes unchanged.
11. private/oracle scan has a firing positive control.
12. static scan and callable tests find no second engine path.
13. fresh-process smoke and target-interpreter Tk test are non-skipped.
14. screenshot or short recording is produced as UX evidence only.

## Acceptance gate

Acceptance requires all 14 checks, a real explicit Tk entrypoint, a default-off
launch path, a recorded real Step and multi-step Run, committed SQLite state,
fresh recovery, recovered waypoint animation, Chinese causal display, and no
second logic path. Test green without a real trigger is insufficient.

## Stop conditions

Stop without widening scope if implementation requires any of:

- engine, microworld, store, claims, launcher, or SQLite schema changes;
- a second candidate/scoring/transition/memory/prediction/replay path;
- LLM, network, subprocess service, background/proactive dispatch, EgoOperator,
  EgoDesktop, runtime authority, or mainline enablement;
- an unlisted path;
- invented Chinese explanations not present in trace;
- skipped Tk trigger evidence relabeled as pass.

## Rollback plan

Keep the work in the exact 12-path boundary. On failure leave task-owned changes
unstaged and preserve `failure_manifest.json`; do not reset, clean, stash,
rebase, amend, or modify protected Ego main work.

## Expected changed files

Exactly the 12 paths in the paired mutation scope. The task card and mutation
scope are read-only dependencies during implementation.

## Forbidden changes

All paths outside the exact mutation scope, especially engine, microworld,
store, claims, launcher, SQLite schema, route/state/validator files,
EgoOperator, EgoDesktop, LLM/network/service code, and protected Ego main.

## Auto-Remote-Anchor

`forbidden`

## Claim ceiling

At most: a local default-off visual console is connected to the canonical
controller, SQLite, recovery, and replay paths and displays a Chinese causal
chain supported by recorded trace fields.

This does not prove real thought, emotion, learning success, memory causality,
initiative, agency, subjectivity, consciousness, electronic life, product
readiness, or user value.
