# Task Memory

这里存放 `TaskHandoffRecord` 与 `TaskClosureRecord`。

- `active/`
  当前任务的 handoff 记录。一个任务一份 JSON。
- `archive/`
  已结束任务的 closure 记录。一个任务一份 JSON。

建议字段最少包含：

- `task_id`
- `real_goal`
- `success_criteria`
- `current_layer`
- `main_chain_status`
- `authority_source`
- `confirmed`
- `unknowns`
- `blockers`
- `next_minimal_closure_action`
- `related_refs`

这些文件默认只保留本地，不自动提交到远端。
