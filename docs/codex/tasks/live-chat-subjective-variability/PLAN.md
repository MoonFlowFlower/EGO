# Live Chat Subjective Variability - PLAN

## Task summary

这是一个 repo-level corrective slice，当前已完成 `M1 Baseline Freeze` 和 `M2 Rich Subject Surface`。目标不是立刻让 live chat 变“更像有主观能动性”，而是先把当前最关键的真实断层按顺序补齐：先冻结 baseline，再让主体 richer surface 在 live artifacts 里显式可见，之后才进入 reply shaping 与 cadence。

## Milestones

### Milestone 1: Baseline Freeze

- scope:
  - 新建 long-run task package
  - 冻结 `telegram:dm:8420019401` 的真实会话基线
  - 固定“已 ingress / tendency 近乎恒定 / richer fields 缺失”的结论
- files / areas likely touched:
  - `docs/codex/tasks/live-chat-subjective-variability/`
- acceptance:
  - baseline 事实写清，不说宽
  - 当前同步聊天契约被明确记录为 baseline，而不是被误写成主体 authority
- validation:
  - `git diff --check -- docs/codex/tasks/live-chat-subjective-variability`

### Milestone 2: Rich Subject Surface

- scope:
  - 让 current Telegram mainline 在 live ordinary chat 中显式携带 richer bounded fields
  - 不再只剩 `policy_hint / response_tendency / reflection_note`
- files / areas likely touched:
  - `EgoCore/app/runtime_v2/proto_self_runtime.py`
  - `EgoCore/tests/test_runtime_v2_proto_self_runtime.py`
  - `EgoCore/tests/test_telegram_proto_self_v2_evidence.py`
- target outputs:
  - `social_policy_hints`
  - `embodied_policy_hints`
  - `integrated_policy_hints`
  - `initiative_policy_hints`
- claim ceiling:
  - 只允许宣称 richer subject surface 已进入 live chat artifacts
  - 仍不允许宣称可感 variability 已成立

### Milestone 3: Tendency-to-Reply Consumption

- scope:
  - 让 richer bounded context 真正改变 `chat_mainline` 的 reply shaping
  - 引入 bounded `chat_expression_hint`
- claim ceiling:
  - 只允许宣称 tendency 开始影响 live reply shaping
  - 不允许宣称 cadence autonomy 已实现

### Milestone 4: Host-Governed Cadence

- scope:
  - 增加 `chat_cadence_mode`
  - 在宿主治理下允许 `short / normal / expand / hold_for_followup`
- claim ceiling:
  - 只允许宣称 host-governed cadence choice 已接入 current Telegram mainline
  - 不允许宣称 unrestricted autonomy

### Milestone 5: Fresh Real Telegram Proof

- scope:
  - 重采 fresh Telegram window
  - 用真实样本证明 richer fields、tendency shift、cadence shift
- claim ceiling:
  - 只允许宣称 live Telegram 有受治理的可感主体现象证据

### Milestone 6: Closeout

- scope:
  - 固定 current report
  - 收平文档口径与剩余 gap

## Progress

- current_status: `in_progress`
- current_milestone: `Milestone 5: Fresh Real Telegram Proof`
- milestone_state: `blocked_on_fresh_sample_mix`

## Decision log

- 当前 corrective slice 不新开 `WP`
- current Telegram mainline 锁定为：
  - `telegram_bot -> runtime_v2/chat_reply_engine -> response_contract -> delivery`
- baseline 只认真实 Telegram 会话，不用旧 verbalizer 或 social handler 冒充 live 证明
- `M2` 先补 richer subject surface，再做 tendency consumption，再做 cadence
- `M2` 只修 current Telegram mainline artifact surface，不改 `chat_reply_engine` / `response_plan`
- `M3` 已把 richer bounded context 接进 current chat mainline reply shaping，并保持 host-governed 边界不变

## Expected outcome

- 给后续 `M4+` 一个不漂移的 baseline
- 明确区分：
  - “主体已经 ingress”
  - “用户已经感受到结构化变化”
- 避免在没有 real-chat proof 前把当前能力说宽

## Outcome

- `M1 Baseline Freeze` 已完成：
  - baseline 会话已冻结
  - 已 ingress / tendency 平 / richer fields 缺失 已写清
  - `M2` 目标与 claim ceiling 已锁定
- `M2 Rich Subject Surface` 已完成：
  - `proto_self_runtime` 现在会对 richer subject surface / trace contexts 做显式规范化
  - ordinary chat artifacts 在 upstream omission 下也会保留 `{}` 键
  - focused runtime/evidence tests 已补齐并通过
- `M3 Tendency-to-Reply Consumption` 已完成：
  - `chat_reply_engine` 现在会显式消费 richer bounded context 与 recent tendency summaries
  - bounded `chat_expression_hint` 已进入 runtime reply / assistant history / response plan metadata
  - `short / normal / expand` shaping 已作用到 current chat mainline
  - repo-wide full verify 通过
- `M4 Host-Governed Cadence` 已完成代码落地：
  - `response_plan` 现在会保留 `chat_cadence_mode`
  - current Telegram mainline 现在支持 host-governed：
    - `reply_now_short`
    - `reply_now_normal`
    - `reply_now_expand`
    - `hold_for_followup`
  - `hold_for_followup` 只在 ordinary chat + host policy allow + 非显式问题时进入现有 proactive substrate
  - `TelegramRuntimeFallbackRunner` 现在会保留 runtime reply metadata，避免 cadence / expression hints 在 Telegram adapter 层丢失
  - focused tests、lint、`verify_repo.py --mode fast` 已通过
  - repo-wide `verify_repo.py --mode full` 已验证到全量 EgoCore suite 通过，但 OpenEmotion Windows interop 包装层未在本轮可接受时间内返回，当前按 verification blocker 记录
- `M5 Fresh Real Telegram Proof` 已完成首轮 fresh-window 复盘：
  - deploy commit = `72148b3`
  - current artifact:
    - `artifacts/telegram_real_mainline_v1/dashboard_v1/LIVE_CHAT_SUBJECTIVE_VARIABILITY_CURRENT.md`
    - `artifacts/telegram_real_mainline_v1/dashboard_v1/LIVE_CHAT_SUBJECTIVE_VARIABILITY_CURRENT.json`
  - 当前 fresh window 共有 `6` 条真实样本
  - 样本分布为：
    - `non_ordinary = 4`
    - `ordinary_text_policy_or_control = 2`
    - `ordinary_chat_mainline = 0`
  - 因此当前没有 fresh ordinary-chat mainline 样本，也没有可用来证明 richer fields / tendency delta / cadence delta 的窗口
  - `M5` 当前结论是 blocker，不是 pass
- 下一步需要人为补一个 fresh ordinary-chat Telegram 窗口，再重跑 proof 脚本
