# EgoDesktop Joi Real-Loop G-ABLATION Trace Runner v0 Spec

- task_id: `EGODESKTOP-GABLATION-003`
- status: `pass__default_off_trace_runner_wired_local_smoke`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / default-off trace runner design`
- current_stage_layer: `implementation authorization`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `false_by_default`
- real_trigger_evidence: `electron_smoke_renderer_ready_trace_only`
- claim_ceiling: `egodesktop_real_loop_g_ablation_trace_runner_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-002` created a pure default-off contract module for a future real-loop G-ABLATION harness. The next
minimal slice is a separate trace-runner task that can exercise the actual EgoDesktop chat-turn and renderer readiness
path only when explicit experiment flags are present, then write replay-oriented local trace artifacts.

This task card does not authorize a route-B verdict, product enablement, default runtime behavior change, or evidence
ledger update. It authorizes only a default-off local trace runner implementation plan.

## Real Objective

Create a bounded implementation slice that proves EGO can collect replayable EgoDesktop real-loop trace rows from the
actual local chat/render path under explicit experiment flags, without giving the creature adapter runtime authority and
without changing default user behavior.

## Authority Source

- Source stage card: `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-stage-card-v0/STAGE_CARD.md`
- Source contract module: `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-harness-contract-v0/SPEC.md`
- Source code contract: `EgoDesktop/src/joiRealLoopGAblationHarness.js`
- joi-demo source contract: `D:\Project\AIProject\MyProject\joi-demo\JOI-DEMO-GRAD-G-ABLATION-RUNTIME-001C-REAL-LOOP-CARD.md`
- joi-demo source commit: `2e14328f1f5887f3dd5298a4768fbb02841f131b`
- EGO program authority: `docs/PROGRAM_STATE_UNIFIED.yaml`

## Mainline Target

The target is not default mainline integration. The target is an explicit experiment-only path:

`JOI_REAL_LOOP_G_ABLATION=1` -> local EgoDesktop launch or test harness -> actual `ego-desktop:chat-turn` and renderer
ready payload -> trace-row builder -> local artifacts.

With the flag absent, EgoDesktop behavior must remain unchanged.

## Enabled-State Requirement

The trace runner must stay inert unless all required `EGODESKTOP-GABLATION-002` flags are valid:

- `JOI_REAL_LOOP_G_ABLATION=1`
- `JOI_REAL_LOOP_CONDITION=<condition>`
- `JOI_REAL_LOOP_TRACE_DIR=<artifact_dir>`
- `JOI_REAL_LOOP_LLM_MODE=replay_locked`
- `JOI_REAL_LOOP_PROMPT_PACK=<hash_or_path>`
- `JOI_REAL_LOOP_SPLIT=<calibration_or_heldout>`

The implementation may add runner-specific flags only if they remain local, explicit, and default false.

## Real-Trigger Evidence Requirement

Acceptance requires at least one local deterministic trace run that uses the same code path as an EgoDesktop chat turn
or a narrow test seam around that handler. The run must write artifact files containing contract rows, renderer-ready
metadata, source hashes, and a report. If real Electron execution is unavailable in the environment, the status must be
`blocked_missing_real_loop_entrypoint` or `blocked_unreplayable_runtime_trace`, not pass.

## Hypothesis

If the trace runner is implemented as a default-off wrapper around the existing contract module and actual EgoDesktop
chat/render events, it can produce replayable trace artifacts without creating runtime authority, default enablement, or
a second logic path.

## Strongest Baseline Explanation

Any apparent creature effect will most likely be explained by current shim behavior, same-pack static replay, heldout
static replay, best same-access reproducer, renderer idle, or unlocked LLM variance. The trace runner must preserve
these explanations as first-class closure gates.

## Ablation Requirement

The implementation must preserve the condition surface from the source contract:

- `CREATURE_ON`
- `CREATURE_FROZEN`
- `OFF_STATE_FLAT`
- `OFF_REACTIVE_ONLY`
- `OFF_STATIC_REPLAY_SAME_PACK`
- `OFF_STATIC_REPLAY_HELDOUT`
- `OFF_SHUFFLED_STATE`
- `CURRENT_SHIM`
- `SAME_ACCESS_REPRODUCER_BATTERY`
- `LLM_REPLAY_LOCKED`
- diagnostic `ZERO_OUTPUT`, `RANDOM_STATE`, and `LEAK_INJECTED_POSCTRL`

This slice may stop at trace collection and baseline-ready labels. It must not claim a full ablation verdict unless
callable baseline implementations and replay recomputation are present.

## Trace And Replay Requirement

Trace artifacts must be generated through callable code and include:

- run id, condition id, turn id, tick/frame id, seed, source hashes;
- prompt id, prompt-pack hash, split id, and LLM replay id or `none`;
- actual chat-turn result fields, including status, expression name, bot text hash, and PSPC scenario id if present;
- `CreatureState` or adapter-state hash, even if represented by a blocked/default-off placeholder in this slice;
- adapter output fields and source attribution;
- public inputs available to same-access reproducers;
- renderer-ready metadata and Live2D parameter samples;
- renderer idle params tagged as excluded from `D`;
- replay reconstruction inputs and trace-row hash.

Replay must recompute from serialized artifacts in a later slice. Stored verdict comparison alone is insufficient.

## Computed-Evidence Provenance Gate

Any report generated by this task must record:

- producer function or script;
- input artifacts;
- run id;
- seed/context/turn ids;
- aggregation rule if any;
- source code hashes.

No hand-written score, static verdict dictionary, unconditional clean report, or same-pack replay positive evidence is
allowed.

## Acceptance Gate

- A task-local implementation plan exists before runtime files are edited.
- The implementation remains default-off and inert without explicit flags.
- A trace-runner module or narrow runtime hook calls `buildJoiRealLoopGAblationContract` and
  `buildJoiRealLoopTraceRow` rather than duplicating verdict/trace logic.
- Targeted tests prove disabled default behavior, flag validation, trace artifact schema, no authority fields, and
  renderer-idle exclusion.
- Local report states what was and was not triggered.
- `node --test` targeted checks pass.
- `git diff --check` passes.
- `scripts/codex_session_guard.py --mutation-scope ... closeout-check` reports no unsafe dirty paths.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_trace_runner_contract_only`.

This can prove only that a default-off trace-runner slice can collect bounded local trace artifacts. It cannot prove
real-loop effect, route-B pass/reopen/close, product benefit, stable user benefit, durable memory efficacy, runtime
integration safety, agency, real emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.

## Stop Condition

Stop and report blocked if:

- flags cannot be validated without weakening the `EGODESKTOP-GABLATION-002` contract;
- actual chat/render path cannot be reached or represented honestly;
- the runner would require default runtime enablement;
- LLM replay lock is absent and text would drive the metric;
- same-access or static replay baselines would be weakened;
- implementation needs `PROGRAM_STATE_UNIFIED.yaml`, evidence ledger, EgoOperator memory/gate/approval/transport, or
  proactive changes.

## Rollback Plan

Delete this task directory and remove `EGODESKTOP-GABLATION-003` from `Tasks/TASK_BOARD.yaml`. If implementation begins
in a later step, also delete only the trace-runner module/tests/artifacts named in that task's mutation scope.

## Expected Future Changed Files

- `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_trace_runner.test.js`
- optionally a narrow, default-off hook in `EgoDesktop/src/main.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_trace_runner_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-trace-runner-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`
- `artifacts/task_board/outbox.jsonl` if GitHub Project sync is unavailable

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No creature direct action, user message, send, schedule, memory write, gate decision, approval, or runtime registration.
- No route-B pass/reopen/close wording.
- No use of same-pack static replay as positive evidence.
- No push, tag, or remote anchor from this card.

## Next Minimal Closed-Loop Action

Implement the default-off trace-runner slice under this mutation scope, starting with targeted tests for disabled
default behavior, explicit flag validation, no-authority payload rejection, trace artifact construction, and honest
blocked verdict labels.
