# MVS 工作包 Shim Register

> 作用：登记与 `WP0 / WP1` 直接相关的 shim、compat path 与 mirror 风险。
> 注意：这不是对 [EgoCore/SHIM_REGISTER.md](/mnt/d/Project/AIProject/MyProject/Ego/EgoCore/SHIM_REGISTER.md) 的替代；后者仍是现有全局 register。本文件只补 MVS 主线相关 inventory。

## 登记规则

1. 任何仍可能影响 `WP0 / WP1` 判断的 compat path / mirror / host-side semantic residue，都必须登记。
2. 登记不等于保留；登记只是为了避免删除时失去因果解释。
3. 没拿到新主链 E3/E4 前，不删除仍可能承载真实入口的对象。

## 当前 MVS 相关条目

| ID | 路径 | 类型 | 当前角色 | 正式归属 | 处理策略 |
|----|------|------|----------|----------|----------|
| MVS-SHIM-01 | `OpenEmotion/openemotion/proto_self/` | compatibility path | 历史 Proto-Self 主体路径 | `OpenEmotion/openemotion/proto_self_v2/` | 不再承接新功能；保留到 `proto_self_v2` 边界与证据门槛满足后再进入删除 |
| MVS-SHIM-02 | `OpenEmotion/openemotion/contracts/event_v1.py` | mirror-at-risk | 当前 `event_v1` 文件位于 OE，但按主线决策应视作 EgoCore 输入 authority 的 mirror 落点 | EgoCore ingress authority | 在 `WP0` 冻结 authority；后续只允许一个正式解释口径 |
| MVS-SHIM-03 | `EgoCore/app/openemotion_adapter/developmental_writeback.py` | host-side semantic residue | 宿主内主体语义残留 | OpenEmotion | 放入 D 池；在 OE 主线证据足够前不删，但禁止扩功能 |
| MVS-SHIM-04 | `EgoCore/app/runtime/interaction_loop.py` | legacy runtime path | 旧宿主交互路径 | `EgoCore/app/runtime_v2/` | 仅作 legacy inventory；待新宿主链 E4 后绞杀 |
| MVS-SHIM-05 | `EgoCore/app/handlers/social_chat_handler.py` | legacy chat path | 旧聊天主链 | `EgoCore/app/runtime_v2/chat_reply_engine.py` | 只作 compat/deletion inventory，不再回接 |

## 当前结论

- `proto_self_v2 + seed_v0_2` 是正式现实主线。
- 旧 `proto_self/` 和 legacy chat/runtime 仍要登记，但不再是未来实现落点。
- `event_v1` 的 authority 归属仍需在 `WP0` 冻结后彻底消除歧义。
