# MVP20 Host-Governed Self-Directed Initiative / Commitment Continuity 状态台账

```yaml
phase: WP15
status: owner_package_complete
current_layer: owner_package
main_chain_status: planning_only_no_current_runtime_consumer
enabled_status: not_enabled
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
verification_level: V2
evidence_level: E3
current_blocker: "none on the WP15 owner-package axis"
next_minimal_closure_action: "T20_PROTO_SELF_CONTRACT_INTEGRATION"
```

## 当前口径

- 可宣称完成：`WP15/MVP20` 已完成 `T10_FORMAL_OWNER_PACKAGE`，formal owner 已落到 `OpenEmotion/openemotion/initiative_self/*`
- 条件性完成：当前只覆盖 owner 层 schema/state/store/governance/replay/projection 与定向 owner-infra 验证；不覆盖 proto-self contract、EgoCore runtime、observation 或 maintenance
- 不可宣称完成：`MVP20` 已实现、已接主链、已 observation_started、已有 `E4/E5`、或已进入 `maintenance_mode`
- 后续处理：下一步只能进入 `T20_PROTO_SELF_CONTRACT_INTEGRATION`，不能跳过 bounded contract 直接做 runtime 或 observation

## 边界提醒

- `WP7` 的 host-governed proactive chain 不是 `WP15` 的 semantic owner
- `WP15` 只能读取 `WP8~WP14` 的冻结 surfaces，不能直接回写 upstream owner state
- `initiative_context` 当前只是 host hint surface target，不是 host authority transfer
- 不得出现“因为已有 initiative continuity，所以 OpenEmotion 可以直接说话 / 直接发工具 / 直接拿 transport claim”这类边界回退
