# EgoDesktop Joi Real-Loop G-ABLATION Stage Card v0

- task_id: `EGODESKTOP-GABLATION-001`
- status: `stage_card_ready__implementation_not_started`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `route governance / real-loop evidence design`
- current_layer: `strategy`
- main_chain_status: `not_connected`
- enabled_status: `false`
- trigger_evidence: `none`
- claim_ceiling: `egodesktop_real_loop_g_ablation_stage_card_only`
- auto_remote_anchor: `forbidden`

## Problem Reframe

`joi-demo` accepted a docs-only route-B real-loop G-ABLATION contract. EGO now needs an EGO-side authorization boundary
before any runtime code exists. The next useful action is not product enablement and not a Live2D polish pass; it is a
separate, default-off real-loop harness stage that can later test whether a read-only `CreatureState` stream causally
moves predeclared EgoDesktop output traces without being explained by static replay, same-access reproducers, current
shim behavior, renderer idle, or LLM nondeterminism.

This stage card does not implement the harness. It freezes the EGO-side boundaries for a future implementation task.

## Authority Source

- EGO repo authority: `docs/PROGRAM_STATE_UNIFIED.yaml`
- Current EGO mainline owner: `EgoOperator/` and local EgoDesktop presentation path
- EGO readback: branch `main`, HEAD `1862875ff3959ff4dea934e4e6e0d1135c253681`, clean at card creation
- joi-demo source contract:
  - repo: `D:\Project\AIProject\MyProject\joi-demo`
  - commit: `2e14328f1f5887f3dd5298a4768fbb02841f131b`
  - file: `JOI-DEMO-GRAD-G-ABLATION-RUNTIME-001C-REAL-LOOP-CARD.md`
- Current EGO runtime surfaces inspected for this card:
  - `EgoDesktop/src/chatTurn.js`
  - `EgoDesktop/src/pspcVisualShim.js`
  - `EgoDesktop/src/main.js`
  - `EgoDesktop/viewer/renderer.js`
  - `EgoDesktop/tests/chat_turn.test.js`

## One Hypothesis

If a future harness runs only under an explicit non-default experiment flag, records the actual EgoDesktop
chat-turn/render path, locks or excludes LLM output, excludes renderer idle, and evaluates strongest same-access and
heldout static-replay baselines, then EGO can produce a route-B real-loop verdict without granting the creature adapter
runtime authority or changing default product behavior.

Expected honest outcomes include `real_loop_g_ablation_baseline_saturated_stop` or
`invalid_baseline_parity_or_privileged_state_leak`. A positive local verdict is not expected and would still remain
bounded attribution evidence only.

## One Change Surface For Future Implementation

A later implementation task may modify only experiment-scoped EgoDesktop harness surfaces:

- a default-off launch/CLI flag contract such as `JOI_REAL_LOOP_G_ABLATION=1`;
- test-only or experiment-only chat-turn/render trace capture;
- a read-only adapter that consumes serialized `CreatureState` records and writes only predeclared visual output fields;
- deterministic prompt/turn packs and calibration/heldout split fixtures;
- baseline runners for `OFF_STATE_FLAT`, `OFF_REACTIVE_ONLY`, `OFF_STATIC_REPLAY_SAME_PACK`,
  `OFF_STATIC_REPLAY_HELDOUT`, `CURRENT_SHIM`, `OFF_SHUFFLED_STATE`, and `SAME_ACCESS_REPRODUCER_BATTERY`;
- replay/leakage/negative-control reports and local artifacts under a new explicit artifact namespace.

Default EgoDesktop behavior must be byte-identical with the flag absent.

## Forbidden Change Surface

- No default runtime enablement.
- No EGO mainline claim upgrade.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger claim update from this card alone.
- No durable memory write.
- No user-visible behavior change outside the explicit experiment flag.
- No direct creature action authority, tool call, user message, send, schedule, approval, or gate decision.
- No LLM/persona/prompt rewrite framed as creature evidence.
- No discrete mood-to-face or state-to-reply lookup as the adapter.
- No use of same-pack static replay as positive evidence.
- No weakening of `SAME_ACCESS_REPRODUCER_BATTERY` or `OFF_STATIC_REPLAY_HELDOUT`.
- No push/tag/remote anchor from this card.

## Required Future Flag Contract

A future implementation task must define a local-only, default-false experiment contract. Minimum fields:

- `JOI_REAL_LOOP_G_ABLATION=1`
- `JOI_REAL_LOOP_CONDITION=<condition>`
- `JOI_REAL_LOOP_TRACE_DIR=<artifact_dir>`
- `JOI_REAL_LOOP_LLM_MODE=replay_locked`
- `JOI_REAL_LOOP_PROMPT_PACK=<hash_or_path>`
- `JOI_REAL_LOOP_SPLIT=<calibration_or_heldout>`

If these are absent, the future harness must be inert.

## Required Future Conditions

The future implementation must preserve the condition set from the `joi-demo` card:

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

## Required Future Trace Contract

Every future trace row must include at least:

- run id, condition id, turn id, tick/frame id, seed, and source hashes;
- user prompt id and prompt-pack hash;
- calibration/heldout split id;
- LLM replay id or `none`;
- chat-turn result fields including status, expression name, bot text hash, and PSPC scenario id if present;
- `CreatureState` record hash and emitted fields;
- adapter output fields and source attribution;
- public-input fields made available to baseline reproducers;
- same-access reproducer id and fit/evaluation split for baseline rows;
- Live2D parameter samples written by the adapter;
- renderer idle params explicitly tagged as excluded from `D`;
- output event timestamp/order;
- replay reconstruction inputs.

Replay must recompute scores from serialized traces and source/config hashes. It must not compare only stored verdicts.

## Required Future Verdicts

Allowed future verdicts are inherited from the `joi-demo` contract:

- `blocked_missing_ego_authorization`
- `blocked_missing_llm_replay_contract`
- `blocked_missing_real_loop_entrypoint`
- `blocked_unreplayable_runtime_trace`
- `invalid_leakage_or_future_info`
- `invalid_baseline_parity_or_privileged_state_leak`
- `invalid_renderer_idle_drives_metric`
- `invalid_llm_unlocked_confounds_metric`
- `invalid_metric_uses_same_pack_static_replay_as_positive_evidence`
- `real_loop_g_ablation_fail_no_creature_effect`
- `real_loop_g_ablation_baseline_saturated_stop`
- `real_loop_g_ablation_partial_causal_path_only`
- `real_loop_causal_path_attribution_pass`

No verdict may be called product pass, EGO integration pass, companion readiness, mechanism validity, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Three-Level Verify For Future Implementation

1. Contract/static level:
   - flag absent leaves EgoDesktop behavior unchanged;
   - forbidden authority fields are rejected;
   - active runtime files do not register an always-on creature adapter.
2. Deterministic harness level:
   - all required conditions can produce trace rows;
   - LLM replay lock is enforced or text fields are excluded;
   - replay/leakage/negative controls recompute from artifacts.
3. Real-loop local level:
   - actual `window.egoDesktop.sendChatTurn(...)` / renderer path is used under the explicit flag;
   - renderer idle is excluded;
   - `OFF_STATIC_REPLAY_HELDOUT` and best same-access reproducer are evaluated before any positive local verdict.

## Acceptance Gate For This Stage Card

This docs-only stage is accepted only if:

- the EGO-side card exists and cites the accepted `joi-demo` source contract;
- the card forbids implementation, runtime enablement, claim upgrade, push/tag/anchor, and default path mutation;
- future implementation is narrowed to a separate default-off task;
- the card preserves same-access/static-replay closure gates and privileged-state invalidation;
- `git diff --check` passes for the docs-only change.

## What This Stage Proves

Only that EGO has an explicit local authorization boundary for a possible future real-loop G-ABLATION harness.

## What This Stage Does Not Prove

This does not prove runtime integration safety, real-loop effect, product benefit, stable user benefit, durable memory
efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status, route-B pass/reopen/close, or
Bar-2 specialness.

## Rollback Plan

Delete this task directory and remove `EGODESKTOP-GABLATION-001` from `Tasks/TASK_BOARD.yaml`. No runtime file or
artifact should need rollback because this stage is docs-only.

## Next Minimal Closed-Loop Action

After this stage card is reviewed, create a separate implementation task for the default-off EgoDesktop real-loop harness.
That implementation task must not begin unless the operator explicitly accepts moving from this stage card to code.
