# Proto-Self Kernel v1 用户测试手册

> 本手册帮助用户第二天不用读大量代码，就能直接测试 Proto-Self Kernel v1 效果。

---

## 一、快速开始（5 分钟）

### 1.1 前置条件

```bash
# 1. 确认 EgoCore 运行
cd D:\Project\AIProject\MyProject\Ego\EgoCore
python -m app.main --telegram

# 2. 确认 Telegram Bot 可用
# 向 Bot 发送任意消息，确认有响应
```

### 1.2 一键诊断

```bash
cd D:\Project\AIProject\MyProject\Ego
python OpenEmotion/scripts/proto_self_diagnostics.py
```

### 1.3 预期输出

```
[Cycles]
- total: X

[Revision Counter]
- count: X

[Known Risks]
  🔴/🟡/🟢 风险警告（如有）
```

---

## 二、核心测试场景

### 场景 A：Cycle 聚合（推荐首选）

**操作**：发送 3 条相似消息
```
1. 读取文件 config.yaml
2. 查看配置文件
3. read the config
```

**验证**：运行诊断，确认 `[Cycles]` 中 `hits = 3`

---

### 场景 B：Reflection 触发

**操作**：触发失败
```
1. 执行不存在的命令
2. 再次执行失败命令
```

**验证**：运行诊断，确认 `[Revision Counter] > 0`

---

### 场景 C：误聚合风险（已知缺陷）

**操作**：发送两条不同风险的消息
```
1. 删除临时文件
2. 删除生产数据库
```

**验证**：运行诊断，确认 `[Known Risks]` 显示 HIGH 警告

---

## 三、对照表

### 3.1 正常现象对照表

| 测试场景 | 检查位置 | 正常值 | 说明 |
|----------|----------|--------|------|
| 相似消息 | [Cycles] hits | 递增 | 3 条消息后 hits = 3 |
| 相似消息 | [Cycles] cycle_id | 相同 | 所有消息命中同一 cycle |
| 失败操作 | [Revision Counter] | 增加 | 每次失败 +1 |
| 失败操作 | [Self Model] mode | 可能变为 repair | 失败后切换 |

### 3.2 异常现象对照表

| 现象 | 检查位置 | 异常值 | 原因 | 排查 |
|------|----------|--------|------|------|
| 聚合失败 | [Cycles] cycle_id | 不同 | intent 分类不一致 | 检查 psi_bucket |
| strengthen 失败 | [Cycles] hits | 不变 | cycle_delta.op != strengthen | 检查 trace |
| Reflection 未触发 | [Revision Counter] | 0 | external_result 不是失败 | 检查事件结果 |
| Drive 不响应 | [Drives] caution | 始终 0 | safety_context 未传入 | 检查事件上下文 |

### 3.3 已知缺陷对照表

| 缺陷 | 触发条件 | 现象 | 风险等级 |
|------|----------|------|----------|
| 高风险误聚合 | "删除临时文件" + "删除生产数据库" | 同一 cycle_id | HIGH |
| 作用域误聚合 | "修改用户配置" + "修改系统配置" | 同一 cycle_id | MEDIUM |
| 环境误聚合 | "测试登录" (dev) + "测试生产" (prod) | 同一 cycle_id | MEDIUM |

---

## 四、诊断命令速查

```bash
# 标准诊断
python OpenEmotion/scripts/proto_self_diagnostics.py

# 演示模式（无需 EgoCore）
python OpenEmotion/scripts/proto_self_diagnostics.py --mock

# 指定状态文件
python OpenEmotion/scripts/proto_self_diagnostics.py --state-file path/to/state.json
```

---

## 五、故障排查

### 5.1 诊断脚本报错

| 错误 | 原因 | 解决 |
|------|------|------|
| 状态文件不存在 | EgoCore 未运行 | 启动 EgoCore |
| JSON 解析失败 | state.json 损坏 | 删除 state.json 重启 |
| 模块导入失败 | 路径问题 | 确认在 Ego 目录运行 |

### 5.2 测试不生效

| 现象 | 检查 | 解决 |
|------|------|------|
| hits 不增加 | trace 是否写入 | 检查 EgoCore 日志 |
| revision_counter 不变 | 失败是否被识别 | 确认 external_result.success = false |
| 风险警告不显示 | cycle 是否创建 | 检查 [Cycles] total |

---

## 六、N3 已知风险清单

| 风险 | 等级 | 说明 | 影响 |
|------|------|------|------|
| 高风险操作误聚合 | HIGH | 删除临时文件与删除生产数据库同一 cycle | 可能导致错误行为预测 |
| 作用域误聚合 | MEDIUM | 不同作用域操作同一 cycle | 预测精度下降 |
| 环境误聚合 | MEDIUM | 开发与生产测试同一 cycle | 环境敏感决策失误 |
| 语言歧义 | LOW | 相同关键词不同语义同一 cycle | 强度计算偏差 |

**根因**：`psi_bucket` 不包含 `safety_context`、`target`、`environment` 等上下文。

---

## 七、相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 用户测试合同 | `artifacts/n4_user_test/N4A_USER_TEST_CONTRACT.md` | 测试定义 |
| 测试场景包 | `artifacts/n4_user_test/N4C_SCENARIO_PACK.md` | 详细场景 |
| N3 主题报告 | `reports/N3_THEME_REPORT.md` | 误聚合分析 |
| 诊断脚本 | `OpenEmotion/scripts/proto_self_diagnostics.py` | 工具 |

---

*最后更新: 2026-03-25*
