# Layer 1: 快速修复模板

> 适用：紧急修复、单文件改动、文档更新、typo 修复
> 预期耗时：5-30 分钟
> 执行方式：`Spec Lite -> Author -> Reviewer -> Verifier -> Publisher`

---

## 任务头（必须）

```yaml
task_id: L1-{YYYYMMDD}-{序号}
created_at: "2026-03-23T10:00:00Z"
owner: "负责人"
layer: 1
type: quick_fix
status: pending  # pending/spec_ready/author_done/review_passed/verify_passed/published
```

---

## 真实目标

<!-- 一句话说明要解决什么问题 -->
修复 semantic_parser.py 中的 parser_source 污染问题

---

## 成功判据

- [ ] 修改已生效
- [ ] 自测通过
- [ ] 无回归风险

---

## 修改点

| 文件 | 行号 | 修改内容 | 原因 |
|------|------|----------|------|
| | | | |

---

## Spec Lite

| 项目 | 内容 |
|------|------|
| authority source | |
| 当前层级 | |
| 变更分类 | 根因修复 / 临时缓解 / 观察增强 |
| 最小验收路径 | |
| 回退动作 | |

## Author

```
发现位置：
问题原因：
最小修改：
```

## Reviewer（findings-first）

### 阻断发现
- [ ] 无

### 固定检查项
- [ ] authority source 未改错
- [ ] 未引入双重真相源
- [ ] 未把 fallback/shim 偷升成正式主链
- [ ] 未遗漏对应测试/文档/回退口径
- [ ] 未把无关日志、state、运行噪声带进提交

### Review 结论
```
自 review 未发现阻断项 / 发现问题并已修复：
```

## Verifier

```
语法/导入检查：
最小验证动作：
结果：
副作用：
```

## Publisher

- [ ] review_passed
- [ ] verify_passed
- [ ] 提交范围干净
- [ ] 可以自动推远端

---

## 完成声明

```yaml
completed_at: ""
verified_by: ""  # 自测/他测
commit_hash: ""
next_action: none  # 无后续
status: published
```

---

## 快速检查清单

- [ ] 只改了必要的文件
- [ ] 没有引入新依赖
- [ ] 没有修改边界文件
- [ ] 自 review 已完成
- [ ] 自测通过
- [ ] 无需文档更新
