# WP10 / MVP15 Reflection Authority Source

## Top-Level Authority

- `Tasks/MVS_task_plan.md`

## Phase-Detail Authority

- `Tasks/MVP15_task_plan.md`

## Version / Scope Authority

- `OpenEmotion/roadmap/versions/MVP15.spec.yaml`

## Technical Reference Inputs

- `OpenEmotion/docs/mvp15/MVP15_STAGE_OVERVIEW.md`
- `OpenEmotion/docs/mvp15/MVP15_EXIT_CRITERIA.md`
- `OpenEmotion/docs/mvp15/REFLECTIVE_SELF_ARCHITECTURE.md`
- `OpenEmotion/docs/mvp15/REFLECTION_STATE_SCHEMA.md`
- `OpenEmotion/docs/mvp15/COUNTERFACTUAL_SELF_EVALUATION.md`
- `OpenEmotion/docs/mvp15/REFLECTIVE_GOVERNANCE_POLICY.md`

## Formal Owner Target

- `OpenEmotion/openemotion/reflective_self/*`

## Bounded Compatibility / Migration Surfaces

- `OpenEmotion/emotiond/reflection_engine/*`
- `OpenEmotion/emotiond/reflection_adapter.py`
- `OpenEmotion/emotiond/reflection_shadow.py`
- `OpenEmotion/emotiond/self_counterfactual.py`

## Legacy Consumer Surfaces

- `OpenEmotion/emotiond/core.py`
- `OpenEmotion/emotiond/api.py`
- `OpenEmotion/emotiond/workspace.py`

## Authority Resolution Rules

- 若 `Tasks/MVS_task_plan.md` 与任何下级文档冲突，以 `Tasks/MVS_task_plan.md` 为准
- 若 `Tasks/MVP15_task_plan.md` 与技术参考冲突，以 `Tasks/MVP15_task_plan.md` 为准
- `emotiond` legacy bounded consumer 的实现现状不自动改变 formal owner 判断
- 未经新的 authority freeze，不得把旧 `SELF_AWARE_STEP_06*` / `ROADMAP_INDEX` 的强结论重新升格为正式裁决源
