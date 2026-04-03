# WP10 / MVP15 Reflection Capability Ownership

## Purpose

冻结 `WP10/MVP15` 的 capability ownership，防止 reflection / counterfactual / proposal / audit 能力在 `OpenEmotion`、`EgoCore`、compatibility adapter 之间再次形成双真相源或职责偷换。

## Formal Ownership Table

| Capability | Formal owner | Bounded consumer / bridge | Explicit non-owner |
|---|---|---|---|
| reflective state | `OpenEmotion/openemotion/reflective_self/*` | `proto_self_v2` 只可读 bounded reflection context | `EgoCore`, `emotiond/reflection_engine/*`, `reflection_adapter.py`, `reflection_shadow.py` |
| diagnosis records | `OpenEmotion/openemotion/reflective_self/*` | governed downstream proposal / audit path | final reply / delivery surfaces |
| counterfactual records | `OpenEmotion/openemotion/reflective_self/*` | bounded counterfactual summary consumers | direct action selection surfaces |
| revision proposal candidates | `OpenEmotion/openemotion/reflective_self/*` | governed proposal gate path | transport / tool / direct policy mutation |
| drive owner state | `OpenEmotion/openemotion/endogenous_drives/*` | `WP10` 只读 frozen drive projection | `WP10` reflection owner path |
| self-model owner state | `OpenEmotion/openemotion/self_model/*` | `WP10` 只读 frozen self-model projection | `WP10` reflection owner path |
| runtime scheduling / delivery / transport | `EgoCore` | n/a | `WP10` reflection owner path |
| final reply authority | `EgoCore` | n/a | `WP10` reflection owner path |
| tool execution authority | `EgoCore` + Governor | n/a | `WP10` reflection owner path |

## Hard Rules

- `OpenEmotion/openemotion/reflective_self/*` 是 `WP10` formal owner target
- `proto_self_v2` 可以消费 bounded reflection context，但不能拥有 reflective state
- `emotiond/reflection_engine/*`、`reflection_adapter.py`、`reflection_shadow.py`、`self_counterfactual.py` 只保留 bounded compatibility / migration / replay-friendly access semantics
- `EgoCore` 可以调度、裁决、投递，但不能伪造或重写 reflection owner state
- reflection / counterfactual 输出必须保持 `proposal_only`

## Forbidden Ownership Drift

- 不把 `emotiond/reflection_engine/*` 保留为长期 formal owner
- 不把 `reflection_adapter.py` 升格为 formal owner
- 不把 `reflection_shadow.py` 升格为 formal owner
- 不把 `self_counterfactual.py` 升格为 formal owner
- 不把 reflection / counterfactual 权限升级成 final reply / tool / transport authority
