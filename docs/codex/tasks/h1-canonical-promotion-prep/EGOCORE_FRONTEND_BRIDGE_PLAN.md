# EgoCore Frontend Bridge Plan

## Goal

给 canonical `shadow_h1` 提供一个最小 EgoCore read-only bridge。

这座桥只负责：

- 把 OpenEmotion 的 `shadow_h1` telemetry 暂存在 `state.proto_self_context`
- 让 observation / dashboard / replay capture 能看见它

这座桥不负责：

- 影响 host decision
- 影响 prompt
- 影响 output_check

## Minimal Bridge Path

### 1. Adapter Layer

优先保持 `EgoCore/app/openemotion_adapter/proto_self_adapter.py` 不变。

原因：

- `trace_payload` 与 `confidence_meta` 已是现有 passthrough 面
- 本轮不改 schema，不需要新的 adapter authority

只有在 adapter 明确丢弃新增 telemetry keys 时，才允许做最小 passthrough 补丁。

### 2. Runtime Bridge

最小桥接点在：

- `EgoCore/app/runtime_v2/proto_self_runtime.py`

future implementation 只需要在已有 `state.proto_self_context[...]` 赋值区块追加：

- `state.proto_self_context["shadow_h1"]`
- 或等价的只读 telemetry summary

建议来源：

- `proto_self_result["trace_payload"]["shadow_h1"]`
- `proto_self_result["confidence_meta"]` 中的 `shadow_h1_*`

### 3. Frontend / Prompt Boundary

`EgoCore/app/runtime_v2/decision_engine.py` 第一阶段必须保持：

- 不读取 `proto_self_context["shadow_h1"]`
- 不把 `shadow_h1` 写进 `build_policy_hint_context()`
- 不对 LLM prompt 产生任何影响

这样能保证：

- canonical patch 是 `shadow-only`
- host authority 没被悄悄放开

## Where The Bridge May Be Observed

允许的消费面：

- observation harness
- replay capture
- read-only dashboard / artifact summary

不允许的消费面：

- decision prompt
- action arbitration
- delivery selection
- output_check

## Bridge Output Shape

建议 `proto_self_context["shadow_h1"]` 只放 representation-neutral summary：

```json
{
  "enabled": true,
  "action_key": "tool:file",
  "predicted_success": 0.22,
  "threshold": 0.35,
  "would_guard": true,
  "would_ask": true
}
```

不要放：

- private state dumps
- entire self_model
- free-form explanation strings

## Rollback-Safe Rule

如果 bridge 出现问题，最小 rollback 只需要：

- 不再把 `shadow_h1` 写入 `proto_self_context`

这不影响：

- OpenEmotion canonical owner
- existing policy_hint flow
- current runtime mainline

## Validation For The Future Bridge Slice

- 定向 runtime unit test：
  - `shadow_h1` 只在 flag on 时出现
- 定向 decision-engine test：
  - `shadow_h1` 不改变 prompt context
- 定向 observation test：
  - `shadow_h1` 能被 artifact capture 看见
