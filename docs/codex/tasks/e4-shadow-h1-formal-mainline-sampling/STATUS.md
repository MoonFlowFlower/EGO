# E4 Shadow H1 Formal Mainline Sampling - STATUS

## Current milestone

- name: Milestone 1: Sample Manifest And Report Chain
- owner: Codex
- state: blocked
- type: exploration

## Current state

- current_layer: verification / observation
- main_chain_status: canonical `shadow_h1` telemetry patch exists; clean-bind preflight is admitted; current authority still has `0/4` frozen-prompt matches
- completion_class: conditional_complete_blocked
- candidate_vs_proof: proof_pending

## Completed work

- 已创建 `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/` 五件套
- 已冻结 `FROZEN_SAMPLE_MATRIX.json`
- 已实现 H1 E4 preflight / report helper 脚本
- 已补 live process version 对 H1 env flags 的记录
- 已产出 `H1_E4_CAUSALITY_EXCLUSION_CURRENT.{json,md}`
- 已通过 `h1-preflight-same-surface-unblock` 重新建立 clean-bind，并把 preflight 翻到 `decision=continue`
- 已把 sample report chain 改成跟随 admitted clean worktree source root 读取 authority bundles
- 已生成 `H1_E4_SAMPLE_MANIFEST_CURRENT.*`、`H1_E4_SHADOW_APPEARANCE_REPORT_CURRENT.*`、`H1_E4_FAILURES_TABLE_CURRENT.*`、`H1_E4_SAMPLE_LEVEL_REPORT_CURRENT.*`

## Last experiment

- question: preflight admitted 后，现有 authority bundles 是否已经包含命中 frozen prompts 的 post-bind samples
- framing: 直接用 current preflight 指向的 clean worktree source root 生成 H1 sample reports，不复制 artifacts、不改 scorer ontology
- result: sample report chain 工作正常，但 `0/4` frozen prompt rows matched any post-bind authority bundle；failures table 全部是 `missing_sample`
- evidence_upgraded: yes

## What was learned

- 当前 clean-bind live Telegram process 已能绑定到 current clean worktree `HEAD`
- `native_loop` 与 `runtime_mainline_observation` 已从 sampling contamination 源降到 `same_surface_cleared`
- H1 sample report chain 现在会自动跟随 admitted preflight 的 `evaluated_repo_root` 读取 authority bundles
- 当前还没有命中 frozen prompts 的现成 `real_telegram` authority bundles，因此不能只靠历史样本直接完成 H1 sample reports
- browser-side operator probe 不可用，当前仓库内也没有替代真实 `user -> bot` ingress 的 operator harness

## What was ruled out

- dirty-tree blind sampling
- 用 dashboard flow detail 当 H1 E4 sample authority
- 在 unresolved `native_loop` blocker 上继续做 bounded live sampling
- 通过 bot-side outbound probe 冒充真实 `user -> bot` ingress

## Next framing

- 当前 blocker 已收敛为 external operator ingress 缺失；若没有真实 Telegram DM operator 发送 frozen prompts，本任务不能再向前推进

## Last validation results

- mode: admitted preflight + source-root-aware report chain
- result: partial_pass
- summary:
  - `artifacts/telegram_real_mainline_v1/reports/H1_E4_PREFLIGHT_CURRENT.json` reports `decision=continue`
  - `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.json` reports `sampling_path_cleared`
  - `python3 -m py_compile scripts/codex/h1_e4_sampling_common.py scripts/codex/build_h1_e4_sample_reports.py EgoCore/tests/test_h1_e4_sampling_tools.py` passed
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_h1_e4_sampling_tools.py -q` passed
  - `python3 scripts/codex/build_h1_e4_sample_reports.py` succeeded and read from admitted worktree source root
  - `H1_E4_SAMPLE_MANIFEST_CURRENT.json` shows `matched_complete = 0`, `missing = 4`

## Decisions made

- live binding 模式固定为 `require clean commit`
- 当前任务在 preflight admitted 后继续停留在 frozen sample matrix，不扩 prompts，不扩 replay suite
- 真实采样 authority 仍固定为 `artifacts/telegram_real_mainline_v1/real_telegram/*/ledger.json`
- 当前不把 browser/MCP 不可用、或 bot-side outbound probe，包装成真实 operator ingress

## Open risks

- 风险 1：真实 E4 sampling 仍缺少 external Telegram operator 通道
- 风险 2：若没有 post-bind authority bundles，本任务会持续停在 `missing_sample`
- proof gap: 尚未取得任何命中 frozen prompts 的 current formal-mainline `shadow_h1` E4 sample bundle

## Next step

- 由真实 Telegram operator 从授权 DM 发送 frozen sample matrix 的 prompts，然后重跑 `python3 scripts/codex/build_h1_e4_sample_reports.py`

## Commands run / evidence

- `artifacts/telegram_real_mainline_v1/reports/H1_E4_PREFLIGHT_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.json`
- `docs/codex/tasks/h1-preflight-same-surface-unblock/STATUS.md`
- `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/FROZEN_SAMPLE_MATRIX.json`
- `python3 -m py_compile scripts/codex/h1_e4_sampling_common.py scripts/codex/build_h1_e4_sample_reports.py EgoCore/tests/test_h1_e4_sampling_tools.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_h1_e4_sampling_tools.py -q`
- `python3 scripts/codex/build_h1_e4_sample_reports.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_SAMPLE_MANIFEST_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_SHADOW_APPEARANCE_REPORT_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_FAILURES_TABLE_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_SAMPLE_LEVEL_REPORT_CURRENT.json`
