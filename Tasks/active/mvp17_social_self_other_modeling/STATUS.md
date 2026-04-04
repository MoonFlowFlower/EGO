# MVP17 Social Self / Other-Modeling 状态台账

```yaml
phase: WP12
status: observation_started
current_layer: observation
main_chain_status: formal_owner_writeback_observed
enabled_status: controlled_mainline_observation
trigger_evidence:
  - WP11/MVP16 controlled observation V5/E5 pass
  - WP11 remains maintenance_mode
  - WP12 authority package present under Tasks/*
  - social_self formal owner package present under OpenEmotion/openemotion/social_self/*
  - proto_self_v2 consumes runtime_summary.social_self_context and social_context through bounded contract
  - runtime_v2 injects social_self_context and social_context through the current proto_self mainline
  - governed social writeback candidate reaches the current runtime mainline with behavioral_authority locked to none
  - EgoCore runtime bridge regression passed for social and adjacent owner families
  - legacy social / relation surfaces are explicitly classified as reference-only or input-only
  - current mainline wiring verifier confirms the formal owner path is active while legacy surfaces stay demoted
  - paired causal validation proves trust / commitment / boundary shifts alter bounded downstream social weighting
  - text-only social event wording changes do not create false downstream behavioral proof
  - single controlled observation report passes with social_writeback_gate allow_writeback and behavioral_authority none
verification_level: V4
evidence_level: E4
current_blocker: "Batch controlled observation and aggregate are still pending; no E5 stability claim yet"
next_minimal_closure_action: "implement T70_BATCH_OBSERVATION_AND_AGGREGATE before closeout work"
```

## 当前口径

- 可宣称完成：`WP12/MVP17` 已完成 `T10/T20/T30/T40/T50/T60`，并已拿到首个 controlled mainline `V4/E4` social proposal-only writeback 样本
- 条件性完成：`MVP17` 已进入 `observation_started`，formal owner + current runtime mainline 的 bounded social bridge 已被单样本 controlled observation 证实；但重复样本和 aggregate 还没完成
- 不可宣称完成：`MVP17` 已达 `E5`、已收口、已进入 `maintenance_mode`、或已具备 live social autonomy / direct reply authority / broader transport claims
- 后续处理：只能按 `cards/` 串行执行，不得回头扩写 `WP12` authority 包

## 边界提醒

- `WP11` 的轴内 `E5` 不是 `WP12` 的实现证据
- `WP11` 新样本只写入其 maintenance ledger
- provider `429/401` 仍按外部预算层风险记录
- `social_self/*` 当前已证明 owner 层、`proto_self_v2` bounded consumer、EgoCore runtime thin bridge、旧 social / relation surfaces 的 reference-only / input-only demotion、trust / commitment / boundary 变化对 bounded downstream weighting 的 causal 影响，以及单样本 controlled mainline social writeback；仍不证明 `E5` 稳定性或维护态成立
- 不得出现“因为 `WP11` 已 pass，所以 social self 可以直接外发 / 直接拿 transport claim”这类边界回退
