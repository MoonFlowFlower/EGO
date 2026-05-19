# Runtime-Proximal Stronger Admission Planning - PLAN

## Purpose

把 `post-low-cue stronger admission` 从一句方向描述收成一张 implementer-ready 的 bounded planning card。

## Current framing

- `basic-standard admission runner` 已通过
- `low-cue ownership runner` 已通过
- 当前最有信息增益的下一步不是继续补 family，也不是碰 live/runtime proof
- 缺的是：把这两层通过的 bounded evidence 组合成下一张更高一级的 aggregate admission card

## Work items

1. Freeze the stronger aggregate question
   - 明确 stronger admission 在工程上到底判什么
2. Freeze the allowed inputs
   - 只消费当前两张已通过的 bounded runner artifacts
3. Freeze the aggregate outputs
   - 定义 future runner 应输出的 stronger verdict / audit surface
4. Freeze blocked / rollback conditions
   - 防止 future runner 借新 API、私有面、live 证据或坏 compare surface 过线
5. Sync repo state
   - 更新 `PROGRAM_STATE_UNIFIED`、`OVERALL_PROGRESS`、campaign ledger / scorecard、evidence ledger

## Planned aggregate outputs

The future runner should emit at least:

- `admission_stack_status`
- `low_cue_resilience_status`
- `host_surface_integrity_status`
- `claim_ceiling_status`
- `stronger_admission_decision`
- `reviewer_gate_ready`
- `blocked_reasons`

## Expected meanings

- `admission_stack_status`
  - current basic-standard admission remains green and reusable as lower-layer floor
- `low_cue_resilience_status`
  - low-cue persistence / ownership ambiguity / agency attribution remain green as stronger bounded layer
- `host_surface_integrity_status`
  - no widened host-consumable surface or authority drift is introduced by the stronger aggregation
- `claim_ceiling_status`
  - wording stays below runtime efficacy / live benefit / consciousness claims
- `stronger_admission_decision`
  - `pass` or `hold`

## Reviewer gate for the future runner

- `success_reached`
  - stronger aggregate verdict is computable, bounded, and passes without overclaim
- `needs_more_implementation`
  - framing is sound, but runner implementation is incomplete
- `needs_more_exploration`
  - stronger aggregation path is still ambiguous
- `blocked_by_external_dependency`
  - required bounded artifact is unavailable
- `needs_reframing`
  - stronger gate itself would force authority widening, bad compare surface, or claim inflation

## Validation for this planning slice

- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `git diff --check -- <scoped files>`

## Completion

This planning slice is complete when:

- `STRONGER_ADMISSION_FREEZE.md` exists
- repo state points to this slice as the next authorized bounded stage
- campaign checkpoint / ledger / scorecard are updated
- reviewer can honestly say the next frontier is implementer-ready
