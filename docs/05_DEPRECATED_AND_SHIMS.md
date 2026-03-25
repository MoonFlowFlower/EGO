# 05_DEPRECATED_AND_SHIMS.md

> 说明：本表只登记当前已经有足够仓库证据、或明确属于过渡/兼容/历史残留的路径。未确认项坚持标 `deprecated-candidate`。

| 路径/模块 | 当前状态 | 类型 | 原用途 | 现替代 | 是否仍被引用 | 是否可删 | 删除前提 | 风险 |
|---|---|---|---|---|---|---|---|---|
| `EgoCore/app/runtime_v2/*` | 当前 Telegram 主链运行时 | active | Runtime v2 Telegram/CLI 主链 | 无 | 是 | 否 | 无 | 主链误删 |
| `EgoCore/app/telegram_bot.py` 中 `use_runtime_v2` 路径 | 当前正式主线 | active | Telegram 正式主线 | 无 | 是 | 否 | 无 | 主线误改 |
| `EgoCore/app/telegram_bot.py` 中 `_handle_with_new_runtime` | compatibility-only | transitional | 旧 runtime/new runtime 兼容路径 | Runtime v2 Telegram path | 是 | 暂否 | 旧测试/兼容逻辑消失后再评估 | 误回漂成双主 |
| `EgoCore/app/telegram_bot.py` 中 `_handle_with_legacy_router` | compatibility-only | deprecated-candidate | 更早 Telegram 路由路径 | Runtime v2 Telegram path | 是 | 暂否 | 无主链引用 + 兼容测试移除 | 删除后旧路径失效 |
| `EgoCore/app/runtime/agent_runner.py` | 旧 runtime 核心 | transitional | 旧 runtime core / compatibility support | `app/runtime_v2/*` (Telegram 主线) | 是 | 暂否 | 旧 runtime 路径与测试进一步迁走 | 历史功能断裂 |
| `EgoCore/app/runtime/request_classifier.py` | 旧 request classifier | transitional | 旧 request 分类/host override | Runtime v2 + bridge | 是 | 暂否 | 旧 runtime 链不再依赖 | host override 回归 |
| `EgoCore/app/runtime/request_registry.py` | 旧 request lifecycle registry | transitional | 旧 request 注册/链维护 | Runtime v2 session state | 是 | 暂否 | 旧 runtime 测试迁移完成 | 链路回归 |
| `EgoCore/prompts/AGENT.md` | 当前 Runtime v2 文件式 prompt | active | agent prompt file | 无 | 是 | 否 | 无 | prompt 误改 |
| `EgoCore/prompts/SOUL.md` | 当前 Runtime v2 文件式 prompt | active | soul prompt file | 无 | 是 | 否 | 无 | prompt 误改 |
| `EgoCore/prompts/TOOLS.md` | 当前 Runtime v2 文件式 prompt | active | tool policy prompt file | 无 | 是 | 否 | 无 | prompt 误改 |
| `EgoCore/app/runtime_v2/prompt_files.py` | 文件式 prompt loader | active | Runtime v2 prompt file loader | 无 | 是 | 否 | 无 | prompt surface 失效 |
| `OpenEmotion/openemotion/*` | 主体本体模块 | active | 正式 identity/self-model/memory 本体 | 无 | 是 | 否 | 无 | 主体本体误删 |
| `OpenEmotion/emotiond/*` | 服务/宿主侧主体处理面 | active | emotiond 处理、服务、接口 | 无 | 是 | 否 | 无 | 服务面失效 |
| `OpenEmotion/legacy/openclaw/*` | 历史 OpenClaw 依赖残留 | deprecated-candidate | 历史 skill/legacy 宿主链 | EgoCore + OpenEmotion 正式双核 | 看起来较弱，但需进一步补证 | 暂否 | 无引用确认 + 替代确认 | 误删后历史链测试断裂 |
| `OpenEmotion/openclaw_skill/*` | 兼容 OpenClaw skill 面 | shim | 兼容 OpenClaw/skill 形态 | 正式双核主链 | 可能仍被局部使用 | 暂否 | 确认无人使用后再删 | 兼容链断裂 |
| `OpenEmotion/emotiond/self_model_mirror.py` | mirror 语义明确 | mirror | 宿主/状态镜像 | self-model 正式本体 | 是 | 否 | 若替代方案出现再评估 | 被误当正式真相 |
| `OpenEmotion/emotiond/memory_legacy.py` | 历史 memory 兼容层 | transitional | 旧 memory 路径兼容 | 新 memory / openemotion.memory | 是 | 暂否 | 引用清零并验证替代稳定 | 记忆链回归 |

## 规则提醒

- `shim` / `mirror` / `cache` 允许存在，但必须承认它们**不拥有最终解释权**
- `deprecated-candidate` 不等于可删
- 只有在“无主链引用 + 有明确替代 + 删除风险可评估”时，才能进 `deprecated`

## 与 generated 的关系

进一步补证时优先看：
- `docs/generated/import_or_reference_map.csv`
- `docs/generated/orphan_candidates.md`
- `docs/generated/recent_hotspots.md`
