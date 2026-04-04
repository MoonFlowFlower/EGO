# WP12 / MVP17 Social Capability Ownership

## Purpose

冻结 `WP12/MVP17` 的 capability ownership，防止 social self / trust / commitment / repair / relation memory 能力在 `OpenEmotion`、`EgoCore`、historical materials 之间再次形成双真相源或职责偷换。

## Ownership Table

| Capability | Formal Owner | Allowed Readers | Forbidden Owner Path |
|------------|--------------|-----------------|----------------------|
| other-model state | `OpenEmotion/openemotion/social_self/*` | `proto_self_v2` bounded projection | historical roadmap/spec materials |
| relation memory | `OpenEmotion/openemotion/social_self/*` | `runtime_v2` via compact projection | host-side cache / mirror |
| trust state | `OpenEmotion/openemotion/social_self/*` | `proto_self_v2` bounded projection | runtime-owned heuristics |
| commitment state | `OpenEmotion/openemotion/social_self/*` | `runtime_v2` via compact projection | delivery-layer state |
| repair state / repair proposal semantics | `OpenEmotion/openemotion/social_self/*` | `proto_self_v2` bounded projection | free-text prompt contract |
| social boundary state | `OpenEmotion/openemotion/social_self/*` | `runtime_v2` via governed intake | direct host shortcut |
| runtime scheduling / delivery / transport | `EgoCore` | n/a | `WP12` owner path |
| final reply authority | `EgoCore` | n/a | `WP12` owner path |
| tool execution authority | `EgoCore` + Governor | n/a | `WP12` owner path |

## Hard Rules

- `OpenEmotion/openemotion/social_self/*` 是 `WP12` formal owner target
- `EgoCore` 只拥有 runtime / governance / delivery / observation 解释权
- `proto_self_v2` 只拥有 bounded consumption / emission 解释权，不拥有 social owner state
- historical roadmap / archive social specs 只能作为 reference input，不再拥有 `WP12` 的 formal owner claim
