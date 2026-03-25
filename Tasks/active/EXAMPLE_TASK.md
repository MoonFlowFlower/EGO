# 示例任务：heuristic 回退收窄 + parser_source 保真修复

> 这是一个示例任务，展示如何使用 Layer 2 模板

---

## 任务头（必须）

```yaml
task_id: L2-20260323-EXAMPLE
owner: "claude"
layer: 2
type: functional
target_repo: EgoCore
status: completed
```

---

## 真实目标

修复语义解析主链中的两个关键问题：
1. heuristic 职责膨胀（开始用执行动词做语义判断）
2. parser_source 失真（实际走 heuristic 但显示 semantic_parser）

---

## 成功判据

- [x] heuristic 不再使用执行动词列表做主语义判定
- [x] parser_source 在三条路径上严格保真
- [x] timeout/invalid JSON/empty 都不会污染 source
- [x] E2E 中能真实分辨当前命中链
- [x] 日志、graph、runtime 观测一致

---

## 当前层级与主链状态

```yaml
current_layer: verification  # 已推进到验证层
main_chain_status: enabled   # 已启用
enabled_status: true
trigger_evidence: E2E 脚本 8/8 通过
```

---

## 路由信息

| 项目 | 内容 |
|------|------|
| 能力归属 | EgoCore |
| 第一落点 | `app/runtime_v2/semantic_parser.py` |
| 权威源 | `semantic_parse_message()` |
| 耦合模块 | `telegram_bridge.py`, `safe_semantic_parse()` |
| 失败兜底 | `heuristic_parse()` |

---

## 阶段执行记录

### Stage 1: 规划

#### 入口检查
- [x] 已读 `00_MASTER_INDEX.md`
- [x] 已读 `04_CHANGE_ROUTING.md`
- [x] 六问门禁已回答

#### 六问门禁
| 问题 | 答案 |
|------|------|
| 能力归属 | EgoCore（语义解析是运行时能力） |
| 权威源 | `semantic_parse_message()` |
| 耦合模块 | telegram_bridge, safe_semantic_parse |
| 双重真相源 | 否，统一入口 |
| shim 黑箱 | 否，heuristic 是明确兜底 |
| 失败兜底 | heuristic_parse → chat_default |

### Stage 2: 实现

#### 修改文件
| 文件路径 | 修改类型 | 影响范围 |
|----------|----------|----------|
| `app/runtime_v2/semantic_parser.py` | 修改 | heuristic_parse 逻辑 |

#### 关键改动
1. **heuristic_parse()**: 移除执行动词列表，只保留显式硬信号
2. **_parse_llm_result()**: 清空 parser_source，强制调用方设置
3. **safe_semantic_parse()**: 不覆写 parser_source

### Stage 3: 验证

#### 测试覆盖
| 测试类型 | 测试文件 | 结果 |
|----------|----------|------|
| 单元测试 | `scripts/e2e_verify_parser_source.py` | 8/8 通过 |
| E2E 验证 | 手动验证 | 通过 |

#### 真实触发证据
```
E2E-1: 长混合输入 + timeout → heuristic_parser ✓
E2E-2: 状态查询 + timeout → chat_default ✓
E2E-3: 所有 fallback 路径保真 ✓
E2E-4: heuristic 不膨胀 ✓
```

---

## 完成声明

```yaml
completed_at: "2026-03-23T17:30:00Z"
verified_by: "self"
main_chain_status: enabled
enabled_status: true
trigger_evidence: "E2E 脚本 8/8 通过"
commit_hash: "b101f42"
solution_grade: formal
next_action: observe
```

---

## 口径

> 已收窄 heuristic 回退职责，并修复 parser_source 观测保真；语义主链观测可信度提升，后续再继续验证 semantic_parser 真实命中率。

---

## 归档

- [x] 代码已提交
- [x] 文档已更新
- [x] 任务单完成
- [x] 移动到 archive
