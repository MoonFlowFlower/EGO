# P1 EVIDENCE_TABLE

| evidence_id | evidence_level | source_type | artifact_path | what_it_proves | what_it_does_not_prove |
|---|---|---|---|---|---|
| P1-E-001 | E1 | code | `EgoCore/app/runtime_v2/loop.py` | `RuntimeV2Loop` 已去掉 proto-self/risk/evidence/feedback 的内联实现，回到 orchestration 主线 | 不证明真实行为未变，需结合回归 |
| P1-E-002 | E1 | code | `EgoCore/app/runtime_v2/proto_self_runtime.py` | 新增宿主 helper，承接 proto-self ingress、risk、feedback、response_plan capture | 不证明 helper 设计已是最终边界 |
| P1-E-003 | E2 | test | `EgoCore/tests/test_runtime_v2_proto_self_runtime.py` | 风险评估、event 构造、response_plan payload 形状可被单测约束 | 不证明真实 Telegram 主链行为稳定 |
| P1-E-004 | E1 | metric | `artifacts/P1/RESPONSIBILITY_MAP.md` | 已有重构前职责图和重构后边界图 | 不证明复杂度下降一定等于架构问题全部解决 |
| P1-E-005 | E1 | metric | `EgoCore/app/runtime_v2/loop.py` | `loop.py` 从 376 行收至 259 行，内联职责显著减少 | 不证明其他文件没有继承隐藏复杂度 |
| P1-E-006 | E2 | validation | `python3 -m py_compile` 本轮输出 | 新增 helper 与测试文件至少通过静态语法校验 | 不证明运行时行为一致 |
| P1-E-007 | E2 | validation | `cmd.exe /c py -3 -m pytest tests\\test_runtime_v2_proto_self_runtime.py ...` 本轮结果 | 9 个最小回归通过，helper 引入未破坏多数现有运行时最小契约 | 不证明全部 runtime 回归通过 |
