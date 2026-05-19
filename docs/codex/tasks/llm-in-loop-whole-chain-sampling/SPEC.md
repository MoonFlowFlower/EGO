# LLM-in-Loop Whole-Chain Sampling

## Goal

在 `simulated telegram -> unified ingress -> native_loop -> contract_runtime -> llm_client -> openemotion hooks -> delivery` 这条正式主体主线上，做一个 bounded 的 LLM-in-loop simulated sampling，并把 whole-chain artifact 收集到后续可用于真正 replay 的粒度。

## Non-goals

- 不把这条任务重命名成 replay，除非 trace 已经足以在不重新 query model 的前提下重放
- 不做 repo-level state upgrade
- 不做 runtime efficacy claim
- 不改 canonical mainline behavior

## Constraints

- 只走现有 canonical surfaces：`UnifiedIngressRequest/build_unified_ingress`、`TelegramBot._run_primary_turn/_deliver_runtime_v2_result`、`NativeToolCallingLoop`、`ContractRuntimeEngine`、`RuntimeV2ProtoSelfRuntime`
- 允许 simulated Telegram transport shape
- 允许 deterministic fake LLM，但必须完整记录 model request/response
- 不混入真实 Telegram / E4 样本

## Required path

- `simulated telegram -> unified ingress -> native_loop -> contract_runtime -> llm_client -> openemotion hooks -> delivery`

## Required artifacts

- ingress event
- normalized event
- native_loop trace
- contract_runtime trace
- model request/response
- tool calls/returns if any
- OpenEmotion structured output
- EgoCore response plan
- delivery record
- timeline/tape artifact

## Acceptance criteria

- [ ] bounded sample set 全部走到 `native_loop`
- [ ] 每个成功样本都产出完整 evidence bundle 与 whole-chain extra traces
- [ ] model request/response 已完整落盘，可供后续 whole-chain replay 使用
- [ ] 失败样本不 silent drop，必须进 failures table
- [ ] 最终报告明确写清 E2/E3 口径下能证明什么、不能证明什么

## Claim ceiling

- 允许：`bounded simulated whole-chain LLM-in-loop sampling complete`
- 不允许：`runtime efficacy proven`
- 不允许：`whole-chain replay proven`，除非 trace 充分性已经被单独证明
- 不允许：`repo-level enabled`

## Authority refs

- `README.md`
- `docs/CURRENT_PROJECT_LOGIC_FLOW.md`
- `EgoCore/app/telegram_bot.py`
- `EgoCore/app/runtime_v2/unified_channel_contract.py`
- `EgoCore/app/agent_core/native_loop.py`
- `EgoCore/app/agent_core/contract_runtime.py`
- `EgoCore/app/telegram_evidence_collector.py`
