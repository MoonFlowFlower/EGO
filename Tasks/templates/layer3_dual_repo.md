# Layer 3: 双仓联动任务模板

> 适用：跨 EgoCore + OpenEmotion 的架构改动、新 Kernel 版本、边界调整
> 预期耗时：4 小时 - 多天
> 执行方式：`Full Spec -> (OpenEmotion Author/Self-Reviewer/Independent Reviewer) -> (EgoCore Author/Self-Reviewer/Independent Reviewer) -> Verifier -> Publisher`

---

## 任务头（必须）

```yaml
task_id: L3-{YYYYMMDD}-{序号}
created_at: "2026-03-23T10:00:00Z"
owner: "规划者"
layer: 3
type: dual_repo  # dual_repo/boundary_fix/architecture
repos: [EgoCore, OpenEmotion]
status: pending  # pending/spec_ready/author_done/review_passed/verify_passed/published
```

---

## 真实目标

<!-- 一句话说清系统级目标 -->
实现 Proto-Self Kernel v2，支持多轮反思和 identity 更新

---

## 成功判据（系统级）

- [ ] identity_invariants 可更新
- [ ] reflection 触发机制接入主链
- [ ] EgoCore adapter 兼容 v1/v2
- [ ] E2E Telegram 验证通过
- [ ] 双仓契约文档同步更新

---

## 当前层级与主链状态

```yaml
current_layer: strategy  # 目标/策略/表示/实现/验证/收口
main_chain_status: idea  # 想法/构件/接入/启用/生效/观察
enabled_status: false
trigger_evidence: none
```

---

## 双仓分工

| 组件 | 所属仓 | 核心修改 | 接口变动 |
|------|--------|----------|----------|
| Proto-Self Kernel v2 | OpenEmotion | `openemotion/proto_self_v2/` | schema v2 |
| Adapter | EgoCore | `egocore/adapters/proto_self_adapter.py` | 支持 v1/v2 |
| Contract | Dual | `contracts/proto_self_v2.schema.json` | 新增 |

---

## 边界检查

### 六问门禁（双仓必须回答）

| 问题 | EgoCore | OpenEmotion | 结论 |
|------|---------|-------------|------|
| 这个能力归谁？ | | | |
| 权威源是谁？ | | | |
| 和哪个模块耦合？ | | | |
| 是否引入双重真相源？ | | | |
| 是否让 shim 变成长期黑箱？ | | | |
| 失败由谁兜底？ | | | |

### 结构化接口检查
- [ ] schema 已定义
- [ ] adapter 已实现
- [ ] contract test 已通过
- [ ] 双仓文档已同步

---

## 阶段规划（多轮接力）

### Stage 1: 规划（规划者）

#### 输入文档
- [ ] 已读 `EgoCore/docs/00_MASTER_INDEX.md`
- [ ] 已读 `OpenEmotion/docs/00_MASTER_INDEX.md`
- [ ] 已读 `POLICIES/EgoCore_OpenEmotion_Boundary_Constitution_v1.md`

#### 输出文档
- `Tasks/L3-XXX-design.md` — 设计稿
- `Tasks/L3-XXX-contract.md` — 接口草案
- `Tasks/L3-XXX-handoff.md` — 交接文档

#### 方案分级
| 等级 | 方案 | 风险 | 回退策略 |
|------|------|------|----------|
| 正式 | | | |
| 过渡 | | | |
| 临时 | | | |

---

### Stage 2: OpenEmotion Author（执行者 A，worktree）

```yaml
agent:
  description: "PSK v2 OpenEmotion 实现"
  prompt: "读取设计稿，实现 openemotion/proto_self_v2/..."
  isolation: "worktree"
  target_repo: OpenEmotion
```

#### 交付物
- [ ] 代码实现
- [ ] 单元测试
- [ ] 接口文档
- [ ] 自测报告

#### OpenEmotion Self-Reviewer
- [ ] authority source 与 schema 未漂移
- [ ] 未让 OpenEmotion 偷做 EgoCore runtime 治理
- [ ] contract / schema / docs 已同步
- [ ] 自 review 未发现阻断项

#### OpenEmotion Independent Reviewer
- [ ] 已由独立 Reviewer subagent 审核
- [ ] findings-first 结果已记录

#### 交接
```yaml
HANDOFF:
  from: 执行者 A
  to: 执行者 B
  status: READY_FOR_EGOCORE_ADAPTER
  deliverables: ["代码", "schema", "测试"]
```

---

### Stage 3: EgoCore Author（执行者 B，worktree）

```yaml
agent:
  description: "PSK v2 EgoCore Adapter"
  prompt: "读取 OpenEmotion 实现，更新 EgoCore adapter..."
  isolation: "worktree"
  target_repo: EgoCore
```

#### 交付物
- [ ] Adapter 实现
- [ ] Contract guard 更新
- [ ] 双仓联动测试

#### EgoCore Self-Reviewer
- [ ] 未在 adapter/prompt 发明 OpenEmotion 语义字段
- [ ] 未把 shim/fallback 偷升成正式主链
- [ ] 双仓接口契约仍唯一
- [ ] 自 review 未发现阻断项

#### EgoCore Independent Reviewer
- [ ] 已由独立 Reviewer subagent 审核
- [ ] findings-first 结果已记录

---

### Stage 4: Verifier（验收者，worktree）

```yaml
agent:
  description: "PSK v2 E2E 验收"
  prompt: "运行 Telegram E2E，验证主链接入..."
  isolation: "worktree"
```

#### 验收标准
- [ ] Gate A: Contract 正确
- [ ] Gate B: E2E 主链可触发
- [ ] Gate C: Preflight / replay 通过
- [ ] 真实触发证据已收集
- [ ] contract/schema gate 已通过
- [ ] cross-repo compatibility gate 已通过
- [ ] adapter/runtime 回归已通过

---

### Stage 5: Publisher

- [ ] `review_passed`
- [ ] `verify_passed`
- [ ] 提交范围干净
- [ ] 按 `code/mainline -> docs -> evidence` 拆分

---

## 状态追踪

```yaml
stage_status:
  planning: completed
  openemotion_impl: in_progress
  egocore_adapter: pending
  e2e_verify: pending
  handoff_ready: false
  publish_ready: false

evidence:
  planning_doc: "Tasks/L3-XXX-design.md"
  contract_doc: "Tasks/L3-XXX-contract.md"
  openemotion_commit: ""
  egocore_commit: ""
  e2e_report: ""
```

---

## 完成声明

```yaml
completed_at: ""
verified_by: "e2e"
main_chain_status: enabled
enabled_status: true
trigger_evidence: "Telegram E2E 验证报告"
commit_hash_ego: ""
commit_hash_emotion: ""
solution_grade: formal
next_action: observe
observation_period: 7d
status: published
```

---

## 回退计划

| 场景 | 回退动作 | 负责人 |
|------|----------|--------|
| OpenEmotion 实现失败 | 回退到 v1，标记 v2 为 experimental | |
| Adapter 不兼容 | 添加 shim 层，延长过渡期 | |
| E2E 失败 | 修复问题，重新验证 | |
| 主链不稳定 | 关闭 v2 入口，保留代码 | |
