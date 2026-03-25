# N4C 固定测试场景包

## 任务信息
- task_id: N4C
- title: 固定测试场景包
- status: verified
- date: 2026-03-25T10:42:00Z

---

## 场景包概述

本场景包包含 5 组固定测试场景，用户可直接按步骤执行，无需阅读源码。

---

## 场景 1：Cycle 聚合验证（正常现象）

### 目的
验证相似意图的事件是否被正确聚合到同一 cycle。

### 输入序列
| 步骤 | Telegram 消息 |
|------|---------------|
| 1 | 读取文件 config.yaml |
| 2 | 查看配置文件 |
| 3 | read the config |
| 4 | check file content |

### 诊断命令
每次发送消息后运行：
```bash
python OpenEmotion/scripts/proto_self_diagnostics.py
```

### 预期现象
```
[Cycles]
- total: 1 (或增加 1)
- cycle_30aa24ef0787e022:
    - psi_bucket: telegram:user_message:file_read
    - hits: 4
    - strength: 0.35
    - promoted: False
```

### 验收标准
| 检查项 | 预期值 |
|--------|--------|
| 所有消息命中同一 cycle_id | ✅ |
| hits = 4 | ✅ |
| strength > 0.3 | ✅ |

### 异常现象
| 现象 | 原因 | 排查 |
|------|------|------|
| cycle_id 不同 | 聚合失败 | 检查 psi_bucket 是否一致 |
| hits 不增加 | strengthen 未触发 | 检查 trace 的 cycle_delta.op |

---

## 场景 2：Reflection 触发验证（正常现象）

### 目的
验证外部失败是否触发 reflection 和 revision_counter 增加。

### 输入序列
| 步骤 | 操作 |
|------|------|
| 1 | 请求执行一个不存在的命令（如 "执行 xyz"） |
| 2 | 等待失败响应 |
| 3 | 再次请求执行失败 |

### 诊断命令
```bash
python OpenEmotion/scripts/proto_self_diagnostics.py
```

### 预期现象
```
[Self Model]
- current_mode: repair (或 exploration)

[Revision Counter]
- count: > 0
```

### 验收标准
| 检查项 | 预期值 |
|--------|--------|
| revision_counter 增加 | ✅ |
| current_mode 可能改变 | ✅ |

### 异常现象
| 现象 | 原因 | 排查 |
|------|------|------|
| revision_counter = 0 | reflection 未触发 | 检查 external_result.success 是否为 false |
| mode 不变 | 阈值未达到 | 多次失败后再观察 |

---

## 场景 3：误聚合风险展示（已知缺陷）

### 目的
验证高风险误聚合风险是否可见。

### 输入序列
| 步骤 | Telegram 消息 |
|------|---------------|
| 1 | 删除临时文件 |
| 2 | 删除生产数据库 |

### 诊断命令
```bash
python OpenEmotion/scripts/proto_self_diagnostics.py
```

### 预期现象（当前已知缺陷）
```
[Cycles]
- cycle_98bd0a1ae1b14728:
    - psi_bucket: telegram:user_message:file_risk_op
    - hits: 2

[Known Risks]
  🔴 [HIGH] 高风险操作聚合
      删除类操作被聚合，可能无法区分临时文件和生产数据库
```

### 验收标准
| 检查项 | 预期值 | 说明 |
|--------|--------|------|
| cycle_id 相同 | ⚠️ 是 | **这是已知缺陷** |
| 风险警告显示 | ✅ 是 | 风险可见 |

### 正常现象（修复后预期）
| 检查项 | 预期值 |
|--------|--------|
| cycle_id 不同 | ✅ |
| safety_context 被区分 | ✅ |

### 排查入口
- N3 主题报告：误聚合风险清单
- cycles.py: `_coarse_intent_classify` 函数
- psi_bucket 不包含 safety_context

---

## 场景 4：Drive Field 响应验证

### 目的
验证 drive_field 是否响应环境信号。

### 输入序列
| 步骤 | Telegram 消息 |
|------|---------------|
| 1 | 删除重要文件（触发高风险） |
| 2 | 查看诊断结果 |

### 诊断命令
```bash
python OpenEmotion/scripts/proto_self_diagnostics.py
```

### 预期现象
```
[Drives]
- caution: > 0.0 (可能增加)
```

### 验收标准
| 检查项 | 预期值 |
|--------|--------|
| caution 可能增加 | ✅ |

### 异常现象
| 现象 | 原因 | 排查 |
|------|------|------|
| caution = 0.0 | 未触发风险评估 | 检查 event 的 safety_context |

---

## 场景 5：综合测试（完整流程）

### 目的
完整测试所有机制。

### 输入序列
| 步骤 | Telegram 消息 |
|------|---------------|
| 1 | 读取文件 test.txt |
| 2 | 查看文件内容 |
| 3 | read the file |
| 4 | 执行不存在的命令（预期失败） |
| 5 | 再次执行失败命令 |
| 6 | 删除临时文件 |
| 7 | 删除生产数据库 |

### 诊断命令
```bash
python OpenEmotion/scripts/proto_self_diagnostics.py
```

### 预期现象汇总
```
[Cycles]
- total: 2 (file_read + file_risk_op)
- cycle_file_read:
    - hits: 3
    - strength: > 0.25

[Self Model]
- current_mode: repair (如果失败足够多)

[Revision Counter]
- count: > 0

[Known Risks]
  🔴 [HIGH] 高风险操作聚合
      删除类操作被聚合，可能无法区分临时文件和生产数据库
```

### 验收标准
| 检查项 | 预期值 |
|--------|--------|
| file_read cycle hits ≥ 3 | ✅ |
| revision_counter > 0 | ✅ |
| 风险警告显示 | ✅ |

---

## 快速诊断对照表

| 现象 | 检查位置 | 预期值 | 异常值 |
|------|----------|--------|--------|
| Cycle 聚合 | [Cycles] hits | 递增 | 不变 |
| Reflection | [Revision Counter] | 增加 | 0 |
| Mode 切换 | [Self Model] mode | repair/exploration | 始终 baseline |
| 误聚合风险 | [Known Risks] | 显示 HIGH | 无警告 |
| Drive 响应 | [Drives] caution | > 0 | 始终 0 |

---

## 注意事项

1. **测试前建议重启 EgoCore**：确保状态干净
2. **Mock 模式可用**：`python OpenEmotion/scripts/proto_self_diagnostics.py --mock`
3. **已知缺陷不掩盖**：场景 3 的误聚合是已知问题，不要忽略
4. **状态持久化**：测试结果会写入 state.json，影响后续测试
