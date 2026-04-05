# MVP20 Host-Governed Self-Directed Initiative / Commitment Continuity 状态台账

```yaml
phase: WP15
status: runtime_bridge_complete
current_layer: implementation
main_chain_status: current_runtime_initiative_consumer_present_legacy_demotion_pending
enabled_status: current_runtime_wired_not_observed
trigger_evidence:
  - WP14/MVP19 is the predecessor and remains the last completed maintenance upstream
  - WP15 authority package now exists under Tasks/*
  - formal owner target is frozen to OpenEmotion/openemotion/initiative_self/*
  - current formal runtime mainline target remains runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2
  - formal intake is frozen to runtime_summary selfhood_integration, self_model, endogenous_drive, reflective_self, developmental_self, social_self, embodied_self, maintenance, resource_budget_hint, recent_delivery_outcome, idle_window, and initiative_context surfaces
  - phase 1 outputs are frozen to initiative_self_delta, initiative_proposal_candidates, commitment_execution_snapshot, initiative_policy_hints, host_proactive_candidate, initiative_audit_entries, initiative_writeback_candidate, and trace_payload.initiative_context
  - output discipline is frozen to proposal_only true, behavioral_authority none, and required_gate initiative_writeback_gate
  - WP7 host proactive chain is frozen as host execution substrate / reference-only, not as initiative semantic owner
  - WP8~WP14 remain maintenance / frozen upstreams and may not be reopened by WP15
  - selfhood initiative formal owner package now exists under OpenEmotion/openemotion/initiative_self/*
  - owner state now covers initiative state, initiative priority state, commitment continuity state, initiative proposal candidate, host proactive candidate semantics, and initiative ledger
  - owner package now includes governance validation, replay/history/store primitives, updater logic, and bounded runtime projection
  - targeted owner infra verification passed in OpenEmotion/tests/mvp20/test_initiative_owner_infra.py
  - proto_self_v2 now reads initiative_self through OpenEmotion/openemotion/proto_self_v2/initiative_self_context.py
  - KernelOutputV2 and trace now expose initiative_self_delta, initiative_proposal_candidates, commitment_execution_snapshot, initiative_policy_hints, host_proactive_candidate, initiative_audit_entries, initiative_writeback_candidate, and trace_payload.initiative_context
  - proposal discipline remains proposal_only true, behavioral_authority none, and required_gate initiative_writeback_gate
  - targeted proto-self contract verification passed in OpenEmotion/tests/mvp20/test_initiative_proto_self_integration.py
  - EgoCore runtime_v2 now injects initiative_self_context and initiative_context into the formal runtime mainline
  - current runtime mainline now records initiative_self_delta, initiative_proposal_candidates, commitment_execution_snapshot, initiative_policy_hints, host_proactive_candidate, initiative_audit_entries, initiative_writeback_candidate, initiative_context, and initiative_writeback in bounded host context
  - initiative writeback remains gated to initiative_writeback_gate with proposal_only discipline and behavioral_authority none
  - targeted runtime bridge verification passed in EgoCore/tests/test_runtime_v2_proto_self_runtime.py -k initiative
verification_level: V3
evidence_level: E3
current_blocker: "none on the WP15 runtime-bridge axis"
next_minimal_closure_action: "T40_LEGACY_DEMOTION_AND_COMPAT_MAP"
```

## 当前口径

- 可宣称完成：`WP15/MVP20` 已完成 `T30_EGOCORE_RUNTIME_BRIDGE`，当前 EgoCore runtime 主链已接入 bounded initiative context 与 gated initiative writeback
- 条件性完成：当前只覆盖 owner 层 + proto-self contract + EgoCore runtime bridge；不覆盖 legacy demotion、causal proof、controlled observation 或 maintenance
- 不可宣称完成：`MVP20` 已实现、已接主链、已 observation_started、已有 `E4/E5`、或已进入 `maintenance_mode`
- 后续处理：下一步只能进入 `T40_LEGACY_DEMOTION_AND_COMPAT_MAP`，不能跳过 demotion 直接做 causal proof 或 observation

## 边界提醒

- `WP7` 的 host-governed proactive chain 不是 `WP15` 的 semantic owner
- `WP15` 只能读取 `WP8~WP14` 的冻结 surfaces，不能直接回写 upstream owner state
- `initiative_context` 当前只是 host hint surface target，不是 host authority transfer
- 不得出现“因为已有 initiative continuity，所以 OpenEmotion 可以直接说话 / 直接发工具 / 直接拿 transport claim”这类边界回退
