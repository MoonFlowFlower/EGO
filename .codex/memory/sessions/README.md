# Session Capsules

本目录用于保存同一任务内的 `SessionCapsule`。

用途：

- 只在同一任务继续推进时减少重开会话带来的上下文损失
- 不跨任务续命
- 不替代 `TaskHandoffRecord`

推荐文件名：

- `{task_id}-{capsule_id}.json`

生成骨架：

```bash
python3 scripts/codex_memory.py create-session-capsule --task-id <TASK_ID> --capsule-id <CAPSULE_ID>
```
