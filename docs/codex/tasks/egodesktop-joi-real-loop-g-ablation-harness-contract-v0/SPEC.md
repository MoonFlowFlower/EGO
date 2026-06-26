# EgoDesktop Joi Real-Loop G-ABLATION Harness Contract v0 Spec

- task_id: `EGODESKTOP-GABLATION-002`
- status: `active`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / default-off evidence harness contract`
- main_chain_status: `contract_module_only`
- enabled_status: `false_by_default`
- real_trigger_evidence: `none`
- claim_ceiling: `egodesktop_real_loop_g_ablation_harness_contract_only`

## Real Goal

Create the first EGO-side implementation slice for the accepted `joi-demo` real-loop G-ABLATION contract: a default-off
EgoDesktop harness contract module that can validate experiment flags, declare required conditions, reject runtime
authority fields, construct replayable trace rows, describe baseline gates, and compute allowed verdict labels from
predeclared rule inputs.

## Non-Goals

- Do not run a real-loop experiment.
- Do not connect a creature adapter to the default product path.
- Do not modify `EgoOperator`, memory, gate, approval, transport, proactive, planner, model, `PROGRAM_STATE_UNIFIED.yaml`,
  or evidence ledger.
- Do not claim route-B pass/reopen/close, EGO integration, product benefit, agency, emotion, subjectivity,
  consciousness, alive status, or Bar-2.

## Authority Source

- Stage card: `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-stage-card-v0/STAGE_CARD.md`
- Source contract: `D:\Project\AIProject\MyProject\joi-demo\JOI-DEMO-GRAD-G-ABLATION-RUNTIME-001C-REAL-LOOP-CARD.md`
- Source contract commit: `2e14328f1f5887f3dd5298a4768fbb02841f131b`
- EGO authority: `docs/PROGRAM_STATE_UNIFIED.yaml`

## Success Criteria

- [ ] Default-disabled contract reports `enabled=false`, `runtime_authority=none`, `mainline_connected=false`, and no
      adapter registration.
- [ ] Explicit enabled contract requires `JOI_REAL_LOOP_G_ABLATION=1`, condition, trace dir, replay-locked LLM mode,
      prompt pack, and calibration/heldout split.
- [ ] Contract rejects executable/runtime-authority fields recursively.
- [ ] Required condition list includes all `joi-demo` 001C conditions, including same-pack and heldout static replay.
- [ ] Baseline plan treats same-pack static replay as diagnostic only and heldout static replay as decisive.
- [ ] Same-access reproducer battery is represented as a strongest/closest reproducer family, not a single EMA.
- [ ] Trace-row builder records the required replay fields and renderer-idle exclusion.
- [ ] Verdict helper cannot return positive attribution when static replay, same-access, privileged-state leakage,
      same-pack replay misuse, renderer idle, or unlocked LLM confounds are present.
- [ ] Targeted Node tests pass.
- [ ] `git diff --check` passes.

## Expected Changed Files

- `EgoDesktop/src/joiRealLoopGAblationHarness.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_harness.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_harness_v0/CONTRACT_REPORT.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-harness-contract-v0/*`
- `Tasks/TASK_BOARD.yaml`

## Rollback Plan

Delete the files above and remove `EGODESKTOP-GABLATION-002` from `Tasks/TASK_BOARD.yaml`. No default runtime behavior
should need rollback because this slice is module/test/report only.
