# 类型模板：验收任务

> 适用：功能验收、E2E 验证、代码审查、质量把关
> 核心原则：未接主链、未启用、无真实触发证据，不得报完成
> 角色定位：只做 Verify，不混写实现

---

## 任务头

```yaml
task_id: VERIFY-{YYYYMMDD}-{序号}
created_at: "2026-03-23T10:00:00Z"
owner: ""
type: verify
verify_scope: feature  # feature/e2e/code_review/release
status: pending
```

---

## 验收对象

| 项目 | 内容 |
|------|------|
| 任务单 | |
| 实现者 | |
| 交付时间 | |
| 代码变更 | |

---

## 验收标准

### Gate A: Contract 正确
- [ ] 接口符合契约
- [ ] Schema 验证通过
- [ ] 边界符合宪法

### Gate B: E2E 主链可触发
- [ ] 主链入口已接入
- [ ] 调用路径正确
- [ ] 日志可观测

### Gate C: Preflight / replay 通过
- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 回归测试通过

---

## 验收记录

### Findings（必须优先写）
| 发现 | 严重程度 | 状态 | 跟进 |
|------|----------|------|------|
| | blocker/warn/info | open/fixed | |

### 代码审查
| 检查项 | 结果 | 备注 |
|--------|------|------|
| 边界正确性 | | |
| 权威源归属 | | |
| 错误处理 | | |
| 日志/观测 | | |
| 测试覆盖 | | |

### E2E 验证
| 场景 | 输入 | 预期 | 实际 | 结果 |
|------|------|------|------|------|
| | | | | |

### 验证门匹配
- [ ] 最低门：`py_compile` / 导入检查 / 脚本语法
- [ ] 最低门：改动相关最小测试集
- [ ] 若为 Telegram 主链：层级测试 + `run_telegram_mainline_regression.sh`
- [ ] 若为双仓 / schema / adapter：contract gate + compatibility gate
- [ ] 若为真实故障修复：replay 复现链已记录

### 真实触发证据
```
日志片段：
截图/输出：
```

---

## 验收结论

```yaml
result: pass  # pass/conditional_pass/fail
blockers: []
observations: |
  1.
  2.
next_action: enable  # enable/observation/fix
```

---

## 放行声明

- [ ] 已验证接入主流程
- [ ] 已验证正确启用
- [ ] 已验证真实触发
- [ ] 已验证可观测
- [ ] 已明确写出“还没证明什么”

**结论**：只有在无 blocker 且 `result=pass` 时，才可放行到 Publisher。
