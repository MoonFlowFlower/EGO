# Proto-Self Seed v0.2 Real Session Rollout - PLAN

## Task summary

当前目标层级是 real-session rollout / V4 证据补齐。范围只覆盖 live Telegram process 绑定、受控消息采样、样本核验、rollout report，不扩到额外代码实现。

## Milestones

### Milestone 1: Arm live mainline

- scope:
  - 创建 rollout task 文档
  - 确认当前没有旧 poller 干扰
  - 启动并绑定到当前 commit 的 live Telegram process
- files / areas likely touched:
  - `docs/codex/tasks/proto-self-seed-real-rollout/*`
  - `EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
  - `EgoCore/logs/egocore_run.log`
- acceptance:
  - live version file 指向当前提交
  - Telegram bot 已进入 `Starting Telegram Bot...` 之后的运行态
- validation:
  - `powershell.exe -ExecutionPolicy Bypass -File scripts/start_egocore_telegram_windows.ps1`
  - 读取 `EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
- rollback note:
  - 杀掉新 poller，恢复到上一个已知可运行进程

### Milestone 2: Capture one real seed session

- scope:
  - 在真实 Telegram DM 中执行受控命令序列
  - 收集 1 条 `seed_v0_2` 自然语言样本
  - 核对 candidate / final host action / exec_result / next-state
  - 写 rollout report
- files / areas likely touched:
  - `EgoCore/artifacts/proto_self_seed/`
  - 真实样本目录
  - rollout report
- acceptance:
  - 至少 1 条真实样本满足 seed rollout 最低验收
  - 样本路径和核验字段被 repo-tracked 固定
- validation:
  - 读取最新 sample `ledger.json` / `sample.json`
  - 必要时补一轮 targeted host/process check
- rollback note:
  - 关闭 `/proto seed` override，回到当前非 seed live 路径

## Progress

- current_status: completed
- current_milestone: Milestone 2: Capture one real seed session
- milestone_state: Milestone 1 and Milestone 2 completed; single-sample real-session rollout evidence is now repo-tracked

## Decision log

- 2026-03-29: live rollout 只针对显式 `seed_v0_2` profile，不切默认路径
- 2026-03-29: 采样消息优先使用带真实文件路径的自然语言输入，以提高 seed affordance 信息量
- 2026-03-29: 真实样本前必须先校正 live process version，否则 rollout 证据无效

## Surprises / discoveries

- 旧的 `LIVE_TELEGRAM_PROCESS_VERSION.json` 仍停在 `468d9a4`，说明 live 版本绑定必须重做
- 新启动的 Telegram process 先被旧 poller lock 拦住，必须先清旧进程/锁后再启动
- 第一轮真实消息虽然已开启 `/proto seed on`，但命中了持久化 `profile_memory` 的 `reply_only_once` 规则，导致路径落在 `D:\\Project\\AIProject\\MyProject\\Test` 时直接 `telegram_early_return -> 什么喵?`
- 这不是 seed profile 完全失效；`/proto seed on` 与部分“继续”消息已经在真实样本里留下 `subject_profile=seed_v0_2` 的痕迹
- follow-up `继续读取完整内容，不要截断` 已能命中 `request_mode=analyze + file read`，说明 parser/bridge 侧绑定已收正
- 剩余问题收窄为首条显式文件读取仍可能被模型选成 `shell type`；已通过 host guardrail 改成 `file read`

## Outcomes / retrospective

- 本轮已证明：
  - rollout task 已建立
  - live Telegram process 已重新绑定到当前 commit
  - follow-up 文件全文读取不再走 `powershell`
  - finalized sample 已保留 ingress candidate payload，audit 不再只剩 metadata
- 第一轮真实 rollout 失败根因已定位为 pre-runtime standing rule 命中，不是 seed kernel 未接线
- 本轮已证明：
  - 修补后的**首条显式文件读取**已在真实样本中命中 `file read`
  - 同一条 finalized sample 中可同时回看 ingress candidate、final host action、`exec_result`、`seed_state_snapshot`
- 下一步最小闭环动作：
  - 若继续推进，进入受控多样本 live observation；当前不再需要为“单样本 real-session rollout”追加补丁
