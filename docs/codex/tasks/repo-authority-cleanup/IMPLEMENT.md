# Repo Authority Cleanup - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/PROTO_SELF_MVP_AUTHORITY_AUDIT.md`
- `docs/PROTO_SELF_SINGLE_AUTHORITY_DECISION.md`
- `EgoCore/docs/05_DEPRECATED_AND_SHIMS.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 6 个 ledger 是 execution ledger，不是新的 authority source
- 所有删改都必须能回答：
  - formal caller 是谁
  - tests/tools/docs caller 是谁
  - 现在为什么还不能删
  - 删除后替代路径是什么
  - 回退方式是什么

## Scope control

- 只改当前 milestone 需要的文件
- 不顺手推进 drives/reflection/developmental 语义改造
- 不把 docs wording 变化冒充“系统收口完成”
- 保持 diff scoped，只触碰本任务文件和被当前波次直接命中的 authority/gate/test 文件

## Validation strategy

- 每个 milestone 完成后运行：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 高风险或 closeout 时运行：
  - `python3 scripts/codex/verify_repo.py --mode full`
- 当前任务默认不触发 provider/runtime e2e gate，除非 formal mainline runtime 行为真的发生变化
- 第一轮定向验证优先：
  - OpenEmotion single-authority static tests
  - self-model integration/readback tests
  - EgoCore runtime self-model/identity writeback tests

## Failure handling

- 验证失败先修复当前波次
- 命中 stop 条件时，记录 blocker、保留 ledger 证据、停止推进下一波
- 不跳过失败验证直接进入下一 milestone

## Stop conditions

仅在以下情况下停止并汇报：

1. formal mainline 会被打断
2. caller 关系不明确，删除风险高
3. dual-authority 无法在当前波次安全收口
4. 证据链/日志链是否可删无法判定

## Per-wave report contract

每一波都按这 12 项写回 `STATUS.md`：

1. 当前层级
2. 当前处理能力域/清理域
3. formal mainline 是否变动
4. 当前确定项
5. 关键未知
6. 本波 authority 结论
7. 本波保留清单
8. 本波降级清单
9. 本波归档清单
10. 本波删除清单
11. 本波不能证明什么
12. 下一波最小动作

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新波次结果与 next step
- [ ] 6 个 ledger 已同步
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
