# H1 Preflight Same-Surface Unblock - STATUS

## Current milestone

- name: Milestone 2 - Clean-bind execution + causality-clear proof
- owner: Codex
- state: closed
- type: implementation

## Current state

- current_layer: implementation / verification
- main_chain_status: sampling stopped; same-surface contamination cleared; clean-bind restored on current temporary worktree; E4 preflight clean; live process stopped after evidence capture
- completion_class: complete_for_task_scope
- candidate_vs_proof: proof_passed_for_preflight_clean

## Completed work

- 已修复 `EgoCore/tests/test_native_loop.py` 的 `FakeLLMClient` fixture drift，`native_path_surface` scoped tests 已转绿
- 已扩展 preflight helper 支持 repo-root-aware evaluation，并新增 `run_h1_clean_bind_cycle.py` 做 temporary clean worktree + clean-bind + preflight rerun
- 已冻结 clean-bind mirrored fileset：`docs/codex/tasks/h1-preflight-same-surface-unblock/CLEAN_BIND_FILESET.json`
- 已修复 clean-bind runner 对 Windows BOM `telegram_launcher_meta.json` 的解析缺陷，并补齐 `OpenEmotion/openemotion/proto_self/trial1_shadow.py` 到 mirrored fileset
- 已生成新的 `H1_E4_PREFLIGHT_CURRENT.*` 与 `H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.*`，证明 same-surface contamination 已排除且 clean-bind preflight 已转为 `continue`

## Last experiment

- question: 旧 clean preflight 只覆盖 `08d85c3`；在当前有效切片 worktree `c256036` 上，clean-bind + preflight 是否仍然保持 `decision=continue`
- framing: 先重跑 clean-bind 到最新 temporary worktree `ego_h1_clean_bind_20260410_002906`，再只对这个 worktree 重跑 preflight；证据取回后立即停掉 poller
- result: latest worktree live process version 记录了正确的 `repo_root / branch / git_commit_short`，且 `git_dirty=false`；随后 preflight 报告转为当前有效 `clean_bind_ready=true`、`live_process_ok=true`、`decision=continue`，并在取证后终止 pid `24448`
- evidence_upgraded: yes

## What was learned

- `test_native_loop_runs_tool_call_and_returns_reply` 当前失败面收敛为 fixture 缺 `generate_with_messages()`，不是新的 runtime semantic blocker
- `EgoCore/.env` 是 Telegram live bind 所需 secret surface，但因 `.gitignore` 屏蔽，可被镜像进 clean worktree 而不破坏 `git_dirty=false`
- `repo-root-guard` 旧逻辑会错误拒绝合法 worktree；加上显式 `EGO_REPO_ROOT` 授权后，worktree startup 已能正确解析到 worktree `EgoCore/OpenEmotion` 路径
- clean-bind preflight 的两条误报根因分别是：tracked runtime 输出不应算代码脏污，以及 mirrored fileset 最初漏掉 `OpenEmotion/openemotion/proto_self/trial1_shadow.py`
- WSL worktree `.git` 文件使用 `/mnt/...` gitdir；Windows live process 写 version 时普通 `git` provenance 可能不稳定，因此 `live_process_version` 的 WSL fallback 和 runtime-dirty allowlist 都是必要补丁
- 这轮 clean-bind runner 本身的 PowerShell start wrapper 没有及时返回，但 latest worktree 上的 Telegram poller 已真实启动并通过 preflight；runner closeout hygiene 不是当前 acceptance blocker
- 旧 clean preflight 报告不能自动继承到新切片；closeout 前必须确认 `H1_E4_PREFLIGHT_CURRENT.*` 指向当前有效 worktree

## What was ruled out

- 被排除路线 1：在 dirty canonical root 上直接重跑 H1 preflight
- 被排除路线 2：为修 Task A 去扩 runtime semantics 或 sampling suite
- 被排除路线 3：继续把 WSL env 透传或 launcher quoting 当成主 blocker
- 被排除路线 4：继续把 `native_loop` / `runtime_observation` 当成 sampling contamination 源
- 被排除路线 5：继续把外部 lock holder 当成当前唯一 blocker
- 被排除路线 6：继续把 runtime-generated tracked artifacts 当成 clean-bind code dirtiness

## Next framing

- 本 task 已完成并关闭；若继续，下一轮问题表述是重新打开 `e4-shadow-h1-formal-mainline-sampling`，而不是继续修 Task A

## Last validation results

- mode: scoped pytest + clean-bind rerun + latest-worktree preflight + fast gate
- result: clean-bind restored on current worktree; preflight clean; task stop condition reached and closeout refreshed
- summary:
  - `python3 -m py_compile scripts/codex/h1_e4_sampling_common.py scripts/codex/run_h1_e4_sampling_preflight.py scripts/codex/run_h1_clean_bind_cycle.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_h1_e4_sampling_tools.py EgoCore/tests/test_live_process_version.py EgoCore/tests/test_native_loop.py EgoCore/tests/test_telegram_bot_native_switch.py -q`
  - `python3 scripts/codex/run_h1_clean_bind_cycle.py --bind-timeout-seconds 8`
  - `python3 scripts/codex/run_h1_e4_sampling_preflight.py --repo-root /mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_225403`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 -m py_compile EgoCore/app/live_process_version.py scripts/codex/h1_e4_sampling_common.py EgoCore/tests/test_live_process_version.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_live_process_version.py EgoCore/tests/test_h1_e4_sampling_tools.py -q`
  - `python3 scripts/codex/run_h1_clean_bind_cycle.py --bind-timeout-seconds 40`
  - `python3 scripts/codex/run_h1_e4_sampling_preflight.py --repo-root /mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_233520`
  - `python3 scripts/codex/run_h1_clean_bind_cycle.py --bind-timeout-seconds 40`
  - `python3 scripts/codex/run_h1_e4_sampling_preflight.py --repo-root /mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260410_002906`
  - `cmd.exe /c taskkill /PID 24448 /T /F`

## Decisions made

- clean-bind 通过 temporary clean execution worktree 完成，不动 canonical root 的脏状态
- live process 只用于 provenance / preflight；不恢复 E4 sample collection
- `H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.*` 是本 slice 的正式 closeout 证据；它证明的是“已排除 same-surface contamination 且 preflight 已 clean”，不是“已恢复采样”
- runtime-generated tracked outputs 允许作为 clean-bind runtime side effect 留在 allowlist 中，不计入 code dirtiness
- stop condition 命中后立即停在 preflight clean，不继续推进 sampling

## Open risks

- 风险 1：`run_h1_clean_bind_cycle.py` 的 PowerShell start wrapper 仍可能挂住，虽然不影响当前 preflight 结论
- 风险 2：后续重新开启 E4 sampling 时，仍需要显式保持 `shadow_h1` telemetry-only，不得把它接进 live decisions
- proof gap: 无当前 milestone blocker；仍未证明 runtime efficacy、repo-level enablement、或 E4 sampling 已恢复

## Next step

- 若用户继续这条线，唯一最高优先级动作是重开 `e4-shadow-h1-formal-mainline-sampling` 并开始正式 E4 sample collection；本 task 已关闭，不再继续

## Commands run / evidence

- `python3 -m py_compile scripts/codex/h1_e4_sampling_common.py scripts/codex/run_h1_e4_sampling_preflight.py scripts/codex/run_h1_clean_bind_cycle.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_h1_e4_sampling_tools.py EgoCore/tests/test_live_process_version.py EgoCore/tests/test_native_loop.py EgoCore/tests/test_telegram_bot_native_switch.py -q`
- `python3 scripts/codex/run_h1_clean_bind_cycle.py --bind-timeout-seconds 8`
- `python3 scripts/codex/run_h1_e4_sampling_preflight.py --repo-root /mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_225403`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 -m py_compile EgoCore/app/live_process_version.py scripts/codex/h1_e4_sampling_common.py EgoCore/tests/test_live_process_version.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_live_process_version.py EgoCore/tests/test_h1_e4_sampling_tools.py -q`
- `python3 scripts/codex/run_h1_clean_bind_cycle.py --bind-timeout-seconds 40`
- `python3 scripts/codex/run_h1_e4_sampling_preflight.py --repo-root /mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_233520`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_PREFLIGHT_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.json`
- `docs/codex/tasks/h1-preflight-same-surface-unblock/CLEAN_BIND_FILESET.json`
- worktree evidence:
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_225403/EgoCore/logs/telegram_launcher_meta.json`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_225403/EgoCore/logs/egocore_run.log`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_231135/EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_231712/EgoCore/logs/egocore_run.log`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_233520/EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_233520/EgoCore/logs/telegram_launcher_meta.json`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260409_233520/EgoCore/logs/egocore_run.log`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260410_002906/EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260410_002906/EgoCore/logs/telegram_launcher_meta.json`
  - `/mnt/d/Project/AIProject/MyProject/_codex_clean_binds/ego_h1_clean_bind_20260410_002906/EgoCore/logs/egocore_run.log`
