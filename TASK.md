# MVP-7.5: 不可绕过 + 可回归

## GOAL
把 MVP-7.4 的策略硬约束升级为：任何情况下都不可绕过，并提供 manifest 回放 + CI 回归。

## Phase
- [ ] 1. 绕过面测试（enforcer 覆盖所有出站通路）
- [ ] 2. 回放能力（manifest 可回放，哈希一致）
- [ ] 3. 审计结构（correlation_id / policy_version 链路）
- [ ] 4. CI 集成（每次 PR 自动验证）

## DoD (Definition of Done)
- [ ] AC1: Enforcer 覆盖所有出站通路（tool 未调用、异常、并发）
- [ ] AC2: manifest 可回放，输出哈希一致（deterministic + identity separation）
- [ ] AC3: 审计日志可机器解析（correlation_id / policy_version / decision_id 链路完整）
- [ ] AC4: CI 每次 PR 必跑并通过（最小关键用例集）

## Priority Hard Holes
1. **绕过面测试** - 确保 enforcer 是"最后一道门"
   - Agent 不调用 tool，直接输出攻击内容 → enforcer 是否拦住
   - 并发消息 → enforcer 是否每条都拉最新 decision
   - tool 异常/超时 → fail-closed 策略
   - 多身份/多 channel → counterparty_id 解析一致性

2. **回放能力** - manifest 可回放
   - 输出 manifest：事件序列、seed、decision_id 序列、状态摘要
   - tools/replay_manifest.sh 复跑并对比哈希
   - identity separation 纳入 manifest

3. **审计结构** - 机器可解析
   - correlation_id（贯穿 hook → tool → emotiond → enforcer）
   - policy_version + schema_version

4. **CI 集成** - 自动验证
   - test_emotiond_deterministic.sh（care/betrayal/apology）
   - test_identity_separation.sh
   - enforcer 绕过面测试

## Current Phase
**Phase 1: 绕过面测试**

## Next Action
创建 test_enforcer_bypass.sh 验证所有绕过路径

## Blockers
(none)

## Evidence
- 脚本路径: tools/test_enforcer_bypass.sh
- 回放脚本: tools/replay_manifest.sh
- CI 配置: .github/workflows/emotiond-test.yml
