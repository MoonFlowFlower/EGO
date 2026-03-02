# MVP-7.4: OpenEmotion ↔ OpenClaw Tool 集成与 Deterministic 测试

## GOAL
建立 tool 层面的 emotiond 集成 + deterministic 测试模式 + 身份分账，确保每次 bot 自报状态都来自真实 API 回包（可审计）。

## Phase
- [x] 1. 基线真值脚本（bash + curl）✅ 2026-03-02 16:28
- [x] 2. OpenClaw emotiond Tool 插件（3 个工具函数）✅ 2026-03-02 16:42
- [x] 3. 身份分账（Moonlight vs main）✅ 2026-03-02 16:46
- [ ] 4. Enforcer 策略硬约束（可选）

## DoD (Definition of Done)
- [x] AC1: 脚本基线可复现（test_mode=true 下 selected action 稳定一致）
- [x] AC2: 工具可审计（bot 状态播报包含 decision_id/selected/candidates）
- [x] AC3: 身份分账有效（Moonlight/main 决策/关系互不污染）
- [ ] AC4: 策略硬约束（withdraw 时永不输出违反 withdraw 的内容）

## Current Phase
**Phase 4: Enforcer 策略硬约束**

## Next Action
创建 emotiond-enforcer hook/middleware，确保 withdraw/boundary 决策不被违背

## Blockers
(none)

## Evidence
- 脚本路径: tools/test_emotiond_deterministic.sh ✅
- 插件路径: ~/.openclaw/extensions/emotiond/index.ts ✅
- 文档路径: integrations/openclaw/TESTING.md ✅
- 身份测试: tools/test_identity_separation.sh ✅

## Completed
- [2026-03-02 16:28] Phase 1: 创建 tools/test_emotiond_deterministic.sh
- [2026-03-02 16:42] Phase 2: 更新插件，增加 3 个工具函数
- [2026-03-02 16:46] Phase 3: 创建 TESTING.md + test_identity_separation.sh，已验证身份分离

## Checkpoints
- [2026-03-02 14:30] 任务启动
- [2026-03-02 16:28] Phase 1 完成
- [2026-03-02 16:42] Phase 2 完成
- [2026-03-02 16:46] Phase 3 完成，commit efef3d9
