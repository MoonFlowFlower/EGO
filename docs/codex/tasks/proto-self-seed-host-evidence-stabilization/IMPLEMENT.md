# Proto-Self Seed Host Evidence Stabilization - IMPLEMENT

## Source of truth

- `Tasks/Proto-Self_Seed/Proto-Self_Seed_v0.2_正式设计稿.md`
- `docs/codex/tasks/proto-self-seed-real-rollout/PLAN.md`
- `docs/codex/tasks/proto-self-seed-real-rollout/STATUS.md`

## Execution rules

- 只修 host/evidence 层，不改 Seed 主体 contract
- follow-up 绑定只覆盖“继续读/看完整/不要截断”这一窄类显式读后续

## Scope control

- 不扩到通用 shell policy
- 不扩到 profile memory standing rule 语义

## Validation strategy

- 先 targeted pytest
- 再跑 `python3 scripts/codex/verify_repo.py --mode fast`

## Failure handling

- 若 follow-up 绑定导致现有 execute/write 语义回归，优先回退到更窄的 analyze-only promotion

## Stopping rule

- 3 个目标行为都被本地测试证明后停止，不顺手处理其他 rollout 缺口

## Final handoff checklist

- 代码 patch
- 测试通过
- task STATUS 更新
