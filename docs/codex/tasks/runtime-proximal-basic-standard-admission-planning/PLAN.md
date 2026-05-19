# Runtime-Proximal Basic-Standard Admission Planning - PLAN

## Purpose

把当前“下一张 bounded planning slice 未定义”的 blocker 收成一个可以直接交给 implementer 的 stage card。

## Current framing

- replay / controlled replay / controlled observation / host contract / host-consumption runner 都已存在
- 当前缺的不是更多局部 patch，而是一个更高一级的 aggregate admission framing
- 这张卡只冻结 planning，不实现 runner

## Work items

1. Freeze the aggregate question
   - 明确 basic-standard admission 在工程上到底判什么
2. Freeze the allowed inputs
   - 只消费五层现有 bounded evidence
3. Freeze the aggregate outputs
   - 定义 future runner 应输出的 aggregate verdict 与 reason surface
4. Freeze rollback / blocked conditions
   - 防止下一张 runner 卡靠偷扩 authority 或新 API 过线
5. Sync repo state
   - 更新 `PROGRAM_STATE_UNIFIED`、`OVERALL_PROGRESS`、evidence ledger、campaign ledger、scorecard

## Planned aggregate outputs

The future runner should emit at least:

- `layer_integrity_status`
- `host_surface_integrity_status`
- `causal_transfer_status`
- `claim_ceiling_status`
- `admission_decision`
- `reviewer_gate_ready`
- `blocked_reasons`

### Expected meanings

- `layer_integrity_status`
  - five frozen evidence layers are present, current, and internally green enough to compose
- `host_surface_integrity_status`
  - no widened host-consumable surface was needed
- `causal_transfer_status`
  - runtime-proximal evidence still shows host-consumable pressure beyond replay-only space
- `claim_ceiling_status`
  - aggregate wording remains below runtime efficacy / live benefit / consciousness claims
- `admission_decision`
  - `pass` or `hold`

## Reviewer gate for the future runner

- `success_reached`
  - aggregate verdict is computable, bounded, and passes without overclaim
- `needs_more_implementation`
  - framing is sound, but runner implementation is incomplete
- `needs_more_exploration`
  - evidence composition path is still ambiguous
- `blocked_by_external_dependency`
  - required artifact or dependency is genuinely unavailable
- `needs_reframing`
  - aggregate gate itself would force authority widening, bad compare surface, or claim inflation

## Validation for this planning slice

- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `git diff --check -- <scoped files>`

## Completion

This planning slice is complete when:

- `BASIC_STANDARD_ADMISSION_FREEZE.md` exists
- repo state points to this slice as the next bounded admission framing
- campaign checkpoint / ledger / scorecard are updated
- reviewer can honestly say the next frontier is implementer-ready
