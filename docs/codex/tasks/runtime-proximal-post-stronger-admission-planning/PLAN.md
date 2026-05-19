# Runtime-Proximal Post-Stronger Admission Planning - PLAN

## Purpose

把 `post-stronger admission` 从一句方向描述收成一张 implementer-ready 的 bounded planning card。

## Current framing

- `stronger-admission runner` 已通过
- 当前最有信息增益的下一步不是继续补 family，也不是碰 live/runtime proof
- 缺的是：把 stronger-admission `pass` 和 replay-selection authority 收成一张更高一级的 bounded coherence card

## Work items

1. Freeze the post-stronger question
   - 明确 post-stronger planning 在工程上到底判什么
2. Freeze the allowed inputs
   - 只消费当前 stronger-admission + replay-selection authority 三张已通过的 bounded artifacts
3. Freeze the aggregate outputs
   - 定义 future runner 应输出的 coherence verdict / audit surface
4. Freeze blocked / rollback conditions
   - 防止 future runner 借新 API、私有面、live 证据或坏 compare surface 过线
5. Sync repo state
   - 更新 `PROGRAM_STATE_UNIFIED`、`OVERALL_PROGRESS`、campaign ledger / scorecard、evidence ledger

## Planned aggregate outputs

The future runner should emit at least:

- `stronger_admission_status`
- `selection_coherence_status`
- `ablation_retention_status`
- `host_surface_integrity_status`
- `claim_ceiling_status`
- `post_stronger_decision`
- `reviewer_gate_ready`
- `blocked_reasons`

## Expected meanings

- `stronger_admission_status`
  - current stronger-admission artifact remains green and reusable as the bounded runtime-proximal floor
- `selection_coherence_status`
  - the stronger runtime-proximal pass remains consistent with the frozen replay-selection decision that keeps `active-inference self-model` as the durable build-first candidate
- `ablation_retention_status`
  - the post-stronger card still respects the replay gate's frozen target / delta / ablation discipline rather than collapsing into generic-safe or narrative-only wording
- `host_surface_integrity_status`
  - no widened host-consumable surface or authority drift is introduced by the stronger aggregation
- `claim_ceiling_status`
  - wording stays below runtime efficacy / live benefit / consciousness claims
- `post_stronger_decision`
  - `pass` or `hold`

## Reviewer gate for the future runner

- `success_reached`
  - post-stronger coherence verdict is computable, bounded, and passes without overclaim
- `needs_more_implementation`
  - framing is sound, but runner implementation is incomplete
- `needs_more_exploration`
  - coherence path is still ambiguous
- `blocked_by_external_dependency`
  - required bounded artifact is unavailable
- `needs_reframing`
  - post-stronger gate itself would force authority widening, bad compare surface, reopened challenger routing, or claim inflation

## Validation for this planning slice

- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `git diff --check -- <tracked scoped files>`
- `git diff --no-index --check /dev/null <each new planning file>` with no check output

## Completion

This planning slice is complete when:

- `POST_STRONGER_ADMISSION_FREEZE.md` exists
- repo state points to this slice as the next authorized bounded stage
- campaign checkpoint / ledger / scorecard are updated
- reviewer can honestly say the next frontier is implementer-ready
