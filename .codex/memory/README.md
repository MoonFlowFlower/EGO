# Codex Assistant Memory

这套目录只服务 `Codex/Claude Code` 一类开发助手的会话衔接，不接入 `EgoCore/OpenEmotion` runtime。

## 分层

- `project_truth.jsonl`
  记录稳定项目真相。只允许保存已核验、且可回溯到仓库文件的事实。
- `user_preferences.jsonl`
  记录已明确确认的长期用户偏好。必须能回溯到真实用户确认。
- `tasks/`
  记录任务 handoff / closure。用于新会话快速恢复“当前任务”。
- `sessions/`
  记录同一任务内的 session capsule。只延长单任务会话寿命，不跨任务续命。

## 记忆晋升规则

- 允许晋升：
  - 稳定项目真相
  - 长期用户偏好
  - 当前任务 handoff / closure
- 禁止晋升：
  - 长聊天原文
  - 未验证结论
  - 临时猜测
  - 调试噪声 / 大段日志
  - 过期讨论

所有长期记录都必须带：

- `scope`
- `source_type`
- `source_ref`
- `last_verified_at`
- `owner`
- `expiry_or_revalidate_rule`

## 会话启动顺序

默认注入优先级：

1. 当前任务 handoff
2. `CODEX_MEMORY.md`
3. 上一任务 closure
4. 同任务 session capsule

## Git 策略

- `project_truth.jsonl`、`user_preferences.jsonl`、`CODEX_MEMORY.md`、说明文档和脚本应纳入版本控制。
- `tasks/active/*.json`、`tasks/archive/*.json`、`sessions/*.json` 默认只保留本地，不自动提交。
