# WP11 / MVP16 Developmental Capability Ownership

## Purpose

冻结 `WP11/MVP16` 的 capability ownership，防止 developmental continuity / adaptation / promotion / audit 能力在 `OpenEmotion`、`EgoCore`、compatibility adapter 之间再次形成双真相源或职责偷换。

## Ownership Table

| Capability | Formal Owner | Allowed Readers | Forbidden Owner Path |
|------------|--------------|-----------------|----------------------|
| developmental self state | `OpenEmotion/openemotion/developmental_self/*` | `proto_self_v2` bounded projection | `emotiond/developmental/*` |
| continuity state / trajectory summary | `OpenEmotion/openemotion/developmental_self/*` | `runtime_v2` via compact projection | `emotiond/developmental_core/*` |
| identity-preserving adaptation semantics | `OpenEmotion/openemotion/developmental_self/*` | `proto_self_v2` bounded projection | host-side cache / mirror |
| promotion queue / governance ledger | `OpenEmotion/openemotion/developmental_self/*` | `runtime_v2` via governed intake | direct runtime-owned state |
| runtime scheduling / delivery / transport | `EgoCore` | n/a | `WP11` owner path |
| final reply authority | `EgoCore` | n/a | `WP11` owner path |
| tool execution authority | `EgoCore` + Governor | n/a | `WP11` owner path |

## Hard Rules

- `OpenEmotion/openemotion/developmental_self/*` 是 `WP11` formal owner target
- `EgoCore` 只拥有 runtime / governance / delivery / observation 解释权
- `proto_self_v2` 只拥有 bounded consumption / emission 解释权，不拥有 developmental owner state
- `WP7` developmental sandbox 只能作为 reference input，不再拥有 `WP11` 的 formal owner claim
