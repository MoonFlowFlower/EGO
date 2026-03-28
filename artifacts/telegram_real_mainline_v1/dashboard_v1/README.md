# Growth Dashboard v1

## 生成索引

```bash
python3 scripts/build_growth_dashboard_indexes.py
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
- `/samples/<sample_id>`

## 说明

- Dashboard v1 只读，允许轮询刷新，不反写 EgoCore / OpenEmotion 状态
- 所有结论强度必须低于或等于当前 artifacts 与 observation 文档的证据强度
