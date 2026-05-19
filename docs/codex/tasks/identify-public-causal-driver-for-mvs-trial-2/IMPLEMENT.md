# Trial-2 Public-Driver-First Spec - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `EXPLORE.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
- `artifacts/self_awareness_research/TRIAL1_HARD_SET_RERUN_SCORED_CURRENT.json`
- `artifacts/self_awareness_research/TRIAL1_HARD_SET_CAUSAL_SEPARATION_CURRENT.json`
- `artifacts/self_awareness_research/TRIAL1_REDESIGNED_ABLATION_EVALUATION_CURRENT.json`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 严格按 `M0 -> M4` 推进
- 每个 milestone 收口必须落一个：
  - `continue`
  - `demote`
  - `close`
- 当前任务只允许最多 `3` 条 public-driver hypotheses

## Scope control

- 只识别当前 hard set + 当前 scorer 下的 bounded active public driver
- 不扩 replay suite
- 不做 challenger scoring
- 不改 scorer ontology
- 不升级 repo-level state
- 不把 `counterfactual_writeback` 重新写回主线赌注
- 不实现 full prototype logic

## Implementation slice allowed at M3

- 允许的最小代码改动：
  - 为 Trial-2 新增 `2` 个 split diagnostic ablation ids
  - 只改 public-path gating helper，不改 scorer ontology
  - 补最小 fidelity / replay tests
  - 增加一个 Trial-2 decision evaluator 脚本
- 不允许的改动：
  - 新增 authority source
  - 另开 parallel mainline
  - 修改 hard set case 内容
  - 修改 scorer 的 ontology、weight、bucket semantics

## Validation strategy

- `M0 / M1 / M2`
  - `git diff --check -- docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2`
- `M3`
  - `python3 -m py_compile ...`
  - 定向 pytest
  - `python3 scripts/codex/verify_repo.py --mode fast`
- `M4`
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- 若候选集想扩到 `3` 条以上，立即停
- 若必须改 scorer / hard set 才能区分，立即按 `underdefined` 收口
- 若 rerun 结果只剩 trace/private differences，不得写成 efficacy 或 active public driver

## Stopping rule

- 当前 milestone 未验证通过，不进入下一 milestone
- 若 `M2` 没有判别实验，直接 `close`
- 若 `M3` rerun 不具判别性，直接进入 `M4` 做 `close` 或 `demote`

## Final handoff checklist

- [ ] `PLAN.md` 已按 `M0 -> M4` 更新
- [ ] `STATUS.md` 已记录每个 milestone 的 terminal label
- [ ] commands run / evidence 已记录
- [ ] no repo-level state upgrade
- [ ] final decision artifact 已落地
