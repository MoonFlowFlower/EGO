# LLM-in-Loop Whole-Chain Sampling - EXPLORE

## E00

- question:
  - 当前 whole-chain 验证最小可行切点是什么？
- hypothesis:
  - 手动复用 `TelegramBot` 内部 canonical steps，比直接 drive `handle_message()` 更容易精确落 ingress/contract/model artifacts，且不改变主链
- experiment:
  - 核对 `TelegramBot._build_unified_telegram_request -> build_unified_ingress -> _ensure_subject_ingress -> _run_primary_turn -> _deliver_runtime_v2_result`
- result:
  - 这条切点完整覆盖 required path，且 `TelegramEvidenceCollector` 已能自动产出 `normalized_event / openemotion_result / response_plan / outbox_record / timeline / tape / replay`
- decision:
  - continue
