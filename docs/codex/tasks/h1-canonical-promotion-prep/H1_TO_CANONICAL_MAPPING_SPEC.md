# H1 To Canonical Mapping Spec

## Decision

`H1 counterfactual low-success guard` 可以表达为现有 canonical `proto_self` surface 的小改，不需要先做 `canonical-contract-stabilization first`。

前提只有一个：**第一阶段必须是 shadow-only telemetry，不得直接接入 live public decision path。**

## Why The Decision Is Yes

- canonical state 已有：
  - `SelfModel.counterfactual_success_by_action`
  - `SelfModel.recent_correction_tags`
  - `DriveField.viability_pressure`
- canonical output 已有：
  - `policy_hint`
  - `response_tendency`
  - `confidence_meta`
  - `trace_payload`
- EgoCore 已有：
  - `state.proto_self_context`
  - runtime observation harness

因此不需要：

- 新 schema
- 新 proto-self engine
- 新 scorer ontology
- repo-level state upgrade

## Bounded H1 Mechanism

Trial-2 的 H1 不是“意识机制”，也不是“通用 MVS 因果核心”。它只是：

- 在现有 hard set + 现有 scorer 下
- 一个 bounded active public driver
- 形式为：
  - 对某动作族的预测成功率显著偏低
  - 该低成功率触发 guard
  - guard 在 public 面上表现为更倾向 `ask / cautious / request replan`

canonical promotion prep 只把这条研究结果翻译为：

- 一个 canonical shadow telemetry candidate
- 供后续 E4 样本采集
- 不直接改变 host behavior

## Mapping Table

| Research construct | Canonical expression | Owner surface | Shadow-only use now | Explicitly not done now |
|---|---|---|---|---|
| bounded H1 action key | `perceived["action_class_seed"]` | `appraisal.py` | 作为 canonical action-family key | 不引入 Trial probe key |
| low predicted success | `SelfModel.counterfactual_success_by_action[action_key]` | `state.py` + `self_model.py` | 维护 shadow success estimate | 不直接驱动 live `ask_preferred` |
| recent corrective evidence | `SelfModel.recent_correction_tags[action_key]` | `state.py` + `self_model.py` | 作为邻接解释与 shadow evidence | 不单独当 H1 verdict |
| supporting tension | `DriveField.viability_pressure` | `state.py` + `appraisal.py` | 作为 neighboring explanation guardrail | 不改 scorer ontology |
| H1 public guard candidate | `trace_payload["shadow_h1"]` | `kernel.py` / reducer derivation | 记录 would-guard / would-ask | 不进入 live host policy |
| H1 confidence summary | `confidence_meta["shadow_h1_*"]` | `kernel.py` | 记录阈值、预测值、action_key | 不当成 efficacy claim |
| future public landing zone | `policy_hint.ask_preferred` + `policy_hint.shadow_counterfactual_guard` + `response_tendency.ask_needed` | `reducers.py` | 只作为 future target surface | 当前不启用 |

## Canonical Output Shape For Shadow Mode

建议第一阶段只新增这类 telemetry，不新增 schema：

```json
{
  "confidence_meta": {
    "shadow_h1_enabled": true,
    "shadow_h1_action_key": "tool:file",
    "shadow_h1_predicted_success": 0.22,
    "shadow_h1_threshold": 0.35,
    "shadow_h1_would_guard": true
  },
  "trace_payload": {
    "shadow_h1": {
      "action_key": "tool:file",
      "predicted_success": 0.22,
      "threshold": 0.35,
      "would_guard": true,
      "would_ask": true,
      "source": "canonical_shadow",
      "neighboring_signals": {
        "recent_correction_tag": 0.9,
        "viability_pressure": 0.55
      }
    }
  }
}
```

这保持：

- scorer ontology 不变
- host authority 不变
- future challenger 可共用同一 observation ontology

## Required Separation

当前 canonical reducer 里，`counterfactual_success_by_action` 一旦变成 live input，就可能把 `lowest_prediction < 0.35` 推到 `ask_preferred`。因此 canonical promotion 必须先做隔离：

- `state write` 可以存在
- `shadow telemetry derivation` 可以存在
- **live public derivation 不能在 shadow 阶段消费 H1**

这不是可选优化，而是当前 mapping 的硬边界。

## Authority Boundary

- authority implementation 未来只能落在 `OpenEmotion/openemotion/proto_self/*`
- `Trial-1` / `Trial-2` 目录与 `trial1_shadow.py` 只保留为 evidence source
- EgoCore 只做 host-owned flag、read-only forwarding、observation capture

## Promotion Ceiling

当前 mapping spec 只支持下面这个口径：

> H1 can be translated into canonical proto_self as a shadow-only telemetry candidate.

当前不支持：

- `H1 已接入 canonical mainline 生效`
- `H1 已经是 runtime active driver`
- `H1 已经击败 challenger`
