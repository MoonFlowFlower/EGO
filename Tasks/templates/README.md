# 任务模板库

> 统一任务格式，支持文档接力工作流

## 使用方式

1. **选择模板**：根据任务类型选择对应模板
2. **复制创建**：复制到 `Tasks/active/` 目录，按命名规范重命名
3. **填充信息**：按模板字段填写
4. **闭环推进**：默认按 `Spec -> Author -> Reviewer -> Verifier -> Publisher` 推进
5. **最终归档**：完成后移动到 `Tasks/archive/`

## 模板清单

| 模板 | 适用场景 | 层级 |
|------|----------|------|
| `layer1_quick_fix.md` | 紧急修复、单文件改动 | Layer 1 |
| `layer2_functional.md` | 功能实现、单模块改动 | Layer 2 |
| `layer3_dual_repo.md` | 双仓联动、架构改动 | Layer 3 |
| `layer3_boundary_fix.md` | 边界争议、权限调整 | Layer 3 |
| `type_troubleshoot.md` | 排障任务专用 | Layer 1/2 |
| `type_design.md` | 设计任务专用 | Layer 2/3 |
| `type_verify.md` | 验收任务专用 | Layer 2/3 |

## 命名规范

```
Tasks/active/
├── YYYYMMDD-{layer}-{type}-{brief}.md
│
├── 20260323-L2-func-parser-source-fix.md
├── 20260323-L3-dual-proto-self-v2.md
└── 20260324-L1-fix-typo-readme.md
```

## 状态流转

```
pending → spec_ready → author_done → review_passed → verify_passed → published → archived
                                ↓
                      blocked / handed_off
```

默认规则：

- `review_passed` 前，不报可交付
- `verify_passed` 前，不自动推远端
- 真实主链证据缺失时，只能报条件性完成

## 接力信号

任务需要交接时，在文档末尾添加：

```markdown
## HANDOFF
- from: 当前负责人
- to: 下阶段负责人
- status: READY_FOR_XXX
- blocked_by: []
- notes: 关键上下文
```
