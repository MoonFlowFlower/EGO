# MVP18 Embodied Loop / Environment Coupling 状态台账

```yaml
phase: WP13
status: observation_started
current_layer: implementation
main_chain_status: current_runtime_embodied_consumer_present_legacy_reference_only
enabled_status: controlled_mainline_observation
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
  - legacy consequence / intervention historical surfaces explicitly classified as technical reference, reference-only, or input-only
  - `OpenEmotion/tools/verify_mvp18_mainline_wiring.py` now proves current runtime embodied consumer presence plus no-second-truth legacy demotion
  - `OpenEmotion/tests/mvp18/test_mainline_reference_demotion.py` now proves legacy consequence / intervention surfaces remain demoted
  - paired causal validation now proves resource/slack pressure, consequence memory, and self/world boundary pressure alter bounded downstream embodied weighting
  - text-only outcome wording changes without metric shift do not create false downstream embodied behavioral proof
  - `OpenEmotion/tools/run_mvp18_controlled_observation.py` now produces the first controlled runtime-mainline embodied proposal-only writeback artifact
  - `OpenEmotion/tests/mvp18/test_controlled_observation.py` now locks the single-sample controlled observation contract
  - `OpenEmotion/tools/run_mvp18_controlled_observation_batch.py` now produces the first repeated controlled runtime-mainline embodied aggregate artifact
  - `OpenEmotion/tests/mvp18/test_controlled_observation_batch.py` now locks the batch controlled observation contract
  - current single controlled observation artifact reports `status = pass`, `verification_level = V4`, `evidence_level = E4`
  - current batch controlled observation artifact reports `status = pass`, `verification_level = V5`, `evidence_level = E5`
  - current batch controlled observation artifact reports `report_count = 3`, `accepted_count = 3`, `proposal_only_discipline_count = 3`, `behavioral_authority_none_count = 3`
verification_level: V5
evidence_level: E5
current_blocker: "T80 closeout / QA baseline pending"
next_minimal_closure_action: "start T80_CLOSEOUT_AND_QA_BASELINE; do not claim maintenance_mode before T80"
```

## 当前口径

- 可宣称完成：`WP13/MVP18` 已完成 `T70_BATCH_OBSERVATION_AND_AGGREGATE`，当前 formal owner path、current runtime embodied consumer、legacy no-second-truth demotion、bounded embodied causal proof、首个 controlled `V4/E4` 样本与 repeated controlled `V5/E5` aggregate 已同时成立
- 条件性完成：当前只证明 repeated controlled observation aggregate 已成立，不覆盖 closeout、`maintenance_mode`、或 authority 放开
- 不可宣称完成：`MVP18` 已收口、已进入 `maintenance_mode`，或已放开 live autonomy / direct reply authority / broader transport claims
- 后续处理：只能按 `T70 -> T80` 串行推进；不得回头扩写 `WP12`

## 边界提醒

- `WP12` 的 institutionalized maintenance 不是 `WP13` 的实现证据
- `WP12` 新样本只写入其 maintenance ledger
- provider `429/401` 仍按外部预算层风险记录
- `embodied_self/*` 当前已是 formal owner 落点，且 current runtime thin bridge + `T40` legacy demotion + `T50` causal proof + `T60` single controlled observation + `T70` batch aggregate 已接入；但还没有 closeout / QA baseline
- 不得出现“因为 `WP12` 已 institutionalized，所以 embodied loop 可以直接外发 / 直接拿 transport claim”这类边界回退
