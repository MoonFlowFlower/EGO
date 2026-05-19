# Feature Flag And Rollback Plan

## Rollout Principle

H1 canonical promotion 的 rollout authority 必须在 EgoCore，而不是 OpenEmotion。

OpenEmotion 只读取一个 host-owned flag，并在 canonical kernel 内决定是否计算 `shadow_h1 telemetry`。

## Flag Topology

### Primary Flag

- name:
  - `proto_self_h1_canonical_shadow`
- owner:
  - EgoCore host runtime
- default:
  - `false`
- transport:
  - 通过现有 `KernelEvent.runtime_summary` 传入 OpenEmotion

### Optional Allowlist

- name:
  - `proto_self_h1_canonical_shadow_allowlist`
- owner:
  - EgoCore host runtime
- purpose:
  - 只允许指定 session / capture run 打开 shadow telemetry

allowlist 不是第二 authority source，它只是 host rollout guard。

## Modes

### Flag Off

- canonical kernel 不计算 `shadow_h1`
- EgoCore 不转发 `shadow_h1`
- observation harness 不要求 `shadow_h1` 字段

### Flag On, Shadow-Only

- canonical kernel 计算 `shadow_h1`
- 只写：
  - `confidence_meta.shadow_h1_*`
  - `trace_payload.shadow_h1`
- EgoCore 只做 telemetry forwarding
- `decision_engine` 不消费

### Explicitly Disallowed In This Task

- public-enable mode
- prompt-injection mode
- delivery-affecting mode

## Rollback Plan

### Fast Rollback

1. 关闭 `proto_self_h1_canonical_shadow`
2. 停止把 `shadow_h1` 从 OpenEmotion 复制到 `state.proto_self_context`
3. 停止 observation capture 中的 `shadow_h1` bundle 扩展

### What Should Happen After Rollback

- runtime behavior 回到当前 canonical baseline
- scorer ontology 不变
- Trial-1 / Trial-2 artifacts 保持只读 evidence status
- repo-level state 不变

### Why Rollback Is Safe

- 不需要删字段
- 不需要 schema migration
- 不需要数据回写
- 即使 state 里残留历史 `counterfactual_success_by_action` 值，只要 live public derivation 不消费 H1，它们就是 inert data

## Rollback Triggers

任何 future implementation 命中下列条件都应立即 rollback：

- `decision_engine` 开始消费 `shadow_h1`
- `policy_hint.ask_preferred` 被 H1 shadow path 改写
- `response_tendency.ask_needed` 被 H1 shadow path 改写
- non-allowlisted session 出现 `shadow_h1`
- E4 样本采集暴露出 host-visible unintended behavior

## Verification After Rollback

- flag off 后，shadow telemetry keys 不再出现
- host prompt context 不新增 H1 内容
- output_check / delivery / response_contract 结果不变
- fast gate 通过；full gate 若有 unrelated 失败，只保留 scoped rollback 结论
