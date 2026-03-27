# MIGRATION_NOTE

## 影响范围

本轮变更扩展了 `CycleSignature` 的持久化字段，但保持了向后兼容加载。

新增字段：

- `closure_signature`
- `closure_family_id`
- `action_signature`
- `outcome_signature`
- `mode_signature`
- `closure_consistency_score`

---

## 兼容策略

- 旧 `proto_self_state.v1.json` 仍可直接加载
- `CycleSignature.from_dict()` 对缺失字段使用默认值回填
- 不需要一次性批量迁移旧镜像文件

---

## 宿主注意事项

- EgoCore 仍然只是 mirror/cache 持有者
- 本次没有引入第二套长期记忆真相源
- 如果后续要对历史 state 做离线分析，应优先按“字段可缺省”的方式读旧数据
