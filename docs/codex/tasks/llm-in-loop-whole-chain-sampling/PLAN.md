# LLM-in-Loop Whole-Chain Sampling - PLAN

## Task summary

用 deterministic fake LLM 驱动正式主体主链，收集 whole-chain sample bundles 与 replay-grade model/tool/runtime traces，但不把这条任务本身叙述成 replay。

## Execution mode

- mode: implementation
- why this mode:
  - 当前目标、路径和 artifact contract 已经明确，重点是最小实现 slice 与验证

## Milestones

### Milestone 1: Freeze bounded sample set and artifact contract

- scope:
  - task docs
  - runner artifact schema
- acceptance:
  - bounded sample set ≤ 3
  - extra trace files 清单冻结
- status at close:
  - `continue`

### Milestone 2: Implement whole-chain simulated runner

- scope:
  - `scripts/codex/run_llm_in_loop_whole_chain_sampling.py`
  - `scripts/codex/verify_llm_in_loop_whole_chain_sampling.py`
- acceptance:
  - runner 通过 TelegramBot canonical path 产出 sample bundles
  - baseline-free single current-path sampling 完成
- status at close:
  - `continue`

### Milestone 3: Verify and close

- scope:
  - targeted test
  - scoped verification
  - final task status
- acceptance:
  - py_compile pass
  - targeted pytest pass
  - runner pass
  - verifier pass
  - `verify_repo.py --mode fast` pass
- status at close:
  - `close`

## Bounded sample set

1. `C1_create_html_intro`
2. `C2_create_html_openemotion`

理由：
- 都能稳定命中 `execute_task -> native_loop -> contract_runtime -> llm_client -> file tool -> finalized delivery`
- 不需要引入额外 source / dataset / operator
- 已足够覆盖 tool-call + reply + OpenEmotion finalized result + delivery

## Risks

- `TelegramBot` 内部 progress/update side-effect 可能污染 outbox 账本
- fake LLM 必须保存完整 request/response，否则不能宣称 replay-ready traces
- 这条任务仍然只到 simulated / E2/E3，不能越口径

## Outcome

- Milestone 1: close
- Milestone 2: close
- Milestone 3: close

## Decision log

- 用 deterministic fake LLM 保持 `llm_client` 在环，同时让 request/response 可完整落盘
- 没有直接 drive `handle_message()`，而是复用 `TelegramBot` 内部 canonical steps，精确抓取 ingress/native_loop/contract_runtime/model/delivery artifacts
- whole-chain extra traces 作为 shadow-only artifact 写入 sample 目录，不改 canonical mainline behavior
- 当前结果停在 bounded simulated whole-chain sampling，不升级 repo-level state
