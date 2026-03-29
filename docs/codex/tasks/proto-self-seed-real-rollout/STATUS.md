# Proto-Self Seed v0.2 Real Session Rollout - STATUS

## Current milestone

- name: Milestone 2: Capture one real seed session
- owner: Codex
- state: completed

## Current state

- current_layer: verification / rollout
- main_chain_status: live Telegram poller rebound to current commit; controlled real session now proves `seed_v0_2` on live Telegram mainline with single-sample closure evidence
- completion_class: completed_not_stable

## Completed work

- 已创建 `docs/codex/tasks/proto-self-seed-real-rollout/` 四件套
- 已确认旧 `LIVE_TELEGRAM_PROCESS_VERSION.json` 停在旧 commit，不可直接用于 rollout
- 已清旧 poller/lock 并重新拉起 live Telegram process
- 已确认当前 live version binding 指向 `0cc39da`
- 已核对第一轮真实样本：
  - `/proto seed on` 样本命中 `subject_profile=seed_v0_2`
  - 目标文件路径消息被 `telegram_early_return` 提前吃掉，没有进入 native OpenEmotion 主链
- 已核对第二轮真实样本：
  - `sample_20260329_170146_12f48d1e` 已出现 `subject_profile=seed_v0_2`、`executed_action=file`、`exec_result=success`、`seed_state_snapshot`
  - `sample_20260329_170252_7fbc5712` 已出现 `candidate_actions=['continue_pending_commitment']`
- 已核对第三轮真实样本：
  - `sample_20260329_173745_c07c7452` 证明首条显式文件读取仍误落到 `shell type`
  - `sample_20260329_173845_30112865` 证明 follow-up `继续读取完整内容，不要截断` 已命中 `request_mode=analyze + file read`
- 已补 host guardrail：
  - 显式路径 + `request_mode=analyze` + shell display command 会在 host 侧改写成 `file {"operation":"read","path":"..."}`
- 已核对第四轮真实样本：
  - `sample_20260329_175737_7ca3cfb6` 在单条 finalized sample 中同时保留：
    - `subject_profile=seed_v0_2`
    - ingress `candidate_actions=['inspect_file', 'continue_pending_commitment']`
    - `executed_action.action_type=file`
    - `exec_result.status=success`
    - `seed_state_snapshot` 更新
- 已输出 real rollout report：
  - `EgoCore/artifacts/proto_self_seed/PROTO_SELF_SEED_V0_2_REAL_SESSION_ROLLOUT_REPORT_20260329.md`

## Last validation results

- mode: real-session evidence check
- result: success
- summary:
  - `EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
  - `git_commit_short = 142c9bd`
  - `process_kind = telegram`
  - `pid = 49424`
  - `sample_20260329_173745_c07c7452`: 旧 host 行为暴露 `shell type` misroute
  - `sample_20260329_173845_30112865`: follow-up 文件完整读取成功，action_type=`file`
  - `sample_20260329_175737_7ca3cfb6`: 首跳显式文件读取成功命中 `file`，且 finalized sample 保留 ingress candidate 与 exec-result
  - 针对 guardrail 的 targeted pytest: `37 passed, 1 warning`

## Decisions made

- 真实 rollout 使用显式 `/proto seed on`，不依赖默认路径
- 受控消息优先带真实文件路径：`D:\\Project\\AIProject\\MyProject\\Test\\任务单.txt`
- 先做单 session / 单样本 V4，不提前扩成 E5
- 由于 `Test` 路径已被既有 `profile_memory` standing rule 污染，第二轮改用仓库内其他显式文件路径
- 当前不把“多样本观察”冒充为稳定性结论；本轮只收单样本 real-session closure
- 先在 host 侧收窄修复，不动 seed kernel / Telegram 主链架构

## Open risks

- 需要用户发送真实 Telegram 消息；当前无法由仓内自动替代
- 若外部又出现重复 poller，证据会被污染
- `/new` 不会清除持久化 profile rules；若再次选中 `Test` 路径，仍会被 `reply_only_once` 早退
- 当前没有新的技术 blocker；剩余工作属于 rollout 扩样而非修复阻塞

## Next step

- 用户发送：
- 若继续推进：
  - 采集第 2 条真实 `seed_v0_2` 样本
  - 观察 candidate / exec-result / next-state 是否继续稳定保持

## Commands run / evidence

- `python3 scripts/codex/new_task.py proto-self-seed-real-rollout --title "Proto-Self Seed v0.2 Real Session Rollout"`
- `powershell.exe -ExecutionPolicy Bypass -File scripts/start_egocore_telegram_windows.ps1`
- `EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
- `EgoCore/logs/egocore_run.log`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_165446_d5f73cf0/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_165503_6f6914f9/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_170146_12f48d1e/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_170252_7fbc5712/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_170539_f38537e9/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_173745_c07c7452/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_173845_30112865/sample.json`
- `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260329_175737_7ca3cfb6/sample.json`
- `EgoCore/data/session_logs/telegram_dm_8420019401.jsonl`
- `PYTHONPATH=OpenEmotion:EgoCore ./EgoCore/.venv/bin/python -m pytest -s -q EgoCore/tests/test_runtime_v2_minimal.py EgoCore/tests/test_runtime_v2_telegram_bridge.py EgoCore/tests/test_runtime_v2_ws4_progress_events.py`
- repo-level proof:
  - `EgoCore/artifacts/proto_self_seed/PROTO_SELF_SEED_V0_2_MAINLINE_EVIDENCE_REPORT_20260329.md`
  - `EgoCore/artifacts/proto_self_seed/PROTO_SELF_SEED_V0_2_REAL_SESSION_ROLLOUT_REPORT_20260329.md`
