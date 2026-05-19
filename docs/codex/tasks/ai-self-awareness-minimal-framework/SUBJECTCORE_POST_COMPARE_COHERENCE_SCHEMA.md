# SubjectCore Post-Compare Coherence Schema

## Purpose

在 `SubjectCore` A/B/C compare 已经 full coverage 并被解释为 `completed architecture reading` 之后，
需要一个最小 planning-side coherence artifact，把：

- `SUBJECTCORE_ABC_COMPARE_SCORED_CURRENT.json`
- `SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json`

连成一条 repo-tracked、bounded、可回读的一致性读数。

这个 artifact 的职责不是继续选 winner，也不是宣称 runtime integration。
它只回答：

- compare 是否 truthfully 收口为 architecture reading
- follow-on batch 是否 truthfully 承接了 unified facade 路线
- 整条研究读数是否仍然停留在 frozen host surface / proposal-only / planning-side ceiling 内

## Input Artifacts

- `artifacts/self_awareness_research/SUBJECTCORE_ABC_COMPARE_SCORED_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json`

## Output Artifacts

- `artifacts/self_awareness_research/SUBJECTCORE_POST_COMPARE_COHERENCE_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_POST_COMPARE_COHERENCE_CURRENT.md`

## Schema

### Header

- `schema_version`
  - fixed: `subjectcore.post_compare_coherence.v1`
- `generated_at`
- `compare_artifact_path`
- `followon_batch_artifact_path`
- `output_schema_path`
- `claim_ceiling_note`

### Aggregate

- `coherence_status`
  - `pass | fail`
- `blocked_reasons`
  - list of failing check ids

### Checks

固定 checks：

- `PC1 compare_completed_architecture_reading`
  - compare 必须保持：
    - `compare_status = pass`
    - `compare_role = completed_architecture_reading`
- `PC2 compare_points_to_unified_facade`
  - compare 必须保持：
    - `winner_reading = no_clear_winner_keep_layers_separate`
    - `post_compare_conclusion = unified_subjectcore_facade_layered_internals`
- `PC3 compare_failure_flags_clean`
  - compare `failure_flags` 必须全部为 `false`
- `PC4 compare_full_coverage`
  - compare `coverage_summary` 必须显示：
    - records full coverage
    - slices full coverage
    - families full coverage
- `PC5 followon_batch_green`
  - follow-on batch 必须保持：
    - `overall_status = pass`
    - `expectation_match_count = sample_count`
- `PC6 followon_distinguishes_failure_types`
  - follow-on batch 必须同时存在：
    - `integrity fail / boundary pass`
    - `integrity fail / boundary fail`
  - proposal-side failures 至少要覆盖到：
    - `proposal_set_completion`
    - `proposal_set_closure`
- `PC7 claim_ceiling_still_bounded`
  - compare 与 follow-on batch 都必须继续把自己描述为：
    - `planning-side`
    - non-runtime-efficacy
    - non-consciousness claim

### Snapshots

- `compare_snapshot`
  - `compare_status`
  - `compare_role`
  - `winner_reading`
  - `post_compare_conclusion`
  - `failure_flags`
  - `coverage_summary`
  - `composite_ranking`
- `followon_batch_snapshot`
  - `overall_status`
  - `sample_count`
  - `integrity_pass_count`
  - `boundary_pass_count`
  - `expectation_match_count`
  - `sample_results`

### Boundaries

- `summary`
- `what_it_proves`
- `what_it_does_not_prove`
- `notes`

## Required Interpretation

- `coherence_status = pass` 只表示：
  - compare read 与 follow-on batch regression 彼此一致
  - 当前 `SubjectCore` planning supplement 没有自相矛盾
  - unified facade + layered internals 仍是正确的 research-side follow-on framing
- `coherence_status = pass` 不得被解释为：
  - runtime integration complete
  - host surface widened
  - autonomy ceiling lifted
  - any consciousness-like property
