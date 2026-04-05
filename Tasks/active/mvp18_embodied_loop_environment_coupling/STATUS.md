# MVP18 Embodied Loop / Environment Coupling 状态台账

```yaml
phase: WP13
status: maintenance_mode
current_layer: maintenance
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
  - `OpenEmotion/tests/mvp18/test_mvp18_mainline_reference_demotion.py` now proves legacy consequence / intervention surfaces remain demoted
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
current_blocker: "none on the WP13 controlled axis"
next_minimal_closure_action: "maintenance intake only; do not reopen WP13 or start WP14 without a new authority package"
```

## 当前口径

- 可宣称完成：`WP13/MVP18` 已在 formal owner path、current runtime embodied consumer、legacy no-second-truth demotion、bounded embodied causal proof、single controlled `V4/E4` 样本与 repeated controlled `V5/E5` aggregate 全部成立后，正式收口进入 `maintenance_mode`
- 条件性完成：当前维护态只覆盖 formal owner + proposal-only embodied writeback + controlled observation 这一条轴，不覆盖 authority 放开
- 不可宣称完成：`MVP18` 已证明 live autonomy、direct reply authority、broader transport claims，或可绕过 host governance
- 后续处理：`WP13` 后续样本只进入 maintenance ledger；不得回头扩写 `WP12`

## 边界提醒

- `WP12` 的 institutionalized maintenance 不是 `WP13` 的实现证据
- `WP12` 新样本只写入其 maintenance ledger
- provider `429/401` 仍按外部预算层风险记录
- `embodied_self/*` 当前已是 formal owner 落点，且 current runtime thin bridge + `T40` legacy demotion + `T50` causal proof + `T60` single controlled observation + `T70` batch aggregate + `T80` closeout / QA baseline 已冻结
- 不得出现“因为 `WP12` 已 institutionalized，所以 embodied loop 可以直接外发 / 直接拿 transport claim”这类边界回退
