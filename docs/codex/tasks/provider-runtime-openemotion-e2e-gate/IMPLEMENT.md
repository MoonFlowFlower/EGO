# Provider / Runtime OpenEmotion E2E Gate - IMPLEMENT

## Current slice

当前已实现到：

- `Milestone 2: Repo Workflow Adoption`
- `Milestone 3: Harness / Script Integration`
- `Milestone 4: First Admission Run`

## Provider/runtime admission checklist

以后任何命中本 gate 的改动，发布前至少按这个顺序过：

1. `config consistency`
   - 检查 `default_provider/default_model`
   - 检查各 use-case：`chat / execution / planning / reporting / memory_summary`
   - 检查代码里是否还有旧 provider/model 硬编码

2. `chat smoke`
   - 用当前正式 `chat` use-case 做一次真实最小请求
   - 目标：证明聊天链路不是纸面配置

3. `execution tool-calling smoke`
   - 用当前正式 `execution` use-case 做一次真实工具调用
   - 目标：证明 native loop / decision path 不是掉回旧 provider

4. `Telegram fresh task flow`
   - `/new`
   - 一条普通 chat
   - 一条 task request
   - 至少一次 task completion

5. `OpenEmotion artifact check`
   - fresh sample 下必须存在：
     - `openemotion_result.json`
     - `openemotion_trace.json`
     - `response_plan.json`
   - 若 task/mainline 本应命中主体但缺这些文件，直接 blocker

6. `follow-up continuity check`
   - 在同 session 里追问刚完成对象，例如：
     - “你觉得你做的这个页面怎么样呀”
     - “你还记得刚刚做的网页吗”
   - 若系统把刚交付结果忘掉、重新让用户指认对象，直接 blocker

7. `artifact / dashboard consistency check`
   - 当前 evidence、audit、dashboard 不得把 provider split 误写成正常主链
   - 若 live reply 成功但 artifacts 记录显示 host degraded fallback / old provider contamination，直接 blocker

## Minimum command set

以下命令集合是最低建议，不是上限：

```bash
python3 -m py_compile path/to/touched_runtime_files.py
python3 scripts/codex/lint_repo.py
python3 scripts/codex/verify_repo.py --mode fast
python3 scripts/codex/run_provider_runtime_openemotion_e2e_gate.py --session-key <telegram:...>
```

若命中 provider/runtime 主链，额外至少补：

```bash
PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest <focused runtime/provider tests> -q -s
python3 scripts/run_telegram_real_channel_capture.py --validate-latest
```

若改动高风险、或已经发生过 live split/provider contamination，收口前再补：

```bash
python3 scripts/codex/verify_repo.py --mode full
```

## Trigger matrix

以下改动默认触发本 gate：

- `EgoCore/config/llm.yaml`
- `EgoCore/app/llm_client.py`
- `EgoCore/app/agent_core/native_loop.py`
- `EgoCore/app/runtime_v2/*` 中涉及 provider selection / chat / decision 的改动
- `EgoCore/app/telegram_bot.py`
- `EgoCore/app/openemotion_hooks/*`
- 任何会改变 Telegram 主链 provider/fallback/contract 的配置或代码

以下改动通常不单独触发本 gate，但若与上面变更同批出现，仍一起纳入：

- 纯文档改动
- 纯样式/UI 文案
- 与 provider/runtime 无关的 OpenEmotion 内部语义单测修复

## Claim ceiling

在 7 项 gate 没全部通过前，只允许使用这些口径：

- `局部接线完成`
- `条件性完成`
- `已证明 chat/execution 局部可用，但 E2E 未完成`
- `blocked_on_openemotion_evidence`
- `blocked_on_followup_continuity`

禁止使用：

- `切换完成`
- `live 已恢复`
- `主链稳定`
- `OpenEmotion 已一路验证通过`

## Evidence to preserve

每次按本 gate 收口时，至少保留：

- config diff / provider selection evidence
- real smoke result
- fresh Telegram sample id
- `openemotion_result.json`
- `openemotion_trace.json`
- `response_plan.json`
- 至少一条 follow-up continuity 正证据

## Current implementation notes

- gate runner 会自动把指定 session 收窄到最新 `/new` window，避免同一 Telegram DM 的历史样本污染当前 admission
- `--session-key telegram:dm:<id>` 会自动归一化到 real sample 中的 `telegram:private:<id>` 记录
- 当前 gate runner 采用真实 provider request，不 mock：
  - chat smoke 会要求返回 `pong`
  - execution smoke 会要求真实 tool call
- 当前 runner 已顺手封住两处旧 fallback 残留：
  - `EgoCore/app/runtime_v2/decision_engine.py`
  - `EgoCore/app/runtime_v2/chat_reply_engine.py`
  - 它们不再把缺省 fallback 指回旧 `qianfan/glm-5`
