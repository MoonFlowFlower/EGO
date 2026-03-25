# Tasks 目录

> 项目任务管理中心

## 目录结构

```
Tasks/
├── README.md              # 本文件
├── templates/             # 任务模板库
│   ├── README.md          # 模板说明
│   ├── QUICKSTART.md      # 快速启动指南
│   ├── layer1_quick_fix.md      # Layer 1: 快速修复
│   ├── layer2_functional.md     # Layer 2: 功能实现
│   ├── layer3_dual_repo.md      # Layer 3: 双仓联动
│   ├── layer3_boundary_fix.md   # Layer 3: 边界修复
│   ├── type_troubleshoot.md     # 类型: 排障
│   ├── type_design.md           # 类型: 设计
│   └── type_verify.md           # 类型: 验收
├── active/                # 进行中任务
│   └── EXAMPLE_TASK.md    # 示例任务
└── archive/               # 已完成/归档任务
```

## 快速开始

### 1. 选择模板

```bash
# 5分钟内完成？
cp templates/layer1_quick_fix.md active/20260323-L1-fix-xxx.md

# 功能实现？
cp templates/layer2_functional.md active/20260323-L2-func-xxx.md

# 双仓联动？
cp templates/layer3_dual_repo.md active/20260323-L3-dual-xxx.md
```

### 2. 填充信息

编辑文件，填写：
- `task_id`
- `owner`
- `真实目标`
- `成功判据`
- `当前层级`

### 3. 按阶段执行

参考模板中的 Stage 1/2/3 逐步推进。

### 4. 更新状态

每完成一个阶段，更新任务单状态。

### 5. 完成后归档

```bash
mv active/20260323-xxx.md archive/
```

## 命名规范

```
YYYYMMDD-L{layer}-{type}-{brief}.md

示例：
- 20260323-L1-fix-typo-readme.md
- 20260323-L2-func-parser-source.md
- 20260323-L3-dual-proto-v2.md
- 20260323-TROUBLESHOOT-timeout-issue.md
- 20260323-DESIGN-memory-v2.md
- 20260323-VERIFY-parser-e2e.md
```

## 层级说明

| 层级 | 模板 | 适用场景 | 耗时 | 执行方式 |
|------|------|----------|------|----------|
| Layer 1 | `layer1_quick_fix.md` | 紧急修复、typo | 5-30分钟 | 单会话直接完成 |
| Layer 2 | `layer2_functional.md` | 功能实现、单模块 | 30分钟-4小时 | 文档接力（同一会话） |
| Layer 3 | `layer3_dual_repo.md` | 双仓联动、架构 | 4小时-多天 | Subagent worktree 隔离 |

## 关键原则

1. **Persist first**：先写任务单，再执行
2. **One task one file**：一个任务一个文档
3. **Update as you go**：边做边更新
4. **Handoff clear**：交接必须填写 HANDOFF 区
5. **No false completion**：无真实触发证据，不得报完成

## 工作流支持

### Layer 2 文档接力
```
你（规划者）→ 填充 Stage 1 → 执行 Stage 2 → 执行 Stage 3 → 完成
```

### Layer 3 Subagent 接力
```
你（规划者）→ 派发 Agent（worktree 执行者）→ 派发 Agent（worktree 验收者）→ 完成
```

## 相关文档

- [模板说明](templates/README.md)
- [快速启动指南](templates/QUICKSTART.md)
- [示例任务](active/EXAMPLE_TASK.md)
- [EgoCore 变更路由](../EgoCore/docs/04_CHANGE_ROUTING.md)
- [EgoCore 边界定义](../EgoCore/docs/03_BOUNDARY_AND_OWNERSHIP.md)
