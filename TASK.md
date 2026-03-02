# MVP-7.4: OpenEmotion ↔ OpenClaw Tool 集成与 Deterministic 测试

## GOAL ✅ COMPLETED
建立 tool 层面的 emotiond 集成 + deterministic 测试模式 + 身份分账，确保每次 bot 自报状态都来自真实 API 回包（可审计）。

## Phase - ALL COMPLETE
- [x] 1. 基线真值脚本（bash + curl）✅ 2026-03-02 16:28
- [x] 2. OpenClaw emotiond Tool 插件（3 个工具函数）✅ 2026-03-02 16:42
- [x] 3. 身份分账（Moonlight vs main）✅ 2026-03-02 16:46
- [x] 4. Enforcer 策略硬约束 ✅ 2026-03-02 16:50

## DoD (Definition of Done) - ALL PASSED
- [x] AC1: 脚本基线可复现（test_mode=true 下 selected action 稳定一致）✅
- [x] AC2: 工具可审计（bot 状态播报包含 decision_id/selected/candidates）✅
- [x] AC3: 身份分账有效（Moonlight/main 决策/关系互不污染）✅
- [x] AC4: 策略硬约束（withdraw 时永不输出违反 withdraw 的内容）✅

## Deliverables
| 文件 | 状态 | 路径 |
|------|------|------|
| 测试脚本 | ✅ | tools/test_emotiond_deterministic.sh |
| 身份分离脚本 | ✅ | tools/test_identity_separation.sh |
| OpenClaw 插件 | ✅ | ~/.openclaw/extensions/emotiond/index.ts |
| Hook + Enforcer | ✅ | ~/.openclaw/hooks/emotiond-bridge/handler.js v1.4 |
| Enforcer 配置 | ✅ | ~/.openclaw/hooks/emotiond-enforcer/hook.json |
| 测试文档 | ✅ | integrations/openclaw/TESTING.md |

## Final Verification
```
$ ./tools/test_emotiond_deterministic.sh agent moonlight care
Deterministic: YES
Action: repair_offer (consistent across 2 calls)
```

## Completed
- [2026-03-02 16:28] Phase 1: 测试脚本
- [2026-03-02 16:42] Phase 2: 插件更新 (3 工具)
- [2026-03-02 16:46] Phase 3: 身份分账 + TESTING.md
- [2026-03-02 16:50] Phase 4: Enforcer 策略硬约束
- [2026-03-02 16:52] AC1 验证通过
