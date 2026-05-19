# Active-Inference Mainline Activation - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- 相关 authority refs

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 中的 `Current milestone`
- 现有 `Tasks/active/*.md` 只作为 authority refs，不复制成第二真相源
- 当前 milestone 只允许推进 `Stage 3 deterministic stance-integrity runner + bounded validation`
- 先修订 runner/schema/tests，再同步 repo authority / task authority / campaign ledger
- 当前 milestone 内不得宣称 Stage 3 已证明，不得推进 authority release、cross-entry promotion、或 broader user-benefit closeout

## Scope control

- 只改当前 milestone 需要的文件
- 不顺手推进下一个 milestone
- 保持 diff scoped
- 不新增 scorer ontology
- 不扩 `policy_hint / response_tendency / trace_payload` 之外的 host-consumable surface
- 不释放 `direct tool / direct reply / direct transport authority`
- 不把 bounded research evidence 说成 runtime proof

## Validation strategy

- 每个 milestone 完成后运行：
  - `python3 scripts/codex/verify_repo.py --mode fast`
- 收口或高风险改动时运行：
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- 验证失败先修复
- 修不动就记录 blocker、降级完成口径、停止推进
- 不跳过失败验证直接进入下一 milestone

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 缺少外部凭据/审批、authority source 冲突、或 slice 无法闭环时停止

## Final handoff checklist

- [ ] `PLAN.md` 已更新进度与决策
- [ ] `STATUS.md` 已更新验证结果与 next step
- [ ] commands run / evidence 已记录
- [ ] risks / rollback notes 已记录
- [ ] repo state / progress / README routing 已与当前 execution owner 对齐
- [ ] Stage 3 deterministic runner 已明确记录固定 case set / parser / scorer / 不可宣称边界
