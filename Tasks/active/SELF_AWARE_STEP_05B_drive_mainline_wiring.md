# SELF_AWARE_STEP_05B_drive_mainline_wiring

```yaml
task_id: SELF_AWARE_STEP_05B
created_at: "2026-03-29T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: published
```

## real_goal

把 `MVP14` 的 formal owner `emotiond/drives/*` 接入正式主链，使后续 `drive/homeostasis formal proof` 可以在唯一 authority source 上进行。

## success_criteria

- 新 drive path 有唯一正式 consumer
- legacy path 降级为 bounded compatibility / observation path
- governance integrity 不受破坏
- replay / audit 路径仍可用

## authority_source

- `OpenEmotion/roadmap/versions/MVP14.spec.yaml`
- `OpenEmotion/docs/mvp14/`
- `OpenEmotion/emotiond/core.py`
- `OpenEmotion/emotiond/drive_adapter.py`
- `OpenEmotion/emotiond/drives/`

## current_layer

```yaml
current_layer: implementation
main_chain_status: core_decision_mainline_boundedly_converged_via_adapter_workspace_still_legacy
```

## required_artifacts

- `OpenEmotion/roadmap/SELF_AWARE_STEP_05B_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_05B_REVIEW_20260329.md`

## required_tests

- `pytest -q tests/mvp14/test_drive_infra.py`
- `pytest -q tests/mvp14/test_drive_integration.py`
- `pytest -q tests/mvp14/test_e2e_gate_b.py`
- `git diff --check`

## promotion_blockers

- 新 drive path 尚未接入正式 mainline
- adapter 仍通过 legacy modulation params 提供 bounded compatibility，formal owner 的行为影响尚未证明

## next_minimal_closure_action

本步已完成并发布；下一步切到 `SELF_AWARE_STEP_05C_drive_behavioral_influence_formal_proof.md`。
