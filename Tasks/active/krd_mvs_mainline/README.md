# K / R / D + 新主链 MVS 重构任务

```yaml
task_id: L3-20260331-KRD-MVS
created_at: "2026-03-31T18:02:13Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: spec_ready
```

---

## 真实目标

把 `K / R / D 重构清单模板 + 新主链最小目录结构` 收成一套可直接实施的 MVS 主链重构路线，先锁定权威源、迁移矩阵和首批条目详表，不立刻做全量目录搬迁。

## 成功判据

- [x] 首批 mainline-reachable 模块已纳入 K/R/D 总表
- [x] 首批迁移矩阵已按当前仓库现状映射到真实承接路径
- [x] 首批详表已覆盖 K 池、EgoCore R 池、OpenEmotion R 池、D 池
- [x] 每个条目都写明归属、权威源、主链接入状态、替代物或删除条件
- [ ] 基于本任务进入第一实现轮
- [ ] 新主链达到 E3/E4 后再启动删除绞杀

## 当前层级与主链状态

```yaml
current_layer: strategy
main_chain_status: idea
enabled_status: false
trigger_evidence: planning artifacts only
```

## Authority Source

- `Tasks/K  R  D 重构清单模板 + 新主链最小目录结构.txt`
- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- 当前仓库实际代码布局：
  - `EgoCore/app/interaction`
  - `EgoCore/app/runtime_v2`
  - `EgoCore/app/openemotion_adapter`
  - `EgoCore/app/response`
  - `OpenEmotion/openemotion/contracts`
  - `OpenEmotion/openemotion/proto_self`
  - `OpenEmotion/openemotion/self_model`
  - `OpenEmotion/openemotion/memory`

## 本轮范围

- 落地 Milestone 1 文档：
  - `KRD_MASTER.md`
  - `MIGRATION_MATRIX.md`
  - `ITEMS/` 首批详表
- 不做代码重构
- 不做目录 rename
- 不删除任何旧路径

## 下一步最小闭环动作

按 `MIGRATION_MATRIX.md` 启动第一实现轮，只做一个最小 EgoCore host-chain skeleton slice：

1. 冻结 `InteractionKind`
2. 落一个最小 `response_plan` authority
3. 给 Telegram 主链补最小 route regression

