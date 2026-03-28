# SELF_AWARE_STEP_05A_drive_authority_resolution

```yaml
task_id: SELF_AWARE_STEP_05A
created_at: "2026-03-29T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: published
```

## real_goal

统一 `MVP14` 的 formal owner convergence target、formal contract 与 mainline convergence 方向，防止在 authority/mainline split 状态下继续做伪 formal proof。

## success_criteria

- 明确 `MVP14` 的 formal owner convergence target
- 明确 legacy drive/homeostasis path 的角色边界
- 明确下一步 mainline wiring convergence 的唯一目标
- 状态机不再把 `Step05` 误当成可直接做 proof

## authority_source

- `OpenEmotion/roadmap/versions/MVP14.spec.yaml`
- `OpenEmotion/docs/mvp14/`
- `OpenEmotion/artifacts/verification/TRACE_INDEX.md`
- `OpenEmotion/artifacts/verification/MVP_VERIFICATION_SUMMARY.md`
- `OpenEmotion/artifacts/verification/MVP_STAGE_CODE_MAP.md`
- `OpenEmotion/artifacts/verification/MVP_STAGE_SCORECARD.json`

## current_layer

```yaml
current_layer: strategy
main_chain_status: authority_target_selected_mainline_not_yet_converged
```

## required_artifacts

- `OpenEmotion/roadmap/SELF_AWARE_STEP_05A_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_05A_REVIEW_20260329.md`

## required_tests

- `git diff --check`
- `json parse: OpenEmotion/roadmap/self_aware_normalized_state.json`
- `yaml parse: EgoCore/docs/PROGRAM_STATE_UNIFIED.yaml`

## promotion_blockers

- `emotiond/drives/*` 仍未接正式主链
- legacy drive/homeostasis path 仍承担实际因果效力
- 尚无 owner-backed drive/mainline convergence 证明

## next_minimal_closure_action

执行 `SELF_AWARE_STEP_05B_drive_mainline_wiring.md`，把 formal owner convergence target 接入正式 mainline。
