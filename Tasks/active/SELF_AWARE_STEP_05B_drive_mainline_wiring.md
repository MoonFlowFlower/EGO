# SELF_AWARE_STEP_05B_drive_mainline_wiring

```yaml
task_id: SELF_AWARE_STEP_05B
created_at: "2026-03-29T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: pending
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
main_chain_status: authority_resolved_wiring_pending
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
- proof harness 仍无法证明 formal owner 的行为影响

## next_minimal_closure_action

完成最小 bounded wiring convergence，并在正式 mainline 上补一条 owner-backed drive/homeostasis paired proof。
