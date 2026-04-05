# MVP21 Host-Governed Initiative Realization / Proactive Delivery Mediation 状态台账

```yaml
phase: WP16
status: maintenance_mode
current_layer: closeout_and_qa_baseline
main_chain_status: current_runtime_initiative_realization_consumer_present_legacy_reference_only
enabled_status: authority_owner_proto_self_runtime_demotion_causal_batch_and_closeout
trigger_evidence:
  - WP15/MVP20 is the predecessor and remains in maintenance_mode
  - WP16 authority package now exists under Tasks/*
  - formal owner target is frozen to OpenEmotion/openemotion/initiative_realization/*
  - current formal runtime mainline target remains runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2
  - formal intake is frozen to runtime_summary initiative_self_context, initiative_context, selfhood_integration_context, maintenance_context, resource_budget_hint, recent_delivery_outcome, idle_window, and host_proactive_context surfaces
  - phase 1 outputs are frozen to initiative_realization_delta, commitment_fulfillment_candidates, delivery_readiness_snapshot, host_lane_hints, controlled_delivery_candidate, initiative_realization_audit_entries, initiative_realization_writeback_candidate, and trace_payload.initiative_realization_context
  - output discipline is frozen to proposal_only true, behavioral_authority none, and required_gate initiative_realization_writeback_gate
  - WP7 proactive runtime chain is frozen as host execution substrate / reference-only, not as initiative realization semantic owner
  - WP8~WP15 remain maintenance / frozen upstreams and may not be reopened by WP16
  - initiative realization formal owner package now exists under OpenEmotion/openemotion/initiative_realization/*
  - owner state now covers realization state, delivery readiness state, commitment fulfillment state, initiative realization candidate, controlled delivery candidate semantics, and realization ledger
  - owner package now includes governance validation, replay/history/store primitives, updater logic, and bounded runtime projection
  - targeted owner infra verification passed in OpenEmotion/tests/mvp21/test_realization_owner_infra.py
  - proto_self_v2 now reads initiative_realization through OpenEmotion/openemotion/proto_self_v2/initiative_realization_context.py
  - KernelOutputV2 and trace now expose initiative_realization_context, initiative_realization_delta, commitment_fulfillment_candidates, delivery_readiness_snapshot, host_lane_hints, controlled_delivery_candidate, initiative_realization_audit_entries, and initiative_realization_writeback_candidate
  - proposal discipline remains proposal_only true, behavioral_authority none, and required_gate initiative_realization_writeback_gate
  - targeted proto-self contract verification passed in OpenEmotion/tests/mvp21/test_realization_proto_self_integration.py
  - EgoCore runtime_v2 now injects initiative_realization_context and host_proactive_context into the formal runtime mainline
  - current runtime records initiative_realization_delta, commitment_fulfillment_candidates, delivery_readiness_snapshot, host_lane_hints, controlled_delivery_candidate, initiative_realization_writeback_candidate, initiative_realization_context, host_proactive_context, and initiative_realization_writeback on bounded host context
  - runtime writeback remains proposal_only true, behavioral_authority none, and required_gate initiative_realization_writeback_gate
  - targeted runtime bridge verification passed in EgoCore/tests/test_runtime_v2_proto_self_runtime.py
  - host proactive runtime / delivery / outbox / transport substrate is now explicitly frozen as host_substrate_only / reference-only to WP16 semantics
  - `OpenEmotion/tools/verify_mvp21_mainline_wiring.py --json` now reports `current_runtime_initiative_realization_consumer_present_legacy_reference_only`
  - `OpenEmotion/tests/mvp21/test_mvp21_mainline_reference_demotion.py` now proves current runtime consumer remains the WP16 formal owner path while host proactive substrate and roadmap materials remain reference-only
  - `OpenEmotion/tests/mvp21/test_realization_causal_formal_proof.py` now proves realization readiness / fulfillment / hold / failure recovery change bounded downstream tendency while text-only changes do not create structural effects
  - `OpenEmotion/tools/run_mvp21_causal_validation.py` now emits `OpenEmotion/artifacts/mvp21/mvp21_causal_validation_current.{json,md}` with `status = pass`, `verification_level = V3`, `evidence_level = E3`, `pair_count = 4`, and `passed_count = 4`
  - `OpenEmotion/tests/mvp21/test_controlled_observation.py` now proves the single controlled runtime-mainline observation path writes a bounded initiative realization report with `initiative_realization_writeback_gate = allow_writeback`, `proposal_only_discipline_consistent = true`, `behavioral_authority_none = true`, `bounded_influence_present = true`, and `replay_valid = true`
  - `OpenEmotion/tools/run_mvp21_controlled_observation.py` now emits `OpenEmotion/artifacts/mvp21/mvp21_controlled_observation_current.{json,md}` with `status = pass`, `verification_level = V4`, `evidence_level = E4`, `initiative_realization_writeback_gate = allow_writeback`, `initiative_realization_proposal_present = true`, `proposal_only_discipline_consistent = true`, `behavioral_authority_none = true`, and `replay_valid = true`
  - `OpenEmotion/scenarios/mvp21_observation_bank/*` now provides a repo-authored realization observation bank covering commitment fulfillment prepare review, delivery failure hold review, and realization follow-up review
  - `OpenEmotion/tests/mvp21/test_controlled_observation_batch.py` now proves the batch aggregate path reaches `report_count = 3`, `accepted_count = 3`, `replay_consistent_count = 3`, `initiative_realization_proposal_present_count = 3`, `proposal_only_discipline_count = 3`, `behavioral_authority_none_count = 3`, and `bounded_influence_present_count = 3`
  - `OpenEmotion/tools/run_mvp21_controlled_observation_batch.py` now emits `OpenEmotion/artifacts/mvp21/mvp21_controlled_observation_batch_current.{json,md}` with `status = pass`, `verification_level = V5`, `evidence_level = E5`, `report_count = 3`, `accepted_count = 3`, `replay_consistent_count = 3`, `proposal_only_discipline_count = 3`, `behavioral_authority_none_count = 3`, and `bounded_influence_present_count = 3`
verification_level: V5
evidence_level: E5
current_blocker: "none on the WP16 controlled-axis maintenance path"
next_minimal_closure_action: "maintenance verification only"
```

## 当前口径

- 可宣称完成：`WP16/MVP21` 已完成 authority freeze、`T10_FORMAL_OWNER_PACKAGE`、`T20_PROTO_SELF_CONTRACT_INTEGRATION`、`T30_EGOCORE_RUNTIME_BRIDGE`、`T40_LEGACY_DEMOTION_AND_COMPAT_MAP`、`T50_CAUSAL_VALIDATION`、`T60_CONTROLLED_OBSERVATION_SINGLE`、`T70_BATCH_OBSERVATION_AND_AGGREGATE` 与 `T80_CLOSEOUT_AND_QA_BASELINE`；当前 formal owner target、authority source、IO contract、legacy demotion 边界、task cards 与 subagent assignment 已冻结为一致 package，formal owner package 已落到 `OpenEmotion/openemotion/initiative_realization/*`，并已通过唯一 bounded consumer path 接到 `proto_self_v2` 与当前 EgoCore runtime 主链，在 formal owner + proposal-only initiative realization writeback + controlled observation 轴上收口进入 `maintenance_mode`
- 条件性完成：当前维护态只覆盖 controlled axis closeout，不扩 authority
- 不可宣称完成：live autonomy、OpenEmotion direct reply authority、tool authority、broader transport claims、或任何 authority release
- 后续处理：后续只允许 maintenance verification、maintenance ledger intake、artifact refresh、bugfix 或 wording correction；不得借机扩 `WP16` scope 或创建 `WP17` authority docs

## 边界提醒

- `WP15` 保持 `maintenance_mode`，不是 `WP16` 的 fallback owner
- `WP16` 只能读取 `WP7~WP15` 的冻结 surfaces，不能直接回写 upstream owner state
- `host_proactive_context` 当前只是 host hint surface target，不是 host authority transfer
- 不得出现“因为已有 initiative realization，所以 OpenEmotion 可以直接说话 / 直接发工具 / 直接拿 transport claim / 直接入 outbox”这类边界回退
