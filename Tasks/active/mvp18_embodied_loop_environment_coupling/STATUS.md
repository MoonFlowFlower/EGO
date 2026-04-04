# MVP18 Embodied Loop / Environment Coupling 状态台账

```yaml
phase: WP13
status: runtime_bridge_complete
current_layer: implementation
main_chain_status: embodied_runtime_bridge_present
enabled_status: not_started
trigger_evidence:
  - WP12/MVP17 maintenance institutionalization complete
  - WP12 remains maintenance_mode
  - WP13 authority package present under Tasks/*
  - embodied_self formal owner package present under OpenEmotion/openemotion/embodied_self/*
  - owner state covers embodied, environment coupling, resource pressure, boundary pressure, action consequence memory, and self-world boundary semantics
  - owner store, replay, governance, and bounded runtime projection tests passed
  - proto_self_v2 consumes runtime_summary.embodied_self_context and environment_context through a bounded embodied contract
  - KernelOutputV2 emits embodied_self_delta, consequence_update_candidates, resource_boundary_snapshot, embodied_policy_hints, repair_or_stabilize_proposal_candidates, and embodied_writeback_candidate
  - trace payload mirrors environment_context without promoting legacy consequence or intervention surfaces
  - embodied outputs remain proposal_only with behavioral_authority locked to none
  - EgoCore runtime_v2 now injects embodied_self_context and environment_context into the current proto-self mainline
  - Runtime proto_self_context now records embodied_self_delta, consequence_update_candidates, resource_boundary_snapshot, embodied_policy_hints, repair_or_stabilize_proposal_candidates, embodied_writeback_candidate, environment_context, and embodied_writeback
  - embodied writeback remains gated by embodied_writeback_gate and proposal_only with behavioral_authority none
  - EgoCore runtime embodied bridge tests passed in test_runtime_v2_proto_self_runtime.py
  - legacy consequence / intervention surfaces explicitly classified as reference-only or input-only
verification_level: V3
evidence_level: E3
current_blocker: "T40 legacy demotion / compat map pending"
next_minimal_closure_action: "start T40_LEGACY_DEMOTION_AND_COMPAT_MAP; do not implement observation before T40/T50"
```

## 当前口径

- 可宣称完成：`WP13/MVP18` 已完成 `T30_EGOCORE_RUNTIME_BRIDGE`，当前 EgoCore runtime 主线已注入 embodied_self_context / environment_context，并记录 gated embodied proposal-only outputs
- 条件性完成：当前只证明 owner 层、`proto_self_v2` bounded contract 与 EgoCore runtime thin bridge 已成立，不覆盖 legacy demotion、causal proof、controlled observation、或 `E4/E5`
- 不可宣称完成：`MVP18` 已实现、已接主链、已启用、或已有 `E4/E5`
- 后续处理：只能按 `T40 -> T50 -> T60 -> T70 -> T80` 串行推进；不得回头扩写 `WP12`

## 边界提醒

- `WP12` 的 institutionalized maintenance 不是 `WP13` 的实现证据
- `WP12` 新样本只写入其 maintenance ledger
- provider `429/401` 仍按外部预算层风险记录
- `embodied_self/*` 当前已是 formal owner 落点，且当前 runtime thin bridge 已接入；但还没有 `T40` legacy demotion、`T50` causal proof、single controlled observation、或 batch aggregate evidence
- 不得出现“因为 `WP12` 已 institutionalized，所以 embodied loop 可以直接外发 / 直接拿 transport claim”这类边界回退
