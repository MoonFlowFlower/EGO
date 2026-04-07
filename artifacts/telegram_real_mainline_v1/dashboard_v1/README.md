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
- `/flow`
- `/growth`
- `/failures`
- `/agency`
- `/samples/<sample_id>`
- `/samples/<sample_id>/flow`

## 说明

- Dashboard v1 只读，允许轮询刷新，不反写 EgoCore / OpenEmotion 状态
- 页面层提供共享语义摘要与中英切换，但原始 artifact 仍是唯一权威证据
- 所有结论强度必须低于或等于当前 artifacts 与 observation 文档的证据强度

## `/flow` 读法

`/flow` 与 `/samples/<sample_id>/flow` 当前固定按这些段落展示：

1. `Flow Verdict`
2. `Input`
3. `Host Ingress`
4. `Subject Understanding`
5. `Reply Evolution`
6. `Host Arbitration`
7. `Output`

关键解释：

- `Subject Understanding`
  - 区分“主体链是否已接通”和“某个 context 是否加载”
  - `self_model = false` 不再自动表示 `proto_self_v2` 断线
- `Reply Evolution`
  - 当前是 `evidence_only_v1`
  - 只覆盖 `chat_mainline`
  - 展示的是：
    - 主体修正信号
    - 宿主裁决
    - 最终输出
  - 不是“原始 LLM 草稿 vs 修正后文本”的 diff

如果样本里消息已送出、但最终文本没有在 evidence bundle 持久化，页面会明确显示：

- `final_text_capture_status = missing_but_delivered`
- `reply_length`

这表示主链已送出消息，但当前证据包没有保存最终文本预览，不是页面渲染故障。
