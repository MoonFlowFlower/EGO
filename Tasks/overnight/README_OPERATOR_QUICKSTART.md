# 操作员快速开始

## 现在从哪里开始

本包默认承认：
- N1 已完成
- 现在应从 N2 / N3 / N4 的主题批次开始

## 推荐夜间节奏

- Night A：N2
- Night B：N3
- Night C：N4

## 最稳跑法

### 跑法 1：每晚一个主题，一个新会话（推荐）

1. 解压本包
2. 选择今晚主题，比如 N2
3. 把 `prompts/START_THEME_NEW_SESSION.txt` 贴给 Claude，并替换：
   - `<THEME_ID>`
   - `<REPO_PATH>`
   - `<BATCH_PATH>`
   - `<THEME_FILE>`
4. 第二天只看：
   - `runtime/RUN_STATE.json`
   - `reports/<SUBTASK_ID>_REPORT.md`
   - `reports/<THEME_ID>_THEME_REPORT.md`
   - 关键 artifact / trace / 脚本输出

### 跑法 2：同主题内继续子任务（备选）

只有在上一子任务已完成交接后才允许。

1. 确认上一子任务已更新：
   - `runtime/RUN_STATE.json`
   - `reports/<SUBTASK_ID>_REPORT.md`
   - `runtime/SESSION_HANDOFF.md`
2. 若是新开会话，使用 `prompts/CONTINUE_THEME_FROM_HANDOFF.txt`
3. 若不得不仍在同会话，使用 `prompts/SAME_SESSION_CONTINUE_THEME_FALLBACK.txt`
4. 继续前必须重新读取关键文件

## 每晚结束后怎么验收

只看四件事：

1. `runtime/RUN_STATE.json`
2. `reports/<SUBTASK_ID>_REPORT.md`
3. `reports/<THEME_ID>_THEME_REPORT.md`
4. 关键 artifact / trace / 脚本输出

如果没有真实证据，不接受 verified。
