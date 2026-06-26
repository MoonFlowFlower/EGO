# EgoDesktop Joi Real-Loop G-ABLATION Harness Contract v0 Report

- task_id: `EGODESKTOP-GABLATION-002`
- status: `pass`
- claim_ceiling: `egodesktop_real_loop_g_ablation_harness_contract_only`
- mainline_connected: `false`
- enabled: `false_by_default`
- real_trigger_evidence: `none`
- runtime_authority: `none`
- adapter_registered: `false`

## Summary

This slice adds a pure CommonJS contract module for a future default-off EgoDesktop real-loop G-ABLATION harness. It does
not connect a creature adapter to default EgoDesktop behavior and does not run a real-loop experiment.

## Implemented Contract Surface

- Default-disabled experiment contract via `buildJoiRealLoopGAblationContract`.
- Required explicit flags:
  - `JOI_REAL_LOOP_G_ABLATION=1`
  - `JOI_REAL_LOOP_CONDITION`
  - `JOI_REAL_LOOP_TRACE_DIR`
  - `JOI_REAL_LOOP_LLM_MODE=replay_locked`
  - `JOI_REAL_LOOP_PROMPT_PACK`
  - `JOI_REAL_LOOP_SPLIT`
- Recursive no-authority field rejection.
- Required condition set from the accepted `joi-demo` 001C card.
- Trace-row builder with condition, prompt, split, LLM replay, chat-turn hash, CreatureState hash, adapter-output hash,
  public-input hash, renderer-idle exclusion, output event, and replay inputs.
- Baseline plan metadata for same-pack diagnostic replay, heldout input-blind static replay, and strongest same-access
  reproducer battery.
- Verdict helper preserving blocked, invalid, saturation, partial, and bounded local attribution labels.

## Verification Run

- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_harness.test.js`
  - result: `9 passed`
- `npm test` from `EgoDesktop`
  - result: `66 passed`

## What This Proves

Only that EGO now has a local, default-off contract module and tests for a future real-loop G-ABLATION harness.

## What This Does Not Prove

This does not prove real-loop effect, runtime integration safety, product benefit, stable user benefit, durable memory
efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status, route-B pass/reopen/close, or
Bar-2 specialness.

## Next Minimal Closed-Loop Action

If continuing, the next slice is a separate default-off trace runner that invokes the actual EgoDesktop chat-turn/render
path under explicit experiment flags and writes local trace artifacts. It must still avoid default runtime enablement.
