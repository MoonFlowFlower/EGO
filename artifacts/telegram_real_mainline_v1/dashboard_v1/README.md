# Growth Dashboard v1

## 生成索引

```bash
python3 scripts/build_growth_dashboard_indexes.py
python3 scripts/codex/build_dashboard_stage1_evidence_views.py
```

## 启动只读服务

```bash
cd EgoCore
PYTHONPATH=. python3 -m app.main --dashboard --host 127.0.0.1 --port 8787
```

## 页面

- `/runs`
- `/growth`
- `/failures`
- `/agency`
- `/samples/<sample_id>`

## 说明

- Dashboard v1 只读，允许轮询刷新，不反写 EgoCore / OpenEmotion 状态
- 页面层提供共享语义摘要与中英切换，但原始 artifact 仍是唯一权威证据
- 所有结论强度必须低于或等于当前 artifacts 与 observation 文档的证据强度
- `STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.*` 会把 bounded preflight、single-entry live window、comparative audit 三层证据分开记账
- `ARTIFACT_MANIFEST_CURRENT.*` 只做 inventory 分类与后续整理入口，不升格成新的 authority source
