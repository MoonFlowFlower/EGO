# Task State And Handoff

适用范围：需要写任务状态、恢复上下文、做 handoff brief、或判断下一步最小闭环动作的任务。

## 最小状态字段

正式任务文档或状态报告至少应覆盖：

- `task type`
- `real goal`
- `success criteria`
- `authority source`
- `current layer`
- `main-chain status`
- `change classification`
- `verification level`
- `current blocker`
- `key unknown`
- `next minimal closure action`
- `refs to raw evidence`

## 默认状态流转

```text
pending -> spec_ready -> author_done -> review_passed -> verify_passed -> published -> archived
```

可选中断状态：

```text
blocked
handed_off
```

## 恢复上下文时要回答

- 当前目标是什么
- 已证实什么
- 未证实什么
- 当前卡在哪一层
- 当前主链阶段是什么
- 下一步最小闭环动作是什么

默认先恢复上下文，不直接扩大实现范围。

## Handoff brief 最小字段

对子代理或外部执行器派发时，至少写清：

- `task type`
- `real goal`
- `success criteria`
- `current symptom` 或当前状态
- `current layer`
- `authority source`
- `proof required to call it effective`
- `change classification`
- `minimal decision point`
- `next action`
- `rollback / exit plan`

## Review against acceptance

对照验收或 code review 收口时，至少判断：

- 是否命中当前 milestone / acceptance
- 是否留了任务匹配的验证
- 是否有主链证据缺口
- 是否还混入 scope 外改动
- 当前应报：
  - `可宣称完成`
  - `条件性完成`
  - `不可宣称完成`
