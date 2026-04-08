# WP10 / MVP15 Legacy Reference Register

## 作用

本文件登记 `WP10` 启动前仓内已有的 `MVP15` 相关材料。它们可以作为参考输入，但不能直接充当新的 `WP10` authority、formal owner 或 formal proof。

## Reference-Only Task Materials

- `reference-only` means the material is archived reference input only and must not be promoted to current formal owner/proof.

- `Tasks/active/SELF_AWARE_STEP_06_mvp15_formal_proof.md`
- `Tasks/active/SELF_AWARE_STEP_06A_reflection_mainline_resolution.md`
- `Tasks/active/SELF_AWARE_STEP_06B_reflection_behavioral_relevance_formal_proof.md`
- `Tasks/active/SELF_AWARE_STEP_07_mvp16_unblock.md`
- `Tasks/active/SELF_AWARE_STEP_08_admission_review.md`
- `Tasks/active/SELF_AWARE_STEP_08A_real_developmental_evidence_closure.md`
- `Tasks/active/SELF_AWARE_STEP_08B_admission_retry_review.md`

## Reference-Only Compatibility / Legacy Code Surfaces

- `OpenEmotion/emotiond/reflection_engine/*`
- `OpenEmotion/emotiond/reflection_adapter.py`
- `OpenEmotion/emotiond/reflection_shadow.py`
- `OpenEmotion/emotiond/self_counterfactual.py`
- `OpenEmotion/emotiond/core.py`
- `OpenEmotion/emotiond/api.py`
- `OpenEmotion/emotiond/workspace.py`

## Reference-Only Legacy Claims

- `OpenEmotion/roadmap/ROADMAP_INDEX.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_06_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_06A_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_06B_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_07_EXECUTION_REPORT_20260330.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_08_EXECUTION_REPORT_20260330.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_08B_PUBLICATION_REPORT_20260329.md`

## Active Technical References

这些文件不是 legacy，但在 `WP10` 第一刀中仍只作为参考，不单独拥有执行裁决权：

- `OpenEmotion/roadmap/versions/MVP15.spec.yaml`
- `OpenEmotion/docs/mvp15/MVP15_STAGE_OVERVIEW.md`
- `OpenEmotion/docs/mvp15/MVP15_EXIT_CRITERIA.md`
- `OpenEmotion/docs/mvp15/REFLECTIVE_SELF_ARCHITECTURE.md`
- `OpenEmotion/docs/mvp15/REFLECTION_STATE_SCHEMA.md`
- `OpenEmotion/docs/mvp15/COUNTERFACTUAL_SELF_EVALUATION.md`
- `OpenEmotion/docs/mvp15/REFLECTIVE_GOVERNANCE_POLICY.md`
- `OpenEmotion/tests/mvp15/*`
- `OpenEmotion/tools/verify_mvp15_mainline_wiring.py`

## Current Rule

- `Tasks/MVS_task_plan.md` 是顶层裁决源
- `Tasks/MVP15_task_plan.md` 是 `WP10` phase-detail authority
- 本文件只负责说明哪些旧材料不能被误升格为新的 formal owner / formal proof path
- `OpenEmotion/tools/verify_mvp15_mainline_wiring.py`、`OpenEmotion/tools/mvp15_funnel_check.py`、`OpenEmotion/tools/mvp15_funnel_tracker.py`、`OpenEmotion/tools/mvp15_daily_validation.sh`、`OpenEmotion/tools/setup_mvp15_cron.sh` 只是 reference-only / archive surfaces，不是 current formal caller
